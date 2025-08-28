"""
ChecklistLibraries entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ChecklistLibrariesEntity(BaseEntity):
    """
    Handles all ChecklistLibraries-related operations for the Autotask API.

    ChecklistLibraries represent reusable templates for checklists that can be
    applied to tickets, projects, or other work items for standardized procedures.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_checklist_library(
        self,
        name: str,
        description: str,
        category: Optional[str] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new checklist library.

        Args:
            name: Name of the checklist library
            description: Description of the checklist library
            category: Category or type of checklist
            is_active: Whether the checklist is active
            **kwargs: Additional checklist library properties

        Returns:
            Created checklist library data
        """
        library_data = {
            "Name": name,
            "Description": description,
            "IsActive": is_active,
            **kwargs,
        }

        if category:
            library_data["Category"] = category

        return self.create(library_data)

    def get_active_libraries(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all active checklist libraries.

        Args:
            limit: Maximum number of libraries to return

        Returns:
            List of active checklist libraries
        """
        filters = [QueryFilter(field="IsActive", op="eq", value=True)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_libraries_by_category(
        self, category: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get checklist libraries by category.

        Args:
            category: Category to filter by
            active_only: Whether to return only active libraries
            limit: Maximum number of libraries to return

        Returns:
            List of checklist libraries in the specified category
        """
        filters = [QueryFilter(field="Category", op="eq", value=category)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def search_libraries_by_name(
        self, search_term: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search checklist libraries by name.

        Args:
            search_term: Term to search for in library names
            limit: Maximum number of libraries to return

        Returns:
            List of matching checklist libraries
        """
        filters = [QueryFilter(field="Name", op="contains", value=search_term)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def activate_library(self, library_id: int) -> EntityDict:
        """
        Activate a checklist library.

        Args:
            library_id: ID of the library to activate

        Returns:
            Updated library data
        """
        return self.update_by_id(library_id, {"IsActive": True})

    def deactivate_library(self, library_id: int) -> EntityDict:
        """
        Deactivate a checklist library.

        Args:
            library_id: ID of the library to deactivate

        Returns:
            Updated library data
        """
        return self.update_by_id(library_id, {"IsActive": False})

    def update_library_details(
        self,
        library_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Update checklist library details.

        Args:
            library_id: ID of the library to update
            name: New name for the library
            description: New description for the library
            category: New category for the library
            **kwargs: Additional properties to update

        Returns:
            Updated library data
        """
        update_data = {**kwargs}

        if name:
            update_data["Name"] = name
        if description:
            update_data["Description"] = description
        if category:
            update_data["Category"] = category

        return self.update_by_id(library_id, update_data)

    def get_library_usage_statistics(self, library_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a checklist library.

        Args:
            library_id: ID of the library

        Returns:
            Dictionary containing usage statistics
        """
        # This would typically require cross-referencing with tickets/projects
        # that use this checklist library

        library = self.get(library_id)
        if not library:
            return {"error": "Library not found"}

        # Basic statistics (would be enhanced with actual usage data)
        return {
            "library_id": library_id,
            "library_name": library.get("Name"),
            "is_active": library.get("IsActive", False),
            "category": library.get("Category"),
            "total_items": 0,  # Would come from ChecklistLibraryChecklistItems
            "usage_count": 0,  # Would come from actual usage tracking
            "last_used": None,  # Would come from usage tracking
            "created_date": library.get("CreateDateTime"),
            "last_modified": library.get("LastModifiedDateTime"),
        }

    def duplicate_library(
        self,
        source_library_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> EntityDict:
        """
        Create a duplicate of an existing checklist library.

        Args:
            source_library_id: ID of the library to duplicate
            new_name: Name for the new library
            new_description: Description for the new library

        Returns:
            Created duplicate library data
        """
        source_library = self.get(source_library_id)
        if not source_library:
            raise ValueError(f"Source library {source_library_id} not found")

        # Create new library with copied properties
        duplicate_data = {
            "Name": new_name,
            "Description": new_description
            or f"Copy of {source_library.get('Description', '')}",
            "Category": source_library.get("Category"),
            "IsActive": source_library.get("IsActive", True),
        }

        return self.create_checklist_library(**duplicate_data)

    def bulk_create_libraries(
        self, libraries_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple checklist libraries in batch.

        Args:
            libraries_data: List of library data dictionaries

        Returns:
            List of created library responses
        """
        return self.batch_create(libraries_data)

    def get_libraries_summary_by_category(self) -> Dict[str, Any]:
        """
        Get a summary of checklist libraries grouped by category.

        Returns:
            Dictionary containing libraries summary by category
        """
        all_libraries = self.get_active_libraries()

        summary = {
            "total_libraries": len(all_libraries),
            "active_libraries": len(
                [lib for lib in all_libraries if lib.get("IsActive", False)]
            ),
            "categories": {},
            "uncategorized_count": 0,
        }

        for library in all_libraries:
            category = library.get("Category", "Uncategorized")

            if category == "Uncategorized" or not category:
                summary["uncategorized_count"] += 1
            else:
                if category not in summary["categories"]:
                    summary["categories"][category] = {
                        "count": 0,
                        "active_count": 0,
                        "libraries": [],
                    }

                summary["categories"][category]["count"] += 1
                if library.get("IsActive", False):
                    summary["categories"][category]["active_count"] += 1

                summary["categories"][category]["libraries"].append(
                    {
                        "id": library.get("id"),
                        "name": library.get("Name"),
                        "is_active": library.get("IsActive", False),
                    }
                )

        return summary

    def export_library_templates(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Export checklist library templates for backup or migration.

        Args:
            category: Optional category filter

        Returns:
            List of library template data
        """
        if category:
            libraries = self.get_libraries_by_category(category, active_only=False)
        else:
            libraries = self.query_all()

        export_data = []
        for library in libraries:
            template = {
                "name": library.get("Name"),
                "description": library.get("Description"),
                "category": library.get("Category"),
                "is_active": library.get("IsActive", False),
                "export_date": library.get("LastModifiedDateTime"),
                # Would include checklist items if available
                "checklist_items": [],
            }
            export_data.append(template)

        return export_data
