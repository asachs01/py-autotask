"""
Price List Roles entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PriceListRolesEntity(BaseEntity):
    """
    Handles all Price List Role-related operations for the Autotask API.

    Price list roles define pricing for different resource roles within
    specific price lists, enabling flexible labor pricing structures.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_price_list_role(
        self,
        price_list_id: int,
        role_id: int,
        hourly_rate: float,
        hourly_cost: Optional[float] = None,
        currency_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """Create a new price list role entry."""
        pricing_data = {
            "PriceListID": price_list_id,
            "RoleID": role_id,
            "HourlyRate": hourly_rate,
            "IsActive": is_active,
            **kwargs,
        }

        if hourly_cost is not None:
            pricing_data["HourlyCost"] = hourly_cost
        if currency_id:
            pricing_data["CurrencyID"] = currency_id

        return self.create(pricing_data)

    def get_roles_for_price_list(
        self, price_list_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all roles for a specific price list."""
        filters = [{"field": "PriceListID", "op": "eq", "value": price_list_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_price_lists_for_role(
        self, role_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all price lists that include a specific role."""
        filters = [{"field": "RoleID", "op": "eq", "value": role_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def update_role_rates(
        self,
        price_list_id: int,
        role_id: int,
        new_hourly_rate: Optional[float] = None,
        new_hourly_cost: Optional[float] = None,
    ) -> EntityDict:
        """Update rates for a role in a price list."""
        existing_entries = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "RoleID", "op": "eq", "value": role_id},
            ]
        )

        if not existing_entries:
            raise ValueError(
                f"No pricing found for role {role_id} in price list {price_list_id}"
            )

        update_data = {}
        if new_hourly_rate is not None:
            update_data["HourlyRate"] = new_hourly_rate
        if new_hourly_cost is not None:
            update_data["HourlyCost"] = new_hourly_cost

        return self.update_by_id(existing_entries[0]["id"], update_data)

    def apply_rate_increase(
        self,
        price_list_id: int,
        percentage_increase: float,
        role_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Apply a percentage rate increase to roles in a price list."""
        roles = self.get_roles_for_price_list(price_list_id)

        if role_ids:
            roles = [r for r in roles if r.get("RoleID") in role_ids]

        results = []

        for role in roles:
            role_id = role.get("RoleID")
            current_rate = role.get("HourlyRate", 0)
            new_rate = current_rate * (1 + percentage_increase / 100)

            try:
                updated = self.update_role_rates(
                    price_list_id=price_list_id,
                    role_id=role_id,
                    new_hourly_rate=new_rate,
                )
                results.append(
                    {
                        "role_id": role_id,
                        "old_rate": current_rate,
                        "new_rate": new_rate,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {"role_id": role_id, "status": "failed", "error": str(e)}
                )

        return results

    def get_role_rate_comparison(
        self, role_id: int, price_list_ids: List[int]
    ) -> Dict[str, Any]:
        """Compare rates for a role across multiple price lists."""
        comparison = {
            "role_id": role_id,
            "rate_comparisons": [],
            "min_rate": None,
            "max_rate": None,
            "avg_rate": None,
        }

        rates = []

        for price_list_id in price_list_ids:
            pricing_entries = self.query_all(
                filters=[
                    {"field": "RoleID", "op": "eq", "value": role_id},
                    {"field": "PriceListID", "op": "eq", "value": price_list_id},
                    {"field": "IsActive", "op": "eq", "value": "true"},
                ]
            )

            if pricing_entries:
                entry = pricing_entries[0]
                hourly_rate = entry.get("HourlyRate", 0)
                rates.append(hourly_rate)

                comparison["rate_comparisons"].append(
                    {
                        "price_list_id": price_list_id,
                        "hourly_rate": hourly_rate,
                        "hourly_cost": entry.get("HourlyCost"),
                        "margin": (
                            (
                                (hourly_rate - entry.get("HourlyCost", 0))
                                / hourly_rate
                                * 100
                            )
                            if hourly_rate > 0 and entry.get("HourlyCost")
                            else None
                        ),
                    }
                )
            else:
                comparison["rate_comparisons"].append(
                    {
                        "price_list_id": price_list_id,
                        "hourly_rate": None,
                        "status": "not_found",
                    }
                )

        if rates:
            comparison["min_rate"] = min(rates)
            comparison["max_rate"] = max(rates)
            comparison["avg_rate"] = sum(rates) / len(rates)
            comparison["rate_variance"] = (
                comparison["max_rate"] - comparison["min_rate"]
            )

        return comparison

    def get_margin_analysis_by_role(self, price_list_id: int) -> Dict[str, Any]:
        """Analyze profit margins for roles in a price list."""
        roles = self.get_roles_for_price_list(price_list_id)

        analysis = {
            "price_list_id": price_list_id,
            "total_roles": len(roles),
            "roles_with_cost_data": 0,
            "margin_statistics": {},
            "roles_by_margin_range": {
                "negative_margin": 0,
                "0_to_25_percent": 0,
                "25_to_50_percent": 0,
                "50_plus_percent": 0,
            },
        }

        margins = []

        for role in roles:
            hourly_rate = role.get("HourlyRate", 0)
            hourly_cost = role.get("HourlyCost")

            if hourly_cost is not None and hourly_rate > 0:
                analysis["roles_with_cost_data"] += 1
                margin = (hourly_rate - hourly_cost) / hourly_rate * 100
                margins.append(margin)

                if margin < 0:
                    analysis["roles_by_margin_range"]["negative_margin"] += 1
                elif margin < 25:
                    analysis["roles_by_margin_range"]["0_to_25_percent"] += 1
                elif margin < 50:
                    analysis["roles_by_margin_range"]["25_to_50_percent"] += 1
                else:
                    analysis["roles_by_margin_range"]["50_plus_percent"] += 1

        if margins:
            analysis["margin_statistics"] = {
                "min_margin": min(margins),
                "max_margin": max(margins),
                "avg_margin": sum(margins) / len(margins),
            }

        return analysis
