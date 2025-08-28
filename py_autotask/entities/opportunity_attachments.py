"""
OpportunityAttachments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class OpportunityAttachmentsEntity(BaseEntity):
    """
    Handles all Opportunity Attachment-related operations for the Autotask API.

    Opportunity Attachments are files or documents attached to opportunity records.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_opportunity_attachment(
        self,
        opportunity_id: int,
        title: str,
        file_path: str,
        description: Optional[str] = None,
        is_public: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new opportunity attachment.

        Args:
            opportunity_id: ID of the opportunity
            title: Title of the attachment
            file_path: Path to the file to attach
            description: Description of the attachment
            is_public: Whether the attachment is publicly viewable
            **kwargs: Additional attachment fields

        Returns:
            Created attachment data
        """
        attachment_data = {
            "ParentID": opportunity_id,
            "ParentType": "Opportunity",
            "Title": title,
            "FilePath": file_path,
            "IsPublic": is_public,
            **kwargs,
        }

        if description:
            attachment_data["Description"] = description

        return self.create(attachment_data)

    def get_attachments_by_opportunity(
        self,
        opportunity_id: int,
        public_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all attachments for a specific opportunity.

        Args:
            opportunity_id: ID of the opportunity
            public_only: Whether to return only public attachments
            limit: Maximum number of records to return

        Returns:
            List of attachments for the opportunity
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=opportunity_id),
            QueryFilter(field="ParentType", op="eq", value="Opportunity"),
        ]

        if public_only:
            filters.append(QueryFilter(field="IsPublic", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def search_attachments_by_title(
        self, title: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for attachments by title.

        Args:
            title: Title to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching attachments
        """
        if exact_match:
            filters = [QueryFilter(field="Title", op="eq", value=title)]
        else:
            filters = [QueryFilter(field="Title", op="contains", value=title)]

        # Ensure we only get opportunity attachments
        filters.append(QueryFilter(field="ParentType", op="eq", value="Opportunity"))

        return self.query(filters=filters, max_records=limit)

    def get_attachments_by_file_type(
        self, file_extension: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get attachments by file type/extension.

        Args:
            file_extension: File extension to filter by (e.g., 'pdf', 'docx')
            limit: Maximum number of records to return

        Returns:
            List of attachments with the specified file type
        """
        filters = [
            QueryFilter(field="FilePath", op="contains", value=f".{file_extension}"),
            QueryFilter(field="ParentType", op="eq", value="Opportunity"),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_public_attachments(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all public opportunity attachments.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of public attachments
        """
        filters = [
            QueryFilter(field="IsPublic", op="eq", value=True),
            QueryFilter(field="ParentType", op="eq", value="Opportunity"),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_recent_attachments(
        self, days: int = 30, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get recently added opportunity attachments.

        Args:
            days: Number of days to look back
            limit: Maximum number of records to return

        Returns:
            List of recent attachments
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        filters = [
            QueryFilter(field="CreateDate", op="ge", value=start_date),
            QueryFilter(field="ParentType", op="eq", value="Opportunity"),
        ]

        return self.query(filters=filters, max_records=limit)

    def update_attachment_visibility(
        self, attachment_id: int, is_public: bool
    ) -> EntityDict:
        """
        Update the public visibility of an attachment.

        Args:
            attachment_id: ID of the attachment
            is_public: Whether to make the attachment public

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"IsPublic": is_public})

    def update_attachment_description(
        self, attachment_id: int, description: str
    ) -> EntityDict:
        """
        Update the description of an attachment.

        Args:
            attachment_id: ID of the attachment
            description: New description

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"Description": description})

    def get_attachment_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about opportunity attachments.

        Returns:
            Dictionary containing attachment statistics
        """
        filters = [QueryFilter(field="ParentType", op="eq", value="Opportunity")]
        all_attachments = self.query(filters=filters)

        # Count file types
        file_types = {}
        for attachment in all_attachments:
            file_path = attachment.get("FilePath", "")
            if "." in file_path:
                extension = file_path.split(".")[-1].lower()
                file_types[extension] = file_types.get(extension, 0) + 1

        stats = {
            "total_attachments": len(all_attachments),
            "public_attachments": len(
                [att for att in all_attachments if att.get("IsPublic", False)]
            ),
            "private_attachments": len(
                [att for att in all_attachments if not att.get("IsPublic", False)]
            ),
            "attachments_with_description": len(
                [att for att in all_attachments if att.get("Description")]
            ),
            "file_types": file_types,
        }

        return stats

    def get_large_attachments(
        self, min_size_mb: float = 5.0, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get attachments larger than a specified size.

        Args:
            min_size_mb: Minimum file size in megabytes
            limit: Maximum number of records to return

        Returns:
            List of large attachments
        """
        # Note: This assumes file size is stored in bytes in a FileSize field
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        filters = [
            QueryFilter(field="FileSize", op="ge", value=min_size_bytes),
            QueryFilter(field="ParentType", op="eq", value="Opportunity"),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_opportunity_attachment_summary(self, opportunity_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of attachments for an opportunity.

        Args:
            opportunity_id: ID of the opportunity

        Returns:
            Dictionary with attachment summary
        """
        attachments = self.get_attachments_by_opportunity(opportunity_id)

        # Analyze file types
        file_types = {}
        total_size = 0
        for attachment in attachments:
            # File type analysis
            file_path = attachment.get("FilePath", "")
            if "." in file_path:
                extension = file_path.split(".")[-1].lower()
                file_types[extension] = file_types.get(extension, 0) + 1

            # Size calculation (if available)
            file_size = attachment.get("FileSize", 0)
            if file_size:
                total_size += file_size

        summary = {
            "opportunity_id": opportunity_id,
            "total_attachments": len(attachments),
            "public_attachments": len(
                [att for att in attachments if att.get("IsPublic", False)]
            ),
            "private_attachments": len(
                [att for att in attachments if not att.get("IsPublic", False)]
            ),
            "file_types": file_types,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
            "attachments_with_description": len(
                [att for att in attachments if att.get("Description")]
            ),
        }

        return summary
