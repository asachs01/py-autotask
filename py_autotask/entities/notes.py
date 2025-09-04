"""
Notes entity for Autotask API.

This module provides the NotesEntity class for managing
notes and annotations across different entity types.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class NotesEntity(BaseEntity):
    """
    Entity for managing Autotask Notes.

    Notes provide annotation and communication capabilities
    across various entity types with rich text and attachment support.
    """

    def __init__(self, client, entity_name="Notes"):
        """Initialize the Notes entity."""
        super().__init__(client, entity_name)

    def create(self, note_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new note.

        Args:
            note_data: Dictionary containing note information
                Required fields:
                - title: Note title
                - description: Note content/body
                - noteType: Type of note (1=General, 2=Important, 3=Technical)
                - entityType: Type of associated entity ('Ticket', 'Account', 'Project', etc.)
                - entityID: ID of the associated entity
                Optional fields:
                - publishToClientPortal: Whether to publish to client portal
                - noteDateTime: Date/time of the note
                - creatorResourceID: ID of the creator resource
                - lastActivityPersonType: Type of last activity person
                - isSystem: Whether this is a system-generated note
                - attachments: List of attachment IDs

        Returns:
            CreateResponse: Response containing created note data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["title", "description", "noteType", "entityType", "entityID"]
        self._validate_required_fields(note_data, required_fields)

        # Set default values
        if "noteDateTime" not in note_data:
            note_data["noteDateTime"] = datetime.now().isoformat()

        return self._create(note_data)

    def get(self, note_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a note by ID.

        Args:
            note_id: The note ID

        Returns:
            Dictionary containing note data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(note_id)

    def update(self, note_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing note.

        Args:
            note_id: The note ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated note data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        # Update last modified timestamp
        update_data["lastActivityDate"] = datetime.now().isoformat()

        return self._update(note_id, update_data)

    def delete(self, note_id: int) -> bool:
        """
        Delete a note.

        Args:
            note_id: The note ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(note_id)

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        note_type: Optional[int] = None,
        include_system_notes: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all notes for a specific entity.

        Args:
            entity_type: Type of entity ('Ticket', 'Account', 'Project', etc.)
            entity_id: ID of the entity
            note_type: Optional filter by note type
            include_system_notes: Whether to include system-generated notes
            limit: Maximum number of notes to return

        Returns:
            List of notes for the entity
        """
        filters = [
            QueryFilter(field="entityType", op="eq", value=entity_type),
            QueryFilter(field="entityID", op="eq", value=entity_id),
        ]

        if note_type is not None:
            filters.append(QueryFilter(field="noteType", op="eq", value=note_type))

        if not include_system_notes:
            filters.append(QueryFilter(field="isSystem", op="eq", value=False))

        notes = self.query(filters=filters, max_records=limit)

        # Sort by date (newest first)
        return sorted(notes, key=lambda x: x.get("noteDateTime", ""), reverse=True)

    def get_ticket_notes(
        self,
        ticket_id: int,
        note_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notes for a specific ticket.

        Args:
            ticket_id: Ticket ID
            note_type: Optional note type filter
            limit: Maximum number of notes to return

        Returns:
            List of ticket notes
        """
        return self.get_by_entity("Ticket", ticket_id, note_type, limit=limit)

    def get_account_notes(
        self,
        account_id: int,
        note_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notes for a specific account.

        Args:
            account_id: Account ID
            note_type: Optional note type filter
            limit: Maximum number of notes to return

        Returns:
            List of account notes
        """
        return self.get_by_entity("Account", account_id, note_type, limit=limit)

    def get_project_notes(
        self,
        project_id: int,
        note_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notes for a specific project.

        Args:
            project_id: Project ID
            note_type: Optional note type filter
            limit: Maximum number of notes to return

        Returns:
            List of project notes
        """
        return self.get_by_entity("Project", project_id, note_type, limit=limit)

    def get_by_creator(
        self,
        creator_resource_id: int,
        date_range: Optional[tuple] = None,
        entity_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notes created by a specific resource.

        Args:
            creator_resource_id: ID of the creator resource
            date_range: Optional tuple of (start_date, end_date)
            entity_type: Optional filter by entity type
            limit: Maximum number of notes to return

        Returns:
            List of notes created by the resource
        """
        filters = [
            QueryFilter(field="creatorResourceID", op="eq", value=creator_resource_id)
        ]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="noteDateTime",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="noteDateTime",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if entity_type:
            filters.append(QueryFilter(field="entityType", op="eq", value=entity_type))

        return self.query(filters=filters, max_records=limit)

    def get_client_portal_notes(
        self, entity_type: str, entity_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notes published to client portal for an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            limit: Maximum number of notes to return

        Returns:
            List of client portal notes
        """
        filters = [
            QueryFilter(field="entityType", op="eq", value=entity_type),
            QueryFilter(field="entityID", op="eq", value=entity_id),
            QueryFilter(field="publishToClientPortal", op="eq", value=True),
        ]

        return self.query(filters=filters, max_records=limit)

    def add_ticket_note(
        self,
        ticket_id: int,
        title: str,
        description: str,
        note_type: int = 1,
        publish_to_portal: bool = False,
        creator_resource_id: Optional[int] = None,
    ) -> CreateResponse:
        """
        Add a note to a ticket.

        Args:
            ticket_id: Ticket ID
            title: Note title
            description: Note content
            note_type: Note type (1=General, 2=Important, 3=Technical)
            publish_to_portal: Whether to publish to client portal
            creator_resource_id: Optional creator resource ID

        Returns:
            Created note data
        """
        note_data = {
            "title": title,
            "description": description,
            "noteType": note_type,
            "entityType": "Ticket",
            "entityID": ticket_id,
            "publishToClientPortal": publish_to_portal,
        }

        if creator_resource_id:
            note_data["creatorResourceID"] = creator_resource_id

        return self.create(note_data)

    def add_account_note(
        self,
        account_id: int,
        title: str,
        description: str,
        note_type: int = 1,
        creator_resource_id: Optional[int] = None,
    ) -> CreateResponse:
        """
        Add a note to an account.

        Args:
            account_id: Account ID
            title: Note title
            description: Note content
            note_type: Note type
            creator_resource_id: Optional creator resource ID

        Returns:
            Created note data
        """
        note_data = {
            "title": title,
            "description": description,
            "noteType": note_type,
            "entityType": "Account",
            "entityID": account_id,
        }

        if creator_resource_id:
            note_data["creatorResourceID"] = creator_resource_id

        return self.create(note_data)

    def add_project_note(
        self,
        project_id: int,
        title: str,
        description: str,
        note_type: int = 1,
        creator_resource_id: Optional[int] = None,
    ) -> CreateResponse:
        """
        Add a note to a project.

        Args:
            project_id: Project ID
            title: Note title
            description: Note content
            note_type: Note type
            creator_resource_id: Optional creator resource ID

        Returns:
            Created note data
        """
        note_data = {
            "title": title,
            "description": description,
            "noteType": note_type,
            "entityType": "Project",
            "entityID": project_id,
        }

        if creator_resource_id:
            note_data["creatorResourceID"] = creator_resource_id

        return self.create(note_data)

    def update_note_content(
        self, note_id: int, new_content: str, update_title: Optional[str] = None
    ) -> UpdateResponse:
        """
        Update note content.

        Args:
            note_id: Note ID to update
            new_content: New note content
            update_title: Optional new title

        Returns:
            Updated note data
        """
        update_data = {
            "description": new_content,
            "lastActivityDate": datetime.now().isoformat(),
        }

        if update_title:
            update_data["title"] = update_title

        return self.update(note_id, update_data)

    def toggle_client_portal_visibility(
        self, note_id: int, publish_to_portal: bool
    ) -> UpdateResponse:
        """
        Toggle client portal visibility for a note.

        Args:
            note_id: Note ID to update
            publish_to_portal: Whether to publish to client portal

        Returns:
            Updated note data
        """
        update_data = {
            "publishToClientPortal": publish_to_portal,
            "lastActivityDate": datetime.now().isoformat(),
        }

        return self.update(note_id, update_data)

    def bulk_update_note_type(
        self, note_ids: List[int], new_note_type: int
    ) -> List[UpdateResponse]:
        """
        Update note type for multiple notes.

        Args:
            note_ids: List of note IDs to update
            new_note_type: New note type

        Returns:
            List of update responses
        """
        results = []

        for note_id in note_ids:
            try:
                result = self.update(note_id, {"noteType": new_note_type})
                results.append(result)
            except Exception as e:
                self.client.logger.error(f"Failed to update note {note_id}: {e}")
                results.append({"error": str(e), "note_id": note_id})

        return results

    def search_notes(
        self,
        search_text: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        date_range: Optional[tuple] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search notes by text content.

        Args:
            search_text: Text to search for
            entity_type: Optional filter by entity type
            entity_id: Optional filter by entity ID
            date_range: Optional date range filter
            limit: Maximum number of notes to return

        Returns:
            List of matching notes
        """
        filters = []

        # Text search (simplified - actual implementation may use full-text search)
        filters.append(
            QueryFilter(field="description", op="contains", value=search_text)
        )

        if entity_type:
            filters.append(QueryFilter(field="entityType", op="eq", value=entity_type))

        if entity_id:
            filters.append(QueryFilter(field="entityID", op="eq", value=entity_id))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="noteDateTime",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="noteDateTime",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        return self.query(filters=filters, max_records=limit)

    def get_note_statistics(
        self, entity_type: Optional[str] = None, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get note statistics and analytics.

        Args:
            entity_type: Optional filter by entity type
            date_range: Optional date range for analysis

        Returns:
            Dictionary with note statistics
        """
        filters = []

        if entity_type:
            filters.append(QueryFilter(field="entityType", op="eq", value=entity_type))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="noteDateTime",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="noteDateTime",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        notes = self.query(filters=filters)

        stats = {
            "total_notes": len(notes),
            "by_type": {1: 0, 2: 0, 3: 0},  # General, Important, Technical
            "by_entity_type": {},
            "client_portal_notes": 0,
            "system_notes": 0,
            "user_notes": 0,
            "by_creator": {},
            "notes_per_day": {},
            "avg_note_length": 0,
        }

        note_lengths = []

        for note in notes:
            note_type = note.get("noteType", 1)
            entity_type = note.get("entityType", "Unknown")
            creator_id = note.get("creatorResourceID", "System")
            is_system = note.get("isSystem", False)
            publish_to_portal = note.get("publishToClientPortal", False)
            description = note.get("description", "")
            note_date = note.get("noteDateTime", "")

            # Count by type
            if note_type in stats["by_type"]:
                stats["by_type"][note_type] += 1

            # Count by entity type
            stats["by_entity_type"][entity_type] = (
                stats["by_entity_type"].get(entity_type, 0) + 1
            )

            # Count by creator
            stats["by_creator"][creator_id] = stats["by_creator"].get(creator_id, 0) + 1

            # Portal and system notes
            if publish_to_portal:
                stats["client_portal_notes"] += 1

            if is_system:
                stats["system_notes"] += 1
            else:
                stats["user_notes"] += 1

            # Note length
            if description:
                note_lengths.append(len(description))

            # Notes per day
            if note_date:
                try:
                    note_dt = datetime.fromisoformat(note_date.replace("Z", "+00:00"))
                    day_key = note_dt.date().isoformat()
                    stats["notes_per_day"][day_key] = (
                        stats["notes_per_day"].get(day_key, 0) + 1
                    )
                except ValueError:
                    pass

        # Calculate average note length
        if note_lengths:
            stats["avg_note_length"] = sum(note_lengths) / len(note_lengths)

        return stats

    def get_entity_note_summary(
        self, entity_type: str, entity_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive note summary for an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity

        Returns:
            Dictionary with note summary
        """
        notes = self.get_by_entity(entity_type, entity_id)

        summary = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_notes": len(notes),
            "by_type": {1: 0, 2: 0, 3: 0},
            "client_portal_notes": 0,
            "recent_notes": [],
            "most_recent_note": None,
            "oldest_note": None,
        }

        if not notes:
            return summary

        # Sort notes by date
        sorted_notes = sorted(
            notes, key=lambda x: x.get("noteDateTime", ""), reverse=True
        )

        summary["most_recent_note"] = sorted_notes[0]
        summary["oldest_note"] = sorted_notes[-1]
        summary["recent_notes"] = sorted_notes[:5]  # Last 5 notes

        for note in notes:
            note_type = note.get("noteType", 1)
            if note_type in summary["by_type"]:
                summary["by_type"][note_type] += 1

            if note.get("publishToClientPortal", False):
                summary["client_portal_notes"] += 1

        return summary

    def validate_note_data(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate note data.

        Args:
            note_data: Note data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["title", "description", "noteType", "entityType", "entityID"]
        for field in required_fields:
            if field not in note_data or note_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate title
        title = note_data.get("title", "")
        if title:
            if len(title) < 2:
                errors.append("Note title must be at least 2 characters")
            elif len(title) > 255:
                errors.append("Note title must not exceed 255 characters")

        # Validate description
        description = note_data.get("description", "")
        if description:
            if len(description) < 1:
                errors.append("Note description cannot be empty")
            elif len(description) > 10000:
                warnings.append(
                    "Note description is very long (over 10,000 characters)"
                )

        # Validate note type
        note_type = note_data.get("noteType")
        if note_type is not None:
            if note_type not in [1, 2, 3]:
                errors.append(
                    "Note type must be 1 (General), 2 (Important), or 3 (Technical)"
                )

        # Validate entity type
        entity_type = note_data.get("entityType", "")
        valid_entity_types = [
            "Ticket",
            "Account",
            "Project",
            "Contact",
            "Contract",
            "Task",
        ]
        if entity_type and entity_type not in valid_entity_types:
            warnings.append(f"Entity type '{entity_type}' may not be supported")

        # Validate note date
        note_date = note_data.get("noteDateTime")
        if note_date:
            try:
                if isinstance(note_date, str):
                    datetime.fromisoformat(note_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Note date/time must be a valid datetime")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
