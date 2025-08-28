"""
Price List Service Bundles entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PriceListServiceBundlesEntity(BaseEntity):
    """
    Handles all Price List Service Bundle-related operations for the Autotask API.

    Price list service bundles define pricing for service bundles within
    specific price lists, enabling bundled service offerings.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_price_list_service_bundle(
        self,
        price_list_id: int,
        service_bundle_id: int,
        unit_price: float,
        unit_cost: Optional[float] = None,
        currency_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """Create a new price list service bundle entry."""
        pricing_data = {
            "PriceListID": price_list_id,
            "ServiceBundleID": service_bundle_id,
            "UnitPrice": unit_price,
            "IsActive": is_active,
            **kwargs,
        }

        if unit_cost is not None:
            pricing_data["UnitCost"] = unit_cost
        if currency_id:
            pricing_data["CurrencyID"] = currency_id

        return self.create(pricing_data)

    def get_service_bundles_for_price_list(
        self, price_list_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all service bundles for a specific price list."""
        filters = [{"field": "PriceListID", "op": "eq", "value": price_list_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_price_lists_for_service_bundle(
        self, service_bundle_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all price lists that include a specific service bundle."""
        filters = [{"field": "ServiceBundleID", "op": "eq", "value": service_bundle_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def update_service_bundle_pricing(
        self,
        price_list_id: int,
        service_bundle_id: int,
        new_unit_price: Optional[float] = None,
        new_unit_cost: Optional[float] = None,
    ) -> EntityDict:
        """Update pricing for a service bundle in a price list."""
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "ServiceBundleID", "op": "eq", "value": service_bundle_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for service bundle {service_bundle_id} in price list {price_list_id}"
            )

        update_data = {}
        if new_unit_price is not None:
            update_data["UnitPrice"] = new_unit_price
        if new_unit_cost is not None:
            update_data["UnitCost"] = new_unit_cost

        return self.update_by_id(existing_entries[0]["id"], update_data)

    def apply_bundle_discount(
        self,
        price_list_id: int,
        discount_percentage: float,
        service_bundle_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Apply a discount to service bundles in a price list."""
        bundles = self.get_service_bundles_for_price_list(price_list_id)

        if service_bundle_ids:
            bundles = [
                b for b in bundles if b.get("ServiceBundleID") in service_bundle_ids
            ]

        results = []

        for bundle in bundles:
            bundle_id = bundle.get("ServiceBundleID")
            current_price = bundle.get("UnitPrice", 0)
            new_price = current_price * (1 - discount_percentage / 100)

            try:
                updated = self.update_service_bundle_pricing(
                    price_list_id=price_list_id,
                    service_bundle_id=bundle_id,
                    new_unit_price=new_price,
                )
                results.append(
                    {
                        "service_bundle_id": bundle_id,
                        "old_price": current_price,
                        "new_price": new_price,
                        "discount_applied": discount_percentage,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "service_bundle_id": bundle_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results

    def get_bundle_pricing_comparison(
        self, service_bundle_id: int, price_list_ids: List[int]
    ) -> Dict[str, Any]:
        """Compare pricing for a service bundle across multiple price lists."""
        comparison = {
            "service_bundle_id": service_bundle_id,
            "price_comparisons": [],
            "min_price": None,
            "max_price": None,
            "avg_price": None,
        }

        prices = []

        for price_list_id in price_list_ids:
            pricing_entries = self.query_all(
                filters=[
                    {
                        "field": "ServiceBundleID",
                        "op": "eq",
                        "value": service_bundle_id,
                    },
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
                    }
                )

        if prices:
            comparison["min_price"] = min(prices)
            comparison["max_price"] = max(prices)
            comparison["avg_price"] = sum(prices) / len(prices)

        return comparison

    def deactivate_service_bundle(
        self, price_list_id: int, service_bundle_id: int
    ) -> EntityDict:
        """Deactivate a service bundle in a price list."""
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "ServiceBundleID", "op": "eq", "value": service_bundle_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for service bundle {service_bundle_id} in price list {price_list_id}"
            )

        return self.update_by_id(existing_entries[0]["id"], {"IsActive": False})

    def get_bundle_value_analysis(self, price_list_id: int) -> Dict[str, Any]:
        """Analyze value proposition of service bundles in a price list."""
        bundles = self.get_service_bundles_for_price_list(price_list_id)

        analysis = {
            "price_list_id": price_list_id,
            "total_bundles": len(bundles),
            "active_bundles": len([b for b in bundles if b.get("IsActive")]),
            "bundles_with_cost_data": 0,
            "value_statistics": {},
        }

        margins = []

        for bundle in bundles:
            unit_price = bundle.get("UnitPrice", 0)
            unit_cost = bundle.get("UnitCost")

            if unit_cost is not None and unit_price > 0:
                analysis["bundles_with_cost_data"] += 1
                margin = (unit_price - unit_cost) / unit_price * 100
                margins.append(margin)

        if margins:
            analysis["value_statistics"] = {
                "min_margin": min(margins),
                "max_margin": max(margins),
                "avg_margin": sum(margins) / len(margins),
            }

        return analysis

    def clone_bundle_pricing(
        self,
        source_price_list_id: int,
        target_price_list_id: int,
        price_adjustment: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Clone service bundle pricing from one price list to another."""
        source_bundles = self.get_service_bundles_for_price_list(source_price_list_id)

        results = {
            "total_bundles": len(source_bundles),
            "successful_copies": 0,
            "failed_copies": 0,
        }

        for bundle in source_bundles:
            bundle_id = bundle.get("ServiceBundleID")
            unit_price = bundle.get("UnitPrice", 0)

            if price_adjustment:
                unit_price = unit_price * (1 + price_adjustment / 100)

            try:
                self.create_price_list_service_bundle(
                    price_list_id=target_price_list_id,
                    service_bundle_id=bundle_id,
                    unit_price=unit_price,
                    unit_cost=bundle.get("UnitCost"),
                )
                results["successful_copies"] += 1
            except Exception:
                results["failed_copies"] += 1

        return results
