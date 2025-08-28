"""
CompanyAttachments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyAttachmentsEntity(BaseEntity):
    """
    Handles all Company Attachment-related operations for the Autotask API.

    Company Attachments in Autotask represent files, documents, and other
    attachments associated with company records.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company_attachment(
        self,
        company_id: int,
        attachment_data: bytes,
        file_name: str,
        content_type: str,
        title: Optional[str] = None,
        attach_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company attachment.

        Args:
            company_id: ID of the company
            attachment_data: Binary data of the attachment
            file_name: Name of the file
            content_type: MIME type of the attachment
            title: Optional title for the attachment
            attach_date: Optional attachment date (ISO format)
            **kwargs: Additional attachment fields

        Returns:
            Created company attachment data
        """
        attachment_data = {
            "ParentID": company_id,
            "ParentType": "Company",
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

    def get_company_attachments(
        self, company_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific company.

        Args:
            company_id: ID of the company
            limit: Maximum number of attachments to return

        Returns:
            List of company attachments
        """
        filters = [QueryFilter(field="ParentID", op="eq", value=company_id)]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_type(
        self,
        company_id: int,
        content_type: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company attachments filtered by content type.

        Args:
            company_id: ID of the company
            content_type: MIME type to filter by (e.g., 'image/jpeg', 'application/pdf')
            limit: Maximum number of attachments to return

        Returns:
            List of attachments matching the criteria
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=company_id),
            QueryFilter(field="ContentType", op="eq", value=content_type),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_title(
        self,
        company_id: int,
        title: str,
        exact_match: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search company attachments by title.

        Args:
            company_id: ID of the company
            title: Title to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of attachments to return

        Returns:
            List of matching attachments
        """
        filters = [QueryFilter(field="ParentID", op="eq", value=company_id)]

        if exact_match:
            filters.append(QueryFilter(field="Title", op="eq", value=title))
        else:
            filters.append(QueryFilter(field="Title", op="contains", value=title))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachment_data(self, attachment_id: int) -> bytes:
        """
        Download the binary data for a specific attachment.

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
        Update the title of a company attachment.

        Args:
            attachment_id: ID of attachment to update
            new_title: New title for the attachment

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"Title": new_title})

    def get_attachments_by_date_range(
        self,
        company_id: int,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company attachments within a specific date range.

        Args:
            company_id: ID of the company
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of attachments to return

        Returns:
            List of attachments within the date range
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=company_id),
            QueryFilter(field="AttachDate", op="gte", value=start_date),
            QueryFilter(field="AttachDate", op="lte", value=end_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_image_attachments(
        self, company_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all image attachments for a company.

        Args:
            company_id: ID of the company
            limit: Maximum number of attachments to return

        Returns:
            List of image attachments
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=company_id),
            QueryFilter(field="ContentType", op="beginsWith", value="image/"),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_document_attachments(
        self, company_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all document attachments for a company.

        Args:
            company_id: ID of the company
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
            QueryFilter(field="ParentID", op="eq", value=company_id),
            QueryFilter(field="ContentType", op="in", value=document_types),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def bulk_delete_attachments(self, attachment_ids: List[int]) -> List[bool]:
        """
        Delete multiple company attachments in bulk.

        Args:
            attachment_ids: List of attachment IDs to delete

        Returns:
            List of success indicators
        """
        return self.batch_delete(attachment_ids)
