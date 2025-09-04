"""
ClassificationIcons entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ClassificationIconsEntity(BaseEntity):
    """
    Handles all ClassificationIcons-related operations for the Autotask API.

    ClassificationIcons represent visual indicators used to classify and
    categorize various entities in Autotask, providing quick visual identification.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_classification_icon(
        self,
        name: str,
        icon_type: str,
        file_path: str,
        description: Optional[str] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new classification icon.

        Args:
            name: Name of the classification icon
            icon_type: Type of icon (e.g., 'ticket', 'project', 'company')
            file_path: Path to the icon file
            description: Description of the icon usage
            is_active: Whether the icon is active
            **kwargs: Additional icon properties

        Returns:
            Created classification icon data
        """
        icon_data = {
            "Name": name,
            "IconType": icon_type,
            "FilePath": file_path,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            icon_data["Description"] = description

        return self.create(icon_data)

    def get_active_icons(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all active classification icons.

        Args:
            limit: Maximum number of icons to return

        Returns:
            List of active classification icons
        """
        filters = [QueryFilter(field="IsActive", op="eq", value=True)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_icons_by_type(
        self, icon_type: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get classification icons by type.

        Args:
            icon_type: Type of icon to filter by
            active_only: Whether to return only active icons
            limit: Maximum number of icons to return

        Returns:
            List of classification icons of the specified type
        """
        filters = [QueryFilter(field="IconType", op="eq", value=icon_type)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def search_icons_by_name(
        self, search_term: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search classification icons by name.

        Args:
            search_term: Term to search for in icon names
            limit: Maximum number of icons to return

        Returns:
            List of matching classification icons
        """
        filters = [QueryFilter(field="Name", op="contains", value=search_term)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def activate_icon(self, icon_id: int) -> EntityDict:
        """
        Activate a classification icon.

        Args:
            icon_id: ID of the icon to activate

        Returns:
            Updated icon data
        """
        return self.update_by_id(icon_id, {"IsActive": True})

    def deactivate_icon(self, icon_id: int) -> EntityDict:
        """
        Deactivate a classification icon.

        Args:
            icon_id: ID of the icon to deactivate

        Returns:
            Updated icon data
        """
        return self.update_by_id(icon_id, {"IsActive": False})

    def update_icon_file_path(self, icon_id: int, new_file_path: str) -> EntityDict:
        """
        Update the file path of a classification icon.

        Args:
            icon_id: ID of the icon to update
            new_file_path: New file path for the icon

        Returns:
            Updated icon data
        """
        return self.update_by_id(icon_id, {"FilePath": new_file_path})

    def get_icon_usage_statistics(self, icon_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a classification icon.

        Args:
            icon_id: ID of the icon

        Returns:
            Dictionary containing usage statistics
        """
        icon = self.get(icon_id)
        if not icon:
            return {"error": "Icon not found"}

        # This would typically require cross-referencing with entities that use this icon
        # For now, return basic icon information
        return {
            "icon_id": icon_id,
            "icon_name": icon.get("Name"),
            "icon_type": icon.get("IconType"),
            "is_active": icon.get("IsActive", False),
            "file_path": icon.get("FilePath"),
            "usage_count": 0,  # Would be calculated from actual usage
            "last_used": None,  # Would come from usage tracking
            "created_date": icon.get("CreateDateTime"),
            "last_modified": icon.get("LastModifiedDateTime"),
        }

    def bulk_create_icons(self, icons_data: List[Dict[str, Any]]) -> List[EntityDict]:
        """
        Create multiple classification icons in batch.

        Args:
            icons_data: List of icon data dictionaries

        Returns:
            List of created icon responses
        """
        return self.batch_create(icons_data)

    def get_icons_by_file_format(
        self, file_extension: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get classification icons by file format.

        Args:
            file_extension: File extension to filter by (e.g., '.png', '.svg')
            limit: Maximum number of icons to return

        Returns:
            List of icons with the specified file format
        """
        filters = [QueryFilter(field="FilePath", op="endswith", value=file_extension)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_icon_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an icon file path for common issues.

        Args:
            file_path: File path to validate

        Returns:
            Dictionary containing validation results
        """
        validation_results = {"is_valid": True, "warnings": [], "errors": []}

        # Check if path is provided
        if not file_path:
            validation_results["is_valid"] = False
            validation_results["errors"].append("File path is required")
            return validation_results

        # Check file extension
        valid_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"]
        if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
            validation_results["warnings"].append(
                f"File extension may not be supported. Valid extensions: {', '.join(valid_extensions)}"
            )

        # Check path length
        if len(file_path) > 255:
            validation_results["is_valid"] = False
            validation_results["errors"].append(
                "File path exceeds maximum length (255 characters)"
            )

        # Check for common path issues
        if "\\" in file_path and "/" in file_path:
            validation_results["warnings"].append("Mixed path separators detected")

        if file_path.startswith(" ") or file_path.endswith(" "):
            validation_results["warnings"].append(
                "File path has leading or trailing spaces"
            )

        return validation_results

    def get_icons_summary_by_type(self) -> Dict[str, Any]:
        """
        Get a summary of classification icons grouped by type.

        Returns:
            Dictionary containing icons summary by type
        """
        all_icons = self.query_all()

        summary = {
            "total_icons": len(all_icons),
            "active_icons": len(
                [icon for icon in all_icons if icon.get("IsActive", False)]
            ),
            "types": {},
            "file_formats": {},
        }

        for icon in all_icons:
            icon_type = icon.get("IconType", "Unknown")
            file_path = icon.get("FilePath", "")

            # Count by type
            if icon_type not in summary["types"]:
                summary["types"][icon_type] = {"count": 0, "active_count": 0}

            summary["types"][icon_type]["count"] += 1
            if icon.get("IsActive", False):
                summary["types"][icon_type]["active_count"] += 1

            # Count by file format
            if file_path:
                ext = (
                    file_path.split(".")[-1].lower() if "." in file_path else "unknown"
                )
                if ext not in summary["file_formats"]:
                    summary["file_formats"][ext] = 0
                summary["file_formats"][ext] += 1

        return summary

    def duplicate_icon(
        self, source_icon_id: int, new_name: str, new_file_path: str
    ) -> EntityDict:
        """
        Create a duplicate of an existing classification icon.

        Args:
            source_icon_id: ID of the icon to duplicate
            new_name: Name for the new icon
            new_file_path: File path for the new icon

        Returns:
            Created duplicate icon data
        """
        source_icon = self.get(source_icon_id)
        if not source_icon:
            raise ValueError(f"Source icon {source_icon_id} not found")

        duplicate_data = {
            "Name": new_name,
            "IconType": source_icon.get("IconType"),
            "FilePath": new_file_path,
            "Description": f"Copy of {source_icon.get('Description', '')}",
            "IsActive": source_icon.get("IsActive", True),
        }

        return self.create_classification_icon(**duplicate_data)

    def cleanup_unused_icons(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Identify or remove unused classification icons.

        Args:
            dry_run: If True, only identify unused icons without deleting

        Returns:
            Dictionary containing cleanup results
        """
        all_icons = self.query_all()
        inactive_icons = [icon for icon in all_icons if not icon.get("IsActive", False)]

        cleanup_results = {
            "total_icons": len(all_icons),
            "inactive_icons": len(inactive_icons),
            "potentially_unused": inactive_icons,
            "dry_run": dry_run,
            "deleted_count": 0,
        }

        if not dry_run and inactive_icons:
            # In a real implementation, you would check usage before deleting
            # For now, we'll just mark them as potentially deletable
            cleanup_results["warning"] = (
                "Actual deletion not implemented - use with caution"
            )

        return cleanup_results
