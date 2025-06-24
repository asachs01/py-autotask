"""
Time Entries entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter, TimeEntryData
from .base import BaseEntity


class TimeEntriesEntity(BaseEntity):
    """
    Handles all Time Entry-related operations for the Autotask API.

    Time entries in Autotask represent logged work time against tickets,
    projects, or other billable/non-billable activities.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_time_entry(
        self,
        resource_id: int,
        date_worked: str,
        hours_worked: float,
        ticket_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        role_id: Optional[int] = None,
        billing_code_id: Optional[int] = None,
        internal_notes: Optional[str] = None,
        summary_notes: Optional[str] = None,
        **kwargs,
    ) -> TimeEntryData:
        """
        Create a new time entry.

        Args:
            resource_id: ID of the resource logging time
            date_worked: Date the work was performed (YYYY-MM-DD format)
            hours_worked: Number of hours worked (decimal)
            ticket_id: Optional ticket ID
            project_id: Optional project ID
            task_id: Optional task ID
            role_id: Optional role ID for billing
            billing_code_id: Optional billing code
            internal_notes: Internal notes (not visible to customer)
            summary_notes: Summary notes (may be visible to customer)
            **kwargs: Additional time entry fields

        Returns:
            Created time entry data
        """
        time_entry_data = {
            "ResourceID": resource_id,
            "DateWorked": date_worked,
            "HoursWorked": hours_worked,
            **kwargs,
        }

        if ticket_id:
            time_entry_data["TicketID"] = ticket_id
        if project_id:
            time_entry_data["ProjectID"] = project_id
        if task_id:
            time_entry_data["TaskID"] = task_id
        if role_id:
            time_entry_data["RoleID"] = role_id
        if billing_code_id:
            time_entry_data["BillingCodeID"] = billing_code_id
        if internal_notes:
            time_entry_data["InternalNotes"] = internal_notes
        if summary_notes:
            time_entry_data["SummaryNotes"] = summary_notes

        return self.create(time_entry_data)

    def get_time_entries_by_resource(
        self,
        resource_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific resource.

        Args:
            resource_id: Resource ID to filter by
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            limit: Maximum number of entries to return

        Returns:
            List of time entries for the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        return self.query(filters=filters, max_records=limit)

    def get_time_entries_by_ticket(
        self,
        ticket_id: int,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            resource_id: Optional resource filter
            limit: Maximum number of entries to return

        Returns:
            List of time entries for the ticket
        """
        filters = [QueryFilter(field="TicketID", op="eq", value=ticket_id)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def get_time_entries_by_project(
        self,
        project_id: int,
        resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific project.

        Args:
            project_id: Project ID to filter by
            resource_id: Optional resource filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of entries to return

        Returns:
            List of time entries for the project
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        return self.query(filters=filters, max_records=limit)

    def get_billable_time_entries(
        self,
        resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get billable time entries.

        Args:
            resource_id: Optional resource filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of entries to return

        Returns:
            List of billable time entries
        """
        filters = [QueryFilter(field="BillableToAccount", op="eq", value=True)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        return self.query(filters=filters, max_records=limit)

    def get_time_entries_for_period(
        self,
        start_date: str,
        end_date: str,
        resource_id: Optional[int] = None,
        account_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            resource_id: Optional resource filter
            account_id: Optional account filter
            limit: Maximum number of entries to return

        Returns:
            List of time entries in the date range
        """
        filters = [
            QueryFilter(field="DateWorked", op="gte", value=start_date),
            QueryFilter(field="DateWorked", op="lte", value=end_date),
        ]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        return self.query(filters=filters, max_records=limit)

    def update_time_entry_hours(
        self,
        time_entry_id: int,
        hours_worked: float,
        update_notes: Optional[str] = None,
    ) -> TimeEntryData:
        """
        Update hours worked on a time entry.

        Args:
            time_entry_id: ID of time entry to update
            hours_worked: New hours worked value
            update_notes: Optional notes about the update

        Returns:
            Updated time entry data
        """
        update_data = {"HoursWorked": hours_worked}

        if update_notes:
            update_data["InternalNotes"] = update_notes

        return self.update_by_id(time_entry_id, update_data)

    def submit_time_entry(self, time_entry_id: int) -> TimeEntryData:
        """
        Submit a time entry for approval.

        Args:
            time_entry_id: ID of time entry to submit

        Returns:
            Updated time entry data
        """
        # In Autotask, submitted time entries typically have a status change
        update_data = {"Status": 1}  # Submitted status
        return self.update_by_id(time_entry_id, update_data)

    def approve_time_entry(
        self, time_entry_id: int, approval_notes: Optional[str] = None
    ) -> TimeEntryData:
        """
        Approve a time entry.

        Args:
            time_entry_id: ID of time entry to approve
            approval_notes: Optional approval notes

        Returns:
            Updated time entry data
        """
        update_data = {"Status": 2}  # Approved status

        if approval_notes:
            update_data["InternalNotes"] = approval_notes

        return self.update_by_id(time_entry_id, update_data)

    def get_time_summary_by_resource(
        self, resource_id: int, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Get time summary for a resource over a date range.

        Args:
            resource_id: Resource ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary with time summary data
        """
        time_entries = self.get_time_entries_by_resource(
            resource_id, start_date, end_date
        )

        total_hours = sum(entry.get("HoursWorked", 0) for entry in time_entries)
        billable_hours = sum(
            entry.get("HoursWorked", 0)
            for entry in time_entries
            if entry.get("BillableToAccount", False)
        )

        return {
            "resource_id": resource_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": total_hours - billable_hours,
            "entry_count": len(time_entries),
            "entries": time_entries,
        }
