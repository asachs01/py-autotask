"""
py-autotask: A comprehensive Python client library for the Autotask REST API.

This library provides a Pythonic interface to the Autotask REST API with:
- Automatic zone detection
- Full CRUD operations for all entities
- Intelligent pagination and filtering
- Comprehensive error handling
- CLI interface

Example:
    from py_autotask import AutotaskClient

    client = AutotaskClient.create(
        username="user@example.com",
        integration_code="YOUR_INTEGRATION_CODE",
        secret="YOUR_SECRET"
    )

    # Get a ticket
    ticket = client.tickets.get(12345)

    # Query companies
    companies = client.companies.query({
        "filter": [{"op": "eq", "field": "isActive", "value": "true"}]
    })
"""

__version__ = "0.1.1"
__author__ = "Aaron Sachs"
__email__ = "asachs@wyre.engineering"

# Core imports
from .client import AutotaskClient
from .exceptions import (
    AutotaskAPIError,
    AutotaskAuthError,
    AutotaskConnectionError,
    AutotaskError,
    AutotaskValidationError,
)

# Type imports for better IDE support
from .types import (
    EntityMetadata,
    FilterOperation,
    PaginationInfo,
    QueryFilter,
)

__all__ = [
    # Core classes
    "AutotaskClient",
    # Exceptions
    "AutotaskError",
    "AutotaskAPIError",
    "AutotaskAuthError",
    "AutotaskConnectionError",
    "AutotaskValidationError",
    # Types
    "FilterOperation",
    "QueryFilter",
    "PaginationInfo",
    "EntityMetadata",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]
