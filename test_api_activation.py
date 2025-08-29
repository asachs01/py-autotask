#!/usr/bin/env python3
"""
Monitor Autotask API activation for newly created API users.
API users can take up to 5 minutes to activate after creation.
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from py_autotask import AsyncAutotaskClient
from py_autotask.types import AuthCredentials

async def test_api():
    """Test if API is accessible."""
    creds = AuthCredentials(
        username=os.getenv('AUTOTASK_USERNAME'),
        integration_code=os.getenv('AUTOTASK_INTEGRATION_CODE'),
        secret=os.getenv('AUTOTASK_SECRET')
    )
    
    try:
        client = await AsyncAutotaskClient.create(credentials=creds)
        async with client:
            # Zone detection works even before API is fully activated
            zone_info = client.auth.zone_info
            zone_works = zone_info is not None
            
            # This is what fails until API user is activated
            api_works = await client.test_connection_async()
            
            return zone_works, api_works
    except Exception as e:
        return False, False

async def monitor_activation():
    """Monitor API activation status."""
    print("🔍 Monitoring Autotask API activation...")
    print("⏱️  New API users can take up to 5 minutes to activate\n")
    
    start_time = datetime.now()
    timeout = start_time + timedelta(minutes=6)
    attempt = 0
    
    while datetime.now() < timeout:
        attempt += 1
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"Attempt #{attempt} (elapsed: {int(elapsed)}s)...", end=" ")
        
        zone_works, api_works = await test_api()
        
        if zone_works and api_works:
            print("✅ API is fully activated!")
            print(f"\n🎉 Success! Your API user is now active.")
            print(f"Total activation time: {int(elapsed)} seconds")
            return True
        elif zone_works and not api_works:
            print("⏳ Zone detection works, waiting for API activation...")
        else:
            print("❌ Connection failed")
        
        if not api_works and datetime.now() < timeout:
            await asyncio.sleep(30)  # Check every 30 seconds
    
    print("\n❌ Timeout reached. The API user may need manual configuration.")
    print("\nPlease verify in Autotask admin panel:")
    print("1. Navigate to Admin → Resources → Security Levels")
    print("2. Ensure your API user has 'API User (API-only)' security level")
    print("3. Check that the API tracking identifier is set")
    print("4. Verify the user is marked as Active")
    
    return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not all([os.getenv('AUTOTASK_USERNAME'), 
                os.getenv('AUTOTASK_INTEGRATION_CODE'),
                os.getenv('AUTOTASK_SECRET')]):
        print("❌ Missing environment variables!")
        print("Required: AUTOTASK_USERNAME, AUTOTASK_INTEGRATION_CODE, AUTOTASK_SECRET")
        exit(1)
    
    asyncio.run(monitor_activation())