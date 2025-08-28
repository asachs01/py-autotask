"""
Type definitions for py-autotask.

This module provides type hints and data structures for better IDE support
and runtime validation using Pydantic.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class FilterOperation(str, Enum):
    """Enumeration of supported filter operations for Autotask API queries."""

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    BEGINS_WITH = "beginsWith"
    ENDS_WITH = "endsWith"
    CONTAINS = "contains"
    IS_NULL = "isNull"
    IS_NOT_NULL = "isNotNull"
    IN = "in"
    NOT_IN = "notIn"
    BETWEEN = "between"


class QueryFilter(BaseModel):
    """Represents a single filter condition in an Autotask API query."""

    op: FilterOperation = Field(..., description="Filter operation")
    field: str = Field(..., description="Field name to filter on")
    value: Optional[Union[str, int, float, bool, List[Any]]] = Field(
        None, description="Filter value"
    )
    udf: bool = Field(False, description="Whether this is a user-defined field")


class PaginationInfo(BaseModel):
    """Information about pagination in API responses."""

    count: int = Field(..., description="Number of items in current page")
    request_count: int = Field(
        ..., alias="requestCount", description="Requested page size"
    )
    prev_page_url: Optional[str] = Field(
        None, alias="prevPageUrl", description="URL for previous page"
    )
    next_page_url: Optional[str] = Field(
        None, alias="nextPageUrl", description="URL for next page"
    )


class QueryRequest(BaseModel):
    """Structure for API query requests."""

    filter: Optional[List[QueryFilter]] = Field(
        None, description="List of filter conditions"
    )
    include_fields: Optional[List[str]] = Field(
        None, alias="includeFields", description="Fields to include in response"
    )
    max_records: Optional[int] = Field(
        None, alias="maxRecords", description="Maximum records to return"
    )


class QueryResponse(BaseModel):
    """Structure for API query responses."""

    items: List[Dict[str, Any]] = Field(..., description="Query result items")
    page_details: PaginationInfo = Field(
        ..., alias="pageDetails", description="Pagination information"
    )


class EntityMetadata(BaseModel):
    """Metadata information about an Autotask entity."""

    name: str = Field(..., description="Entity name")
    can_create: bool = Field(..., alias="canCreate")
    can_update: bool = Field(..., alias="canUpdate")
    can_query: bool = Field(..., alias="canQuery")
    can_delete: bool = Field(..., alias="canDelete")
    has_user_defined_fields: bool = Field(..., alias="hasUserDefinedFields")


class FieldMetadata(BaseModel):
    """Metadata about a specific field in an entity."""

    name: str = Field(..., description="Field name")
    data_type: str = Field(..., alias="dataType", description="Field data type")
    length: int = Field(..., description="Maximum field length")
    is_required: bool = Field(..., alias="isRequired")
    is_read_only: bool = Field(..., alias="isReadOnly")
    is_queryable: bool = Field(..., alias="isQueryable")
    is_reference: bool = Field(..., alias="isReference")
    reference_entity_type: str = Field(
        "", alias="referenceEntityType", description="Referenced entity type"
    )
    is_pick_list: bool = Field(..., alias="isPickList")
    picklist_values: Optional[List[Dict[str, Any]]] = Field(
        None, alias="picklistValues"
    )
    picklist_parent_value_field: str = Field("", alias="picklistParentValueField")


class CreateResponse(BaseModel):
    """Response from entity creation operations."""

    item_id: int = Field(..., alias="itemId", description="ID of created item")


class UpdateResponse(BaseModel):
    """Response from entity update operations."""

    item_id: int = Field(..., alias="itemId", description="ID of updated item")


class ZoneInfo(BaseModel):
    """Information about an Autotask zone."""

    url: str = Field(..., description="Zone API URL")
    zone_name: Optional[str] = Field(None, alias="zoneName", description="Zone name")
    web_url: Optional[str] = Field(None, alias="webUrl", description="Web URL")
    ci: Optional[int] = Field(None, description="CI identifier")
    data_base_type: Optional[str] = Field(None, alias="dataBaseType")
    ci_level: Optional[int] = Field(None, alias="ciLevel")


class AuthCredentials(BaseModel):
    """Authentication credentials for Autotask API."""

    username: str = Field(..., description="API username")
    integration_code: str = Field(..., description="Integration code")
    secret: str = Field(..., description="API secret")
    api_url: Optional[str] = Field(None, description="Override API URL")


class RequestConfig(BaseModel):
    """Configuration for HTTP requests."""

    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, description="Base retry delay in seconds")
    retry_backoff: float = Field(2.0, description="Retry backoff multiplier")


# Type aliases for convenience
EntityDict = Dict[str, Any]
EntityList = List[EntityDict]
FilterDict = Dict[str, Any]

# Specific entity data types
TicketData = EntityDict
CompanyData = EntityDict
ContactData = EntityDict
ProjectData = EntityDict
ResourceData = EntityDict
ContractData = EntityDict


# Time Entry Related Types
class TimeEntryData(BaseModel):
    """Data structure for time entries."""

    id: Optional[int] = None
    resource_id: Optional[int] = None
    ticket_id: Optional[int] = None
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    start_date_time: Optional[str] = None
    end_date_time: Optional[str] = None
    hours_worked: Optional[float] = None
    hours_to_bill: Optional[float] = None
    billable_to_account: Optional[bool] = None
    non_billable: Optional[bool] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    summary_notes: Optional[str] = None
    type: Optional[int] = None
    created_date_time: Optional[str] = None
    last_modified_date_time: Optional[str] = None
    created_by: Optional[int] = None
    last_modified_by: Optional[int] = None


# Attachment Related Types
class AttachmentData(BaseModel):
    """Data structure for file attachments."""

    id: Optional[int] = None
    parent_type: Optional[str] = None
    parent_id: Optional[int] = None
    title: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    description: Optional[str] = None
    created_date_time: Optional[str] = None
    created_by: Optional[int] = None
    last_modified_date_time: Optional[str] = None
    last_modified_by: Optional[int] = None

    class Config:
        populate_by_name = True
        alias_generator = None
