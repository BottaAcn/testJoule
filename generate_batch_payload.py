#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate batch payload for debugging - no network connection needed
Exact replica of Node.js buildBatchPayload function
"""

import json

SAP_CLIENT = "200"

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
    """Build batch payload with CRLF line endings (exact replica of Node.js code)"""
    
    # Build GET query part
    material = filters["materialStartsWith"]
    plant = filters["plant"]
    sales_org = filters["salesOrg"]
    date = filters["creationDate"]
    
    get_query_lines = [
        f"GET C_RFM_MaSaDoEditSlsOrdItm?sap-client={SAP_CLIENT}&$top=1&$filter=startswith(Material,%27{material}%27)%20and%20Plant%20eq%20%27{plant}%27%20and%20SalesDocumentDate%20eq%20datetime%27{date}T00%3a00%3a00%27%20and%20SalesOrganization%20eq%20%27{sales_org}%27 HTTP/1.1",
        "sap-cancel-on-close: true",
        "sap-contextid-accept: header",
        "Accept: application/json",
        "Accept-Language: en",
        "DataServiceVersion: 2.0",
        "MaxDataServiceVersion: 2.0",
        "X-Requested-With: XMLHttpRequest",
        "sap-message-scope: BusinessObject"
    ]
    get_query = "\r\n".join(get_query_lines)
    
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
    
    # Build complete batch payload with CRLF
    payload_lines = [
        "--batch_Test01",
        "Content-Type: multipart/mixed; boundary=changeset_Ugo1",
        "",
        "--changeset_Ugo1",
        "Content-Type: application/http",
        "Content-Transfer-Encoding: binary",
        "",
        f"MERGE C_RFM_MaSaDoEditSlsOrdItm(SalesOrder='100001681',SalesOrderItem='000010')?sap-client={SAP_CLIENT} HTTP/1.1",
        "sap-contextid-accept: header",
        "Accept: application/json",
        "Accept-Language: en",
        "DataServiceVersion: 2.0",
        "MaxDataServiceVersion: 2.0",
        "X-Requested-With: XMLHttpRequest",
        "Content-Type: application/json",
        "sap-message-scope: BusinessObject",
        "",  # Blank line before body
        merge_body,
        "--changeset_Ugo1--",
        "",
        "--batch_Test01",
        "Content-Type: application/http",
        "Content-Transfer-Encoding: binary",
        "",
        get_query,
        "",  # Blank line after GET headers (GET has no body)
        "--batch_Test01--"
    ]
    
    return "\r\n".join(payload_lines)


def main():
    print("=" * 80)
    print("Batch Payload Generator - Exact Node.js Replica")
    print("=" * 80)
    
    # Generate payload
    batch_payload = build_batch_payload(FILTERS, FIELDS_TO_UPDATE)
    
    print(f"\n✓ Payload generated: {len(batch_payload)} bytes")
    print(f"✓ CRLF line endings: {'YES' if '\\r\\n' in repr(batch_payload) else 'NO'}")
    print(f"✓ Lines count: {batch_payload.count(chr(10)) + 1}")
    
    # Display payload sections
    print("\n" + "=" * 80)
    print("PAYLOAD PREVIEW:")
    print("=" * 80)
    
    lines = batch_payload.split("\r\n")
    for i, line in enumerate(lines[:15], 1):
        print(f"{i:2d}: {repr(line)}")
    
    if len(lines) > 30:
        print(f"... ({len(lines) - 30} lines omitted) ...")
    
    for i, line in enumerate(lines[-15:], len(lines) - 14):
        print(f"{i:2d}: {repr(line)}")
    
    # Save to file
    output_file = "batch_payload_generated.txt"
    with open(output_file, "w", encoding="utf-8", newline='') as f:
        f.write(batch_payload)
    
    print("\n" + "=" * 80)
    print(f"📁 Payload saved to: {output_file}")
    print("   Use this file to compare with Postman's payload")
    
    # Save hex dump
    hex_file = "batch_payload_generated_hex.txt"
    with open(hex_file, "w", encoding="utf-8") as f:
        f.write("Hex Dump (first 1000 bytes):\n")
        f.write("=" * 80 + "\n\n")
        
        for i in range(0, min(len(batch_payload), 1000), 16):
            chunk = batch_payload[i:i+16]
            hex_part = " ".join(f"{ord(c):02x}" for c in chunk)
            ascii_part = "".join(c if 32 <= ord(c) < 127 else '.' for c in chunk)
            f.write(f"{i:04x}  {hex_part:<48}  {ascii_part}\n")
        
        # Also show CRLF positions
        f.write("\n\n" + "=" * 80)
        f.write("\nCRLF Positions:\n")
        f.write("=" * 80 + "\n\n")
        
        pos = 0
        crlf_count = 0
        while pos < len(batch_payload):
            if batch_payload[pos:pos+2] == "\r\n":
                # Show context around CRLF
                start = max(0, pos - 20)
                end = min(len(batch_payload), pos + 22)
                context = batch_payload[start:end]
                f.write(f"CRLF #{crlf_count+1:2d} at byte {pos:4d}: {repr(context)}\n")
                crlf_count += 1
                pos += 2
            else:
                pos += 1
        
        f.write(f"\nTotal CRLFs found: {crlf_count}\n")
    
    print(f"📁 Hex dump saved to: {hex_file}")
    
    # Save statistics
    stats_file = "batch_payload_stats.txt"
    with open(stats_file, "w", encoding="utf-8") as f:
        f.write("Batch Payload Statistics\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total bytes: {len(batch_payload)}\n")
        f.write(f"Total lines: {len(lines)}\n")
        f.write(f"CRLF count: {batch_payload.count(chr(13) + chr(10))}\n")
        f.write(f"LF-only count: {batch_payload.count(chr(10)) - batch_payload.count(chr(13) + chr(10))}\n")
        f.write(f"\nBoundaries found:\n")
        f.write(f"  --batch_Test01 (start): {batch_payload.count('--batch_Test01')}\n")
        f.write(f"  --batch_Test01-- (end): {batch_payload.count('--batch_Test01--')}\n")
        f.write(f"  --changeset_Ugo1: {batch_payload.count('--changeset_Ugo1')}\n")
        f.write(f"  --changeset_Ugo1--: {batch_payload.count('--changeset_Ugo1--')}\n")
        
        f.write(f"\nContent headers:\n")
        f.write(f"  Content-Type: {batch_payload.count('Content-Type:')}\n")
        f.write(f"  Content-Transfer-Encoding: {batch_payload.count('Content-Transfer-Encoding:')}\n")
        
        f.write(f"\nHTTP methods:\n")
        f.write(f"  MERGE requests: {batch_payload.count('MERGE ')}\n")
        f.write(f"  GET requests: {batch_payload.count('GET ')}\n")
        
        f.write(f"\nJSON body:\n")
        f.write(f"  Start position: {batch_payload.find('{')}\n")
        f.write(f"  End position: {batch_payload.find('}')}\n")
        f.write(f"  Length: {batch_payload.find('}') - batch_payload.find('{') + 1}\n")
    
    print(f"📁 Statistics saved to: {stats_file}")
    
    print("\n" + "=" * 80)
    print("✅ DONE! Files ready for analysis:")
    print(f"   1. {output_file} - Full payload (UTF-8 text)")
    print(f"   2. {hex_file} - Hex dump with CRLF positions")
    print(f"   3. {stats_file} - Payload statistics")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
