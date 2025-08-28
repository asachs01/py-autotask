"""
Price List Work Type Modifiers entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PriceListWorkTypeModifiersEntity(BaseEntity):
    """
    Handles all Price List Work Type Modifier-related operations for the Autotask API.

    Price list work type modifiers define rate adjustments for different
    types of work within price lists (e.g., overtime, weekend, holiday rates).
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_work_type_modifier(
        self,
        price_list_id: int,
        work_type_id: int,
        modifier_percentage: float,
        is_active: bool = True,
        effective_date: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """Create a new price list work type modifier."""
        modifier_data = {
            "PriceListID": price_list_id,
            "WorkTypeID": work_type_id,
            "ModifierPercentage": modifier_percentage,
            "IsActive": is_active,
            **kwargs,
        }

        if effective_date:
            modifier_data["EffectiveDate"] = effective_date

        return self.create(modifier_data)

    def get_modifiers_for_price_list(
        self, price_list_id: int, active_only: bool = True
    ) -> List[EntityDict]:
        """Get all work type modifiers for a specific price list."""
        filters = [{"field": "PriceListID", "op": "eq", "value": price_list_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_modifier_for_work_type(
        self, price_list_id: int, work_type_id: int
    ) -> Optional[EntityDict]:
        """Get modifier for a specific work type in a price list."""
        modifiers = self.query_all(
            filters=[
                {"field": "PriceListID", "op": "eq", "value": price_list_id},
                {"field": "WorkTypeID", "op": "eq", "value": work_type_id},
                {"field": "IsActive", "op": "eq", "value": "true"},
            ]
        )
        return modifiers[0] if modifiers else None

    def update_modifier_percentage(
        self, price_list_id: int, work_type_id: int, new_percentage: float
    ) -> EntityDict:
        """Update modifier percentage for a work type."""
        modifier = self.get_modifier_for_work_type(price_list_id, work_type_id)
        if not modifier:
            raise ValueError(
                f"No modifier found for work type {work_type_id} in price list {price_list_id}"
            )

        return self.update_by_id(modifier["id"], {"ModifierPercentage": new_percentage})

    def apply_global_modifier_adjustment(
        self, price_list_id: int, adjustment_percentage: float
    ) -> List[Dict[str, Any]]:
        """Apply percentage adjustment to all modifiers in a price list."""
        modifiers = self.get_modifiers_for_price_list(price_list_id)
        results = []

        for modifier in modifiers:
            work_type_id = modifier.get("WorkTypeID")
            current_percentage = modifier.get("ModifierPercentage", 0)
            new_percentage = current_percentage * (1 + adjustment_percentage / 100)

            try:
                updated = self.update_modifier_percentage(
                    price_list_id, work_type_id, new_percentage
                )
                results.append(
                    {
                        "work_type_id": work_type_id,
                        "old_percentage": current_percentage,
                        "new_percentage": new_percentage,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {"work_type_id": work_type_id, "status": "failed", "error": str(e)}
                )

        return results

    def get_modifier_comparison(
        self, work_type_id: int, price_list_ids: List[int]
    ) -> Dict[str, Any]:
        """Compare modifiers for a work type across price lists."""
        comparison = {"work_type_id": work_type_id, "modifier_comparisons": []}

        for price_list_id in price_list_ids:
            modifier = self.get_modifier_for_work_type(price_list_id, work_type_id)

            if modifier:
                comparison["modifier_comparisons"].append(
                    {
                        "price_list_id": price_list_id,
                        "modifier_percentage": modifier.get("ModifierPercentage", 0),
                        "effective_date": modifier.get("EffectiveDate"),
                        "is_active": modifier.get("IsActive"),
                    }
                )
            else:
                comparison["modifier_comparisons"].append(
                    {
                        "price_list_id": price_list_id,
                        "modifier_percentage": None,
                        "status": "not_found",
                    }
                )

        return comparison

    def calculate_adjusted_rate(
        self, base_rate: float, price_list_id: int, work_type_id: int
    ) -> Dict[str, Any]:
        """Calculate adjusted rate using work type modifier."""
        modifier = self.get_modifier_for_work_type(price_list_id, work_type_id)

        if not modifier:
            return {
                "base_rate": base_rate,
                "modifier_percentage": 0,
                "adjusted_rate": base_rate,
                "modifier_applied": False,
            }

        modifier_percentage = modifier.get("ModifierPercentage", 0)
        adjusted_rate = base_rate * (1 + modifier_percentage / 100)

        return {
            "base_rate": base_rate,
            "modifier_percentage": modifier_percentage,
            "adjusted_rate": adjusted_rate,
            "modifier_applied": True,
            "rate_difference": adjusted_rate - base_rate,
        }

    def get_modifier_summary(self, price_list_id: int) -> Dict[str, Any]:
        """Get summary of work type modifiers for a price list."""
        modifiers = self.get_modifiers_for_price_list(price_list_id)

        if not modifiers:
            return {
                "price_list_id": price_list_id,
                "total_modifiers": 0,
                "modifier_statistics": None,
            }

        percentages = [m.get("ModifierPercentage", 0) for m in modifiers]
        positive_modifiers = [p for p in percentages if p > 0]
        negative_modifiers = [p for p in percentages if p < 0]

        return {
            "price_list_id": price_list_id,
            "total_modifiers": len(modifiers),
            "active_modifiers": len([m for m in modifiers if m.get("IsActive")]),
            "modifier_statistics": {
                "min_percentage": min(percentages),
                "max_percentage": max(percentages),
                "avg_percentage": sum(percentages) / len(percentages),
                "positive_modifiers": len(positive_modifiers),
                "negative_modifiers": len(negative_modifiers),
                "neutral_modifiers": len([p for p in percentages if p == 0]),
            },
        }
