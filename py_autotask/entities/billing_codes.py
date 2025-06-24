"""
BillingCodes Entity for py-autotask

This module provides the BillingCodesEntity class for managing billing codes
in Autotask. Billing codes define how time, expenses, and other charges are
categorized and billed to customers.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class BillingCodesEntity(BaseEntity):
    """
    Manages Autotask BillingCodes - billing code definitions and rates.

    Billing codes are used to categorize and price different types of work,
    expenses, and charges. They support hierarchical organization and
    flexible rate structures.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "BillingCodes"

    # Core CRUD Operations

    def create_billing_code(
        self,
        name: str,
        description: str,
        code_type: str,
        is_active: bool = True,
        unit_price: Optional[Union[float, Decimal]] = None,
        unit_cost: Optional[Union[float, Decimal]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new billing code.

        Args:
            name: Name of the billing code
            description: Description of the billing code
            code_type: Type of billing code (Labor, Material, Expense, etc.)
            is_active: Whether the billing code is active
            unit_price: Default unit price for this billing code
            unit_cost: Default unit cost for this billing code
            **kwargs: Additional fields for the billing code

        Returns:
            Create response with new billing code ID

        Example:
            billing_code = client.billing_codes.create_billing_code(
                name="Senior Engineer",
                description="Senior level engineering services",
                code_type="Labor",
                unit_price=150.00,
                unit_cost=75.00
            )
        """
        billing_code_data = {
            "name": name,
            "description": description,
            "codeType": code_type,
            "isActive": is_active,
            **kwargs,
        }

        if unit_price is not None:
            billing_code_data["unitPrice"] = float(unit_price)
        if unit_cost is not None:
            billing_code_data["unitCost"] = float(unit_cost)

        return self.create(billing_code_data)

    def get_active_billing_codes(
        self, code_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active billing codes.

        Args:
            code_type: Optional filter by code type

        Returns:
            List of active billing codes
        """
        filters = ["isActive eq true"]

        if code_type:
            filters.append(f"codeType eq '{code_type}'")

        return self.query(filter=" and ".join(filters))

    def get_billing_codes_by_type(
        self, code_type: str, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get billing codes by type.

        Args:
            code_type: Type of billing codes to retrieve
            include_inactive: Whether to include inactive codes

        Returns:
            List of billing codes of the specified type
        """
        filters = [f"codeType eq '{code_type}'"]

        if not include_inactive:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    # Business Logic Methods

    def update_billing_code_rates(
        self,
        billing_code_id: int,
        unit_price: Optional[Union[float, Decimal]] = None,
        unit_cost: Optional[Union[float, Decimal]] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update billing code rates with optional effective date.

        Args:
            billing_code_id: ID of the billing code to update
            unit_price: New unit price
            unit_cost: New unit cost
            effective_date: When the new rates become effective

        Returns:
            Update response
        """
        update_data = {}

        if unit_price is not None:
            update_data["unitPrice"] = float(unit_price)
        if unit_cost is not None:
            update_data["unitCost"] = float(unit_cost)
        if effective_date is not None:
            update_data["effectiveDate"] = effective_date.isoformat()

        return self.update(billing_code_id, update_data)

    def get_billing_code_hierarchy(
        self, parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get billing code hierarchy starting from a parent.

        Args:
            parent_id: ID of parent billing code (None for root level)

        Returns:
            List of billing codes in hierarchy
        """
        if parent_id is None:
            filters = ["parentID eq null"]
        else:
            filters = [f"parentID eq {parent_id}"]

        return self.query(filter=" and ".join(filters))

    def calculate_rate_markup(
        self, billing_code_id: int, markup_percentage: Union[float, Decimal]
    ) -> Dict[str, Any]:
        """
        Calculate new rates with markup percentage.

        Args:
            billing_code_id: ID of the billing code
            markup_percentage: Markup percentage (e.g., 50 for 50%)

        Returns:
            Dictionary with current and calculated rates
        """
        billing_code = self.get(billing_code_id)

        current_cost = Decimal(str(billing_code.get("unitCost", 0)))
        current_price = Decimal(str(billing_code.get("unitPrice", 0)))
        markup_factor = Decimal(str(markup_percentage)) / 100

        new_price = current_cost * (1 + markup_factor)

        return {
            "billing_code_id": billing_code_id,
            "current_cost": current_cost,
            "current_price": current_price,
            "markup_percentage": markup_percentage,
            "calculated_price": new_price,
            "price_change": new_price - current_price,
            "effective_markup": (
                float((current_price - current_cost) / current_cost * 100)
                if current_cost > 0
                else 0
            ),
        }

    def bulk_update_rates(self, rate_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update rates for multiple billing codes.

        Args:
            rate_updates: List of rate update dictionaries
                Each should contain: billing_code_id, unit_price?, unit_cost?

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in rate_updates:
            billing_code_id = update["billing_code_id"]
            update_data = {k: v for k, v in update.items() if k != "billing_code_id"}

            try:
                result = self.update(billing_code_id, update_data)
                results.append(
                    {"id": billing_code_id, "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"id": billing_code_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(rate_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_billing_code_usage_report(
        self, billing_code_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Get usage report for a specific billing code.

        Args:
            billing_code_id: ID of the billing code
            date_from: Start date for report
            date_to: End date for report

        Returns:
            Usage statistics for the billing code
        """
        # This would typically query related entities like TimeEntries, BillingItems
        # For now, we'll provide a structure that could be populated

        return {
            "billing_code_id": billing_code_id,
            "reporting_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "usage_summary": {
                "total_hours": 0,  # Would be calculated from TimeEntries
                "total_items": 0,  # Would be calculated from BillingItems
                "total_revenue": Decimal("0"),
                "total_cost": Decimal("0"),
                "profit_margin": Decimal("0"),
            },
            "usage_by_entity": {
                "time_entries": 0,
                "billing_items": 0,
                "project_charges": 0,
                "ticket_charges": 0,
            },
        }

    def activate_billing_code(self, billing_code_id: int) -> Dict[str, Any]:
        """
        Activate a billing code.

        Args:
            billing_code_id: ID of the billing code to activate

        Returns:
            Update response
        """
        return self.update(billing_code_id, {"isActive": True})

    def deactivate_billing_code(self, billing_code_id: int) -> Dict[str, Any]:
        """
        Deactivate a billing code.

        Args:
            billing_code_id: ID of the billing code to deactivate

        Returns:
            Update response
        """
        return self.update(billing_code_id, {"isActive": False})

    def get_billing_codes_with_rates(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get billing codes with their current rates.

        Args:
            include_inactive: Whether to include inactive codes

        Returns:
            List of billing codes with rate information
        """
        filters = []

        if not include_inactive:
            filters.append("isActive eq true")

        billing_codes = self.query(filter=" and ".join(filters) if filters else None)

        # Enhance with calculated fields
        for code in billing_codes:
            unit_price = Decimal(str(code.get("unitPrice", 0)))
            unit_cost = Decimal(str(code.get("unitCost", 0)))

            code["profit_margin"] = unit_price - unit_cost
            code["markup_percentage"] = (
                float((unit_price - unit_cost) / unit_cost * 100)
                if unit_cost > 0
                else 0
            )

        return billing_codes

    def search_billing_codes(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search billing codes by name, description, or other fields.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching billing codes
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        filters = []
        for field in search_fields:
            filters.append(f"contains({field}, '{search_term}')")

        return self.query(filter=" or ".join(filters))

    def get_billing_code_rate_history(
        self, billing_code_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get rate change history for a billing code.

        Args:
            billing_code_id: ID of the billing code

        Returns:
            List of rate changes (would be from a rate history table)
        """
        # This would typically query a rate history table
        # For now, return structure that could be populated

        return [
            {
                "billing_code_id": billing_code_id,
                "effective_date": datetime.now().isoformat(),
                "unit_price": 0,
                "unit_cost": 0,
                "changed_by_resource_id": None,
                "change_reason": "Rate adjustment",
            }
        ]

    def copy_billing_code(
        self,
        source_billing_code_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing billing code.

        Args:
            source_billing_code_id: ID of the billing code to copy
            new_name: Name for the new billing code
            new_description: Description for the new billing code

        Returns:
            Create response for the new billing code
        """
        source_code = self.get(source_billing_code_id)

        # Remove fields that shouldn't be copied
        copy_data = {
            k: v
            for k, v in source_code.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        copy_data["name"] = new_name
        if new_description:
            copy_data["description"] = new_description

        return self.create(copy_data)

    def get_billing_codes_by_price_range(
        self,
        min_price: Optional[Union[float, Decimal]] = None,
        max_price: Optional[Union[float, Decimal]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing codes within a price range.

        Args:
            min_price: Minimum unit price
            max_price: Maximum unit price

        Returns:
            List of billing codes within the price range
        """
        filters = []

        if min_price is not None:
            filters.append(f"unitPrice ge {float(min_price)}")
        if max_price is not None:
            filters.append(f"unitPrice le {float(max_price)}")

        return self.query(filter=" and ".join(filters) if filters else None)
