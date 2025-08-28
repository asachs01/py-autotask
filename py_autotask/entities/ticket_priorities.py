"""
Ticket Priorities entity for Autotask API.

This module provides the TicketPrioritiesEntity class for managing
ticket priority levels and SLA integration.
"""

from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class TicketPrioritiesEntity(BaseEntity):
    """
    Entity for managing Autotask Ticket Priorities.

    Ticket Priorities define urgency levels for tickets and integrate
    with SLA timers and escalation rules.
    """

    def __init__(self, client, entity_name="TicketPriorities"):
        """Initialize the Ticket Priorities entity."""
        super().__init__(client, entity_name)

    def create(self, priority_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new ticket priority.

        Args:
            priority_data: Dictionary containing priority information
                Required fields:
                - name: Name of the priority
                - priorityLevel: Numeric priority level (1=Critical, 2=High, 3=Medium, 4=Low)
                - active: Whether the priority is active
                Optional fields:
                - description: Description of the priority
                - color: Color code for the priority
                - isDefault: Whether this is a default priority
                - sortOrder: Sort order for display
                - responseTimeHours: SLA response time in hours
                - resolutionTimeHours: SLA resolution time in hours
                - escalationTimeHours: Escalation time in hours

        Returns:
            CreateResponse: Response containing created priority data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["name", "priorityLevel", "active"]
        self._validate_required_fields(priority_data, required_fields)

        # Validate priority level
        priority_level = priority_data.get("priorityLevel")
        if priority_level not in [1, 2, 3, 4]:
            raise ValueError(
                "Priority level must be 1 (Critical), 2 (High), 3 (Medium), or 4 (Low)"
            )

        return self._create(priority_data)

    def get(self, priority_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ticket priority by ID.

        Args:
            priority_id: The priority ID

        Returns:
            Dictionary containing priority data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(priority_id)

    def update(self, priority_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing ticket priority.

        Args:
            priority_id: The priority ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated priority data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(priority_id, update_data)

    def delete(self, priority_id: int) -> bool:
        """
        Delete a ticket priority.

        Args:
            priority_id: The priority ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(priority_id)

    def get_active_priorities(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all active ticket priorities.

        Args:
            include_inactive: Whether to include inactive priorities

        Returns:
            List of active priorities ordered by priority level
        """
        filters = []

        if not include_inactive:
            filters.append(QueryFilter(field="active", op="eq", value=True))

        priorities = self.query(filters=filters)

        # Sort by priority level (1=Critical first)
        return sorted(priorities, key=lambda x: x.get("priorityLevel", 4))

    def get_priority_by_level(self, priority_level: int) -> Optional[Dict[str, Any]]:
        """
        Get priority by numeric level.

        Args:
            priority_level: Priority level (1=Critical, 2=High, 3=Medium, 4=Low)

        Returns:
            Priority data for the specified level
        """
        filters = [
            QueryFilter(field="priorityLevel", op="eq", value=priority_level),
            QueryFilter(field="active", op="eq", value=True),
        ]

        priorities = self.query(filters=filters)
        return priorities[0] if priorities else None

    def get_default_priority(self) -> Optional[Dict[str, Any]]:
        """
        Get the default priority.

        Returns:
            Default priority data
        """
        filters = [
            QueryFilter(field="isDefault", op="eq", value=True),
            QueryFilter(field="active", op="eq", value=True),
        ]

        priorities = self.query(filters=filters)
        return priorities[0] if priorities else None

    def get_critical_priorities(self) -> List[Dict[str, Any]]:
        """
        Get all critical priority levels (level 1).

        Returns:
            List of critical priorities
        """
        return self.query(
            filters=[
                QueryFilter(field="priorityLevel", op="eq", value=1),
                QueryFilter(field="active", op="eq", value=True),
            ]
        )

    def get_priority_usage_stats(
        self, priority_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a priority.

        Args:
            priority_id: Priority ID to get stats for
            date_range: Optional date range for ticket counts

        Returns:
            Dictionary with usage statistics
        """
        # Build filter for tickets with this priority
        filters = [QueryFilter(field="priority", op="eq", value=priority_id)]

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

        # Query tickets with this priority
        tickets = self.client.query("Tickets", filters=filters)

        # Calculate statistics
        stats = {
            "priority_id": priority_id,
            "total_tickets": len(tickets),
            "open_tickets": 0,
            "closed_tickets": 0,
            "overdue_tickets": 0,
            "avg_resolution_time": 0,
            "sla_compliance_rate": 0,
            "by_status": {},
            "by_category": {},
        }

        resolution_times = []
        sla_violations = 0

        for ticket in tickets:
            status = ticket.get("status", 1)
            category = ticket.get("ticketCategory", "Other")

            # Count by status
            if status in [5, 6]:  # Closed/Complete statuses
                stats["closed_tickets"] += 1
            else:
                stats["open_tickets"] += 1

            # Count by status
            status_name = f"status_{status}"
            stats["by_status"][status_name] = stats["by_status"].get(status_name, 0) + 1

            # Count by category
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # Calculate resolution time for closed tickets
            if status in [5, 6]:
                create_date = ticket.get("createDate")
                close_date = ticket.get("lastActivityDate")

                if create_date and close_date:
                    try:
                        from datetime import datetime

                        created = datetime.fromisoformat(
                            create_date.replace("Z", "+00:00")
                        )
                        closed = datetime.fromisoformat(
                            close_date.replace("Z", "+00:00")
                        )
                        resolution_time = (
                            closed - created
                        ).total_seconds() / 3600  # Hours
                        resolution_times.append(resolution_time)

                        # Check SLA compliance (simplified)
                        priority_data = self.get(priority_id)
                        if priority_data:
                            sla_hours = priority_data.get("resolutionTimeHours", 24)
                            if resolution_time > sla_hours:
                                sla_violations += 1

                    except ValueError:
                        pass

            # Check for overdue tickets (simplified)
            due_date = ticket.get("dueDateTime")
            if due_date and status not in [5, 6]:
                try:
                    from datetime import datetime

                    due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                    now = datetime.now(due.tzinfo)
                    if now > due:
                        stats["overdue_tickets"] += 1
                except ValueError:
                    pass

        # Calculate averages
        if resolution_times:
            stats["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)

        if stats["closed_tickets"] > 0:
            stats["sla_compliance_rate"] = (
                (stats["closed_tickets"] - sla_violations) / stats["closed_tickets"]
            ) * 100

        return stats

    def get_priority_comparison(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get comparative statistics across all priority levels.

        Args:
            date_range: Optional date range for analysis

        Returns:
            Dictionary with comparative priority statistics
        """
        priorities = self.get_active_priorities()
        comparison = {
            "total_priorities": len(priorities),
            "by_level": {},
            "summary": {
                "total_tickets": 0,
                "avg_resolution_time": 0,
                "overall_sla_compliance": 0,
            },
        }

        all_resolution_times = []
        total_closed = 0
        total_sla_violations = 0

        for priority in priorities:
            priority_id = priority["id"]
            level = priority.get("priorityLevel", 4)
            name = priority.get("name", f"Priority {level}")

            stats = self.get_priority_usage_stats(priority_id, date_range)

            comparison["by_level"][level] = {
                "id": priority_id,
                "name": name,
                "stats": stats,
            }

            # Aggregate for summary
            comparison["summary"]["total_tickets"] += stats["total_tickets"]

            if stats["avg_resolution_time"] > 0:
                all_resolution_times.append(stats["avg_resolution_time"])

            total_closed += stats["closed_tickets"]

            # Estimate SLA violations for overall compliance
            if stats["sla_compliance_rate"] < 100:
                violation_count = stats["closed_tickets"] * (
                    1 - stats["sla_compliance_rate"] / 100
                )
                total_sla_violations += violation_count

        # Calculate overall averages
        if all_resolution_times:
            comparison["summary"]["avg_resolution_time"] = sum(
                all_resolution_times
            ) / len(all_resolution_times)

        if total_closed > 0:
            comparison["summary"]["overall_sla_compliance"] = (
                (total_closed - total_sla_violations) / total_closed
            ) * 100

        return comparison

    def set_priority_order(
        self, priority_orders: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Set the sort order for multiple priorities.

        Args:
            priority_orders: List of dictionaries with 'id' and 'sortOrder'

        Returns:
            List of update responses
        """
        results = []

        for order_data in priority_orders:
            priority_id = order_data.get("id")
            sort_order = order_data.get("sortOrder")

            if priority_id and sort_order is not None:
                update_data = {"sortOrder": sort_order}
                result = self.update(priority_id, update_data)
                results.append(result)

        return results

    def bulk_update_sla_times(
        self, sla_updates: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Update SLA times for multiple priorities in bulk.

        Args:
            sla_updates: List of dictionaries with 'id' and SLA time fields

        Returns:
            List of update responses
        """
        results = []

        for update_info in sla_updates:
            priority_id = update_info.get("id")
            sla_data = {k: v for k, v in update_info.items() if k != "id"}

            if priority_id and sla_data:
                try:
                    result = self.update(priority_id, sla_data)
                    results.append(result)
                except Exception as e:
                    self.client.logger.error(
                        f"Failed to update priority {priority_id}: {e}"
                    )
                    results.append({"error": str(e), "priority_id": priority_id})

        return results

    def calculate_sla_metrics(
        self, priority_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Calculate detailed SLA metrics for a priority.

        Args:
            priority_id: Priority ID to calculate metrics for
            date_range: Optional date range for analysis

        Returns:
            Dictionary with detailed SLA metrics
        """
        priority_data = self.get(priority_id)
        if not priority_data:
            return {"error": "Priority not found"}

        # Get tickets for this priority
        filters = [QueryFilter(field="priority", op="eq", value=priority_id)]

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

        tickets = self.client.query("Tickets", filters=filters)

        metrics = {
            "priority_id": priority_id,
            "priority_name": priority_data.get("name", ""),
            "sla_response_hours": priority_data.get("responseTimeHours", 4),
            "sla_resolution_hours": priority_data.get("resolutionTimeHours", 24),
            "total_tickets": len(tickets),
            "response_metrics": {
                "within_sla": 0,
                "breached_sla": 0,
                "avg_response_time": 0,
                "compliance_rate": 0,
            },
            "resolution_metrics": {
                "within_sla": 0,
                "breached_sla": 0,
                "avg_resolution_time": 0,
                "compliance_rate": 0,
            },
        }

        response_times = []
        resolution_times = []

        sla_response_hours = priority_data.get("responseTimeHours", 4)
        sla_resolution_hours = priority_data.get("resolutionTimeHours", 24)

        for ticket in tickets:
            create_date = ticket.get("createDate")
            first_response = ticket.get("firstResponseDate")
            close_date = ticket.get("lastActivityDate")
            status = ticket.get("status", 1)

            # Response time analysis
            if create_date and first_response:
                try:
                    from datetime import datetime

                    created = datetime.fromisoformat(create_date.replace("Z", "+00:00"))
                    responded = datetime.fromisoformat(
                        first_response.replace("Z", "+00:00")
                    )
                    response_time = (
                        responded - created
                    ).total_seconds() / 3600  # Hours
                    response_times.append(response_time)

                    if response_time <= sla_response_hours:
                        metrics["response_metrics"]["within_sla"] += 1
                    else:
                        metrics["response_metrics"]["breached_sla"] += 1

                except ValueError:
                    pass

            # Resolution time analysis (for closed tickets)
            if status in [5, 6] and create_date and close_date:
                try:
                    from datetime import datetime

                    created = datetime.fromisoformat(create_date.replace("Z", "+00:00"))
                    closed = datetime.fromisoformat(close_date.replace("Z", "+00:00"))
                    resolution_time = (closed - created).total_seconds() / 3600  # Hours
                    resolution_times.append(resolution_time)

                    if resolution_time <= sla_resolution_hours:
                        metrics["resolution_metrics"]["within_sla"] += 1
                    else:
                        metrics["resolution_metrics"]["breached_sla"] += 1

                except ValueError:
                    pass

        # Calculate averages and compliance rates
        if response_times:
            metrics["response_metrics"]["avg_response_time"] = sum(
                response_times
            ) / len(response_times)
            total_responses = (
                metrics["response_metrics"]["within_sla"]
                + metrics["response_metrics"]["breached_sla"]
            )
            if total_responses > 0:
                metrics["response_metrics"]["compliance_rate"] = (
                    metrics["response_metrics"]["within_sla"] / total_responses
                ) * 100

        if resolution_times:
            metrics["resolution_metrics"]["avg_resolution_time"] = sum(
                resolution_times
            ) / len(resolution_times)
            total_resolutions = (
                metrics["resolution_metrics"]["within_sla"]
                + metrics["resolution_metrics"]["breached_sla"]
            )
            if total_resolutions > 0:
                metrics["resolution_metrics"]["compliance_rate"] = (
                    metrics["resolution_metrics"]["within_sla"] / total_resolutions
                ) * 100

        return metrics

    def validate_priority_data(self, priority_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate priority data.

        Args:
            priority_data: Priority data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["name", "priorityLevel", "active"]
        for field in required_fields:
            if field not in priority_data or priority_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate name
        name = priority_data.get("name", "")
        if name:
            if len(name) < 2:
                errors.append("Priority name must be at least 2 characters")
            elif len(name) > 50:
                errors.append("Priority name must not exceed 50 characters")

        # Validate priority level
        priority_level = priority_data.get("priorityLevel")
        if priority_level is not None:
            if priority_level not in [1, 2, 3, 4]:
                errors.append(
                    "Priority level must be 1 (Critical), 2 (High), 3 (Medium), or 4 (Low)"
                )

        # Validate SLA times
        response_time = priority_data.get("responseTimeHours")
        if response_time is not None:
            try:
                response_val = float(response_time)
                if response_val <= 0:
                    errors.append("Response time must be positive")
                elif response_val > 168:  # 1 week
                    warnings.append("Response time exceeds 1 week")
            except (ValueError, TypeError):
                errors.append("Response time must be a valid number")

        resolution_time = priority_data.get("resolutionTimeHours")
        if resolution_time is not None:
            try:
                resolution_val = float(resolution_time)
                if resolution_val <= 0:
                    errors.append("Resolution time must be positive")
                elif resolution_val > 720:  # 1 month
                    warnings.append("Resolution time exceeds 1 month")
            except (ValueError, TypeError):
                errors.append("Resolution time must be a valid number")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
