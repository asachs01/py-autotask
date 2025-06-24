"""
Resources entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter, ResourceData
from .base import BaseEntity


class ResourcesEntity(BaseEntity):
    """
    Handles all Resource-related operations for the Autotask API.

    Resources in Autotask represent employees, contractors, and other
    personnel who perform work and track time.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def get_active_resources(self, limit: Optional[int] = None) -> List[ResourceData]:
        """
        Get all active resources.

        Args:
            limit: Maximum number of resources to return

        Returns:
            List of active resources
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]
        return self.query(filters=filters, max_records=limit)

    def search_resources_by_name(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        exact_match: bool = False,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[ResourceData]:
        """
        Search for resources by name.

        Args:
            first_name: First name to search for
            last_name: Last name to search for
            exact_match: Whether to do exact match or partial match
            active_only: Whether to return only active resources
            limit: Maximum number of resources to return

        Returns:
            List of matching resources
        """
        filters = []

        if first_name:
            op = "eq" if exact_match else "contains"
            filters.append(QueryFilter(field="FirstName", op=op, value=first_name))

        if last_name:
            op = "eq" if exact_match else "contains"
            filters.append(QueryFilter(field="LastName", op=op, value=last_name))

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        if not first_name and not last_name:
            raise ValueError("At least one name field must be provided")

        return self.query(filters=filters, max_records=limit)

    def get_resource_tickets(
        self,
        resource_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tickets assigned to a specific resource.

        Args:
            resource_id: ID of the resource
            status_filter: Optional status filter ('open', 'closed', etc.)
            limit: Maximum number of tickets to return

        Returns:
            List of tickets assigned to the resource
        """
        filters = [QueryFilter(field="AssignedResourceID", op="eq", value=resource_id)]

        if status_filter:
            status_map = {
                "open": [1, 8, 9, 10, 11],
                "closed": [5],
                "new": [1],
                "in_progress": [8, 9, 10, 11],
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        return self._client.query("Tickets", filters=filters, max_records=limit)

    def get_resource_time_entries(
        self,
        resource_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get time entries for a specific resource.

        Args:
            resource_id: ID of the resource
            date_from: Start date filter (ISO format)
            date_to: End date filter (ISO format)
            limit: Maximum number of time entries to return

        Returns:
            List of time entries for the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_from:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=date_from))
        if date_to:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=date_to))

        return self._client.query("TimeEntries", filters=filters, max_records=limit)
