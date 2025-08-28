"""
Document Categories entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class DocumentCategoriesEntity(BaseEntity):
    """
    Handles all Document Category-related operations for the Autotask API.

    Document categories are used to organize and classify documents within
    the Autotask system, providing a hierarchical structure for document
    management and making documents easier to locate and manage.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_document_category(
        self,
        category_name: str,
        description: Optional[str] = None,
        parent_category_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new document category.

        Args:
            category_name: Name of the document category
            description: Optional description of the category
            parent_category_id: ID of parent category for hierarchical organization
            is_active: Whether the category is active
            **kwargs: Additional category fields

        Returns:
            Created document category data
        """
        category_data = {
            "CategoryName": category_name,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            category_data["Description"] = description
        if parent_category_id:
            category_data["ParentCategoryID"] = parent_category_id

        return self.create(category_data)

    def get_active_categories(self) -> List[EntityDict]:
        """
        Get all active document categories.

        Returns:
            List of active document categories
        """
        return self.query_all(
            filters={"field": "IsActive", "op": "eq", "value": "true"}
        )

    def get_categories_by_parent(
        self, parent_id: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get document categories by parent category.

        Args:
            parent_id: Parent category ID (None for root categories)

        Returns:
            List of document categories under the specified parent
        """
        if parent_id is None:
            # Get root categories (no parent)
            return self.query_all(
                filters={"field": "ParentCategoryID", "op": "isnull", "value": ""}
            )
        else:
            return self.query_all(
                filters={"field": "ParentCategoryID", "op": "eq", "value": parent_id}
            )

    def get_category_hierarchy(self, category_id: int) -> Dict[str, Any]:
        """
        Get complete hierarchy path for a document category.

        Args:
            category_id: Category ID to get hierarchy for

        Returns:
            Dictionary containing category hierarchy information
        """
        hierarchy = []
        current_id = category_id

        while current_id:
            category = self.get(current_id)
            if not category:
                break

            hierarchy.insert(
                0,
                {
                    "id": category["id"],
                    "name": category.get("CategoryName", ""),
                    "description": category.get("Description", ""),
                },
            )

            current_id = category.get("ParentCategoryID")

        return {
            "category_id": category_id,
            "hierarchy": hierarchy,
            "full_path": " > ".join([item["name"] for item in hierarchy]),
        }

    def search_categories_by_name(self, search_term: str) -> List[EntityDict]:
        """
        Search document categories by name.

        Args:
            search_term: Term to search for in category names

        Returns:
            List of matching document categories
        """
        return self.query_all(
            filters={"field": "CategoryName", "op": "contains", "value": search_term}
        )

    def deactivate_category(self, category_id: int) -> EntityDict:
        """
        Deactivate a document category.

        Args:
            category_id: ID of the category to deactivate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": False})

    def get_category_descendants(self, parent_id: int) -> List[EntityDict]:
        """
        Get all descendant categories of a parent category.

        Args:
            parent_id: Parent category ID

        Returns:
            List of all descendant categories (recursive)
        """
        descendants = []
        direct_children = self.get_categories_by_parent(parent_id)

        for child in direct_children:
            descendants.append(child)
            # Recursively get descendants of this child
            child_descendants = self.get_category_descendants(child["id"])
            descendants.extend(child_descendants)

        return descendants

    def move_category(
        self, category_id: int, new_parent_id: Optional[int]
    ) -> EntityDict:
        """
        Move a category to a new parent category.

        Args:
            category_id: ID of category to move
            new_parent_id: ID of new parent category (None for root)

        Returns:
            Updated category data
        """
        update_data = {"ParentCategoryID": new_parent_id}
        return self.update_by_id(category_id, update_data)

    def get_category_usage_stats(self, category_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a document category.

        Args:
            category_id: Category ID to get stats for

        Returns:
            Dictionary containing usage statistics
        """
        # Note: This would typically require querying Documents entity
        # to count documents in this category
        category = self.get(category_id)
        if not category:
            return {"error": "Category not found"}

        descendants = self.get_category_descendants(category_id)

        return {
            "category_id": category_id,
            "category_name": category.get("CategoryName", ""),
            "direct_subcategories": len(self.get_categories_by_parent(category_id)),
            "total_descendant_categories": len(descendants),
            "is_active": category.get("IsActive", False),
        }
