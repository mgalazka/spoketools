import asyncio
import itertools
import os
import re
import meraki.aio
import time

RETRIES = 5  # max number of retries per call for 429 rate limit status code

# Define your Meraki API key and organization ID
org_id = os.environ.get('MERAKI_ORG_ID')


# Function to fetch a list of networks in the organization
async def get_appliance_networks(aiomeraki: meraki.aio.AsyncDashboardAPI, orgid):
    print(f'getting networks for org ID {orgid}')
    try:
        networks = await aiomeraki.organizations.getOrganizationNetworks(organizationId=orgid)
    except meraki.AsyncAPIError as e:
        print(f"Meraki API error: {e}")
        return str(orgid)
    except Exception as e:
        print(f"some other error: {e}")
        return str(orgid)

    # filter for just MX/Z networks
    appliances = []
    for network in networks:
        if 'appliance' in network['productTypes']:
            appliances.append(network)
    return appliances


# Function to return only spokes
async def filter_spoke(aiomeraki: meraki.aio.AsyncDashboardAPI, network_id):
    try:
        net = await aiomeraki.appliance.getNetworkApplianceVpnSiteToSiteVpn(network_id)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
        return
    except Exception as e:
        print(f'The following error has occurred: {e}')
        return
    if net['mode'] == "spoke":
        return net, network_id
    else:
        return


# Function to prepare network tags by removing any HUB_ tags
def prep_hub_tag_removal(net):
    if len(net['tags']) < 1:
        return {}
    for tag in net['tags']:
        if re.match("^HUB_*", tag):
            net['tags'].remove(tag)
    return {net['id']: net['tags']}



# Function to add a network tag to a network
async def update_network_tags(aiomeraki: meraki.aio.AsyncDashboardAPI, network_id, tag):
    try:
        await aiomeraki.networks.updateNetwork(network_id, tags=tag)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
    except Exception as e:
        print(f'The following error has occurred: {e}')
    return network_id, tag


# Main function to iterate through networks and check site-to-site VPN settings
async def main():
    # track runtime
    startTime = time.time_ns()

    async with meraki.aio.AsyncDashboardAPI(
        log_file_prefix=__file__[:-3],
        print_console=False,
        maximum_retries=RETRIES
    ) as aiomeraki:
        # define vars
        spokes = []
        get_tasks = []
        updateTags = {}
        netNames = {}
        get_tag_tasks = []
        tag_results = []


        # Get all networks that are MX/Z appliances
        networks = await get_appliance_networks(aiomeraki, org_id)
        for net in networks:
            # Save names without spaces in dictionary for quick tag use
            netNames[net['id']] = net['name'].replace(' ', '_')
            # remove existing HUB_ tags
            updateTags = updateTags | prep_hub_tag_removal(net)
            # Prepare async task to filter network list for just spokes
            get_tasks.append(filter_spoke(aiomeraki, net['id']))


        # Gather results of filtering for spokes
        for task in asyncio.as_completed(get_tasks):
            spoke = await task
            spokes.append(spoke)
        # remove None entries from iterative functions
        spokes = list(itertools.filterfalse(lambda item: not item , spokes))


        # iterate through spokes and add tags for primary hub to tag dictionary
        for spoke in spokes:
            if spoke[1] in updateTags:
                updateTags[spoke[1]].append('HUB_' + netNames[spoke[0]['hubs'][0]['hubId']])
            else:
                updateTags[spoke[1]] = ['HUB_' + netNames[spoke[0]['hubs'][0]['hubId']]]


        # Prepare async task to update all spoke tags with primary hub
        for net_id, net_tags in updateTags.items():
            get_tag_tasks.append(update_network_tags(aiomeraki, net_id, net_tags))
        for task in asyncio.as_completed(get_tag_tasks):
            tag = await task
            tag_results.append(tag)
        for result in tag_results:
            print(f'Network {netNames[result[0]]} has the following tags: {result[1]}')
    endTime = time.time_ns()
    print(f'Total time to run: {(endTime - startTime)/1000000} ms')

if __name__ == '__main__':
    asyncio.run(main())

