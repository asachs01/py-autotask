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

try:
    from ._version import version as __version__
except ImportError:
    # Fallback for when setuptools_scm hasn't created _version.py yet
    __version__ = "0.0.0+unknown"

__author__ = "Aaron Sachs"
__email__ = "asachs@wyre.engineering"


# Lazy imports to avoid circular dependencies during version detection
def __getattr__(name):
    """Lazy import mechanism to avoid importing heavy dependencies during build."""
    if name == "AutotaskClient":
        from .client import AutotaskClient

        return AutotaskClient
    elif name == "AsyncAutotaskClient":
        from .async_client import AsyncAutotaskClient

        return AsyncAutotaskClient
    elif name == "IntelligentBulkManager":
        from .bulk_manager import IntelligentBulkManager

        return IntelligentBulkManager
    elif name == "BulkConfig":
        from .bulk_manager import BulkConfig

        return BulkConfig
    elif name == "BulkResult":
        from .bulk_manager import BulkResult

        return BulkResult
    elif name == "AutotaskError":
        from .exceptions import AutotaskError

        return AutotaskError
    elif name == "AutotaskAPIError":
        from .exceptions import AutotaskAPIError

        return AutotaskAPIError
    elif name == "AutotaskAuthError":
        from .exceptions import AutotaskAuthError

        return AutotaskAuthError
    elif name == "AutotaskConnectionError":
        from .exceptions import AutotaskConnectionError

        return AutotaskConnectionError
    elif name == "AutotaskValidationError":
        from .exceptions import AutotaskValidationError

        return AutotaskValidationError
    elif name == "FilterOperation":
        from .types import FilterOperation

        return FilterOperation
    elif name == "QueryFilter":
        from .types import QueryFilter

        return QueryFilter
    elif name == "PaginationInfo":
        from .types import PaginationInfo

        return PaginationInfo
    elif name == "EntityMetadata":
        from .types import EntityMetadata

        return EntityMetadata
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Core classes
    "AutotaskClient",
    "AsyncAutotaskClient",
    "IntelligentBulkManager",
    "BulkConfig",
    "BulkResult",
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
