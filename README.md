# spoketools

## Merak AutoVPN Spoke Tools
This is a set of tools to help manage AutoVPN spokes in a Meraki environment. Currently published scripts allow an administrator to tag AutoVPN spoke networks with the primary hub name as a network tag. This allows, via API or Dashboard access, the administrator to more easily identify which spokes are leveraging which hub as primary.

## Scripts

**tag-networks.py** - This is a script written with traditional 'requests' module in python. It will identify any MX/Z network in the provided organization and update the network tags of any spokes to include the primary hub name as a tag, with HUB_ prepended to the start of the name and any spaces replaced by underscores. It will also remove any tag beginning with HUB_ that does not reflect the primary hub, either because the network is not a spoke, or the primary hub differs from what had been tagged previously on that network.

**tag-networks-aio.py** - This script has similar functionality, but it is written using the Meraki Dashboard API python module, in concert with asyncio. This allows the script to complete much more quickly than the _tag_networks.py_ version. 

## Usage Requirements ##
These scripts require that the following environment variables are set:

**MERAKI_DASHBOARD_API_KEY** - this should be set to the API key copied from Dashboard.

**MERAKI_ORG_ID** - this should be set to the Meraki Org ID that represents the org with the AutoVPN setup to be modified. Org ID can be pulled either via API (https://developer.cisco.com/meraki/api/get-organizations/) or by looking at the footer of any page on the Meraki Dashboard when logged in.

