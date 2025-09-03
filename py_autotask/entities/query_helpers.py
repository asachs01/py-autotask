"""
Query helper utilities for standardized query building.

This module provides utilities to build consistent QueryFilter objects
and handle common query patterns across all entities.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from ..types import FilterOperation, QueryFilter


def build_filter(
    field: str,
    operation: Union[str, FilterOperation],
    value: Optional[Union[str, int, float, bool, List[Any]]] = None,
    udf: bool = False,
) -> QueryFilter:
    """
    Build a QueryFilter object with proper validation.

    Args:
        field: Field name to filter on
        operation: Filter operation (string or FilterOperation enum)
        value: Filter value (None for isNull/isNotNull operations)
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter object

    Examples:
        build_filter("isActive", "eq", True)
        build_filter("accountType", FilterOperation.EQ, "Customer")
        build_filter("createdDate", "gte", "2023-01-01")
    """
    if isinstance(operation, str):
        operation = FilterOperation(operation)

    return QueryFilter(field=field, op=operation, value=value, udf=udf)


def build_equality_filter(field: str, value: Any, udf: bool = False) -> QueryFilter:
    """
    Build an equality filter.

    Args:
        field: Field name
        value: Value to match
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter for equality comparison
    """
    return build_filter(field, FilterOperation.EQ, value, udf)


def build_active_filter(active: bool = True) -> QueryFilter:
    """
    Build a standard active/inactive filter.

    Args:
        active: Whether to filter for active (True) or inactive (False) records

    Returns:
        QueryFilter for active status
    """
    return build_equality_filter("isActive", active)


def build_date_range_filters(
    field: str,
    start_date: Optional[Union[str, date, datetime]] = None,
    end_date: Optional[Union[str, date, datetime]] = None,
) -> List[QueryFilter]:
    """
    Build date range filters.

    Args:
        field: Date field name
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        List of QueryFilter objects for date range
    """
    filters = []

    if start_date:
        if isinstance(start_date, (date, datetime)):
            start_date = start_date.isoformat()
        filters.append(build_filter(field, FilterOperation.GTE, start_date))

    if end_date:
        if isinstance(end_date, (date, datetime)):
            end_date = end_date.isoformat()
        filters.append(build_filter(field, FilterOperation.LTE, end_date))

    return filters


def build_gte_filter(field: str, value: Any, udf: bool = False) -> QueryFilter:
    """
    Build a greater-than-or-equal filter.

    Args:
        field: Field name
        value: Minimum value
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter for >= comparison
    """
    return build_filter(field, FilterOperation.GTE, value, udf)


def build_lte_filter(field: str, value: Any, udf: bool = False) -> QueryFilter:
    """
    Build a less-than-or-equal filter.

    Args:
        field: Field name
        value: Maximum value
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter for <= comparison
    """
    return build_filter(field, FilterOperation.LTE, value, udf)


def build_search_filters(
    search_term: str, fields: List[str], case_sensitive: bool = False
) -> List[QueryFilter]:
    """
    Build search filters for multiple fields using 'contains' operation.

    Args:
        search_term: Term to search for
        fields: List of field names to search in
        case_sensitive: Whether search should be case sensitive

    Returns:
        List of QueryFilter objects for search (OR logic when used together)
    """
    filters = []
    operation = FilterOperation.CONTAINS

    # Note: Autotask API case sensitivity is handled server-side
    # We document the parameter but don't modify the search term
    for field in fields:
        filters.append(build_filter(field, operation, search_term))

    return filters


def build_in_filter(field: str, values: List[Any], udf: bool = False) -> QueryFilter:
    """
    Build an 'in' filter for multiple values.

    Args:
        field: Field name
        values: List of values to match
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter for 'in' operation
    """
    # Convert values to strings for API compatibility
    string_values = [str(v) for v in values]
    return build_filter(field, FilterOperation.IN, string_values, udf)


def build_null_filter(
    field: str, is_null: bool = True, udf: bool = False
) -> QueryFilter:
    """
    Build a null/not null filter.

    Args:
        field: Field name
        is_null: Whether to filter for null (True) or not null (False) values
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter for null check
    """
    operation = FilterOperation.IS_NULL if is_null else FilterOperation.IS_NOT_NULL
    return build_filter(field, operation, udf=udf)


def combine_filters(
    filters: List[QueryFilter], logic: str = "and"
) -> List[QueryFilter]:
    """
    Combine multiple filters with specified logic.

    Note: The Autotask API handles multiple filters in a list as AND logic by default.
    For OR logic, you typically need to use a single filter with multiple values
    or structure the query differently.

    Args:
        filters: List of QueryFilter objects
        logic: Logic operator ("and" or "or") - currently only "and" is supported

    Returns:
        List of QueryFilter objects
    """
    if logic.lower() != "and":
        raise ValueError(
            "Only 'and' logic is currently supported. "
            "For OR logic, use 'in' operation or multiple separate queries."
        )

    return filters


def convert_string_filter_to_query_filter(filter_string: str) -> List[QueryFilter]:
    """
    Convert old string-based filter format to QueryFilter objects.

    Args:
        filter_string: String like "field eq 'value'" or "field1 eq 'value1' and field2 gt 2"

    Returns:
        List of QueryFilter objects

    Examples:
        convert_string_filter_to_query_filter("isActive eq true")
        convert_string_filter_to_query_filter("accountType eq 'Customer' and isActive eq true")
    """
    import re

    # Simple regex to parse filter strings
    # This handles basic patterns like "field op value" and "field1 op1 value1 and field2 op2 value2"
    filters = []

    # Split by 'and' first
    and_parts = filter_string.split(" and ")

    for part in and_parts:
        # Split by 'or' if present
        or_parts = part.split(" or ")

        if len(or_parts) > 1:
            # This is complex OR logic - not easily convertible
            # For now, we'll handle the first part and warn about the rest
            part = or_parts[0]
            # TODO: Handle OR logic properly

        # Parse individual filter: "field op value"
        # Handle quoted values and unquoted values
        match = re.match(r"(\w+)\s+(\w+)\s+(.+)", part.strip())
        if match:
            field, op, value_str = match.groups()

            # Parse value
            value_str = value_str.strip()
            if value_str.startswith("'") and value_str.endswith("'"):
                # String value
                value = value_str[1:-1]
            elif value_str.lower() == "true":
                value = True
            elif value_str.lower() == "false":
                value = False
            elif value_str.lower() == "null":
                value = None
            else:
                # Try to parse as number
                try:
                    if "." in value_str:
                        value = float(value_str)
                    else:
                        value = int(value_str)
                except ValueError:
                    # Keep as string
                    value = value_str

            filters.append(build_filter(field, op, value))

    return filters


def build_parent_child_filter(
    parent_field: str,
    parent_id: int,
    additional_filters: Optional[List[QueryFilter]] = None,
) -> List[QueryFilter]:
    """
    Build filters for parent-child entity relationships.

    Args:
        parent_field: Name of the parent ID field (e.g., "companyID", "projectID")
        parent_id: ID of the parent entity
        additional_filters: Additional filters to combine

    Returns:
        List of QueryFilter objects
    """
    filters = [build_equality_filter(parent_field, str(parent_id))]

    if additional_filters:
        filters.extend(additional_filters)

    return filters


def build_status_filter(
    status_field: str = "status", status_value: Union[str, int] = 1
) -> QueryFilter:
    """
    Build a status filter for active/open items.

    Args:
        status_field: Name of the status field
        status_value: Value representing active/open status

    Returns:
        QueryFilter for status
    """
    return build_equality_filter(status_field, status_value)


def build_type_filter(
    type_field: str, type_value: Union[str, int], udf: bool = False
) -> QueryFilter:
    """
    Build a type filter.

    Args:
        type_field: Name of the type field
        type_value: Type value to filter for
        udf: Whether this is a user-defined field

    Returns:
        QueryFilter for type
    """
    return build_equality_filter(type_field, type_value, udf)
