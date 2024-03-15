import asyncio
import os
import meraki.aio
import time
import re

RETRIES = 5  # max number of retries per call for 429 rate limit status code

# Define your Meraki API key and organization ID
org_id = os.environ.get('MERAKI_ORG_ID')


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

async def get_org_uplink_usage(aiomeraki: meraki.aio.AsyncDashboardAPI, org_id, t1, timespan):
    try:
        net = await aiomeraki.appliance.getOrganizationApplianceUplinksUsageByNetwork(org_id, t1=t1, timespan=timespan)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
        return
    except Exception as e:
        print(f'The following error has occurred: {e}')
        return
    return net

async def get_net_uplink_usage(aiomeraki: meraki.aio.AsyncDashboardAPI, net_id, t1, timespan):
    try:
        net = await aiomeraki.appliance.getNetworkApplianceUplinksUsageHistory(net_id, t1=t1, timespan=timespan)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
        return
    except Exception as e:
        print(f'The following error has occurred: {e}')
        return
    return net, net_id

async def get_net_uplink_bw(aiomeraki:meraki.aio.AsyncDashboardAPI, net_id):
    try:
        net = await aiomeraki.appliance.getNetworkApplianceTrafficShapingUplinkBandwidth(net_id)
    except meraki.AsyncAPIError as e:
        print(f'Meraki API error: {e}')
        return
    except Exception as e:
        print(f'The following error has occurred: {e}')
        return
    return {net_id:net}

async def main():
    # track runtime
    startTime = time.time_ns()
    netNames = {}
    clicklist = []
    get_tasks = []
    get_ul_tasks = []
    netDetails = []
    netUplinks = {}

    # define timespans and percentages
    tspan = 300 # org-wide timespan check default 5 min
    orgThreshold =.5 # default 50% utilization over tspan average
    netThreshold = .7 # default 70% utilization over 60 sec per network

    async with meraki.aio.AsyncDashboardAPI(
        log_file_prefix=__file__[:-3],
        print_console=False,
        maximum_retries=RETRIES
    ) as aiomeraki:
        networks = await get_appliance_networks(aiomeraki, org_id)
        for net in networks:
            get_ul_tasks.append(get_net_uplink_bw(aiomeraki, net['id']))

        for task in asyncio.as_completed(get_ul_tasks):
            netUplink = await task
            netUplinks = netUplinks | netUplink

        currentTime = int(time.time())
        networks = await get_org_uplink_usage(aiomeraki, org_id, currentTime, tspan )
        for net in networks:
            for uplink in net['byUplink']:
                if re.search("wan*", uplink['interface']):
                    #print(f'Uplink limit for {net['name']} interface {uplink['interface']} is {float(netUplinks[net['networkId']]['bandwidthLimits'][uplink['interface']]['limitUp']*.6)}')
                    #print(f'Current usage over 5 min avg for this network is {float(uplink['sent']*8/tspan/1024)} Kbps')
                    if float(uplink['sent']*8/tspan/1024) >= float(netUplinks[net['networkId']]['bandwidthLimits'][uplink['interface']]['limitUp']*orgThreshold):
                        print(f"Uplink usage alert on {net["name"]} :: hit at least {int(orgThreshold*100)}% avg uplink with {(round(int(uplink['sent'])*8/tspan/1024,2))} Kbps in the last {tspan} seconds!")
                        clicklist.append(net['networkId'])
                        netNames[net['networkId']] = net['name']


        for net in clicklist:
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime), 60 ))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 60), 60))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 120), 60))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 180), 60))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 240), 60))

        for task in asyncio.as_completed(get_tasks):
            netDetail = await task
            netDetails.append(netDetail)

        for net in netDetails:
            for uplink in net[0][0]['byInterface']:
                if re.match("wan*", uplink['interface']):
                    if float(uplink['sent']*8/60/1024) >= float(netUplinks[net[1]]['bandwidthLimits'][uplink['interface']]['limitUp']*netThreshold):
                        print(f"network {netNames[net[1]]} hit at least {int(netThreshold*100)}% avg uplink with {(round(int(uplink['sent'])*8/60/1024,2))} Kbps in a 60-sec interval")

        endTime = time.time_ns()
        print(f'Total time to run: {(endTime - startTime) / 1000000} ms')


if __name__ == '__main__':
    asyncio.run(main())
