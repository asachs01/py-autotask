"""
InventoryStockedItems entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class InventoryStockedItemsEntity(BaseEntity):
    """
    Handles all Inventory Stocked Item-related operations for the Autotask API.

    Inventory Stocked Items represent items that are tracked in inventory at specific locations.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_stocked_item(
        self,
        product_id: int,
        location_id: int,
        quantity_on_hand: int = 0,
        quantity_committed: int = 0,
        quantity_available: int = 0,
        minimum_stock_level: Optional[int] = None,
        maximum_stock_level: Optional[int] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new inventory stocked item record.

        Args:
            product_id: ID of the product
            location_id: ID of the inventory location
            quantity_on_hand: Current quantity on hand
            quantity_committed: Quantity committed to orders
            quantity_available: Quantity available for use
            minimum_stock_level: Minimum stock level for reordering
            maximum_stock_level: Maximum stock level
            **kwargs: Additional stocked item fields

        Returns:
            Created stocked item data
        """
        stocked_item_data = {
            "ProductID": product_id,
            "LocationID": location_id,
            "QuantityOnHand": quantity_on_hand,
            "QuantityCommitted": quantity_committed,
            "QuantityAvailable": quantity_available,
            **kwargs,
        }

        if minimum_stock_level is not None:
            stocked_item_data["MinimumStockLevel"] = minimum_stock_level
        if maximum_stock_level is not None:
            stocked_item_data["MaximumStockLevel"] = maximum_stock_level

        return self.create(stocked_item_data)

    def get_stocked_items_by_location(
        self, location_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all stocked items at a specific location.

        Args:
            location_id: ID of the inventory location
            limit: Maximum number of records to return

        Returns:
            List of stocked items at the location
        """
        filters = [QueryFilter(field="LocationID", op="eq", value=location_id)]

        return self.query(filters=filters, max_records=limit)

    def get_stocked_items_by_product(
        self, product_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all stocked item records for a specific product.

        Args:
            product_id: ID of the product
            limit: Maximum number of records to return

        Returns:
            List of stocked item records for the product
        """
        filters = [QueryFilter(field="ProductID", op="eq", value=product_id)]

        return self.query(filters=filters, max_records=limit)

    def get_low_stock_items(
        self, location_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get items that are below their minimum stock level.

        Args:
            location_id: Optional location ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of items with low stock
        """
        # Note: This would need custom filtering logic since we need to compare
        # QuantityOnHand with MinimumStockLevel
        filters = []
        if location_id:
            filters.append(QueryFilter(field="LocationID", op="eq", value=location_id))

        all_items = self.query(filters=filters, max_records=limit)

        # Filter items where quantity on hand is less than minimum stock level
        low_stock_items = []
        for item in all_items:
            qty_on_hand = item.get("QuantityOnHand", 0)
            min_level = item.get("MinimumStockLevel")
            if min_level is not None and qty_on_hand < min_level:
                low_stock_items.append(item)

        return low_stock_items[:limit] if limit else low_stock_items

    def update_quantity_on_hand(
        self, stocked_item_id: int, new_quantity: int
    ) -> EntityDict:
        """
        Update the quantity on hand for a stocked item.

        Args:
            stocked_item_id: ID of the stocked item
            new_quantity: New quantity on hand

        Returns:
            Updated stocked item data
        """
        return self.update_by_id(stocked_item_id, {"QuantityOnHand": new_quantity})

    def adjust_stock_levels(
        self,
        stocked_item_id: int,
        minimum_level: Optional[int] = None,
        maximum_level: Optional[int] = None,
    ) -> EntityDict:
        """
        Adjust the minimum and maximum stock levels.

        Args:
            stocked_item_id: ID of the stocked item
            minimum_level: New minimum stock level
            maximum_level: New maximum stock level

        Returns:
            Updated stocked item data
        """
        update_data = {}
        if minimum_level is not None:
            update_data["MinimumStockLevel"] = minimum_level
        if maximum_level is not None:
            update_data["MaximumStockLevel"] = maximum_level

        return self.update_by_id(stocked_item_id, update_data)

    def commit_quantity(
        self, stocked_item_id: int, quantity_to_commit: int
    ) -> EntityDict:
        """
        Commit a quantity of stock (for orders, reservations, etc.).

        Args:
            stocked_item_id: ID of the stocked item
            quantity_to_commit: Quantity to commit

        Returns:
            Updated stocked item data
        """
        current_item = self.get_by_id(stocked_item_id)
        if not current_item:
            raise ValueError(f"Stocked item {stocked_item_id} not found")

        current_committed = current_item.get("QuantityCommitted", 0)
        new_committed = current_committed + quantity_to_commit

        return self.update_by_id(stocked_item_id, {"QuantityCommitted": new_committed})

    def release_committed_quantity(
        self, stocked_item_id: int, quantity_to_release: int
    ) -> EntityDict:
        """
        Release committed quantity back to available stock.

        Args:
            stocked_item_id: ID of the stocked item
            quantity_to_release: Quantity to release from commitment

        Returns:
            Updated stocked item data
        """
        current_item = self.get_by_id(stocked_item_id)
        if not current_item:
            raise ValueError(f"Stocked item {stocked_item_id} not found")

        current_committed = current_item.get("QuantityCommitted", 0)
        new_committed = max(0, current_committed - quantity_to_release)

        return self.update_by_id(stocked_item_id, {"QuantityCommitted": new_committed})

    def get_total_stock_by_product(self, product_id: int) -> Dict[str, int]:
        """
        Get total stock quantities across all locations for a product.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with total quantities
        """
        stocked_items = self.get_stocked_items_by_product(product_id)

        totals = {
            "total_on_hand": 0,
            "total_committed": 0,
            "total_available": 0,
        }

        for item in stocked_items:
            totals["total_on_hand"] += item.get("QuantityOnHand", 0)
            totals["total_committed"] += item.get("QuantityCommitted", 0)
            totals["total_available"] += item.get("QuantityAvailable", 0)

        return totals

    def get_inventory_value_by_location(self, location_id: int) -> Dict[str, Any]:
        """
        Calculate inventory value at a specific location.

        Args:
            location_id: ID of the inventory location

        Returns:
            Dictionary with inventory valuation data
        """
        stocked_items = self.get_stocked_items_by_location(location_id)

        # Note: This would need product cost information which might come from
        # a separate API call to get product details
        stats = {
            "total_items": len(stocked_items),
            "total_quantity_on_hand": sum(
                item.get("QuantityOnHand", 0) for item in stocked_items
            ),
            "total_quantity_committed": sum(
                item.get("QuantityCommitted", 0) for item in stocked_items
            ),
            "items_below_min_level": len(
                [
                    item
                    for item in stocked_items
                    if item.get("MinimumStockLevel")
                    and item.get("QuantityOnHand", 0) < item["MinimumStockLevel"]
                ]
            ),
        }

        return stats
