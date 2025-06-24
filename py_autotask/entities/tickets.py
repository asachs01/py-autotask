"""
Tickets entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter, TicketData
from .base import BaseEntity


class TicketsEntity(BaseEntity):
    """
    Handles all Ticket-related operations for the Autotask API.

    Tickets are the core work items in Autotask representing service requests,
    incidents, changes, and other work items.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ticket(
        self,
        title: str,
        description: str,
        account_id: int,
        queue_id: Optional[int] = None,
        priority: Optional[int] = None,
        status: Optional[int] = None,
        ticket_type: Optional[int] = None,
        **kwargs,
    ) -> TicketData:
        """
        Create a new ticket with required and optional fields.

        Args:
            title: Ticket title/summary
            description: Detailed description
            account_id: ID of the account/company
            queue_id: Queue to assign ticket to
            priority: Priority level (1-4, 1=Critical, 4=Low)
            status: Status ID
            ticket_type: Type of ticket
            **kwargs: Additional ticket fields

        Returns:
            Created ticket data
        """
        ticket_data = {
            "Title": title,
            "Description": description,
            "AccountID": account_id,
            **kwargs,
        }

        # Add optional fields if provided
        if queue_id is not None:
            ticket_data["QueueID"] = queue_id
        if priority is not None:
            ticket_data["Priority"] = priority
        if status is not None:
            ticket_data["Status"] = status
        if ticket_type is not None:
            ticket_data["TicketType"] = ticket_type

        return self.create(ticket_data)

    def get_tickets_by_account(
        self,
        account_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TicketData]:
        """
        Get all tickets for a specific account.

        Args:
            account_id: Account ID to filter by
            status_filter: Optional status filter ('open', 'closed', etc.)
            limit: Maximum number of tickets to return

        Returns:
            List of tickets for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        if status_filter:
            # Map common status filters to Autotask status IDs
            status_map = {
                "open": [1, 8, 9, 10, 11],  # Common open statuses
                "closed": [5],  # Closed/Complete
                "new": [1],  # New
                "in_progress": [8, 9, 10, 11],  # Various in-progress statuses
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    # Use 'in' operator for multiple status IDs
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        return self.query(filters=filters, max_records=limit)

    def get_tickets_by_resource(
        self,
        resource_id: int,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> List[TicketData]:
        """
        Get tickets assigned to a specific resource.

        Args:
            resource_id: Resource ID to filter by
            include_completed: Whether to include completed tickets
            limit: Maximum number of tickets to return

        Returns:
            List of tickets assigned to the resource
        """
        filters = [QueryFilter(field="AssignedResourceID", op="eq", value=resource_id)]

        if not include_completed:
            # Exclude completed status (5)
            filters.append(QueryFilter(field="Status", op="ne", value=5))

        return self.query(filters=filters, max_records=limit)

    def get_overdue_tickets(
        self, account_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[TicketData]:
        """
        Get tickets that are past their due date.

        Args:
            account_id: Optional account ID filter
            limit: Maximum number of tickets to return

        Returns:
            List of overdue tickets
        """
        from datetime import datetime

        filters = [
            QueryFilter(field="DueDateTime", op="lt", value=datetime.now().isoformat()),
            QueryFilter(field="Status", op="ne", value=5),  # Not completed
        ]

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        return self.query(filters=filters, max_records=limit)

    def update_ticket_status(
        self, ticket_id: int, status: int, note: Optional[str] = None
    ) -> TicketData:
        """
        Update a ticket's status with optional note.

        Args:
            ticket_id: ID of ticket to update
            status: New status ID
            note: Optional note to add with status change

        Returns:
            Updated ticket data
        """
        update_data = {"Status": status}

        if note:
            # Add a note about the status change
            update_data["LastActivityPersonType"] = 1  # Internal note
            update_data["LastActivityBy"] = note

        return self.update_by_id(ticket_id, update_data)

    def assign_ticket(
        self, ticket_id: int, resource_id: int, queue_id: Optional[int] = None
    ) -> TicketData:
        """
        Assign a ticket to a resource and optionally change queue.

        Args:
            ticket_id: ID of ticket to assign
            resource_id: ID of resource to assign to
            queue_id: Optional new queue ID

        Returns:
            Updated ticket data
        """
        update_data = {"AssignedResourceID": resource_id}

        if queue_id:
            update_data["QueueID"] = queue_id

        return self.update_by_id(ticket_id, update_data)

    def get_ticket_notes(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get all notes for a specific ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of ticket notes
        """
        # Note: This would typically be a separate entity (TicketNotes)
        # but including here for convenience

        filters = [QueryFilter(field="TicketID", op="eq", value=ticket_id)]
        return self.client.query("TicketNotes", filters=filters)

    def add_ticket_note(
        self,
        ticket_id: int,
        note_text: str,
        note_type: int = 1,  # 1 = Internal, 2 = External
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a note to a ticket.

        Args:
            ticket_id: ID of the ticket
            note_text: Content of the note
            note_type: Type of note (1=Internal, 2=External)
            title: Optional note title

        Returns:
            Created note data
        """
        note_data = {
            "TicketID": ticket_id,
            "Description": note_text,
            "NoteType": note_type,
        }

        if title:
            note_data["Title"] = title

        return self.client.create_entity("TicketNotes", note_data)

    def get_ticket_time_entries(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get all time entries for a specific ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of time entries
        """
        filters = [QueryFilter(field="TicketID", op="eq", value=ticket_id)]
        return self.client.query("TimeEntries", filters=filters)

    def bulk_update_status(
        self, ticket_ids: List[int], status: int
    ) -> List[TicketData]:
        """
        Update status for multiple tickets.

        Args:
            ticket_ids: List of ticket IDs to update
            status: New status for all tickets

        Returns:
            List of updated ticket data
        """
        results = []
        for ticket_id in ticket_ids:
            try:
                result = self.update_ticket_status(ticket_id, status)
                results.append(result)
            except Exception as e:
                # Log error but continue with other tickets
                self.logger.error(f"Failed to update ticket {ticket_id}: {e}")

        return results

    def get_tickets_by_queue(
        self,
        queue_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TicketData]:
        """
        Get all tickets in a specific queue.

        Args:
            queue_id: Queue ID to filter by
            status_filter: Optional status filter ('open', 'closed', etc.)
            limit: Maximum number of tickets to return

        Returns:
            List of tickets in the queue
        """
        filters = [QueryFilter(field="QueueID", op="eq", value=queue_id)]

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

        return self.query(filters=filters, max_records=limit)

    def get_tickets_by_priority(
        self,
        priority: int,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> List[TicketData]:
        """
        Get tickets by priority level.

        Args:
            priority: Priority level (1=Critical, 2=High, 3=Medium, 4=Low)
            include_completed: Whether to include completed tickets
            limit: Maximum number of tickets to return

        Returns:
            List of tickets with the specified priority
        """
        filters = [QueryFilter(field="Priority", op="eq", value=priority)]

        if not include_completed:
            filters.append(QueryFilter(field="Status", op="ne", value=5))

        return self.query(filters=filters, max_records=limit)

    def escalate_ticket(
        self,
        ticket_id: int,
        escalation_level: int,
        escalation_note: Optional[str] = None,
    ) -> TicketData:
        """
        Escalate a ticket to a higher level.

        Args:
            ticket_id: ID of ticket to escalate
            escalation_level: New escalation level
            escalation_note: Optional escalation note

        Returns:
            Updated ticket data
        """
        update_data = {"EscalationLevel": escalation_level}

        if escalation_note:
            # Add escalation note
            self.add_ticket_note(
                ticket_id,
                f"Ticket escalated to level {escalation_level}: {escalation_note}",
                note_type=1,  # Internal note
            )

        return self.update_by_id(ticket_id, update_data)

    def close_ticket(
        self,
        ticket_id: int,
        resolution: Optional[str] = None,
        close_note: Optional[str] = None,
    ) -> TicketData:
        """
        Close a ticket with optional resolution.

        Args:
            ticket_id: ID of ticket to close
            resolution: Resolution description
            close_note: Optional closing note

        Returns:
            Updated ticket data
        """
        update_data = {"Status": 5}  # Closed/Complete status

        if resolution:
            update_data["Resolution"] = resolution

        if close_note:
            self.add_ticket_note(
                ticket_id,
                close_note,
                note_type=1,  # Internal note
                title="Ticket Closed",
            )

        return self.update_by_id(ticket_id, update_data)

    def reopen_ticket(
        self, ticket_id: int, reopen_reason: Optional[str] = None
    ) -> TicketData:
        """
        Reopen a closed ticket.

        Args:
            ticket_id: ID of ticket to reopen
            reopen_reason: Optional reason for reopening

        Returns:
            Updated ticket data
        """
        update_data = {"Status": 1}  # New status

        if reopen_reason:
            self.add_ticket_note(
                ticket_id,
                f"Ticket reopened: {reopen_reason}",
                note_type=1,  # Internal note
                title="Ticket Reopened",
            )

        return self.update_by_id(ticket_id, update_data)
