"""
Configuration Item Attachments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemAttachmentsEntity(BaseEntity):
    """
    Handles all Configuration Item Attachment-related operations for the Autotask API.

    Configuration Item Attachments represent files and documents associated with
    configuration items in Autotask for documentation and reference purposes.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ci_attachment(
        self,
        configuration_item_id: int,
        attachment_info_id: int,
        title: str,
        attachment_type: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item attachment.

        Args:
            configuration_item_id: ID of the configuration item
            attachment_info_id: ID of the attachment info record
            title: Title of the attachment
            attachment_type: Optional attachment type ID
            **kwargs: Additional attachment fields

        Returns:
            Created configuration item attachment data
        """
        attachment_data = {
            "ParentID": configuration_item_id,
            "AttachmentInfoID": attachment_info_id,
            "Title": title,
            **kwargs,
        }

        if attachment_type:
            attachment_data["Type"] = attachment_type

        return self.create(attachment_data)

    def get_ci_attachments(
        self,
        configuration_item_id: int,
        attachment_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            attachment_type: Optional filter by attachment type
            limit: Maximum number of attachments to return

        Returns:
            List of configuration item attachments
        """
        filters = [QueryFilter(field="ParentID", op="eq", value=configuration_item_id)]

        if attachment_type:
            filters.append(QueryFilter(field="Type", op="eq", value=attachment_type))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_type(
        self,
        configuration_item_id: int,
        attachment_type: int,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration item attachments filtered by attachment type.

        Args:
            configuration_item_id: ID of the configuration item
            attachment_type: Attachment type to filter by
            limit: Maximum number of attachments to return

        Returns:
            List of attachments matching the criteria
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=configuration_item_id),
            QueryFilter(field="Type", op="eq", value=attachment_type),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def search_attachments_by_title(
        self,
        configuration_item_id: int,
        search_text: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search configuration item attachments by title.

        Args:
            configuration_item_id: ID of the configuration item
            search_text: Text to search for in attachment titles
            limit: Maximum number of attachments to return

        Returns:
            List of attachments containing the search text
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=configuration_item_id),
            QueryFilter(field="Title", op="contains", value=search_text),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_date_range(
        self,
        configuration_item_id: int,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration item attachments within a specific date range.

        Args:
            configuration_item_id: ID of the configuration item
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of attachments to return

        Returns:
            List of attachments within the date range
        """
        filters = [
            QueryFilter(field="ParentID", op="eq", value=configuration_item_id),
            QueryFilter(field="AttachDate", op="gte", value=start_date),
            QueryFilter(field="AttachDate", op="lte", value=end_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_attachment_title(
        self, attachment_id: int, new_title: str
    ) -> Dict[str, Any]:
        """
        Update the title of a configuration item attachment.

        Args:
            attachment_id: ID of attachment to update
            new_title: New attachment title

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"Title": new_title})

    def get_recent_attachments(
        self,
        configuration_item_id: int,
        days: int = 30,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent configuration item attachments from the last N days.

        Args:
            configuration_item_id: ID of the configuration item
            days: Number of days to look back
            limit: Maximum number of attachments to return

        Returns:
            List of recent attachments
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        filters = [
            QueryFilter(field="ParentID", op="eq", value=configuration_item_id),
            QueryFilter(field="AttachDate", op="gte", value=cutoff_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachment_with_info(self, attachment_id: int) -> Dict[str, Any]:
        """
        Get a configuration item attachment along with its attachment info details.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Attachment data with info details included
        """
        attachment = self.get(attachment_id)
        if not attachment:
            raise ValueError(f"Attachment with ID {attachment_id} not found")

        # Get attachment info details
        attachment_info_id = attachment.get("AttachmentInfoID")
        if attachment_info_id:
            attachment_info = self.client.get("AttachmentInfo", attachment_info_id)
            attachment["attachment_info"] = attachment_info

        return attachment

    def get_attachments_summary(self, configuration_item_id: int) -> Dict[str, Any]:
        """
        Get a summary of attachments for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item

        Returns:
            Dictionary with attachment statistics
        """
        attachments = self.get_ci_attachments(configuration_item_id)

        summary = {
            "total_attachments": len(attachments),
            "by_type": {},
            "total_size": 0,
            "recent_count": 0,
        }

        from datetime import datetime, timedelta

        week_ago = datetime.now() - timedelta(days=7)

        for attachment in attachments:
            # Count by type
            attachment_type = attachment.get("Type", "Unknown")
            summary["by_type"][attachment_type] = (
                summary["by_type"].get(attachment_type, 0) + 1
            )

            # Count recent attachments
            attach_date = attachment.get("AttachDate")
            if attach_date:
                try:
                    attach_dt = datetime.fromisoformat(
                        attach_date.replace("Z", "+00:00")
                    )
                    if attach_dt > week_ago:
                        summary["recent_count"] += 1
                except ValueError:
                    pass

            # Add to total size if available
            file_size = attachment.get("FileSize")
            if file_size:
                summary["total_size"] += int(file_size)

        return summary

    def bulk_update_attachment_type(
        self, attachment_ids: List[int], new_type: int
    ) -> List[Dict[str, Any]]:
        """
        Update the attachment type for multiple configuration item attachments in bulk.

        Args:
            attachment_ids: List of attachment IDs to update
            new_type: New attachment type ID

        Returns:
            List of updated attachment data
        """
        update_data = [
            {"id": attachment_id, "Type": new_type} for attachment_id in attachment_ids
        ]
        return self.batch_update(update_data)
