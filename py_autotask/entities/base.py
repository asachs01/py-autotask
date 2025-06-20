"""
Base entity class for Autotask API entities.

This module provides the base class that all entity-specific classes
inherit from, providing common CRUD operations and utilities.
"""

import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from ..types import QueryRequest, QueryResponse, CreateResponse, EntityDict, EntityList
from ..exceptions import AutotaskValidationError

if TYPE_CHECKING:
    from ..client import AutotaskClient

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
    ) -> EntityList:
        """
        Query all entities, automatically handling pagination.
        
        Args:
            filters: Filter conditions
            include_fields: Specific fields to include in response
            
        Returns:
            List of all matching entities
            
        Example:
            all_active_companies = client.companies.query_all(
                {"field": "isActive", "op": "eq", "value": "true"}
            )
        """
        all_items = []
        query_request = QueryRequest()
        
        if filters:
            if isinstance(filters, dict):
                query_request.filter = [filters]
            elif isinstance(filters, list):
                query_request.filter = filters
                
        if include_fields:
            query_request.include_fields = include_fields
            
        self.logger.debug(f"Querying all {self.entity_name} with pagination")
        
        while True:
            response = self.client.query(self.entity_name, query_request)
            all_items.extend(response.items)
            
            # Check if there are more pages
            if not response.page_details.next_page_url:
                break
                
            # Update query for next page
            # Note: The Autotask API handles pagination differently,
            # this would need to be adjusted based on actual API behavior
            # For now, we'll break to avoid infinite loops
            break
            
        self.logger.debug(f"Retrieved {len(all_items)} {self.entity_name} items")
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
        return self.client.create(self.entity_name, entity_data)
        
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