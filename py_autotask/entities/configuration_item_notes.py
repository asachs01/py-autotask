"""
Configuration Item Notes entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemNotesEntity(BaseEntity):
    """
    Handles all Configuration Item Note-related operations for the Autotask API.

    Configuration Item Notes represent textual notes, comments, and documentation
    associated with configuration item records for tracking changes, maintenance, and history.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ci_note(
        self,
        configuration_item_id: int,
        note_text: str,
        title: Optional[str] = None,
        note_type: Optional[int] = None,
        created_by_resource_id: Optional[int] = None,
        is_published: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item note.

        Args:
            configuration_item_id: ID of the configuration item
            note_text: Content of the note
            title: Optional title for the note
            note_type: Optional note type ID
            created_by_resource_id: ID of resource creating the note
            is_published: Whether the note is published/visible
            **kwargs: Additional note fields

        Returns:
            Created configuration item note data
        """
        note_data = {
            "ConfigurationItemID": configuration_item_id,
            "Description": note_text,
            "IsPublished": is_published,
            **kwargs,
        }

        if title:
            note_data["Title"] = title

        if note_type:
            note_data["NoteType"] = note_type

        if created_by_resource_id:
            note_data["CreatedByResourceID"] = created_by_resource_id

        return self.create(note_data)

    def get_ci_notes(
        self,
        configuration_item_id: int,
        published_only: bool = True,
        note_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all notes for a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            published_only: Whether to return only published notes
            note_type: Optional filter by note type
            limit: Maximum number of notes to return

        Returns:
            List of configuration item notes
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            )
        ]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        if note_type:
            filters.append(QueryFilter(field="NoteType", op="eq", value=note_type))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_notes_by_type(
        self,
        configuration_item_id: int,
        note_type: int,
        published_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration item notes filtered by note type.

        Args:
            configuration_item_id: ID of the configuration item
            note_type: Note type to filter by
            published_only: Whether to return only published notes
            limit: Maximum number of notes to return

        Returns:
            List of notes matching the criteria
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            ),
            QueryFilter(field="NoteType", op="eq", value=note_type),
        ]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def search_notes_by_content(
        self,
        configuration_item_id: int,
        search_text: str,
        published_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search configuration item notes by content.

        Args:
            configuration_item_id: ID of the configuration item
            search_text: Text to search for in note descriptions
            published_only: Whether to return only published notes
            limit: Maximum number of notes to return

        Returns:
            List of notes containing the search text
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            ),
            QueryFilter(field="Description", op="contains", value=search_text),
        ]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_notes_by_author(
        self,
        configuration_item_id: int,
        resource_id: int,
        published_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration item notes created by a specific resource.

        Args:
            configuration_item_id: ID of the configuration item
            resource_id: ID of the resource who created the notes
            published_only: Whether to return only published notes
            limit: Maximum number of notes to return

        Returns:
            List of notes created by the specified resource
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            ),
            QueryFilter(field="CreatedByResourceID", op="eq", value=resource_id),
        ]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_notes_by_date_range(
        self,
        configuration_item_id: int,
        start_date: str,
        end_date: str,
        published_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration item notes within a specific date range.

        Args:
            configuration_item_id: ID of the configuration item
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            published_only: Whether to return only published notes
            limit: Maximum number of notes to return

        Returns:
            List of notes within the date range
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            ),
            QueryFilter(field="CreateDateTime", op="gte", value=start_date),
            QueryFilter(field="CreateDateTime", op="lte", value=end_date),
        ]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_note_content(
        self, note_id: int, new_content: str, new_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the content and/or title of a configuration item note.

        Args:
            note_id: ID of note to update
            new_content: New note content
            new_title: Optional new note title

        Returns:
            Updated note data
        """
        update_data = {"Description": new_content}

        if new_title is not None:
            update_data["Title"] = new_title

        return self.update_by_id(note_id, update_data)

    def publish_note(self, note_id: int) -> Dict[str, Any]:
        """
        Publish a configuration item note (make it visible).

        Args:
            note_id: ID of note to publish

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"IsPublished": True})

    def unpublish_note(self, note_id: int) -> Dict[str, Any]:
        """
        Unpublish a configuration item note (hide it).

        Args:
            note_id: ID of note to unpublish

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"IsPublished": False})

    def get_recent_notes(
        self,
        configuration_item_id: int,
        days: int = 30,
        published_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent configuration item notes from the last N days.

        Args:
            configuration_item_id: ID of the configuration item
            days: Number of days to look back
            published_only: Whether to return only published notes
            limit: Maximum number of notes to return

        Returns:
            List of recent notes
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            ),
            QueryFilter(field="CreateDateTime", op="gte", value=cutoff_date),
        ]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_note_with_attachments(self, note_id: int) -> Dict[str, Any]:
        """
        Get a configuration item note along with its attachments.

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
            "ConfigurationItemNoteAttachments",
            filters=[QueryFilter(field="ParentID", op="eq", value=note_id)],
        )

        note["attachments"] = attachments_response.get("items", [])
        return note

    def get_ci_notes_summary(self, configuration_item_id: int) -> Dict[str, Any]:
        """
        Get a summary of notes for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item

        Returns:
            Dictionary with notes statistics
        """
        all_notes = self.get_ci_notes(configuration_item_id, published_only=False)

        summary = {
            "configuration_item_id": configuration_item_id,
            "total_notes": len(all_notes),
            "published_notes": 0,
            "unpublished_notes": 0,
            "by_type": {},
            "by_author": {},
            "recent_count": 0,
            "oldest_note": None,
            "newest_note": None,
        }

        if not all_notes:
            return summary

        from datetime import datetime, timedelta

        week_ago = datetime.now() - timedelta(days=7)
        oldest_date = None
        newest_date = None

        for note in all_notes:
            # Count by publication status
            if note.get("IsPublished"):
                summary["published_notes"] += 1
            else:
                summary["unpublished_notes"] += 1

            # Count by type
            note_type = note.get("NoteType", "Unknown")
            summary["by_type"][note_type] = summary["by_type"].get(note_type, 0) + 1

            # Count by author
            author_id = note.get("CreatedByResourceID", "Unknown")
            summary["by_author"][author_id] = summary["by_author"].get(author_id, 0) + 1

            # Count recent notes and track dates
            create_date_str = note.get("CreateDateTime")
            if create_date_str:
                try:
                    create_date = datetime.fromisoformat(
                        create_date_str.replace("Z", "+00:00")
                    )

                    if create_date > week_ago:
                        summary["recent_count"] += 1

                    # Track oldest and newest
                    if oldest_date is None or create_date < oldest_date:
                        oldest_date = create_date
                        summary["oldest_note"] = {
                            "id": note.get("id"),
                            "title": note.get("Title"),
                            "date": create_date_str,
                        }

                    if newest_date is None or create_date > newest_date:
                        newest_date = create_date
                        summary["newest_note"] = {
                            "id": note.get("id"),
                            "title": note.get("Title"),
                            "date": create_date_str,
                        }

                except ValueError:
                    pass

        return summary

    def create_maintenance_note(
        self,
        configuration_item_id: int,
        maintenance_type: str,
        maintenance_details: str,
        performed_by_resource_id: Optional[int] = None,
        maintenance_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized maintenance note for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            maintenance_type: Type of maintenance (e.g., "Hardware Replacement", "Software Update")
            maintenance_details: Detailed description of maintenance performed
            performed_by_resource_id: ID of resource who performed maintenance
            maintenance_date: Date maintenance was performed (defaults to now)

        Returns:
            Created maintenance note data
        """
        from datetime import datetime

        if not maintenance_date:
            maintenance_date = datetime.now().isoformat()

        title = f"Maintenance - {maintenance_type}"

        note_text = f"""
Maintenance Type: {maintenance_type}
Date: {maintenance_date}
Performed By: Resource ID {performed_by_resource_id or 'Unknown'}

Details:
{maintenance_details}
""".strip()

        return self.create_ci_note(
            configuration_item_id=configuration_item_id,
            note_text=note_text,
            title=title,
            created_by_resource_id=performed_by_resource_id,
            is_published=True,
            maintenance_type=maintenance_type,
            maintenance_date=maintenance_date,
        )

    def bulk_update_note_types(
        self, note_ids: List[int], new_note_type: int
    ) -> List[Dict[str, Any]]:
        """
        Update the note type for multiple configuration item notes in bulk.

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

    def get_maintenance_history(
        self, configuration_item_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get maintenance history for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            limit: Maximum number of maintenance notes to return

        Returns:
            List of maintenance notes sorted by date
        """
        # Search for notes that contain maintenance information
        maintenance_notes = self.search_notes_by_content(
            configuration_item_id, "Maintenance", limit=limit
        )

        # Sort by creation date (newest first)
        maintenance_notes.sort(key=lambda x: x.get("CreateDateTime", ""), reverse=True)

        return maintenance_notes
