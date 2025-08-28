"""
Ticket Notes entity for Autotask API operations.
"""

from typing import Any, Dict, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketNotesEntity(BaseEntity):
    """
    Handles all Ticket Note-related operations for the Autotask API.

    Ticket Notes provide communication tracking and documentation
    for tickets, supporting both internal and external visibility.
    """

    def __init__(self, client, entity_name: str = "TicketNotes"):
        super().__init__(client, entity_name)

    def create_note(
        self,
        ticket_id: int,
        description: str,
        note_type: int = 1,
        title: Optional[str] = None,
        publish: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new ticket note.

        Args:
            ticket_id: ID of the ticket to add note to
            description: Note content/description
            note_type: Type of note (1=Activity Log, 2=Detailed Description)
            title: Optional note title
            publish: Publish setting (1=All, 2=Internal Only)
            **kwargs: Additional note fields

        Returns:
            Created ticket note data
        """
        note_data = {
            "TicketID": ticket_id,
            "Description": description,
            "NoteType": note_type,
            "Publish": publish,
            **kwargs,
        }

        if title:
            note_data["Title"] = title

        return self.create(note_data)

    def get_notes_by_ticket(
        self,
        ticket_id: int,
        note_type: Optional[int] = None,
        include_private: bool = True,
    ) -> EntityList:
        """
        Get all notes for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            note_type: Optional note type filter
            include_private: Whether to include private/internal notes

        Returns:
            List of ticket notes
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]

        if note_type is not None:
            filters.append({"field": "NoteType", "op": "eq", "value": str(note_type)})

        if not include_private:
            filters.append({"field": "Publish", "op": "ne", "value": "2"})

        return self.query_all(filters=filters)

    def get_recent_notes(
        self,
        days: int = 7,
        note_type: Optional[int] = None,
        ticket_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get recent ticket notes within specified timeframe.

        Args:
            days: Number of days back to search
            note_type: Optional note type filter
            ticket_id: Optional ticket ID filter

        Returns:
            List of recent ticket notes
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        filters = [
            {"field": "CreateDateTime", "op": "gte", "value": cutoff_date.isoformat()}
        ]

        if note_type is not None:
            filters.append({"field": "NoteType", "op": "eq", "value": str(note_type)})

        if ticket_id is not None:
            filters.append({"field": "TicketID", "op": "eq", "value": str(ticket_id)})

        return self.query_all(filters=filters)

    def get_notes_by_creator(
        self,
        creator_resource_id: int,
        days: Optional[int] = None,
        ticket_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get notes created by a specific resource.

        Args:
            creator_resource_id: ID of the creator resource
            days: Optional days filter for recent notes
            ticket_id: Optional ticket ID filter

        Returns:
            List of notes created by the resource
        """
        filters = [
            {
                "field": "CreatorResourceID",
                "op": "eq",
                "value": str(creator_resource_id),
            }
        ]

        if days is not None:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            filters.append(
                {
                    "field": "CreateDateTime",
                    "op": "gte",
                    "value": cutoff_date.isoformat(),
                }
            )

        if ticket_id is not None:
            filters.append({"field": "TicketID", "op": "eq", "value": str(ticket_id)})

        return self.query_all(filters=filters)

    def add_status_change_note(
        self,
        ticket_id: int,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a note documenting a status change.

        Args:
            ticket_id: Ticket ID
            old_status: Previous status
            new_status: New status
            reason: Optional reason for status change

        Returns:
            Created note data
        """
        description = f"Status changed from {old_status} to {new_status}"
        if reason:
            description += f". Reason: {reason}"

        return self.create_note(
            ticket_id=ticket_id,
            description=description,
            title="Status Change",
            note_type=1,  # Activity Log
        )

    def add_escalation_note(
        self,
        ticket_id: int,
        escalation_level: int,
        escalated_by: str,
        reason: str,
    ) -> EntityDict:
        """
        Add a note documenting ticket escalation.

        Args:
            ticket_id: Ticket ID
            escalation_level: New escalation level
            escalated_by: Who escalated the ticket
            reason: Reason for escalation

        Returns:
            Created note data
        """
        description = (
            f"Ticket escalated to level {escalation_level} by {escalated_by}. "
            f"Reason: {reason}"
        )

        return self.create_note(
            ticket_id=ticket_id,
            description=description,
            title="Escalation",
            note_type=1,  # Activity Log
        )

    def add_resolution_note(
        self,
        ticket_id: int,
        resolution_summary: str,
        time_spent: Optional[str] = None,
        follow_up_required: bool = False,
    ) -> EntityDict:
        """
        Add a note documenting ticket resolution.

        Args:
            ticket_id: Ticket ID
            resolution_summary: Summary of the resolution
            time_spent: Optional time spent on resolution
            follow_up_required: Whether follow-up is needed

        Returns:
            Created note data
        """
        description = f"Resolution: {resolution_summary}"

        if time_spent:
            description += f"\nTime spent: {time_spent}"

        if follow_up_required:
            description += "\nFollow-up required: Yes"

        return self.create_note(
            ticket_id=ticket_id,
            description=description,
            title="Resolution",
            note_type=2,  # Detailed Description
            publish=1,  # All - customer can see resolution
        )

    def update_note_visibility(
        self, note_id: int, publish: int
    ) -> Optional[EntityDict]:
        """
        Update a note's visibility/publish setting.

        Args:
            note_id: ID of note to update
            publish: New publish setting (1=All, 2=Internal Only)

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"Publish": publish})

    def search_notes_by_content(
        self,
        search_text: str,
        ticket_id: Optional[int] = None,
        days: Optional[int] = None,
    ) -> EntityList:
        """
        Search notes by content text.

        Args:
            search_text: Text to search for in note descriptions
            ticket_id: Optional ticket ID filter
            days: Optional days filter for recent notes

        Returns:
            List of matching notes
        """
        filters = [{"field": "Description", "op": "contains", "value": search_text}]

        if ticket_id is not None:
            filters.append({"field": "TicketID", "op": "eq", "value": str(ticket_id)})

        if days is not None:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            filters.append(
                {
                    "field": "CreateDateTime",
                    "op": "gte",
                    "value": cutoff_date.isoformat(),
                }
            )

        return self.query_all(filters=filters)

    def get_note_statistics(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get statistics about notes for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with note statistics
        """
        all_notes = self.get_notes_by_ticket(ticket_id)

        stats = {
            "total_notes": len(all_notes),
            "internal_notes": 0,
            "external_notes": 0,
            "activity_logs": 0,
            "detailed_descriptions": 0,
            "unique_creators": set(),
        }

        for note in all_notes:
            # Count by visibility
            if note.get("Publish") == 2:
                stats["internal_notes"] += 1
            else:
                stats["external_notes"] += 1

            # Count by type
            if note.get("NoteType") == 1:
                stats["activity_logs"] += 1
            elif note.get("NoteType") == 2:
                stats["detailed_descriptions"] += 1

            # Track creators
            if note.get("CreatorResourceID"):
                stats["unique_creators"].add(note["CreatorResourceID"])

        # Convert set to count
        stats["unique_creators"] = len(stats["unique_creators"])

        return stats
