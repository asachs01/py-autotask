"""
Ticket Attachments entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketAttachmentsEntity(BaseEntity):
    """
    Handles Ticket Attachments operations for the Autotask API.

    Manages file attachments associated with tickets, including document uploads,
    images, and other file types that support ticket resolution.
    """

    def __init__(self, client, entity_name: str = "TicketAttachments"):
        super().__init__(client, entity_name)

    def add_attachment_to_ticket(
        self,
        ticket_id: int,
        attachment_info: Dict[str, Any],
        **kwargs,
    ) -> EntityDict:
        """
        Add an attachment to a ticket.

        Args:
            ticket_id: ID of the ticket
            attachment_info: Dictionary containing attachment details
                - Title: Attachment title/name
                - Data: Base64 encoded file content
                - FileSize: Size of file in bytes
                - FullFileName: Full file name with extension
            **kwargs: Additional fields

        Returns:
            Created ticket attachment data
        """
        attachment_data = {
            "ParentID": ticket_id,
            "ParentType": "Ticket",
            **attachment_info,
            **kwargs,
        }

        return self.create(attachment_data)

    def get_attachments_by_ticket(self, ticket_id: int) -> EntityList:
        """
        Get all attachments for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by

        Returns:
            List of attachments for the ticket
        """
        filters = [
            {"field": "ParentID", "op": "eq", "value": str(ticket_id)},
            {"field": "ParentType", "op": "eq", "value": "Ticket"},
        ]
        return self.query_all(filters=filters)

    def get_attachment_details(self, attachment_id: int) -> Optional[EntityDict]:
        """
        Get detailed information about a specific attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment details or None if not found
        """
        return self.get(attachment_id)

    def remove_attachment_from_ticket(self, attachment_id: int) -> bool:
        """
        Remove an attachment from a ticket.

        Args:
            attachment_id: Attachment ID to remove

        Returns:
            True if removal was successful
        """
        return self.delete(attachment_id)

    def update_attachment_metadata(
        self,
        attachment_id: int,
        metadata_updates: Dict[str, Any],
    ) -> Optional[EntityDict]:
        """
        Update attachment metadata (title, description, etc.).

        Args:
            attachment_id: Attachment ID
            metadata_updates: Dictionary of metadata updates

        Returns:
            Updated attachment record or None if failed
        """
        update_data = {"id": attachment_id, **metadata_updates}
        return self.update(update_data)

    def get_attachments_by_type(
        self,
        ticket_id: int,
        file_extension: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> EntityList:
        """
        Get attachments filtered by file type for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            file_extension: Filter by file extension (e.g., 'pdf', 'jpg')
            mime_type: Filter by MIME type (e.g., 'image/jpeg')

        Returns:
            List of filtered attachments
        """
        attachments = self.get_attachments_by_ticket(ticket_id)

        filtered_attachments = []
        for attachment in attachments:
            include_attachment = True

            if file_extension and "FullFileName" in attachment:
                filename = attachment["FullFileName"].lower()
                if not filename.endswith(f".{file_extension.lower()}"):
                    include_attachment = False

            if mime_type and "ContentType" in attachment:
                if attachment["ContentType"] != mime_type:
                    include_attachment = False

            if include_attachment:
                filtered_attachments.append(attachment)

        return filtered_attachments

    def get_ticket_attachment_summary(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get a summary of all attachments for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with attachment summary statistics
        """
        attachments = self.get_attachments_by_ticket(ticket_id)

        total_size = 0
        file_types = {}

        for attachment in attachments:
            # Calculate total file size
            if "FileSize" in attachment and attachment["FileSize"]:
                total_size += int(attachment["FileSize"])

            # Count file types
            if "FullFileName" in attachment:
                filename = attachment["FullFileName"]
                extension = (
                    filename.split(".")[-1].lower() if "." in filename else "unknown"
                )
                file_types[extension] = file_types.get(extension, 0) + 1

        return {
            "ticket_id": ticket_id,
            "total_attachments": len(attachments),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "attachments": attachments,
        }

    def bulk_remove_attachments(
        self,
        attachment_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Remove multiple attachments in bulk.

        Args:
            attachment_ids: List of attachment IDs to remove

        Returns:
            Dictionary with removal results
        """
        results = {
            "successful": [],
            "failed": [],
            "errors": [],
        }

        for attachment_id in attachment_ids:
            try:
                success = self.remove_attachment_from_ticket(attachment_id)
                if success:
                    results["successful"].append(attachment_id)
                else:
                    results["failed"].append(attachment_id)
            except Exception as e:
                results["failed"].append(attachment_id)
                results["errors"].append(
                    {
                        "attachment_id": attachment_id,
                        "error": str(e),
                    }
                )
                self.logger.error(f"Failed to remove attachment {attachment_id}: {e}")

        return results

    def search_attachments_by_filename(
        self,
        ticket_id: int,
        filename_pattern: str,
        case_sensitive: bool = False,
    ) -> EntityList:
        """
        Search attachments by filename pattern.

        Args:
            ticket_id: Ticket ID to search within
            filename_pattern: Pattern to search for in filenames
            case_sensitive: Whether search should be case sensitive

        Returns:
            List of matching attachments
        """
        attachments = self.get_attachments_by_ticket(ticket_id)

        matching_attachments = []
        for attachment in attachments:
            if "FullFileName" in attachment:
                filename = attachment["FullFileName"]
                search_filename = filename if case_sensitive else filename.lower()
                search_pattern = (
                    filename_pattern if case_sensitive else filename_pattern.lower()
                )

                if search_pattern in search_filename:
                    matching_attachments.append(attachment)

        return matching_attachments

    def get_recent_attachments(
        self,
        ticket_id: int,
        hours: int = 24,
    ) -> EntityList:
        """
        Get attachments added to a ticket within the specified time period.

        Args:
            ticket_id: Ticket ID
            hours: Number of hours to look back

        Returns:
            List of recent attachments
        """
        attachments = self.get_attachments_by_ticket(ticket_id)
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_attachments = []
        for attachment in attachments:
            if "CreateDateTime" in attachment:
                try:
                    create_time = datetime.fromisoformat(
                        attachment["CreateDateTime"].replace("Z", "+00:00")
                    )
                    if create_time >= cutoff_time:
                        recent_attachments.append(attachment)
                except ValueError:
                    # Skip if date parsing fails
                    continue

        return recent_attachments

    def validate_attachment(
        self,
        attachment_info: Dict[str, Any],
        max_file_size_mb: int = 25,
        allowed_extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate attachment before upload.

        Args:
            attachment_info: Attachment information to validate
            max_file_size_mb: Maximum allowed file size in MB
            allowed_extensions: List of allowed file extensions

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Check file size
        if "FileSize" in attachment_info:
            file_size_mb = int(attachment_info["FileSize"]) / (1024 * 1024)
            if file_size_mb > max_file_size_mb:
                result["valid"] = False
                result["errors"].append(
                    f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed ({max_file_size_mb} MB)"
                )

        # Check file extension
        if allowed_extensions and "FullFileName" in attachment_info:
            filename = attachment_info["FullFileName"]
            extension = filename.split(".")[-1].lower() if "." in filename else ""
            if extension not in [ext.lower() for ext in allowed_extensions]:
                result["valid"] = False
                result["errors"].append(
                    f"File extension '.{extension}' is not allowed. "
                    f"Allowed extensions: {', '.join(allowed_extensions)}"
                )

        # Check required fields
        required_fields = ["Title", "FullFileName"]
        for field in required_fields:
            if field not in attachment_info or not attachment_info[field]:
                result["valid"] = False
                result["errors"].append(f"Required field '{field}' is missing or empty")

        return result

    def get_attachment_download_info(
        self, attachment_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get information needed to download an attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            Dictionary with download information or None if not found
        """
        attachment = self.get_attachment_details(attachment_id)

        if not attachment:
            return None

        return {
            "attachment_id": attachment_id,
            "filename": attachment.get("FullFileName"),
            "file_size": attachment.get("FileSize"),
            "content_type": attachment.get("ContentType"),
            "title": attachment.get("Title"),
            "create_date": attachment.get("CreateDateTime"),
            "created_by": attachment.get("CreatedByResourceID"),
        }
