#!/usr/bin/env python3
"""Debug what payload the SDK is sending."""

import json
import logging
import os

from py_autotask import AutotaskClient
from py_autotask.types import QueryFilter, QueryRequest

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Get credentials from environment
username = os.getenv("AUTOTASK_USERNAME")
integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
secret = os.getenv("AUTOTASK_SECRET")

# Create a QueryRequest manually to see what gets sent
query_request = QueryRequest()
query_request.filter = [QueryFilter(op="gte", field="id", value=0)]
query_request.max_records = 2

print("QueryRequest object:")
print(f"  filter: {query_request.filter}")
print(f"  max_records: {query_request.max_records}")

# Convert to dict to see what would be sent
payload = query_request.model_dump(exclude_unset=True, by_alias=True)
print("\nPayload that would be sent:")
print(json.dumps(payload, indent=2))

# Now test with raw request to see what works
import requests

# Get zone
zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={username}"
headers = {
    "Content-Type": "application/json",
    "ApiIntegrationCode": integration_code,
    "UserName": username,
    "Secret": secret,
}

response = requests.get(zone_url, headers=headers)
if response.status_code == 200:
    zone_data = response.json()
    api_url = zone_data["url"].rstrip("/")

    # Test with the exact payload the SDK would send
    query_url = f"{api_url}/v1.0/Companies/query"
    print(f"\nTesting with SDK payload at: {query_url}")

    response = requests.post(query_url, headers=headers, json=payload)
    print(f"Response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
