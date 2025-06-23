# py-autotask API Reference

Complete API reference for the py-autotask library.

## Table of Contents

- [Client](#client)
- [Authentication](#authentication)
- [Entity Management](#entity-management)
- [Query Operations](#query-operations)
- [Batch Operations](#batch-operations)
- [File Attachments](#file-attachments)
- [CLI Interface](#cli-interface)
- [Types](#types)
- [Exceptions](#exceptions)

## Client

### AutotaskClient

The main client class for interacting with the Autotask REST API.

```python
from py_autotask import AutotaskClient
from py_autotask.auth import AuthCredentials

credentials = AuthCredentials(
    username="your_username",
    integration_code="your_integration_code",
    secret="your_secret"
)

client = AutotaskClient(credentials)
```

#### Constructor

```python
AutotaskClient(credentials: AuthCredentials, config: Optional[ClientConfig] = None)
```

**Parameters:**
- `credentials` (AuthCredentials): Authentication credentials
- `config` (ClientConfig, optional): Client configuration options

#### Core Methods

##### get_zone_info()
```python
get_zone_info() -> ZoneInfo
```
Retrieves zone information for the authenticated user.

**Returns:** ZoneInfo object containing API URL and database type.

##### get_entity_metadata(entity: str)
```python
get_entity_metadata(entity: str) -> EntityMetadata
```
Gets metadata for a specific entity type.

**Parameters:**
- `entity` (str): Entity name (e.g., "Companies", "Tickets")

**Returns:** EntityMetadata with entity capabilities and field information.

##### get_field_metadata(entity: str)
```python
get_field_metadata(entity: str) -> List[FieldMetadata]
```
Gets field metadata for a specific entity.

**Parameters:**
- `entity` (str): Entity name

**Returns:** List of FieldMetadata objects.

##### query(entity: str, **kwargs)
```python
query(
    entity: str,
    filters: Optional[List[QueryFilter]] = None,
    include_fields: Optional[List[str]] = None,
    max_records: int = 500
) -> QueryResponse
```
Queries entities with optional filtering.

**Parameters:**
- `entity` (str): Entity name to query
- `filters` (List[QueryFilter], optional): Query filters
- `include_fields` (List[str], optional): Fields to include in response
- `max_records` (int): Maximum records to return (default: 500)

**Returns:** QueryResponse with items and pagination details.

##### get(entity: str, entity_id: int)
```python
get(entity: str, entity_id: int) -> Dict[str, Any]
```
Retrieves a single entity by ID.

**Parameters:**
- `entity` (str): Entity name
- `entity_id` (int): Entity ID

**Returns:** Entity data as dictionary.

##### create_entity(entity: str, **data)
```python
create_entity(entity: str, **data) -> CreateResponse
```
Creates a new entity.

**Parameters:**
- `entity` (str): Entity name
- `**data`: Entity field values

**Returns:** CreateResponse with created entity ID.

##### update(entity: str, entity_id: int, **data)
```python
update(entity: str, entity_id: int, **data) -> Dict[str, Any]
```
Updates an existing entity.

**Parameters:**
- `entity` (str): Entity name
- `entity_id` (int): Entity ID
- `**data`: Fields to update

**Returns:** Updated entity data.

##### delete(entity: str, entity_id: int)
```python
delete(entity: str, entity_id: int) -> bool
```
Deletes an entity.

**Parameters:**
- `entity` (str): Entity name
- `entity_id` (int): Entity ID

**Returns:** True if successful, False otherwise.

#### Batch Operations

##### batch_create(entity: str, entities_data: List[EntityDict], batch_size: int = 200)
```python
batch_create(
    entity: str,
    entities_data: List[EntityDict],
    batch_size: int = 200
) -> List[CreateResponse]
```
Creates multiple entities in batches.

**Parameters:**
- `entity` (str): Entity name
- `entities_data` (List[EntityDict]): List of entity data dictionaries
- `batch_size` (int): Maximum entities per batch (default: 200)

**Returns:** List of CreateResponse objects.

##### batch_update(entity: str, entities_data: List[EntityDict], batch_size: int = 200)
```python
batch_update(
    entity: str,
    entities_data: List[EntityDict],
    batch_size: int = 200
) -> List[Dict[str, Any]]
```
Updates multiple entities in batches.

**Parameters:**
- `entity` (str): Entity name
- `entities_data` (List[EntityDict]): List of entity data with IDs
- `batch_size` (int): Maximum entities per batch (default: 200)

**Returns:** List of updated entity data.

##### batch_delete(entity: str, entity_ids: List[int], batch_size: int = 200)
```python
batch_delete(
    entity: str,
    entity_ids: List[int],
    batch_size: int = 200
) -> List[bool]
```
Deletes multiple entities in batches.

**Parameters:**
- `entity` (str): Entity name
- `entity_ids` (List[int]): List of entity IDs to delete
- `batch_size` (int): Maximum entities per batch (default: 200)

**Returns:** List of success indicators.

#### Properties

##### entities
```python
@property
entities -> EntityManager
```
Access to entity-specific operations through the EntityManager.

##### attachments
```python
@property
attachments -> AttachmentsEntity
```
Direct access to attachments entity operations.

##### time_entries
```python
@property
time_entries -> TimeEntriesEntity
```
Direct access to time entries entity operations.

## Authentication

### AuthCredentials

Authentication credentials for the Autotask API.

```python
from py_autotask.auth import AuthCredentials

credentials = AuthCredentials(
    username="your_username",
    integration_code="your_integration_code",
    secret="your_secret",
    api_url="https://api.autotask.net"  # Optional
)
```

#### Constructor Parameters

- `username` (str): Autotask username
- `integration_code` (str): Integration code from Autotask
- `secret` (str): API secret key
- `api_url` (str, optional): API base URL (auto-detected if not provided)

## Entity Management

### EntityManager

Provides access to all entity-specific operations.

```python
# Access through client
entities = client.entities

# Available entities
tickets = entities.tickets
companies = entities.companies
contacts = entities.contacts
projects = entities.projects
resources = entities.resources
contracts = entities.contracts
time_entries = entities.time_entries
attachments = entities.attachments
```

### BaseEntity

Base class for all entity operations. All entity classes inherit from this.

#### Common Methods

##### query(**kwargs)
```python
query(
    filters: Optional[List[QueryFilter]] = None,
    include_fields: Optional[List[str]] = None,
    max_records: int = 500
) -> QueryResponse
```
Query entities with filtering and field selection.

##### query_by_id(entity_id: int)
```python
query_by_id(entity_id: int) -> Optional[Dict[str, Any]]
```
Get a single entity by ID.

##### get_next_page(current_response: QueryResponse)
```python
get_next_page(current_response: QueryResponse) -> Optional[QueryResponse]
```
Get the next page of results from a paginated query.

##### batch_create(entities_data: List[EntityDict], batch_size: int = 200)
```python
batch_create(
    entities_data: List[EntityDict],
    batch_size: int = 200
) -> List[CreateResponse]
```
Create multiple entities in batches.

##### batch_update(entities_data: List[EntityDict], batch_size: int = 200)
```python
batch_update(
    entities_data: List[EntityDict],
    batch_size: int = 200
) -> List[Dict[str, Any]]
```
Update multiple entities in batches.

##### batch_delete(entity_ids: List[int], batch_size: int = 200)
```python
batch_delete(
    entity_ids: List[int],
    batch_size: int = 200
) -> List[bool]
```
Delete multiple entities in batches.

### TicketsEntity

Specialized operations for ticket management.

#### Methods

##### create_ticket(title: str, description: str, account_id: int, **kwargs)
```python
create_ticket(
    title: str,
    description: str,
    account_id: int,
    queue_id: Optional[int] = None,
    priority: Optional[int] = None,
    status: Optional[int] = None,
    assigned_resource_id: Optional[int] = None,
    **kwargs
) -> CreateResponse
```
Create a new ticket with required and optional fields.

##### get_tickets_by_account(account_id: int, status_filter: Optional[str] = None)
```python
get_tickets_by_account(
    account_id: int,
    status_filter: Optional[str] = None
) -> QueryResponse
```
Get all tickets for a specific account.

##### get_tickets_by_resource(resource_id: int, include_completed: bool = True)
```python
get_tickets_by_resource(
    resource_id: int,
    include_completed: bool = True
) -> QueryResponse
```
Get tickets assigned to a specific resource.

##### update_ticket_status(ticket_id: int, status: int, note: Optional[str] = None)
```python
update_ticket_status(
    ticket_id: int,
    status: int,
    note: Optional[str] = None
) -> Dict[str, Any]
```
Update a ticket's status with optional note.

##### assign_ticket(ticket_id: int, resource_id: int, note: Optional[str] = None)
```python
assign_ticket(
    ticket_id: int,
    resource_id: int,
    note: Optional[str] = None
) -> Dict[str, Any]
```
Assign a ticket to a resource.

##### add_ticket_note(ticket_id: int, note: str, **kwargs)
```python
add_ticket_note(
    ticket_id: int,
    note: str,
    note_type: int = 1,
    title: Optional[str] = None,
    publish: int = 1
) -> CreateResponse
```
Add a note to a ticket.

### CompaniesEntity

Specialized operations for company management.

#### Methods

##### create_company(company_name: str, **kwargs)
```python
create_company(
    company_name: str,
    company_type: int = 1,
    phone: Optional[str] = None,
    address1: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
    **kwargs
) -> CreateResponse
```
Create a new company.

##### search_companies_by_name(name: str, exact_match: bool = False)
```python
search_companies_by_name(
    name: str,
    exact_match: bool = False
) -> QueryResponse
```
Search companies by name with optional exact matching.

##### get_companies_by_type(company_type: int, active_only: bool = True)
```python
get_companies_by_type(
    company_type: int,
    active_only: bool = True
) -> QueryResponse
```
Get companies by type with optional active filter.

##### get_customer_companies(active_only: bool = True)
```python
get_customer_companies(active_only: bool = True) -> QueryResponse
```
Get all customer companies.

##### get_prospect_companies(active_only: bool = True)
```python
get_prospect_companies(active_only: bool = True) -> QueryResponse
```
Get all prospect companies.

##### update_company_address(company_id: int, **address_fields)
```python
update_company_address(
    company_id: int,
    address1: Optional[str] = None,
    address2: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Any]
```
Update a company's address information.

### AttachmentsEntity

File attachment management operations.

#### Methods

##### upload_file(parent_type: str, parent_id: int, file_path: str, **kwargs)
```python
upload_file(
    parent_type: str,
    parent_id: int,
    file_path: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> AttachmentData
```
Upload a file from disk as an attachment.

**Parameters:**
- `parent_type` (str): Entity type ("Ticket", "Project", etc.)
- `parent_id` (int): Parent entity ID
- `file_path` (str): Path to file to upload
- `title` (str, optional): Attachment title
- `description` (str, optional): Attachment description

##### upload_from_data(parent_type: str, parent_id: int, file_data: bytes, filename: str, **kwargs)
```python
upload_from_data(
    parent_type: str,
    parent_id: int,
    file_data: bytes,
    filename: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> AttachmentData
```
Upload file data from memory as an attachment.

##### download_file(attachment_id: int, output_path: Optional[str] = None)
```python
download_file(
    attachment_id: int,
    output_path: Optional[str] = None
) -> bytes
```
Download an attachment file.

**Returns:** File content as bytes. If `output_path` provided, also saves to disk.

##### get_attachments_for_entity(parent_type: str, parent_id: int)
```python
get_attachments_for_entity(
    parent_type: str,
    parent_id: int
) -> List[AttachmentData]
```
Get all attachments for a specific entity.

##### delete_attachment(attachment_id: int)
```python
delete_attachment(attachment_id: int) -> bool
```
Delete an attachment.

##### batch_upload(parent_type: str, parent_id: int, file_paths: List[str])
```python
batch_upload(
    parent_type: str,
    parent_id: int,
    file_paths: List[str]
) -> List[AttachmentData]
```
Upload multiple files concurrently.

## CLI Interface

The py-autotask CLI provides command-line access to all library functionality.

### Basic Commands

#### Query Operations

```bash
# Query tickets
py-autotask query tickets --max-records 10

# Query with filters
py-autotask query companies --filter "isActive eq true"

# Query specific fields
py-autotask query tickets --fields "id,title,status"

# Output as JSON
py-autotask query companies --output json
```

#### Entity Operations

```bash
# Get entity by ID
py-autotask get tickets 12345

# Create entity
py-autotask create tickets --data '{"title":"Test","accountID":123}'

# Update entity
py-autotask update tickets 12345 --data '{"status":2}'

# Delete entity
py-autotask delete tickets 12345
```

#### Batch Operations

```bash
# Batch create from JSON file
py-autotask batch create tickets --file data.json

# Batch update
py-autotask batch update companies --file updates.json

# Batch delete with confirmation
py-autotask batch delete tickets --ids 123,124,125
```

#### Attachment Operations

```bash
# Upload file
py-autotask attachments upload --parent-type Ticket --parent-id 123 --file document.pdf

# Download attachment
py-autotask attachments download --attachment-id 456 --output downloaded.pdf

# List attachments
py-autotask attachments list --parent-type Ticket --parent-id 123

# Delete attachment
py-autotask attachments delete-attachment --attachment-id 456
```

## Types

### Core Types

#### CreateResponse
```python
class CreateResponse(BaseModel):
    item_id: int
```
Response from entity creation operations.

#### QueryResponse
```python
class QueryResponse(BaseModel):
    items: List[Dict[str, Any]]
    page_details: PageDetails
```
Response from query operations with pagination.

#### PageDetails
```python
class PageDetails(BaseModel):
    count: int
    request_count: int
    next_page_url: Optional[str]
    prev_page_url: Optional[str]
```
Pagination information for query responses.

#### AttachmentData
```python
class AttachmentData(BaseModel):
    id: int
    parent_type: str
    parent_id: int
    file_name: str
    file_size: int
    content_type: str
    title: Optional[str]
    description: Optional[str]
    created_date_time: str
    created_by: int
```
Attachment metadata and information.

### Entity-Specific Types

#### TicketData
```python
class TicketData(BaseModel):
    id: int
    account_id: int
    title: str
    description: Optional[str]
    status: int
    priority: Optional[int]
    assigned_resource_id: Optional[int]
    create_date: str
    # ... additional fields
```

#### CompanyData
```python
class CompanyData(BaseModel):
    id: int
    company_name: str
    company_type: int
    is_active: bool
    phone: Optional[str]
    address1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    # ... additional fields
```

## Exceptions

### AutotaskException

Base exception class for all Autotask-related errors.

```python
from py_autotask.exceptions import AutotaskException
```

### AutotaskAuthenticationError

Raised when authentication fails.

```python
from py_autotask.exceptions import AutotaskAuthenticationError

try:
    client = AutotaskClient(credentials)
except AutotaskAuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### AutotaskConnectionError

Raised when network/connection issues occur.

```python
from py_autotask.exceptions import AutotaskConnectionError

try:
    tickets = client.entities.tickets.query()
except AutotaskConnectionError as e:
    print(f"Connection error: {e}")
```

### AutotaskValidationError

Raised when data validation fails.

```python
from py_autotask.exceptions import AutotaskValidationError

try:
    client.create_entity("Tickets", invalid_data=True)
except AutotaskValidationError as e:
    print(f"Validation error: {e}")
```

### AutotaskAPIError

Raised when the API returns an error response.

```python
from py_autotask.exceptions import AutotaskAPIError

try:
    client.get("Tickets", 999999)
except AutotaskAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response}")
```

## Usage Examples

### Basic Usage

```python
from py_autotask import AutotaskClient
from py_autotask.auth import AuthCredentials

# Initialize client
credentials = AuthCredentials(
    username="your_username",
    integration_code="your_code",
    secret="your_secret"
)
client = AutotaskClient(credentials)

# Query tickets
tickets = client.entities.tickets.query(max_records=10)
for ticket in tickets.items:
    print(f"Ticket {ticket['id']}: {ticket['title']}")

# Create a company
company_data = {
    "companyName": "Acme Corp",
    "companyType": 1,
    "phone": "555-1234"
}
new_company = client.entities.companies.create_company(**company_data)
print(f"Created company with ID: {new_company.item_id}")
```

### Advanced Filtering

```python
from py_autotask.types import QueryFilter, FilterOperation

# Complex filtering
filters = [
    QueryFilter(field="isActive", op=FilterOperation.EQ, value=True),
    QueryFilter(field="companyType", op=FilterOperation.EQ, value=1),
    QueryFilter(field="city", op=FilterOperation.CONTAINS, value="New York")
]

companies = client.entities.companies.query(
    filters=filters,
    include_fields=["id", "companyName", "phone"],
    max_records=50
)
```

### Batch Operations

```python
# Batch create tickets
ticket_data = [
    {"title": "Issue 1", "accountID": 123, "description": "First issue"},
    {"title": "Issue 2", "accountID": 124, "description": "Second issue"},
    {"title": "Issue 3", "accountID": 125, "description": "Third issue"}
]

results = client.batch_create("Tickets", ticket_data)
print(f"Created {len(results)} tickets")

# Batch update
updates = [
    {"id": 123, "status": 2},
    {"id": 124, "status": 2},
    {"id": 125, "status": 2}
]

updated = client.batch_update("Tickets", updates)
print(f"Updated {len(updated)} tickets")
```

### File Attachments

```python
# Upload file
attachment = client.attachments.upload_file(
    parent_type="Ticket",
    parent_id=12345,
    file_path="/path/to/document.pdf",
    title="Important Document",
    description="Ticket documentation"
)
print(f"Uploaded attachment: {attachment.id}")

# Download file
file_content = client.attachments.download_file(
    attachment_id=attachment.id,
    output_path="/path/to/downloaded.pdf"
)

# List attachments
attachments = client.attachments.get_attachments_for_entity(
    parent_type="Ticket",
    parent_id=12345
)
for att in attachments:
    print(f"Attachment: {att.file_name} ({att.file_size} bytes)")
```

### Error Handling

```python
from py_autotask.exceptions import (
    AutotaskAuthenticationError,
    AutotaskConnectionError,
    AutotaskValidationError,
    AutotaskAPIError
)

try:
    # Your Autotask operations here
    tickets = client.entities.tickets.query()
    
except AutotaskAuthenticationError:
    print("Authentication failed - check credentials")
except AutotaskConnectionError:
    print("Network error - check connection")
except AutotaskValidationError as e:
    print(f"Data validation error: {e}")
except AutotaskAPIError as e:
    print(f"API error {e.status_code}: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Connection Pooling

The client automatically uses connection pooling for better performance:

```python
# Connection pooling is enabled by default
client = AutotaskClient(credentials)

# Configure pool size if needed
from py_autotask.client import ClientConfig

config = ClientConfig(
    timeout=30,
    max_retries=3,
    pool_connections=10,
    pool_maxsize=20
)
client = AutotaskClient(credentials, config=config)
```

### Batch Operations

Use batch operations for better performance when dealing with multiple entities:

```python
# Instead of individual creates
for data in large_dataset:
    client.create_entity("Tickets", **data)  # Slow

# Use batch create
client.batch_create("Tickets", large_dataset)  # Fast
```

### Pagination

Handle large result sets efficiently with pagination:

```python
# Get first page
page = client.entities.tickets.query(max_records=100)

# Process all pages
while page:
    for ticket in page.items:
        process_ticket(ticket)
    
    # Get next page
    page = client.entities.tickets.get_next_page(page)
```

### Memory Management

For large datasets, process data in chunks to manage memory usage:

```python
# Process in smaller batches
batch_size = 100
for i in range(0, len(large_dataset), batch_size):
    batch = large_dataset[i:i + batch_size]
    results = client.batch_create("Tickets", batch)
    # Process results immediately
    process_results(results)
    # Clear references to help garbage collection
    del batch, results
``` 