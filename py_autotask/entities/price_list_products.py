"""
Price List Products entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PriceListProductsEntity(BaseEntity):
    """
    Handles all Price List Product-related operations for the Autotask API.

    Price list products define pricing for products within specific price lists,
    enabling flexible product pricing for different customer segments.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_price_list_product(
        self,
        price_list_id: int,
        product_id: int,
        unit_price: float,
        unit_cost: Optional[float] = None,
        currency_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new price list product entry.

        Args:
            price_list_id: ID of the price list
            product_id: ID of the product
            unit_price: Unit price for this product in this price list
            unit_cost: Optional unit cost
            currency_id: Currency ID for pricing
            is_active: Whether this pricing is active
            **kwargs: Additional pricing fields

        Returns:
            Created price list product data
        """
        pricing_data = {
            "PriceListID": price_list_id,
            "ProductID": product_id,
            "UnitPrice": unit_price,
            "IsActive": is_active,
            **kwargs,
        }

        if unit_cost is not None:
            pricing_data["UnitCost"] = unit_cost
        if currency_id:
            pricing_data["CurrencyID"] = currency_id

        return self.create(pricing_data)

    def get_products_for_price_list(
        self, price_list_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """
        Get all products for a specific price list.

        Args:
            price_list_id: Price list ID to get products for
            active_only: Whether to return only active pricing

        Returns:
            List of product pricing for the price list
        """
        filters = [{"field": "PriceListID", "op": "eq", "value": price_list_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_price_lists_for_product(
        self, product_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """
        Get all price lists that include a specific product.

        Args:
            product_id: Product ID
            active_only: Whether to return only active pricing

        Returns:
            List of price list entries for the product
        """
        filters = [{"field": "ProductID", "op": "eq", "value": product_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def update_product_pricing(
        self,
        price_list_id: int,
        product_id: int,
        new_unit_price: Optional[float] = None,
        new_unit_cost: Optional[float] = None,
    ) -> EntityDict:
        """
        Update pricing for a product in a price list.

        Args:
            price_list_id: Price list ID
            product_id: Product ID
            new_unit_price: New unit price
            new_unit_cost: New unit cost

        Returns:
            Updated pricing data
        """
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "ProductID", "op": "eq", "value": product_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for product {product_id} in price list {price_list_id}"
            )

        update_data = {}
        if new_unit_price is not None:
            update_data["UnitPrice"] = new_unit_price
        if new_unit_cost is not None:
            update_data["UnitCost"] = new_unit_cost

        return self.update_by_id(existing_entries[0]["id"], update_data)

    def apply_price_increase(
        self,
        price_list_id: int,
        percentage_increase: float,
        product_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Apply a percentage price increase to products in a price list.

        Args:
            price_list_id: Price list ID
            percentage_increase: Percentage to increase prices
            product_ids: Optional list of specific product IDs

        Returns:
            List of update results
        """
        products = self.get_products_for_price_list(price_list_id)

        if product_ids:
            products = [p for p in products if p.get("ProductID") in product_ids]

        results = []

        for product in products:
            product_id = product.get("ProductID")
            current_price = product.get("UnitPrice", 0)
            new_price = current_price * (1 + percentage_increase / 100)

            try:
                updated = self.update_product_pricing(
                    price_list_id=price_list_id,
                    product_id=product_id,
                    new_unit_price=new_price,
                )
                results.append(
                    {
                        "product_id": product_id,
                        "old_price": current_price,
                        "new_price": new_price,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {"product_id": product_id, "status": "failed", "error": str(e)}
                )

        return results

    def get_product_price_comparison(
        self, product_id: int, price_list_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Compare pricing for a product across multiple price lists.

        Args:
            product_id: Product ID to compare
            price_list_ids: List of price list IDs to compare

        Returns:
            Dictionary containing pricing comparison
        """
        comparison = {
            "product_id": product_id,
            "price_comparisons": [],
            "min_price": None,
            "max_price": None,
            "avg_price": None,
        }

        prices = []

        for price_list_id in price_list_ids:
            pricing_entries = self.query_all(
                filters=[
                    {"field": "ProductID", "op": "eq", "value": product_id},
                    {"field": "PriceListID", "op": "eq", "value": price_list_id},
                    {"field": "IsActive", "op": "eq", "value": "true"},
                ]
            )

            if pricing_entries:
                entry = pricing_entries[0]
                unit_price = entry.get("UnitPrice", 0)
                prices.append(unit_price)

                comparison["price_comparisons"].append(
                    {
                        "price_list_id": price_list_id,
                        "unit_price": unit_price,
                        "unit_cost": entry.get("UnitCost"),
                        "margin": (
                            ((unit_price - entry.get("UnitCost", 0)) / unit_price * 100)
                            if unit_price > 0 and entry.get("UnitCost")
                            else None
                        ),
                    }
                )
            else:
                comparison["price_comparisons"].append(
                    {
                        "price_list_id": price_list_id,
                        "unit_price": None,
                        "status": "not_found",
                    }
                )

        if prices:
            comparison["min_price"] = min(prices)
            comparison["max_price"] = max(prices)
            comparison["avg_price"] = sum(prices) / len(prices)
            comparison["price_variance"] = (
                comparison["max_price"] - comparison["min_price"]
            )

        return comparison

    def clone_price_list(
        self,
        source_price_list_id: int,
        target_price_list_id: int,
        price_adjustment: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Clone all product pricing from one price list to another.

        Args:
            source_price_list_id: Source price list ID
            target_price_list_id: Target price list ID
            price_adjustment: Optional percentage adjustment for all prices

        Returns:
            Dictionary with cloning results
        """
        source_products = self.get_products_for_price_list(source_price_list_id)

        results = {
            "source_price_list_id": source_price_list_id,
            "target_price_list_id": target_price_list_id,
            "total_products": len(source_products),
            "successful_copies": 0,
            "failed_copies": 0,
            "details": [],
        }

        for product in source_products:
            product_id = product.get("ProductID")
            unit_price = product.get("UnitPrice", 0)
            unit_cost = product.get("UnitCost")

            # Apply price adjustment if specified
            if price_adjustment:
                unit_price = unit_price * (1 + price_adjustment / 100)

            try:
                new_entry = self.create_price_list_product(
                    price_list_id=target_price_list_id,
                    product_id=product_id,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    currency_id=product.get("CurrencyID"),
                )
                results["successful_copies"] += 1
                results["details"].append(
                    {
                        "product_id": product_id,
                        "status": "success",
                        "new_entry_id": new_entry["id"],
                    }
                )
            except Exception as e:
                results["failed_copies"] += 1
                results["details"].append(
                    {"product_id": product_id, "status": "failed", "error": str(e)}
                )

        return results

    def get_margin_analysis(self, price_list_id: int) -> Dict[str, Any]:
        """
        Analyze profit margins for products in a price list.

        Args:
            price_list_id: Price list ID to analyze

        Returns:
            Dictionary containing margin analysis
        """
        products = self.get_products_for_price_list(price_list_id)

        analysis = {
            "price_list_id": price_list_id,
            "total_products": len(products),
            "products_with_cost_data": 0,
            "margin_statistics": {},
            "products_by_margin_range": {
                "negative_margin": 0,
                "0_to_10_percent": 0,
                "10_to_25_percent": 0,
                "25_to_50_percent": 0,
                "50_plus_percent": 0,
            },
        }

        margins = []

        for product in products:
            unit_price = product.get("UnitPrice", 0)
            unit_cost = product.get("UnitCost")

            if unit_cost is not None and unit_price > 0:
                analysis["products_with_cost_data"] += 1
                margin = (unit_price - unit_cost) / unit_price * 100
                margins.append(margin)

                # Categorize by margin range
                if margin < 0:
                    analysis["products_by_margin_range"]["negative_margin"] += 1
                elif margin < 10:
                    analysis["products_by_margin_range"]["0_to_10_percent"] += 1
                elif margin < 25:
                    analysis["products_by_margin_range"]["10_to_25_percent"] += 1
                elif margin < 50:
                    analysis["products_by_margin_range"]["25_to_50_percent"] += 1
                else:
                    analysis["products_by_margin_range"]["50_plus_percent"] += 1

        if margins:
            analysis["margin_statistics"] = {
                "min_margin": min(margins),
                "max_margin": max(margins),
                "avg_margin": sum(margins) / len(margins),
                "median_margin": sorted(margins)[len(margins) // 2],
            }

        return analysis
