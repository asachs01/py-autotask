"""
Price List Material Codes entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PriceListMaterialCodesEntity(BaseEntity):
    """
    Handles all Price List Material Code-related operations for the Autotask API.

    Price list material codes define pricing for materials and products within
    specific price lists, enabling flexible pricing structures for different
    customer segments or contract types.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_price_list_material_code(
        self,
        price_list_id: int,
        material_code_id: int,
        unit_price: float,
        unit_cost: Optional[float] = None,
        currency_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new price list material code entry.

        Args:
            price_list_id: ID of the price list
            material_code_id: ID of the material code
            unit_price: Unit price for this material in this price list
            unit_cost: Optional unit cost
            currency_id: Currency ID for pricing
            is_active: Whether this pricing is active
            **kwargs: Additional pricing fields

        Returns:
            Created price list material code data
        """
        pricing_data = {
            "PriceListID": price_list_id,
            "MaterialCodeID": material_code_id,
            "UnitPrice": unit_price,
            "IsActive": is_active,
            **kwargs,
        }

        if unit_cost is not None:
            pricing_data["UnitCost"] = unit_cost
        if currency_id:
            pricing_data["CurrencyID"] = currency_id

        return self.create(pricing_data)

    def get_materials_for_price_list(
        self, price_list_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """
        Get all material codes for a specific price list.

        Args:
            price_list_id: Price list ID to get materials for
            active_only: Whether to return only active pricing

        Returns:
            List of material code pricing for the price list
        """
        filters = [{"field": "PriceListID", "op": "eq", "value": price_list_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_price_lists_for_material(
        self, material_code_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """
        Get all price lists that include a specific material code.

        Args:
            material_code_id: Material code ID
            active_only: Whether to return only active pricing

        Returns:
            List of price list entries for the material code
        """
        filters = [{"field": "MaterialCodeID", "op": "eq", "value": material_code_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def update_material_pricing(
        self,
        price_list_id: int,
        material_code_id: int,
        new_unit_price: Optional[float] = None,
        new_unit_cost: Optional[float] = None,
    ) -> EntityDict:
        """
        Update pricing for a material code in a price list.

        Args:
            price_list_id: Price list ID
            material_code_id: Material code ID
            new_unit_price: New unit price
            new_unit_cost: New unit cost

        Returns:
            Updated pricing data
        """
        # Find the existing entry
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "MaterialCodeID", "op": "eq", "value": material_code_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for material {material_code_id} in price list {price_list_id}"
            )

        update_data = {}
        if new_unit_price is not None:
            update_data["UnitPrice"] = new_unit_price
        if new_unit_cost is not None:
            update_data["UnitCost"] = new_unit_cost

        return self.update_by_id(existing_entries[0]["id"], update_data)

    def bulk_update_pricing(
        self,
        price_list_id: int,
        pricing_updates: List[Dict[str, Any]],
        percentage_increase: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Update pricing for multiple materials in bulk.

        Args:
            price_list_id: Price list ID to update
            pricing_updates: List of dicts with material_code_id and new prices
            percentage_increase: Optional percentage increase to apply to all prices

        Returns:
            List of update results
        """
        results = []

        for update_item in pricing_updates:
            material_code_id = update_item["material_code_id"]
            new_unit_price = update_item.get("unit_price")
            new_unit_cost = update_item.get("unit_cost")

            try:
                # Apply percentage increase if specified
                if percentage_increase and new_unit_price:
                    new_unit_price = new_unit_price * (1 + percentage_increase / 100)

                updated = self.update_material_pricing(
                    price_list_id=price_list_id,
                    material_code_id=material_code_id,
                    new_unit_price=new_unit_price,
                    new_unit_cost=new_unit_cost,
                )
                results.append(
                    {
                        "material_code_id": material_code_id,
                        "status": "success",
                        "updated_data": updated,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "material_code_id": material_code_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results

    def deactivate_material_pricing(
        self, price_list_id: int, material_code_id: int
    ) -> EntityDict:
        """
        Deactivate pricing for a material in a price list.

        Args:
            price_list_id: Price list ID
            material_code_id: Material code ID

        Returns:
            Updated pricing data
        """
        # Find the existing entry
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "MaterialCodeID", "op": "eq", "value": material_code_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for material {material_code_id} in price list {price_list_id}"
            )

        return self.update_by_id(existing_entries[0]["id"], {"IsActive": False})

    def copy_pricing_to_price_list(
        self,
        source_price_list_id: int,
        target_price_list_id: int,
        material_code_ids: Optional[List[int]] = None,
        price_adjustment_percentage: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Copy material pricing from one price list to another.

        Args:
            source_price_list_id: Source price list ID
            target_price_list_id: Target price list ID
            material_code_ids: Optional list of specific material codes to copy
            price_adjustment_percentage: Optional percentage adjustment for prices

        Returns:
            List of copy results
        """
        # Get source pricing
        source_pricing = self.get_materials_for_price_list(source_price_list_id)

        if material_code_ids:
            source_pricing = [
                p
                for p in source_pricing
                if p.get("MaterialCodeID") in material_code_ids
            ]

        results = []

        for pricing in source_pricing:
            material_code_id = pricing.get("MaterialCodeID")
            unit_price = pricing.get("UnitPrice", 0)
            unit_cost = pricing.get("UnitCost")

            # Apply price adjustment if specified
            if price_adjustment_percentage and unit_price:
                unit_price = unit_price * (1 + price_adjustment_percentage / 100)

            try:
                new_pricing = self.create_price_list_material_code(
                    price_list_id=target_price_list_id,
                    material_code_id=material_code_id,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    currency_id=pricing.get("CurrencyID"),
                )
                results.append(
                    {
                        "material_code_id": material_code_id,
                        "status": "success",
                        "new_pricing_id": new_pricing["id"],
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "material_code_id": material_code_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results

    def get_pricing_comparison(
        self, material_code_id: int, price_list_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Compare pricing for a material across multiple price lists.

        Args:
            material_code_id: Material code ID to compare
            price_list_ids: List of price list IDs to compare

        Returns:
            Dictionary containing pricing comparison
        """
        comparison = {
            "material_code_id": material_code_id,
            "price_comparisons": [],
            "min_price": None,
            "max_price": None,
            "avg_price": None,
        }

        prices = []

        for price_list_id in price_list_ids:
            pricing_entries = self.query_all(
                filters=[
                    {"field": "MaterialCodeID", "op": "eq", "value": material_code_id},
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
                        "currency_id": entry.get("CurrencyID"),
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

    def get_price_list_material_summary(self, price_list_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for materials in a price list.

        Args:
            price_list_id: Price list ID to summarize

        Returns:
            Dictionary containing material pricing summary
        """
        materials = self.get_materials_for_price_list(price_list_id)
        active_materials = [m for m in materials if m.get("IsActive")]

        if not active_materials:
            return {
                "price_list_id": price_list_id,
                "total_materials": 0,
                "active_materials": 0,
                "pricing_statistics": None,
            }

        prices = [
            m.get("UnitPrice", 0)
            for m in active_materials
            if m.get("UnitPrice") is not None
        ]
        costs = [
            m.get("UnitCost", 0)
            for m in active_materials
            if m.get("UnitCost") is not None
        ]

        return {
            "price_list_id": price_list_id,
            "total_materials": len(materials),
            "active_materials": len(active_materials),
            "inactive_materials": len(materials) - len(active_materials),
            "pricing_statistics": {
                "min_price": min(prices) if prices else 0,
                "max_price": max(prices) if prices else 0,
                "avg_price": sum(prices) / len(prices) if prices else 0,
                "materials_with_cost": len(costs),
                "avg_cost": sum(costs) / len(costs) if costs else 0,
                "avg_margin": (
                    (sum(prices) - sum(costs)) / sum(prices) * 100
                    if prices and costs and sum(prices) > 0
                    else 0
                ),
            },
        }
