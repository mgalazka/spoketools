# spoketools

## Merak AutoVPN Spoke Tools
This is a set of tools to help manage AutoVPN spokes in a Meraki environment. Note that all of these scripts are considered proof of concept scripts and may not contain much error handling or checking. Please exercise caution when using them.

## Scripts

**tag-networks.py** - This is a script written with traditional 'requests' module in python. It will identify any MX/Z network in the provided organization and update the network tags of any spokes to include the primary hub name as a tag, with HUB_ prepended to the start of the name and any spaces replaced by underscores. It will also remove any tag beginning with HUB_ that does not reflect the primary hub, either because the network is not a spoke, or the primary hub differs from what had been tagged previously on that network.

**tag-networks-aio.py** - This script has similar functionality, but it is written using the Meraki Dashboard API python module, in concert with asyncio. This allows the script to complete much more quickly than the _tag_networks.py_ version. It will identify any MX/Z network in the provided organization and update the network tags of any spokes to include the primary hub name as a tag, with HUB_ prepended to the start of the name and any spaces replaced by underscores. It will also remove any tag beginning with HUB_ that does not reflect the primary hub, either because the network is not a spoke, or the primary hub differs from what had been tagged previously on that network.

**query-uplinks.py** - Quick proof of concept script to check for high upload usage for all networks in an org for the last 5-minute window. In the event that a network uplink hits a data threshold (calculated by a variable percentage of the uplink's traffic shaping rate) for the 5-min window, 60-sec resolution grabs over that 5-min period will then be run. This script is rough around the edges and has had little testing/debugging, use at your own risk.

**swap-hubs.py** - Warning - this is the first version and has very little error checking. This script takes a tag name as input (i.e. one that was applied with tag-networks-aio.py), and it will find all networks with that tag. If the network is configured as an AutoVPN spoke and has at least 2 hubs configured, it will swap the primary and secondary hubs.

## Usage Requirements
These scripts require that the following environment variables are set:

**MERAKI_DASHBOARD_API_KEY** - this should be set to the API key copied from Dashboard.

**MERAKI_ORG_ID** - this should be set to the Meraki Org ID that represents the org with the AutoVPN setup to be modified. Org ID can be pulled either via API (https://developer.cisco.com/meraki/api/get-organizations/) or by looking at the footer of any page on the Meraki Dashboard when logged in.

