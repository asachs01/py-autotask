"""
Comprehensive Time Entries entity for Autotask API operations.

This module provides full PSA functionality for time tracking, billing, approvals,
and analytics in Autotask. It includes:

- Full CRUD operations for time entries
- Time tracking and management (start/stop timers, duration calculation)
- Billing and invoicing support
- Approval workflows (submit for approval, approve, reject)
- Integration with tickets, tasks, and projects
- Bulk time entry operations
- Time sheet generation and reporting
- Overtime and holiday tracking
- Advanced search and filtering
- Analytics (utilization, billable vs non-billable, etc.)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ..constants import (
    TimeEntryBillingType,
    TimeEntryConstants,
    TimeEntryStatus,
    TimeEntryType,
    validate_status_filter,
)
from ..types import QueryFilter, TimeEntryData
from .base import BaseEntity

logger = logging.getLogger(__name__)


class TimeEntriesEntity(BaseEntity):
    """
    Comprehensive time entries entity for Autotask PSA.

    Provides full time tracking and billing functionality including:
    - Time entry CRUD operations
    - Time tracking with start/stop timers
    - Billing and invoicing integration
    - Approval workflows
    - Bulk operations
    - Time sheet management
    - Overtime calculations
    - Advanced analytics and reporting
    """

    def __init__(self, client, entity_name="TimeEntries"):
        """Initialize the time entries entity."""
        super().__init__(client, entity_name)
        self.logger = logging.getLogger(f"{__name__}.{entity_name}")

    # =============================================================================
    # Core CRUD Operations
    # =============================================================================

    def create_time_entry(
        self,
        resource_id: int,
        date_worked: str,
        hours_worked: float,
        ticket_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        account_id: Optional[int] = None,
        role_id: Optional[int] = None,
        billing_code_id: Optional[int] = None,
        entry_type: int = TimeEntryType.REGULAR,
        billable: bool = True,
        description: Optional[str] = None,
        internal_notes: Optional[str] = None,
        summary_notes: Optional[str] = None,
        **kwargs,
    ) -> TimeEntryData:
        """
        Create a new time entry with comprehensive field support.

        Args:
            resource_id: ID of the resource logging time
            date_worked: Date the work was performed (YYYY-MM-DD format)
            hours_worked: Number of hours worked (decimal)
            ticket_id: Optional ticket ID
            project_id: Optional project ID
            task_id: Optional task ID
            account_id: Optional account ID
            role_id: Optional role ID for billing
            billing_code_id: Optional billing code
            entry_type: Time entry type (use TimeEntryType enum)
            billable: Whether the time is billable to the account
            description: Work description/summary
            internal_notes: Internal notes (not visible to customer)
            summary_notes: Summary notes (may be visible to customer)
            **kwargs: Additional time entry fields

        Returns:
            Created time entry data

        Raises:
            ValueError: If hours_worked is invalid or required associations missing
            AutotaskAPIError: If the API request fails
        """
        self._validate_hours(hours_worked)
        self._validate_work_associations(ticket_id, project_id, task_id)

        time_entry_data = {
            "ResourceID": resource_id,
            "DateWorked": date_worked,
            "HoursWorked": hours_worked,
            "Type": entry_type,
            "BillableToAccount": billable,
            "Status": TimeEntryStatus.DRAFT,
            **kwargs,
        }

        # Add optional associations
        if ticket_id:
            time_entry_data["TicketID"] = ticket_id
        if project_id:
            time_entry_data["ProjectID"] = project_id
        if task_id:
            time_entry_data["TaskID"] = task_id
        if account_id:
            time_entry_data["AccountID"] = account_id
        if role_id:
            time_entry_data["RoleID"] = role_id
        if billing_code_id:
            time_entry_data["BillingCodeID"] = billing_code_id

        # Add descriptions and notes
        if description:
            time_entry_data["Description"] = description
        if internal_notes:
            time_entry_data["InternalNotes"] = internal_notes
        if summary_notes:
            time_entry_data["SummaryNotes"] = summary_notes

        self.logger.info(
            f"Creating time entry for resource {resource_id}: {hours_worked} hours on {date_worked}"
        )
        return self.create(time_entry_data)

    def update_time_entry(
        self,
        time_entry_id: int,
        hours_worked: Optional[float] = None,
        description: Optional[str] = None,
        internal_notes: Optional[str] = None,
        summary_notes: Optional[str] = None,
        entry_type: Optional[int] = None,
        billable: Optional[bool] = None,
        **kwargs,
    ) -> TimeEntryData:
        """
        Update an existing time entry.

        Args:
            time_entry_id: ID of time entry to update
            hours_worked: New hours worked value
            description: Updated description
            internal_notes: Updated internal notes
            summary_notes: Updated summary notes
            entry_type: Updated entry type
            billable: Updated billable status
            **kwargs: Additional fields to update

        Returns:
            Updated time entry data

        Raises:
            ValueError: If hours_worked is invalid
            AutotaskAPIError: If the API request fails
        """
        update_data = {}

        if hours_worked is not None:
            self._validate_hours(hours_worked)
            update_data["HoursWorked"] = hours_worked

        if description is not None:
            update_data["Description"] = description
        if internal_notes is not None:
            update_data["InternalNotes"] = internal_notes
        if summary_notes is not None:
            update_data["SummaryNotes"] = summary_notes
        if entry_type is not None:
            update_data["Type"] = entry_type
        if billable is not None:
            update_data["BillableToAccount"] = billable

        update_data.update(kwargs)

        if not update_data:
            raise ValueError("No fields provided to update")

        self.logger.info(f"Updating time entry {time_entry_id}")
        return self.update_by_id(time_entry_id, update_data)

    def get_time_entry(self, time_entry_id: int) -> Optional[TimeEntryData]:
        """
        Get a single time entry by ID.

        Args:
            time_entry_id: Time entry ID

        Returns:
            Time entry data or None if not found
        """
        return self.get(time_entry_id)

    def delete_time_entry(self, time_entry_id: int) -> bool:
        """
        Delete a time entry.

        Args:
            time_entry_id: Time entry ID to delete

        Returns:
            True if deleted successfully

        Note:
            Some time entries may not be deletable if they've been approved or invoiced
        """
        try:
            self.delete(time_entry_id)
            self.logger.info(f"Deleted time entry {time_entry_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete time entry {time_entry_id}: {e}")
            return False

    # =============================================================================
    # Query and Search Operations
    # =============================================================================

    def get_time_entries_by_resource(
        self,
        resource_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status_filter: Optional[str] = None,
        include_non_billable: bool = True,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific resource with advanced filtering.

        Args:
            resource_id: Resource ID to filter by
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            status_filter: Status filter (draft, submitted, approved, etc.)
            include_non_billable: Whether to include non-billable entries
            limit: Maximum number of entries to return

        Returns:
            List of time entries for the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        if status_filter:
            status_ids = validate_status_filter(TimeEntryConstants, status_filter)
            if len(status_ids) == 1:
                filters.append(
                    QueryFilter(field="Status", op="eq", value=status_ids[0])
                )
            else:
                filters.append(QueryFilter(field="Status", op="in", value=status_ids))

        if not include_non_billable:
            filters.append(QueryFilter(field="BillableToAccount", op="eq", value=True))

        self.logger.debug(f"Querying time entries for resource {resource_id}")
        return self.query(filters=filters, max_records=limit)

    def get_time_entries_by_ticket(
        self,
        ticket_id: int,
        resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            resource_id: Optional resource filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of entries to return

        Returns:
            List of time entries for the ticket
        """
        filters = [QueryFilter(field="TicketID", op="eq", value=ticket_id)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        return self.query(filters=filters, max_records=limit)

    def get_time_entries_by_project(
        self,
        project_id: int,
        resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        task_id: Optional[int] = None,
        billable_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries for a specific project with advanced filtering.

        Args:
            project_id: Project ID to filter by
            resource_id: Optional resource filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            task_id: Optional task filter
            billable_only: Whether to include only billable entries
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
        if task_id:
            filters.append(QueryFilter(field="TaskID", op="eq", value=task_id))
        if billable_only:
            filters.append(QueryFilter(field="BillableToAccount", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_billable_time_entries(
        self,
        resource_id: Optional[int] = None,
        account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        unbilled_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get billable time entries with advanced filtering.

        Args:
            resource_id: Optional resource filter
            account_id: Optional account filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            unbilled_only: Whether to include only unbilled entries
            limit: Maximum number of entries to return

        Returns:
            List of billable time entries
        """
        filters = [QueryFilter(field="BillableToAccount", op="eq", value=True)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))
        if unbilled_only:
            filters.append(QueryFilter(field="Billed", op="eq", value=False))

        return self.query(filters=filters, max_records=limit)

    def search_time_entries(
        self,
        search_text: str,
        resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Search time entries by text across multiple fields.

        Args:
            search_text: Text to search for
            resource_id: Optional resource filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            search_fields: Fields to search in (default: description, notes)
            limit: Maximum number of entries to return

        Returns:
            List of matching time entries
        """
        if not search_fields:
            search_fields = ["Description", "InternalNotes", "SummaryNotes"]

        filters = []

        # Add text search filters (OR condition across fields)
        for field in search_fields:
            filters.append(QueryFilter(field=field, op="contains", value=search_text))

        # Add additional filters
        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        return self.query(filters=filters, max_records=limit)

    # =============================================================================
    # Time Tracking and Management
    # =============================================================================

    def start_time_tracking(
        self,
        resource_id: int,
        ticket_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a time tracking session (creates a draft time entry with start time).

        Args:
            resource_id: Resource starting the timer
            ticket_id: Optional ticket being worked on
            project_id: Optional project being worked on
            task_id: Optional task being worked on
            description: Optional description of work

        Returns:
            Dictionary with timer session information
        """
        start_time = datetime.now()

        # Create a draft time entry with start time
        time_entry_data = {
            "ResourceID": resource_id,
            "DateWorked": start_time.strftime("%Y-%m-%d"),
            "StartDateTime": start_time.isoformat(),
            "HoursWorked": 0.0,  # Will be calculated when stopped
            "Status": TimeEntryStatus.DRAFT,
            "Type": TimeEntryType.REGULAR,
            "BillableToAccount": True,  # Default to billable
        }

        if ticket_id:
            time_entry_data["TicketID"] = ticket_id
        if project_id:
            time_entry_data["ProjectID"] = project_id
        if task_id:
            time_entry_data["TaskID"] = task_id
        if description:
            time_entry_data["Description"] = description

        time_entry = self.create(time_entry_data)

        timer_session = {
            "time_entry_id": time_entry.get("id"),
            "resource_id": resource_id,
            "start_time": start_time.isoformat(),
            "status": "running",
            "ticket_id": ticket_id,
            "project_id": project_id,
            "task_id": task_id,
            "description": description,
        }

        self.logger.info(f"Started time tracking for resource {resource_id}")
        return timer_session

    def stop_time_tracking(
        self,
        time_entry_id: int,
        description: Optional[str] = None,
        internal_notes: Optional[str] = None,
    ) -> TimeEntryData:
        """
        Stop a time tracking session and calculate hours worked.

        Args:
            time_entry_id: ID of the time entry to stop
            description: Updated description of work performed
            internal_notes: Internal notes about the work

        Returns:
            Updated time entry with calculated hours
        """
        # Get the current time entry
        current_entry = self.get_time_entry(time_entry_id)
        if not current_entry:
            raise ValueError(f"Time entry {time_entry_id} not found")

        end_time = datetime.now()
        start_time_str = current_entry.get("StartDateTime") or current_entry.get(
            "start_date_time"
        )

        if not start_time_str:
            raise ValueError("Time entry does not have a start time")

        start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

        # Calculate hours worked
        duration = end_time - start_time
        hours_worked = duration.total_seconds() / 3600

        # Round to nearest increment (default 0.25 hours = 15 minutes)
        hours_worked = (
            round(hours_worked / TimeEntryConstants.DEFAULT_INCREMENT)
            * TimeEntryConstants.DEFAULT_INCREMENT
        )

        # Update the time entry
        update_data = {
            "EndDateTime": end_time.isoformat(),
            "HoursWorked": hours_worked,
        }

        if description:
            update_data["Description"] = description
        if internal_notes:
            update_data["InternalNotes"] = internal_notes

        self.logger.info(
            f"Stopped time tracking for entry {time_entry_id}: {hours_worked} hours"
        )
        return self.update_time_entry(time_entry_id, **update_data)

    def calculate_duration(self, start_time: str, end_time: str) -> float:
        """
        Calculate duration between start and end times.

        Args:
            start_time: Start time (ISO format)
            end_time: End time (ISO format)

        Returns:
            Duration in hours (decimal)
        """
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        duration = end_dt - start_dt
        return duration.total_seconds() / 3600

    def round_hours(self, hours: float, increment: float = None) -> float:
        """
        Round hours to the nearest increment.

        Args:
            hours: Hours to round
            increment: Rounding increment (default: 0.25 = 15 minutes)

        Returns:
            Rounded hours
        """
        if increment is None:
            increment = TimeEntryConstants.DEFAULT_INCREMENT

        return round(hours / increment) * increment

    # =============================================================================
    # Approval Workflows
    # =============================================================================

    def submit_for_approval(
        self,
        time_entry_ids: Union[int, List[int]],
        submission_notes: Optional[str] = None,
    ) -> List[TimeEntryData]:
        """
        Submit time entries for approval.

        Args:
            time_entry_ids: Single ID or list of time entry IDs
            submission_notes: Optional notes for the submission

        Returns:
            List of updated time entries
        """
        if isinstance(time_entry_ids, int):
            time_entry_ids = [time_entry_ids]

        updated_entries = []
        for time_entry_id in time_entry_ids:
            update_data = {
                "Status": TimeEntryStatus.SUBMITTED,
                "SubmittedDate": datetime.now().isoformat(),
            }

            if submission_notes:
                current_notes = ""
                entry = self.get_time_entry(time_entry_id)
                if entry and entry.get("InternalNotes"):
                    current_notes = entry["InternalNotes"] + "\n\n"

                update_data["InternalNotes"] = (
                    f"{current_notes}Submission: {submission_notes}"
                )

            updated_entry = self.update_time_entry(time_entry_id, **update_data)
            updated_entries.append(updated_entry)

        self.logger.info(f"Submitted {len(time_entry_ids)} time entries for approval")
        return updated_entries

    def approve_time_entries(
        self,
        time_entry_ids: Union[int, List[int]],
        approver_resource_id: int,
        approval_notes: Optional[str] = None,
    ) -> List[TimeEntryData]:
        """
        Approve time entries.

        Args:
            time_entry_ids: Single ID or list of time entry IDs to approve
            approver_resource_id: Resource ID of the approver
            approval_notes: Optional approval notes

        Returns:
            List of approved time entries
        """
        if isinstance(time_entry_ids, int):
            time_entry_ids = [time_entry_ids]

        updated_entries = []
        for time_entry_id in time_entry_ids:
            update_data = {
                "Status": TimeEntryStatus.APPROVED,
                "ApprovedDate": datetime.now().isoformat(),
                "ApprovedBy": approver_resource_id,
            }

            if approval_notes:
                current_notes = ""
                entry = self.get_time_entry(time_entry_id)
                if entry and entry.get("InternalNotes"):
                    current_notes = entry["InternalNotes"] + "\n\n"

                update_data["InternalNotes"] = (
                    f"{current_notes}Approved: {approval_notes}"
                )

            updated_entry = self.update_time_entry(time_entry_id, **update_data)
            updated_entries.append(updated_entry)

        self.logger.info(f"Approved {len(time_entry_ids)} time entries")
        return updated_entries

    def reject_time_entries(
        self,
        time_entry_ids: Union[int, List[int]],
        rejection_reason: str,
        rejector_resource_id: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Reject time entries with reason.

        Args:
            time_entry_ids: Single ID or list of time entry IDs to reject
            rejection_reason: Reason for rejection
            rejector_resource_id: Optional resource ID of the rejector

        Returns:
            List of rejected time entries
        """
        if isinstance(time_entry_ids, int):
            time_entry_ids = [time_entry_ids]

        updated_entries = []
        for time_entry_id in time_entry_ids:
            update_data = {
                "Status": TimeEntryStatus.REJECTED,
                "RejectedDate": datetime.now().isoformat(),
                "RejectionReason": rejection_reason,
            }

            if rejector_resource_id:
                update_data["RejectedBy"] = rejector_resource_id

            # Add rejection reason to internal notes
            current_notes = ""
            entry = self.get_time_entry(time_entry_id)
            if entry and entry.get("InternalNotes"):
                current_notes = entry["InternalNotes"] + "\n\n"

            update_data["InternalNotes"] = (
                f"{current_notes}Rejected: {rejection_reason}"
            )

            updated_entry = self.update_time_entry(time_entry_id, **update_data)
            updated_entries.append(updated_entry)

        self.logger.info(f"Rejected {len(time_entry_ids)} time entries")
        return updated_entries

    def get_pending_approvals(
        self,
        approver_resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TimeEntryData]:
        """
        Get time entries pending approval.

        Args:
            approver_resource_id: Optional approver filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of entries to return

        Returns:
            List of time entries pending approval
        """
        filters = [
            QueryFilter(field="Status", op="eq", value=TimeEntryStatus.SUBMITTED)
        ]

        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        # Note: In a real implementation, you'd filter by approver permissions/hierarchy
        # This is simplified for demonstration

        return self.query(filters=filters, max_records=limit)

    # =============================================================================
    # Bulk Operations
    # =============================================================================

    def bulk_create_time_entries(
        self, time_entries_data: List[Dict[str, Any]]
    ) -> List[TimeEntryData]:
        """
        Create multiple time entries in bulk.

        Args:
            time_entries_data: List of time entry data dictionaries

        Returns:
            List of created time entries
        """
        created_entries = []

        for entry_data in time_entries_data:
            try:
                # Validate required fields
                required_fields = ["ResourceID", "DateWorked", "HoursWorked"]
                for field in required_fields:
                    if field not in entry_data:
                        raise ValueError(f"Missing required field: {field}")

                # Set defaults
                if "Status" not in entry_data:
                    entry_data["Status"] = TimeEntryStatus.DRAFT
                if "Type" not in entry_data:
                    entry_data["Type"] = TimeEntryType.REGULAR
                if "BillableToAccount" not in entry_data:
                    entry_data["BillableToAccount"] = True

                created_entry = self.create(entry_data)
                created_entries.append(created_entry)

            except Exception as e:
                self.logger.error(f"Failed to create time entry in bulk: {e}")
                # Continue with other entries rather than failing completely
                continue

        self.logger.info(f"Bulk created {len(created_entries)} time entries")
        return created_entries

    def bulk_update_time_entries(
        self, updates: List[Dict[str, Any]]
    ) -> List[TimeEntryData]:
        """
        Update multiple time entries in bulk.

        Args:
            updates: List of dictionaries with 'id' and update data

        Returns:
            List of updated time entries
        """
        updated_entries = []

        for update_data in updates:
            try:
                time_entry_id = update_data.pop("id")
                updated_entry = self.update_time_entry(time_entry_id, **update_data)
                updated_entries.append(updated_entry)

            except Exception as e:
                self.logger.error(f"Failed to update time entry in bulk: {e}")
                continue

        self.logger.info(f"Bulk updated {len(updated_entries)} time entries")
        return updated_entries

    def bulk_submit_for_approval(
        self,
        resource_id: int,
        start_date: str,
        end_date: str,
        submission_notes: Optional[str] = None,
    ) -> List[TimeEntryData]:
        """
        Submit all draft time entries for a resource/period for approval.

        Args:
            resource_id: Resource whose entries to submit
            start_date: Start date for entries to submit
            end_date: End date for entries to submit
            submission_notes: Optional submission notes

        Returns:
            List of submitted time entries
        """
        # Get all draft entries for the resource/period
        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="DateWorked", op="gte", value=start_date),
            QueryFilter(field="DateWorked", op="lte", value=end_date),
            QueryFilter(field="Status", op="eq", value=TimeEntryStatus.DRAFT),
        ]

        draft_entries = self.query(filters=filters)

        if not draft_entries:
            return []

        entry_ids = [entry["id"] for entry in draft_entries]
        return self.submit_for_approval(entry_ids, submission_notes)

    def bulk_delete_time_entries(
        self, time_entry_ids: List[int], force: bool = False
    ) -> Dict[str, Any]:
        """
        Delete multiple time entries in bulk.

        Args:
            time_entry_ids: List of time entry IDs to delete
            force: Whether to attempt deletion even if entries may be protected

        Returns:
            Dictionary with deletion results
        """
        results = {
            "deleted": [],
            "failed": [],
            "total_requested": len(time_entry_ids),
        }

        for time_entry_id in time_entry_ids:
            try:
                if self.delete_time_entry(time_entry_id):
                    results["deleted"].append(time_entry_id)
                else:
                    results["failed"].append(
                        {"id": time_entry_id, "reason": "Delete failed"}
                    )
            except Exception as e:
                results["failed"].append({"id": time_entry_id, "reason": str(e)})

        results["deleted_count"] = len(results["deleted"])
        results["failed_count"] = len(results["failed"])

        self.logger.info(
            f"Bulk delete completed: {results['deleted_count']} deleted, {results['failed_count']} failed"
        )
        return results

    # =============================================================================
    # Time Sheet Operations
    # =============================================================================

    def get_time_sheet(
        self,
        resource_id: int,
        week_ending_date: str,
        include_non_billable: bool = True,
    ) -> Dict[str, Any]:
        """
        Get time sheet data for a resource and week.

        Args:
            resource_id: Resource ID
            week_ending_date: Week ending date (YYYY-MM-DD, typically Saturday)
            include_non_billable: Whether to include non-billable entries

        Returns:
            Dictionary with time sheet data including daily breakdowns
        """
        # Calculate week start date (7 days before ending date)
        week_end = datetime.strptime(week_ending_date, "%Y-%m-%d")
        week_start = week_end - timedelta(days=6)
        week_start_str = week_start.strftime("%Y-%m-%d")

        # Get time entries for the week
        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="DateWorked", op="gte", value=week_start_str),
            QueryFilter(field="DateWorked", op="lte", value=week_ending_date),
        ]

        if not include_non_billable:
            filters.append(QueryFilter(field="BillableToAccount", op="eq", value=True))

        time_entries = self.query(filters=filters)

        # Organize entries by day
        daily_breakdown = {}
        total_hours = 0
        billable_hours = 0
        overtime_hours = 0

        for entry in time_entries:
            date = entry.get("DateWorked") or entry.get("date_worked")
            hours = float(entry.get("HoursWorked") or entry.get("hours_worked", 0))
            is_billable = entry.get("BillableToAccount") or entry.get(
                "billable_to_account", False
            )
            entry_type = entry.get("Type") or entry.get("type", TimeEntryType.REGULAR)

            if date not in daily_breakdown:
                daily_breakdown[date] = {
                    "entries": [],
                    "total_hours": 0,
                    "billable_hours": 0,
                    "overtime_hours": 0,
                }

            daily_breakdown[date]["entries"].append(entry)
            daily_breakdown[date]["total_hours"] += hours

            if is_billable:
                daily_breakdown[date]["billable_hours"] += hours
                billable_hours += hours

            if entry_type in [TimeEntryType.OVERTIME, TimeEntryType.DOUBLE_TIME]:
                daily_breakdown[date]["overtime_hours"] += hours
                overtime_hours += hours

            total_hours += hours

        # Calculate overtime eligibility
        overtime_eligible = total_hours > TimeEntryConstants.OVERTIME_WEEKLY_THRESHOLD

        time_sheet = {
            "resource_id": resource_id,
            "week_start_date": week_start_str,
            "week_ending_date": week_ending_date,
            "daily_breakdown": daily_breakdown,
            "totals": {
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": total_hours - billable_hours,
                "overtime_hours": overtime_hours,
                "regular_hours": total_hours - overtime_hours,
            },
            "overtime_eligible": overtime_eligible,
            "entry_count": len(time_entries),
        }

        return time_sheet

    def generate_time_sheet_report(
        self,
        resource_id: int,
        start_date: str,
        end_date: str,
        format: str = "summary",
    ) -> Dict[str, Any]:
        """
        Generate time sheet report for a date range.

        Args:
            resource_id: Resource ID
            start_date: Report start date
            end_date: Report end date
            format: Report format ('summary', 'detailed', 'weekly')

        Returns:
            Dictionary with time sheet report data
        """
        time_entries = self.get_time_entries_by_resource(
            resource_id, start_date, end_date
        )

        if format == "weekly":
            # Group by weeks
            weekly_data = {}
            for entry in time_entries:
                date = datetime.strptime(
                    entry.get("DateWorked", entry.get("date_worked")), "%Y-%m-%d"
                )
                # Calculate week ending date (next Saturday)
                days_until_saturday = (5 - date.weekday()) % 7
                if days_until_saturday == 0 and date.weekday() != 5:  # If not Saturday
                    days_until_saturday = 7
                week_end = date + timedelta(days=days_until_saturday)
                week_key = week_end.strftime("%Y-%m-%d")

                if week_key not in weekly_data:
                    weekly_data[week_key] = self.get_time_sheet(resource_id, week_key)

            return {
                "resource_id": resource_id,
                "start_date": start_date,
                "end_date": end_date,
                "format": format,
                "weekly_data": weekly_data,
            }

        # Calculate summary data
        total_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in time_entries
        )
        billable_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in time_entries
            if entry.get("BillableToAccount", entry.get("billable_to_account", False))
        )

        summary_data = {
            "resource_id": resource_id,
            "start_date": start_date,
            "end_date": end_date,
            "format": format,
            "totals": {
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": total_hours - billable_hours,
                "entry_count": len(time_entries),
                "average_hours_per_day": total_hours
                / max(
                    1,
                    len(
                        set(
                            entry.get("DateWorked", entry.get("date_worked"))
                            for entry in time_entries
                        )
                    ),
                ),
            },
        }

        if format == "detailed":
            summary_data["entries"] = time_entries

        return summary_data

    # =============================================================================
    # Overtime and Holiday Tracking
    # =============================================================================

    def calculate_overtime(
        self,
        resource_id: int,
        date: str,
    ) -> Dict[str, Any]:
        """
        Calculate overtime hours for a resource on a specific date.

        Args:
            resource_id: Resource ID
            date: Date to calculate overtime for

        Returns:
            Dictionary with overtime calculation details
        """
        # Get all time entries for the date
        daily_entries = self.get_time_entries_by_resource(resource_id, date, date)

        total_daily_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in daily_entries
        )

        regular_hours = min(
            total_daily_hours, TimeEntryConstants.OVERTIME_DAILY_THRESHOLD
        )
        overtime_hours = max(
            0, total_daily_hours - TimeEntryConstants.OVERTIME_DAILY_THRESHOLD
        )
        double_time_hours = max(
            0, total_daily_hours - TimeEntryConstants.DOUBLE_TIME_THRESHOLD
        )

        # Adjust overtime if there's double time
        if double_time_hours > 0:
            overtime_hours = max(0, overtime_hours - double_time_hours)

        return {
            "resource_id": resource_id,
            "date": date,
            "total_hours": total_daily_hours,
            "regular_hours": regular_hours,
            "overtime_hours": overtime_hours,
            "double_time_hours": double_time_hours,
            "entries": daily_entries,
        }

    def calculate_weekly_overtime(
        self,
        resource_id: int,
        week_ending_date: str,
    ) -> Dict[str, Any]:
        """
        Calculate weekly overtime for a resource.

        Args:
            resource_id: Resource ID
            week_ending_date: Week ending date

        Returns:
            Dictionary with weekly overtime calculation
        """
        week_end = datetime.strptime(week_ending_date, "%Y-%m-%d")
        week_start = week_end - timedelta(days=6)

        weekly_entries = self.get_time_entries_by_resource(
            resource_id, week_start.strftime("%Y-%m-%d"), week_ending_date
        )

        total_weekly_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in weekly_entries
        )

        regular_hours = min(
            total_weekly_hours, TimeEntryConstants.OVERTIME_WEEKLY_THRESHOLD
        )
        overtime_hours = max(
            0, total_weekly_hours - TimeEntryConstants.OVERTIME_WEEKLY_THRESHOLD
        )

        return {
            "resource_id": resource_id,
            "week_start_date": week_start.strftime("%Y-%m-%d"),
            "week_ending_date": week_ending_date,
            "total_weekly_hours": total_weekly_hours,
            "regular_hours": regular_hours,
            "overtime_hours": overtime_hours,
            "entries": weekly_entries,
        }

    def mark_holiday_entries(
        self,
        date: str,
        resource_ids: Optional[List[int]] = None,
        holiday_type: int = TimeEntryType.HOLIDAY,
    ) -> List[TimeEntryData]:
        """
        Mark time entries for a specific date as holiday entries.

        Args:
            date: Holiday date
            resource_ids: Optional list of resource IDs (if None, applies to all entries on date)
            holiday_type: Type of holiday entry

        Returns:
            List of updated time entries
        """
        filters = [QueryFilter(field="DateWorked", op="eq", value=date)]

        if resource_ids:
            filters.append(QueryFilter(field="ResourceID", op="in", value=resource_ids))

        entries_to_update = self.query(filters=filters)
        updated_entries = []

        for entry in entries_to_update:
            entry_id = entry.get("id")
            if entry_id:
                updated_entry = self.update_time_entry(
                    entry_id,
                    entry_type=holiday_type,
                    is_holiday=True,
                    internal_notes=f"Holiday entry for {date}",
                )
                updated_entries.append(updated_entry)

        self.logger.info(f"Marked {len(updated_entries)} entries as holiday for {date}")
        return updated_entries

    def get_holiday_hours(
        self,
        resource_id: int,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        Get holiday hours for a resource over a date range.

        Args:
            resource_id: Resource ID
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with holiday hours breakdown
        """
        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="DateWorked", op="gte", value=start_date),
            QueryFilter(field="DateWorked", op="lte", value=end_date),
            QueryFilter(field="Type", op="eq", value=TimeEntryType.HOLIDAY),
        ]

        holiday_entries = self.query(filters=filters)
        total_holiday_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in holiday_entries
        )

        # Group by date
        by_date = {}
        for entry in holiday_entries:
            date = entry.get("DateWorked", entry.get("date_worked"))
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(entry)

        return {
            "resource_id": resource_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_holiday_hours": total_holiday_hours,
            "holiday_days": len(by_date),
            "by_date": by_date,
            "entries": holiday_entries,
        }

    # =============================================================================
    # Analytics and Reporting
    # =============================================================================

    def get_utilization_report(
        self,
        resource_id: int,
        start_date: str,
        end_date: str,
        target_hours_per_week: float = 40.0,
    ) -> Dict[str, Any]:
        """
        Generate utilization report for a resource.

        Args:
            resource_id: Resource ID
            start_date: Start date
            end_date: End date
            target_hours_per_week: Target billable hours per week

        Returns:
            Dictionary with utilization metrics
        """
        time_entries = self.get_time_entries_by_resource(
            resource_id, start_date, end_date
        )

        # Calculate date range in weeks
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_in_range = (end_dt - start_dt).days + 1
        weeks_in_range = days_in_range / 7

        # Calculate metrics
        total_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in time_entries
        )
        billable_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in time_entries
            if entry.get("BillableToAccount", entry.get("billable_to_account", False))
        )

        target_billable_hours = target_hours_per_week * weeks_in_range
        utilization_percentage = (billable_hours / max(target_billable_hours, 1)) * 100
        efficiency_percentage = (billable_hours / max(total_hours, 1)) * 100

        return {
            "resource_id": resource_id,
            "start_date": start_date,
            "end_date": end_date,
            "days_in_range": days_in_range,
            "weeks_in_range": weeks_in_range,
            "metrics": {
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": total_hours - billable_hours,
                "target_billable_hours": target_billable_hours,
                "utilization_percentage": utilization_percentage,
                "efficiency_percentage": efficiency_percentage,
                "average_hours_per_week": total_hours / max(weeks_in_range, 1),
                "average_billable_per_week": billable_hours / max(weeks_in_range, 1),
            },
            "entry_count": len(time_entries),
        }

    def get_billability_analysis(
        self,
        resource_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze billability across time entries.

        Args:
            resource_id: Optional resource filter
            project_id: Optional project filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary with billability analysis
        """
        filters = []

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if project_id:
            filters.append(QueryFilter(field="ProjectID", op="eq", value=project_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        time_entries = self.query(filters=filters) if filters else []

        # Calculate billability metrics
        total_hours = 0
        billable_hours = 0
        non_billable_hours = 0
        billed_hours = 0
        unbilled_hours = 0

        by_type = {}
        by_resource = {}
        by_project = {}

        for entry in time_entries:
            hours = float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            is_billable = entry.get(
                "BillableToAccount", entry.get("billable_to_account", False)
            )
            is_billed = entry.get("Billed", entry.get("billed", False))
            entry_type = entry.get("Type", entry.get("type", TimeEntryType.REGULAR))
            resource = entry.get("ResourceID", entry.get("resource_id"))
            project = entry.get("ProjectID", entry.get("project_id"))

            total_hours += hours

            if is_billable:
                billable_hours += hours
                if is_billed:
                    billed_hours += hours
                else:
                    unbilled_hours += hours
            else:
                non_billable_hours += hours

            # Group by type
            if entry_type not in by_type:
                by_type[entry_type] = {"hours": 0, "billable_hours": 0, "count": 0}
            by_type[entry_type]["hours"] += hours
            if is_billable:
                by_type[entry_type]["billable_hours"] += hours
            by_type[entry_type]["count"] += 1

            # Group by resource
            if resource:
                if resource not in by_resource:
                    by_resource[resource] = {
                        "hours": 0,
                        "billable_hours": 0,
                        "count": 0,
                    }
                by_resource[resource]["hours"] += hours
                if is_billable:
                    by_resource[resource]["billable_hours"] += hours
                by_resource[resource]["count"] += 1

            # Group by project
            if project:
                if project not in by_project:
                    by_project[project] = {"hours": 0, "billable_hours": 0, "count": 0}
                by_project[project]["hours"] += hours
                if is_billable:
                    by_project[project]["billable_hours"] += hours
                by_project[project]["count"] += 1

        billability_percentage = (billable_hours / max(total_hours, 1)) * 100
        utilization_percentage = (billed_hours / max(billable_hours, 1)) * 100

        return {
            "filters": {
                "resource_id": resource_id,
                "project_id": project_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            "totals": {
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": non_billable_hours,
                "billed_hours": billed_hours,
                "unbilled_hours": unbilled_hours,
                "billability_percentage": billability_percentage,
                "utilization_percentage": utilization_percentage,
            },
            "breakdowns": {
                "by_type": by_type,
                "by_resource": by_resource,
                "by_project": by_project,
            },
            "entry_count": len(time_entries),
        }

    def get_productivity_metrics(
        self,
        resource_id: int,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        Calculate productivity metrics for a resource.

        Args:
            resource_id: Resource ID
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with productivity metrics
        """
        time_entries = self.get_time_entries_by_resource(
            resource_id, start_date, end_date
        )

        # Group entries by day
        daily_data = {}
        for entry in time_entries:
            date = entry.get("DateWorked", entry.get("date_worked"))
            if date not in daily_data:
                daily_data[date] = {
                    "total_hours": 0,
                    "billable_hours": 0,
                    "entries": 0,
                    "projects": set(),
                    "tickets": set(),
                }

            hours = float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            is_billable = entry.get(
                "BillableToAccount", entry.get("billable_to_account", False)
            )
            project_id = entry.get("ProjectID", entry.get("project_id"))
            ticket_id = entry.get("TicketID", entry.get("ticket_id"))

            daily_data[date]["total_hours"] += hours
            if is_billable:
                daily_data[date]["billable_hours"] += hours
            daily_data[date]["entries"] += 1

            if project_id:
                daily_data[date]["projects"].add(project_id)
            if ticket_id:
                daily_data[date]["tickets"].add(ticket_id)

        # Calculate metrics
        total_days = len(daily_data)
        total_hours = sum(day["total_hours"] for day in daily_data.values())
        total_billable = sum(day["billable_hours"] for day in daily_data.values())
        total_entries = sum(day["entries"] for day in daily_data.values())

        # Convert sets to counts for JSON serialization
        for date_data in daily_data.values():
            date_data["project_count"] = len(date_data["projects"])
            date_data["ticket_count"] = len(date_data["tickets"])
            date_data.pop("projects", None)
            date_data.pop("tickets", None)

        return {
            "resource_id": resource_id,
            "start_date": start_date,
            "end_date": end_date,
            "summary": {
                "total_days_worked": total_days,
                "total_hours": total_hours,
                "total_billable_hours": total_billable,
                "total_entries": total_entries,
                "average_hours_per_day": total_hours / max(total_days, 1),
                "average_entries_per_day": total_entries / max(total_days, 1),
                "billability_percentage": (total_billable / max(total_hours, 1)) * 100,
            },
            "daily_breakdown": daily_data,
        }

    def get_time_distribution(
        self,
        resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "project",
    ) -> Dict[str, Any]:
        """
        Get time distribution across different dimensions.

        Args:
            resource_id: Optional resource filter
            start_date: Optional start date
            end_date: Optional end date
            group_by: Grouping dimension (project, ticket, account, type, etc.)

        Returns:
            Dictionary with time distribution data
        """
        filters = []

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if start_date:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=end_date))

        time_entries = self.query(filters=filters)

        # Group data by the specified dimension
        distribution = {}
        total_hours = 0

        field_mapping = {
            "project": "ProjectID",
            "ticket": "TicketID",
            "account": "AccountID",
            "type": "Type",
            "task": "TaskID",
        }

        group_field = field_mapping.get(group_by.lower(), "ProjectID")

        for entry in time_entries:
            hours = float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            group_value = (
                entry.get(group_field) or entry.get(group_field.lower()) or "Unassigned"
            )

            if group_value not in distribution:
                distribution[group_value] = {
                    "total_hours": 0,
                    "billable_hours": 0,
                    "entry_count": 0,
                    "percentage": 0,
                }

            distribution[group_value]["total_hours"] += hours
            distribution[group_value]["entry_count"] += 1

            if entry.get("BillableToAccount", entry.get("billable_to_account", False)):
                distribution[group_value]["billable_hours"] += hours

            total_hours += hours

        # Calculate percentages
        for group_data in distribution.values():
            group_data["percentage"] = (
                group_data["total_hours"] / max(total_hours, 1)
            ) * 100

        # Sort by total hours (descending)
        sorted_distribution = dict(
            sorted(
                distribution.items(), key=lambda x: x[1]["total_hours"], reverse=True
            )
        )

        return {
            "group_by": group_by,
            "filters": {
                "resource_id": resource_id,
                "start_date": start_date,
                "end_date": end_date,
            },
            "total_hours": total_hours,
            "distribution": sorted_distribution,
            "group_count": len(distribution),
        }

    # =============================================================================
    # Helper and Utility Methods
    # =============================================================================

    def _validate_hours(self, hours: float) -> None:
        """Validate hours worked value."""
        if hours < TimeEntryConstants.MIN_HOURS:
            raise ValueError(f"Hours must be at least {TimeEntryConstants.MIN_HOURS}")
        if hours > TimeEntryConstants.MAX_HOURS_PER_ENTRY:
            raise ValueError(
                f"Hours cannot exceed {TimeEntryConstants.MAX_HOURS_PER_ENTRY}"
            )

    def _validate_work_associations(
        self,
        ticket_id: Optional[int] = None,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> None:
        """Validate that at least one work association is provided."""
        if not any([ticket_id, project_id, task_id]):
            raise ValueError(
                "Time entry must be associated with at least one ticket, project, or task"
            )

    def get_summary_for_period(
        self,
        start_date: str,
        end_date: str,
        resource_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary for a date period.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            resource_id: Optional resource filter
            account_id: Optional account filter

        Returns:
            Dictionary with period summary data
        """
        filters = [
            QueryFilter(field="DateWorked", op="gte", value=start_date),
            QueryFilter(field="DateWorked", op="lte", value=end_date),
        ]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))
        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        time_entries = self.query(filters=filters)

        # Calculate comprehensive metrics
        total_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in time_entries
        )
        billable_hours = sum(
            float(entry.get("HoursWorked", entry.get("hours_worked", 0)))
            for entry in time_entries
            if entry.get("BillableToAccount", entry.get("billable_to_account", False))
        )

        # Count by status
        status_counts = {}
        for entry in time_entries:
            status = entry.get("Status", entry.get("status", TimeEntryStatus.DRAFT))
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by type
        type_counts = {}
        for entry in time_entries:
            entry_type = entry.get("Type", entry.get("type", TimeEntryType.REGULAR))
            type_counts[entry_type] = type_counts.get(entry_type, 0) + 1

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "resource_id": resource_id,
                "account_id": account_id,
            },
            "totals": {
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": total_hours - billable_hours,
                "entry_count": len(time_entries),
                "billability_percentage": (billable_hours / max(total_hours, 1)) * 100,
            },
            "breakdowns": {
                "by_status": status_counts,
                "by_type": type_counts,
            },
            "entries": time_entries,
        }
