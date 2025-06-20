# py-autotask

A comprehensive Python client library for the Autotask REST API with feature parity to popular Node.js libraries.

[![PyPI version](https://badge.fury.io/py/py-autotask.svg)](https://badge.fury.io/py/py-autotask)
[![Python Version](https://img.shields.io/pypi/pyversions/py-autotask.svg)](https://pypi.org/project/py-autotask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://codecov.io/gh/asachs01/py-autotask/branch/main/graph/badge.svg)](https://codecov.io/gh/asachs01/py-autotask)

## Features

- **🚀 Easy to Use** - Intuitive API that follows Python best practices
- **🔐 Automatic Authentication** - Handles zone detection and authentication seamlessly  
- **📊 Full CRUD Operations** - Create, Read, Update, Delete for all Autotask entities
- **🔍 Advanced Querying** - Powerful filtering and pagination support
- **⚡ Performance Optimized** - Intelligent retry logic and connection pooling
- **🛡️ Type Safe** - Full type hints for better IDE support and code reliability
- **🧪 Well Tested** - Comprehensive test suite with >90% coverage
- **📱 CLI Interface** - Command-line tool for quick operations
- **📚 Comprehensive Documentation** - Detailed examples and API reference

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

### Filtering and Pagination

```python
# Complex filtering
tickets = client.tickets.query({
    "filter": [
        {"op": "eq", "field": "status", "value": "1"},
        {"op": "gte", "field": "priority", "value": "3"},
        {"op": "contains", "field": "title", "value": "urgent"}
    ],
    "includeFields": ["id", "title", "status", "priority"],
    "maxRecords": 100
})

# Automatic pagination
all_companies = client.companies.query_all({
    "filter": [{"op": "eq", "field": "isActive", "value": "true"}]
})
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