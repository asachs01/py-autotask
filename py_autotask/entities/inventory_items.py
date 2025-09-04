"""
Inventory Items entity for Autotask API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class InventoryItemsEntity(BaseEntity):
    """
    Handles Inventory Item operations for the Autotask API.

    Manages inventory tracking, stock levels, and item management
    for physical goods and assets in the Autotask system.
    """

    def __init__(self, client, entity_name: str = "InventoryItems"):
        super().__init__(client, entity_name)

    def create_inventory_item(
        self,
        name: str,
        description: str,
        product_id: int,
        location_id: int,
        quantity_on_hand: int = 0,
        minimum_stock_level: Optional[int] = None,
        serial_number: Optional[str] = None,
        cost: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new inventory item.

        Args:
            name: Item name/identifier
            description: Item description
            product_id: Associated product ID
            location_id: Storage location ID
            quantity_on_hand: Current quantity in stock
            minimum_stock_level: Minimum stock level for reordering
            serial_number: Optional serial number for tracking
            cost: Item cost/value
            **kwargs: Additional item fields

        Returns:
            Created inventory item data
        """
        item_data = {
            "Name": name,
            "Description": description,
            "ProductID": product_id,
            "LocationID": location_id,
            "QuantityOnHand": quantity_on_hand,
            **kwargs,
        }

        if minimum_stock_level is not None:
            item_data["MinimumStockLevel"] = minimum_stock_level

        if serial_number:
            item_data["SerialNumber"] = serial_number

        if cost is not None:
            item_data["Cost"] = cost

        return self.create(item_data)

    def get_items_by_location(
        self,
        location_id: int,
        include_zero_stock: bool = True,
    ) -> EntityList:
        """
        Get all inventory items at a specific location.

        Args:
            location_id: Location ID to filter by
            include_zero_stock: Whether to include items with zero stock

        Returns:
            List of inventory items at the location
        """
        filters = [{"field": "LocationID", "op": "eq", "value": str(location_id)}]

        if not include_zero_stock:
            filters.append({"field": "QuantityOnHand", "op": "gt", "value": "0"})

        return self.query_all(filters=filters)

    def get_items_by_product(
        self,
        product_id: int,
        location_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get all inventory items for a specific product.

        Args:
            product_id: Product ID to filter by
            location_id: Optional location filter

        Returns:
            List of inventory items for the product
        """
        filters = [{"field": "ProductID", "op": "eq", "value": str(product_id)}]

        if location_id is not None:
            filters.append(
                {"field": "LocationID", "op": "eq", "value": str(location_id)}
            )

        return self.query_all(filters=filters)

    def get_low_stock_items(
        self,
        location_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get inventory items that are below minimum stock level.

        Args:
            location_id: Optional location filter

        Returns:
            List of low stock items
        """
        # This requires a complex filter comparing two fields
        # For now, we'll get all items and filter programmatically
        filters = []
        if location_id is not None:
            filters.append(
                {"field": "LocationID", "op": "eq", "value": str(location_id)}
            )

        all_items = self.query_all(filters=filters)
        low_stock_items = []

        for item in all_items:
            quantity_on_hand = int(item.get("QuantityOnHand", 0))
            minimum_stock = item.get("MinimumStockLevel")

            if minimum_stock is not None and quantity_on_hand <= int(minimum_stock):
                low_stock_items.append(item)

        return low_stock_items

    def get_out_of_stock_items(
        self,
        location_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get inventory items that are out of stock.

        Args:
            location_id: Optional location filter

        Returns:
            List of out of stock items
        """
        filters = [{"field": "QuantityOnHand", "op": "eq", "value": "0"}]

        if location_id is not None:
            filters.append(
                {"field": "LocationID", "op": "eq", "value": str(location_id)}
            )

        return self.query_all(filters=filters)

    def adjust_inventory_quantity(
        self,
        item_id: int,
        quantity_change: int,
        reason: str,
        reference: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Adjust the quantity of an inventory item.

        Args:
            item_id: Inventory item ID
            quantity_change: Change in quantity (positive or negative)
            reason: Reason for the adjustment
            reference: Optional reference (PO number, ticket, etc.)

        Returns:
            Updated inventory item data
        """
        current_item = self.get(item_id)
        if not current_item:
            return None

        current_quantity = int(current_item.get("QuantityOnHand", 0))
        new_quantity = max(0, current_quantity + quantity_change)

        # Create adjustment record (this would typically be in a separate table)
        adjustment_note = f"Qty adjusted by {quantity_change} ({reason})"
        if reference:
            adjustment_note += f" - Ref: {reference}"

        update_data = {
            "QuantityOnHand": new_quantity,
            "LastAdjustmentDate": datetime.now().isoformat(),
            "LastAdjustmentNote": adjustment_note,
        }

        return self.update_by_id(item_id, update_data)

    def receive_inventory(
        self,
        item_id: int,
        quantity_received: int,
        purchase_order_id: Optional[int] = None,
        cost: Optional[float] = None,
    ) -> Optional[EntityDict]:
        """
        Receive inventory items (increase stock).

        Args:
            item_id: Inventory item ID
            quantity_received: Quantity being received
            purchase_order_id: Optional purchase order reference
            cost: Optional cost per unit

        Returns:
            Updated inventory item data
        """
        reference = f"PO {purchase_order_id}" if purchase_order_id else "Manual Receipt"

        result = self.adjust_inventory_quantity(
            item_id, quantity_received, "Stock Receipt", reference
        )

        # Update cost if provided
        if result and cost is not None:
            self.update_by_id(item_id, {"Cost": cost})
            result = self.get(item_id)

        return result

    def issue_inventory(
        self,
        item_id: int,
        quantity_issued: int,
        ticket_id: Optional[int] = None,
        project_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Issue inventory items (decrease stock).

        Args:
            item_id: Inventory item ID
            quantity_issued: Quantity being issued
            ticket_id: Optional ticket reference
            project_id: Optional project reference
            notes: Optional issue notes

        Returns:
            Updated inventory item data
        """
        reason = "Stock Issue"
        if notes:
            reason += f" - {notes}"

        reference = None
        if ticket_id:
            reference = f"Ticket {ticket_id}"
        elif project_id:
            reference = f"Project {project_id}"

        return self.adjust_inventory_quantity(
            item_id, -quantity_issued, reason, reference
        )

    def transfer_inventory(
        self,
        item_id: int,
        from_location_id: int,
        to_location_id: int,
        quantity: int,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transfer inventory between locations.

        Args:
            item_id: Inventory item ID at source location
            from_location_id: Source location ID
            to_location_id: Destination location ID
            quantity: Quantity to transfer
            reason: Optional transfer reason

        Returns:
            Dictionary with transfer results
        """
        result = {
            "success": False,
            "source_item": None,
            "destination_item": None,
            "error": None,
        }

        try:
            # Get source item
            source_item = self.get(item_id)
            if not source_item:
                result["error"] = "Source item not found"
                return result

            if int(source_item.get("LocationID", 0)) != from_location_id:
                result["error"] = "Item is not at the specified source location"
                return result

            current_quantity = int(source_item.get("QuantityOnHand", 0))
            if current_quantity < quantity:
                result["error"] = (
                    f"Insufficient stock (available: {current_quantity}, requested: {quantity})"
                )
                return result

            # Find or create destination item
            product_id = source_item.get("ProductID")
            dest_items = self.get_items_by_product(product_id, to_location_id)

            destination_item = None
            if dest_items:
                # Use existing item at destination
                destination_item = dest_items[0]
            else:
                # Create new item at destination
                dest_data = {
                    "Name": source_item.get("Name"),
                    "Description": source_item.get("Description"),
                    "ProductID": product_id,
                    "LocationID": to_location_id,
                    "QuantityOnHand": 0,
                    "Cost": source_item.get("Cost"),
                    "MinimumStockLevel": source_item.get("MinimumStockLevel"),
                }
                destination_item = self.create(dest_data)

            # Perform transfer
            transfer_reason = reason or "Inventory Transfer"

            # Remove from source
            source_updated = self.adjust_inventory_quantity(
                item_id, -quantity, transfer_reason, f"To Location {to_location_id}"
            )

            # Add to destination
            dest_updated = self.adjust_inventory_quantity(
                int(destination_item["id"]),
                quantity,
                transfer_reason,
                f"From Location {from_location_id}",
            )

            if source_updated and dest_updated:
                result["success"] = True
                result["source_item"] = source_updated
                result["destination_item"] = dest_updated
            else:
                result["error"] = "Transfer failed during update"

        except Exception as e:
            result["error"] = f"Transfer error: {str(e)}"

        return result

    def get_inventory_valuation(
        self,
        location_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate inventory valuation.

        Args:
            location_id: Optional location filter
            product_id: Optional product filter

        Returns:
            Dictionary with valuation information
        """
        filters = []
        if location_id is not None:
            filters.append(
                {"field": "LocationID", "op": "eq", "value": str(location_id)}
            )
        if product_id is not None:
            filters.append({"field": "ProductID", "op": "eq", "value": str(product_id)})

        items = self.query_all(filters=filters)

        valuation = {
            "total_items": len(items),
            "total_quantity": 0,
            "total_value": 0.0,
            "items_with_cost": 0,
            "items_without_cost": 0,
            "zero_stock_items": 0,
            "by_location": {},
            "by_product": {},
        }

        for item in items:
            quantity = int(item.get("QuantityOnHand", 0))
            cost = item.get("Cost")
            location_id = item.get("LocationID")
            product_id = item.get("ProductID")

            valuation["total_quantity"] += quantity

            if quantity == 0:
                valuation["zero_stock_items"] += 1

            if cost is not None and cost != 0:
                item_value = quantity * float(cost)
                valuation["total_value"] += item_value
                valuation["items_with_cost"] += 1
            else:
                valuation["items_without_cost"] += 1

            # Group by location
            if location_id not in valuation["by_location"]:
                valuation["by_location"][location_id] = {
                    "quantity": 0,
                    "value": 0.0,
                    "items": 0,
                }
            valuation["by_location"][location_id]["quantity"] += quantity
            valuation["by_location"][location_id]["items"] += 1
            if cost is not None:
                valuation["by_location"][location_id]["value"] += quantity * float(cost)

            # Group by product
            if product_id not in valuation["by_product"]:
                valuation["by_product"][product_id] = {
                    "quantity": 0,
                    "value": 0.0,
                    "items": 0,
                }
            valuation["by_product"][product_id]["quantity"] += quantity
            valuation["by_product"][product_id]["items"] += 1
            if cost is not None:
                valuation["by_product"][product_id]["value"] += quantity * float(cost)

        return valuation

    def get_inventory_movement_report(
        self,
        days: int = 30,
        location_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate inventory movement report.

        Note: This assumes movement history is tracked separately.

        Args:
            days: Number of days to analyze
            location_id: Optional location filter

        Returns:
            Dictionary with movement analysis
        """
        # This would typically query movement/transaction history
        # For now, provide a placeholder report structure

        filters = []
        if location_id is not None:
            filters.append(
                {"field": "LocationID", "op": "eq", "value": str(location_id)}
            )

        current_items = self.query_all(filters=filters)

        report = {
            "period_days": days,
            "total_items": len(current_items),
            "items_with_movement": 0,  # Placeholder
            "total_receipts": 0,  # Placeholder
            "total_issues": 0,  # Placeholder
            "total_adjustments": 0,  # Placeholder
            "fast_moving_items": [],  # Top movers
            "slow_moving_items": [],  # Items with no movement
            "location_id": location_id,
        }

        # Placeholder logic - in practice, this would analyze actual movement data
        for item in current_items:
            last_adjustment = item.get("LastAdjustmentDate")
            if last_adjustment:
                # Check if recent adjustment
                try:
                    adj_date = datetime.fromisoformat(
                        last_adjustment.replace("Z", "+00:00")
                    )
                    if (datetime.now() - adj_date).days <= days:
                        report["items_with_movement"] += 1
                except (ValueError, TypeError):
                    pass

        return report

    def search_inventory_by_serial(self, serial_number: str) -> EntityList:
        """
        Search inventory items by serial number.

        Args:
            serial_number: Serial number to search for

        Returns:
            List of matching inventory items
        """
        filters = [{"field": "SerialNumber", "op": "eq", "value": serial_number}]
        return self.query_all(filters=filters)

    def get_reorder_recommendations(
        self, location_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get reorder recommendations based on minimum stock levels.

        Args:
            location_id: Optional location filter

        Returns:
            List of reorder recommendations
        """
        low_stock_items = self.get_low_stock_items(location_id)

        recommendations = []
        for item in low_stock_items:
            current_qty = int(item.get("QuantityOnHand", 0))
            minimum_stock = int(item.get("MinimumStockLevel", 0))

            # Simple reorder logic: order 2x minimum stock level
            suggested_order_qty = (minimum_stock * 2) - current_qty

            recommendation = {
                "item_id": item.get("id"),
                "item_name": item.get("Name"),
                "product_id": item.get("ProductID"),
                "location_id": item.get("LocationID"),
                "current_quantity": current_qty,
                "minimum_stock": minimum_stock,
                "suggested_order_quantity": suggested_order_qty,
                "estimated_cost": None,
            }

            # Calculate estimated cost if available
            cost = item.get("Cost")
            if cost:
                recommendation["estimated_cost"] = suggested_order_qty * float(cost)

            recommendations.append(recommendation)

        # Sort by urgency (lowest stock first)
        recommendations.sort(key=lambda x: x["current_quantity"])

        return recommendations
