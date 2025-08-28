"""
CompanyNotes entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyNotesEntity(BaseEntity):
    """
    Handles all Company Note-related operations for the Autotask API.

    Company Notes in Autotask represent textual notes, comments, and
    documentation associated with company records.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company_note(
        self,
        company_id: int,
        note_text: str,
        note_type: Optional[int] = None,
        created_by_resource_id: Optional[int] = None,
        is_published: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company note.

        Args:
            company_id: ID of the company
            note_text: Content of the note
            note_type: Optional note type ID
            created_by_resource_id: ID of resource creating the note
            is_published: Whether the note is published/visible
            **kwargs: Additional note fields

        Returns:
            Created company note data
        """
        note_data = {
            "CompanyID": company_id,
            "Description": note_text,
            "IsPublished": is_published,
            **kwargs,
        }

        if note_type:
            note_data["NoteType"] = note_type
        if created_by_resource_id:
            note_data["CreatedByResourceID"] = created_by_resource_id

        return self.create(note_data)

    def get_company_notes(
        self,
        company_id: int,
        published_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all notes for a specific company.

        Args:
            company_id: ID of the company
            published_only: Whether to return only published notes
            limit: Maximum number of notes to return

        Returns:
            List of company notes
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_notes_by_type(
        self,
        company_id: int,
        note_type: int,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company notes filtered by note type.

        Args:
            company_id: ID of the company
            note_type: Note type to filter by
            limit: Maximum number of notes to return

        Returns:
            List of notes matching the criteria
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="NoteType", op="eq", value=note_type),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def search_notes_by_content(
        self,
        company_id: int,
        search_text: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search company notes by content.

        Args:
            company_id: ID of the company
            search_text: Text to search for in note descriptions
            limit: Maximum number of notes to return

        Returns:
            List of notes containing the search text
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="Description", op="contains", value=search_text),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_notes_by_author(
        self,
        company_id: int,
        resource_id: int,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company notes created by a specific resource.

        Args:
            company_id: ID of the company
            resource_id: ID of the resource who created the notes
            limit: Maximum number of notes to return

        Returns:
            List of notes created by the specified resource
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="CreatedByResourceID", op="eq", value=resource_id),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_notes_by_date_range(
        self,
        company_id: int,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company notes within a specific date range.

        Args:
            company_id: ID of the company
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of notes to return

        Returns:
            List of notes within the date range
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="CreateDateTime", op="gte", value=start_date),
            QueryFilter(field="CreateDateTime", op="lte", value=end_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_note_content(self, note_id: int, new_content: str) -> Dict[str, Any]:
        """
        Update the content of a company note.

        Args:
            note_id: ID of note to update
            new_content: New note content

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"Description": new_content})

    def publish_note(self, note_id: int) -> Dict[str, Any]:
        """
        Publish a company note (make it visible).

        Args:
            note_id: ID of note to publish

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"IsPublished": True})

    def unpublish_note(self, note_id: int) -> Dict[str, Any]:
        """
        Unpublish a company note (hide it).

        Args:
            note_id: ID of note to unpublish

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"IsPublished": False})

    def get_recent_notes(
        self,
        company_id: int,
        days: int = 30,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent company notes from the last N days.

        Args:
            company_id: ID of the company
            days: Number of days to look back
            limit: Maximum number of notes to return

        Returns:
            List of recent notes
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="CreateDateTime", op="gte", value=cutoff_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_note_with_attachments(self, note_id: int) -> Dict[str, Any]:
        """
        Get a company note along with its attachments.

        Args:
            note_id: ID of the note

        Returns:
            Note data with attachments included
        """
        note = self.get(note_id)
        if not note:
            raise ValueError(f"Note with ID {note_id} not found")

        # Get attachments for this note
        attachments_response = self.client.query(
            "CompanyNoteAttachments",
            filters=[QueryFilter(field="NoteID", op="eq", value=note_id)],
        )

        note["attachments"] = attachments_response.get("items", [])
        return note

    def bulk_update_note_types(
        self, note_ids: List[int], new_note_type: int
    ) -> List[Dict[str, Any]]:
        """
        Update the note type for multiple company notes in bulk.

        Args:
            note_ids: List of note IDs to update
            new_note_type: New note type ID

        Returns:
            List of updated note data
        """
        update_data = [
            {"id": note_id, "NoteType": new_note_type} for note_id in note_ids
        ]
        return self.batch_update(update_data)
