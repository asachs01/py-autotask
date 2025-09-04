"""
Ticket Statuses entity for Autotask API.

This module provides the TicketStatusesEntity class for managing
ticket status definitions and workflow transitions.
"""

from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class TicketStatusesEntity(BaseEntity):
    """
    Entity for managing Autotask Ticket Statuses.

    Ticket Statuses define the workflow states that tickets can be in,
    controlling transitions and automation rules.
    """

    def __init__(self, client, entity_name="TicketStatuses"):
        """Initialize the Ticket Statuses entity."""
        super().__init__(client, entity_name)

    def create(self, status_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new ticket status.

        Args:
            status_data: Dictionary containing status information
                Required fields:
                - name: Name of the status
                - active: Whether the status is active
                - systemStatus: System status type (1=New, 2=In Progress, 3=Waiting, 4=Complete, 5=Cancelled)
                Optional fields:
                - description: Description of the status
                - color: Color code for the status
                - isDefault: Whether this is a default status
                - sortOrder: Sort order for display
                - isComplete: Whether this represents a completed state
                - isVisibleToClient: Whether clients can see this status

        Returns:
            CreateResponse: Response containing created status data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["name", "active", "systemStatus"]
        self._validate_required_fields(status_data, required_fields)

        # Validate system status
        valid_system_statuses = [1, 2, 3, 4, 5]
        system_status = status_data.get("systemStatus")
        if system_status not in valid_system_statuses:
            raise ValueError(f"System status must be one of: {valid_system_statuses}")

        return self._create(status_data)

    def get(self, status_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ticket status by ID.

        Args:
            status_id: The status ID

        Returns:
            Dictionary containing status data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(status_id)

    def update(self, status_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing ticket status.

        Args:
            status_id: The status ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated status data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(status_id, update_data)

    def delete(self, status_id: int) -> bool:
        """
        Delete a ticket status.

        Args:
            status_id: The status ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(status_id)

    def get_active_statuses(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all active ticket statuses.

        Args:
            include_inactive: Whether to include inactive statuses

        Returns:
            List of active statuses
        """
        filters = []

        if not include_inactive:
            filters.append(QueryFilter(field="active", op="eq", value=True))

        return self.query(filters=filters)

    def get_statuses_by_type(self, system_status: int) -> List[Dict[str, Any]]:
        """
        Get statuses by system status type.

        Args:
            system_status: System status type
                1 = New
                2 = In Progress
                3 = Waiting
                4 = Complete
                5 = Cancelled

        Returns:
            List of statuses with the specified system status
        """
        filters = [
            QueryFilter(field="systemStatus", op="eq", value=system_status),
            QueryFilter(field="active", op="eq", value=True),
        ]

        return self.query(filters=filters)

    def get_completion_statuses(self) -> List[Dict[str, Any]]:
        """
        Get all statuses that represent completion states.

        Returns:
            List of completion statuses
        """
        filters = [
            QueryFilter(field="isComplete", op="eq", value=True),
            QueryFilter(field="active", op="eq", value=True),
        ]

        return self.query(filters=filters)

    def get_client_visible_statuses(self) -> List[Dict[str, Any]]:
        """
        Get all statuses visible to clients.

        Returns:
            List of client-visible statuses
        """
        filters = [
            QueryFilter(field="isVisibleToClient", op="eq", value=True),
            QueryFilter(field="active", op="eq", value=True),
        ]

        return self.query(filters=filters)

    def get_status_workflow(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the complete status workflow organization.

        Returns:
            Dictionary organized by system status type
        """
        all_statuses = self.get_active_statuses()

        workflow = {
            "new": [],
            "in_progress": [],
            "waiting": [],
            "complete": [],
            "cancelled": [],
        }

        system_status_map = {
            1: "new",
            2: "in_progress",
            3: "waiting",
            4: "complete",
            5: "cancelled",
        }

        for status in all_statuses:
            system_status = status.get("systemStatus", 1)
            workflow_key = system_status_map.get(system_status, "new")
            workflow[workflow_key].append(status)

        # Sort by sort order
        for key in workflow:
            workflow[key].sort(key=lambda x: x.get("sortOrder", 999))

        return workflow

    def set_status_order(
        self, status_orders: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Set the sort order for multiple statuses.

        Args:
            status_orders: List of dictionaries with 'id' and 'sortOrder'

        Returns:
            List of update responses
        """
        results = []

        for order_data in status_orders:
            status_id = order_data.get("id")
            sort_order = order_data.get("sortOrder")

            if status_id and sort_order is not None:
                update_data = {"sortOrder": sort_order}
                result = self.update(status_id, update_data)
                results.append(result)

        return results

    def get_status_usage_stats(
        self, status_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a status.

        Args:
            status_id: Status ID to get stats for
            date_range: Optional date range for ticket counts

        Returns:
            Dictionary with usage statistics
        """
        # Build filter for tickets with this status
        filters = [QueryFilter(field="status", op="eq", value=status_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        # Query tickets with this status
        tickets = self.client.query("Tickets", filters=filters)

        # Calculate statistics
        stats = {
            "status_id": status_id,
            "total_tickets": len(tickets),
            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
            "by_category": {},
            "avg_time_in_status": 0,
            "resolution_rate": 0,
        }

        time_in_status = []
        resolved_count = 0

        for ticket in tickets:
            priority = ticket.get("priority", 4)
            category = ticket.get("ticketCategory", "Other")

            # Count by priority
            if priority in stats["by_priority"]:
                stats["by_priority"][priority] += 1

            # Count by category
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # Calculate time in status (simplified - would need status history for accuracy)
            create_date = ticket.get("createDate")
            last_activity = ticket.get("lastActivityDate")

            if create_date and last_activity:
                try:
                    from datetime import datetime

                    created = datetime.fromisoformat(create_date.replace("Z", "+00:00"))
                    last_act = datetime.fromisoformat(
                        last_activity.replace("Z", "+00:00")
                    )
                    time_diff = (last_act - created).total_seconds() / 3600  # Hours
                    time_in_status.append(time_diff)
                except ValueError:
                    pass

            # Check if resolved
            ticket_status = ticket.get("status", 1)
            if ticket_status in [4, 5]:  # Complete or cancelled system statuses
                resolved_count += 1

        # Calculate averages
        if time_in_status:
            stats["avg_time_in_status"] = sum(time_in_status) / len(time_in_status)

        if stats["total_tickets"] > 0:
            stats["resolution_rate"] = (resolved_count / stats["total_tickets"]) * 100

        return stats

    def get_status_transitions(
        self, from_status_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get transition patterns from a specific status.

        Args:
            from_status_id: Status ID to analyze transitions from
            date_range: Optional date range for analysis

        Returns:
            Dictionary with transition statistics
        """
        # This would typically require ticket status history
        # For now, we'll provide a simplified version

        # Get tickets that were in this status
        filters = [QueryFilter(field="status", op="eq", value=from_status_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="lastActivityDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="lastActivityDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        tickets = self.client.query("Tickets", filters=filters)

        transitions = {
            "from_status_id": from_status_id,
            "total_tickets": len(tickets),
            "current_status_breakdown": {},
            "transition_time_avg": 0,
        }

        current_statuses = {}

        for ticket in tickets:
            current_status = ticket.get("status", from_status_id)
            current_statuses[current_status] = (
                current_statuses.get(current_status, 0) + 1
            )

        transitions["current_status_breakdown"] = current_statuses

        return transitions

    def bulk_update_status_properties(
        self, status_updates: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Update properties for multiple statuses in bulk.

        Args:
            status_updates: List of dictionaries with 'id' and update data

        Returns:
            List of update responses
        """
        results = []

        for update_info in status_updates:
            status_id = update_info.get("id")
            update_data = update_info.get("data", {})

            if status_id and update_data:
                try:
                    result = self.update(status_id, update_data)
                    results.append(result)
                except Exception as e:
                    self.client.logger.error(
                        f"Failed to update status {status_id}: {e}"
                    )
                    results.append({"error": str(e), "status_id": status_id})

        return results

    def validate_status_data(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate status data.

        Args:
            status_data: Status data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["name", "active", "systemStatus"]
        for field in required_fields:
            if field not in status_data or status_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate name
        name = status_data.get("name", "")
        if name:
            if len(name) < 2:
                errors.append("Status name must be at least 2 characters")
            elif len(name) > 50:
                errors.append("Status name must not exceed 50 characters")

        # Validate system status
        system_status = status_data.get("systemStatus")
        if system_status is not None:
            valid_statuses = [1, 2, 3, 4, 5]
            if system_status not in valid_statuses:
                errors.append(f"System status must be one of: {valid_statuses}")

        # Validate color format if provided
        color = status_data.get("color")
        if color:
            if not color.startswith("#") or len(color) != 7:
                warnings.append("Color should be in hex format (#RRGGBB)")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
