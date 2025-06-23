# py-autotask User Guide

A comprehensive guide to using the py-autotask Python library for Autotask PSA integration.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Basic Operations](#basic-operations)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

Install py-autotask using pip:

```bash
pip install py-autotask
```

### Quick Start

```python
from py_autotask import AutotaskClient
from py_autotask.auth import AuthCredentials

# Set up authentication
credentials = AuthCredentials(
    username="your_username",
    integration_code="your_integration_code",
    secret="your_secret"
)

# Create client
client = AutotaskClient(credentials)

# Query some tickets
tickets = client.entities.tickets.query(max_records=5)
print(f"Found {len(tickets.items)} tickets")
```

## Authentication

### Setting Up Credentials

You'll need three pieces of information from your Autotask administrator:

1. **Username**: Your Autotask username
2. **Integration Code**: A unique code for your integration
3. **Secret**: API secret key

#### Method 1: Direct Credentials

```python
from py_autotask.auth import AuthCredentials

credentials = AuthCredentials(
    username="john.doe@company.com",
    integration_code="ABC123DEF456",
    secret="your-secret-key-here"
)
```

#### Method 2: Environment Variables

Set environment variables:

```bash
export AUTOTASK_USERNAME="john.doe@company.com"
export AUTOTASK_INTEGRATION_CODE="ABC123DEF456"
export AUTOTASK_SECRET="your-secret-key-here"
```

Then use them in your code:

```python
import os
from py_autotask.auth import AuthCredentials

credentials = AuthCredentials(
    username=os.getenv('AUTOTASK_USERNAME'),
    integration_code=os.getenv('AUTOTASK_INTEGRATION_CODE'),
    secret=os.getenv('AUTOTASK_SECRET')
)
```

#### Method 3: Configuration File

Create a config file `autotask_config.json`:

```json
{
    "username": "john.doe@company.com",
    "integration_code": "ABC123DEF456",
    "secret": "your-secret-key-here"
}
```

Load it in your code:

```python
import json
from py_autotask.auth import AuthCredentials

with open('autotask_config.json') as f:
    config = json.load(f)

credentials = AuthCredentials(**config)
```

### Testing Authentication

```python
try:
    client = AutotaskClient(credentials)
    zone_info = client.get_zone_info()
    print(f"Connected to: {zone_info.url}")
    print(f"Database type: {zone_info.data_base_type}")
except Exception as e:
    print(f"Authentication failed: {e}")
```

## Basic Operations

### Querying Data

#### Simple Queries

```python
# Get all active companies
companies = client.entities.companies.query(max_records=100)

# Get tickets created in the last 7 days
from py_autotask.types import QueryFilter, FilterOperation
from datetime import datetime, timedelta

week_ago = datetime.now() - timedelta(days=7)
filter_recent = QueryFilter(
    field="createDate",
    op=FilterOperation.GT,
    value=week_ago.strftime("%Y-%m-%d")
)

recent_tickets = client.entities.tickets.query(
    filters=[filter_recent],
    max_records=50
)
```

#### Advanced Filtering

```python
from py_autotask.types import QueryFilter, FilterOperation

# Multiple filters
filters = [
    QueryFilter(field="isActive", op=FilterOperation.EQ, value=True),
    QueryFilter(field="companyType", op=FilterOperation.EQ, value=1),
    QueryFilter(field="companyName", op=FilterOperation.CONTAINS, value="Tech")
]

tech_companies = client.entities.companies.query(
    filters=filters,
    include_fields=["id", "companyName", "phone", "city"],
    max_records=100
)

for company in tech_companies.items:
    print(f"{company['companyName']} - {company['city']}")
```

#### Field Selection

```python
# Only get specific fields to reduce bandwidth
tickets = client.entities.tickets.query(
    include_fields=["id", "title", "status", "priority"],
    max_records=100
)
```

### Creating Records

#### Create a Company

```python
# Basic company creation
new_company = client.entities.companies.create_company(
    company_name="Acme Corporation",
    company_type=1,  # Customer
    phone="555-123-4567",
    address1="123 Main Street",
    city="New York",
    state="NY",
    postal_code="10001",
    country="USA"
)

print(f"Created company with ID: {new_company.item_id}")
```

#### Create a Ticket

```python
# Create a support ticket
new_ticket = client.entities.tickets.create_ticket(
    title="Email server down",
    description="Users cannot access email",
    account_id=12345,  # Company ID
    priority=1,  # High priority
    status=1,    # New
    queue_id=5   # IT Support queue
)

print(f"Created ticket #{new_ticket.item_id}")
```

#### Create with Custom Fields

```python
# Create entity with custom fields
ticket_data = {
    "title": "Custom Ticket",
    "accountID": 12345,
    "description": "Ticket with custom fields",
    "customfield_12345": "Custom Value",  # Custom field
    "customfield_67890": 100             # Numeric custom field
}

new_ticket = client.create_entity("Tickets", **ticket_data)
```

### Updating Records

#### Simple Update

```python
# Update a ticket status
updated_ticket = client.update("Tickets", 12345, status=2, priority=2)
print(f"Updated ticket: {updated_ticket['title']}")
```

#### Specialized Updates

```python
# Update ticket status with note
client.entities.tickets.update_ticket_status(
    ticket_id=12345,
    status=2,  # In Progress
    note="Started working on this issue"
)

# Assign ticket to technician
client.entities.tickets.assign_ticket(
    ticket_id=12345,
    resource_id=67890,
    note="Assigned to John Doe"
)

# Update company address
client.entities.companies.update_company_address(
    company_id=12345,
    address1="456 Oak Street",
    city="Boston",
    state="MA",
    postal_code="02101"
)
```

### Deleting Records

```python
# Delete a record
success = client.delete("TicketNotes", 12345)
if success:
    print("Note deleted successfully")
else:
    print("Failed to delete note")
```

### Pagination

When dealing with large datasets, use pagination:

```python
# Process all tickets in pages
current_page = client.entities.tickets.query(max_records=100)

while current_page:
    print(f"Processing {len(current_page.items)} tickets...")
    
    for ticket in current_page.items:
        # Process each ticket
        print(f"Ticket {ticket['id']}: {ticket['title']}")
    
    # Get next page
    current_page = client.entities.tickets.get_next_page(current_page)

print("Finished processing all tickets")
```

## Advanced Features

### Batch Operations

Batch operations are much more efficient when working with multiple records.

#### Batch Create

```python
# Create multiple tickets at once
ticket_data = [
    {
        "title": "Issue 1",
        "accountID": 123,
        "description": "First issue description",
        "priority": 2
    },
    {
        "title": "Issue 2", 
        "accountID": 124,
        "description": "Second issue description",
        "priority": 1
    },
    {
        "title": "Issue 3",
        "accountID": 125,
        "description": "Third issue description",
        "priority": 3
    }
]

# Create all tickets in one batch
results = client.batch_create("Tickets", ticket_data)
print(f"Created {len(results)} tickets")

for result in results:
    print(f"Created ticket ID: {result.item_id}")
```

#### Batch Update

```python
# Update multiple tickets
updates = [
    {"id": 123, "status": 2, "priority": 1},
    {"id": 124, "status": 2, "priority": 2},
    {"id": 125, "status": 3, "priority": 1}
]

updated_tickets = client.batch_update("Tickets", updates)
print(f"Updated {len(updated_tickets)} tickets")
```

#### Batch Delete

```python
# Delete multiple records
ticket_ids = [123, 124, 125]
results = client.batch_delete("Tickets", ticket_ids)

successful_deletes = sum(results)
print(f"Successfully deleted {successful_deletes} out of {len(ticket_ids)} tickets")
```

### File Attachments

#### Upload Files

```python
# Upload a file to a ticket
attachment = client.attachments.upload_file(
    parent_type="Ticket",
    parent_id=12345,
    file_path="/path/to/document.pdf",
    title="Technical Documentation",
    description="Detailed technical specs for the issue"
)

print(f"Uploaded attachment: {attachment.file_name} ({attachment.file_size} bytes)")
```

#### Upload from Memory

```python
# Upload file data from memory
file_content = b"This is file content"
attachment = client.attachments.upload_from_data(
    parent_type="Ticket",
    parent_id=12345,
    file_data=file_content,
    filename="notes.txt",
    title="Quick Notes"
)
```

#### Download Files

```python
# Download an attachment
file_content = client.attachments.download_file(
    attachment_id=67890,
    output_path="/path/to/save/file.pdf"
)

# Or just get the content in memory
file_bytes = client.attachments.download_file(attachment_id=67890)
```

#### List Attachments

```python
# Get all attachments for a ticket
attachments = client.attachments.get_attachments_for_entity(
    parent_type="Ticket",
    parent_id=12345
)

for attachment in attachments:
    print(f"File: {attachment.file_name}")
    print(f"Size: {attachment.file_size} bytes")
    print(f"Type: {attachment.content_type}")
    print(f"Created: {attachment.created_date_time}")
    print("---")
```

#### Batch Upload

```python
# Upload multiple files at once
file_paths = [
    "/path/to/file1.pdf",
    "/path/to/file2.docx", 
    "/path/to/file3.png"
]

attachments = client.attachments.batch_upload(
    parent_type="Ticket",
    parent_id=12345,
    file_paths=file_paths
)

print(f"Uploaded {len(attachments)} files")
```

### Entity-Specific Operations

#### Working with Companies

```python
# Search companies by name
companies = client.entities.companies.search_companies_by_name(
    name="Acme",
    exact_match=False
)

# Get customer companies only
customers = client.entities.companies.get_customer_companies(active_only=True)

# Get companies by location
local_companies = client.entities.companies.get_companies_by_location(
    city="New York",
    state="NY"
)
```

#### Working with Tickets

```python
# Get tickets for a specific account
account_tickets = client.entities.tickets.get_tickets_by_account(
    account_id=12345,
    status_filter="open"  # Only open tickets
)

# Get tickets assigned to a resource
my_tickets = client.entities.tickets.get_tickets_by_resource(
    resource_id=67890,
    include_completed=False
)

# Add a note to a ticket
note = client.entities.tickets.add_ticket_note(
    ticket_id=12345,
    note="Customer called to provide additional information",
    note_type=1,  # General note
    title="Customer Update"
)
```

## Best Practices

### Performance Optimization

#### Use Batch Operations

```python
# Instead of individual operations
for item in large_dataset:
    client.create_entity("Tickets", **item)  # Slow!

# Use batch operations
client.batch_create("Tickets", large_dataset)  # Fast!
```

#### Limit Fields in Queries

```python
# Don't fetch all fields if you don't need them
tickets = client.entities.tickets.query(
    include_fields=["id", "title", "status"],  # Only what you need
    max_records=100
)
```

#### Use Pagination Efficiently

```python
# Process data in chunks to manage memory
def process_all_tickets():
    page = client.entities.tickets.query(max_records=100)
    
    while page:
        # Process current page
        for ticket in page.items:
            process_ticket(ticket)
        
        # Clear references to help garbage collection
        tickets_to_process = page.items
        page = client.entities.tickets.get_next_page(page)
        del tickets_to_process
```

### Error Handling

```python
from py_autotask.exceptions import (
    AutotaskAuthenticationError,
    AutotaskConnectionError,
    AutotaskValidationError,
    AutotaskAPIError
)

def safe_autotask_operation():
    try:
        # Your Autotask operations here
        tickets = client.entities.tickets.query()
        return tickets
        
    except AutotaskAuthenticationError:
        print("Authentication failed - check your credentials")
        return None
        
    except AutotaskConnectionError:
        print("Network error - check your internet connection")
        return None
        
    except AutotaskValidationError as e:
        print(f"Data validation error: {e}")
        return None
        
    except AutotaskAPIError as e:
        print(f"API error {e.status_code}: {e}")
        return None
```

### Logging

```python
import logging

# Enable debug logging to see API calls
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('py_autotask')
logger.setLevel(logging.INFO)
```

### Connection Management

```python
# Configure connection settings for better performance
from py_autotask.client import ClientConfig

config = ClientConfig(
    timeout=30,           # Request timeout
    max_retries=3,        # Retry failed requests
    pool_connections=10,  # Connection pool size
    pool_maxsize=20      # Max connections in pool
)

client = AutotaskClient(credentials, config=config)
```

## Common Use Cases

### Daily Ticket Report

```python
from datetime import datetime, timedelta
from py_autotask.types import QueryFilter, FilterOperation

def daily_ticket_report():
    # Get tickets created today
    today = datetime.now().strftime("%Y-%m-%d")
    
    filter_today = QueryFilter(
        field="createDate",
        op=FilterOperation.GE,
        value=today
    )
    
    tickets = client.entities.tickets.query(
        filters=[filter_today],
        include_fields=["id", "title", "accountID", "status", "priority"],
        max_records=500
    )
    
    print(f"Tickets created today: {len(tickets.items)}")
    
    # Group by priority
    by_priority = {}
    for ticket in tickets.items:
        priority = ticket.get('priority', 'Unknown')
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(ticket)
    
    for priority, ticket_list in by_priority.items():
        print(f"Priority {priority}: {len(ticket_list)} tickets")
```

### Customer Onboarding

```python
def onboard_new_customer(company_info, contact_info):
    # Create company
    company = client.entities.companies.create_company(
        company_name=company_info['name'],
        company_type=1,  # Customer
        phone=company_info['phone'],
        address1=company_info['address'],
        city=company_info['city'],
        state=company_info['state'],
        postal_code=company_info['zip']
    )
    
    print(f"Created company: {company.item_id}")
    
    # Create primary contact
    contact = client.create_entity("Contacts", 
        companyID=company.item_id,
        firstName=contact_info['first_name'],
        lastName=contact_info['last_name'],
        emailAddress=contact_info['email'],
        phone=contact_info['phone']
    )
    
    print(f"Created contact: {contact.item_id}")
    
    # Create welcome ticket
    welcome_ticket = client.entities.tickets.create_ticket(
        title="Welcome to our service!",
        description="New customer onboarding ticket",
        account_id=company.item_id,
        status=1,
        priority=3
    )
    
    print(f"Created welcome ticket: {welcome_ticket.item_id}")
    
    return {
        'company_id': company.item_id,
        'contact_id': contact.item_id,
        'ticket_id': welcome_ticket.item_id
    }
```

### Bulk Status Updates

```python
def close_resolved_tickets():
    # Find tickets that are resolved but not closed
    filters = [
        QueryFilter(field="status", op=FilterOperation.EQ, value=5),  # Resolved
    ]
    
    resolved_tickets = client.entities.tickets.query(
        filters=filters,
        include_fields=["id", "title"],
        max_records=100
    )
    
    if not resolved_tickets.items:
        print("No resolved tickets to close")
        return
    
    # Prepare batch update
    updates = []
    for ticket in resolved_tickets.items:
        updates.append({
            "id": ticket["id"],
            "status": 5  # Closed
        })
    
    # Perform batch update
    results = client.batch_update("Tickets", updates)
    print(f"Closed {len(results)} tickets")
```

### File Backup System

```python
import os
from pathlib import Path

def backup_ticket_attachments(ticket_id, backup_dir):
    # Create backup directory
    backup_path = Path(backup_dir) / f"ticket_{ticket_id}"
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Get all attachments for the ticket
    attachments = client.attachments.get_attachments_for_entity(
        parent_type="Ticket",
        parent_id=ticket_id
    )
    
    print(f"Found {len(attachments)} attachments for ticket {ticket_id}")
    
    # Download each attachment
    for attachment in attachments:
        file_path = backup_path / attachment.file_name
        
        try:
            client.attachments.download_file(
                attachment_id=attachment.id,
                output_path=str(file_path)
            )
            print(f"Downloaded: {attachment.file_name}")
            
        except Exception as e:
            print(f"Failed to download {attachment.file_name}: {e}")
    
    print(f"Backup completed in: {backup_path}")
```

## Troubleshooting

### Common Issues

#### Authentication Problems

```python
# Test your credentials
try:
    client = AutotaskClient(credentials)
    zone_info = client.get_zone_info()
    print("Authentication successful!")
except Exception as e:
    print(f"Authentication failed: {e}")
    # Check username, integration code, and secret
```

#### Network Issues

```python
# Add retry logic for network issues
import time
from py_autotask.exceptions import AutotaskConnectionError

def retry_operation(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except AutotaskConnectionError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Network error, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
```

#### Rate Limiting

```python
# Handle rate limiting gracefully
import time

def rate_limited_operation():
    try:
        return client.entities.tickets.query()
    except AutotaskAPIError as e:
        if e.status_code == 429:  # Too Many Requests
            print("Rate limited, waiting...")
            time.sleep(60)  # Wait 1 minute
            return client.entities.tickets.query()
        else:
            raise
```

#### Data Validation Issues

```python
# Validate data before sending
def create_ticket_safely(ticket_data):
    # Check required fields
    required_fields = ['title', 'accountID']
    for field in required_fields:
        if field not in ticket_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate data types
    if not isinstance(ticket_data['accountID'], int):
        raise ValueError("accountID must be an integer")
    
    # Create ticket
    return client.create_entity("Tickets", **ticket_data)
```

### Debug Mode

```python
# Enable detailed logging for debugging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# This will show all HTTP requests and responses
client = AutotaskClient(credentials)
```

### Performance Monitoring

```python
import time

def monitor_performance():
    start_time = time.time()
    
    # Your operation
    tickets = client.entities.tickets.query(max_records=100)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Query took {duration:.2f} seconds")
    print(f"Retrieved {len(tickets.items)} tickets")
    print(f"Rate: {len(tickets.items)/duration:.1f} tickets/second")
```

This user guide covers the most common scenarios and best practices for using py-autotask. For more advanced usage and complete API reference, see the [API Reference](API_REFERENCE.md). 