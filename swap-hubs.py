import asyncio
import meraki.aio
import os
import time

RETRIES = 5  # max number of retries per call for 429 rate limit status code

org_id = os.environ.get('MERAKI_ORG_ID')


async def get_tagged_networks(aiomeraki: meraki.aio.AsyncDashboardAPI, orgid, tag):
    print(f'getting networks for org ID {orgid}')
    try:
        networks = await aiomeraki.organizations.getOrganizationNetworks(organizationId=orgid, tags=tag)
        return networks
    except meraki.AsyncAPIError as e:
        print(f"Meraki API error: {e}")
        return str(orgid)
    except Exception as e:
        print(f"some other error: {e}")
        return str(orgid)


# Function to add a network tag to a network
async def update_network_tags(aiomeraki: meraki.aio.AsyncDashboardAPI, network_id, tag):
    try:
        await aiomeraki.networks.updateNetwork(network_id, tags=tag)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
    except Exception as e:
        print(f'The following error has occurred: {e}')
    return network_id, tag


# Function to swap the primary and secondary hubs
async def swap_hubs(aiomeraki: meraki.aio.AsyncDashboardAPI, network_id):
    # Logic: grab the site to site VPN config for a network
    # 1. Ensure network is type 'spoke'
    # 2. If there are 2 or more hubs, then set hub1 = hub2 and hub2 = hub 1. hubs[0], hubs[1] = hubs[1], hubs[0]
    #   2a. Update the site to site VPN settings with updated hub list
    #   2b. If there is not more than 2 hubs, just return without changing anything.
    # Initialize the dashboard API session
    try:
        net = await aiomeraki.appliance.getNetworkApplianceVpnSiteToSiteVpn(network_id)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
        return
    except Exception as e:
        print(f'The following error has occurred: {e}')
        return
    if net['mode'] == "spoke":
        if(len(net['hubs']) >= 2):
            net['hubs'][0], net['hubs'][1] = net['hubs'][1], net['hubs'][0]
            try:
                await aiomeraki.appliance.updateNetworkApplianceVpnSiteToSiteVpn(network_id, mode=net['mode'], hubs=net['hubs'])
            except meraki.AsyncAPIError as e:
                print(f'Meraki API error: {e}')
                return
            except Exception as e:
                print(f'The following error has occurred: {e}')
                return
            return network_id
        else:
            return
    else:
        return

# Main function to run the script
async def main():
    # Prompt the user for the API key, organization ID, and tag to filter on
    tag = input("Enter the tag to filter on (e.g., 'HUB_'): ")

    startTime = time.time_ns()

    async with meraki.aio.AsyncDashboardAPI(
        log_file_prefix=__file__[:-3],
        print_console=False,
        maximum_retries=RETRIES
    ) as aiomeraki:
        # define vars
        get_tasks = []
        swap_results = []


        # Get all networks that are tagged with specified tag
        networks = await get_tagged_networks(aiomeraki, org_id, tag)
        for net in networks:
            # Prepare async task to swap the first and second hubs
            get_tasks.append(swap_hubs(aiomeraki, net['id']))

        for task in asyncio.as_completed(get_tasks):
            swap = await task
            swap_results.append(swap)
        for result in swap_results:
            if(result):
                print(f'Network ID {result} had its hubs swapped')

    endTime = time.time_ns()
    print(f'Total time to run: {(endTime - startTime)/1000000} ms')

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())