import requests
import os
import re
import time

# Define your Meraki API key and organization ID
api_key = "Bearer " + os.environ.get('MERAKI_DASHBOARD_API_KEY')
org_id = os.environ.get('MERAKI_ORG_ID')

# Define the URL for Meraki API endpoints
base_url = 'https://api.meraki.com/api/v1'

# Set up headers for API requests
headers = {
    'Authorization': api_key,
    'Content-Type': 'application/json'
}


# Function to fetch a list of networks in the organization
def get_organization_networks():
    url = f'{base_url}/organizations/{org_id}/networks'
    response = requests.get(url, headers=headers).json()
    appliances = []
    for network in response:
        if 'appliance' in network['productTypes']:
            appliances.append(network)
    return appliances


# Function to get the hub name for tag purposes
def get_hub_name(hub_id):
    url = f'{base_url}/networks/{hub_id}'
    response = requests.get(url, headers=headers).json()
    return response['name'].replace(' ', '_')


# Function to get the current tags on a network
def get_network_tags(network_id):
    url = f'{base_url}/networks/{network_id}'
    response = requests.get(url, headers=headers).json()
    return response['tags']


# Function to add a network tag to a network
def update_network_tags(network_id, tag):
    url = f'{base_url}/networks/{network_id}'
    data = {
        'tags': tag
    }
    response = requests.put(url, headers=headers, json=data)
    return response.status_code == 200


# Main function to iterate through networks and check site-to-site VPN settings
def main():
    # track runtime
    startTime = time.time_ns()

    networks = get_organization_networks()
    
    for network in networks:
        network_id = network['id']
        
        # Fetch site-to-site VPN settings
        url = f'{base_url}/networks/{network_id}/appliance/vpn/siteToSiteVpn'
        response = requests.get(url, headers=headers)
        vpn_settings = response.json()
        hubs = {}

        # Check if the first hub has the specified hubId
        if vpn_settings['mode'] == "spoke":  # and vpn_settings['hubs'][0]['hubId'] == hub_id_to_check:
            myTags = get_network_tags(network_id)
            for tag in myTags:
                if re.match("^HUB_*", tag):
                    myTags.remove(tag)
            if vpn_settings['hubs'][0]['hubId'] in hubs:
                myTags.append('HUB_'+hubs[vpn_settings['hubs'][0]['hubId']])
            else:
                new_hub = get_hub_name(vpn_settings['hubs'][0]['hubId'])
                hubs[vpn_settings['hubs'][0]['hubId']] = new_hub
                myTags.append('HUB_'+new_hub)
            print(f"Applying tags '{myTags}' to network {network['name']}")
            if update_network_tags(network_id, myTags):
                print(f"\tTags '{myTags}' applied successfully.")
            else:
                print(f"\tFailed to apply tags to the network.")
        else:
            print(f"Network {network['name']} (ID: {network_id}) is not a spoke.")
    endTime = time.time_ns()
    print(f'Total time to run: {(endTime - startTime) / 1000000} ms')

if __name__ == '__main__':
    main()
