"""
Test script for scheduleMassChange action on BTP deployed app
Uses OAuth2 Client Credentials flow for authentication
"""
import requests
import json

# XSUAA credentials from cf env testJoule-srv
XSUAA_URL = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com"
CLIENT_ID = "sb-testJoule!t576522"
CLIENT_SECRET = "eebdae2b-5b43-4a3e-b0ae-b84c0470feb3$P2Smi6nkmIQ_Le3eRwIemcLSCyDPmM9-TbNtL6wCdig="

# Service URL on BTP
SERVICE_URL = "https://otb-joule-s4-sb4-2e2gsnau-joule-s4-sb4-testjoule-srv.cfapps.eu10-004.hana.ondemand.com/odata/v4/mass-change/scheduleMassChange"

def get_oauth_token():
    """Get OAuth2 token using client credentials flow"""
    print("🔐 Getting OAuth2 token from XSUAA...")
    
    token_url = f"{XSUAA_URL}/oauth/token"
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    token = response.json()['access_token']
    print(f"✅ Token obtained (length: {len(token)})\n")
    return token

def call_schedule_mass_change(token):
    """Call the scheduleMassChange action"""
    print("📞 Calling scheduleMassChange action...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test payload
    payload = {
        "filters": {
            "materialStartsWith": "J01AA0119J35002001",
            "plant": "142A",
            "salesOrg": "142",
            "creationDate": "2024-01-15"
        },
        "fieldsToUpdate": {
            "RequirementSegment": "PPCOMFR",
            "Plant": "140A",
            "StorageLocation": "ROD"
        }
    }
    
    print(f"Request payload:\n{json.dumps(payload, indent=2)}\n")
    
    response = requests.post(SERVICE_URL, headers=headers, json=payload)
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS! Response:")
        print(json.dumps(result, indent=2))
        
        # Check if it actually worked
        if result.get('status') == 'JOB_SCHEDULED':
            print("\n🎉 JOB SCHEDULED SUCCESSFULLY!")
            print(f"Job Name: {result.get('jobName')}")
            print(f"Message: {result.get('message')}")
            print(f"Fiori App Link: {result.get('fioriAppLink')}")
        elif result.get('status') == 'ERROR':
            print("\n❌ ERROR OCCURRED:")
            print(f"Message: {result.get('message')}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    return response

if __name__ == "__main__":
    print("=" * 80)
    print("Testing scheduleMassChange on BTP deployed app")
    print("=" * 80 + "\n")
    
    try:
        # Step 1: Get OAuth token
        token = get_oauth_token()
        
        # Step 2: Call the service
        response = call_schedule_mass_change(token)
        
        print("\n" + "=" * 80)
        print("Test completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
