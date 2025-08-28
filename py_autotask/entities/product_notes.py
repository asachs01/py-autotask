"""
ProductNotes entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ProductNotesEntity(BaseEntity):
    """
    Handles all Product Note-related operations for the Autotask API.

    Product Notes are text notes attached to products for documentation and tracking.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_product_note(
        self,
        product_id: int,
        title: str,
        description: str,
        note_type: Optional[int] = None,
        is_published: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new product note.

        Args:
            product_id: ID of the product
            title: Title of the note
            description: Content of the note
            note_type: Type/category of the note
            is_published: Whether the note is published/visible
            **kwargs: Additional note fields

        Returns:
            Created product note data
        """
        note_data = {
            "ProductID": product_id,
            "Title": title,
            "Description": description,
            "IsPublished": is_published,
            **kwargs,
        }

        if note_type is not None:
            note_data["NoteType"] = note_type

        return self.create(note_data)

    def get_notes_by_product(
        self, product_id: int, published_only: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all notes for a specific product.

        Args:
            product_id: ID of the product
            published_only: Whether to return only published notes
            limit: Maximum number of records to return

        Returns:
            List of notes for the product
        """
        filters = [QueryFilter(field="ProductID", op="eq", value=product_id)]

        if published_only:
            filters.append(QueryFilter(field="IsPublished", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def search_notes_by_title(
        self, title: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for product notes by title.

        Args:
            title: Title to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching notes
        """
        if exact_match:
            filters = [QueryFilter(field="Title", op="eq", value=title)]
        else:
            filters = [QueryFilter(field="Title", op="contains", value=title)]

        return self.query(filters=filters, max_records=limit)

    def search_notes_by_content(
        self, search_text: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for product notes by content.

        Args:
            search_text: Text to search for in note content
            limit: Maximum number of records to return

        Returns:
            List of notes containing the search text
        """
        filters = [QueryFilter(field="Description", op="contains", value=search_text)]

        return self.query(filters=filters, max_records=limit)

    def get_notes_by_type(
        self, note_type: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get product notes by type.

        Args:
            note_type: Type/category of notes to retrieve
            limit: Maximum number of records to return

        Returns:
            List of notes of the specified type
        """
        filters = [QueryFilter(field="NoteType", op="eq", value=note_type)]

        return self.query(filters=filters, max_records=limit)

    def get_recent_notes(
        self, days: int = 30, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get recently created product notes.

        Args:
            days: Number of days to look back
            limit: Maximum number of records to return

        Returns:
            List of recent notes
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        filters = [QueryFilter(field="CreateDate", op="ge", value=start_date)]

        return self.query(filters=filters, max_records=limit)

    def get_published_notes(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all published product notes.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of published notes
        """
        filters = [QueryFilter(field="IsPublished", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def update_note_content(self, note_id: int, new_content: str) -> EntityDict:
        """
        Update the content of a product note.

        Args:
            note_id: ID of the note
            new_content: New content for the note

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"Description": new_content})

    def publish_note(self, note_id: int) -> EntityDict:
        """
        Publish a product note (make it visible).

        Args:
            note_id: ID of the note

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"IsPublished": True})

    def unpublish_note(self, note_id: int) -> EntityDict:
        """
        Unpublish a product note (make it private).

        Args:
            note_id: ID of the note

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"IsPublished": False})

    def update_note_type(self, note_id: int, note_type: int) -> EntityDict:
        """
        Update the type/category of a product note.

        Args:
            note_id: ID of the note
            note_type: New note type

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"NoteType": note_type})

    def get_notes_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about product notes.

        Returns:
            Dictionary containing note statistics
        """
        all_notes = self.query()

        # Group by note type
        type_counts = {}
        for note in all_notes:
            note_type = note.get("NoteType", "Unknown")
            type_counts[note_type] = type_counts.get(note_type, 0) + 1

        # Calculate content length statistics
        content_lengths = [len(note.get("Description", "")) for note in all_notes]

        stats = {
            "total_notes": len(all_notes),
            "published_notes": len(
                [note for note in all_notes if note.get("IsPublished", False)]
            ),
            "unpublished_notes": len(
                [note for note in all_notes if not note.get("IsPublished", False)]
            ),
            "notes_by_type": type_counts,
            "unique_products": len(
                set(
                    note.get("ProductID") for note in all_notes if note.get("ProductID")
                )
            ),
        }

        if content_lengths:
            stats["content_stats"] = {
                "average_length": round(sum(content_lengths) / len(content_lengths), 2),
                "shortest_note": min(content_lengths),
                "longest_note": max(content_lengths),
            }

        return stats

    def get_product_note_summary(self, product_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of notes for a specific product.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with note summary for the product
        """
        product_notes = self.get_notes_by_product(product_id)

        # Analyze note types
        type_counts = {}
        for note in product_notes:
            note_type = note.get("NoteType", "General")
            type_counts[note_type] = type_counts.get(note_type, 0) + 1

        # Get recent activity
        recent_notes = [
            note
            for note in product_notes
            if self._is_recent_date(note.get("CreateDate"), 30)
        ]

        summary = {
            "product_id": product_id,
            "total_notes": len(product_notes),
            "published_notes": len(
                [note for note in product_notes if note.get("IsPublished", False)]
            ),
            "unpublished_notes": len(
                [note for note in product_notes if not note.get("IsPublished", False)]
            ),
            "notes_by_type": type_counts,
            "recent_activity": {
                "notes_last_30_days": len(recent_notes),
                "last_note_date": max(
                    (
                        note.get("CreateDate")
                        for note in product_notes
                        if note.get("CreateDate")
                    ),
                    default=None,
                ),
            },
        }

        return summary

    def _is_recent_date(self, date_str: Optional[str], days: int) -> bool:
        """
        Helper method to check if a date is within the last N days.

        Args:
            date_str: Date string to check
            days: Number of days to check against

        Returns:
            True if the date is within the last N days
        """
        if not date_str:
            return False

        try:
            from datetime import date, datetime, timedelta

            note_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            cutoff_date = date.today() - timedelta(days=days)
            return note_date >= cutoff_date
        except (ValueError, TypeError):
            return False
