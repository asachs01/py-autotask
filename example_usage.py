#!/usr/bin/env python3
"""
Example usage of the py-autotask SDK.
Shows how to authenticate and make API calls to Autotask.
"""

import asyncio
import os
from dotenv import load_dotenv
from py_autotask import AsyncAutotaskClient

async def main():
    # Load credentials from .env file
    load_dotenv(override=True)  # Override any shell environment variables
    
    # Check that credentials are loaded
    username = os.getenv("AUTOTASK_USERNAME")
    secret = os.getenv("AUTOTASK_SECRET")
    integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
    
    if not all([username, secret, integration_code]):
        print("❌ Missing credentials in .env file")
        print("Required environment variables:")
        print("  AUTOTASK_USERNAME")
        print("  AUTOTASK_SECRET")
        print("  AUTOTASK_INTEGRATION_CODE")
        return
    
    # Create client - will automatically detect zone
    client = await AsyncAutotaskClient.create(
        username=username,
        secret=secret,
        integration_code=integration_code
    )
    
    async with client:
        # Test connection
        connected = await client.test_connection_async()
        if connected:
            print("✅ Successfully connected to Autotask API!")
            
            # Get zone information
            zone_info = client.auth.zone_info
            if zone_info:
                print(f"Zone: {zone_info.zone_name}")
                print(f"API URL: {zone_info.url}")
            
            # The SDK is now properly authenticated and ready to use!
            # You can make API calls like:
            #
            # companies = await client.companies.query_async(...)
            # tickets = await client.tickets.query_async(...)
            # contacts = await client.contacts.query_async(...)
            #
            # See the SDK documentation for query format details
            
        else:
            print("❌ Failed to connect to Autotask API")
            print("Check your credentials in the .env file")

if __name__ == "__main__":
    asyncio.run(main())