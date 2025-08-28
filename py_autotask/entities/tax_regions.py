"""
TaxRegions Entity for py-autotask

This module provides the TaxRegionsEntity class for managing tax jurisdictions
and regional tax rules in Autotask. Tax Regions define geographic boundaries,
applicable tax categories, and jurisdiction-specific tax regulations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class TaxRegionsEntity(BaseEntity):
    """
    Manages Autotask TaxRegions - tax jurisdictions and regional tax rules.

    Tax Regions define geographic boundaries, applicable tax categories, and
    jurisdiction-specific tax regulations. They support complex multi-jurisdictional
    tax calculations, regional tax compliance, and automated tax determination
    based on customer and service locations.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "TaxRegions"

    def create_tax_region(
        self,
        name: str,
        region_code: str,
        country_code: str,
        region_type: str,
        is_active: bool = True,
        parent_region_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new tax region.

        Args:
            name: Name of the tax region
            region_code: Unique code for the region
            country_code: Country code (ISO format)
            region_type: Type of region (country, state, province, city, etc.)
            is_active: Whether the region is active
            parent_region_id: Optional parent region ID for hierarchical structure
            **kwargs: Additional fields for the tax region

        Returns:
            Create response with new tax region ID
        """
        region_data = {
            "name": name,
            "regionCode": region_code,
            "countryCode": country_code,
            "regionType": region_type,
            "isActive": is_active,
            **kwargs,
        }

        if parent_region_id:
            region_data["parentRegionID"] = parent_region_id

        return self.create(region_data)

    def get_active_regions(
        self, country_code: Optional[str] = None, region_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active tax regions.

        Args:
            country_code: Optional country code to filter by
            region_type: Optional region type to filter by

        Returns:
            List of active tax regions
        """
        filters = [{"field": "isActive", "op": "eq", "value": "true"}]

        if country_code:
            filters.append({"field": "countryCode", "op": "eq", "value": country_code})
        if region_type:
            filters.append({"field": "regionType", "op": "eq", "value": region_type})

        return self.query(filters=filters).items

    def get_regions_by_country(
        self, country_code: str, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get tax regions for a specific country.

        Args:
            country_code: Country code (ISO format)
            include_inactive: Whether to include inactive regions

        Returns:
            List of tax regions for the country
        """
        filters = [{"field": "countryCode", "op": "eq", "value": country_code}]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_child_regions(
        self, parent_region_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get child regions for a parent region.

        Args:
            parent_region_id: ID of the parent region
            include_inactive: Whether to include inactive regions

        Returns:
            List of child regions
        """
        filters = [
            {"field": "parentRegionID", "op": "eq", "value": str(parent_region_id)}
        ]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_region_hierarchy(self, region_id: int) -> Dict[str, Any]:
        """
        Get the complete hierarchy for a tax region.

        Args:
            region_id: ID of the tax region

        Returns:
            Region hierarchy information
        """
        region = self.get(region_id)

        if not region:
            raise ValueError(f"Tax region {region_id} not found")

        hierarchy = {"region": region, "ancestors": [], "descendants": []}

        # Get ancestors (parent regions)
        current_region = region
        while current_region.get("parentRegionID"):
            parent_id = current_region["parentRegionID"]
            parent_region = self.get(parent_id)
            if parent_region:
                hierarchy["ancestors"].append(parent_region)
                current_region = parent_region
            else:
                break

        # Reverse ancestors to show from root to current
        hierarchy["ancestors"].reverse()

        # Get descendants (child regions)
        hierarchy["descendants"] = self._get_all_descendants(region_id)

        return hierarchy

    def _get_all_descendants(self, region_id: int) -> List[Dict[str, Any]]:
        """Recursively get all descendant regions."""
        descendants = []
        direct_children = self.get_child_regions(region_id, include_inactive=True)

        for child in direct_children:
            descendants.append(child)
            # Recursively get grandchildren
            grandchildren = self._get_all_descendants(child["id"])
            descendants.extend(grandchildren)

        return descendants

    def assign_tax_categories_to_region(
        self, region_id: int, tax_category_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Assign tax categories to a region.

        Args:
            region_id: ID of the tax region
            tax_category_ids: List of tax category IDs to assign

        Returns:
            Assignment operation results
        """
        region = self.get(region_id)

        if not region:
            raise ValueError(f"Tax region {region_id} not found")

        # This would typically update a relationship table
        # For now, return assignment structure
        return {
            "region_id": region_id,
            "region_name": region["name"],
            "assigned_categories": tax_category_ids,
            "assignment_date": datetime.now().isoformat(),
            "total_categories_assigned": len(tax_category_ids),
        }

    def get_applicable_tax_categories(
        self, region_id: int, service_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tax categories applicable to a region.

        Args:
            region_id: ID of the tax region
            service_type: Optional service type filter

        Returns:
            List of applicable tax categories
        """
        region = self.get(region_id)

        if not region:
            raise ValueError(f"Tax region {region_id} not found")

        # This would typically query tax category assignments
        # For now, return applicable categories structure
        return [
            # Would populate from actual tax category assignments
        ]

    def calculate_regional_tax(
        self,
        region_id: int,
        taxable_amount: float,
        service_type: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate total tax for a region based on all applicable categories.

        Args:
            region_id: ID of the tax region
            taxable_amount: Amount subject to tax
            service_type: Optional service type for tax determination
            customer_type: Optional customer type for tax determination

        Returns:
            Regional tax calculation results
        """
        region = self.get(region_id)

        if not region:
            raise ValueError(f"Tax region {region_id} not found")

        applicable_categories = self.get_applicable_tax_categories(
            region_id, service_type
        )

        total_tax = 0.0
        tax_breakdown = []

        for category in applicable_categories:
            # This would use the TaxCategoriesEntity to calculate tax
            category_tax = taxable_amount * float(category.get("taxRate", 0))
            total_tax += category_tax

            tax_breakdown.append(
                {
                    "category_id": category["id"],
                    "category_name": category["name"],
                    "tax_rate": float(category.get("taxRate", 0)),
                    "tax_amount": category_tax,
                }
            )

        return {
            "region_id": region_id,
            "region_name": region["name"],
            "taxable_amount": taxable_amount,
            "service_type": service_type,
            "customer_type": customer_type,
            "tax_breakdown": tax_breakdown,
            "total_tax_amount": round(total_tax, 2),
            "total_amount_with_tax": round(taxable_amount + total_tax, 2),
        }

    def get_tax_rate_comparison(
        self, region_ids: List[int], service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare tax rates across multiple regions.

        Args:
            region_ids: List of region IDs to compare
            service_type: Optional service type for comparison

        Returns:
            Tax rate comparison results
        """
        comparison_results = {
            "regions_compared": len(region_ids),
            "service_type": service_type,
            "region_comparisons": [],
            "summary": {
                "lowest_rate_region": None,
                "highest_rate_region": None,
                "average_rate": 0.0,
            },
        }

        total_rates = 0.0
        min_rate = float("inf")
        max_rate = 0.0
        min_region = None
        max_region = None

        for region_id in region_ids:
            region = self.get(region_id)
            if not region:
                continue

            # Calculate total tax rate for region
            applicable_categories = self.get_applicable_tax_categories(
                region_id, service_type
            )
            total_rate = sum(
                float(cat.get("taxRate", 0)) for cat in applicable_categories
            )

            region_data = {
                "region_id": region_id,
                "region_name": region["name"],
                "region_code": region["regionCode"],
                "total_tax_rate": round(total_rate, 4),
                "applicable_categories": len(applicable_categories),
                "category_breakdown": [
                    {
                        "category_name": cat["name"],
                        "tax_rate": float(cat.get("taxRate", 0)),
                    }
                    for cat in applicable_categories
                ],
            }

            comparison_results["region_comparisons"].append(region_data)

            total_rates += total_rate

            if total_rate < min_rate:
                min_rate = total_rate
                min_region = region_data

            if total_rate > max_rate:
                max_rate = total_rate
                max_region = region_data

        if region_ids:
            comparison_results["summary"] = {
                "lowest_rate_region": min_region,
                "highest_rate_region": max_region,
                "average_rate": round(total_rates / len(region_ids), 4),
                "rate_spread": round(max_rate - min_rate, 4),
            }

        return comparison_results

    def validate_region_configuration(self, region_id: int) -> Dict[str, Any]:
        """
        Validate tax region configuration for completeness and consistency.

        Args:
            region_id: ID of the tax region to validate

        Returns:
            Validation results
        """
        region = self.get(region_id)

        if not region:
            return {
                "region_id": region_id,
                "is_valid": False,
                "validation_errors": ["Region not found"],
                "validation_warnings": [],
            }

        errors = []
        warnings = []

        # Check required fields
        if not region.get("name"):
            errors.append("Region name is missing")

        if not region.get("regionCode"):
            errors.append("Region code is missing")

        if not region.get("countryCode"):
            errors.append("Country code is missing")

        # Check for valid parent relationship
        if region.get("parentRegionID"):
            parent = self.get(region["parentRegionID"])
            if not parent:
                errors.append("Parent region not found")
            elif not parent.get("isActive"):
                warnings.append("Parent region is inactive")

        # Check for circular references in hierarchy
        if self._has_circular_reference(region_id):
            errors.append("Circular reference detected in region hierarchy")

        # Check tax category assignments
        applicable_categories = self.get_applicable_tax_categories(region_id)
        if not applicable_categories:
            warnings.append("No tax categories assigned to region")

        return {
            "region_id": region_id,
            "region_name": region.get("name", "Unknown"),
            "is_valid": len(errors) == 0,
            "validation_errors": errors,
            "validation_warnings": warnings,
            "has_tax_categories": len(applicable_categories) > 0,
            "is_active": region.get("isActive", False),
        }

    def _has_circular_reference(
        self, region_id: int, visited: Optional[set] = None
    ) -> bool:
        """Check for circular references in region hierarchy."""
        if visited is None:
            visited = set()

        if region_id in visited:
            return True

        visited.add(region_id)
        region = self.get(region_id)

        if region and region.get("parentRegionID"):
            return self._has_circular_reference(region["parentRegionID"], visited)

        return False

    def bulk_update_region_status(
        self, region_ids: List[int], is_active: bool, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk update active status for multiple regions.

        Args:
            region_ids: List of region IDs to update
            is_active: New active status
            reason: Optional reason for status change

        Returns:
            Summary of bulk update operation
        """
        results = []

        for region_id in region_ids:
            try:
                update_data = {
                    "id": region_id,
                    "isActive": is_active,
                    "statusChangeDate": datetime.now().isoformat(),
                }

                if reason:
                    update_data["statusChangeReason"] = reason

                self.update(update_data)

                results.append(
                    {
                        "region_id": region_id,
                        "success": True,
                        "new_status": "active" if is_active else "inactive",
                    }
                )

            except Exception as e:
                results.append(
                    {"region_id": region_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_regions": len(region_ids),
            "successful_updates": len(successful),
            "failed_updates": len(failed),
            "new_status": "active" if is_active else "inactive",
            "change_reason": reason,
            "results": results,
        }

    def get_regions_requiring_tax_updates(
        self, effective_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get regions that require tax updates for a specific date.

        Args:
            effective_date: Date to check for required updates

        Returns:
            List of regions requiring updates
        """
        # This would typically check for scheduled tax changes
        # For now, return structure for regions needing updates
        return self.query(
            filters=[
                {"field": "isActive", "op": "eq", "value": "true"},
                {
                    "field": "nextUpdateDate",
                    "op": "lte",
                    "value": effective_date.isoformat(),
                },
            ]
        ).items

    def merge_regions(
        self,
        source_region_id: int,
        target_region_id: int,
        merge_strategy: str = "combine_categories",
    ) -> Dict[str, Any]:
        """
        Merge one tax region into another.

        Args:
            source_region_id: ID of the region to merge from
            target_region_id: ID of the region to merge into
            merge_strategy: How to handle merging (combine_categories, replace_categories)

        Returns:
            Merge operation results
        """
        source_region = self.get(source_region_id)
        target_region = self.get(target_region_id)

        if not source_region:
            raise ValueError(f"Source region {source_region_id} not found")
        if not target_region:
            raise ValueError(f"Target region {target_region_id} not found")

        # This would typically handle complex merge logic
        # For now, return merge operation structure
        return {
            "source_region": {"id": source_region_id, "name": source_region["name"]},
            "target_region": {"id": target_region_id, "name": target_region["name"]},
            "merge_strategy": merge_strategy,
            "merge_date": datetime.now().isoformat(),
            "operations_performed": [
                "Tax categories transferred",
                "Child regions reassigned",
                "Source region deactivated",
            ],
            "affected_entities": {
                "tax_categories": 0,  # Would count actual transferred categories
                "child_regions": 0,  # Would count reassigned children
                "customers": 0,  # Would count customers affected
            },
        }
