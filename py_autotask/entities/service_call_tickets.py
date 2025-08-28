"""
ServiceCallTickets entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ServiceCallTicketsEntity(BaseEntity):
    """
    Handles all Service Call Ticket-related operations for the Autotask API.

    Service Call Tickets represent scheduled service calls and field service work orders.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_service_call_ticket(
        self,
        account_id: int,
        title: str,
        description: str,
        status: int = 1,  # Default to New
        priority: int = 3,  # Default to Medium
        service_call_date: Optional[str] = None,
        duration_hours: Optional[float] = None,
        assigned_resource_id: Optional[int] = None,
        service_location: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new service call ticket.

        Args:
            account_id: ID of the account/company
            title: Title of the service call ticket
            description: Description of the service call
            status: Status of the ticket (1=New, 2=In Progress, etc.)
            priority: Priority level (1=Critical, 2=High, 3=Medium, 4=Low)
            service_call_date: Scheduled date for the service call
            duration_hours: Expected duration in hours
            assigned_resource_id: ID of the assigned resource
            service_location: Location where service will be performed
            **kwargs: Additional service call ticket fields

        Returns:
            Created service call ticket data
        """
        ticket_data = {
            "AccountID": account_id,
            "Title": title,
            "Description": description,
            "Status": status,
            "Priority": priority,
            **kwargs,
        }

        if service_call_date:
            ticket_data["ServiceCallDate"] = service_call_date
        if duration_hours is not None:
            ticket_data["DurationHours"] = duration_hours
        if assigned_resource_id:
            ticket_data["AssignedResourceID"] = assigned_resource_id
        if service_location:
            ticket_data["ServiceLocation"] = service_location

        return self.create(ticket_data)

    def get_service_calls_by_account(
        self, account_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all service call tickets for a specific account.

        Args:
            account_id: ID of the account
            limit: Maximum number of records to return

        Returns:
            List of service call tickets for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        return self.query(filters=filters, max_records=limit)

    def get_service_calls_by_resource(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all service call tickets assigned to a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of records to return

        Returns:
            List of service call tickets assigned to the resource
        """
        filters = [QueryFilter(field="AssignedResourceID", op="eq", value=resource_id)]

        return self.query(filters=filters, max_records=limit)

    def get_service_calls_by_status(
        self, status: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get service call tickets by status.

        Args:
            status: Status ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of service call tickets with the specified status
        """
        filters = [QueryFilter(field="Status", op="eq", value=status)]

        return self.query(filters=filters, max_records=limit)

    def get_open_service_calls(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all open service call tickets.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of open service call tickets
        """
        # Assuming status 1-4 are open statuses (New, In Progress, etc.)
        open_statuses = [1, 2, 3, 4]
        filters = [QueryFilter(field="Status", op="in", value=open_statuses)]

        return self.query(filters=filters, max_records=limit)

    def get_service_calls_by_date_range(
        self, start_date: str, end_date: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get service call tickets within a specific date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            limit: Maximum number of records to return

        Returns:
            List of service call tickets within the date range
        """
        filters = [
            QueryFilter(field="ServiceCallDate", op="ge", value=start_date),
            QueryFilter(field="ServiceCallDate", op="le", value=end_date),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_high_priority_service_calls(
        self, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get high-priority service call tickets.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of high-priority service call tickets
        """
        # Priority 1 = Critical, 2 = High
        high_priorities = [1, 2]
        filters = [QueryFilter(field="Priority", op="in", value=high_priorities)]

        return self.query(filters=filters, max_records=limit)

    def get_overdue_service_calls(
        self, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get overdue service call tickets.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of overdue service call tickets
        """
        from datetime import date

        today = date.today().strftime("%Y-%m-%d")

        # Get open tickets scheduled before today
        filters = [
            QueryFilter(field="ServiceCallDate", op="lt", value=today),
            QueryFilter(field="Status", op="in", value=[1, 2, 3, 4]),  # Open statuses
        ]

        return self.query(filters=filters, max_records=limit)

    def search_service_calls_by_title(
        self, title: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for service call tickets by title.

        Args:
            title: Title to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching service call tickets
        """
        if exact_match:
            filters = [QueryFilter(field="Title", op="eq", value=title)]
        else:
            filters = [QueryFilter(field="Title", op="contains", value=title)]

        return self.query(filters=filters, max_records=limit)

    def update_service_call_status(
        self, service_call_id: int, status: int
    ) -> EntityDict:
        """
        Update the status of a service call ticket.

        Args:
            service_call_id: ID of the service call ticket
            status: New status

        Returns:
            Updated service call ticket data
        """
        return self.update_by_id(service_call_id, {"Status": status})

    def assign_resource(self, service_call_id: int, resource_id: int) -> EntityDict:
        """
        Assign a resource to a service call ticket.

        Args:
            service_call_id: ID of the service call ticket
            resource_id: ID of the resource to assign

        Returns:
            Updated service call ticket data
        """
        return self.update_by_id(service_call_id, {"AssignedResourceID": resource_id})

    def schedule_service_call(
        self,
        service_call_id: int,
        service_call_date: str,
        duration_hours: Optional[float] = None,
    ) -> EntityDict:
        """
        Schedule a service call ticket.

        Args:
            service_call_id: ID of the service call ticket
            service_call_date: Scheduled date and time
            duration_hours: Expected duration in hours

        Returns:
            Updated service call ticket data
        """
        update_data = {"ServiceCallDate": service_call_date}
        if duration_hours is not None:
            update_data["DurationHours"] = duration_hours

        return self.update_by_id(service_call_id, update_data)

    def complete_service_call(self, service_call_id: int) -> EntityDict:
        """
        Mark a service call ticket as completed.

        Args:
            service_call_id: ID of the service call ticket

        Returns:
            Updated service call ticket data
        """
        # Assuming status 5 is "Completed"
        return self.update_by_id(service_call_id, {"Status": 5})

    def get_service_call_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about service call tickets.

        Returns:
            Dictionary containing service call statistics
        """
        all_service_calls = self.query()

        # Group by status
        status_counts = {}
        for ticket in all_service_calls:
            status = ticket.get("Status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Group by priority
        priority_counts = {}
        for ticket in all_service_calls:
            priority = ticket.get("Priority", "Unknown")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Calculate duration statistics
        durations = [
            ticket.get("DurationHours", 0)
            for ticket in all_service_calls
            if ticket.get("DurationHours")
        ]

        # Count assigned vs unassigned
        assigned_count = len(
            [ticket for ticket in all_service_calls if ticket.get("AssignedResourceID")]
        )

        stats = {
            "total_service_calls": len(all_service_calls),
            "assigned_service_calls": assigned_count,
            "unassigned_service_calls": len(all_service_calls) - assigned_count,
            "service_calls_by_status": status_counts,
            "service_calls_by_priority": priority_counts,
            "service_calls_with_location": len(
                [
                    ticket
                    for ticket in all_service_calls
                    if ticket.get("ServiceLocation")
                ]
            ),
        }

        if durations:
            stats["duration_statistics"] = {
                "total_hours": sum(durations),
                "average_duration": round(sum(durations) / len(durations), 2),
                "min_duration": min(durations),
                "max_duration": max(durations),
            }

        return stats

    def get_resource_schedule(
        self, resource_id: int, date_range_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get the service call schedule for a specific resource.

        Args:
            resource_id: ID of the resource
            date_range_days: Number of days to include in schedule

        Returns:
            Dictionary with schedule information
        """
        from datetime import date, timedelta

        start_date = date.today().strftime("%Y-%m-%d")
        end_date = (date.today() + timedelta(days=date_range_days)).strftime("%Y-%m-%d")

        # Get service calls for the resource in the date range
        filters = [
            QueryFilter(field="AssignedResourceID", op="eq", value=resource_id),
            QueryFilter(field="ServiceCallDate", op="ge", value=start_date),
            QueryFilter(field="ServiceCallDate", op="le", value=end_date),
        ]

        scheduled_calls = self.query(filters=filters)

        # Sort by date
        scheduled_calls.sort(key=lambda x: x.get("ServiceCallDate", ""))

        total_hours = sum(call.get("DurationHours", 0) for call in scheduled_calls)

        schedule = {
            "resource_id": resource_id,
            "date_range": f"{start_date} to {end_date}",
            "total_service_calls": len(scheduled_calls),
            "total_scheduled_hours": total_hours,
            "scheduled_calls": [
                {
                    "id": call.get("id"),
                    "title": call.get("Title"),
                    "date": call.get("ServiceCallDate"),
                    "duration": call.get("DurationHours"),
                    "location": call.get("ServiceLocation"),
                    "status": call.get("Status"),
                }
                for call in scheduled_calls
            ],
        }

        return schedule

    def get_daily_schedule(self, target_date: str) -> Dict[str, Any]:
        """
        Get all service calls scheduled for a specific date.

        Args:
            target_date: Date to get schedule for (YYYY-MM-DD)

        Returns:
            Dictionary with daily schedule
        """
        filters = [
            QueryFilter(field="ServiceCallDate", op="contains", value=target_date)
        ]

        daily_calls = self.query(filters=filters)

        # Group by resource
        resource_schedules = {}
        unassigned_calls = []

        for call in daily_calls:
            resource_id = call.get("AssignedResourceID")
            if resource_id:
                if resource_id not in resource_schedules:
                    resource_schedules[resource_id] = []
                resource_schedules[resource_id].append(call)
            else:
                unassigned_calls.append(call)

        schedule = {
            "date": target_date,
            "total_service_calls": len(daily_calls),
            "assigned_calls": len(daily_calls) - len(unassigned_calls),
            "unassigned_calls": len(unassigned_calls),
            "resource_schedules": resource_schedules,
            "unassigned_calls_list": unassigned_calls,
        }

        return schedule
