"""
Product Vendors entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class ProductVendorsEntity(BaseEntity):
    """
    Handles all Product Vendor-related operations for the Autotask API.

    Product vendors define vendor relationships and pricing information
    for products, enabling vendor management and procurement tracking.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_product_vendor(
        self,
        product_id: int,
        vendor_id: int,
        vendor_product_number: Optional[str] = None,
        vendor_cost: Optional[float] = None,
        is_primary_vendor: bool = False,
        minimum_order_quantity: Optional[int] = None,
        **kwargs,
    ) -> EntityDict:
        """Create a new product vendor relationship."""
        vendor_data = {
            "ProductID": product_id,
            "VendorID": vendor_id,
            "IsPrimaryVendor": is_primary_vendor,
            **kwargs,
        }

        if vendor_product_number:
            vendor_data["VendorProductNumber"] = vendor_product_number
        if vendor_cost is not None:
            vendor_data["VendorCost"] = vendor_cost
        if minimum_order_quantity is not None:
            vendor_data["MinimumOrderQuantity"] = minimum_order_quantity

        return self.create(vendor_data)

    def get_vendors_for_product(self, product_id: int) -> List[EntityDict]:
        """Get all vendors for a specific product."""
        return self.query_all(
            filters={"field": "ProductID", "op": "eq", "value": product_id}
        )

    def get_products_for_vendor(self, vendor_id: int) -> List[EntityDict]:
        """Get all products for a specific vendor."""
        return self.query_all(
            filters={"field": "VendorID", "op": "eq", "value": vendor_id}
        )

    def get_primary_vendor_for_product(self, product_id: int) -> Optional[EntityDict]:
        """Get the primary vendor for a product."""
        vendors = self.query_all(
            filters=[
                {"field": "ProductID", "op": "eq", "value": product_id},
                {"field": "IsPrimaryVendor", "op": "eq", "value": "true"},
            ]
        )
        return vendors[0] if vendors else None

    def set_primary_vendor(self, product_id: int, vendor_id: int) -> Dict[str, Any]:
        """Set a vendor as the primary vendor for a product."""
        # First, unset any existing primary vendor
        existing_primary = self.get_primary_vendor_for_product(product_id)
        if existing_primary and existing_primary.get("VendorID") != vendor_id:
            self.update_by_id(existing_primary["id"], {"IsPrimaryVendor": False})

        # Set the new primary vendor
        vendors = self.query_all(
            filters=[
                {"field": "ProductID", "op": "eq", "value": product_id},
                {"field": "VendorID", "op": "eq", "value": vendor_id},
            ]
        )

        if not vendors:
            raise ValueError(
                f"No vendor relationship found for product {product_id} and vendor {vendor_id}"
            )

        updated = self.update_by_id(vendors[0]["id"], {"IsPrimaryVendor": True})

        return {
            "product_id": product_id,
            "new_primary_vendor_id": vendor_id,
            "previous_primary_vendor_id": (
                existing_primary.get("VendorID") if existing_primary else None
            ),
            "updated_relationship": updated,
        }

    def update_vendor_cost(
        self, product_id: int, vendor_id: int, new_cost: float
    ) -> EntityDict:
        """Update vendor cost for a product."""
        vendors = self.query_all(
            filters=[
                {"field": "ProductID", "op": "eq", "value": product_id},
                {"field": "VendorID", "op": "eq", "value": vendor_id},
            ]
        )

        if not vendors:
            raise ValueError(
                f"No vendor relationship found for product {product_id} and vendor {vendor_id}"
            )

        return self.update_by_id(vendors[0]["id"], {"VendorCost": new_cost})

    def bulk_update_vendor_costs(
        self,
        vendor_id: int,
        cost_updates: List[Dict[str, Any]],
        percentage_adjustment: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Update costs for multiple products from a vendor."""
        results = []

        for update in cost_updates:
            product_id = update["product_id"]
            new_cost = update.get("new_cost")

            # Apply percentage adjustment if specified
            if percentage_adjustment and not new_cost:
                current_vendors = self.query_all(
                    filters=[
                        {"field": "ProductID", "op": "eq", "value": product_id},
                        {"field": "VendorID", "op": "eq", "value": vendor_id},
                    ]
                )
                if current_vendors:
                    current_cost = current_vendors[0].get("VendorCost", 0)
                    new_cost = current_cost * (1 + percentage_adjustment / 100)

            if new_cost is None:
                results.append(
                    {
                        "product_id": product_id,
                        "status": "skipped",
                        "reason": "no cost provided",
                    }
                )
                continue

            try:
                self.update_vendor_cost(product_id, vendor_id, new_cost)
                results.append(
                    {
                        "product_id": product_id,
                        "new_cost": new_cost,
                        "status": "success",
                    }
                )
            except Exception as e:
                results.append(
                    {"product_id": product_id, "status": "failed", "error": str(e)}
                )

        return results

    def get_cost_comparison_for_product(self, product_id: int) -> Dict[str, Any]:
        """Get cost comparison across all vendors for a product."""
        vendors = self.get_vendors_for_product(product_id)

        comparison = {
            "product_id": product_id,
            "vendor_costs": [],
            "cost_statistics": {},
        }

        costs = []
        primary_vendor_cost = None

        for vendor in vendors:
            vendor_cost = vendor.get("VendorCost")
            vendor_info = {
                "vendor_id": vendor.get("VendorID"),
                "vendor_cost": vendor_cost,
                "vendor_product_number": vendor.get("VendorProductNumber"),
                "is_primary": vendor.get("IsPrimaryVendor", False),
                "minimum_order_qty": vendor.get("MinimumOrderQuantity"),
            }

            comparison["vendor_costs"].append(vendor_info)

            if vendor_cost is not None:
                costs.append(vendor_cost)
                if vendor.get("IsPrimaryVendor"):
                    primary_vendor_cost = vendor_cost

        if costs:
            comparison["cost_statistics"] = {
                "min_cost": min(costs),
                "max_cost": max(costs),
                "avg_cost": sum(costs) / len(costs),
                "cost_variance": max(costs) - min(costs),
                "primary_vendor_cost": primary_vendor_cost,
                "vendors_with_costs": len(costs),
            }

        return comparison

    def get_vendor_product_catalog(self, vendor_id: int) -> Dict[str, Any]:
        """Get product catalog summary for a vendor."""
        products = self.get_products_for_vendor(vendor_id)

        catalog = {
            "vendor_id": vendor_id,
            "total_products": len(products),
            "primary_products": len([p for p in products if p.get("IsPrimaryVendor")]),
            "products_with_costs": len(
                [p for p in products if p.get("VendorCost") is not None]
            ),
            "cost_summary": {},
        }

        costs = [
            p.get("VendorCost") for p in products if p.get("VendorCost") is not None
        ]

        if costs:
            catalog["cost_summary"] = {
                "min_cost": min(costs),
                "max_cost": max(costs),
                "avg_cost": sum(costs) / len(costs),
                "total_catalog_value": sum(costs),
            }

        return catalog

    def remove_vendor_relationship(self, product_id: int, vendor_id: int) -> bool:
        """Remove vendor relationship for a product."""
        vendors = self.query_all(
            filters=[
                {"field": "ProductID", "op": "eq", "value": product_id},
                {"field": "VendorID", "op": "eq", "value": vendor_id},
            ]
        )

        if not vendors:
            return False

        return self.delete(vendors[0]["id"])
