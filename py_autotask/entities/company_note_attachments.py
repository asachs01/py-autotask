"""
CompanyNoteAttachments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyNoteAttachmentsEntity(BaseEntity):
    """
    Handles all Company Note Attachment-related operations for the Autotask API.

    Company Note Attachments in Autotask represent files, documents, and other
    attachments associated with company note records.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_note_attachment(
        self,
        note_id: int,
        attachment_data: bytes,
        file_name: str,
        content_type: str,
        title: Optional[str] = None,
        attach_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new attachment for a company note.

        Args:
            note_id: ID of the company note
            attachment_data: Binary data of the attachment
            file_name: Name of the file
            content_type: MIME type of the attachment
            title: Optional title for the attachment
            attach_date: Optional attachment date (ISO format)
            **kwargs: Additional attachment fields

        Returns:
            Created note attachment data
        """
        attachment_data = {
            "NoteID": note_id,
            "Data": attachment_data,
            "FullPath": file_name,
            "ContentType": content_type,
            **kwargs,
        }

        if title:
            attachment_data["Title"] = title
        if attach_date:
            attachment_data["AttachDate"] = attach_date

        return self.create(attachment_data)

    def get_note_attachments(
        self, note_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific company note.

        Args:
            note_id: ID of the company note
            limit: Maximum number of attachments to return

        Returns:
            List of note attachments
        """
        filters = [QueryFilter(field="NoteID", op="eq", value=note_id)]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_company_note_attachments(
        self, company_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all note attachments for a specific company.

        Args:
            company_id: ID of the company
            limit: Maximum number of attachments to return

        Returns:
            List of all note attachments for the company
        """
        # First get all company notes
        notes_response = self.client.query(
            "CompanyNotes",
            filters=[QueryFilter(field="CompanyID", op="eq", value=company_id)],
        )
        company_notes = notes_response.get("items", [])

        if not company_notes:
            return []

        note_ids = [note["id"] for note in company_notes]

        # Get attachments for all these notes
        filters = [QueryFilter(field="NoteID", op="in", value=note_ids)]
        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_type(
        self,
        note_id: int,
        content_type: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get note attachments filtered by content type.

        Args:
            note_id: ID of the company note
            content_type: MIME type to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of attachments matching the criteria
        """
        filters = [
            QueryFilter(field="NoteID", op="eq", value=note_id),
            QueryFilter(field="ContentType", op="eq", value=content_type),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_title(
        self,
        note_id: int,
        title: str,
        exact_match: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search note attachments by title.

        Args:
            note_id: ID of the company note
            title: Title to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of attachments to return

        Returns:
            List of matching attachments
        """
        filters = [QueryFilter(field="NoteID", op="eq", value=note_id)]

        if exact_match:
            filters.append(QueryFilter(field="Title", op="eq", value=title))
        else:
            filters.append(QueryFilter(field="Title", op="contains", value=title))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachment_data(self, attachment_id: int) -> bytes:
        """
        Download the binary data for a specific note attachment.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Binary data of the attachment
        """
        attachment = self.get(attachment_id)
        if not attachment:
            raise ValueError(f"Attachment with ID {attachment_id} not found")

        return attachment.get("Data", b"")

    def update_attachment_title(
        self, attachment_id: int, new_title: str
    ) -> Dict[str, Any]:
        """
        Update the title of a note attachment.

        Args:
            attachment_id: ID of attachment to update
            new_title: New title for the attachment

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"Title": new_title})

    def get_attachments_by_date_range(
        self,
        note_id: int,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get note attachments within a specific date range.

        Args:
            note_id: ID of the company note
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of attachments to return

        Returns:
            List of attachments within the date range
        """
        filters = [
            QueryFilter(field="NoteID", op="eq", value=note_id),
            QueryFilter(field="AttachDate", op="gte", value=start_date),
            QueryFilter(field="AttachDate", op="lte", value=end_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_image_attachments(
        self, note_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all image attachments for a company note.

        Args:
            note_id: ID of the company note
            limit: Maximum number of attachments to return

        Returns:
            List of image attachments
        """
        filters = [
            QueryFilter(field="NoteID", op="eq", value=note_id),
            QueryFilter(field="ContentType", op="beginsWith", value="image/"),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_document_attachments(
        self, note_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all document attachments for a company note.

        Args:
            note_id: ID of the company note
            limit: Maximum number of attachments to return

        Returns:
            List of document attachments
        """
        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain",
        ]

        filters = [
            QueryFilter(field="NoteID", op="eq", value=note_id),
            QueryFilter(field="ContentType", op="in", value=document_types),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def bulk_delete_attachments(self, attachment_ids: List[int]) -> List[bool]:
        """
        Delete multiple note attachments in bulk.

        Args:
            attachment_ids: List of attachment IDs to delete

        Returns:
            List of success indicators
        """
        return self.batch_delete(attachment_ids)
