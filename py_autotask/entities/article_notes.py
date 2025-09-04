"""
Article Notes entity for Autotask API.

This module provides the ArticleNotesEntity class for managing
notes and comments associated with knowledge base articles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleNotesEntity(BaseEntity):
    """
    Entity for managing Autotask Article Notes.

    Article notes provide annotation and communication capabilities
    for knowledge base articles, enabling collaboration and feedback.
    """

    def __init__(self, client, entity_name="ArticleNotes"):
        """Initialize the Article Notes entity."""
        super().__init__(client, entity_name)

    def create(self, note_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article note.

        Args:
            note_data: Dictionary containing note information
                Required fields:
                - articleId: ID of the article
                - title: Note title
                - description: Note content/body
                - noteType: Type of note (1=General, 2=Important, 3=Technical, 4=Editorial)
                Optional fields:
                - createdBy: ID of the creator resource
                - isInternal: Whether the note is internal only
                - isPublished: Whether the note is published
                - publishDate: Date the note should be published
                - expirationDate: Date the note expires

        Returns:
            CreateResponse: Response containing created note data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["articleId", "title", "description", "noteType"]
        self._validate_required_fields(note_data, required_fields)

        # Set default values
        if "createdDate" not in note_data:
            note_data["createdDate"] = datetime.now().isoformat()

        if "isInternal" not in note_data:
            note_data["isInternal"] = False

        if "isPublished" not in note_data:
            note_data["isPublished"] = True

        return self._create(note_data)

    def get(self, note_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an article note by ID.

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
        Update an existing article note.

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
        update_data["lastModifiedDate"] = datetime.now().isoformat()

        return self._update(note_id, update_data)

    def delete(self, note_id: int) -> bool:
        """
        Delete an article note.

        Args:
            note_id: The note ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(note_id)

    def get_by_article(
        self,
        article_id: int,
        note_type: Optional[int] = None,
        include_internal: bool = True,
        include_unpublished: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all notes for a specific article.

        Args:
            article_id: ID of the article
            note_type: Optional filter by note type
            include_internal: Whether to include internal notes
            include_unpublished: Whether to include unpublished notes
            limit: Maximum number of notes to return

        Returns:
            List of notes for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if note_type is not None:
            filters.append(QueryFilter(field="noteType", op="eq", value=note_type))

        if not include_internal:
            filters.append(QueryFilter(field="isInternal", op="eq", value=False))

        if not include_unpublished:
            filters.append(QueryFilter(field="isPublished", op="eq", value=True))

        notes = self.query(filters=filters, max_records=limit)

        # Sort by creation date (newest first)
        return sorted(notes, key=lambda x: x.get("createdDate", ""), reverse=True)

    def add_article_note(
        self,
        article_id: int,
        title: str,
        description: str,
        note_type: int = 1,
        is_internal: bool = False,
        is_published: bool = True,
        created_by: Optional[int] = None,
    ) -> CreateResponse:
        """
        Add a note to an article.

        Args:
            article_id: ID of the article
            title: Note title
            description: Note content
            note_type: Note type (1=General, 2=Important, 3=Technical, 4=Editorial)
            is_internal: Whether the note is internal only
            is_published: Whether the note is published
            created_by: Optional creator resource ID

        Returns:
            Created note data
        """
        note_data = {
            "articleId": article_id,
            "title": title,
            "description": description,
            "noteType": note_type,
            "isInternal": is_internal,
            "isPublished": is_published,
        }

        if created_by:
            note_data["createdBy"] = created_by

        return self.create(note_data)

    def add_editorial_note(
        self,
        article_id: int,
        title: str,
        description: str,
        is_internal: bool = True,
        created_by: Optional[int] = None,
    ) -> CreateResponse:
        """
        Add an editorial note to an article.

        Args:
            article_id: ID of the article
            title: Note title
            description: Editorial comment
            is_internal: Whether the note is internal (default: True)
            created_by: Optional creator resource ID

        Returns:
            Created editorial note data
        """
        return self.add_article_note(
            article_id=article_id,
            title=title,
            description=description,
            note_type=4,  # Editorial
            is_internal=is_internal,
            created_by=created_by,
        )

    def add_technical_note(
        self,
        article_id: int,
        title: str,
        description: str,
        is_published: bool = True,
        created_by: Optional[int] = None,
    ) -> CreateResponse:
        """
        Add a technical note to an article.

        Args:
            article_id: ID of the article
            title: Note title
            description: Technical information
            is_published: Whether the note is published
            created_by: Optional creator resource ID

        Returns:
            Created technical note data
        """
        return self.add_article_note(
            article_id=article_id,
            title=title,
            description=description,
            note_type=3,  # Technical
            is_internal=False,
            is_published=is_published,
            created_by=created_by,
        )

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
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if update_title:
            update_data["title"] = update_title

        return self.update(note_id, update_data)

    def publish_note(
        self, note_id: int, publish_date: Optional[str] = None
    ) -> UpdateResponse:
        """
        Publish a note.

        Args:
            note_id: Note ID to publish
            publish_date: Optional publish date (defaults to now)

        Returns:
            Updated note data
        """
        update_data = {
            "isPublished": True,
            "publishDate": publish_date or datetime.now().isoformat(),
        }

        return self.update(note_id, update_data)

    def unpublish_note(self, note_id: int) -> UpdateResponse:
        """
        Unpublish a note.

        Args:
            note_id: Note ID to unpublish

        Returns:
            Updated note data
        """
        update_data = {
            "isPublished": False,
        }

        return self.update(note_id, update_data)

    def set_expiration_date(self, note_id: int, expiration_date: str) -> UpdateResponse:
        """
        Set expiration date for a note.

        Args:
            note_id: Note ID to update
            expiration_date: Date the note should expire

        Returns:
            Updated note data
        """
        update_data = {
            "expirationDate": expiration_date,
        }

        return self.update(note_id, update_data)

    def get_by_creator(
        self,
        creator_id: int,
        date_range: Optional[tuple] = None,
        note_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notes created by a specific user.

        Args:
            creator_id: ID of the creator resource
            date_range: Optional tuple of (start_date, end_date)
            note_type: Optional filter by note type
            limit: Maximum number of notes to return

        Returns:
            List of notes created by the user
        """
        filters = [QueryFilter(field="createdBy", op="eq", value=creator_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createdDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createdDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if note_type is not None:
            filters.append(QueryFilter(field="noteType", op="eq", value=note_type))

        return self.query(filters=filters, max_records=limit)

    def get_expired_notes(
        self, check_date: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notes that have expired.

        Args:
            check_date: Date to check against (defaults to now)
            limit: Maximum number of notes to return

        Returns:
            List of expired notes
        """
        check_date = check_date or datetime.now().isoformat()

        filters = [
            QueryFilter(field="expirationDate", op="lt", value=check_date),
            QueryFilter(field="isPublished", op="eq", value=True),
        ]

        return self.query(filters=filters, max_records=limit)

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
                self.logger.error(f"Failed to update note {note_id}: {e}")
                results.append({"error": str(e), "note_id": note_id})

        return results

    def search_notes(
        self,
        search_text: str,
        article_id: Optional[int] = None,
        note_type: Optional[int] = None,
        date_range: Optional[tuple] = None,
        include_internal: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search article notes by text content.

        Args:
            search_text: Text to search for
            article_id: Optional filter by article ID
            note_type: Optional filter by note type
            date_range: Optional date range filter
            include_internal: Whether to include internal notes
            limit: Maximum number of notes to return

        Returns:
            List of matching notes
        """
        filters = [QueryFilter(field="description", op="contains", value=search_text)]

        if article_id:
            filters.append(QueryFilter(field="articleId", op="eq", value=article_id))

        if note_type is not None:
            filters.append(QueryFilter(field="noteType", op="eq", value=note_type))

        if not include_internal:
            filters.append(QueryFilter(field="isInternal", op="eq", value=False))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createdDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createdDate",
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
        self,
        article_ids: Optional[List[int]] = None,
        date_range: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Get note statistics and analytics.

        Args:
            article_ids: Optional list of article IDs to analyze
            date_range: Optional date range for analysis

        Returns:
            Dictionary with note statistics
        """
        filters = []

        if article_ids:
            filters.append(QueryFilter(field="articleId", op="in", value=article_ids))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createdDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createdDate",
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
            "by_type": {
                1: 0,
                2: 0,
                3: 0,
                4: 0,
            },  # General, Important, Technical, Editorial
            "by_article": {},
            "published_notes": 0,
            "internal_notes": 0,
            "expired_notes": 0,
            "by_creator": {},
            "notes_per_day": {},
            "avg_note_length": 0,
        }

        note_lengths = []
        current_date = datetime.now().isoformat()

        for note in notes:
            note_type = note.get("noteType", 1)
            article_id = note.get("articleId")
            creator_id = note.get("createdBy", "Unknown")
            is_published = note.get("isPublished", True)
            is_internal = note.get("isInternal", False)
            description = note.get("description", "")
            created_date = note.get("createdDate", "")
            expiration_date = note.get("expirationDate")

            # Count by type
            if note_type in stats["by_type"]:
                stats["by_type"][note_type] += 1

            # Count by article
            stats["by_article"][article_id] = stats["by_article"].get(article_id, 0) + 1

            # Count by creator
            stats["by_creator"][creator_id] = stats["by_creator"].get(creator_id, 0) + 1

            # Published/internal notes
            if is_published:
                stats["published_notes"] += 1

            if is_internal:
                stats["internal_notes"] += 1

            # Expired notes
            if expiration_date and expiration_date < current_date:
                stats["expired_notes"] += 1

            # Note length
            if description:
                note_lengths.append(len(description))

            # Notes per day
            if created_date:
                try:
                    note_dt = datetime.fromisoformat(
                        created_date.replace("Z", "+00:00")
                    )
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
