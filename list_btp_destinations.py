"""
Script to list BTP destinations using the Destination Service API
"""
import requests
import json
 
# Service key credentials
XSUAA_URL = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com"
CLIENT_ID = "sb-clone71c05d751e91409c93f13d107ad8db24!b576522|destination-xsappname!b404"
CLIENT_SECRET = "f921addf-670e-4b1a-adb2-794f7f0868c5$yIhvLM3HkxvF3Nmgk-nFO6WU4MIhFIpL9htuo0gBZ-M="
DESTINATION_URI = "https://destination-configuration.cfapps.eu10.hana.ondemand.com"
 
def get_oauth_token():
    """Get OAuth token from XSUAA"""
    token_url = f"{XSUAA_URL}/oauth/token"
   
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
   
    response = requests.post(token_url, data=data)
    response.raise_for_status()
   
    return response.json()['access_token']
 
def list_destinations(token):
    """List all destinations in the subaccount"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
   
    # Get subaccount destinations
    url = f"{DESTINATION_URI}/destination-configuration/v1/subaccountDestinations"
   
    response = requests.get(url, headers=headers)
    response.raise_for_status()
   
    return response.json()
 
def get_destination_details(token, destination_name):
    """Get details of a specific destination"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
   
    url = f"{DESTINATION_URI}/destination-configuration/v1/subaccountDestinations/{destination_name}"
   
    response = requests.get(url, headers=headers)
    response.raise_for_status()
   
    return response.json()
 
if __name__ == "__main__":
    print("🔐 Getting OAuth token...")
    token = get_oauth_token()
    print("✅ Token obtained\n")
   
    print("📋 Listing destinations...")
    destinations = list_destinations(token)
   
    print(f"\n🎯 Found {len(destinations)} destinations:\n")
    print(json.dumps(destinations, indent=2))
   
    # Optionally get details of first destination
    if destinations:
        first_dest = destinations[0]['Name']
        print(f"\n📄 Details of '{first_dest}':")
        details = get_destination_details(token, first_dest)
        print(json.dumps(details, indent=2))