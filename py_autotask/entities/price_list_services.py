"""
Price List Services entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PriceListServicesEntity(BaseEntity):
    """
    Handles all Price List Service-related operations for the Autotask API.

    Price list services define pricing for services within specific price lists,
    enabling flexible service pricing for different customer segments.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_price_list_service(
        self,
        price_list_id: int,
        service_id: int,
        unit_price: float,
        unit_cost: Optional[float] = None,
        currency_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """Create a new price list service entry."""
        pricing_data = {
            "PriceListID": price_list_id,
            "ServiceID": service_id,
            "UnitPrice": unit_price,
            "IsActive": is_active,
            **kwargs,
        }

        if unit_cost is not None:
            pricing_data["UnitCost"] = unit_cost
        if currency_id:
            pricing_data["CurrencyID"] = currency_id

        return self.create(pricing_data)

    def get_services_for_price_list(
        self, price_list_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all services for a specific price list."""
        filters = [{"field": "PriceListID", "op": "eq", "value": price_list_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_price_lists_for_service(
        self, service_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all price lists that include a specific service."""
        filters = [{"field": "ServiceID", "op": "eq", "value": service_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def update_service_pricing(
        self,
        price_list_id: int,
        service_id: int,
        new_unit_price: Optional[float] = None,
        new_unit_cost: Optional[float] = None,
    ) -> EntityDict:
        """Update pricing for a service in a price list."""
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "ServiceID", "op": "eq", "value": service_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for service {service_id} in price list {price_list_id}"
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
        service_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Apply a percentage price increase to services in a price list."""
        services = self.get_services_for_price_list(price_list_id)

        if service_ids:
            services = [s for s in services if s.get("ServiceID") in service_ids]

        results = []

        for service in services:
            service_id = service.get("ServiceID")
            current_price = service.get("UnitPrice", 0)
            new_price = current_price * (1 + percentage_increase / 100)

            try:
                updated = self.update_service_pricing(
                    price_list_id=price_list_id,
                    service_id=service_id,
                    new_unit_price=new_price,
                )
                results.append(
                    {
                        "service_id": service_id,
                        "old_price": current_price,
                        "new_price": new_price,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {"service_id": service_id, "status": "failed", "error": str(e)}
                )

        return results

    def get_service_price_comparison(
        self, service_id: int, price_list_ids: List[int]
    ) -> Dict[str, Any]:
        """Compare pricing for a service across multiple price lists."""
        comparison = {
            "service_id": service_id,
            "price_comparisons": [],
            "min_price": None,
            "max_price": None,
            "avg_price": None,
        }

        prices = []

        for price_list_id in price_list_ids:
            pricing_entries = self.query_all(
                filters=[
                    {"field": "ServiceID", "op": "eq", "value": service_id},
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

        return comparison

    def clone_service_pricing(
        self,
        source_price_list_id: int,
        target_price_list_id: int,
        price_adjustment: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Clone service pricing from one price list to another."""
        source_services = self.get_services_for_price_list(source_price_list_id)

        results = {
            "source_price_list_id": source_price_list_id,
            "target_price_list_id": target_price_list_id,
            "total_services": len(source_services),
            "successful_copies": 0,
            "failed_copies": 0,
        }

        for service in source_services:
            service_id = service.get("ServiceID")
            unit_price = service.get("UnitPrice", 0)
            unit_cost = service.get("UnitCost")

            if price_adjustment:
                unit_price = unit_price * (1 + price_adjustment / 100)

            try:
                self.create_price_list_service(
                    price_list_id=target_price_list_id,
                    service_id=service_id,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    currency_id=service.get("CurrencyID"),
                )
                results["successful_copies"] += 1
            except Exception:
                results["failed_copies"] += 1

        return results

    def get_pricing_summary(self, price_list_id: int) -> Dict[str, Any]:
        """Get summary statistics for services in a price list."""
        services = self.get_services_for_price_list(price_list_id)

        if not services:
            return {
                "price_list_id": price_list_id,
                "total_services": 0,
                "pricing_statistics": None,
            }

        prices = [
            s.get("UnitPrice", 0) for s in services if s.get("UnitPrice") is not None
        ]

        return {
            "price_list_id": price_list_id,
            "total_services": len(services),
            "active_services": len([s for s in services if s.get("IsActive")]),
            "pricing_statistics": {
                "min_price": min(prices) if prices else 0,
                "max_price": max(prices) if prices else 0,
                "avg_price": sum(prices) / len(prices) if prices else 0,
            },
        }
