# py-autotask

A comprehensive Python SDK for the Autotask REST API providing **100% complete API coverage** with 193 entity implementations.

[![PyPI version](https://badge.fury.io/py/py-autotask.svg)](https://badge.fury.io/py/py-autotask)
[![Python Version](https://img.shields.io/pypi/pyversions/py-autotask.svg)](https://pypi.org/project/py-autotask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://codecov.io/gh/asachs01/py-autotask/branch/main/graph/badge.svg)](https://codecov.io/gh/asachs01/py-autotask)
[![API Coverage](https://img.shields.io/badge/API%20Coverage-100%25-brightgreen)](docs/API_COVERAGE.md)
[![Entities](https://img.shields.io/badge/Entities-193-blue)](docs/API_COVERAGE.md)

## Features

- **🎯 100% API Coverage** - Complete implementation of all 193 Autotask REST API entities
- **🚀 Easy to Use** - Intuitive API that follows Python best practices
- **🔐 Automatic Authentication** - Handles zone detection and authentication seamlessly  
- **📊 Full CRUD Operations** - Create, Read, Update, Delete for all Autotask entities
- **🔍 Advanced Query Builder** - Fluent API for complex filtering and relationship queries
- **🏗️ Parent-Child Relationships** - Built-in support for entity relationships and hierarchies
- **⚡ Batch Operations** - Efficient bulk operations for create, update, delete, and retrieve
- **📄 Enhanced Pagination** - Automatic pagination with safety limits and cursor support
- **⚡ Performance Optimized** - Intelligent retry logic and connection pooling
- **🛡️ Type Safe** - Full type hints for better IDE support and code reliability
- **🧪 Well Tested** - Comprehensive test suite with 82+ test methods
- **📱 CLI Interface** - Command-line tool for quick operations
- **📚 Comprehensive Documentation** - Detailed examples and complete API reference
- **💼 Enterprise Ready** - Production-grade with extensive error handling and logging

## Quick Start

### Installation

```bash
pip install py-autotask
```

### Basic Usage

```python
from py_autotask import AutotaskClient

# Create client with credentials
client = AutotaskClient.create(
    username="user@example.com",
    integration_code="YOUR_INTEGRATION_CODE", 
    secret="YOUR_SECRET"
)

# Get a ticket
ticket = client.tickets.get(12345)
print(f"Ticket: {ticket['title']}")

# Query companies
companies = client.companies.query({
    "filter": [{"op": "eq", "field": "isActive", "value": "true"}]
})

# Create a new contact
new_contact = client.contacts.create({
    "firstName": "John",
    "lastName": "Doe", 
    "emailAddress": "john.doe@example.com",
    "companyID": 12345
})
```

### Environment Variables

You can also configure authentication using environment variables:

```bash
export AUTOTASK_USERNAME="user@example.com"
export AUTOTASK_INTEGRATION_CODE="YOUR_INTEGRATION_CODE"
export AUTOTASK_SECRET="YOUR_SECRET"
```

```python
from py_autotask import AutotaskClient

# Client will automatically use environment variables
client = AutotaskClient.from_env()
```

## CLI Usage

The library includes a powerful CLI for common operations:

```bash
# Test authentication
py-autotask auth

# Get a ticket
py-autotask get ticket 12345

# Query active companies
py-autotask query companies --filter '{"op": "eq", "field": "isActive", "value": "true"}'

# Get field information
py-autotask info Tickets
```

## Supported Entities

py-autotask supports all major Autotask entities:

- **Tickets** - Service desk tickets and related operations
- **Companies** - Customer and vendor company records  
- **Contacts** - Individual contact records
- **Projects** - Project management and tracking
- **Resources** - User and technician records
- **Contracts** - Service contracts and agreements
- **Time Entries** - Time tracking and billing
- **Expenses** - Expense tracking and management
- **Products** - Product catalog and inventory
- **Services** - Service catalog management

## Advanced Features

### Advanced Query Builder

```python
from py_autotask.entities import FilterOperator

# Fluent query building with method chaining
tickets = (client.tickets.query_builder()
    .where("status", FilterOperator.EQUAL, "1")
    .where("priority", FilterOperator.GREATER_THAN_OR_EQUAL, 3)
    .where("title", FilterOperator.CONTAINS, "urgent")
    .select(["id", "title", "status", "priority"])
    .limit(100)
    .order_by("createDateTime", "desc")
    .execute_all())

# Date range queries
recent_tickets = (client.tickets.query_builder()
    .where_date_range("createDateTime", "2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z")
    .where_in("status", ["1", "2", "3"])
    .execute())

# Relationship-based queries
tickets_for_acme = (client.tickets.query_builder()
    .where_related("Companies", "companyName", "contains", "Acme")
    .execute_all())
```

### Parent-Child Relationships

```python
# Get all tickets for a company
company_tickets = client.companies.get_children(12345, "Tickets")

# Get all active tickets for a project  
active_tickets = client.projects.get_children(
    67890, 
    "Tickets", 
    filters={"field": "status", "op": "eq", "value": "1"}
)

# Get parent company for a ticket
company = client.tickets.get_parent(12345, "Companies")

# Link entities
client.tickets.link_to_parent(ticket_id=1001, parent_id=123, parent_entity="Companies")

# Batch link multiple tickets to a company
client.companies.batch_link_children(12345, [1001, 1002, 1003], "Tickets")
```

### Batch Operations

```python
# Batch create multiple tickets
tickets_data = [
    {"title": "Issue 1", "accountID": 123, "status": 1},
    {"title": "Issue 2", "accountID": 123, "status": 1},
    {"title": "Issue 3", "accountID": 456, "status": 1},
]
results = client.tickets.batch_create(tickets_data)

# Batch update
updates = [
    {"id": 1001, "priority": 4},
    {"id": 1002, "priority": 3},
    {"id": 1003, "status": 2},
]
updated = client.tickets.batch_update(updates)

# Batch retrieve
tickets = client.tickets.batch_get([1001, 1002, 1003])

# Batch delete with results
result = client.tickets.batch_delete([1001, 1002, 1003])
print(f"Deleted: {result['success_count']}, Failed: {result['failure_count']}")
```

### Enhanced Pagination

```python
# Automatic pagination with safety limits
all_companies = client.companies.query_all(
    filters={"field": "isActive", "op": "eq", "value": "true"},
    max_total_records=10000,  # Safety limit
    page_size=500  # Records per page
)

# Check if records exist without retrieving them
has_urgent_tickets = (client.tickets.query_builder()
    .where("priority", "gte", 4)
    .exists())

# Get just the first matching record
first_urgent = (client.tickets.query_builder()
    .where("priority", "gte", 4)
    .order_by("createDateTime", "desc")
    .first())
```

### Time Entry Management

Track time against tickets, projects, and tasks with comprehensive time management features:

```python
# Create time entries
time_entry = client.time_entries.create_time_entry(
    resource_id=123,
    ticket_id=12345,
    start_date_time="2023-08-01T09:00:00",
    end_date_time="2023-08-01T17:00:00",
    hours_worked=8.0,
    hours_to_bill=8.0,
    description="Development work on feature X",
    billable_to_account=True
)

# Get time entries for a resource
time_entries = client.time_entries.get_time_entries_by_resource(
    resource_id=123,
    start_date="2023-08-01",
    end_date="2023-08-31"
)

# Get billable time for invoicing
billable_time = client.time_entries.get_billable_time_entries(
    account_id=456,
    start_date="2023-08-01",
    end_date="2023-08-31"
)

# Time analytics and reporting
time_summary = client.time_entries.get_time_summary_by_resource(
    resource_id=123,
    start_date="2023-08-01",
    end_date="2023-08-31"
)
print(f"Total hours: {time_summary['total_hours']}")
print(f"Billable hours: {time_summary['billable_hours']}")
print(f"Utilization: {time_summary['utilization_rate']}%")

# Time entry workflow management
client.time_entries.submit_time_entry(time_entry_id=789)
client.time_entries.approve_time_entry(time_entry_id=789, approver_notes="Approved for billing")
```

### Error Handling

```python
from py_autotask.exceptions import (
    AutotaskAuthError,
    AutotaskAPIError,
    AutotaskRateLimitError
)

try:
    ticket = client.tickets.get(12345)
except AutotaskAuthError:
    print("Authentication failed - check credentials")
except AutotaskRateLimitError as e:
    print(f"Rate limit exceeded, retry after {e.retry_after} seconds")
except AutotaskAPIError as e:
    print(f"API error: {e.message}")
```

### Batch Operations

```python
# Bulk create
contacts_data = [
    {"firstName": "John", "lastName": "Doe", "companyID": 123},
    {"firstName": "Jane", "lastName": "Smith", "companyID": 123}
]

# Create multiple contacts
results = []
for contact_data in contacts_data:
    result = client.contacts.create(contact_data)
    results.append(result)
```

## Configuration

### Request Configuration

```python
from py_autotask.types import RequestConfig

config = RequestConfig(
    timeout=60,          # Request timeout in seconds
    max_retries=5,       # Maximum retry attempts
    retry_delay=2.0,     # Base retry delay
    retry_backoff=2.0    # Exponential backoff multiplier
)

client = AutotaskClient(auth, config)
```

### Logging

```python
import logging

# Enable debug logging
logging.getLogger('py_autotask').setLevel(logging.DEBUG)

# Configure custom logging
logger = logging.getLogger('py_autotask.client')
logger.addHandler(logging.FileHandler('autotask.log'))
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/asachs01/py-autotask.git
cd py-autotask

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=py_autotask --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run integration tests (requires API credentials)
pytest tests/integration/ --integration
```

### Code Quality

```bash
# Format code
black py_autotask tests

# Sort imports
isort py_autotask tests

# Lint code
flake8 py_autotask tests

# Type checking
mypy py_autotask
```

## API Reference

For detailed API documentation, visit [our documentation site](https://py-autotask.readthedocs.io/).

### Core Classes

- **AutotaskClient** - Main client class for API operations
- **AutotaskAuth** - Authentication and zone detection
- **BaseEntity** - Base class for all entity operations
- **EntityManager** - Factory for entity handlers

### Exception Classes

- **AutotaskError** - Base exception class
- **AutotaskAPIError** - HTTP/API related errors
- **AutotaskAuthError** - Authentication failures
- **AutotaskValidationError** - Data validation errors
- **AutotaskRateLimitError** - Rate limiting errors

## Migration Guide

### From autotask-node (Node.js)

py-autotask provides similar functionality to the popular Node.js autotask library:

```javascript
// Node.js (autotask-node)
const autotask = require('autotask-node');
const at = new autotask(username, integration, secret);

at.tickets.get(12345).then(ticket => {
    console.log(ticket.title);
});
```

```python
# Python (py-autotask)
from py_autotask import AutotaskClient

client = AutotaskClient.create(username, integration, secret)
ticket = client.tickets.get(12345)
print(ticket['title'])
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Reporting Issues

- Use the [GitHub Issues](https://github.com/asachs01/py-autotask/issues) page
- Include Python version, library version, and error details
- Provide minimal reproduction code when possible

### Feature Requests

- Open an issue with the "enhancement" label
- Describe the use case and expected behavior
- Include relevant Autotask API documentation references

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://py-autotask.readthedocs.io/)
- 💬 [GitHub Discussions](https://github.com/asachs01/py-autotask/discussions)
- 🐛 [Issue Tracker](https://github.com/asachs01/py-autotask/issues)
- 📧 [Email Support](mailto:support@py-autotask.dev)

## Acknowledgments

- Autotask API team for excellent documentation
- Contributors to the autotask-node library for inspiration
- Python community for amazing libraries and tools

---

**Disclaimer**: This library is not officially affiliated with Datto/Autotask. It is an independent implementation of the Autotask REST API. 

## Phase 4: Advanced Features

### Batch Operations

Efficiently process multiple entities with built-in batch support:

```python
# Batch create tickets
tickets_data = [
    {
        "title": "Server Down - Critical",
        "description": "Production server unresponsive",
        "accountID": 123,
        "priority": 1,
        "status": 1
    },
    {
        "title": "Email Issues",
        "description": "Users unable to send email",
        "accountID": 123,
        "priority": 2,
        "status": 1
    }
]

# Create multiple tickets in batches
results = client.tickets.batch_create(tickets_data, batch_size=200)
for result in results:
    if result.item_id:
        print(f"Created ticket: {result.item_id}")
    else:
        print(f"Failed to create ticket: {result.errors}")

# Batch update multiple entities
updates = [
    {"id": 12345, "priority": 1, "status": 8},  # Set to high priority, in progress
    {"id": 12346, "priority": 3, "status": 5}   # Set to medium priority, complete
]

updated_tickets = client.tickets.batch_update(updates)
print(f"Updated {len(updated_tickets)} tickets")

# Batch delete entities (with confirmation)
ticket_ids = [12347, 12348, 12349]
deletion_results = client.tickets.batch_delete(ticket_ids)
successful_deletions = sum(deletion_results)
print(f"Deleted {successful_deletions}/{len(ticket_ids)} tickets")

# Batch operations work with all entities
company_updates = [
    {"id": 1001, "isActive": True},
    {"id": 1002, "isActive": False}
]
client.companies.batch_update(company_updates)

# Low-level batch operations (direct client access)
results = client.batch_create("Projects", project_data_list, batch_size=100)
updated = client.batch_update("Contracts", contract_updates, batch_size=50)
deleted = client.batch_delete("TimeEntries", time_entry_ids, batch_size=200)
```

### File Attachment Management

Upload, download, and manage file attachments for any entity:

```python
# Upload a file to a ticket
attachment = client.attachments.upload_file(
    parent_type="Ticket",
    parent_id=12345,
    file_path="/path/to/screenshot.png",
    title="Error Screenshot",
    description="Screenshot showing the error state"
)
print(f"Uploaded attachment with ID: {attachment.id}")

# Upload from memory/data
with open("/path/to/document.pdf", "rb") as f:
    file_data = f.read()

attachment = client.attachments.upload_from_data(
    parent_type="Project",
    parent_id=67890,
    file_data=file_data,
    filename="project_spec.pdf",
    content_type="application/pdf",
    title="Project Specification",
    description="Detailed project requirements"
)

# Download attachments
file_data = client.attachments.download_file(
    attachment_id=attachment.id,
    output_path="/path/to/downloads/project_spec.pdf"
)

# List all attachments for an entity
attachments = client.attachments.get_attachments_for_entity(
    parent_type="Ticket",
    parent_id=12345
)

for attachment in attachments:
    print(f"ID: {attachment.id}")
    print(f"  File: {attachment.file_name}")
    print(f"  Size: {attachment.file_size} bytes")
    print(f"  Type: {attachment.content_type}")
    print(f"  Title: {attachment.title}")

# Batch upload multiple files
file_paths = [
    "/path/to/log1.txt",
    "/path/to/log2.txt", 
    "/path/to/config.xml"
]

uploaded_attachments = client.attachments.batch_upload(
    parent_type="Ticket",
    parent_id=12345,
    file_paths=file_paths,
    batch_size=5  # Upload 5 files concurrently
)

print(f"Successfully uploaded {len(uploaded_attachments)} files")

# Delete attachments
client.attachments.delete_attachment(attachment_id=12345)

# Get attachment metadata only (without downloading)
attachment_info = client.attachments.get_attachment_info(attachment_id=12345)
if attachment_info:
    print(f"Attachment exists: {attachment_info.file_name}")
```

### Enhanced CLI Interface

The CLI now supports batch operations and attachment management:

```bash
# Batch operations
py-autotask batch create Tickets tickets.json --batch-size 100
py-autotask batch update Companies company_updates.json --output summary
py-autotask batch delete Tickets --ids-file ticket_ids.txt --confirm

# With inline IDs
py-autotask batch delete Projects 1001 1002 1003 --confirm

# Attachment operations
py-autotask attachments upload Ticket 12345 /path/to/file.pdf --title "Documentation"
py-autotask attachments download 67890 /path/to/downloads/file.pdf
py-autotask attachments list Ticket 12345 --output table
py-autotask attachments delete-attachment 67890 --confirm

# Batch create example with JSON file
echo '[
  {"title": "Issue 1", "description": "First issue", "accountID": 123},
  {"title": "Issue 2", "description": "Second issue", "accountID": 123}
]' > tickets.json

py-autotask batch create Tickets tickets.json
```

## Performance Optimization

Phase 4 includes several performance improvements:

### Intelligent Batching
- Automatic batch size optimization (up to API limit of 200)
- Parallel processing where possible
- Progress tracking for large operations
- Graceful error handling with partial success reporting

### Connection Pooling
- HTTP session reuse for multiple requests
- Configurable connection timeouts and retries
- Built-in rate limiting awareness

### Memory Efficiency
- Streaming file uploads/downloads for large attachments
- Lazy loading of entity relationships
- Efficient pagination for large result sets

```python
# Configure performance settings
from py_autotask.types import RequestConfig

config = RequestConfig(
    timeout=30,           # Request timeout in seconds
    max_retries=3,        # Maximum retry attempts
    retry_backoff=1.0,    # Backoff factor for retries
    max_records=1000      # Default pagination limit
)

client = AutotaskClient.create(
    username="user@example.com",
    integration_code="YOUR_CODE", 
    secret="YOUR_SECRET",
    config=config
)

# Batch operations automatically optimize performance
large_dataset = client.tickets.query({
    "filter": [{"op": "gte", "field": "createDate", "value": "2023-01-01"}]
})  # Handles pagination automatically

# Stream large file uploads
large_attachment = client.attachments.upload_file(
    parent_type="Project",
    parent_id=12345,
    file_path="/path/to/large_file.zip"  # Efficient streaming upload
)
``` 