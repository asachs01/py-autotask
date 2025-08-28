"""
Configuration Item Note Attachments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemNoteAttachmentsEntity(BaseEntity):
    """
    Handles all Configuration Item Note Attachment-related operations for the Autotask API.

    Configuration Item Note Attachments represent files and documents that are attached
    to configuration item notes for additional documentation and reference purposes.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_note_attachment(
        self,
        note_id: int,
        attachment_info_id: int,
        title: str,
        attachment_type: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item note attachment.

        Args:
            note_id: ID of the configuration item note
            attachment_info_id: ID of the attachment info record
            title: Title of the attachment
            attachment_type: Optional attachment type ID
            **kwargs: Additional attachment fields

        Returns:
            Created note attachment data
        """
        attachment_data = {
            "ParentID": note_id,
            "AttachmentInfoID": attachment_info_id,
            "Title": title,
            **kwargs,
        }

        if attachment_type:
            attachment_data["Type"] = attachment_type

        return self.create(attachment_data)

    def get_note_attachments(
        self,
        note_id: int,
        attachment_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific configuration item note.

        Args:
            note_id: ID of the configuration item note
            attachment_type: Optional filter by attachment type
            limit: Maximum number of attachments to return

        Returns:
            List of note attachments
        """
        filters = [QueryFilter(field="ParentID", op="eq", value=note_id)]

        if attachment_type:
            filters.append(QueryFilter(field="Type", op="eq", value=attachment_type))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_ci_note(
        self,
        configuration_item_id: int,
        attachment_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for notes belonging to a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            attachment_type: Optional filter by attachment type
            limit: Maximum number of attachments to return

        Returns:
            List of attachments from CI notes
        """
        # First get all notes for the CI
        ci_notes_response = self.client.query(
            "ConfigurationItemNotes",
            filters=[
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            ],
        )
        ci_notes = ci_notes_response.get("items", [])

        if not ci_notes:
            return []

        # Get attachments for all these notes
        all_attachments = []
        for note in ci_notes:
            note_id = note.get("id")
            if note_id:
                note_attachments = self.get_note_attachments(note_id, attachment_type)
                # Add note context to each attachment
                for attachment in note_attachments:
                    attachment["note_context"] = {
                        "note_id": note_id,
                        "note_title": note.get("Title"),
                        "configuration_item_id": configuration_item_id,
                    }
                all_attachments.extend(note_attachments)

        if limit and len(all_attachments) > limit:
            all_attachments = all_attachments[:limit]

        return all_attachments

    def search_attachments_by_title(
        self,
        search_text: str,
        note_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search configuration item note attachments by title.

        Args:
            search_text: Text to search for in attachment titles
            note_id: Optional filter by specific note
            limit: Maximum number of attachments to return

        Returns:
            List of attachments containing the search text
        """
        filters = [QueryFilter(field="Title", op="contains", value=search_text)]

        if note_id:
            filters.append(QueryFilter(field="ParentID", op="eq", value=note_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachments_by_date_range(
        self,
        start_date: str,
        end_date: str,
        note_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration item note attachments within a specific date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            note_id: Optional filter by specific note
            limit: Maximum number of attachments to return

        Returns:
            List of attachments within the date range
        """
        filters = [
            QueryFilter(field="AttachDate", op="gte", value=start_date),
            QueryFilter(field="AttachDate", op="lte", value=end_date),
        ]

        if note_id:
            filters.append(QueryFilter(field="ParentID", op="eq", value=note_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_attachment_title(
        self, attachment_id: int, new_title: str
    ) -> Dict[str, Any]:
        """
        Update the title of a note attachment.

        Args:
            attachment_id: ID of attachment to update
            new_title: New attachment title

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"Title": new_title})

    def get_recent_attachments(
        self,
        days: int = 30,
        note_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent configuration item note attachments from the last N days.

        Args:
            days: Number of days to look back
            note_id: Optional filter by specific note
            limit: Maximum number of attachments to return

        Returns:
            List of recent attachments
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        filters = [QueryFilter(field="AttachDate", op="gte", value=cutoff_date)]

        if note_id:
            filters.append(QueryFilter(field="ParentID", op="eq", value=note_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_attachment_with_info(self, attachment_id: int) -> Dict[str, Any]:
        """
        Get a note attachment along with its attachment info and note details.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Attachment data with extended information
        """
        attachment = self.get(attachment_id)
        if not attachment:
            raise ValueError(f"Attachment with ID {attachment_id} not found")

        # Get attachment info details
        attachment_info_id = attachment.get("AttachmentInfoID")
        if attachment_info_id:
            attachment_info = self.client.get("AttachmentInfo", attachment_info_id)
            attachment["attachment_info"] = attachment_info

        # Get note details
        note_id = attachment.get("ParentID")
        if note_id:
            note = self.client.get("ConfigurationItemNotes", note_id)
            if note:
                attachment["note_details"] = note
                # Also get the CI details
                ci_id = note.get("ConfigurationItemID")
                if ci_id:
                    ci = self.client.get("ConfigurationItems", ci_id)
                    attachment["configuration_item_details"] = ci

        return attachment

    def get_note_attachments_summary(self, note_id: int) -> Dict[str, Any]:
        """
        Get a summary of attachments for a configuration item note.

        Args:
            note_id: ID of the configuration item note

        Returns:
            Dictionary with attachment statistics
        """
        attachments = self.get_note_attachments(note_id)

        summary = {
            "note_id": note_id,
            "total_attachments": len(attachments),
            "by_type": {},
            "total_size": 0,
            "recent_count": 0,
            "oldest_attachment": None,
            "newest_attachment": None,
        }

        if not attachments:
            return summary

        from datetime import datetime, timedelta

        week_ago = datetime.now() - timedelta(days=7)
        oldest_date = None
        newest_date = None

        for attachment in attachments:
            # Count by type
            attachment_type = attachment.get("Type", "Unknown")
            summary["by_type"][attachment_type] = (
                summary["by_type"].get(attachment_type, 0) + 1
            )

            # Count recent attachments and track dates
            attach_date_str = attachment.get("AttachDate")
            if attach_date_str:
                try:
                    attach_date = datetime.fromisoformat(
                        attach_date_str.replace("Z", "+00:00")
                    )

                    if attach_date > week_ago:
                        summary["recent_count"] += 1

                    # Track oldest and newest
                    if oldest_date is None or attach_date < oldest_date:
                        oldest_date = attach_date
                        summary["oldest_attachment"] = {
                            "id": attachment.get("id"),
                            "title": attachment.get("Title"),
                            "date": attach_date_str,
                        }

                    if newest_date is None or attach_date > newest_date:
                        newest_date = attach_date
                        summary["newest_attachment"] = {
                            "id": attachment.get("id"),
                            "title": attachment.get("Title"),
                            "date": attach_date_str,
                        }

                except ValueError:
                    pass

            # Add to total size if available
            file_size = attachment.get("FileSize")
            if file_size:
                try:
                    summary["total_size"] += int(file_size)
                except (ValueError, TypeError):
                    pass

        return summary

    def move_attachments_between_notes(
        self,
        source_note_id: int,
        target_note_id: int,
        attachment_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Move attachments from one note to another.

        Args:
            source_note_id: ID of the source note
            target_note_id: ID of the target note
            attachment_ids: Optional list of specific attachment IDs to move (all if None)

        Returns:
            List of moved attachments
        """
        if attachment_ids:
            # Move specific attachments
            attachments_to_move = []
            for attachment_id in attachment_ids:
                attachment = self.get(attachment_id)
                if attachment and attachment.get("ParentID") == source_note_id:
                    attachments_to_move.append(attachment)
        else:
            # Move all attachments from source note
            attachments_to_move = self.get_note_attachments(source_note_id)

        moved_attachments = []
        for attachment in attachments_to_move:
            attachment_id = attachment.get("id")
            if attachment_id:
                try:
                    updated_attachment = self.update_by_id(
                        attachment_id, {"ParentID": target_note_id}
                    )
                    moved_attachments.append(updated_attachment)
                except Exception as e:
                    # Log error but continue with other attachments
                    self.client.logger.error(
                        f"Failed to move attachment {attachment_id}: {e}"
                    )

        return moved_attachments

    def bulk_update_attachment_type(
        self, attachment_ids: List[int], new_type: int
    ) -> List[Dict[str, Any]]:
        """
        Update the attachment type for multiple note attachments in bulk.

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
