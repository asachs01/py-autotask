"""
Purchase Order Items entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class PurchaseOrderItemsEntity(BaseEntity):
    """
    Handles Purchase Order Item operations for the Autotask API.

    Manages individual line items within purchase orders, including
    products, quantities, pricing, and receiving status.
    """

    def __init__(self, client, entity_name: str = "PurchaseOrderItems"):
        super().__init__(client, entity_name)

    def create_purchase_order_item(
        self,
        purchase_order_id: int,
        product_id: int,
        quantity_ordered: float,
        unit_cost: float,
        description: Optional[str] = None,
        memo: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new purchase order item.

        Args:
            purchase_order_id: ID of the purchase order
            product_id: ID of the product being ordered
            quantity_ordered: Quantity being ordered
            unit_cost: Cost per unit
            description: Optional item description
            memo: Optional memo/notes
            **kwargs: Additional item fields

        Returns:
            Created purchase order item data
        """
        item_data = {
            "PurchaseOrderID": purchase_order_id,
            "ProductID": product_id,
            "QuantityOrdered": quantity_ordered,
            "UnitCost": unit_cost,
            **kwargs,
        }

        if description:
            item_data["Description"] = description

        if memo:
            item_data["Memo"] = memo

        return self.create(item_data)

    def get_items_by_purchase_order(self, purchase_order_id: int) -> EntityList:
        """
        Get all items for a specific purchase order.

        Args:
            purchase_order_id: Purchase order ID

        Returns:
            List of purchase order items
        """
        filters = [
            {"field": "PurchaseOrderID", "op": "eq", "value": str(purchase_order_id)}
        ]
        return self.query_all(filters=filters)

    def get_items_by_product(
        self,
        product_id: int,
        days: Optional[int] = None,
    ) -> EntityList:
        """
        Get all purchase order items for a specific product.

        Args:
            product_id: Product ID
            days: Optional filter for recent orders (last N days)

        Returns:
            List of purchase order items
        """
        filters = [{"field": "ProductID", "op": "eq", "value": str(product_id)}]

        if days is not None:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            filters.append(
                {"field": "CreateDate", "op": "gte", "value": cutoff_date.isoformat()}
            )

        return self.query_all(filters=filters)

    def update_item_quantity(
        self, item_id: int, quantity_ordered: float
    ) -> Optional[EntityDict]:
        """
        Update the quantity ordered for a purchase order item.

        Args:
            item_id: Purchase order item ID
            quantity_ordered: New quantity ordered

        Returns:
            Updated item data
        """
        return self.update_by_id(item_id, {"QuantityOrdered": quantity_ordered})

    def update_item_cost(self, item_id: int, unit_cost: float) -> Optional[EntityDict]:
        """
        Update the unit cost for a purchase order item.

        Args:
            item_id: Purchase order item ID
            unit_cost: New unit cost

        Returns:
            Updated item data
        """
        return self.update_by_id(item_id, {"UnitCost": unit_cost})

    def update_item_receiving_status(
        self,
        item_id: int,
        quantity_received: float,
        received_date: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Update the receiving status of a purchase order item.

        Args:
            item_id: Purchase order item ID
            quantity_received: Quantity received
            received_date: Date received (ISO format)

        Returns:
            Updated item data
        """
        update_data = {"QuantityReceived": quantity_received}

        if received_date:
            update_data["ReceivedDate"] = received_date
        else:
            from datetime import datetime

            update_data["ReceivedDate"] = datetime.now().isoformat()

        return self.update_by_id(item_id, update_data)

    def get_pending_items(self, purchase_order_id: Optional[int] = None) -> EntityList:
        """
        Get purchase order items that are pending receipt.

        Args:
            purchase_order_id: Optional purchase order filter

        Returns:
            List of pending items
        """
        # Items where quantity received is less than quantity ordered
        filters = []

        if purchase_order_id:
            filters.append(
                {
                    "field": "PurchaseOrderID",
                    "op": "eq",
                    "value": str(purchase_order_id),
                }
            )

        # This would need a more complex filter for quantity comparison
        # For now, we'll return items where QuantityReceived is null or 0
        filters.append({"field": "QuantityReceived", "op": "eq", "value": "0"})

        return self.query_all(filters=filters)

    def get_overdue_items(
        self, days_overdue: int = 7, purchase_order_id: Optional[int] = None
    ) -> EntityList:
        """
        Get purchase order items that are overdue for receiving.

        Args:
            days_overdue: Number of days past expected date to consider overdue
            purchase_order_id: Optional purchase order filter

        Returns:
            List of overdue items
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days_overdue)
        filters = [
            {
                "field": "ExpectedReceiveDate",
                "op": "lt",
                "value": cutoff_date.isoformat(),
            },
            {"field": "QuantityReceived", "op": "eq", "value": "0"},  # Still pending
        ]

        if purchase_order_id:
            filters.append(
                {
                    "field": "PurchaseOrderID",
                    "op": "eq",
                    "value": str(purchase_order_id),
                }
            )

        return self.query_all(filters=filters)

    def calculate_item_totals(self, item_data: EntityDict) -> Dict[str, float]:
        """
        Calculate totals for a purchase order item.

        Args:
            item_data: Purchase order item data

        Returns:
            Dictionary with calculated totals
        """
        quantity = float(item_data.get("QuantityOrdered", 0))
        unit_cost = float(item_data.get("UnitCost", 0))

        line_total = quantity * unit_cost

        # Calculate received totals if applicable
        quantity_received = float(item_data.get("QuantityReceived", 0))
        received_total = quantity_received * unit_cost

        # Calculate pending amounts
        quantity_pending = quantity - quantity_received
        pending_total = quantity_pending * unit_cost

        return {
            "line_total": line_total,
            "received_total": received_total,
            "pending_total": pending_total,
            "quantity_pending": quantity_pending,
        }

    def get_purchase_order_summary(self, purchase_order_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of all items in a purchase order.

        Args:
            purchase_order_id: Purchase order ID

        Returns:
            Dictionary with purchase order item summary
        """
        items = self.get_items_by_purchase_order(purchase_order_id)

        summary = {
            "total_items": len(items),
            "total_ordered_value": 0.0,
            "total_received_value": 0.0,
            "total_pending_value": 0.0,
            "items_fully_received": 0,
            "items_partially_received": 0,
            "items_pending": 0,
            "unique_products": set(),
        }

        for item in items:
            totals = self.calculate_item_totals(item)

            # Add to summary totals
            summary["total_ordered_value"] += totals["line_total"]
            summary["total_received_value"] += totals["received_total"]
            summary["total_pending_value"] += totals["pending_total"]

            # Count item statuses
            quantity_ordered = float(item.get("QuantityOrdered", 0))
            quantity_received = float(item.get("QuantityReceived", 0))

            if quantity_received >= quantity_ordered:
                summary["items_fully_received"] += 1
            elif quantity_received > 0:
                summary["items_partially_received"] += 1
            else:
                summary["items_pending"] += 1

            # Track unique products
            if item.get("ProductID"):
                summary["unique_products"].add(int(item["ProductID"]))

        summary["unique_products_count"] = len(summary["unique_products"])
        del summary["unique_products"]  # Remove set from final output

        return summary

    def bulk_receive_items(
        self,
        item_updates: List[Dict[str, Any]],
        received_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bulk update receiving status for multiple items.

        Args:
            item_updates: List of dictionaries with item_id and quantity_received
            received_date: Date received (ISO format)

        Returns:
            Dictionary with bulk update results
        """
        if not received_date:
            from datetime import datetime

            received_date = datetime.now().isoformat()

        results = {
            "updated_items": [],
            "failed_items": [],
            "total_processed": len(item_updates),
        }

        for update in item_updates:
            try:
                item_id = update["item_id"]
                quantity_received = update["quantity_received"]

                updated_item = self.update_item_receiving_status(
                    item_id, quantity_received, received_date
                )

                if updated_item:
                    results["updated_items"].append(
                        {
                            "item_id": item_id,
                            "quantity_received": quantity_received,
                            "updated_data": updated_item,
                        }
                    )
                else:
                    results["failed_items"].append(
                        {
                            "item_id": item_id,
                            "error": "Update returned no data",
                        }
                    )

            except Exception as e:
                results["failed_items"].append(
                    {
                        "item_id": update.get("item_id", "unknown"),
                        "error": str(e),
                    }
                )

        return results

    def get_cost_variance_report(self, purchase_order_id: int) -> Dict[str, Any]:
        """
        Generate a cost variance report for a purchase order.

        Args:
            purchase_order_id: Purchase order ID

        Returns:
            Dictionary with cost variance analysis
        """
        items = self.get_items_by_purchase_order(purchase_order_id)

        report = {
            "total_items": len(items),
            "total_variance": 0.0,
            "items_over_budget": 0,
            "items_under_budget": 0,
            "items_on_budget": 0,
            "largest_variance": 0.0,
            "variance_details": [],
        }

        for item in items:
            original_cost = float(item.get("UnitCost", 0))
            actual_cost = float(
                item.get("ActualUnitCost", original_cost)
            )  # If available
            quantity = float(item.get("QuantityOrdered", 0))

            unit_variance = actual_cost - original_cost
            line_variance = unit_variance * quantity

            report["total_variance"] += line_variance

            # Track largest variance
            if abs(line_variance) > abs(report["largest_variance"]):
                report["largest_variance"] = line_variance

            # Categorize items
            if line_variance > 0:
                report["items_over_budget"] += 1
            elif line_variance < 0:
                report["items_under_budget"] += 1
            else:
                report["items_on_budget"] += 1

            # Store detailed variance info
            report["variance_details"].append(
                {
                    "item_id": int(item["id"]),
                    "product_id": item.get("ProductID"),
                    "description": item.get("Description", ""),
                    "original_cost": original_cost,
                    "actual_cost": actual_cost,
                    "unit_variance": unit_variance,
                    "line_variance": line_variance,
                    "quantity": quantity,
                }
            )

        return report

    def validate_item_data(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate purchase order item data.

        Args:
            item_data: Item data to validate

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Required fields
        required_fields = [
            "PurchaseOrderID",
            "ProductID",
            "QuantityOrdered",
            "UnitCost",
        ]
        for field in required_fields:
            if field not in item_data or item_data[field] is None:
                result["errors"].append(f"Missing required field: {field}")
                result["valid"] = False

        # Numeric validations
        if "QuantityOrdered" in item_data:
            try:
                qty = float(item_data["QuantityOrdered"])
                if qty <= 0:
                    result["errors"].append("Quantity ordered must be greater than 0")
                    result["valid"] = False
            except (ValueError, TypeError):
                result["errors"].append("Quantity ordered must be a valid number")
                result["valid"] = False

        if "UnitCost" in item_data:
            try:
                cost = float(item_data["UnitCost"])
                if cost < 0:
                    result["errors"].append("Unit cost cannot be negative")
                    result["valid"] = False
                elif cost == 0:
                    result["warnings"].append(
                        "Unit cost is zero - confirm this is correct"
                    )
            except (ValueError, TypeError):
                result["errors"].append("Unit cost must be a valid number")
                result["valid"] = False

        return result
