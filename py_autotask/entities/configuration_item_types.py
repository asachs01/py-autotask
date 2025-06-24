"""
ConfigurationItemTypes Entity for py-autotask

This module provides the ConfigurationItemTypesEntity class for managing
configuration item types in Autotask. Configuration item types classify
CIs for better organization, reporting, and CMDB management.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ConfigurationItemTypesEntity(BaseEntity):
    """
    Manages Autotask ConfigurationItemTypes - CI classification and categorization.

    Configuration item types classify configuration items for better organization,
    asset management, and CMDB (Configuration Management Database) operations
    within Autotask.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ConfigurationItemTypes"

    def create_configuration_item_type(
        self,
        name: str,
        description: str,
        category: str,
        is_active: bool = True,
        default_warranty_months: int = 12,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item type.

        Args:
            name: Name of the CI type
            description: Description of the CI type
            category: Category (Hardware, Software, Network, etc.)
            is_active: Whether the CI type is active
            default_warranty_months: Default warranty period in months
            **kwargs: Additional fields for the CI type

        Returns:
            Create response with new CI type ID
        """
        ci_type_data = {
            "name": name,
            "description": description,
            "category": category,
            "isActive": is_active,
            "defaultWarrantyMonths": default_warranty_months,
            **kwargs,
        }

        return self.create(ci_type_data)

    def get_active_ci_types(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active configuration item types.

        Args:
            category: Optional category to filter by

        Returns:
            List of active CI types
        """
        filters = ["isActive eq true"]

        if category:
            filters.append(f"category eq '{category}'")

        return self.query(filter=" and ".join(filters))

    def get_ci_types_by_category(
        self, category: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get CI types by category.

        Args:
            category: Category to filter by
            active_only: Whether to only return active CI types

        Returns:
            List of CI types in the specified category
        """
        filters = [f"category eq '{category}'"]

        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def get_hardware_ci_types(self) -> List[Dict[str, Any]]:
        """
        Get all hardware configuration item types.

        Returns:
            List of hardware CI types
        """
        return self.get_ci_types_by_category("Hardware")

    def get_software_ci_types(self) -> List[Dict[str, Any]]:
        """
        Get all software configuration item types.

        Returns:
            List of software CI types
        """
        return self.get_ci_types_by_category("Software")

    def get_network_ci_types(self) -> List[Dict[str, Any]]:
        """
        Get all network configuration item types.

        Returns:
            List of network CI types
        """
        return self.get_ci_types_by_category("Network")

    def get_ci_type_statistics(self, ci_type_id: int) -> Dict[str, Any]:
        """
        Get statistics for a CI type.

        Args:
            ci_type_id: ID of the CI type

        Returns:
            CI type statistics
        """
        # This would typically query related configuration items
        # For now, return statistics structure

        ci_type = self.get(ci_type_id)

        return {
            "ci_type_id": ci_type_id,
            "name": ci_type.get("name"),
            "category": ci_type.get("category"),
            "statistics": {
                "total_items": 0,  # Would count CIs of this type
                "active_items": 0,  # Would count active CIs
                "retired_items": 0,  # Would count retired CIs
                "under_warranty": 0,  # Would count items under warranty
                "expired_warranty": 0,  # Would count items with expired warranty
                "total_value": Decimal("0.00"),  # Would sum CI values
                "average_age_months": 0.0,  # Would calculate average age
            },
        }

    def get_ci_type_asset_summary(
        self, ci_type_id: int, include_retired: bool = False
    ) -> Dict[str, Any]:
        """
        Get asset summary for a CI type.

        Args:
            ci_type_id: ID of the CI type
            include_retired: Whether to include retired items

        Returns:
            Asset summary for the CI type
        """
        ci_type = self.get(ci_type_id)

        # This would typically query related configuration items
        # For now, return asset summary structure

        return {
            "ci_type_id": ci_type_id,
            "name": ci_type.get("name"),
            "category": ci_type.get("category"),
            "asset_summary": {
                "total_assets": 0,  # Would count assets
                "deployed_assets": 0,  # Would count deployed assets
                "available_assets": 0,  # Would count available assets
                "maintenance_assets": 0,  # Would count assets in maintenance
                "warranty_status": {
                    "under_warranty": 0,  # Would count under warranty
                    "warranty_expiring": 0,  # Would count expiring soon
                    "expired_warranty": 0,  # Would count expired
                },
                "total_purchase_value": Decimal("0.00"),  # Would sum purchase values
                "current_book_value": Decimal("0.00"),  # Would calculate book value
            },
            "include_retired": include_retired,
        }

    def activate_ci_type(self, ci_type_id: int) -> Dict[str, Any]:
        """
        Activate a CI type.

        Args:
            ci_type_id: ID of the CI type to activate

        Returns:
            Update response
        """
        return self.update(ci_type_id, {"isActive": True})

    def deactivate_ci_type(self, ci_type_id: int) -> Dict[str, Any]:
        """
        Deactivate a CI type.

        Args:
            ci_type_id: ID of the CI type to deactivate

        Returns:
            Update response
        """
        return self.update(ci_type_id, {"isActive": False})

    def update_default_warranty(
        self, ci_type_id: int, warranty_months: int
    ) -> Dict[str, Any]:
        """
        Update default warranty period for a CI type.

        Args:
            ci_type_id: ID of the CI type
            warranty_months: New default warranty period in months

        Returns:
            Update response
        """
        return self.update(ci_type_id, {"defaultWarrantyMonths": warranty_months})

    def clone_ci_type(
        self,
        source_ci_type_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing CI type.

        Args:
            source_ci_type_id: ID of the CI type to clone
            new_name: Name for the new CI type
            new_description: Description for the new CI type

        Returns:
            Create response for the new CI type
        """
        source_ci_type = self.get(source_ci_type_id)

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_ci_type.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        clone_data["isActive"] = True
        if new_description:
            clone_data["description"] = new_description

        return self.create(clone_data)

    def get_ci_types_summary(self) -> Dict[str, Any]:
        """
        Get summary of all CI types.

        Returns:
            Summary of CI types by various categories
        """
        ci_types = self.query()

        # Group by category
        category_groups = {}
        warranty_groups = {}

        for ci_type in ci_types:
            category = ci_type.get("category", "Unknown")
            warranty_months = ci_type.get("defaultWarrantyMonths", 0)

            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(ci_type)

            # Group by warranty ranges
            if warranty_months <= 12:
                warranty_group = "1-12 months"
            elif warranty_months <= 24:
                warranty_group = "13-24 months"
            elif warranty_months <= 36:
                warranty_group = "25-36 months"
            else:
                warranty_group = "36+ months"

            if warranty_group not in warranty_groups:
                warranty_groups[warranty_group] = []
            warranty_groups[warranty_group].append(ci_type)

        active_count = len([ct for ct in ci_types if ct.get("isActive")])
        inactive_count = len(ci_types) - active_count

        return {
            "total_ci_types": len(ci_types),
            "active_ci_types": active_count,
            "inactive_ci_types": inactive_count,
            "by_category": {
                category: len(types) for category, types in category_groups.items()
            },
            "by_warranty": {
                warranty: len(types) for warranty, types in warranty_groups.items()
            },
            "category_distribution": category_groups,
            "warranty_distribution": warranty_groups,
        }

    def get_cmdb_organization_report(self) -> Dict[str, Any]:
        """
        Get CMDB organization report showing CI type structure.

        Returns:
            CMDB organization report
        """
        ci_types = self.query()

        # Organize for CMDB view
        cmdb_structure = {
            "hardware": [],
            "software": [],
            "network": [],
            "services": [],
            "other": [],
        }

        for ci_type in ci_types:
            category = ci_type.get("category", "").lower()

            # Categorize for CMDB
            if "hardware" in category or "server" in category or "desktop" in category:
                cmdb_structure["hardware"].append(ci_type)
            elif "software" in category or "application" in category:
                cmdb_structure["software"].append(ci_type)
            elif "network" in category or "router" in category or "switch" in category:
                cmdb_structure["network"].append(ci_type)
            elif "service" in category:
                cmdb_structure["services"].append(ci_type)
            else:
                cmdb_structure["other"].append(ci_type)

        return {
            "cmdb_organization": cmdb_structure,
            "totals_by_cmdb_category": {
                category: len(types) for category, types in cmdb_structure.items()
            },
            "total_ci_types": len(ci_types),
            "active_ci_types": len([ct for ct in ci_types if ct.get("isActive")]),
        }

    def bulk_update_warranty_periods(
        self, warranty_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update warranty periods for multiple CI types.

        Args:
            warranty_updates: List of updates
                Each should contain: ci_type_id, warranty_months

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in warranty_updates:
            ci_type_id = update["ci_type_id"]
            warranty_months = update["warranty_months"]

            try:
                result = self.update_default_warranty(ci_type_id, warranty_months)
                results.append({"id": ci_type_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": ci_type_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(warranty_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }
