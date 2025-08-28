"""
Attachment Info entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class AttachmentInfoEntity(BaseEntity):
    """
    Handles Attachment Information operations for the Autotask API.

    Provides enhanced attachment management with metadata,
    categorization, and advanced search capabilities.
    """

    def __init__(self, client, entity_name: str = "AttachmentInfo"):
        super().__init__(client, entity_name)

    def create_attachment_info(
        self,
        parent_id: int,
        parent_type: str,
        title: str,
        file_path: str,
        content_type: str,
        file_size: int,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_public: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create attachment information record.

        Args:
            parent_id: ID of the parent entity
            parent_type: Type of parent (Ticket, Project, etc.)
            title: Attachment title/name
            file_path: Path to the file
            content_type: MIME type of the file
            file_size: File size in bytes
            description: Optional description
            category: Optional category for organization
            is_public: Whether attachment is publicly visible
            **kwargs: Additional attachment fields

        Returns:
            Created attachment info data
        """
        attachment_data = {
            "ParentID": parent_id,
            "ParentType": parent_type,
            "Title": title,
            "FilePath": file_path,
            "ContentType": content_type,
            "FileSize": file_size,
            "IsPublic": is_public,
            **kwargs,
        }

        if description:
            attachment_data["Description"] = description

        if category:
            attachment_data["Category"] = category

        return self.create(attachment_data)

    def get_attachments_by_parent(
        self,
        parent_id: int,
        parent_type: str,
        category: Optional[str] = None,
        public_only: bool = False,
    ) -> EntityList:
        """
        Get all attachments for a specific parent entity.

        Args:
            parent_id: Parent entity ID
            parent_type: Type of parent entity
            category: Optional category filter
            public_only: Whether to include only public attachments

        Returns:
            List of attachment info records
        """
        filters = [
            {"field": "ParentID", "op": "eq", "value": str(parent_id)},
            {"field": "ParentType", "op": "eq", "value": parent_type},
        ]

        if category:
            filters.append({"field": "Category", "op": "eq", "value": category})

        if public_only:
            filters.append({"field": "IsPublic", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_attachments_by_type(
        self,
        content_type: str,
        days: Optional[int] = None,
    ) -> EntityList:
        """
        Get attachments filtered by content type.

        Args:
            content_type: MIME type to filter by
            days: Optional filter for recent attachments

        Returns:
            List of attachments with specified content type
        """
        filters = [{"field": "ContentType", "op": "eq", "value": content_type}]

        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            filters.append(
                {"field": "CreateDate", "op": "gte", "value": cutoff_date.isoformat()}
            )

        return self.query_all(filters=filters)

    def get_large_attachments(
        self,
        min_size_mb: float = 10.0,
        parent_type: Optional[str] = None,
    ) -> EntityList:
        """
        Get attachments larger than specified size.

        Args:
            min_size_mb: Minimum size in megabytes
            parent_type: Optional parent type filter

        Returns:
            List of large attachments
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        filters = [{"field": "FileSize", "op": "gte", "value": str(min_size_bytes)}]

        if parent_type:
            filters.append({"field": "ParentType", "op": "eq", "value": parent_type})

        return self.query_all(filters=filters)

    def search_attachments_by_name(
        self,
        search_term: str,
        parent_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> EntityList:
        """
        Search attachments by title or description.

        Args:
            search_term: Term to search for
            parent_type: Optional parent type filter
            category: Optional category filter

        Returns:
            List of matching attachments
        """
        # Search in both title and description
        title_matches = self.query_all(
            filters=[{"field": "Title", "op": "contains", "value": search_term}]
        )

        desc_matches = self.query_all(
            filters=[{"field": "Description", "op": "contains", "value": search_term}]
        )

        # Combine results and remove duplicates
        all_matches = {}
        for attachment in title_matches + desc_matches:
            all_matches[attachment["id"]] = attachment

        results = list(all_matches.values())

        # Apply additional filters
        if parent_type:
            results = [a for a in results if a.get("ParentType") == parent_type]

        if category:
            results = [a for a in results if a.get("Category") == category]

        return results

    def update_attachment_category(
        self, attachment_id: int, category: str
    ) -> Optional[EntityDict]:
        """
        Update the category of an attachment.

        Args:
            attachment_id: Attachment ID
            category: New category

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"Category": category})

    def update_attachment_visibility(
        self, attachment_id: int, is_public: bool
    ) -> Optional[EntityDict]:
        """
        Update the visibility of an attachment.

        Args:
            attachment_id: Attachment ID
            is_public: New visibility setting

        Returns:
            Updated attachment data
        """
        return self.update_by_id(attachment_id, {"IsPublic": is_public})

    def categorize_attachments_by_type(
        self, parent_id: int, parent_type: str
    ) -> Dict[str, Any]:
        """
        Automatically categorize attachments based on file type.

        Args:
            parent_id: Parent entity ID
            parent_type: Parent entity type

        Returns:
            Dictionary with categorization results
        """
        attachments = self.get_attachments_by_parent(parent_id, parent_type)

        # Define content type mappings to categories
        type_mappings = {
            "image": [
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/bmp",
                "image/webp",
            ],
            "document": [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "text/rtf",
            ],
            "spreadsheet": [
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/csv",
            ],
            "presentation": [
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ],
            "archive": [
                "application/zip",
                "application/x-rar",
                "application/x-7z-compressed",
            ],
            "video": ["video/mp4", "video/avi", "video/mov", "video/wmv"],
            "audio": ["audio/mp3", "audio/wav", "audio/aac", "audio/ogg"],
        }

        results = {
            "processed": 0,
            "updated": 0,
            "errors": [],
            "categories": {category: 0 for category in type_mappings.keys()},
        }

        for attachment in attachments:
            results["processed"] += 1
            content_type = attachment.get("ContentType", "").lower()

            # Skip if already categorized
            if attachment.get("Category"):
                continue

            # Find matching category
            new_category = "other"  # default
            for category, mime_types in type_mappings.items():
                if any(mime_type in content_type for mime_type in mime_types):
                    new_category = category
                    break

            try:
                # Update the attachment with new category
                updated = self.update_attachment_category(
                    int(attachment["id"]), new_category
                )
                if updated:
                    results["updated"] += 1
                    results["categories"][new_category] += 1

            except Exception as e:
                results["errors"].append(
                    f"Failed to update attachment {attachment['id']}: {e}"
                )

        return results

    def get_attachment_statistics(
        self, parent_id: Optional[int] = None, parent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics about attachments.

        Args:
            parent_id: Optional parent ID filter
            parent_type: Optional parent type filter

        Returns:
            Dictionary with attachment statistics
        """
        filters = []
        if parent_id and parent_type:
            filters = [
                {"field": "ParentID", "op": "eq", "value": str(parent_id)},
                {"field": "ParentType", "op": "eq", "value": parent_type},
            ]

        attachments = self.query_all(filters=filters) if filters else self.query_all()

        stats = {
            "total_attachments": len(attachments),
            "total_size_bytes": 0,
            "total_size_mb": 0.0,
            "public_attachments": 0,
            "private_attachments": 0,
            "by_content_type": {},
            "by_category": {},
            "by_parent_type": {},
            "largest_file": {"size": 0, "title": ""},
            "oldest_attachment": None,
            "newest_attachment": None,
        }

        oldest_date = None
        newest_date = None

        for attachment in attachments:
            # Size calculations
            file_size = int(attachment.get("FileSize", 0))
            stats["total_size_bytes"] += file_size

            # Track largest file
            if file_size > stats["largest_file"]["size"]:
                stats["largest_file"]["size"] = file_size
                stats["largest_file"]["title"] = attachment.get("Title", "Unknown")

            # Visibility counts
            if attachment.get("IsPublic", True):
                stats["public_attachments"] += 1
            else:
                stats["private_attachments"] += 1

            # Content type distribution
            content_type = attachment.get("ContentType", "unknown")
            if content_type not in stats["by_content_type"]:
                stats["by_content_type"][content_type] = 0
            stats["by_content_type"][content_type] += 1

            # Category distribution
            category = attachment.get("Category", "uncategorized")
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1

            # Parent type distribution
            parent_type = attachment.get("ParentType", "unknown")
            if parent_type not in stats["by_parent_type"]:
                stats["by_parent_type"][parent_type] = 0
            stats["by_parent_type"][parent_type] += 1

            # Date tracking
            create_date_str = attachment.get("CreateDate")
            if create_date_str:
                create_date = datetime.fromisoformat(
                    create_date_str.replace("Z", "+00:00")
                )
                if oldest_date is None or create_date < oldest_date:
                    oldest_date = create_date
                    stats["oldest_attachment"] = attachment.get("Title", "Unknown")
                if newest_date is None or create_date > newest_date:
                    newest_date = create_date
                    stats["newest_attachment"] = attachment.get("Title", "Unknown")

        # Convert to megabytes
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)

        return stats

    def cleanup_orphaned_attachments(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Identify and optionally remove attachments with missing parent entities.

        Args:
            dry_run: If True, only identify orphaned attachments without deleting

        Returns:
            Dictionary with cleanup results
        """
        all_attachments = self.query_all()

        results = {
            "total_checked": len(all_attachments),
            "orphaned_attachments": [],
            "deleted_count": 0,
            "errors": [],
            "dry_run": dry_run,
        }

        for attachment in all_attachments:
            parent_id = attachment.get("ParentID")
            parent_type = attachment.get("ParentType")

            if not parent_id or not parent_type:
                results["orphaned_attachments"].append(attachment)
                continue

            try:
                # Check if parent entity exists
                parent_exists = False
                try:
                    parent_entity = self.client.get(parent_type, int(parent_id))
                    parent_exists = parent_entity is not None
                except Exception:
                    parent_exists = False

                if not parent_exists:
                    results["orphaned_attachments"].append(attachment)

                    # Delete if not dry run
                    if not dry_run:
                        if self.delete(int(attachment["id"])):
                            results["deleted_count"] += 1

            except Exception as e:
                results["errors"].append(
                    f"Error checking attachment {attachment['id']}: {e}"
                )

        return results

    def get_duplicate_attachments(self) -> Dict[str, List[EntityDict]]:
        """
        Find potential duplicate attachments based on name and size.

        Returns:
            Dictionary mapping duplicate keys to lists of attachments
        """
        all_attachments = self.query_all()
        duplicates = {}

        for attachment in all_attachments:
            # Create a key based on title and file size
            title = attachment.get("Title", "").lower().strip()
            file_size = attachment.get("FileSize", 0)
            duplicate_key = f"{title}_{file_size}"

            if duplicate_key not in duplicates:
                duplicates[duplicate_key] = []

            duplicates[duplicate_key].append(attachment)

        # Filter to only include actual duplicates
        actual_duplicates = {
            key: attachments
            for key, attachments in duplicates.items()
            if len(attachments) > 1
        }

        return actual_duplicates
