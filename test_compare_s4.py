"""
Test the deployed testS4Endpoints action via BTP
"""
import requests
import json

# BTP OAuth2 credentials
TOKEN_URL = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com/oauth/token"
CLIENT_ID = "sb-testJoule!t576522"
CLIENT_SECRET = "d588dc8b-910a-45aa-89ab-e7f18e0300d8$yluYROsM8_T7r3Tav153DVk77bhxSbryzo8FcTqMVSw="

# BTP service URL
SERVICE_URL = "https://otb-joule-s4-sb4-2e2gsnau-joule-s4-sb4-testjoule-srv.cfapps.eu10-004.hana.ondemand.com/odata/v4/mass-change/testS4Endpoints"

print("=" * 80)
print("Testing S/4HANA Endpoints Comparison")
print("=" * 80)

# Step 1: Get OAuth2 token
print("\n1️⃣  Getting OAuth2 token...")
token_response = requests.post(
    TOKEN_URL,
    data={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
)

if token_response.status_code != 200:
    print(f"❌ Failed to get token: {token_response.status_code}")
    print(token_response.text)
    exit(1)

access_token = token_response.json()['access_token']
print("✅ Token obtained")

# Step 2: Call testS4Endpoints action
print("\n2️⃣  Calling testS4Endpoints action on BTP...")
print(f"URL: {SERVICE_URL}")

response = requests.post(
    SERVICE_URL,
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    json={}  # Empty body for the action
)

print(f"\n📊 Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\n⏰ Timestamp: {result.get('timestamp')}")
    print(f"\n💡 Recommendation: {result.get('recommendation')}")
    
    print("\n" + "-" * 80)
    print("Endpoint Comparison:")
    print("-" * 80)
    
    for i, endpoint_result in enumerate(result.get('results', []), 1):
        status_icon = "✅" if endpoint_result['status'] == 'SUCCESS' else "❌"
        print(f"\n{status_icon} Test {i}: {endpoint_result['endpoint']}")
        print(f"   Status: {endpoint_result['status']}")
        
        if endpoint_result['status'] == 'SUCCESS':
            print(f"   Status Code: {endpoint_result.get('statusCode')}")
            print(f"   Content Length: {endpoint_result.get('contentLength')} bytes")
            print(f"   Preview: {endpoint_result.get('preview', '')[:150]}...")
        else:
            print(f"   Error: {endpoint_result.get('error')}")
    
    print("\n" + "=" * 80)
    
    # Determine which one works
    successful = [r for r in result.get('results', []) if r['status'] == 'SUCCESS']
    
    if successful:
        print("\n🎯 WORKING ENDPOINTS:")
        for r in successful:
            print(f"   ✅ {r['endpoint']}")
    else:
        print("\n❌ No endpoints working - both failed")
        
else:
    print(f"\n❌ Request failed: {response.status_code}")
    print(response.text)

print("\n" + "=" * 80)
