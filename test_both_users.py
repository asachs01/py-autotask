#!/usr/bin/env python3
"""
Test both API users to see if either is properly configured.
"""

import base64
import requests

def test_user(username, secret, integration_code, label):
    """Test a single user's credentials."""
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"Username: {username}")
    print(f"Integration Code: {integration_code[:10]}...")
    print('='*60)
    
    # 1. Test zone detection
    zone_url = f"https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user={username}"
    auth = (username, secret)
    headers = {"ApiIntegrationCode": integration_code}
    
    zone_resp = requests.get(zone_url, auth=auth, headers=headers)
    
    if zone_resp.status_code != 200:
        print(f"❌ Zone detection failed: {zone_resp.status_code}")
        return False
    
    zone_data = zone_resp.json()
    api_url = zone_data['url'].rstrip('/')
    print(f"✅ Zone: {zone_data.get('zoneName', 'Unknown')} - {api_url}")
    
    # 2. Test API access
    test_url = f"{api_url}/v1.0/Companies/query"
    headers['Content-Type'] = 'application/json'
    
    api_resp = requests.post(
        test_url,
        auth=auth,
        headers=headers,
        json={"maxRecords": 1}
    )
    
    if api_resp.status_code == 200:
        print(f"✅ API Access: SUCCESS!")
        return True
    else:
        print(f"❌ API Access: {api_resp.status_code}")
        return False

def main():
    print("🔍 Testing Both Autotask API Users")
    
    # User 1: From local .env file
    user1 = {
        'username': 'behhutgjzzn3zdl@wyretechnology.com',
        'secret': 'sH~63nY*@8dBkA9#$bL1S0m#q',
        'integration_code': 'FDTGHADJ2IPG7ZCLAJDVKNRGGZH',
        'label': 'Local .env User (behhutgjzzn3zdl)'
    }
    
    # User 2: From shell environment (if different)
    # Update these if you have another user to test
    user2 = {
        'username': 'fadvvai5ylrwk46@wyretechnology.com',
        'secret': '7Nx#z0*TAs5@~2KkY$b8q9$B3',
        'integration_code': 'C7GDLOXNSWC5T56W5YKT5EP75JQ',
        'label': 'Shell Env User (fadvvai5ylrwk46)'
    }
    
    # Test both users
    result1 = test_user(user1['username'], user1['secret'], 
                       user1['integration_code'], user1['label'])
    
    result2 = test_user(user2['username'], user2['secret'],
                       user2['integration_code'], user2['label'])
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"  {user1['label']}: {'✅ Working' if result1 else '❌ Not configured as API User'}")
    print(f"  {user2['label']}: {'✅ Working' if result2 else '❌ Not configured as API User'}")
    
    if not result1 and not result2:
        print("\n⚠️  Neither user is properly configured as an API User!")
        print("Create a new user with 'API User (system)' license type.")
    elif result1 or result2:
        working_user = user1 if result1 else user2
        print(f"\n✅ Use these credentials in your .env file:")
        print(f'AUTOTASK_USERNAME="{working_user["username"]}"')
        print(f'AUTOTASK_SECRET=\'{working_user["secret"]}\'')
        print(f'AUTOTASK_INTEGRATION_CODE="{working_user["integration_code"]}"')

if __name__ == "__main__":
    main()