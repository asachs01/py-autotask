#!/usr/bin/env python3
"""
Test Autotask API using ONLY the local .env file values,
bypassing any shell environment variables.
"""

import re
import base64
import requests

def parse_local_env():
    """Parse the local .env file directly, bypassing shell environment."""
    env_vars = {}
    
    # Read the local .env file
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse export statements
                if line.startswith('export '):
                    line = line[7:]  # Remove 'export '
                
                # Parse KEY=VALUE or KEY="VALUE" or KEY='VALUE'
                match = re.match(r'^([A-Z_]+)=(["\']?)(.+?)\2$', line)
                if match:
                    key = match.group(1)
                    value = match.group(3)
                    env_vars[key] = value
                    print(f"Parsed from .env: {key} = {repr(value)}")
    
    return env_vars

def test_api(username, secret, integration_code):
    """Test the API with the given credentials."""
    print("\n" + "="*60)
    print("Testing with LOCAL .env credentials:")
    print(f"Username: {username}")
    print(f"Secret: {repr(secret)}")
    print(f"Integration Code: {integration_code}")
    print("="*60)
    
    # Test zone detection
    print("\n1. Testing zone detection...")
    zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={username}"
    
    # Create auth header manually
    auth_string = f"{username}:{secret}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "ApiIntegrationCode": integration_code
    }
    
    print(f"   Zone URL: {zone_url}")
    print(f"   Auth header (first 20 chars): Basic {auth_b64[:20]}...")
    
    zone_resp = requests.get(zone_url, headers=headers)
    
    if zone_resp.status_code == 200:
        zone_data = zone_resp.json()
        print(f"   ✅ Zone detected: {zone_data.get('zoneName', 'Unknown')}")
        print(f"   API URL: {zone_data.get('url', 'Unknown')}")
        api_url = zone_data.get('url', '').rstrip('/')
    else:
        print(f"   ❌ Zone detection failed: {zone_resp.status_code}")
        print(f"   Response: {zone_resp.text[:200]}")
        return
    
    # Test API access
    print("\n2. Testing API access...")
    test_url = f"{api_url}/v1.0/Companies/query"
    
    headers['Content-Type'] = 'application/json'
    
    print(f"   API URL: {test_url}")
    print(f"   Headers:")
    for k, v in headers.items():
        if k == 'Authorization':
            print(f"     {k}: {v[:30]}...")
        else:
            print(f"     {k}: {v}")
    
    api_resp = requests.post(
        test_url,
        headers=headers,
        json={"maxRecords": 1}
    )
    
    print(f"\n   Response Status: {api_resp.status_code}")
    
    if api_resp.status_code == 200:
        print("   ✅ API access successful!")
        print("\n🎉 SUCCESS! The API user is properly configured!")
    elif api_resp.status_code == 401:
        print("   ❌ API access denied (401)")
        print("\n   This means the user is not configured as an API User.")
        print("   The user needs 'API User (system)' license type.")
    else:
        print(f"   ⚠️  Unexpected status: {api_resp.status_code}")
        print(f"   Response: {api_resp.text[:200]}")

def main():
    print("🔍 Testing Autotask API with LOCAL .env file only")
    print("   (Ignoring any shell environment variables)")
    print()
    
    # Parse local .env file
    env_vars = parse_local_env()
    
    # Extract credentials
    username = env_vars.get('AUTOTASK_USERNAME', '')
    secret = env_vars.get('AUTOTASK_SECRET', '')
    integration_code = env_vars.get('AUTOTASK_INTEGRATION_CODE', '')
    
    if not all([username, secret, integration_code]):
        print("\n❌ Missing credentials in local .env file!")
        print(f"   Username: {'✅' if username else '❌'}")
        print(f"   Secret: {'✅' if secret else '❌'}")
        print(f"   Integration Code: {'✅' if integration_code else '❌'}")
        return
    
    # Test API
    test_api(username, secret, integration_code)

if __name__ == "__main__":
    main()