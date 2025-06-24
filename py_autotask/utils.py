"""
Utility functions for py-autotask.

This module provides various utility functions for working with the Autotask API,
including pagination, retry logic, and data transformation.
"""

import logging
from typing import Any, Dict, Generator, List, Optional, Union
from urllib.parse import parse_qs, urlparse

from .exceptions import AutotaskValidationError
from .types import FilterOperation, QueryRequest

logger = logging.getLogger(__name__)


def build_query_params(query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build query parameters for API requests.

    Args:
        query: Query dictionary with filters and options

    Returns:
        Dictionary of query parameters for the request

    Raises:
        AutotaskValidationError: If query structure is invalid
    """
    if not query:
        return {}

    try:
        # Validate and convert using Pydantic model
        query_request = QueryRequest(**query)

        # Convert back to dict, excluding None values
        params = query_request.model_dump(exclude_none=True, by_alias=True)

        # Convert filter objects to dictionaries
        if "filter" in params:
            params["filter"] = [
                filter_obj.model_dump(exclude_none=True, by_alias=True)
                for filter_obj in query_request.filter or []
            ]

        return params

    except Exception as e:
        raise AutotaskValidationError(f"Invalid query structure: {e}")


def validate_filter_operation(field: str, operation: str, value: Any) -> None:
    """
    Validate a filter operation.

    Args:
        field: Field name
        operation: Filter operation
        value: Filter value

    Raises:
        AutotaskValidationError: If the filter is invalid
    """
    try:
        op_enum = FilterOperation(operation)
    except ValueError:
        valid_ops = [op.value for op in FilterOperation]
        raise AutotaskValidationError(
            f"Invalid filter operation '{operation}'. Valid operations: {valid_ops}",
            field=field,
        )

    # Validate value requirements for specific operations
    if op_enum in [FilterOperation.IS_NULL, FilterOperation.IS_NOT_NULL]:
        if value is not None:
            raise AutotaskValidationError(
                f"Operation '{operation}' should not have a value",
                field=field,
                value=value,
            )
    elif op_enum in [FilterOperation.IN, FilterOperation.NOT_IN]:
        if not isinstance(value, list):
            raise AutotaskValidationError(
                f"Operation '{operation}' requires a list value",
                field=field,
                value=value,
            )
    elif op_enum == FilterOperation.BETWEEN:
        if not isinstance(value, list) or len(value) != 2:
            raise AutotaskValidationError(
                "Operation 'between' requires a list with exactly 2 values",
                field=field,
                value=value,
            )
    else:
        if value is None:
            raise AutotaskValidationError(
                f"Operation '{operation}' requires a value", field=field
            )


def extract_pagination_info(response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract pagination information from API response.

    Args:
        response_data: API response data

    Returns:
        Pagination information or None if not present
    """
    return response_data.get("pageDetails")


def extract_next_page_url(pagination_info: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract next page URL from pagination info.

    Args:
        pagination_info: Pagination information

    Returns:
        Next page URL or None if no more pages
    """
    if not pagination_info:
        return None

    return pagination_info.get("nextPageUrl")


def parse_next_page_params(next_page_url: str) -> Dict[str, str]:
    """
    Parse query parameters from next page URL.

    Args:
        next_page_url: URL for next page of results

    Returns:
        Dictionary of query parameters
    """
    parsed_url = urlparse(next_page_url)
    query_params = parse_qs(parsed_url.query)

    # Convert list values to single values (Autotask URLs have single values)
    return {key: values[0] for key, values in query_params.items()}


def chunk_list(items: List[Any], chunk_size: int) -> Generator[List[Any], None, None]:
    """
    Split a list into chunks of specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Yields:
        Chunks of the original list
    """
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def safe_get_nested(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary values.

    Args:
        data: Dictionary to search
        *keys: Sequence of keys for nested access
        default: Default value if key path doesn't exist

    Returns:
        Nested value or default
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def format_entity_name(entity_name: str) -> str:
    """
    Format entity name for API endpoints.

    Args:
        entity_name: Raw entity name

    Returns:
        Formatted entity name
    """
    # Remove common suffixes/prefixes if needed
    return entity_name


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (starting from 1)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Exponential backoff factor

    Returns:
        Delay in seconds
    """
    delay = base_delay * (backoff_factor ** (attempt - 1))
    return min(delay, max_delay)


def log_api_call(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    response_time: Optional[float] = None,
) -> None:
    """
    Log API call details.

    Args:
        method: HTTP method
        url: Request URL
        params: Query parameters
        data: Request data
        response_time: Response time in seconds
    """
    log_msg = f"{method} {url}"

    if params:
        log_msg += f" (params: {len(params)} items)"

    if data:
        log_msg += f" (data: {len(data)} items)"

    if response_time:
        log_msg += f" ({response_time:.2f}s)"

    logger.debug(log_msg)


def validate_entity_id(entity_id: Union[int, str]) -> int:
    """
    Validate and convert entity ID to integer.

    Args:
        entity_id: Entity ID to validate

    Returns:
        Valid integer entity ID

    Raises:
        AutotaskValidationError: If ID is invalid
    """
    try:
        int_id = int(entity_id)
        if int_id <= 0:
            raise ValueError("ID must be positive")
        return int_id
    except (ValueError, TypeError) as e:
        raise AutotaskValidationError(f"Invalid entity ID '{entity_id}': {e}")


def clean_entity_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean entity data by removing None values and empty strings.

    Args:
        data: Entity data dictionary

    Returns:
        Cleaned data dictionary
    """
    cleaned = {}
    for key, value in data.items():
        if value is not None and value != "":
            cleaned[key] = value
    return cleaned


def paginate_query(
    client, entity: str, query_params: Dict[str, Any], max_records: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Handle pagination for query operations.

    Args:
        client: AutotaskClient instance
        entity: Entity name
        query_params: Query parameters
        max_records: Maximum records to return (None for all)

    Returns:
        List of all items from paginated results
    """
    all_items = []
    current_params = query_params.copy()

    while True:
        # Make the request
        response = client._raw_query(entity, current_params)
        items = response.get("items", [])
        all_items.extend(items)

        # Check if we've hit the max records limit
        if max_records and len(all_items) >= max_records:
            return all_items[:max_records]

        # Check for next page
        page_details = response.get("pageDetails", {})
        next_page_url = page_details.get("nextPageUrl")

        if not next_page_url:
            break

        # Extract parameters for next page
        next_params = parse_next_page_params(next_page_url)
        current_params.update(next_params)

    return all_items


def validate_filter(filter_dict: Dict[str, Any]) -> None:
    """
    Validate a filter dictionary for API queries.

    Args:
        filter_dict: Filter dictionary to validate

    Raises:
        ValueError: If filter is invalid
    """
    required_fields = ["field", "op"]

    for field in required_fields:
        if field not in filter_dict:
            raise ValueError(f"Filter missing required field: {field}")

    # Validate operation
    valid_ops = [
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "beginsWith",
        "endsWith",
        "contains",
        "isNull",
        "isNotNull",
        "in",
        "notIn",
    ]

    if filter_dict["op"] not in valid_ops:
        raise ValueError(f"Invalid filter operation: {filter_dict['op']}")

    # Some operations require value, others don't
    ops_requiring_value = [
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "beginsWith",
        "endsWith",
        "contains",
        "in",
        "notIn",
    ]

    if filter_dict["op"] in ops_requiring_value and "value" not in filter_dict:
        raise ValueError(f"Filter operation '{filter_dict['op']}' requires a value")


def build_query_url(base_url: str, entity: str, query_params: Dict[str, Any]) -> str:
    """
    Build a complete query URL with parameters.

    Args:
        base_url: Base API URL
        entity: Entity name
        query_params: Query parameters

    Returns:
        Complete URL with query string
    """
    import urllib.parse

    url = f"{base_url}/v1.0/{entity}/query"

    if query_params:
        query_string = urllib.parse.urlencode(query_params)
        url = f"{url}?{query_string}"

    return url


def parse_api_response(response) -> Dict[str, Any]:
    """
    Parse API response and handle common response patterns.

    Args:
        response: HTTP response object

    Returns:
        Parsed response data

    Raises:
        AutotaskAPIError: If response indicates an error
    """
    try:
        data = response.json()
    except ValueError as e:
        raise ValueError(f"Invalid JSON response: {e}")

    # Check for API-level errors
    if "errors" in data and data["errors"]:
        error_messages = [error.get("message", str(error)) for error in data["errors"]]
        raise ValueError(f"API errors: {'; '.join(error_messages)}")

    return data


def handle_api_error(response) -> None:
    """
    Handle API error responses and raise appropriate exceptions.

    Args:
        response: HTTP response object

    Raises:
        AutotaskAPIError: For API-specific errors
        AutotaskAuthError: For authentication errors
        AutotaskNotFoundError: For 404 errors
    """
    from .exceptions import AutotaskAPIError, AutotaskAuthError, AutotaskNotFoundError

    if response.status_code == 401:
        raise AutotaskAuthError("Authentication failed")
    elif response.status_code == 404:
        raise AutotaskNotFoundError("Resource not found")
    elif response.status_code >= 400:
        try:
            error_data = response.json()
            error_message = error_data.get("message", f"HTTP {response.status_code}")
        except (ValueError, TypeError):
            error_message = f"HTTP {response.status_code}: {response.text}"

        raise AutotaskAPIError(f"API error: {error_message}")
