#!/usr/bin/env python3
"""Quick test of the new API user."""

import requests
import time

# New credentials
USERNAME = 'cv7opkumxrj3chl@wyretechnology.com'
SECRET = 'W@b08M~e*5fJ4sT#H2$n~i3Qp'
INTEGRATION_CODE = 'FDTGHADJ2IPG7ZCLAJDVKNRGGZH'

print("🔍 Testing new API user...")
print(f"Username: {USERNAME}")
print(f"Integration Code: {INTEGRATION_CODE[:10]}...")
print("\nWaiting for potential activation delay (up to 5 minutes)...")

for i in range(10):
    print(f"\nAttempt {i+1}/10:", end=" ")
    
    # Test zone detection
    zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={USERNAME}"
    zone_resp = requests.get(
        zone_url,
        auth=(USERNAME, SECRET),
        headers={"ApiIntegrationCode": INTEGRATION_CODE},
        timeout=5
    )
    
    if zone_resp.status_code != 200:
        print(f"Zone detection failed: {zone_resp.status_code}")
        time.sleep(30)
        continue
    
    zone_data = zone_resp.json()
    api_url = zone_data['url'].rstrip('/')
    
    # Test API access
    test_url = f"{api_url}/v1.0/Companies/query"
    api_resp = requests.post(
        test_url,
        auth=(USERNAME, SECRET),
        headers={
            "ApiIntegrationCode": INTEGRATION_CODE,
            "Content-Type": "application/json"
        },
        json={"maxRecords": 1},
        timeout=5
    )
    
    if api_resp.status_code == 200:
        print("✅ SUCCESS! API is working!")
        print("\n🎉 The new user is properly configured!")
        break
    else:
        print(f"API returned {api_resp.status_code} - waiting 30 seconds...")
        if i < 9:
            time.sleep(30)
else:
    print("\n❌ After 5 minutes, the API still returns 401.")
    print("\nThe user is NOT configured as 'API User (system)' license type.")
    print("\nIn Autotask, verify:")
    print("1. License Type = 'API User (system)' (NOT 'Full User')")
    print("2. Security Level = 'API User (API-only)'")
    print("3. Status = Active")
    print("4. API Tracking Identifier is set")