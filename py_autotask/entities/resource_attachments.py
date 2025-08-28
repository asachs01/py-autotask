"""
ResourceAttachments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ResourceAttachmentsEntity(BaseEntity):
    """
    Handles all Resource Attachment-related operations for the Autotask API.

    ResourceAttachments in Autotask represent file attachments associated with
    resources (employees, contractors, etc.), such as contracts, certifications,
    ID documents, or other resource-related files.
    """

    def __init__(self, client, entity_name="ResourceAttachments"):
        super().__init__(client, entity_name)

    def get_attachments_for_resource(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of attachments to return

        Returns:
            List of resource attachments

        Example:
            attachments = client.resource_attachments.get_attachments_for_resource(123)
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]
        return self.query(filters=filters, max_records=limit)

    def get_attachments_by_type(
        self,
        attachment_type: str,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get attachments filtered by attachment type.

        Args:
            attachment_type: Type of attachment (e.g., 'Contract', 'Certificate', 'ID')
            resource_id: Optional resource ID to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of filtered attachments
        """
        filters = [QueryFilter(field="Type", op="eq", value=attachment_type)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def search_attachments_by_title(
        self,
        title: str,
        exact_match: bool = False,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for resource attachments by title.

        Args:
            title: Title to search for
            exact_match: Whether to do exact match or partial match
            resource_id: Optional resource ID to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of matching attachments
        """
        op = "eq" if exact_match else "contains"
        filters = [QueryFilter(field="Title", op=op, value=title)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def get_recent_attachments(
        self,
        days: int = 30,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recently created or modified resource attachments.

        Args:
            days: Number of days back to look
            resource_id: Optional resource ID to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of recent attachments
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filters = [QueryFilter(field="CreateDate", op="gte", value=cutoff_date)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def get_attachments_by_file_type(
        self,
        file_extension: str,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get attachments filtered by file extension.

        Args:
            file_extension: File extension to filter by (e.g., 'pdf', 'docx')
            resource_id: Optional resource ID to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of filtered attachments
        """
        # Remove leading dot if present
        if file_extension.startswith("."):
            file_extension = file_extension[1:]

        filters = [QueryFilter(field="FileExtension", op="eq", value=file_extension)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def get_large_attachments(
        self,
        min_size_mb: float = 5.0,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get attachments larger than specified size.

        Args:
            min_size_mb: Minimum size in megabytes
            resource_id: Optional resource ID to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of large attachments
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        filters = [QueryFilter(field="FileSize", op="gte", value=min_size_bytes)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def get_expiring_documents(
        self,
        days_ahead: int = 30,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get resource attachments with expiration dates within specified period.

        Args:
            days_ahead: Number of days ahead to check for expirations
            resource_id: Optional resource ID to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of expiring attachments
        """
        from datetime import datetime, timedelta

        expiry_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        filters = [
            QueryFilter(field="ExpirationDate", op="isNotNull", value=None),
            QueryFilter(field="ExpirationDate", op="lte", value=expiry_date),
        ]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def create_attachment_record(
        self,
        resource_id: int,
        title: str,
        file_name: str,
        file_size: int,
        attachment_type: Optional[str] = None,
        description: Optional[str] = None,
        expiration_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new resource attachment record.

        Args:
            resource_id: ID of the resource
            title: Title of the attachment
            file_name: Name of the file
            file_size: Size of the file in bytes
            attachment_type: Type of attachment
            description: Optional description
            expiration_date: Optional expiration date (YYYY-MM-DD)

        Returns:
            Created attachment record

        Example:
            attachment = client.resource_attachments.create_attachment_record(
                resource_id=123,
                title="Employment Contract",
                file_name="contract.pdf",
                file_size=1024000,
                attachment_type="Contract",
                description="Signed employment contract",
                expiration_date="2025-12-31"
            )
        """
        data = {
            "ResourceID": resource_id,
            "Title": title,
            "FileName": file_name,
            "FileSize": file_size,
        }

        if attachment_type:
            data["Type"] = attachment_type

        if description:
            data["Description"] = description

        if expiration_date:
            data["ExpirationDate"] = expiration_date

        return self.create(data)

    def bulk_update_attachment_types(
        self, attachment_ids: List[int], new_type: str
    ) -> List[Dict[str, Any]]:
        """
        Update the type for multiple resource attachments.

        Args:
            attachment_ids: List of attachment IDs to update
            new_type: New attachment type to set

        Returns:
            List of updated attachment records
        """
        updated_records = []

        for attachment_id in attachment_ids:
            try:
                data = {"Type": new_type}
                updated = self.update(attachment_id, data)
                updated_records.append(updated)
            except Exception as e:
                self.logger.warning(f"Failed to update attachment {attachment_id}: {e}")

        return updated_records

    def get_attachment_statistics(
        self, resource_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about resource attachments.

        Args:
            resource_id: Optional resource ID to get stats for specific resource

        Returns:
            Dictionary with attachment statistics
        """
        filters = []
        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        all_attachments = self.query(filters=filters)

        if not all_attachments:
            return {
                "total_count": 0,
                "total_size": 0,
                "by_type": {},
                "by_extension": {},
                "average_size": 0,
            }

        total_size = sum(att.get("FileSize", 0) for att in all_attachments)
        by_type = {}
        by_extension = {}

        for attachment in all_attachments:
            # Count by type
            att_type = attachment.get("Type", "Unknown")
            by_type[att_type] = by_type.get(att_type, 0) + 1

            # Count by extension
            file_name = attachment.get("FileName", "")
            if "." in file_name:
                ext = file_name.split(".")[-1].lower()
                by_extension[ext] = by_extension.get(ext, 0) + 1

        return {
            "total_count": len(all_attachments),
            "total_size": total_size,
            "by_type": by_type,
            "by_extension": by_extension,
            "average_size": total_size / len(all_attachments) if all_attachments else 0,
        }
