"""
ShippingTypes Entity for py-autotask

This module provides the ShippingTypesEntity class for managing shipping methods
and delivery options in Autotask. Shipping Types define available delivery methods,
costs, and tracking capabilities for product shipments.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ShippingTypesEntity(BaseEntity):
    """
    Manages Autotask ShippingTypes - shipping methods and delivery options.

    Shipping Types define the available shipping methods, delivery timeframes,
    costs, and tracking capabilities for product shipments. They support
    integration with shipping carriers and automated shipping calculations.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ShippingTypes"

    def create_shipping_type(
        self,
        name: str,
        description: str,
        carrier: str,
        delivery_days: Optional[int] = None,
        cost_calculation_method: Optional[str] = None,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new shipping type.

        Args:
            name: Name of the shipping type
            description: Description of the shipping method
            carrier: Shipping carrier name
            delivery_days: Expected delivery days
            cost_calculation_method: Method for calculating shipping costs
            is_active: Whether the shipping type is active
            **kwargs: Additional fields for the shipping type

        Returns:
            Create response with new shipping type ID
        """
        shipping_data = {
            "name": name,
            "description": description,
            "carrier": carrier,
            "isActive": is_active,
            **kwargs,
        }

        if delivery_days is not None:
            shipping_data["deliveryDays"] = delivery_days
        if cost_calculation_method:
            shipping_data["costCalculationMethod"] = cost_calculation_method

        return self.create(shipping_data)

    def get_active_shipping_types(
        self, carrier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active shipping types.

        Args:
            carrier: Optional carrier to filter by

        Returns:
            List of active shipping types
        """
        filters = [{"field": "isActive", "op": "eq", "value": "true"}]

        if carrier:
            filters.append({"field": "carrier", "op": "eq", "value": carrier})

        return self.query(filters=filters).items

    def get_shipping_types_by_carrier(self, carrier: str) -> List[Dict[str, Any]]:
        """
        Get shipping types for a specific carrier.

        Args:
            carrier: Name of the shipping carrier

        Returns:
            List of shipping types for the carrier
        """
        return self.query(
            filters=[{"field": "carrier", "op": "eq", "value": carrier}]
        ).items

    def calculate_shipping_cost(
        self,
        shipping_type_id: int,
        weight: float,
        dimensions: Optional[Dict[str, float]] = None,
        destination_zone: Optional[str] = None,
        declared_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate shipping cost for given parameters.

        Args:
            shipping_type_id: ID of the shipping type
            weight: Package weight
            dimensions: Optional package dimensions (length, width, height)
            destination_zone: Optional destination zone for zoned pricing
            declared_value: Optional declared value for insurance

        Returns:
            Shipping cost calculation results
        """
        shipping_type = self.get(shipping_type_id)

        if not shipping_type:
            raise ValueError(f"Shipping type {shipping_type_id} not found")

        cost_method = shipping_type.get("costCalculationMethod", "flat_rate")
        base_cost = float(shipping_type.get("baseCost", 0))

        calculated_cost = base_cost
        calculation_details = {
            "base_cost": base_cost,
            "weight_charge": 0.0,
            "dimension_charge": 0.0,
            "zone_charge": 0.0,
            "insurance_charge": 0.0,
        }

        # Apply weight-based calculations
        if cost_method in ["per_pound", "tiered_weight"]:
            weight_rate = float(shipping_type.get("weightRate", 0))
            weight_charge = weight * weight_rate
            calculated_cost += weight_charge
            calculation_details["weight_charge"] = weight_charge

        # Apply dimensional calculations
        if dimensions and cost_method == "dimensional":
            dimensional_factor = float(shipping_type.get("dimensionalFactor", 139))
            dim_weight = (
                dimensions["length"] * dimensions["width"] * dimensions["height"]
            ) / dimensional_factor
            actual_weight = max(weight, dim_weight)
            dimensional_rate = float(shipping_type.get("dimensionalRate", 0))
            dimension_charge = actual_weight * dimensional_rate
            calculated_cost += dimension_charge
            calculation_details["dimension_charge"] = dimension_charge

        # Apply zone-based pricing
        if destination_zone and shipping_type.get("supportsZonePricing"):
            zone_rate = float(shipping_type.get(f"zone{destination_zone}Rate", 0))
            calculated_cost += zone_rate
            calculation_details["zone_charge"] = zone_rate

        # Apply insurance if declared value provided
        if declared_value and shipping_type.get("supportsInsurance"):
            insurance_rate = float(
                shipping_type.get("insuranceRate", 0.01)
            )  # 1% default
            insurance_charge = declared_value * insurance_rate
            calculated_cost += insurance_charge
            calculation_details["insurance_charge"] = insurance_charge

        return {
            "shipping_type_id": shipping_type_id,
            "shipping_type_name": shipping_type.get("name"),
            "carrier": shipping_type.get("carrier"),
            "calculation_method": cost_method,
            "input_parameters": {
                "weight": weight,
                "dimensions": dimensions,
                "destination_zone": destination_zone,
                "declared_value": declared_value,
            },
            "calculation_details": calculation_details,
            "total_cost": round(calculated_cost, 2),
            "estimated_delivery_days": shipping_type.get("deliveryDays"),
        }

    def get_shipping_options_comparison(
        self,
        weight: float,
        dimensions: Optional[Dict[str, float]] = None,
        destination_zone: Optional[str] = None,
        max_cost: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get comparison of shipping options for given parameters.

        Args:
            weight: Package weight
            dimensions: Optional package dimensions
            destination_zone: Optional destination zone
            max_cost: Optional maximum cost filter

        Returns:
            List of shipping options with costs and delivery times
        """
        active_types = self.get_active_shipping_types()
        options = []

        for shipping_type in active_types:
            try:
                cost_calc = self.calculate_shipping_cost(
                    shipping_type["id"], weight, dimensions, destination_zone
                )

                if max_cost is None or cost_calc["total_cost"] <= max_cost:
                    options.append(
                        {
                            "shipping_type_id": shipping_type["id"],
                            "name": shipping_type["name"],
                            "carrier": shipping_type["carrier"],
                            "cost": cost_calc["total_cost"],
                            "delivery_days": shipping_type.get("deliveryDays"),
                            "supports_tracking": shipping_type.get(
                                "supportsTracking", False
                            ),
                            "supports_insurance": shipping_type.get(
                                "supportsInsurance", False
                            ),
                        }
                    )
            except Exception as e:
                self.logger.warning(
                    f"Failed to calculate cost for shipping type {shipping_type['id']}: {e}"
                )
                continue

        # Sort by cost (ascending)
        options.sort(key=lambda x: x["cost"])
        return options

    def update_shipping_rates(
        self,
        shipping_type_id: int,
        base_cost: Optional[float] = None,
        weight_rate: Optional[float] = None,
        zone_rates: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Update shipping rates for a shipping type.

        Args:
            shipping_type_id: ID of the shipping type
            base_cost: Optional new base cost
            weight_rate: Optional new weight rate
            zone_rates: Optional zone-specific rates

        Returns:
            Updated shipping type data
        """
        update_data = {"id": shipping_type_id}

        if base_cost is not None:
            update_data["baseCost"] = base_cost
        if weight_rate is not None:
            update_data["weightRate"] = weight_rate
        if zone_rates:
            for zone, rate in zone_rates.items():
                update_data[f"zone{zone}Rate"] = rate

        return self.update(update_data)

    def get_carrier_performance_report(
        self, carrier: str, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Generate performance report for a shipping carrier.

        Args:
            carrier: Name of the shipping carrier
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Carrier performance report
        """
        shipping_types = self.get_shipping_types_by_carrier(carrier)

        # This would typically analyze shipment data
        # For now, return performance report structure
        return {
            "carrier": carrier,
            "analysis_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "shipping_types_count": len(shipping_types),
            "performance_metrics": {
                "total_shipments": 0,  # Would query actual shipment data
                "on_time_deliveries": 0,
                "delayed_deliveries": 0,
                "damaged_packages": 0,
                "lost_packages": 0,
                "average_delivery_time": 0.0,
                "on_time_percentage": 0.0,
                "damage_rate": 0.0,
                "loss_rate": 0.0,
            },
            "cost_analysis": {
                "total_shipping_costs": 0.0,
                "average_cost_per_shipment": 0.0,
                "cost_per_pound": 0.0,
            },
        }

    def activate_shipping_type(self, shipping_type_id: int) -> Dict[str, Any]:
        """
        Activate a shipping type.

        Args:
            shipping_type_id: ID of the shipping type

        Returns:
            Updated shipping type data
        """
        return self.update({"id": shipping_type_id, "isActive": True})

    def deactivate_shipping_type(self, shipping_type_id: int) -> Dict[str, Any]:
        """
        Deactivate a shipping type.

        Args:
            shipping_type_id: ID of the shipping type

        Returns:
            Updated shipping type data
        """
        return self.update({"id": shipping_type_id, "isActive": False})

    def bulk_update_carrier_rates(
        self, carrier: str, rate_adjustments: Dict[str, Union[float, Dict[str, float]]]
    ) -> Dict[str, Any]:
        """
        Bulk update rates for all shipping types of a carrier.

        Args:
            carrier: Name of the shipping carrier
            rate_adjustments: Dictionary of rate adjustments
                Can include: base_cost_multiplier, weight_rate_adjustment, zone_rate_adjustments

        Returns:
            Summary of bulk update operation
        """
        shipping_types = self.get_shipping_types_by_carrier(carrier)
        results = []

        base_multiplier = rate_adjustments.get("base_cost_multiplier", 1.0)
        weight_adjustment = rate_adjustments.get("weight_rate_adjustment", 0.0)
        zone_adjustments = rate_adjustments.get("zone_rate_adjustments", {})

        for shipping_type in shipping_types:
            try:
                update_data = {"id": shipping_type["id"]}

                # Update base cost
                if "baseCost" in shipping_type:
                    current_base = float(shipping_type["baseCost"])
                    update_data["baseCost"] = current_base * base_multiplier

                # Update weight rate
                if "weightRate" in shipping_type:
                    current_weight_rate = float(shipping_type["weightRate"])
                    update_data["weightRate"] = current_weight_rate + weight_adjustment

                # Update zone rates
                for zone, adjustment in zone_adjustments.items():
                    zone_field = f"zone{zone}Rate"
                    if zone_field in shipping_type:
                        current_zone_rate = float(shipping_type[zone_field])
                        update_data[zone_field] = current_zone_rate + adjustment

                self.update(update_data)
                results.append(
                    {
                        "shipping_type_id": shipping_type["id"],
                        "name": shipping_type["name"],
                        "success": True,
                        "updated_fields": list(update_data.keys()),
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "shipping_type_id": shipping_type["id"],
                        "name": shipping_type.get("name", "Unknown"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "carrier": carrier,
            "total_shipping_types": len(shipping_types),
            "successful_updates": len(successful),
            "failed_updates": len(failed),
            "rate_adjustments_applied": rate_adjustments,
            "results": results,
        }

    def clone_shipping_type(
        self,
        source_shipping_type_id: int,
        new_name: str,
        new_carrier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing shipping type.

        Args:
            source_shipping_type_id: ID of the shipping type to clone
            new_name: Name for the new shipping type
            new_carrier: Optional new carrier name

        Returns:
            Create response for the new shipping type
        """
        source_type = self.get(source_shipping_type_id)

        if not source_type:
            raise ValueError(
                f"Source shipping type {source_shipping_type_id} not found"
            )

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_type.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        if new_carrier:
            clone_data["carrier"] = new_carrier

        return self.create(clone_data)
