#!/usr/bin/env python3
"""
Test Sequence: READ -> RITORNO -> READ -> ANDATA -> READ
Verifica il ciclo completo partendo da RITORNO
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
CLIENT_ID = "sb-testJoule!t576522"
CLIENT_SECRET = "6f32a36a-3882-4cd0-9430-a87e099878cf$i-k9re-OJROa1lbO9kkLdfQji4paoyB1_pvMlFwoUH8="
TOKEN_URL = "https://joule-s4-sb4-2e2gsnau.authentication.eu10.hana.ondemand.com/oauth/token"
SERVICE_URL = "https://otb-joule-s4-sb4-2e2gsnau-joule-s4-sb4-testjoule-srv.cfapps.eu10-004.hana.ondemand.com/odata/v4/mass-change"

def get_token():
    """Ottiene token OAuth2"""
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def read_orders(token, plant):
    """Legge ordini con filtro plant"""
    print(f"\n{'='*60}")
    print(f"READ - Plant={plant}")
    print(f"{'='*60}")
    
    body = {
        "filters": {
            "materialStartsWith": "J01AA0119J3",
            "plant": plant,
            "salesOrg": "142",
            "creationDate": "2026-01-13"
        }
    }
    
    response = requests.post(
        f"{SERVICE_URL}/readOrders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=body
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"Timestamp: {result.get('timestamp')}")
    print(f"Count: {result.get('count')}")
    if result.get('orders'):
        for order in result['orders']:
            print(f"  Order: {order.get('SalesOrder')} | Plant: {order.get('Plant')} | "
                  f"ReqSeg: {order.get('RequirementSegment')} | Storage: {order.get('StorageLocation')}")
    else:
        print("  Nessun ordine trovato")
    
    return result

def andata(token):
    """ANDATA: 142A -> 140A"""
    print(f"\n{'='*60}")
    print(f"ANDATA - Plant 142A -> 140A")
    print(f"{'='*60}")
    
    body = {
        "filters": {
            "materialStartsWith": "J01AA0119J3",
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
    
    response = requests.post(
        f"{SERVICE_URL}/scheduleMassChange",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=body
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"Job ID: {result.get('ID')}")
    print(f"Status: {result.get('status')}")
    print(f"Timestamp: {result.get('timestamp')}")
    
    return result

def ritorno(token):
    """RITORNO: 140A -> 142A"""
    print(f"\n{'='*60}")
    print(f"RITORNO - Plant 140A -> 142A")
    print(f"{'='*60}")
    
    body = {
        "filters": {
            "materialStartsWith": "J01AA0119J3",
            "plant": "140A",
            "salesOrg": "142",
            "creationDate": "2026-01-13"
        },
        "fieldsToUpdate": {
            "RequirementSegment": "PPCOM99",
            "Plant": "142A",
            "StorageLocation": "AFS"
        }
    }
    
    response = requests.post(
        f"{SERVICE_URL}/reverseMassChange",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=body
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"Job ID: {result.get('ID')}")
    print(f"Status: {result.get('status')}")
    print(f"Timestamp: {result.get('timestamp')}")
    
    return result

def main():
    print(f"\n{'#'*60}")
    print(f"# TEST SEQUENCE: READ -> RITORNO -> READ -> ANDATA -> READ")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    # Ottieni token
    print("\nOttengo token OAuth2...")
    token = get_token()
    print("✓ Token ottenuto")
    
    # 1. READ iniziale (dovrebbe trovare ordine in 140A dopo precedente ANDATA)
    read_orders(token, "140A")
    time.sleep(2)
    
    # 2. RITORNO (140A -> 142A)
    ritorno(token)
    print("\nAttendo 5 secondi per il completamento del job...")
    time.sleep(5)
    
    # 3. READ dopo RITORNO (dovrebbe trovare ordine in 142A)
    read_orders(token, "142A")
    time.sleep(2)
    
    # 4. ANDATA (142A -> 140A)
    andata(token)
    print("\nAttendo 5 secondi per il completamento del job...")
    time.sleep(5)
    
    # 5. READ finale (dovrebbe trovare ordine in 140A)
    read_orders(token, "140A")
    
    print(f"\n{'#'*60}")
    print(f"# TEST COMPLETATO")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
