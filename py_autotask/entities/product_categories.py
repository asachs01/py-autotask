"""
ProductCategories entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ProductCategoriesEntity(BaseEntity):
    """
    Handles all Product Category-related operations for the Autotask API.

    Product Categories are used to organize and group products in a hierarchical structure.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_product_category(
        self,
        name: str,
        is_active: bool = True,
        parent_category_id: Optional[int] = None,
        display_color_rgb: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new product category.

        Args:
            name: Name of the product category
            is_active: Whether the category is active
            parent_category_id: ID of parent category (for subcategories)
            display_color_rgb: RGB color code for display
            description: Description of the category
            **kwargs: Additional category fields

        Returns:
            Created product category data
        """
        category_data = {
            "Name": name,
            "IsActive": is_active,
            **kwargs,
        }

        if parent_category_id:
            category_data["ParentCategoryID"] = parent_category_id
        if display_color_rgb:
            category_data["DisplayColorRGB"] = display_color_rgb
        if description:
            category_data["Description"] = description

        return self.create(category_data)

    def get_active_categories(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all active product categories.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of active product categories
        """
        filters = [QueryFilter(field="IsActive", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def get_root_categories(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all root-level categories (no parent).

        Args:
            limit: Maximum number of records to return

        Returns:
            List of root categories
        """
        filters = [QueryFilter(field="ParentCategoryID", op="eq", value=None)]

        return self.query(filters=filters, max_records=limit)

    def get_subcategories(
        self, parent_category_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all subcategories of a parent category.

        Args:
            parent_category_id: ID of the parent category
            limit: Maximum number of records to return

        Returns:
            List of subcategories
        """
        filters = [
            QueryFilter(field="ParentCategoryID", op="eq", value=parent_category_id)
        ]

        return self.query(filters=filters, max_records=limit)

    def search_categories_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for product categories by name.

        Args:
            name: Category name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching categories
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_category_hierarchy(self, category_id: int) -> Dict[str, Any]:
        """
        Get the full hierarchy path for a category.

        Args:
            category_id: ID of the category

        Returns:
            Dictionary with hierarchy information
        """
        category = self.get_by_id(category_id)
        if not category:
            return {}

        hierarchy = []
        current_category = category

        # Build hierarchy from current category up to root
        while current_category:
            hierarchy.insert(
                0,
                {
                    "id": current_category.get("id"),
                    "name": current_category.get("Name"),
                    "level": len(hierarchy),
                },
            )

            parent_id = current_category.get("ParentCategoryID")
            if parent_id:
                current_category = self.get_by_id(parent_id)
            else:
                current_category = None

        return {
            "category_id": category_id,
            "full_path": " > ".join([cat["name"] for cat in hierarchy]),
            "hierarchy": hierarchy,
            "depth": len(hierarchy),
        }

    def get_category_tree(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get the complete category tree structure.

        Args:
            include_inactive: Whether to include inactive categories

        Returns:
            List representing the tree structure
        """
        # Get all categories
        filters = []
        if not include_inactive:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        all_categories = self.query(filters=filters)

        # Organize into tree structure
        category_dict = {cat["id"]: cat for cat in all_categories}

        def build_tree(parent_id=None):
            children = []
            for cat in all_categories:
                if cat.get("ParentCategoryID") == parent_id:
                    cat_node = {
                        "id": cat["id"],
                        "name": cat.get("Name"),
                        "is_active": cat.get("IsActive", True),
                        "description": cat.get("Description"),
                        "children": build_tree(cat["id"]),
                    }
                    children.append(cat_node)
            return children

        return build_tree()

    def update_category_status(self, category_id: int, is_active: bool) -> EntityDict:
        """
        Activate or deactivate a product category.

        Args:
            category_id: ID of the category
            is_active: Whether to activate or deactivate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": is_active})

    def move_category(
        self, category_id: int, new_parent_id: Optional[int]
    ) -> EntityDict:
        """
        Move a category to a different parent (or make it root level).

        Args:
            category_id: ID of the category to move
            new_parent_id: ID of new parent category (None for root level)

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"ParentCategoryID": new_parent_id})

    def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """
        Get all products in a specific category.

        Args:
            category_id: ID of the category

        Returns:
            List of products in the category
        """
        # This would typically query the Products entity
        filters = [QueryFilter(field="CategoryID", op="eq", value=category_id)]
        return self.client.query("Products", filters=filters)

    def get_category_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about product categories.

        Returns:
            Dictionary containing category statistics
        """
        all_categories = self.query()

        root_categories = [
            cat for cat in all_categories if not cat.get("ParentCategoryID")
        ]

        # Calculate hierarchy depth
        max_depth = 0
        for category in all_categories:
            hierarchy = self.get_category_hierarchy(category["id"])
            depth = hierarchy.get("depth", 0)
            max_depth = max(max_depth, depth)

        stats = {
            "total_categories": len(all_categories),
            "active_categories": len(
                [cat for cat in all_categories if cat.get("IsActive", False)]
            ),
            "inactive_categories": len(
                [cat for cat in all_categories if not cat.get("IsActive", False)]
            ),
            "root_categories": len(root_categories),
            "subcategories": len(all_categories) - len(root_categories),
            "max_hierarchy_depth": max_depth,
            "categories_with_description": len(
                [cat for cat in all_categories if cat.get("Description")]
            ),
        }

        return stats

    def get_categories_with_color(
        self, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get categories that have a display color assigned.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of categories with display colors
        """
        all_categories = self.query(max_records=limit)

        # Filter categories that have a display color
        colored_categories = [
            cat for cat in all_categories if cat.get("DisplayColorRGB")
        ]

        return colored_categories
