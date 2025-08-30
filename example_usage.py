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
    load_dotenv()
    
    # Create client - will automatically detect zone
    client = await AsyncAutotaskClient.create()
    
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
            
            # Example: Query companies
            companies = await client.companies.query_async({
                "filter": [
                    {"field": "isActive", "op": "eq", "value": True}
                ],
                "maxRecords": 5
            })
            
            print(f"\nFound {len(companies)} active companies")
            for company in companies:
                print(f"  - {company.companyName}")
            
            # Example: Get a specific ticket (if you know the ID)
            # ticket = await client.tickets.get_async(12345)
            # print(f"Ticket: {ticket.title}")
            
        else:
            print("❌ Failed to connect to Autotask API")
            print("Check your credentials in the .env file")

if __name__ == "__main__":
    asyncio.run(main())