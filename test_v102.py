#!/usr/bin/env python3
"""Test v1.0.2 release with real API calls"""

import asyncio
import os
from dotenv import load_dotenv
from py_autotask import AutotaskClient
from py_autotask.auth import AutotaskAuth
from py_autotask.types import AuthCredentials

# Load environment variables
load_dotenv()

async def test_api():
    """Test various API endpoints"""
    
    # Create credentials
    credentials = AuthCredentials(
        username=os.getenv('AUTOTASK_USERNAME'),
        secret=os.getenv('AUTOTASK_SECRET'),
        integration_code=os.getenv('AUTOTASK_INTEGRATION_CODE'),
        api_url=None  # Will auto-detect zone
    )
    
    # Initialize auth
    auth = AutotaskAuth(credentials=credentials)
    
    # Initialize client
    client = AutotaskClient(auth=auth)
    
    print("Testing py-autotask v1.0.2...")
    print("=" * 50)
    
    try:
        # Test 1: Get Companies
        print("\n1. Testing Companies endpoint...")
        companies = await client.get_companies(max_records=5)
        print(f"   ✓ Retrieved {len(companies)} companies")
        if companies:
            print(f"   First company: {companies[0].get('companyName', 'N/A')}")
        
        # Test 2: Get Contacts
        print("\n2. Testing Contacts endpoint...")
        contacts = await client.get_contacts(max_records=5)
        print(f"   ✓ Retrieved {len(contacts)} contacts")
        if contacts:
            first_contact = contacts[0]
            print(f"   First contact: {first_contact.get('firstName', '')} {first_contact.get('lastName', '')}")
        
        # Test 3: Get Tickets
        print("\n3. Testing Tickets endpoint...")
        tickets = await client.get_tickets(max_records=5)
        print(f"   ✓ Retrieved {len(tickets)} tickets")
        if tickets:
            print(f"   First ticket: #{tickets[0].get('ticketNumber', 'N/A')} - {tickets[0].get('title', 'N/A')}")
        
        # Test 4: Get Projects
        print("\n4. Testing Projects endpoint...")
        projects = await client.get_projects(max_records=5)
        print(f"   ✓ Retrieved {len(projects)} projects")
        if projects:
            print(f"   First project: {projects[0].get('projectName', 'N/A')}")
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("Authentication and API access working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the client
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_api())