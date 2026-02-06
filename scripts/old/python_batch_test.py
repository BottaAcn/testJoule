#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test batch OData request directly to S/4HANA with Basic Auth
Bypasses BTP Connectivity to isolate payload issues
"""
 
import requests
from requests.auth import HTTPBasicAuth
import json
 
# S/4HANA connection details (Public RISE endpoint from Postman docs)
BASE_URL = "https://vhotbsb4ci.rise.otb.net:44300"
ODATA_PATH = "/sap/opu/odata/sap/RFM_MANAGE_SALES_ORDERS_SRV/"
SAP_CLIENT = "200"
USERNAME = "JOULE_ADMIN"
PASSWORD = "Diesel_2025_978625!"
 
# Test data (from docs/postman.md)
FILTERS = {
    "materialStartsWith": "J01AA0119J35002001",
    "plant": "142A",
    "salesOrg": "142",
    "creationDate": "2026-01-13"
}
 
FIELDS_TO_UPDATE = {
    "RequirementSegment": "PPCOMFR",
    "Plant": "140A",
    "StorageLocation": "ROD"
}
 
 
def build_batch_payload(filters, fields):
    """
    Build complete batch payload with CRLF line endings
    Includes: changeset with MERGE + GET query
    """
    # Build JSON body for MERGE (compact, no indentation)
    merge_body = json.dumps({
        "RequirementSegment": fields["RequirementSegment"],
        "Plant": fields["Plant"],
        "StorageLocation": fields["StorageLocation"],
        "RFM_SD_ApplJobAction": "01",
        "InternalComment": "Mass Field Update from Joule",
        "SalesOrdItemIsSelected": "X",
        "SalesOrdItemsAreSelected": "X"
    })
   
    # Build GET filter
    material = filters["materialStartsWith"]
    plant = filters["plant"]
    sales_org = filters["salesOrg"]
    date = filters["creationDate"]
    get_filter = f"startswith(Material,%27{material}%27)%20and%20Plant%20eq%20%27{plant}%27%20and%20SalesDocumentDate%20eq%20datetime%27{date}T00%3a00%3a00%27%20and%20SalesOrganization%20eq%20%27{sales_org}%27"
   
    HOST = "vhotbsb4ci.rise.otb.net:44300"
   
    # Complete batch with changeset + GET
    payload = (
        # Changeset part (for MERGE/write operations)
        "--batch_Test01\r\n"
        "Content-Type: multipart/mixed; boundary=changeset_Ugo1\r\n"
        "\r\n"
        "--changeset_Ugo1\r\n"
        "Content-Type: application/http\r\n"
        "Content-Transfer-Encoding: binary\r\n"
        "\r\n"
        f"MERGE C_RFM_MaSaDoEditSlsOrdItm(SalesOrder='100001681',SalesOrderItem='000010')?sap-client={SAP_CLIENT} HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(merge_body)}\r\n"
        "Accept: application/json\r\n"
        "\r\n"
        f"{merge_body}\r\n"
        "--changeset_Ugo1--\r\n"
        "\r\n"
        # GET part (read operation, outside changeset)
        "--batch_Test01\r\n"
        "Content-Type: application/http\r\n"
        "Content-Transfer-Encoding: binary\r\n"
        "\r\n"
        f"GET C_RFM_MaSaDoEditSlsOrdItm?$top=1&sap-client={SAP_CLIENT}&$filter={get_filter} HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        "Accept: application/json\r\n"
        "\r\n"
        "\r\n"
        "--batch_Test01--"
    )
   
    return payload
 
 
def main():
    print("=" * 80)
    print("S/4HANA Batch OData Test - Direct Connection (Basic Auth)")
    print("=" * 80)
   
    # Step 1: Fetch CSRF token
    print("\n[1] Fetching CSRF token...")
    csrf_url = f"{BASE_URL}{ODATA_PATH}"
   
    csrf_response = requests.get(
        csrf_url,
        params={"sap-client": SAP_CLIENT},
        headers={
            "X-CSRF-Token": "Fetch",
            "Accept": "application/json"
        },
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        verify=False  # Disable SSL verification for internal system
    )
   
    print(f"   Status: {csrf_response.status_code}")
   
    if csrf_response.status_code != 200:
        print(f"   ERROR: Failed to fetch CSRF token")
        print(f"   Response: {csrf_response.text}")
        return
   
    csrf_token = csrf_response.headers.get("x-csrf-token")
    cookies = csrf_response.cookies  # Use cookies object instead of raw header
   
    print(f"   ✓ CSRF Token: {csrf_token}")
    print(f"   ✓ Cookies: {dict(cookies)}")
   
    # Step 2: Build batch payload
    print("\n[2] Building batch payload...")
    batch_payload = build_batch_payload(FILTERS, FIELDS_TO_UPDATE)
   
    print(f"   Payload size: {len(batch_payload)} bytes")
    print(f"   Has CRLF: {'YES' if '\\r\\n' in repr(batch_payload) else 'NO'}")
    print(f"\n   First 400 chars:")
    print(f"   {repr(batch_payload[:400])}\n")
    print(f"   Last 300 chars:")
    print(f"   {repr(batch_payload[-300:])}\n")
   
    # Step 3: First test a simple GET (no batch)
    print("\n[3] Testing simple GET first...")
    simple_url = f"{BASE_URL}{ODATA_PATH}C_RFM_MaSaDoEditSlsOrdItm"
   
    simple_response = requests.get(
        simple_url,
        params={"sap-client": SAP_CLIENT, "$top": "1"},
        headers={"Accept": "application/json"},
        cookies=cookies,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        verify=False
    )
    print(f"   Simple GET Status: {simple_response.status_code}")
    if simple_response.status_code == 200:
        print(f"   ✓ Simple GET works! Response: {simple_response.text[:300]}...")
    else:
        print(f"   Simple GET failed: {simple_response.text[:500]}")
   
    # Step 4: Send batch request
    print("\n[4] Sending batch request...")
    batch_url = f"{BASE_URL}{ODATA_PATH}$batch"
   
    batch_response = requests.post(
        batch_url,
        params={"sap-client": SAP_CLIENT},
        headers={
            "Content-Type": "multipart/mixed; boundary=batch_Test01",
            "Accept": "multipart/mixed",
            "X-CSRF-Token": csrf_token
        },
        cookies=cookies,  # Pass cookies object directly
        data=batch_payload.encode('utf-8'),  # Explicit UTF-8 encoding
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        verify=False
    )
   
    print(f"   Status: {batch_response.status_code}")
    print(f"   Content-Type: {batch_response.headers.get('content-type')}")
   
    # Step 5: Display response
    print("\n[5] Response Details:")
    print("=" * 80)
   
    if batch_response.status_code == 200 or batch_response.status_code == 202:
        print("✅ SUCCESS! Batch request accepted")
        print(f"\nResponse body ({len(batch_response.text)} bytes):")
        print(batch_response.text[:2000])  # First 2000 chars
    else:
        print(f"❌ ERROR {batch_response.status_code}")
        print(f"\nResponse body:")
        try:
            error_json = batch_response.json()
            print(json.dumps(error_json, indent=2))
        except:
            print(batch_response.text)
   
    print("\n" + "=" * 80)
   
    # Save payload to file for inspection
    with open("batch_payload_debug.txt", "w", encoding="utf-8") as f:
        f.write(batch_payload)
    print("\n📁 Payload saved to: batch_payload_debug.txt")
   
    # Save payload as hex dump for byte-level inspection
    with open("batch_payload_hex.txt", "w", encoding="utf-8") as f:
        hex_lines = []
        for i in range(0, min(len(batch_payload), 1000), 16):
            chunk = batch_payload[i:i+16]
            hex_part = " ".join(f"{ord(c):02x}" for c in chunk)
            ascii_part = "".join(c if 32 <= ord(c) < 127 else '.' for c in chunk)
            hex_lines.append(f"{i:04x}  {hex_part:<48}  {ascii_part}")
        f.write("\n".join(hex_lines))
    print("📁 Hex dump (first 1000 bytes) saved to: batch_payload_hex.txt")
 
 
if __name__ == "__main__":
    # Disable SSL warnings for internal systems
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
   
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()