"""
ProductTiers entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ProductTiersEntity(BaseEntity):
    """
    Handles all Product Tier-related operations for the Autotask API.

    Product Tiers define different pricing levels or service tiers for products.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_product_tier(
        self,
        product_id: int,
        name: str,
        description: str,
        unit_price: float,
        unit_cost: Optional[float] = None,
        minimum_quantity: int = 1,
        is_active: bool = True,
        tier_level: Optional[int] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new product tier.

        Args:
            product_id: ID of the product
            name: Name of the tier
            description: Description of the tier
            unit_price: Price per unit for this tier
            unit_cost: Cost per unit for this tier
            minimum_quantity: Minimum quantity required for this tier
            is_active: Whether the tier is active
            tier_level: Hierarchical level of the tier
            **kwargs: Additional tier fields

        Returns:
            Created product tier data
        """
        tier_data = {
            "ProductID": product_id,
            "Name": name,
            "Description": description,
            "UnitPrice": unit_price,
            "MinimumQuantity": minimum_quantity,
            "IsActive": is_active,
            **kwargs,
        }

        if unit_cost is not None:
            tier_data["UnitCost"] = unit_cost
        if tier_level is not None:
            tier_data["TierLevel"] = tier_level

        return self.create(tier_data)

    def get_tiers_by_product(
        self, product_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all tiers for a specific product.

        Args:
            product_id: ID of the product
            active_only: Whether to return only active tiers
            limit: Maximum number of records to return

        Returns:
            List of tiers for the product
        """
        filters = [QueryFilter(field="ProductID", op="eq", value=product_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_tier_by_quantity(
        self, product_id: int, quantity: int
    ) -> Optional[EntityDict]:
        """
        Get the appropriate tier for a specific quantity.

        Args:
            product_id: ID of the product
            quantity: Quantity to find tier for

        Returns:
            Best matching tier or None if not found
        """
        tiers = self.get_tiers_by_product(product_id, active_only=True)

        # Sort tiers by minimum quantity descending
        sorted_tiers = sorted(
            tiers, key=lambda x: x.get("MinimumQuantity", 0), reverse=True
        )

        # Find the first tier where quantity meets minimum requirement
        for tier in sorted_tiers:
            if quantity >= tier.get("MinimumQuantity", 1):
                return tier

        return None

    def search_tiers_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for product tiers by name.

        Args:
            name: Tier name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching tiers
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_tiers_by_price_range(
        self, min_price: float, max_price: float, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get tiers within a specific price range.

        Args:
            min_price: Minimum unit price
            max_price: Maximum unit price
            limit: Maximum number of records to return

        Returns:
            List of tiers within the price range
        """
        filters = [
            QueryFilter(field="UnitPrice", op="ge", value=min_price),
            QueryFilter(field="UnitPrice", op="le", value=max_price),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_high_volume_tiers(
        self, minimum_threshold: int = 100, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get tiers designed for high-volume purchases.

        Args:
            minimum_threshold: Minimum quantity threshold
            limit: Maximum number of records to return

        Returns:
            List of high-volume tiers
        """
        filters = [
            QueryFilter(field="MinimumQuantity", op="ge", value=minimum_threshold)
        ]

        return self.query(filters=filters, max_records=limit)

    def update_tier_pricing(
        self,
        tier_id: int,
        unit_price: Optional[float] = None,
        unit_cost: Optional[float] = None,
    ) -> EntityDict:
        """
        Update the pricing for a product tier.

        Args:
            tier_id: ID of the tier
            unit_price: New unit price
            unit_cost: New unit cost

        Returns:
            Updated tier data
        """
        update_data = {}
        if unit_price is not None:
            update_data["UnitPrice"] = unit_price
        if unit_cost is not None:
            update_data["UnitCost"] = unit_cost

        return self.update_by_id(tier_id, update_data)

    def update_tier_quantity_threshold(
        self, tier_id: int, minimum_quantity: int
    ) -> EntityDict:
        """
        Update the minimum quantity threshold for a tier.

        Args:
            tier_id: ID of the tier
            minimum_quantity: New minimum quantity

        Returns:
            Updated tier data
        """
        return self.update_by_id(tier_id, {"MinimumQuantity": minimum_quantity})

    def activate_tier(self, tier_id: int) -> EntityDict:
        """
        Activate a product tier.

        Args:
            tier_id: ID of the tier

        Returns:
            Updated tier data
        """
        return self.update_by_id(tier_id, {"IsActive": True})

    def deactivate_tier(self, tier_id: int) -> EntityDict:
        """
        Deactivate a product tier.

        Args:
            tier_id: ID of the tier

        Returns:
            Updated tier data
        """
        return self.update_by_id(tier_id, {"IsActive": False})

    def calculate_tier_pricing(
        self, product_id: int, quantities: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Calculate pricing for multiple quantities using tier pricing.

        Args:
            product_id: ID of the product
            quantities: List of quantities to calculate pricing for

        Returns:
            Dictionary mapping quantities to pricing information
        """
        pricing_results = {}

        for quantity in quantities:
            tier = self.get_tier_by_quantity(product_id, quantity)
            if tier:
                unit_price = tier.get("UnitPrice", 0)
                total_price = unit_price * quantity
                unit_cost = tier.get("UnitCost", 0)
                total_cost = unit_cost * quantity
                margin = total_price - total_cost

                pricing_results[quantity] = {
                    "tier_id": tier.get("id"),
                    "tier_name": tier.get("Name"),
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "unit_cost": unit_cost,
                    "total_cost": total_cost,
                    "margin": margin,
                    "margin_percentage": (
                        (margin / total_price * 100) if total_price > 0 else 0
                    ),
                }
            else:
                pricing_results[quantity] = {
                    "error": "No matching tier found for quantity"
                }

        return pricing_results

    def get_tier_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about product tiers.

        Returns:
            Dictionary containing tier statistics
        """
        all_tiers = self.query()

        # Calculate price statistics
        prices = [
            tier.get("UnitPrice", 0) for tier in all_tiers if tier.get("UnitPrice")
        ]
        quantities = [tier.get("MinimumQuantity", 0) for tier in all_tiers]

        # Group by product
        products_with_tiers = set(
            tier.get("ProductID") for tier in all_tiers if tier.get("ProductID")
        )

        stats = {
            "total_tiers": len(all_tiers),
            "active_tiers": len(
                [tier for tier in all_tiers if tier.get("IsActive", False)]
            ),
            "inactive_tiers": len(
                [tier for tier in all_tiers if not tier.get("IsActive", False)]
            ),
            "products_with_tiers": len(products_with_tiers),
        }

        if prices:
            stats["price_statistics"] = {
                "average_price": round(sum(prices) / len(prices), 2),
                "min_price": min(prices),
                "max_price": max(prices),
            }

        if quantities:
            stats["quantity_statistics"] = {
                "average_min_quantity": round(sum(quantities) / len(quantities), 2),
                "lowest_min_quantity": min(quantities),
                "highest_min_quantity": max(quantities),
            }

        return stats

    def get_product_tier_summary(self, product_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of tiers for a specific product.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with tier summary for the product
        """
        product_tiers = self.get_tiers_by_product(product_id, active_only=False)

        # Sort tiers by minimum quantity
        sorted_tiers = sorted(product_tiers, key=lambda x: x.get("MinimumQuantity", 0))

        # Calculate price range
        prices = [tier.get("UnitPrice", 0) for tier in product_tiers]
        quantities = [tier.get("MinimumQuantity", 0) for tier in product_tiers]

        summary = {
            "product_id": product_id,
            "total_tiers": len(product_tiers),
            "active_tiers": len(
                [tier for tier in product_tiers if tier.get("IsActive", False)]
            ),
            "tier_breakdown": [
                {
                    "id": tier.get("id"),
                    "name": tier.get("Name"),
                    "min_quantity": tier.get("MinimumQuantity"),
                    "unit_price": tier.get("UnitPrice"),
                    "is_active": tier.get("IsActive"),
                }
                for tier in sorted_tiers
            ],
        }

        if prices:
            summary["price_range"] = {
                "lowest": min(prices),
                "highest": max(prices),
                "spread": max(prices) - min(prices),
            }

        if quantities:
            summary["quantity_range"] = {
                "lowest_threshold": min(quantities),
                "highest_threshold": max(quantities),
            }

        return summary
