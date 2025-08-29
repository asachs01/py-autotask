#!/usr/bin/env python3
"""
Diagnose Autotask API authentication issues.
Helps identify why zone detection works but API calls fail.
"""

import os
import base64
import requests
from dotenv import load_dotenv

def diagnose():
    """Run diagnostic tests to identify the issue."""
    load_dotenv()
    
    username = os.getenv('AUTOTASK_USERNAME')
    integration_code = os.getenv('AUTOTASK_INTEGRATION_CODE')
    secret = os.getenv('AUTOTASK_SECRET')
    
    print("🔍 Autotask API Diagnostics")
    print("=" * 50)
    
    # Test 1: Credentials loaded
    print("\n1. Checking credentials...")
    if not all([username, integration_code, secret]):
        print("   ❌ Missing credentials in environment")
        return
    print(f"   ✅ Username: {username}")
    print(f"   ✅ Integration Code: {integration_code[:10]}...")
    print(f"   ✅ Secret: {'*' * 10}")
    
    # Test 2: Zone detection (no special permissions needed)
    print("\n2. Testing zone detection (works for ANY user)...")
    zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={username}"
    
    zone_response = requests.get(
        zone_url,
        auth=(username, secret),
        headers={"ApiIntegrationCode": integration_code}
    )
    
    if zone_response.status_code == 200:
        zone_data = zone_response.json()
        print(f"   ✅ Zone detected: {zone_data.get('zoneName', 'Unknown')}")
        print(f"   ✅ API URL: {zone_data.get('url', 'Unknown')}")
        api_base = zone_data.get('url', '').rstrip('/')
    else:
        print(f"   ❌ Zone detection failed: {zone_response.status_code}")
        return
    
    # Test 3: API call (requires API User license)
    print("\n3. Testing API access (requires API User license)...")
    api_url = f"{api_base}/v1.0/Companies/query"
    
    api_response = requests.post(
        api_url,
        auth=(username, secret),
        headers={
            "ApiIntegrationCode": integration_code,
            "Content-Type": "application/json"
        },
        json={"maxRecords": 1}
    )
    
    if api_response.status_code == 200:
        print("   ✅ API access successful!")
        print("\n🎉 Your API user is properly configured!")
    elif api_response.status_code == 401:
        print("   ❌ API access denied (401)")
        print("\n📋 DIAGNOSIS: Zone detection works but API fails")
        print("\nThis means your credentials are valid, but the user is NOT")
        print("configured as an API User. This is the most common issue!")
        print("\n🔧 TO FIX THIS:")
        print("1. Log into Autotask")
        print("2. Go to: Admin → Resources")
        print("3. Find user:", username)
        print("4. Click Edit")
        print("5. On General tab, check:")
        print("   - License Type: Must be 'API User (system)'")
        print("   - NOT 'Full User' or any other type")
        print("6. On Security tab, check:")
        print("   - Security Level: Must be 'API User (API-only)'")
        print("   - NOT 'Full Access' or any other level")
        print("7. In API Tracking section:")
        print("   - API Tracking Identifier: Must be set")
        print("\n⚠️  IMPORTANT: If the user has a regular license,")
        print("you may need to CREATE A NEW USER with API User license")
        print("from the start. You cannot always convert a regular user.")
    else:
        print(f"   ❌ Unexpected error: {api_response.status_code}")
        print(f"   Response: {api_response.text[:200]}")
    
    # Additional diagnostic info
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"• Credentials present: ✅")
    print(f"• Zone detection: {'✅' if zone_response.status_code == 200 else '❌'}")
    print(f"• API access: {'✅' if api_response.status_code == 200 else '❌'}")
    
    if zone_response.status_code == 200 and api_response.status_code == 401:
        print("\n🚨 ACTION REQUIRED:")
        print("Your user account is NOT an API User.")
        print("You need to either:")
        print("1. Convert this user to API User license type (if possible)")
        print("2. Create a NEW user with 'API User (system)' license")

if __name__ == "__main__":
    diagnose()