"""
VendorTypes Entity for py-autotask

This module provides the VendorTypesEntity class for managing vendor types
in Autotask. Vendor types classify vendors by category, relationship type,
and business function for better organization and reporting.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class VendorTypesEntity(BaseEntity):
    """
    Manages Autotask VendorTypes - vendor classification and categorization.

    Vendor types classify vendors by category, relationship type, and business
    function within Autotask. They support vendor organization, reporting,
    and relationship management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "VendorTypes"

    def create_vendor_type(
        self,
        name: str,
        description: str,
        category: str,
        payment_terms_days: int = 30,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new vendor type.

        Args:
            name: Name of the vendor type
            description: Description of the vendor type
            category: Category of vendor (Software, Hardware, Services, etc.)
            payment_terms_days: Default payment terms in days
            is_active: Whether the vendor type is active
            **kwargs: Additional fields for the vendor type

        Returns:
            Create response with new vendor type ID
        """
        vendor_type_data = {
            "name": name,
            "description": description,
            "category": category,
            "paymentTermsDays": payment_terms_days,
            "isActive": is_active,
            **kwargs,
        }

        return self.create(vendor_type_data)

    def get_active_vendor_types(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active vendor types.

        Args:
            category: Optional category to filter by

        Returns:
            List of active vendor types
        """
        filters = ["isActive eq true"]

        if category:
            filters.append(f"category eq '{category}'")

        return self.query(filter=" and ".join(filters))

    def get_vendor_types_by_category(
        self, category: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get vendor types by category.

        Args:
            category: Category to filter by
            active_only: Whether to only return active vendor types

        Returns:
            List of vendor types in the specified category
        """
        filters = [f"category eq '{category}'"]

        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def get_vendor_type_statistics(self, vendor_type_id: int) -> Dict[str, Any]:
        """
        Get statistics for a vendor type.

        Args:
            vendor_type_id: ID of the vendor type

        Returns:
            Vendor type statistics
        """
        # This would typically query related vendors and transactions
        # For now, return statistics structure

        vendor_type = self.get(vendor_type_id)

        return {
            "vendor_type_id": vendor_type_id,
            "name": vendor_type.get("name"),
            "category": vendor_type.get("category"),
            "statistics": {
                "total_vendors": 0,  # Would count vendors of this type
                "active_vendors": 0,  # Would count active vendors
                "total_spend": Decimal("0.00"),  # Would sum vendor spending
                "average_payment_terms": 0,  # Would calculate avg payment terms
                "on_time_payment_rate": 0.0,  # Would calculate payment performance
            },
        }

    def get_vendor_types_spending_summary(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get spending summary by vendor type.

        Args:
            date_from: Start date for spending analysis
            date_to: End date for spending analysis

        Returns:
            Spending summary by vendor type
        """
        vendor_types = self.query()

        # This would typically aggregate spending data
        # For now, return summary structure

        spending_by_type = {}
        for vendor_type in vendor_types:
            type_id = vendor_type.get("id")
            type_name = vendor_type.get("name")
            category = vendor_type.get("category")

            spending_by_type[type_id] = {
                "name": type_name,
                "category": category,
                "total_spend": Decimal("0.00"),  # Would calculate actual spending
                "vendor_count": 0,  # Would count vendors
                "transaction_count": 0,  # Would count transactions
            }

        return {
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "spending_by_type": spending_by_type,
            "total_spending": Decimal("0.00"),  # Would sum all spending
            "most_expensive_type": None,  # Would identify highest spend
            "least_expensive_type": None,  # Would identify lowest spend
        }

    def activate_vendor_type(self, vendor_type_id: int) -> Dict[str, Any]:
        """
        Activate a vendor type.

        Args:
            vendor_type_id: ID of the vendor type to activate

        Returns:
            Update response
        """
        return self.update(vendor_type_id, {"isActive": True})

    def deactivate_vendor_type(self, vendor_type_id: int) -> Dict[str, Any]:
        """
        Deactivate a vendor type.

        Args:
            vendor_type_id: ID of the vendor type to deactivate

        Returns:
            Update response
        """
        return self.update(vendor_type_id, {"isActive": False})

    def update_payment_terms(
        self, vendor_type_id: int, payment_terms_days: int
    ) -> Dict[str, Any]:
        """
        Update payment terms for a vendor type.

        Args:
            vendor_type_id: ID of the vendor type
            payment_terms_days: New payment terms in days

        Returns:
            Update response
        """
        return self.update(vendor_type_id, {"paymentTermsDays": payment_terms_days})

    def clone_vendor_type(
        self,
        source_vendor_type_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing vendor type.

        Args:
            source_vendor_type_id: ID of the vendor type to clone
            new_name: Name for the new vendor type
            new_description: Description for the new vendor type

        Returns:
            Create response for the new vendor type
        """
        source_vendor_type = self.get(source_vendor_type_id)

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_vendor_type.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        clone_data["isActive"] = True
        if new_description:
            clone_data["description"] = new_description

        return self.create(clone_data)

    def get_vendor_types_summary(self) -> Dict[str, Any]:
        """
        Get summary of all vendor types.

        Returns:
            Summary of vendor types by various categories
        """
        vendor_types = self.query()

        # Group by category
        category_groups = {}
        payment_terms_groups = {}

        for vendor_type in vendor_types:
            category = vendor_type.get("category", "Unknown")
            payment_terms = vendor_type.get("paymentTermsDays", 0)

            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(vendor_type)

            # Group by payment terms ranges
            if payment_terms <= 15:
                terms_group = "1-15 days"
            elif payment_terms <= 30:
                terms_group = "16-30 days"
            elif payment_terms <= 60:
                terms_group = "31-60 days"
            else:
                terms_group = "60+ days"

            if terms_group not in payment_terms_groups:
                payment_terms_groups[terms_group] = []
            payment_terms_groups[terms_group].append(vendor_type)

        active_count = len([vt for vt in vendor_types if vt.get("isActive")])
        inactive_count = len(vendor_types) - active_count

        return {
            "total_vendor_types": len(vendor_types),
            "active_vendor_types": active_count,
            "inactive_vendor_types": inactive_count,
            "by_category": {
                category: len(types) for category, types in category_groups.items()
            },
            "by_payment_terms": {
                terms: len(types) for terms, types in payment_terms_groups.items()
            },
            "category_distribution": category_groups,
            "payment_terms_distribution": payment_terms_groups,
        }

    def bulk_update_payment_terms(
        self, payment_terms_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update payment terms for multiple vendor types.

        Args:
            payment_terms_updates: List of updates
                Each should contain: vendor_type_id, payment_terms_days

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in payment_terms_updates:
            vendor_type_id = update["vendor_type_id"]
            payment_terms_days = update["payment_terms_days"]

            try:
                result = self.update_payment_terms(vendor_type_id, payment_terms_days)
                results.append(
                    {"id": vendor_type_id, "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"id": vendor_type_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(payment_terms_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }
