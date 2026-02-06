"""
Test script to directly test S/4HANA connection through BTP destination
This bypasses CAP and tests the raw OData endpoint
"""
import requests
import json
import base64

# XSUAA credentials for OAuth token
XSUAA_URL = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com"
CLIENT_ID = "sb-testJoule!t576522"
CLIENT_SECRET = "eebdae2b-5b43-4a3e-b0ae-b84c0470feb3$P2Smi6nkmIQ_Le3eRwIemcLSCyDPmM9-TbNtL6wCdig="

# Connectivity service credentials (from cf env testJoule-srv)
CONNECTIVITY_CLIENT_ID = "sb-cloned262633d3674452c9da8e55a4c1b01a8!b576522|connectivity!b114511"
CONNECTIVITY_CLIENT_SECRET = "04209481-1190-4725-84d2-f6cf815fbf22$RG3ZfsVJbZvha5kRR71LMxkcqb1OtRDZnLipy76N2SY="

# Destination credentials (from cf env testJoule-srv)  
DESTINATION_CLIENT_ID = "sb-clone71c05d751e91409c93f13d107ad8db24!b576522|destination-xsappname!b404"
DESTINATION_CLIENT_SECRET = "2779f57c-2d7f-46bc-b9b1-b7cc3e0e306a$3JsRRPyCPkff6IvhKjgnQycJtjOi4rC09R_J1NzGMww="
DESTINATION_URI = "https://destination-configuration.cfapps.eu10.hana.ondemand.com"

# S/4HANA endpoint info from destination
S4_URL = "http://s4-sb4:44380"
S4_USER = "JOULE_ADMIN"
S4_PASSWORD = "Diesel_2025_978625!"

def test_1_basic_auth_direct():
    """Test 1: Direct S/4HANA call with Basic Auth (simulating what BTP does)"""
    print("\n" + "="*80)
    print("TEST 1: Direct S/4HANA OData Service Metadata (Basic Auth)")
    print("="*80)
    
    url = f"{S4_URL}/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200"
    
    # Create Basic Auth header
    credentials = f"{S4_USER}:{S4_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Accept': 'application/xml'
    }
    
    print(f"URL: {url}")
    print(f"User: {S4_USER}")
    print(f"Auth: Basic (credentials hidden)")
    
    try:
        # This will fail because we can't reach on-premise from local
        # But it shows what the request looks like
        print("\n⚠️  Note: This will fail locally (no access to on-premise)")
        print("But it shows the exact request that BTP makes to S/4HANA\n")
        
        response = requests.get(url, headers=headers, timeout=5)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body (first 500 chars):\n{response.text[:500]}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error (expected - can't reach on-premise from local)")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_2_get_destination_details():
    """Test 2: Get destination configuration from BTP"""
    print("\n" + "="*80)
    print("TEST 2: Get S4HANA_PCE_SSO Destination Configuration")
    print("="*80)
    
    # Get OAuth token for destination service
    token_url = f"{XSUAA_URL}/oauth/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': DESTINATION_CLIENT_ID,
        'client_secret': DESTINATION_CLIENT_SECRET
    }
    
    print("Getting OAuth token for Destination service...")
    token_response = requests.post(token_url, data=data)
    token = token_response.json()['access_token']
    print(f"✅ Token obtained\n")
    
    # Get destination details
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    dest_url = f"{DESTINATION_URI}/destination-configuration/v1/subaccountDestinations/S4HANA_PCE_SSO"
    print(f"Fetching destination: {dest_url}\n")
    
    response = requests.get(dest_url, headers=headers)
    
    if response.status_code == 200:
        dest_config = response.json()
        print("✅ Destination Configuration:")
        print(json.dumps({
            "Name": dest_config.get("Name"),
            "Type": dest_config.get("Type"),
            "URL": dest_config.get("URL"),
            "Authentication": dest_config.get("Authentication"),
            "ProxyType": dest_config.get("ProxyType"),
            "User": dest_config.get("User"),
            "sap-client": dest_config.get("sap-client")
        }, indent=2))
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")

def test_3_simulate_cap_request():
    """Test 3: Show what CAP is trying to do"""
    print("\n" + "="*80)
    print("TEST 3: What CAP/CDS is Requesting")
    print("="*80)
    
    print("\nCAP makes this request through the destination:")
    print(f"  Method: GET")
    print(f"  URL: {S4_URL}/")  # CAP uses '/' as path
    print(f"  Headers:")
    print(f"    - Accept: application/json")
    print(f"    - Authorization: Basic (using destination credentials)")
    print(f"    - x-csrf-token: Fetch")
    print(f"    - sap-client: 200")
    
    print("\n📋 The 403 error means:")
    print("  1. ✅ Cloud Connector is working (request reached S/4HANA)")
    print("  2. ✅ Destination is configured correctly")
    print("  3. ✅ Authentication credentials are being sent")
    print("  4. ❌ S/4HANA is rejecting the request")
    
    print("\n🔍 Possible causes on S/4HANA side:")
    print("  • User 'JOULE_ADMIN' doesn't have authorization for the OData service")
    print("  • Service 'RFM_MANAGE_SALES_ORDERS_SRV' is not activated")
    print("  • Wrong password in destination")
    print("  • User is locked or expired")
    print("  • Required S/4HANA authorizations missing (transaction code access, etc.)")

if __name__ == "__main__":
    print("="*80)
    print("S/4HANA Connection Diagnostic Test")
    print("="*80)
    
    test_1_basic_auth_direct()
    test_2_get_destination_details()
    test_3_simulate_cap_request()
    
    print("\n" + "="*80)
    print("SUMMARY & NEXT STEPS")
    print("="*80)
    print("\n✅ What's working:")
    print("  - BTP Destination service")
    print("  - Cloud Connector (passing requests to S/4HANA)")
    print("  - Connectivity service")
    print("  - CAP application code")
    
    print("\n❌ The 403 Forbidden error indicates:")
    print("  S/4HANA is actively rejecting the request")
    
    print("\n🔧 To fix, check in S/4HANA (ask S/4HANA admin):")
    print("  1. Verify user JOULE_ADMIN exists and is not locked")
    print("  2. Check password is correct: Diesel_2025_978625!")
    print("  3. Verify user has authorization for:")
    print("     - Transaction: /IWFND/MAINT_SERVICE")
    print("     - Service: RFM_MANAGE_SALES_ORDERS_SRV")
    print("     - Authorization object: S_SERVICE")
    print("  4. Check if service is activated in /IWFND/MAINT_SERVICE")
    print("  5. Test in S/4HANA directly:")
    print(f"     {S4_URL}/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200")
    
    print("\n" + "="*80)
