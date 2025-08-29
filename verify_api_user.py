#!/usr/bin/env python3
"""
Comprehensive verification script for Autotask API users.
Tests all possible authentication variations to identify the exact issue.
"""

import os
import base64
import requests
import json
from dotenv import load_dotenv

def test_auth_variation(username, secret, integration_code, header_name, api_url):
    """Test a specific authentication variation."""
    auth = (username, secret)
    headers = {
        header_name: integration_code,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{api_url}/v1.0/Companies/query",
            auth=auth,
            headers=headers,
            json={"maxRecords": 1},
            timeout=5
        )
        return response.status_code, response.headers.get('WWW-Authenticate', '')
    except Exception as e:
        return None, str(e)

def main():
    load_dotenv()
    
    # Test both sets of credentials if you have them
    credentials_sets = []
    
    # Current credentials
    if os.getenv('AUTOTASK_USERNAME'):
        credentials_sets.append({
            'name': 'Current User',
            'username': os.getenv('AUTOTASK_USERNAME'),
            'secret': os.getenv('AUTOTASK_SECRET'),
            'integration_code': os.getenv('AUTOTASK_INTEGRATION_CODE')
        })
    
    # Add backup/new credentials here if needed
    # credentials_sets.append({
    #     'name': 'New API User',
    #     'username': 'new_api_user@domain.com',
    #     'secret': 'new_secret',
    #     'integration_code': 'new_integration_code'
    # })
    
    # Header variations to test
    header_variations = [
        'ApiIntegrationCode',
        'ApiIntegrationcode',
        'APIIntegrationCode',
        'APIIntegrationcode',
        'apiintegrationcode',
        'Api-Integration-Code',
        'X-ApiIntegrationCode',
        'X-API-Integration-Code'
    ]
    
    print("🔍 Autotask API User Verification")
    print("=" * 60)
    
    for cred_set in credentials_sets:
        print(f"\n📧 Testing: {cred_set['name']}")
        print(f"   Username: {cred_set['username']}")
        print(f"   Integration Code: {cred_set['integration_code'][:10]}...")
        print("-" * 60)
        
        # First, test zone detection
        zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={cred_set['username']}"
        zone_resp = requests.get(
            zone_url,
            auth=(cred_set['username'], cred_set['secret']),
            headers={'ApiIntegrationCode': cred_set['integration_code']}
        )
        
        if zone_resp.status_code != 200:
            print(f"   ❌ Zone detection failed: {zone_resp.status_code}")
            continue
        
        zone_data = zone_resp.json()
        api_url = zone_data['url'].rstrip('/')
        print(f"   ✅ Zone detected: {zone_data.get('zoneName', 'Unknown')}")
        print(f"   📍 API URL: {api_url}")
        
        # Test all header variations
        print("\n   Testing header variations:")
        successful = []
        
        for header_name in header_variations:
            status, auth_header = test_auth_variation(
                cred_set['username'],
                cred_set['secret'],
                cred_set['integration_code'],
                header_name,
                api_url
            )
            
            if status == 200:
                print(f"   ✅ {header_name}: SUCCESS!")
                successful.append(header_name)
            elif status == 401:
                print(f"   ❌ {header_name}: 401 Unauthorized")
            else:
                print(f"   ⚠️  {header_name}: {status}")
        
        if successful:
            print(f"\n   🎉 Working headers: {', '.join(successful)}")
        else:
            print("\n   ❌ No working header variations found")
            print("\n   Possible issues:")
            print("   1. User is not configured as 'API User (system)' license")
            print("   2. API Tracking Identifier doesn't match Integration Code")
            print("   3. User is inactive or locked")
            print("   4. Security level is not 'API User (API-only)'")
            print("   5. Account-level API restrictions")
            
            # Try to get more info from the auth challenge
            print("\n   Authentication challenge details:")
            print(f"   Realm: {zone_data.get('zoneName', 'Unknown')}")
            print(f"   Zone CI: {zone_data.get('ci', 'Unknown')}")

if __name__ == "__main__":
    main()