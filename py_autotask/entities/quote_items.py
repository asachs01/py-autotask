"""
QuoteItems entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class QuoteItemsEntity(BaseEntity):
    """
    Handles all Quote Item-related operations for the Autotask API.

    Quote Items represent individual products or services included in a quote.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_quote_item(
        self,
        quote_id: int,
        product_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        quantity: int = 1,
        unit_price: float = 0.0,
        unit_cost: Optional[float] = None,
        discount_percentage: float = 0.0,
        tax_category_id: Optional[int] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new quote item.

        Args:
            quote_id: ID of the quote
            product_id: ID of the product (if using existing product)
            name: Name of the item (required if not using product_id)
            description: Description of the item
            quantity: Quantity of the item
            unit_price: Price per unit
            unit_cost: Cost per unit
            discount_percentage: Discount percentage to apply
            tax_category_id: ID of the tax category
            **kwargs: Additional quote item fields

        Returns:
            Created quote item data
        """
        quote_item_data = {
            "QuoteID": quote_id,
            "Quantity": quantity,
            "UnitPrice": unit_price,
            "DiscountPercentage": discount_percentage,
            **kwargs,
        }

        if product_id:
            quote_item_data["ProductID"] = product_id
        if name:
            quote_item_data["Name"] = name
        if description:
            quote_item_data["Description"] = description
        if unit_cost is not None:
            quote_item_data["UnitCost"] = unit_cost
        if tax_category_id:
            quote_item_data["TaxCategoryID"] = tax_category_id

        return self.create(quote_item_data)

    def get_items_by_quote(
        self, quote_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all items for a specific quote.

        Args:
            quote_id: ID of the quote
            limit: Maximum number of records to return

        Returns:
            List of items for the quote
        """
        filters = [QueryFilter(field="QuoteID", op="eq", value=quote_id)]

        return self.query(filters=filters, max_records=limit)

    def get_items_by_product(
        self, product_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all quote items for a specific product.

        Args:
            product_id: ID of the product
            limit: Maximum number of records to return

        Returns:
            List of quote items for the product
        """
        filters = [QueryFilter(field="ProductID", op="eq", value=product_id)]

        return self.query(filters=filters, max_records=limit)

    def search_items_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for quote items by name.

        Args:
            name: Item name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching quote items
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_high_value_items(
        self, minimum_value: float, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get quote items with high total values.

        Args:
            minimum_value: Minimum total value (quantity * unit_price)
            limit: Maximum number of records to return

        Returns:
            List of high-value quote items
        """
        # Note: This would ideally use a calculated field, but we'll filter after query
        all_items = self.query(max_records=limit)

        high_value_items = []
        for item in all_items:
            quantity = item.get("Quantity", 1)
            unit_price = item.get("UnitPrice", 0)
            discount = item.get("DiscountPercentage", 0)

            # Calculate total value after discount
            subtotal = quantity * unit_price
            total_value = subtotal * (1 - discount / 100)

            if total_value >= minimum_value:
                item["calculated_total_value"] = total_value
                high_value_items.append(item)

        # Sort by total value descending
        high_value_items.sort(
            key=lambda x: x.get("calculated_total_value", 0), reverse=True
        )

        return high_value_items[:limit] if limit else high_value_items

    def get_discounted_items(
        self, minimum_discount: float = 0.0, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get quote items with discounts applied.

        Args:
            minimum_discount: Minimum discount percentage
            limit: Maximum number of records to return

        Returns:
            List of discounted quote items
        """
        filters = [
            QueryFilter(field="DiscountPercentage", op="gt", value=minimum_discount)
        ]

        return self.query(filters=filters, max_records=limit)

    def update_item_pricing(
        self,
        quote_item_id: int,
        unit_price: Optional[float] = None,
        discount_percentage: Optional[float] = None,
    ) -> EntityDict:
        """
        Update the pricing for a quote item.

        Args:
            quote_item_id: ID of the quote item
            unit_price: New unit price
            discount_percentage: New discount percentage

        Returns:
            Updated quote item data
        """
        update_data = {}
        if unit_price is not None:
            update_data["UnitPrice"] = unit_price
        if discount_percentage is not None:
            update_data["DiscountPercentage"] = discount_percentage

        return self.update_by_id(quote_item_id, update_data)

    def update_item_quantity(self, quote_item_id: int, quantity: int) -> EntityDict:
        """
        Update the quantity for a quote item.

        Args:
            quote_item_id: ID of the quote item
            quantity: New quantity

        Returns:
            Updated quote item data
        """
        return self.update_by_id(quote_item_id, {"Quantity": quantity})

    def calculate_quote_totals(self, quote_id: int) -> Dict[str, float]:
        """
        Calculate totals for all items in a quote.

        Args:
            quote_id: ID of the quote

        Returns:
            Dictionary with calculated totals
        """
        quote_items = self.get_items_by_quote(quote_id)

        subtotal = 0.0
        total_discount = 0.0
        total_cost = 0.0

        for item in quote_items:
            quantity = item.get("Quantity", 1)
            unit_price = item.get("UnitPrice", 0.0)
            unit_cost = item.get("UnitCost", 0.0)
            discount_percentage = item.get("DiscountPercentage", 0.0)

            # Calculate line totals
            line_subtotal = quantity * unit_price
            line_discount = line_subtotal * (discount_percentage / 100)
            line_subtotal - line_discount
            line_cost = quantity * unit_cost

            subtotal += line_subtotal
            total_discount += line_discount
            total_cost += line_cost

        net_total = subtotal - total_discount
        margin = net_total - total_cost

        return {
            "subtotal": round(subtotal, 2),
            "total_discount": round(total_discount, 2),
            "net_total": round(net_total, 2),
            "total_cost": round(total_cost, 2),
            "margin": round(margin, 2),
            "margin_percentage": round(
                (margin / net_total * 100) if net_total > 0 else 0, 2
            ),
            "item_count": len(quote_items),
        }

    def get_popular_quote_items(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get the most frequently quoted items.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of popular items with usage statistics
        """
        all_items = self.query()

        # Group by product ID or item name
        item_frequency = {}
        for item in all_items:
            # Use product ID if available, otherwise use item name
            key = item.get("ProductID") or item.get("Name", "Unknown")

            if key not in item_frequency:
                item_frequency[key] = {
                    "identifier": key,
                    "name": item.get("Name", "Unknown"),
                    "product_id": item.get("ProductID"),
                    "quote_count": 0,
                    "total_quantity": 0,
                    "average_unit_price": 0,
                    "prices": [],
                }

            item_frequency[key]["quote_count"] += 1
            item_frequency[key]["total_quantity"] += item.get("Quantity", 1)

            unit_price = item.get("UnitPrice", 0)
            item_frequency[key]["prices"].append(unit_price)

        # Calculate average prices and sort by frequency
        popular_items = []
        for stats in item_frequency.values():
            if stats["prices"]:
                stats["average_unit_price"] = round(
                    sum(stats["prices"]) / len(stats["prices"]), 2
                )
            stats.pop("prices")  # Remove the prices list from final result
            popular_items.append(stats)

        # Sort by quote count (frequency)
        popular_items.sort(key=lambda x: x["quote_count"], reverse=True)

        return popular_items[:limit]

    def get_quote_item_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about quote items.

        Returns:
            Dictionary containing quote item statistics
        """
        all_items = self.query()

        # Calculate various statistics
        quantities = [item.get("Quantity", 0) for item in all_items]
        prices = [item.get("UnitPrice", 0) for item in all_items]
        discounts = [
            item.get("DiscountPercentage", 0)
            for item in all_items
            if item.get("DiscountPercentage", 0) > 0
        ]

        # Count items by type
        product_items = len([item for item in all_items if item.get("ProductID")])
        custom_items = len(all_items) - product_items

        stats = {
            "total_quote_items": len(all_items),
            "product_based_items": product_items,
            "custom_items": custom_items,
            "items_with_discount": len(discounts),
        }

        if quantities:
            stats["quantity_statistics"] = {
                "average_quantity": round(sum(quantities) / len(quantities), 2),
                "total_quantity": sum(quantities),
                "max_quantity": max(quantities),
            }

        if prices:
            stats["price_statistics"] = {
                "average_unit_price": round(sum(prices) / len(prices), 2),
                "min_unit_price": min(prices),
                "max_unit_price": max(prices),
            }

        if discounts:
            stats["discount_statistics"] = {
                "average_discount": round(sum(discounts) / len(discounts), 2),
                "max_discount": max(discounts),
            }

        return stats
