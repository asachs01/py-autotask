#!/usr/bin/env python3
"""Debug authentication issues with Autotask API."""

import os
import requests
import json

# Get credentials
username = os.getenv("AUTOTASK_USERNAME")
integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
secret = os.getenv("AUTOTASK_SECRET")

print(f"Username: {username}")
print(f"Integration Code: {integration_code[:10]}..." if integration_code else "Not set")
print(f"Secret: {'Set' if secret else 'Not set'}")

# Test zone detection first
zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={username}"
print(f"\nTesting zone detection: {zone_url}")

headers = {
    "Content-Type": "application/json",
    "ApiIntegrationCode": integration_code,
    "UserName": username,
    "Secret": secret,
}

response = requests.get(zone_url, headers=headers)
print(f"Zone detection response: {response.status_code}")
if response.status_code == 200:
    zone_data = response.json()
    print(f"Zone data: {json.dumps(zone_data, indent=2)}")
    api_url = zone_data['url'].rstrip('/')
    
    # Now test a simple query
    query_url = f"{api_url}/v1.0/Companies/query"
    print(f"\nTesting query: {query_url}")
    
    query_body = {
        "filter": [{"op": "gte", "field": "id", "value": 0}],
        "MaxRecords": 1
    }
    
    print(f"Query body: {json.dumps(query_body, indent=2)}")
    print(f"Headers: {json.dumps({k: v[:20] + '...' if len(v) > 20 else v for k, v in headers.items()}, indent=2)}")
    
    query_response = requests.post(query_url, headers=headers, json=query_body)
    print(f"Query response: {query_response.status_code}")
    
    if query_response.status_code == 200:
        print("✅ Authentication successful!")
        data = query_response.json()
        print(f"Response has {len(data.get('items', []))} items")
    else:
        print(f"❌ Query failed: {query_response.text[:500]}")
else:
    print(f"❌ Zone detection failed: {response.text[:500]}")