"""
Configuration Item Categories entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemCategoriesEntity(BaseEntity):
    """
    Handles all Configuration Item Category-related operations for the Autotask API.

    Configuration Item Categories represent classification types for configuration items
    to organize and categorize assets within the Autotask system.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ci_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent_category_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item category.

        Args:
            name: Name of the category
            description: Optional description of the category
            parent_category_id: Optional parent category ID for hierarchy
            is_active: Whether the category is active
            **kwargs: Additional category fields

        Returns:
            Created configuration item category data
        """
        category_data = {
            "Name": name,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            category_data["Description"] = description

        if parent_category_id:
            category_data["ParentCategoryID"] = parent_category_id

        return self.create(category_data)

    def get_all_categories(
        self,
        active_only: bool = True,
        include_hierarchy: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all configuration item categories.

        Args:
            active_only: Whether to return only active categories
            include_hierarchy: Whether to include hierarchy information
            limit: Maximum number of categories to return

        Returns:
            List of configuration item categories
        """
        filters = []

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        categories = response.items

        if include_hierarchy:
            # Build hierarchy information
            categories = self._build_category_hierarchy(categories)

        return categories

    def get_root_categories(
        self,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get root-level configuration item categories (no parent).

        Args:
            active_only: Whether to return only active categories
            limit: Maximum number of categories to return

        Returns:
            List of root configuration item categories
        """
        filters = [QueryFilter(field="ParentCategoryID", op="eq", value=None)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_child_categories(
        self,
        parent_category_id: int,
        active_only: bool = True,
        recursive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get child categories of a specific parent category.

        Args:
            parent_category_id: ID of the parent category
            active_only: Whether to return only active categories
            recursive: Whether to include all descendants recursively
            limit: Maximum number of categories to return

        Returns:
            List of child categories
        """
        filters = [
            QueryFilter(field="ParentCategoryID", op="eq", value=parent_category_id)
        ]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        children = response.items

        if recursive:
            # Recursively get all descendants
            all_children = children.copy()
            for child in children:
                child_id = child.get("id")
                if child_id:
                    descendants = self.get_child_categories(
                        child_id, active_only, recursive=True
                    )
                    all_children.extend(descendants)
            return all_children

        return children

    def search_categories_by_name(
        self,
        search_text: str,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search configuration item categories by name.

        Args:
            search_text: Text to search for in category names
            active_only: Whether to return only active categories
            limit: Maximum number of categories to return

        Returns:
            List of categories containing the search text
        """
        filters = [QueryFilter(field="Name", op="contains", value=search_text)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_category_hierarchy_path(self, category_id: int) -> List[Dict[str, Any]]:
        """
        Get the full hierarchy path from root to the specified category.

        Args:
            category_id: ID of the category

        Returns:
            List of categories from root to target category
        """
        path = []
        current_id = category_id

        while current_id:
            category = self.get(current_id)
            if not category:
                break

            path.insert(0, category)
            current_id = category.get("ParentCategoryID")

        return path

    def update_category_name(self, category_id: int, new_name: str) -> Dict[str, Any]:
        """
        Update the name of a configuration item category.

        Args:
            category_id: ID of category to update
            new_name: New category name

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"Name": new_name})

    def activate_category(self, category_id: int) -> Dict[str, Any]:
        """
        Activate a configuration item category.

        Args:
            category_id: ID of category to activate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": True})

    def deactivate_category(self, category_id: int) -> Dict[str, Any]:
        """
        Deactivate a configuration item category.

        Args:
            category_id: ID of category to deactivate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": False})

    def get_category_usage_statistics(self, category_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a configuration item category.

        Args:
            category_id: ID of the category

        Returns:
            Dictionary with usage statistics
        """
        category = self.get(category_id)
        if not category:
            raise ValueError(f"Category with ID {category_id} not found")

        # Get configuration items using this category
        ci_filters = [
            QueryFilter(field="ConfigurationItemCategoryID", op="eq", value=category_id)
        ]
        ci_response = self.client.query("ConfigurationItems", filters=ci_filters)
        configuration_items = ci_response.get("items", [])

        # Get child categories
        child_categories = self.get_child_categories(category_id, active_only=False)

        statistics = {
            "category_id": category_id,
            "category_name": category.get("Name"),
            "direct_ci_count": len(configuration_items),
            "child_categories_count": len(child_categories),
            "is_active": category.get("IsActive"),
            "has_parent": bool(category.get("ParentCategoryID")),
            "configuration_items_by_type": {},
        }

        # Analyze CI types
        for ci in configuration_items:
            ci_type = ci.get("ConfigurationItemType", "Unknown")
            statistics["configuration_items_by_type"][ci_type] = (
                statistics["configuration_items_by_type"].get(ci_type, 0) + 1
            )

        # If has children, get recursive count
        if child_categories:
            total_descendant_ci_count = 0
            for child in child_categories:
                child_stats = self.get_category_usage_statistics(child.get("id"))
                total_descendant_ci_count += child_stats.get("total_ci_count", 0)

            statistics["total_ci_count"] = (
                statistics["direct_ci_count"] + total_descendant_ci_count
            )
        else:
            statistics["total_ci_count"] = statistics["direct_ci_count"]

        return statistics

    def move_category(
        self, category_id: int, new_parent_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Move a category to a new parent (or make it root-level).

        Args:
            category_id: ID of category to move
            new_parent_id: ID of new parent category (None for root level)

        Returns:
            Updated category data
        """
        update_data = {"ParentCategoryID": new_parent_id}
        return self.update_by_id(category_id, update_data)

    def _build_category_hierarchy(
        self, categories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build hierarchy structure for categories.

        Args:
            categories: Flat list of categories

        Returns:
            Categories with hierarchy information added
        """
        # Create lookup map
        category_map = {cat.get("id"): cat for cat in categories}

        # Add children information
        for category in categories:
            category["children"] = []
            parent_id = category.get("ParentCategoryID")
            if parent_id and parent_id in category_map:
                category_map[parent_id]["children"].append(category)

        return categories
