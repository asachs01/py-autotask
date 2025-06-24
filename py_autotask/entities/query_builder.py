"""
Advanced query builder for Autotask API entities.

This module provides sophisticated query building capabilities including
relationship queries, complex filtering, and query optimization.
"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..exceptions import AutotaskValidationError
from ..types import EntityDict, EntityList, QueryRequest

if TYPE_CHECKING:
    from .base import BaseEntity

logger = logging.getLogger(__name__)


class FilterOperator(Enum):
    """Supported filter operators for query building."""

    EQUAL = "eq"
    NOT_EQUAL = "ne"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    BEGINS_WITH = "beginsWith"
    ENDS_WITH = "endsWith"
    CONTAINS = "contains"
    NOT_CONTAINS = "notContains"
    IS_NULL = "isNull"
    IS_NOT_NULL = "isNotNull"
    IN = "in"
    NOT_IN = "notIn"
    EXISTS = "exist"
    NOT_EXISTS = "notExist"


class LogicalOperator(Enum):
    """Logical operators for combining filters."""

    AND = "and"
    OR = "or"


class QueryBuilder:
    """
    Advanced query builder for constructing complex Autotask API queries.

    Supports filtering, sorting, field selection, relationship queries,
    and query optimization.
    """

    def __init__(self, entity: "BaseEntity") -> None:
        """
        Initialize query builder for an entity.

        Args:
            entity: The entity to build queries for
        """
        self.entity = entity
        self.logger = logging.getLogger(f"{__name__}.{entity.entity_name}")
        self._filters: List[Dict[str, Any]] = []
        self._include_fields: Optional[List[str]] = None
        self._max_records: Optional[int] = None
        self._sort_fields: List[Dict[str, str]] = []

    def reset(self) -> "QueryBuilder":
        """
        Reset the query builder to start fresh.

        Returns:
            Self for method chaining
        """
        self._filters.clear()
        self._include_fields = None
        self._max_records = None
        self._sort_fields.clear()
        return self

    def where(
        self,
        field: str,
        operator: Union[FilterOperator, str],
        value: Any = None,
    ) -> "QueryBuilder":
        """
        Add a filter condition to the query.

        Args:
            field: Field name to filter on
            operator: Filter operator
            value: Value to compare against (not needed for isNull/isNotNull)

        Returns:
            Self for method chaining

        Example:
            query.where("status", FilterOperator.EQUAL, "1")
            query.where("priority", "gte", 3)
            query.where("description", FilterOperator.CONTAINS, "urgent")
        """
        if isinstance(operator, FilterOperator):
            op_str = operator.value
        else:
            op_str = operator

        filter_dict = {
            "field": field,
            "op": op_str,
        }

        # Some operators don't need a value
        if op_str not in ["isNull", "isNotNull"]:
            if value is None:
                raise AutotaskValidationError(
                    f"Value is required for operator '{op_str}'"
                )
            filter_dict["value"] = str(value)

        self._filters.append(filter_dict)
        self.logger.debug(f"Added filter: {field} {op_str} {value}")
        return self

    def where_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """
        Add an 'IN' filter for multiple values.

        Args:
            field: Field name to filter on
            values: List of values to match

        Returns:
            Self for method chaining

        Example:
            query.where_in("status", ["1", "2", "3"])
            query.where_in("priority", [3, 4, 5])
        """
        if not values:
            raise AutotaskValidationError("Values list cannot be empty for 'IN' filter")

        # Convert all values to strings for API
        str_values = [str(v) for v in values]

        self._filters.append({"field": field, "op": "in", "value": str_values})

        self.logger.debug(f"Added IN filter: {field} in {str_values}")
        return self

    def where_null(self, field: str, is_null: bool = True) -> "QueryBuilder":
        """
        Add a null/not null filter.

        Args:
            field: Field name to check
            is_null: True for IS NULL, False for IS NOT NULL

        Returns:
            Self for method chaining

        Example:
            query.where_null("description")  # IS NULL
            query.where_null("assignedResourceID", False)  # IS NOT NULL
        """
        operator = "isNull" if is_null else "isNotNull"

        self._filters.append(
            {
                "field": field,
                "op": operator,
            }
        )

        self.logger.debug(f"Added null filter: {field} {operator}")
        return self

    def where_date_range(
        self,
        field: str,
        start_date: str,
        end_date: str,
    ) -> "QueryBuilder":
        """
        Add a date range filter.

        Args:
            field: Date field name
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Self for method chaining

        Example:
            query.where_date_range(
                "createDateTime",
                "2023-01-01T00:00:00Z",
                "2023-12-31T23:59:59Z"
            )
        """
        self.where(field, FilterOperator.GREATER_THAN_OR_EQUAL, start_date)
        self.where(field, FilterOperator.LESS_THAN_OR_EQUAL, end_date)

        self.logger.debug(
            f"Added date range filter: {field} between {start_date} and {end_date}"
        )
        return self

    def where_related(
        self,
        related_entity: str,
        related_field: str,
        operator: Union[FilterOperator, str],
        value: Any,
    ) -> "QueryBuilder":
        """
        Add a filter based on a related entity field.

        Args:
            related_entity: Name of the related entity
            related_field: Field in the related entity
            operator: Filter operator
            value: Value to compare against

        Returns:
            Self for method chaining

        Example:
            # Find tickets where the company name contains "Acme"
            query.where_related("Companies", "companyName", "contains", "Acme")
        """
        # Get the relationship field name
        relationship_field = self.entity._get_parent_field_name(related_entity)

        # First, find the related entity IDs that match the criteria
        related_handler = self.entity.client.entities.get_entity(related_entity)
        related_query = QueryBuilder(related_handler)
        related_response = (
            related_query.where(related_field, operator, value).select(["id"]).execute()
        )

        if not related_response.items:
            # No matching related entities found, add impossible filter
            self.where("id", FilterOperator.EQUAL, -1)
            self.logger.debug(
                f"No matching {related_entity} found for {related_field} {operator} {value}"
            )
        else:
            # Add filter for the relationship field
            related_ids = [str(item["id"]) for item in related_response.items]
            self.where_in(relationship_field, related_ids)
            self.logger.debug(
                f"Added related filter: {relationship_field} in {len(related_ids)} matching {related_entity} IDs"
            )

        return self

    def select(self, fields: List[str]) -> "QueryBuilder":
        """
        Specify which fields to include in the response.

        Args:
            fields: List of field names to include

        Returns:
            Self for method chaining

        Example:
            query.select(["id", "title", "status", "priority"])
        """
        self._include_fields = fields
        self.logger.debug(f"Set include fields: {fields}")
        return self

    def limit(self, max_records: int) -> "QueryBuilder":
        """
        Limit the number of records returned.

        Args:
            max_records: Maximum number of records

        Returns:
            Self for method chaining

        Example:
            query.limit(100)
        """
        self._max_records = max_records
        self.logger.debug(f"Set max records: {max_records}")
        return self

    def order_by(self, field: str, direction: str = "asc") -> "QueryBuilder":
        """
        Add sorting to the query.

        Args:
            field: Field name to sort by
            direction: Sort direction ("asc" or "desc")

        Returns:
            Self for method chaining

        Example:
            query.order_by("createDateTime", "desc")
            query.order_by("priority").order_by("status")
        """
        if direction not in ["asc", "desc"]:
            raise AutotaskValidationError("Sort direction must be 'asc' or 'desc'")

        self._sort_fields.append({"field": field, "direction": direction})

        self.logger.debug(f"Added sort: {field} {direction}")
        return self

    def build(self) -> QueryRequest:
        """
        Build the final QueryRequest object.

        Returns:
            Configured QueryRequest
        """
        query_request = QueryRequest()

        if self._filters:
            query_request.filter = self._filters

        if self._include_fields:
            query_request.include_fields = self._include_fields

        if self._max_records:
            query_request.max_records = self._max_records

        # Note: Autotask API sorting would need to be implemented
        # based on actual API capabilities
        if self._sort_fields:
            self.logger.warning(
                "Sorting is built but may not be supported by Autotask API"
            )

        self.logger.debug(f"Built query with {len(self._filters)} filters")
        return query_request

    def execute(self) -> Any:
        """
        Execute the query and return results.

        Returns:
            Query response from the API
        """
        query_request = self.build()
        self.logger.debug(f"Executing query for {self.entity.entity_name}")
        return self.entity.client.query(self.entity.entity_name, query_request)

    def execute_all(self, **kwargs) -> EntityList:
        """
        Execute the query with automatic pagination to get all results.

        Args:
            **kwargs: Additional arguments for query_all

        Returns:
            List of all matching entities
        """
        self.logger.debug(f"Executing paginated query for {self.entity.entity_name}")
        return self.entity.query_all(
            filters=self._filters, include_fields=self._include_fields, **kwargs
        )

    def count(self) -> int:
        """
        Execute the query and return only the count of matching records.

        Returns:
            Number of matching records
        """
        self.logger.debug(f"Executing count query for {self.entity.entity_name}")
        return self.entity.count(filters=self._filters)

    def first(self) -> Optional[EntityDict]:
        """
        Execute the query and return only the first result.

        Returns:
            First matching entity or None
        """
        original_max = self._max_records
        self._max_records = 1

        try:
            response = self.execute()
            return response.items[0] if response.items else None
        finally:
            self._max_records = original_max

    def exists(self) -> bool:
        """
        Check if any records match the query criteria.

        Returns:
            True if at least one record matches
        """
        return self.count() > 0


# Add query builder method to BaseEntity
def add_query_builder_to_base_entity():
    """Add query builder method to BaseEntity class."""
    from .base import BaseEntity

    def query_builder(self) -> QueryBuilder:
        """
        Create a new query builder for this entity.

        Returns:
            New QueryBuilder instance

        Example:
            tickets = (client.tickets.query_builder()
                      .where("status", "eq", "1")
                      .where("priority", "gte", 3)
                      .order_by("createDateTime", "desc")
                      .limit(100)
                      .execute_all())
        """
        return QueryBuilder(self)

    # Add method to BaseEntity class
    BaseEntity.query_builder = query_builder
