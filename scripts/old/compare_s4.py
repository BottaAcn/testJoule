"""
Compare two S4 endpoints
"""
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import hashlib
 
# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
 
USERNAME = "JOULE_ADMIN"
PASSWORD = "Diesel_2025_978625!"
 
# Two endpoints to test
ENDPOINTS = [
    {
        "name": "Internal (s4-sb4:44380)",
        "url": "http://s4-sb4:44380/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200",
        "verify": False
    },
    {
        "name": "External (vhotbsb4ci:44300)",
        "url": "https://vhotbsb4ci.rise.otb.net:44300/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/$metadata?sap-client=200",
        "verify": False
    }
]
 
def test_endpoint(endpoint):
    """Test a single endpoint"""
    print(f"\n{'='*80}")
    print(f"Testing: {endpoint['name']}")
    print(f"URL: {endpoint['url']}")
    print(f"{'='*80}")
   
    try:
        response = requests.get(
            endpoint['url'],
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers={'Accept': 'application/xml'},
            verify=endpoint['verify'],
            timeout=10
        )
       
        print(f"✅ Status Code: {response.status_code}")
        print(f"📏 Content Length: {len(response.text)} bytes")
        print(f"📄 Content-Type: {response.headers.get('content-type')}")
       
        # Calculate hash of content
        content_hash = hashlib.md5(response.text.encode()).hexdigest()
        print(f"🔐 MD5 Hash: {content_hash}")
       
        if response.status_code == 200:
            # Show first 500 chars
            print(f"\n📝 First 500 characters:")
            print("-" * 80)
            print(response.text[:500])
            print("...")
           
            return {
                'success': True,
                'status': response.status_code,
                'length': len(response.text),
                'hash': content_hash,
                'content': response.text
            }
        else:
            print(f"\n❌ Error: {response.text[:500]}")
            return {
                'success': False,
                'status': response.status_code,
                'error': response.text[:500]
            }
           
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
 
if __name__ == "__main__":
    print("🚀 Testing S4 Endpoints")
    print("="*80)
    print(f"Username: {USERNAME}")
    print(f"Client: 200")
   
    results = []
    for endpoint in ENDPOINTS:
        result = test_endpoint(endpoint)
        result['name'] = endpoint['name']
        results.append(result)
   
    # Compare results
    print("\n\n" + "="*80)
    print("📊 COMPARISON")
    print("="*80)
   
    successful = [r for r in results if r.get('success')]
   
    if len(successful) >= 2:
        if successful[0]['hash'] == successful[1]['hash']:
            print("✅ Both endpoints return IDENTICAL content!")
            print(f"   Hash: {successful[0]['hash']}")
            print(f"   Length: {successful[0]['length']} bytes")
        else:
            print("⚠️  Endpoints return DIFFERENT content!")
            for r in successful:
                print(f"   {r['name']}: {r['hash']} ({r['length']} bytes)")
    else:
        print("\n❌ Not all endpoints successful:")
        for r in results:
            status = "✅" if r.get('success') else "❌"
            print(f"   {status} {r['name']}: {r.get('status', 'Failed')}")
   
    print("\n" + "="*80)
    print("✅ Test completed")