"""
Base entity class for Autotask API entities.

This module provides the base class that all entity-specific classes
inherit from, providing common CRUD operations and utilities.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..exceptions import AutotaskValidationError
from ..types import CreateResponse, EntityDict, EntityList, QueryRequest, QueryResponse

if TYPE_CHECKING:
    from ..client import AutotaskClient
    from .query_builder import QueryBuilder

logger = logging.getLogger(__name__)


class BaseEntity:
    """
    Base class for all Autotask API entities.

    Provides common CRUD operations that work across all entity types.
    Individual entity classes can override these methods to provide
    entity-specific behavior.
    """

    def __init__(self, client: "AutotaskClient", entity_name: str) -> None:
        """
        Initialize the entity handler.

        Args:
            client: The AutotaskClient instance
            entity_name: Name of the entity (e.g., 'Tickets', 'Companies')
        """
        self.client = client
        self.entity_name = entity_name
        self.logger = logging.getLogger(f"{__name__}.{entity_name}")

    def get(self, entity_id: int) -> Optional[EntityDict]:
        """
        Get a single entity by ID.

        Args:
            entity_id: The entity ID to retrieve

        Returns:
            Entity data or None if not found

        Example:
            ticket = client.tickets.get(12345)
        """
        self.logger.debug(f"Getting {self.entity_name} with ID {entity_id}")
        return self.client.get(self.entity_name, entity_id)

    def query(
        self,
        filters: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        include_fields: Optional[List[str]] = None,
        max_records: Optional[int] = None,
    ) -> QueryResponse:
        """
        Query entities with optional filtering.

        Args:
            filters: Filter conditions (can be single dict or list of dicts)
            include_fields: Specific fields to include in response
            max_records: Maximum number of records to return

        Returns:
            Query response with items and pagination info

        Example:
            # Single filter
            companies = client.companies.query({"field": "isActive", "op": "eq", "value": "true"})

            # Multiple filters
            tickets = client.tickets.query([
                {"field": "status", "op": "eq", "value": "1"},
                {"field": "priority", "op": "gte", "value": "3"}
            ])
        """
        # Build query request
        query_request = QueryRequest()

        if filters:
            if isinstance(filters, dict):
                # Single filter dict
                query_request.filter = [filters]
            elif isinstance(filters, list):
                # List of filter dicts
                query_request.filter = filters
            else:
                raise AutotaskValidationError("Filters must be dict or list of dicts")

        if include_fields:
            query_request.include_fields = include_fields

        if max_records:
            query_request.max_records = max_records

        self.logger.debug(f"Querying {self.entity_name} with filters: {filters}")
        return self.client.query(self.entity_name, query_request)

    def query_all(
        self,
        filters: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        include_fields: Optional[List[str]] = None,
        max_total_records: Optional[int] = None,
        page_size: int = 500,
    ) -> EntityList:
        """
        Query all entities, automatically handling pagination.

        Args:
            filters: Filter conditions
            include_fields: Specific fields to include in response
            max_total_records: Maximum total records to retrieve (safety limit)
            page_size: Number of records per page (default 500, max 500)

        Returns:
            List of all matching entities

        Example:
            all_active_companies = client.companies.query_all(
                {"field": "isActive", "op": "eq", "value": "true"},
                max_total_records=10000
            )
        """
        all_items = []
        total_retrieved = 0
        page_count = 0
        max_pages = 100  # Safety limit to prevent infinite loops

        # Validate page size
        page_size = min(max(page_size, 1), 500)  # Clamp between 1 and 500

        query_request = QueryRequest()
        query_request.max_records = page_size

        if filters:
            if isinstance(filters, dict):
                query_request.filter = [filters]
            elif isinstance(filters, list):
                query_request.filter = filters

        if include_fields:
            query_request.include_fields = include_fields

        self.logger.debug(
            f"Querying all {self.entity_name} with pagination "
            f"(page_size={page_size}, max_total={max_total_records})"
        )

        while page_count < max_pages:
            try:
                response = self.client.query(self.entity_name, query_request)

                if not response.items:
                    self.logger.debug("No more items found, stopping pagination")
                    break

                all_items.extend(response.items)
                total_retrieved += len(response.items)
                page_count += 1

                self.logger.debug(
                    f"Retrieved page {page_count}: {len(response.items)} items "
                    f"(total: {total_retrieved})"
                )

                # Check safety limits
                if max_total_records and total_retrieved >= max_total_records:
                    self.logger.warning(
                        f"Reached max_total_records limit ({max_total_records}), "
                        f"stopping pagination"
                    )
                    all_items = all_items[:max_total_records]
                    break

                # Check if there are more pages
                page_details = response.page_details
                if not page_details or not hasattr(page_details, "next_page_url"):
                    self.logger.debug("No pagination details found, stopping")
                    break

                if not page_details.next_page_url:
                    self.logger.debug("No next page URL, pagination complete")
                    break

                # For Autotask API, pagination typically uses cursor-based approach
                # Extract cursor from next_page_url if available
                if hasattr(page_details, "page_cursors") and page_details.page_cursors:
                    # Use cursor-based pagination
                    if hasattr(page_details.page_cursors, "next"):
                        query_request.page_cursor = page_details.page_cursors.next
                    else:
                        break
                else:
                    # Fallback to offset-based pagination
                    current_offset = getattr(query_request, "offset", 0)
                    query_request.offset = current_offset + page_size

            except Exception as e:
                self.logger.error(
                    f"Error during pagination on page {page_count + 1}: {e}"
                )
                if page_count == 0:
                    # If first page fails, re-raise the error
                    raise
                else:
                    # If subsequent pages fail, log warning and return what we have
                    self.logger.warning(
                        f"Pagination stopped due to error on page {page_count + 1}. "
                        f"Returning {total_retrieved} items."
                    )
                    break

        if page_count >= max_pages:
            self.logger.warning(
                f"Reached maximum page limit ({max_pages}), "
                f"there may be more data available"
            )

        self.logger.debug(
            f"Pagination complete: Retrieved {len(all_items)} {self.entity_name} items "
            f"in {page_count} pages"
        )
        return all_items

    def create(self, entity_data: EntityDict) -> CreateResponse:
        """
        Create a new entity.

        Args:
            entity_data: Data for the new entity

        Returns:
            Create response with new entity ID

        Example:
            new_company = client.companies.create({
                "companyName": "Test Company",
                "companyType": 1,
                "ownerResourceID": 12345
            })
        """
        self.logger.debug(f"Creating new {self.entity_name}")
        return self.client.create_entity(self.entity_name, entity_data)

    def update(self, entity_data: EntityDict) -> EntityDict:
        """
        Update an existing entity.

        Args:
            entity_data: Entity data including ID and fields to update

        Returns:
            Updated entity data

        Example:
            updated_ticket = client.tickets.update({
                "id": 12345,
                "title": "Updated Title",
                "priority": 4
            })
        """
        entity_id = entity_data.get("id")
        self.logger.debug(f"Updating {self.entity_name} with ID {entity_id}")
        return self.client.update(self.entity_name, entity_data)

    def update_by_id(
        self, entity_id: int, update_data: EntityDict
    ) -> Optional[EntityDict]:
        """
        Helper method to update an entity by ID.

        Args:
            entity_id: ID of entity to update
            update_data: Data to update

        Returns:
            Updated entity data or None if not found
        """
        entity_data = {"id": entity_id, **update_data}
        return self.client.update(self.entity_name, entity_data)

    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if successful

        Example:
            success = client.tickets.delete(12345)
        """
        self.logger.debug(f"Deleting {self.entity_name} with ID {entity_id}")
        return self.client.delete(self.entity_name, entity_id)

    def count(
        self,
        filters: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    ) -> int:
        """
        Count entities matching filter criteria.

        Args:
            filters: Filter conditions

        Returns:
            Count of matching entities

        Example:
            active_company_count = client.companies.count(
                {"field": "isActive", "op": "eq", "value": "true"}
            )
        """
        query_request = QueryRequest()

        if filters:
            if isinstance(filters, dict):
                query_request.filter = [filters]
            elif isinstance(filters, list):
                query_request.filter = filters

        self.logger.debug(f"Counting {self.entity_name} with filters: {filters}")
        return self.client.count(self.entity_name, query_request)

    def get_field_info(self) -> Dict[str, Any]:
        """
        Get field metadata for this entity.

        Returns:
            Field metadata information

        Example:
            field_info = client.tickets.get_field_info()
        """
        self.logger.debug(f"Getting field info for {self.entity_name}")
        return self.client.get_field_info(self.entity_name)

    def get_entity_info(self) -> Dict[str, Any]:
        """
        Get general information about this entity.

        Returns:
            Entity information

        Example:
            entity_info = client.tickets.get_entity_info()
        """
        self.logger.debug(f"Getting entity info for {self.entity_name}")
        return self.client.get_entity_info(self.entity_name)

    # Parent-Child Entity Relationship Methods

    def get_children(
        self,
        parent_id: int,
        child_entity: str,
        filters: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        include_fields: Optional[List[str]] = None,
    ) -> EntityList:
        """
        Get child entities related to a parent entity.

        Args:
            parent_id: ID of the parent entity
            child_entity: Name of the child entity type
            filters: Additional filter conditions
            include_fields: Specific fields to include in response

        Returns:
            List of child entities

        Example:
            # Get all tickets for a company
            tickets = client.companies.get_children(12345, "Tickets")

            # Get active tickets for a project
            active_tickets = client.projects.get_children(
                67890,
                "Tickets",
                {"field": "status", "op": "eq", "value": "1"}
            )
        """
        # Build parent filter
        parent_field = self._get_parent_field_name(child_entity)
        parent_filter = {"field": parent_field, "op": "eq", "value": str(parent_id)}

        # Combine with additional filters
        combined_filters = [parent_filter]
        if filters:
            if isinstance(filters, dict):
                combined_filters.append(filters)
            elif isinstance(filters, list):
                combined_filters.extend(filters)

        # Get child entity handler
        child_handler = self.client.entities.get_entity(child_entity)

        self.logger.debug(
            f"Getting {child_entity} children for {self.entity_name} ID {parent_id}"
        )

        return child_handler.query_all(
            filters=combined_filters, include_fields=include_fields
        )

    def get_parent(
        self,
        child_id: int,
        parent_entity: str,
        include_fields: Optional[List[str]] = None,
    ) -> Optional[EntityDict]:
        """
        Get parent entity for a child entity.

        Args:
            child_id: ID of the child entity
            parent_entity: Name of the parent entity type
            include_fields: Specific fields to include in response

        Returns:
            Parent entity data or None if not found

        Example:
            # Get company for a ticket
            company = client.tickets.get_parent(12345, "Companies")

            # Get project for a task
            project = client.tasks.get_parent(67890, "Projects")
        """
        # First get the child entity to find parent ID
        child_data = self.get(child_id)
        if not child_data:
            return None

        parent_field = self._get_parent_field_name(parent_entity)
        parent_id = child_data.get(parent_field)

        if not parent_id:
            self.logger.debug(
                f"No parent {parent_entity} found for {self.entity_name} ID {child_id}"
            )
            return None

        # Get parent entity handler and retrieve parent
        parent_handler = self.client.entities.get_entity(parent_entity)

        self.logger.debug(
            f"Getting {parent_entity} parent (ID {parent_id}) for {self.entity_name} ID {child_id}"
        )

        if include_fields:
            # Query with specific fields
            response = parent_handler.query(
                filters={"field": "id", "op": "eq", "value": str(parent_id)},
                include_fields=include_fields,
            )
            return response.items[0] if response.items else None
        else:
            return parent_handler.get(int(parent_id))

    def link_to_parent(
        self,
        child_id: int,
        parent_id: int,
        parent_entity: str,
    ) -> EntityDict:
        """
        Link a child entity to a parent entity.

        Args:
            child_id: ID of the child entity
            parent_id: ID of the parent entity
            parent_entity: Name of the parent entity type

        Returns:
            Updated child entity data

        Example:
            # Link ticket to a company
            updated_ticket = client.tickets.link_to_parent(12345, 67890, "Companies")

            # Link task to a project
            updated_task = client.tasks.link_to_parent(11111, 22222, "Projects")
        """
        parent_field = self._get_parent_field_name(parent_entity)

        update_data = {"id": child_id, parent_field: parent_id}

        self.logger.debug(
            f"Linking {self.entity_name} ID {child_id} to {parent_entity} ID {parent_id}"
        )

        return self.update(update_data)

    def unlink_from_parent(
        self,
        child_id: int,
        parent_entity: str,
    ) -> EntityDict:
        """
        Remove link between child and parent entity.

        Args:
            child_id: ID of the child entity
            parent_entity: Name of the parent entity type

        Returns:
            Updated child entity data

        Example:
            # Remove company link from ticket
            updated_ticket = client.tickets.unlink_from_parent(12345, "Companies")
        """
        parent_field = self._get_parent_field_name(parent_entity)

        update_data = {"id": child_id, parent_field: None}

        self.logger.debug(
            f"Unlinking {self.entity_name} ID {child_id} from {parent_entity}"
        )

        return self.update(update_data)

    def _get_parent_field_name(self, entity_name: str) -> str:
        """
        Get the field name used to reference a parent entity.

        Args:
            entity_name: Name of the parent entity

        Returns:
            Field name for the parent relationship
        """
        # Autotask standard field naming conventions
        field_mappings = {
            "Companies": "companyID",
            "Accounts": "accountID",
            "Projects": "projectID",
            "Contracts": "contractID",
            "Resources": "resourceID",
            "Tickets": "ticketID",
            "Tasks": "taskID",
            "Opportunities": "opportunityID",
            "Quotes": "quoteID",
            "Contacts": "contactID",
            "Products": "productID",
            "Services": "serviceID",
            "Phases": "phaseID",
        }

        field_name = field_mappings.get(entity_name)
        if not field_name:
            # Fallback to standard naming convention
            field_name = f"{entity_name.lower().rstrip('s')}ID"

        return field_name

    # Batch Operations for Entity Relationships

    def batch_link_children(
        self,
        parent_id: int,
        child_ids: List[int],
        child_entity: str,
    ) -> List[EntityDict]:
        """
        Link multiple child entities to a parent in batch.

        Args:
            parent_id: ID of the parent entity
            child_ids: List of child entity IDs
            child_entity: Name of the child entity type

        Returns:
            List of updated child entities

        Example:
            # Link multiple tickets to a company
            updated_tickets = client.companies.batch_link_children(
                12345, [1001, 1002, 1003], "Tickets"
            )
        """
        child_handler = self.client.entities.get_entity(child_entity)
        parent_field = child_handler._get_parent_field_name(self.entity_name)

        results = []

        self.logger.debug(
            f"Batch linking {len(child_ids)} {child_entity} to {self.entity_name} ID {parent_id}"
        )

        for child_id in child_ids:
            try:
                update_data = {"id": child_id, parent_field: parent_id}
                updated_entity = child_handler.update(update_data)
                results.append(updated_entity)
            except Exception as e:
                self.logger.error(
                    f"Failed to link {child_entity} ID {child_id} to "
                    f"{self.entity_name} ID {parent_id}: {e}"
                )
                # Continue with other entities
                continue

        self.logger.debug(
            f"Successfully linked {len(results)}/{len(child_ids)} {child_entity} entities"
        )

        return results

    # Batch Operations for Phase 4
    def batch_create(
        self, entities_data: List[EntityDict], batch_size: int = 200
    ) -> List[CreateResponse]:
        """
        Create multiple entities in batches.

        Args:
            entities_data: List of entity data to create
            batch_size: Maximum entities per batch (default: 200, API limit)

        Returns:
            List of create responses

        Example:
            tickets_data = [
                {"title": "Issue 1", "description": "First issue"},
                {"title": "Issue 2", "description": "Second issue"}
            ]
            results = client.tickets.batch_create(tickets_data)
            for result in results:
                print(f"Created entity with ID: {result.item_id}")
        """
        self.logger.info(
            f"Starting batch create of {len(entities_data)} {self.entity_name} entities"
        )

        try:
            results = self.client.batch_create(
                self.entity_name, entities_data, batch_size
            )

            self.logger.info(
                f"Successfully created {len(results)} {self.entity_name} entities"
            )
            return results

        except Exception as e:
            self.logger.error(f"Batch create failed for {self.entity_name}: {e}")
            raise

    def batch_update(
        self, entities_data: List[EntityDict], batch_size: int = 200
    ) -> List[EntityDict]:
        """
        Update multiple entities in batches.

        Args:
            entities_data: List of entity data to update (must include 'id' field)
            batch_size: Maximum entities per batch (default: 200, API limit)

        Returns:
            List of updated entity data

        Example:
            updates = [
                {"id": 12345, "status": "Completed"},
                {"id": 12346, "priority": "High"}
            ]
            results = client.tickets.batch_update(updates)
        """
        self.logger.info(
            f"Starting batch update of {len(entities_data)} {self.entity_name} entities"
        )

        try:
            results = self.client.batch_update(
                self.entity_name, entities_data, batch_size
            )

            self.logger.info(
                f"Successfully updated {len(results)} {self.entity_name} entities"
            )
            return results

        except Exception as e:
            self.logger.error(f"Batch update failed for {self.entity_name}: {e}")
            raise

    def batch_delete(self, entity_ids: List[int], batch_size: int = 200) -> List[bool]:
        """
        Delete multiple entities in batches.

        Args:
            entity_ids: List of entity IDs to delete
            batch_size: Maximum entities per batch (default: 200, API limit)

        Returns:
            List of success indicators (True for successful deletion)

        Example:
            ids_to_delete = [12345, 12346, 12347]
            results = client.tickets.batch_delete(ids_to_delete)
            successful_deletions = sum(results)
        """
        self.logger.info(
            f"Starting batch delete of {len(entity_ids)} {self.entity_name} entities"
        )

        try:
            results = self.client.batch_delete(self.entity_name, entity_ids, batch_size)

            successful_count = sum(results)
            self.logger.info(
                f"Successfully deleted {successful_count}/{len(entity_ids)} {self.entity_name} entities"
            )
            return results

        except Exception as e:
            self.logger.error(f"Batch delete failed for {self.entity_name}: {e}")
            raise

    def batch_get(
        self,
        entity_ids: List[int],
        batch_size: int = 20,
        include_fields: Optional[List[str]] = None,
    ) -> List[Optional[EntityDict]]:
        """
        Retrieve multiple entities by ID in batches.

        Args:
            entity_ids: List of entity IDs to retrieve
            batch_size: Number of entities to retrieve per batch
            include_fields: Specific fields to include in response

        Returns:
            List of entity data (None for entities not found)

        Example:
            tickets = client.tickets.batch_get([1001, 1002, 1003])
            valid_tickets = [t for t in tickets if t is not None]
        """
        results = []
        total_batches = (len(entity_ids) + batch_size - 1) // batch_size

        self.logger.debug(
            f"Batch retrieving {len(entity_ids)} {self.entity_name} in {total_batches} batches"
        )

        for i in range(0, len(entity_ids), batch_size):
            batch = entity_ids[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            self.logger.debug(
                f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)"
            )

            # Use query with IN filter for efficiency
            try:
                response = self.query(
                    filters={
                        "field": "id",
                        "op": "in",
                        "value": [str(id) for id in batch],
                    },
                    include_fields=include_fields,
                )

                # Create a map of ID to entity data
                entity_map = {int(item["id"]): item for item in response.items}

                # Add results in the same order as requested IDs
                for entity_id in batch:
                    results.append(entity_map.get(entity_id))

            except Exception as e:
                self.logger.error(f"Failed to retrieve batch {batch_num}: {e}")
                # Add None for all entities in this failed batch
                results.extend([None] * len(batch))

        found_count = sum(1 for r in results if r is not None)
        self.logger.debug(
            f"Batch retrieve complete: {found_count}/{len(entity_ids)} entities found"
        )

        return results

    def query_builder(self) -> "QueryBuilder":
        """
        Create a new QueryBuilder instance for this entity.

        Returns:
            QueryBuilder instance configured for this entity

        Example:
            query = client.tickets.query_builder()
            query.where("status", "eq", 1).where("priority", "gte", 3)
            results = query.execute()
        """
        from .query_builder import QueryBuilder

        return QueryBuilder(self)
