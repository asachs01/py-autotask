#!/usr/bin/env python3
"""Test with Version endpoint which is simpler."""

import json
import os

import requests

# Get credentials
username = os.getenv("AUTOTASK_USERNAME")
integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
secret = os.getenv("AUTOTASK_SECRET")

# Get zone first
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

    # Test Version endpoint (simpler, no body needed)
    version_url = f"{api_url}/v1.0/Version"
    print(f"Testing Version endpoint: {version_url}")

    version_response = requests.get(version_url, headers=headers)
    print(f"Version response: {version_response.status_code}")

    if version_response.status_code == 200:
        print("✅ Authentication successful!")
        print(f"Version data: {version_response.json()}")
    else:
        print(f"❌ Version failed: {version_response.text[:500]}")
        print(f"Headers sent: {version_response.request.headers}")
else:
    print(f"❌ Zone detection failed")
