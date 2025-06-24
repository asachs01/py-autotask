"""
Products Entity for py-autotask

This module provides the ProductsEntity class for managing products
in Autotask. Products represent items that can be sold, installed,
or serviced, including hardware, software, and services.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ProductsEntity(BaseEntity):
    """
    Manages Autotask Products - product catalog and inventory management.

    Products represent items that can be sold, installed, or serviced
    within Autotask. They support pricing management, inventory tracking,
    and product lifecycle management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Products"

    def create_product(
        self,
        name: str,
        description: str,
        product_category: str,
        unit_price: Union[float, Decimal],
        unit_cost: Optional[Union[float, Decimal]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new product.

        Args:
            name: Name of the product
            description: Description of the product
            product_category: Category of the product
            unit_price: Selling price per unit
            unit_cost: Cost per unit (optional)
            **kwargs: Additional fields for the product

        Returns:
            Create response with new product ID
        """
        product_data = {
            "name": name,
            "description": description,
            "productCategory": product_category,
            "unitPrice": float(unit_price),
            **kwargs,
        }

        if unit_cost is not None:
            product_data["unitCost"] = float(unit_cost)

        return self.create(product_data)

    def get_active_products(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active products.

        Args:
            category: Optional product category to filter by

        Returns:
            List of active products
        """
        filters = ["isActive eq true"]

        if category:
            filters.append(f"productCategory eq '{category}'")

        return self.query(filter=" and ".join(filters))

    def get_products_by_category(
        self, category: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get products by category.

        Args:
            category: Product category
            active_only: Whether to only return active products

        Returns:
            List of products in the category
        """
        filters = [f"productCategory eq '{category}'"]

        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def search_products(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search products by name, description, or other fields.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching products
        """
        if search_fields is None:
            search_fields = ["name", "description", "manufacturerName", "vendorName"]

        filters = []
        for field in search_fields:
            filters.append(f"contains({field}, '{search_term}')")

        return self.query(filter=" or ".join(filters))

    def update_product_pricing(
        self,
        product_id: int,
        new_unit_price: Union[float, Decimal],
        new_unit_cost: Optional[Union[float, Decimal]] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update product pricing.

        Args:
            product_id: ID of the product
            new_unit_price: New selling price
            new_unit_cost: New cost price (optional)
            effective_date: When pricing becomes effective

        Returns:
            Update response
        """
        update_data = {"unitPrice": float(new_unit_price)}

        if new_unit_cost is not None:
            update_data["unitCost"] = float(new_unit_cost)
        if effective_date:
            update_data["priceEffectiveDate"] = effective_date.isoformat()

        return self.update(product_id, update_data)

    def calculate_product_margin(self, product_id: int) -> Dict[str, Any]:
        """
        Calculate profit margin for a product.

        Args:
            product_id: ID of the product

        Returns:
            Margin calculation details
        """
        product = self.get(product_id)

        unit_price = Decimal(str(product.get("unitPrice", 0)))
        unit_cost = Decimal(str(product.get("unitCost", 0)))

        if unit_price > 0:
            margin_amount = unit_price - unit_cost
            margin_percentage = (margin_amount / unit_price) * 100
        else:
            margin_amount = Decimal("0")
            margin_percentage = Decimal("0")

        return {
            "product_id": product_id,
            "product_name": product.get("name"),
            "pricing": {
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "margin_amount": margin_amount,
                "margin_percentage": margin_percentage,
            },
        }

    def get_products_by_price_range(
        self,
        min_price: Optional[Union[float, Decimal]] = None,
        max_price: Optional[Union[float, Decimal]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get products within a price range.

        Args:
            min_price: Minimum unit price
            max_price: Maximum unit price

        Returns:
            List of products within price range
        """
        filters = ["isActive eq true"]

        if min_price is not None:
            filters.append(f"unitPrice ge {float(min_price)}")
        if max_price is not None:
            filters.append(f"unitPrice le {float(max_price)}")

        return self.query(filter=" and ".join(filters))

    def get_product_sales_summary(
        self,
        product_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get sales summary for a product.

        Args:
            product_id: ID of the product
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Product sales summary
        """
        # This would typically query sales/invoice data
        # For now, return sales summary structure

        return {
            "product_id": product_id,
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "sales_summary": {
                "total_quantity_sold": 0,  # Would count from invoices/quotes
                "total_revenue": Decimal("0"),  # Would sum revenue
                "average_selling_price": Decimal("0"),  # Would calculate average
                "total_orders": 0,  # Would count orders
                "best_selling_month": None,  # Would identify peak period
            },
        }

    def bulk_update_pricing(
        self, pricing_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update pricing for multiple products.

        Args:
            pricing_updates: List of pricing updates
                Each should contain: product_id, unit_price, optional unit_cost

        Returns:
            Summary of bulk pricing update operation
        """
        results = []

        for update in pricing_updates:
            product_id = update["product_id"]
            unit_price = update["unit_price"]
            unit_cost = update.get("unit_cost")
            effective_date = update.get("effective_date")

            try:
                result = self.update_product_pricing(
                    product_id, unit_price, unit_cost, effective_date
                )
                results.append({"id": product_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": product_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(pricing_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_product_catalog_report(
        self, include_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive product catalog report.

        Args:
            include_inactive: Whether to include inactive products

        Returns:
            Product catalog report
        """
        filters = []
        if not include_inactive:
            filters.append("isActive eq true")

        products = self.query(filter=" and ".join(filters) if filters else None)

        # Analyze product catalog
        total_value = Decimal("0")
        categories = {}

        for product in products:
            category = product.get("productCategory", "Uncategorized")
            unit_price = Decimal(str(product.get("unitPrice", 0)))

            if category not in categories:
                categories[category] = {"count": 0, "total_value": Decimal("0")}

            categories[category]["count"] += 1
            categories[category]["total_value"] += unit_price
            total_value += unit_price

        return {
            "catalog_summary": {
                "total_products": len(products),
                "total_catalog_value": total_value,
                "categories": len(categories),
                "average_product_price": (
                    total_value / len(products) if products else Decimal("0")
                ),
            },
            "by_category": categories,
        }

    def clone_product(
        self,
        source_product_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing product.

        Args:
            source_product_id: ID of the product to clone
            new_name: Name for the new product
            new_description: Description for the new product

        Returns:
            Create response for the new product
        """
        source_product = self.get(source_product_id)

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_product.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        if new_description:
            clone_data["description"] = new_description

        return self.create(clone_data)
