import requests
from requests.auth import HTTPBasicAuth

# RISE S/4HANA URL (pubblico)
url = "https://vhotbsb4ci.rise.otb.net:44300/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200"
user = "JOULE_ADMIN"
password = "Diesel_2025_978625!"

print("=" * 80)
print("Testing RISE S/4HANA Service")
print("=" * 80)
print(f"\n🔗 URL: {url}")
print(f"👤 User: {user}")
print(f"🔑 Password: {'*' * len(password)}")
print("\n" + "=" * 80)

try:
    print("\n📡 Sending GET request to $metadata endpoint...")
    
    response = requests.get(
        url,
        auth=HTTPBasicAuth(user, password),
        timeout=30,
        verify=True  # Verifica SSL certificate
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📋 Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"📏 Content Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Service is available and accessible!")
        print("\n📄 First 500 characters of metadata:")
        print("-" * 80)
        print(response.text[:500])
        print("-" * 80)
        
        # Check if it's valid XML
        if '<?xml' in response.text and 'edmx:Edmx' in response.text:
            print("\n✅ Valid OData metadata XML received!")
            
            # Extract some key info
            if 'RFM_MASS_CHANGE' in response.text:
                print("✅ RFM_MASS_CHANGE entity found in metadata")
            if 'FunctionImport' in response.text:
                print("✅ Function imports found in metadata")
                
    elif response.status_code == 401:
        print("\n❌ AUTHENTICATION FAILED (401 Unauthorized)")
        print("   Check username/password")
        
    elif response.status_code == 403:
        print("\n❌ FORBIDDEN (403)")
        print("   Authentication OK but service not available/authorized")
        print("\n📄 Response body:")
        print(response.text[:500])
        
    elif response.status_code == 404:
        print("\n❌ NOT FOUND (404)")
        print("   Service path doesn't exist or service not activated")
        
    else:
        print(f"\n⚠️ Unexpected status code: {response.status_code}")
        print("\n📄 Response body:")
        print(response.text[:500])
        
except requests.exceptions.SSLError as e:
    print(f"\n❌ SSL Certificate Error: {e}")
    print("\nℹ️  If using self-signed certificate, you can bypass with verify=False")
    
except requests.exceptions.Timeout:
    print("\n❌ Request timed out (30 seconds)")
    print("   Server might be unreachable or very slow")
    
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Connection Error: {e}")
    print("   Check if server is reachable from your network")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
