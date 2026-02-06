#!/usr/bin/env python3
"""
Test deployed CAP service on BTP
"""
import requests
import json

# OAuth2 credentials from cf env testJoule-srv
CLIENT_ID = "sb-testJoule!t576522"
CLIENT_SECRET = "6f32a36a-3882-4cd0-9430-a87e099878cf$i-k9re-OJROa1lbO9kkLdfQji4paoyB1_pvMlFwoUH8="
TOKEN_URL = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com/oauth/token"

# Service URL (diretto a srv, senza approuter)
SERVICE_URL = "https://otb-joule-s4-sb4-2e2gsnau-joule-s4-sb4-testjoule-srv.cfapps.eu10-004.hana.ondemand.com/odata/v4/mass-change/scheduleMassChange"

def get_oauth_token():
    """Get OAuth2 access token"""
    print("🔐 Getting OAuth2 token...")
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    
    token = response.json()['access_token']
    print(f"✅ Token obtained (length: {len(token)} chars)")
    return token

def test_schedule_mass_change(token):
    """Test scheduleMassChange action"""
    print("\n📡 Calling scheduleMassChange...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Payload come da meeting (ANDATA values)
    payload = {
        "filters": {
            "materialStartsWith": "J01AA0119J35002001",
            "plant": "142A",
            "salesOrg": "142",
            "creationDate": "2026-01-13"
        },
        "fieldsToUpdate": {
            "RequirementSegment": "PPCOMFR",
            "Plant": "140A",
            "StorageLocation": "ROD"
        }
    }
    
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(SERVICE_URL, headers=headers, json=payload)
    
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"📄 Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    return response

if __name__ == '__main__':
    try:
        # Step 1: Get OAuth token
        token = get_oauth_token()
        
        # Step 2: Test scheduleMassChange
        response = test_schedule_mass_change(token)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Service is working")
        else:
            print(f"\n❌ FAILED with status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
