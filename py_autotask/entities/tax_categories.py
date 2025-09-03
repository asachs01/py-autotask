"""
TaxCategories Entity for py-autotask

This module provides the TaxCategoriesEntity class for managing tax classification
categories in Autotask. Tax Categories define different tax types, rates, and
applicability rules for products, services, and billing calculations.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class TaxCategoriesEntity(BaseEntity):
    """
    Manages Autotask TaxCategories - tax classification and rate management.

    Tax Categories define different tax types, tax rates, and applicability rules
    for products, services, and billing. They support complex tax calculations,
    jurisdiction-based tax rules, and compliance with various tax regulations.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "TaxCategories"

    def create_tax_category(
        self,
        name: str,
        description: str,
        tax_rate: float,
        tax_type: str,
        is_active: bool = True,
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new tax category.

        Args:
            name: Name of the tax category
            description: Description of the tax category
            tax_rate: Tax rate as a decimal (e.g., 0.08 for 8%)
            tax_type: Type of tax (sales, VAT, GST, etc.)
            is_active: Whether the tax category is active
            effective_date: When the tax category becomes effective
            **kwargs: Additional fields for the tax category

        Returns:
            Create response with new tax category ID
        """
        category_data = {
            "name": name,
            "description": description,
            "taxRate": tax_rate,
            "taxType": tax_type,
            "isActive": is_active,
            **kwargs,
        }

        if effective_date:
            category_data["effectiveDate"] = effective_date.isoformat()

        return self.create(category_data)

    def get_active_tax_categories(
        self, tax_type: Optional[str] = None, jurisdiction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active tax categories.

        Args:
            tax_type: Optional tax type to filter by
            jurisdiction: Optional jurisdiction to filter by

        Returns:
            List of active tax categories
        """
        filters = [{"field": "isActive", "op": "eq", "value": "true"}]

        if tax_type:
            filters.append({"field": "taxType", "op": "eq", "value": tax_type})
        if jurisdiction:
            filters.append({"field": "jurisdiction", "op": "eq", "value": jurisdiction})

        return self.query(filters=filters).items

    def get_tax_categories_by_rate_range(
        self, min_rate: float, max_rate: float
    ) -> List[Dict[str, Any]]:
        """
        Get tax categories within a specific rate range.

        Args:
            min_rate: Minimum tax rate
            max_rate: Maximum tax rate

        Returns:
            List of tax categories within the rate range
        """
        return self.query(
            filters=[
                {"field": "taxRate", "op": "gte", "value": str(min_rate)},
                {"field": "taxRate", "op": "lte", "value": str(max_rate)},
                {"field": "isActive", "op": "eq", "value": "true"},
            ]
        ).items

    def calculate_tax_amount(
        self,
        category_id: int,
        taxable_amount: float,
        quantity: int = 1,
        apply_compound: bool = False,
        compound_categories: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate tax amount for a given taxable amount.

        Args:
            category_id: ID of the tax category
            taxable_amount: Amount subject to tax
            quantity: Quantity multiplier
            apply_compound: Whether to apply compound tax calculations
            compound_categories: List of compound tax category IDs

        Returns:
            Tax calculation details
        """
        tax_category = self.get(category_id)

        if not tax_category:
            raise ValueError(f"Tax category {category_id} not found")

        tax_rate = float(tax_category["taxRate"])
        base_taxable = taxable_amount * quantity
        primary_tax = base_taxable * tax_rate

        calculation_details = {
            "primary_tax": {
                "category_id": category_id,
                "category_name": tax_category["name"],
                "tax_rate": tax_rate,
                "taxable_amount": base_taxable,
                "tax_amount": primary_tax,
            },
            "compound_taxes": [],
            "total_tax_amount": primary_tax,
            "total_amount_including_tax": base_taxable + primary_tax,
        }

        # Apply compound taxes if specified
        if apply_compound and compound_categories:
            compound_taxable = base_taxable + primary_tax

            for compound_id in compound_categories:
                compound_category = self.get(compound_id)
                if compound_category and compound_category.get("isActive"):
                    compound_rate = float(compound_category["taxRate"])
                    compound_tax = compound_taxable * compound_rate

                    calculation_details["compound_taxes"].append(
                        {
                            "category_id": compound_id,
                            "category_name": compound_category["name"],
                            "tax_rate": compound_rate,
                            "taxable_amount": compound_taxable,
                            "tax_amount": compound_tax,
                        }
                    )

                    calculation_details["total_tax_amount"] += compound_tax
                    calculation_details["total_amount_including_tax"] += compound_tax

        # Round to 2 decimal places
        calculation_details["total_tax_amount"] = round(
            calculation_details["total_tax_amount"], 2
        )
        calculation_details["total_amount_including_tax"] = round(
            calculation_details["total_amount_including_tax"], 2
        )

        return calculation_details

    def get_tax_categories_by_jurisdiction(
        self, jurisdiction: str, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get tax categories for a specific jurisdiction.

        Args:
            jurisdiction: Jurisdiction code or name
            include_inactive: Whether to include inactive categories

        Returns:
            List of tax categories for the jurisdiction
        """
        filters = [{"field": "jurisdiction", "op": "eq", "value": jurisdiction}]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def update_tax_rate(
        self,
        category_id: int,
        new_rate: float,
        effective_date: Optional[date] = None,
        change_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the tax rate for a tax category.

        Args:
            category_id: ID of the tax category
            new_rate: New tax rate
            effective_date: When the new rate becomes effective
            change_reason: Reason for the rate change

        Returns:
            Updated tax category data
        """
        update_data = {
            "id": category_id,
            "taxRate": new_rate,
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if effective_date:
            update_data["rateEffectiveDate"] = effective_date.isoformat()
        if change_reason:
            update_data["rateChangeReason"] = change_reason

        return self.update(update_data)

    def get_tax_rate_history(
        self, category_id: int, months_back: int = 12
    ) -> Dict[str, Any]:
        """
        Get tax rate change history for a category.

        Args:
            category_id: ID of the tax category
            months_back: Number of months of history to retrieve

        Returns:
            Tax rate change history
        """
        tax_category = self.get(category_id)

        if not tax_category:
            raise ValueError(f"Tax category {category_id} not found")

        # This would typically query audit logs or rate history table
        # For now, return rate history structure
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        return {
            "category_id": category_id,
            "category_name": tax_category["name"],
            "current_rate": float(tax_category["taxRate"]),
            "history_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months": months_back,
            },
            "rate_changes": [
                # Would populate from actual rate change history
                {
                    "effective_date": end_date.isoformat(),
                    "old_rate": float(tax_category["taxRate"]),
                    "new_rate": float(tax_category["taxRate"]),
                    "change_reason": "Current rate",
                    "changed_by": "system",
                }
            ],
        }

    def validate_tax_configuration(self, category_ids: List[int]) -> Dict[str, Any]:
        """
        Validate tax category configuration for consistency.

        Args:
            category_ids: List of tax category IDs to validate

        Returns:
            Validation results
        """
        validation_results = {
            "categories_validated": len(category_ids),
            "validation_issues": [],
            "is_valid": True,
        }

        for category_id in category_ids:
            category = self.get(category_id)

            if not category:
                validation_results["validation_issues"].append(
                    {
                        "category_id": category_id,
                        "issue_type": "not_found",
                        "description": f"Tax category {category_id} not found",
                        "severity": "error",
                    }
                )
                validation_results["is_valid"] = False
                continue

            # Check for common validation issues
            tax_rate = float(category.get("taxRate", 0))

            if tax_rate < 0:
                validation_results["validation_issues"].append(
                    {
                        "category_id": category_id,
                        "issue_type": "negative_rate",
                        "description": f"Tax rate {tax_rate} is negative",
                        "severity": "error",
                    }
                )
                validation_results["is_valid"] = False

            if tax_rate > 1.0:  # Assuming rates > 100% are unusual
                validation_results["validation_issues"].append(
                    {
                        "category_id": category_id,
                        "issue_type": "high_rate",
                        "description": f"Tax rate {tax_rate * 100}% may be unusually high",
                        "severity": "warning",
                    }
                )

            if not category.get("name"):
                validation_results["validation_issues"].append(
                    {
                        "category_id": category_id,
                        "issue_type": "missing_name",
                        "description": "Tax category name is missing",
                        "severity": "error",
                    }
                )
                validation_results["is_valid"] = False

        return validation_results

    def get_tax_summary_by_type(self, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Get summary of tax categories grouped by tax type.

        Args:
            include_inactive: Whether to include inactive categories

        Returns:
            Tax category summary by type
        """
        filters = []
        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        categories = self.query(filters=filters).items if filters else self.query_all()

        # Group by tax type
        type_summary = {}
        for category in categories:
            tax_type = category.get("taxType", "unknown")

            if tax_type not in type_summary:
                type_summary[tax_type] = {
                    "count": 0,
                    "categories": [],
                    "rate_range": {"min": float("inf"), "max": 0.0},
                    "active_count": 0,
                }

            type_summary[tax_type]["count"] += 1
            type_summary[tax_type]["categories"].append(
                {
                    "id": category["id"],
                    "name": category["name"],
                    "rate": float(category["taxRate"]),
                    "is_active": category.get("isActive", False),
                }
            )

            if category.get("isActive"):
                type_summary[tax_type]["active_count"] += 1

            rate = float(category["taxRate"])
            type_summary[tax_type]["rate_range"]["min"] = min(
                type_summary[tax_type]["rate_range"]["min"], rate
            )
            type_summary[tax_type]["rate_range"]["max"] = max(
                type_summary[tax_type]["rate_range"]["max"], rate
            )

        # Clean up infinite values
        for type_data in type_summary.values():
            if type_data["rate_range"]["min"] == float("inf"):
                type_data["rate_range"]["min"] = 0.0

        return {
            "total_categories": len(categories),
            "tax_types_count": len(type_summary),
            "type_summary": type_summary,
        }

    def bulk_update_rates_by_percentage(
        self,
        category_ids: List[int],
        percentage_change: float,
        effective_date: Optional[date] = None,
        change_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update tax rates for multiple categories by percentage.

        Args:
            category_ids: List of category IDs to update
            percentage_change: Percentage change (e.g., 5.0 for 5% increase)
            effective_date: When changes become effective
            change_reason: Reason for the changes

        Returns:
            Summary of bulk update operation
        """
        results = []
        multiplier = 1 + (percentage_change / 100)

        for category_id in category_ids:
            try:
                category = self.get(category_id)
                if not category:
                    results.append(
                        {
                            "category_id": category_id,
                            "success": False,
                            "error": "Category not found",
                        }
                    )
                    continue

                current_rate = float(category["taxRate"])
                new_rate = current_rate * multiplier

                update_result = self.update_tax_rate(
                    category_id, new_rate, effective_date, change_reason
                )

                results.append(
                    {
                        "category_id": category_id,
                        "category_name": category["name"],
                        "success": True,
                        "old_rate": current_rate,
                        "new_rate": new_rate,
                        "change_amount": new_rate - current_rate,
                    }
                )

            except Exception as e:
                results.append(
                    {"category_id": category_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_categories": len(category_ids),
            "successful_updates": len(successful),
            "failed_updates": len(failed),
            "percentage_change": percentage_change,
            "effective_date": effective_date.isoformat() if effective_date else None,
            "change_reason": change_reason,
            "results": results,
        }

    def archive_tax_category(
        self, category_id: int, archive_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Archive a tax category (mark as inactive).

        Args:
            category_id: ID of the tax category
            archive_reason: Optional reason for archiving

        Returns:
            Updated tax category data
        """
        update_data = {
            "id": category_id,
            "isActive": False,
            "archivedDate": datetime.now().isoformat(),
        }

        if archive_reason:
            update_data["archiveReason"] = archive_reason

        return self.update(update_data)

    def reactivate_tax_category(
        self, category_id: int, reactivation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reactivate an archived tax category.

        Args:
            category_id: ID of the tax category
            reactivation_reason: Optional reason for reactivation

        Returns:
            Updated tax category data
        """
        update_data = {
            "id": category_id,
            "isActive": True,
            "reactivatedDate": datetime.now().isoformat(),
        }

        if reactivation_reason:
            update_data["reactivationReason"] = reactivation_reason

        return self.update(update_data)
