"""
Ticket Categories entity for Autotask API.

This module provides the TicketCategoriesEntity class for managing
ticket categorization and classification within the Autotask service desk.
"""

from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class TicketCategoriesEntity(BaseEntity):
    """
    Entity for managing Autotask Ticket Categories.

    Ticket Categories provide hierarchical organization and classification
    for service desk tickets, enabling better routing and reporting.
    """

    def __init__(self, client, entity_name="TicketCategories"):
        """Initialize the Ticket Categories entity."""
        super().__init__(client, entity_name)

    def create(self, category_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new ticket category.

        Args:
            category_data: Dictionary containing category information
                Required fields:
                - name: Name of the category
                - active: Whether the category is active
                Optional fields:
                - parentCategoryID: ID of parent category for hierarchy
                - description: Description of the category
                - color: Color code for the category
                - sortOrder: Sort order for display
                - isDefault: Whether this is a default category
                - globalDefault: Whether this is the global default

        Returns:
            CreateResponse: Response containing created category data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["name", "active"]
        self._validate_required_fields(category_data, required_fields)

        return self._create(category_data)

    def get(self, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ticket category by ID.

        Args:
            category_id: The category ID

        Returns:
            Dictionary containing category data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(category_id)

    def update(self, category_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing ticket category.

        Args:
            category_id: The category ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated category data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(category_id, update_data)

    def delete(self, category_id: int) -> bool:
        """
        Delete a ticket category.

        Args:
            category_id: The category ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(category_id)

    def get_active_categories(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all active ticket categories.

        Args:
            include_inactive: Whether to include inactive categories

        Returns:
            List of active categories
        """
        filters = []

        if not include_inactive:
            filters.append(QueryFilter(field="active", op="eq", value=True))

        return self.query(filters=filters)

    def get_category_hierarchy(
        self, parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get category hierarchy starting from a parent category.

        Args:
            parent_id: Parent category ID (None for root categories)

        Returns:
            List of categories in hierarchical order
        """
        if parent_id is None:
            # Get root categories (no parent)
            filters = [QueryFilter(field="parentCategoryID", op="eq", value=None)]
        else:
            # Get child categories
            filters = [QueryFilter(field="parentCategoryID", op="eq", value=parent_id)]

        return self.query(filters=filters)

    def get_category_path(self, category_id: int) -> List[Dict[str, Any]]:
        """
        Get the full path from root to the specified category.

        Args:
            category_id: Category ID to get path for

        Returns:
            List of categories from root to specified category
        """
        path = []
        current_id = category_id

        # Build path by walking up the hierarchy
        max_depth = 10  # Prevent infinite loops
        depth = 0

        while current_id and depth < max_depth:
            category = self.get(current_id)
            if not category:
                break

            path.insert(0, category)  # Insert at beginning to build path from root
            current_id = category.get("parentCategoryID")
            depth += 1

        return path

    def get_subcategories(
        self, category_id: int, recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all subcategories for a given category.

        Args:
            category_id: Parent category ID
            recursive: Whether to get subcategories recursively

        Returns:
            List of subcategories
        """
        filters = [QueryFilter(field="parentCategoryID", op="eq", value=category_id)]
        subcategories = self.query(filters=filters)

        if recursive:
            all_subcategories = subcategories.copy()

            for subcat in subcategories:
                sub_id = subcat.get("id")
                if sub_id:
                    deeper_subs = self.get_subcategories(sub_id, recursive=True)
                    all_subcategories.extend(deeper_subs)

            return all_subcategories

        return subcategories

    def create_category_hierarchy(
        self, hierarchy_data: Dict[str, Any]
    ) -> List[CreateResponse]:
        """
        Create a hierarchy of categories.

        Args:
            hierarchy_data: Dictionary defining the hierarchy structure
                Format: {
                    'name': 'Root Category',
                    'children': [
                        {'name': 'Child 1'},
                        {'name': 'Child 2', 'children': [...]}
                    ]
                }

        Returns:
            List of create responses for all created categories
        """
        results = []

        def create_category_recursive(
            category_data: Dict[str, Any], parent_id: Optional[int] = None
        ):
            # Prepare category data
            cat_data = {
                "name": category_data["name"],
                "active": category_data.get("active", True),
                "description": category_data.get("description", ""),
            }

            if parent_id:
                cat_data["parentCategoryID"] = parent_id

            # Create the category
            result = self.create(cat_data)
            results.append(result)

            # Create children if they exist
            children = category_data.get("children", [])
            created_id = result.item_id if hasattr(result, "item_id") else None

            for child in children:
                create_category_recursive(child, created_id)

        create_category_recursive(hierarchy_data)
        return results

    def move_category(
        self, category_id: int, new_parent_id: Optional[int]
    ) -> UpdateResponse:
        """
        Move a category to a new parent.

        Args:
            category_id: ID of category to move
            new_parent_id: ID of new parent (None for root level)

        Returns:
            Updated category data
        """
        update_data = {"parentCategoryID": new_parent_id}
        return self.update(category_id, update_data)

    def set_category_order(
        self, category_orders: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Set the sort order for multiple categories.

        Args:
            category_orders: List of dictionaries with 'id' and 'sortOrder'

        Returns:
            List of update responses
        """
        results = []

        for order_data in category_orders:
            category_id = order_data.get("id")
            sort_order = order_data.get("sortOrder")

            if category_id and sort_order is not None:
                update_data = {"sortOrder": sort_order}
                result = self.update(category_id, update_data)
                results.append(result)

        return results

    def get_category_usage_stats(
        self, category_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a category.

        Args:
            category_id: Category ID to get stats for
            date_range: Optional date range for ticket counts

        Returns:
            Dictionary with usage statistics
        """
        # Build filter for tickets in this category
        filters = [QueryFilter(field="ticketCategory", op="eq", value=category_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        # Query tickets in this category
        tickets = self.client.query("Tickets", filters=filters)

        # Calculate statistics
        stats = {
            "category_id": category_id,
            "total_tickets": len(tickets),
            "open_tickets": 0,
            "closed_tickets": 0,
            "avg_resolution_time": 0,
            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
            "by_status": {},
        }

        resolution_times = []

        for ticket in tickets:
            status = ticket.get("status", 1)
            priority = ticket.get("priority", 4)

            # Count by status
            if status in [5, 6]:  # Closed/Complete statuses
                stats["closed_tickets"] += 1
            else:
                stats["open_tickets"] += 1

            # Count by priority
            if priority in stats["by_priority"]:
                stats["by_priority"][priority] += 1

            # Count by status
            status_name = f"status_{status}"
            stats["by_status"][status_name] = stats["by_status"].get(status_name, 0) + 1

            # Calculate resolution time for closed tickets
            if status in [5, 6]:
                create_date = ticket.get("createDate")
                close_date = ticket.get("lastActivityDate")

                if create_date and close_date:
                    try:
                        from datetime import datetime

                        created = datetime.fromisoformat(
                            create_date.replace("Z", "+00:00")
                        )
                        closed = datetime.fromisoformat(
                            close_date.replace("Z", "+00:00")
                        )
                        resolution_time = (
                            closed - created
                        ).total_seconds() / 3600  # Hours
                        resolution_times.append(resolution_time)
                    except ValueError:
                        pass

        # Calculate average resolution time
        if resolution_times:
            stats["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)

        return stats

    def get_category_tree(self) -> Dict[str, Any]:
        """
        Get the complete category tree structure.

        Returns:
            Dictionary representing the category tree
        """
        # Get all categories
        all_categories = self.get_active_categories(include_inactive=True)

        # Build tree structure
        _ = {cat["id"]: cat for cat in all_categories}
        tree = []

        def build_tree_node(category: Dict[str, Any]) -> Dict[str, Any]:
            node = {
                "id": category["id"],
                "name": category["name"],
                "active": category.get("active", True),
                "description": category.get("description", ""),
                "children": [],
            }

            # Find children
            for cat in all_categories:
                if cat.get("parentCategoryID") == category["id"]:
                    child_node = build_tree_node(cat)
                    node["children"].append(child_node)

            return node

        # Build tree starting from root categories
        for category in all_categories:
            if not category.get("parentCategoryID"):  # Root category
                tree_node = build_tree_node(category)
                tree.append(tree_node)

        return {"categories": tree, "total_count": len(all_categories)}

    def validate_category_data(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate category data.

        Args:
            category_data: Category data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["name", "active"]
        for field in required_fields:
            if field not in category_data or category_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate name
        name = category_data.get("name", "")
        if name:
            if len(name) < 2:
                errors.append("Category name must be at least 2 characters")
            elif len(name) > 100:
                errors.append("Category name must not exceed 100 characters")

        # Validate parent category exists
        parent_id = category_data.get("parentCategoryID")
        if parent_id:
            try:
                parent_category = self.get(parent_id)
                if not parent_category:
                    errors.append(f"Parent category {parent_id} does not exist")
                elif not parent_category.get("active", True):
                    warnings.append("Parent category is inactive")
            except Exception as e:
                errors.append(f"Cannot validate parent category: {e}")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
