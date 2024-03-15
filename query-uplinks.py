import asyncio
import os
import meraki.aio
import time

RETRIES = 5  # max number of retries per call for 429 rate limit status code

# Define your Meraki API key and organization ID
org_id = os.environ.get('MERAKI_ORG_ID')

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


async def main():
    # track runtime
    startTime = time.time_ns()
    netNames = {}
    clicklist = []
    get_tasks = []
    netDetails = []
    currentTime = int(time.time())
    async with meraki.aio.AsyncDashboardAPI(
        log_file_prefix=__file__[:-3],
        print_console=False,
        maximum_retries=RETRIES
    ) as aiomeraki:
        networks = await get_org_uplink_usage(aiomeraki, org_id, currentTime, 300 )
        for net in networks:
            for uplink in net['byUplink']:
                if int(uplink['sent']) >= 10000000:
                    print(f"Uplink usage alert on {net["name"]} :: averaged {(round(int(uplink['sent'])*8/300/1024/1024,2))} Mbps in the last 300 seconds!")
                    clicklist.append(net['networkId'])
                    netNames[net['networkId']] = net['name']


        for net in clicklist:
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime-60), 60 ))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 120), 60))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 180), 60))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 240), 60))
            get_tasks.append(get_net_uplink_usage(aiomeraki, net, (currentTime - 300), 60))

        for task in asyncio.as_completed(get_tasks):
            netDetail = await task
            netDetails.append(netDetail)

        for net in netDetails:
            for uplink in net[0][0]['byInterface']:
                if int(uplink['sent']) >= 1000000:
                    print(f"network {netNames[net[1]]} saw 60-second upload rate of {(round(int(uplink['sent'])*8/60/1024/1024,2))} Mbps in a 60-sec interval")

        endTime = time.time_ns()
        print(f'Total time to run: {(endTime - startTime) / 1000000} ms')


if __name__ == '__main__':
    asyncio.run(main())
