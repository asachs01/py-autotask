"""
UserDefinedFieldListItems entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class UserDefinedFieldListItemsEntity(BaseEntity):
    """
    Handles all User Defined Field List Item-related operations for the Autotask API.

    UserDefinedFieldListItems in Autotask represent the individual list options/values
    available for user-defined fields that are configured as dropdown lists or
    multi-select fields. These items define the selectable values for custom fields
    across various entities.
    """

    def __init__(self, client, entity_name="UserDefinedFieldListItems"):
        super().__init__(client, entity_name)

    def get_field_list_items(
        self, field_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all list items for a specific user-defined field.

        Args:
            field_id: ID of the user-defined field
            active_only: Whether to return only active items
            limit: Maximum number of items to return

        Returns:
            List of field list items

        Example:
            items = client.user_defined_field_list_items.get_field_list_items(123)
        """
        filters = [QueryFilter(field="UserDefinedFieldID", op="eq", value=field_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def search_items_by_value(
        self,
        search_value: str,
        exact_match: bool = False,
        field_id: Optional[int] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for list items by their value/text.

        Args:
            search_value: Value to search for
            exact_match: Whether to do exact match or partial match
            field_id: Optional field ID to limit search to specific field
            active_only: Whether to return only active items
            limit: Maximum number of items to return

        Returns:
            List of matching list items
        """
        op = "eq" if exact_match else "contains"
        filters = [QueryFilter(field="Value", op=op, value=search_value)]

        if field_id:
            filters.append(
                QueryFilter(field="UserDefinedFieldID", op="eq", value=field_id)
            )

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_items_by_sort_order(
        self,
        field_id: int,
        ascending: bool = True,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get field list items ordered by their sort order.

        Args:
            field_id: ID of the user-defined field
            ascending: Whether to sort in ascending order
            active_only: Whether to return only active items
            limit: Maximum number of items to return

        Returns:
            List of ordered list items
        """
        filters = [QueryFilter(field="UserDefinedFieldID", op="eq", value=field_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        # Note: Actual sorting would need to be done client-side if API doesn't support it
        items = self.query(filters=filters, max_records=limit)

        # Sort by SortOrder if available
        if items and "SortOrder" in items[0]:
            items.sort(key=lambda x: x.get("SortOrder", 0), reverse=not ascending)

        return items

    def create_list_item(
        self,
        field_id: int,
        value: str,
        display_value: Optional[str] = None,
        sort_order: Optional[int] = None,
        active: bool = True,
        is_default: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new list item for a user-defined field.

        Args:
            field_id: ID of the user-defined field
            value: The internal value of the list item
            display_value: Optional display text (uses value if not provided)
            sort_order: Optional sort order for the item
            active: Whether the item is active
            is_default: Whether this is a default selection

        Returns:
            Created list item record

        Example:
            item = client.user_defined_field_list_items.create_list_item(
                field_id=123,
                value="HIGH",
                display_value="High Priority",
                sort_order=1,
                is_default=True
            )
        """
        data = {
            "UserDefinedFieldID": field_id,
            "Value": value,
            "Active": active,
            "IsDefault": is_default,
        }

        if display_value:
            data["DisplayValue"] = display_value
        else:
            data["DisplayValue"] = value

        if sort_order is not None:
            data["SortOrder"] = sort_order

        return self.create(data)

    def get_default_items(
        self, field_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get default list items across fields or for a specific field.

        Args:
            field_id: Optional field ID to filter by
            limit: Maximum number of items to return

        Returns:
            List of default list items
        """
        filters = [
            QueryFilter(field="IsDefault", op="eq", value=True),
            QueryFilter(field="Active", op="eq", value=True),
        ]

        if field_id:
            filters.append(
                QueryFilter(field="UserDefinedFieldID", op="eq", value=field_id)
            )

        return self.query(filters=filters, max_records=limit)

    def bulk_create_list_items(
        self, field_id: int, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple list items for a field.

        Args:
            field_id: ID of the user-defined field
            items: List of item dictionaries with keys: value, display_value, sort_order, etc.

        Returns:
            List of created list item records

        Example:
            items_data = [
                {"value": "LOW", "display_value": "Low Priority", "sort_order": 1},
                {"value": "MEDIUM", "display_value": "Medium Priority", "sort_order": 2},
                {"value": "HIGH", "display_value": "High Priority", "sort_order": 3, "is_default": True}
            ]
            created = client.user_defined_field_list_items.bulk_create_list_items(123, items_data)
        """
        created_records = []

        for item_data in items:
            try:
                created_item = self.create_list_item(
                    field_id=field_id,
                    value=item_data["value"],
                    display_value=item_data.get("display_value"),
                    sort_order=item_data.get("sort_order"),
                    active=item_data.get("active", True),
                    is_default=item_data.get("is_default", False),
                )
                created_records.append(created_item)
            except Exception as e:
                self.logger.warning(
                    f"Failed to create list item {item_data.get('value')}: {e}"
                )

        return created_records

    def reorder_field_items(
        self, field_id: int, item_order: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Reorder list items for a field by updating their sort order.

        Args:
            field_id: ID of the user-defined field
            item_order: List of dictionaries with 'item_id' and 'sort_order' keys

        Returns:
            List of updated list item records

        Example:
            reorder_data = [
                {"item_id": 1, "sort_order": 3},
                {"item_id": 2, "sort_order": 1},
                {"item_id": 3, "sort_order": 2}
            ]
            updated = client.user_defined_field_list_items.reorder_field_items(123, reorder_data)
        """
        updated_records = []

        for item in item_order:
            try:
                item_id = item["item_id"]
                sort_order = item["sort_order"]

                updated_item = self.update(item_id, {"SortOrder": sort_order})
                updated_records.append(updated_item)
            except Exception as e:
                self.logger.warning(
                    f"Failed to update sort order for item {item.get('item_id')}: {e}"
                )

        return updated_records

    def get_unused_list_items(
        self,
        field_id: Optional[int] = None,
        days_unused: int = 90,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get list items that haven't been used recently.

        Args:
            field_id: Optional field ID to filter by
            days_unused: Number of days to look back for usage
            limit: Maximum number of items to return

        Returns:
            List of potentially unused list items

        Note:
            This method identifies potentially unused items based on last modified date.
            Actual usage tracking would require additional data sources.
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_unused)).strftime(
            "%Y-%m-%d"
        )
        filters = [
            QueryFilter(field="Active", op="eq", value=True),
            QueryFilter(field="LastModifiedDate", op="lt", value=cutoff_date),
        ]

        if field_id:
            filters.append(
                QueryFilter(field="UserDefinedFieldID", op="eq", value=field_id)
            )

        return self.query(filters=filters, max_records=limit)

    def consolidate_duplicate_values(
        self, field_id: int, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Identify and optionally consolidate duplicate values within a field.

        Args:
            field_id: ID of the user-defined field
            dry_run: If True, only identify duplicates without making changes

        Returns:
            Dictionary with consolidation analysis and results
        """
        # Get all items for the field
        all_items = self.get_field_list_items(field_id, active_only=False)

        # Group by value (case-insensitive)
        value_groups = {}
        for item in all_items:
            value = item.get("Value", "").lower()
            if value not in value_groups:
                value_groups[value] = []
            value_groups[value].append(item)

        # Identify duplicates
        duplicates = {k: v for k, v in value_groups.items() if len(v) > 1}

        consolidation_plan = []
        if not dry_run and duplicates:
            # For each duplicate group, keep the first active item and deactivate others
            for value, items in duplicates.items():
                active_items = [item for item in items if item.get("Active")]
                if len(active_items) > 1:
                    keep_item = active_items[0]  # Keep first active item
                    for duplicate_item in active_items[1:]:
                        try:
                            self.update(duplicate_item["id"], {"Active": False})
                            consolidation_plan.append(
                                {
                                    "action": "deactivated",
                                    "item_id": duplicate_item["id"],
                                    "value": duplicate_item.get("Value"),
                                    "kept_item_id": keep_item["id"],
                                }
                            )
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to deactivate duplicate item {duplicate_item['id']}: {e}"
                            )

        return {
            "field_id": field_id,
            "total_items": len(all_items),
            "duplicate_groups": len(duplicates),
            "duplicates_found": {k: len(v) for k, v in duplicates.items()},
            "dry_run": dry_run,
            "consolidation_actions": consolidation_plan if not dry_run else [],
            "recommendations": self._generate_consolidation_recommendations(duplicates),
        }

    def _generate_consolidation_recommendations(
        self, duplicates: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Generate recommendations for duplicate consolidation."""
        recommendations = []

        if duplicates:
            recommendations.append(
                f"Found {len(duplicates)} duplicate value groups that should be consolidated"
            )

            high_impact_duplicates = [k for k, v in duplicates.items() if len(v) > 3]
            if high_impact_duplicates:
                recommendations.append(
                    f"High-impact duplicates with 4+ items: {', '.join(high_impact_duplicates)}"
                )

        recommendations.extend(
            [
                "Consider implementing value validation to prevent future duplicates",
                "Review field usage patterns to optimize list item organization",
                "Establish naming conventions for new list items",
            ]
        )

        return recommendations

    def get_field_usage_statistics(self, field_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a user-defined field's list items.

        Args:
            field_id: ID of the user-defined field

        Returns:
            Dictionary with usage statistics
        """
        items = self.get_field_list_items(field_id, active_only=False)

        if not items:
            return {
                "field_id": field_id,
                "total_items": 0,
                "active_items": 0,
                "default_items": 0,
                "statistics": {},
            }

        active_count = sum(1 for item in items if item.get("Active"))
        default_count = sum(1 for item in items if item.get("IsDefault"))

        # Analyze sort order distribution
        sort_orders = [
            item.get("SortOrder", 0)
            for item in items
            if item.get("SortOrder") is not None
        ]
        has_gaps_in_sort = False
        if sort_orders:
            sort_orders.sort()
            expected_orders = list(range(1, len(sort_orders) + 1))
            has_gaps_in_sort = sort_orders != expected_orders

        return {
            "field_id": field_id,
            "total_items": len(items),
            "active_items": active_count,
            "inactive_items": len(items) - active_count,
            "default_items": default_count,
            "has_sort_order_gaps": has_gaps_in_sort,
            "sort_order_range": {
                "min": min(sort_orders) if sort_orders else None,
                "max": max(sort_orders) if sort_orders else None,
            },
            "health_score": min(
                100,
                (active_count * 20)
                + (50 if default_count > 0 else 0)
                + (30 if not has_gaps_in_sort else 0),
            ),
            "recommendations": self._generate_usage_recommendations(
                active_count, default_count, has_gaps_in_sort
            ),
        }

    def _generate_usage_recommendations(
        self, active_count: int, default_count: int, has_gaps: bool
    ) -> List[str]:
        """Generate recommendations for field usage optimization."""
        recommendations = []

        if active_count == 0:
            recommendations.append("No active items found - field may be unused")
        elif active_count > 20:
            recommendations.append(
                "Large number of active items - consider categorization"
            )

        if default_count == 0:
            recommendations.append(
                "No default items set - consider setting a default value"
            )
        elif default_count > 3:
            recommendations.append("Multiple default items may cause confusion")

        if has_gaps:
            recommendations.append(
                "Sort order has gaps - consider renumbering for consistency"
            )

        return recommendations
