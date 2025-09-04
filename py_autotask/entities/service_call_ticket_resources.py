"""
ServiceCallTicketResources entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ServiceCallTicketResourcesEntity(BaseEntity):
    """
    Handles all Service Call Ticket Resource-related operations for the Autotask API.

    Service Call Ticket Resources represent the assignment of resources to service call tickets.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_service_call_ticket_resource(
        self,
        service_call_ticket_id: int,
        resource_id: int,
        role: Optional[str] = None,
        is_primary: bool = False,
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new service call ticket resource assignment.

        Args:
            service_call_ticket_id: ID of the service call ticket
            resource_id: ID of the resource being assigned
            role: Role of the resource on this service call
            is_primary: Whether this is the primary resource
            start_date_time: Start date and time for the assignment
            end_date_time: End date and time for the assignment
            estimated_hours: Estimated hours for the resource
            **kwargs: Additional resource assignment fields

        Returns:
            Created service call ticket resource data
        """
        resource_data = {
            "ServiceCallTicketID": service_call_ticket_id,
            "ResourceID": resource_id,
            "IsPrimary": is_primary,
            **kwargs,
        }

        if role:
            resource_data["Role"] = role
        if start_date_time:
            resource_data["StartDateTime"] = start_date_time
        if end_date_time:
            resource_data["EndDateTime"] = end_date_time
        if estimated_hours is not None:
            resource_data["EstimatedHours"] = estimated_hours

        return self.create(resource_data)

    def get_resources_by_service_call_ticket(
        self, service_call_ticket_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all resources assigned to a specific service call ticket.

        Args:
            service_call_ticket_id: ID of the service call ticket
            limit: Maximum number of records to return

        Returns:
            List of resources assigned to the service call ticket
        """
        filters = [
            QueryFilter(
                field="ServiceCallTicketID", op="eq", value=service_call_ticket_id
            )
        ]

        return self.query(filters=filters, max_records=limit)

    def get_assignments_by_resource(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all service call ticket assignments for a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of records to return

        Returns:
            List of service call ticket assignments for the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        return self.query(filters=filters, max_records=limit)

    def get_primary_resource(self, service_call_ticket_id: int) -> Optional[EntityDict]:
        """
        Get the primary resource for a service call ticket.

        Args:
            service_call_ticket_id: ID of the service call ticket

        Returns:
            Primary resource assignment or None if not found
        """
        filters = [
            QueryFilter(
                field="ServiceCallTicketID", op="eq", value=service_call_ticket_id
            ),
            QueryFilter(field="IsPrimary", op="eq", value=True),
        ]

        results = self.query(filters=filters, max_records=1)
        return results[0] if results else None

    def get_assignments_by_role(
        self, role: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all resource assignments for a specific role.

        Args:
            role: Role to filter by
            limit: Maximum number of records to return

        Returns:
            List of assignments for the specified role
        """
        filters = [QueryFilter(field="Role", op="eq", value=role)]

        return self.query(filters=filters, max_records=limit)

    def get_assignments_by_date_range(
        self, start_date: str, end_date: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get resource assignments within a specific date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            limit: Maximum number of records to return

        Returns:
            List of assignments within the date range
        """
        filters = [
            QueryFilter(field="StartDateTime", op="ge", value=start_date),
            QueryFilter(field="EndDateTime", op="le", value=end_date),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_current_assignments(
        self, resource_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get currently active resource assignments.

        Args:
            resource_id: Optional resource ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of current assignments
        """
        from datetime import datetime

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        filters = [
            QueryFilter(field="StartDateTime", op="le", value=current_time),
            QueryFilter(field="EndDateTime", op="ge", value=current_time),
        ]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def set_primary_resource(
        self, service_call_ticket_id: int, resource_id: int
    ) -> EntityDict:
        """
        Set a resource as the primary resource for a service call ticket.

        Args:
            service_call_ticket_id: ID of the service call ticket
            resource_id: ID of the resource to set as primary

        Returns:
            Updated resource assignment data
        """
        # First, unset any existing primary resource for this ticket
        existing_resources = self.get_resources_by_service_call_ticket(
            service_call_ticket_id
        )
        for resource in existing_resources:
            if (
                resource.get("IsPrimary", False)
                and resource.get("ResourceID") != resource_id
            ):
                self.update_by_id(resource["id"], {"IsPrimary": False})

        # Find the assignment for the specified resource and set as primary
        target_assignment = next(
            (r for r in existing_resources if r.get("ResourceID") == resource_id), None
        )

        if target_assignment:
            return self.update_by_id(target_assignment["id"], {"IsPrimary": True})
        else:
            raise ValueError(
                f"Resource {resource_id} is not assigned to ticket {service_call_ticket_id}"
            )

    def update_assignment_schedule(
        self,
        assignment_id: int,
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        estimated_hours: Optional[float] = None,
    ) -> EntityDict:
        """
        Update the schedule for a resource assignment.

        Args:
            assignment_id: ID of the assignment
            start_date_time: New start date and time
            end_date_time: New end date and time
            estimated_hours: New estimated hours

        Returns:
            Updated assignment data
        """
        update_data = {}
        if start_date_time is not None:
            update_data["StartDateTime"] = start_date_time
        if end_date_time is not None:
            update_data["EndDateTime"] = end_date_time
        if estimated_hours is not None:
            update_data["EstimatedHours"] = estimated_hours

        return self.update_by_id(assignment_id, update_data)

    def update_resource_role(self, assignment_id: int, role: str) -> EntityDict:
        """
        Update the role of a resource assignment.

        Args:
            assignment_id: ID of the assignment
            role: New role for the resource

        Returns:
            Updated assignment data
        """
        return self.update_by_id(assignment_id, {"Role": role})

    def get_resource_workload(
        self, resource_id: int, date_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get workload information for a specific resource.

        Args:
            resource_id: ID of the resource
            date_range_days: Number of days to analyze

        Returns:
            Dictionary with workload information
        """
        from datetime import date, timedelta

        start_date = date.today().strftime("%Y-%m-%d")
        end_date = (date.today() + timedelta(days=date_range_days)).strftime("%Y-%m-%d")

        # Get assignments for the resource in the date range
        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="StartDateTime", op="ge", value=start_date),
            QueryFilter(field="StartDateTime", op="le", value=end_date),
        ]

        assignments = self.query(filters=filters)

        total_estimated_hours = sum(
            assignment.get("EstimatedHours", 0) for assignment in assignments
        )

        # Count assignments by role
        role_counts = {}
        for assignment in assignments:
            role = assignment.get("Role", "Unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        workload = {
            "resource_id": resource_id,
            "date_range": f"{start_date} to {end_date}",
            "total_assignments": len(assignments),
            "total_estimated_hours": total_estimated_hours,
            "primary_assignments": len(
                [a for a in assignments if a.get("IsPrimary", False)]
            ),
            "assignments_by_role": role_counts,
            "average_hours_per_assignment": (
                round(total_estimated_hours / len(assignments), 2) if assignments else 0
            ),
        }

        return workload

    def get_assignment_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about service call ticket resource assignments.

        Returns:
            Dictionary containing assignment statistics
        """
        all_assignments = self.query()

        # Calculate estimated hours statistics
        estimated_hours = [
            assignment.get("EstimatedHours", 0)
            for assignment in all_assignments
            if assignment.get("EstimatedHours")
        ]

        # Group by role
        role_counts = {}
        for assignment in all_assignments:
            role = assignment.get("Role", "Unspecified")
            role_counts[role] = role_counts.get(role, 0) + 1

        # Count unique resources and tickets
        unique_resources = set(
            assignment.get("ResourceID")
            for assignment in all_assignments
            if assignment.get("ResourceID")
        )

        unique_tickets = set(
            assignment.get("ServiceCallTicketID")
            for assignment in all_assignments
            if assignment.get("ServiceCallTicketID")
        )

        stats = {
            "total_assignments": len(all_assignments),
            "primary_assignments": len(
                [a for a in all_assignments if a.get("IsPrimary", False)]
            ),
            "assignments_with_estimated_hours": len(
                [a for a in all_assignments if a.get("EstimatedHours")]
            ),
            "unique_resources": len(unique_resources),
            "unique_service_call_tickets": len(unique_tickets),
            "assignments_by_role": role_counts,
        }

        if estimated_hours:
            stats["estimated_hours_statistics"] = {
                "total_hours": sum(estimated_hours),
                "average_hours": round(sum(estimated_hours) / len(estimated_hours), 2),
                "min_hours": min(estimated_hours),
                "max_hours": max(estimated_hours),
            }

        return stats
