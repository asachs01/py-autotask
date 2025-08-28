"""
CompanySiteConfigurations entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanySiteConfigurationsEntity(BaseEntity):
    """
    Handles all Company Site Configuration-related operations for the Autotask API.

    Company Site Configurations in Autotask represent technical configurations,
    settings, and parameters for client sites and locations.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_site_configuration(
        self,
        company_id: int,
        configuration_name: str,
        configuration_type: int,
        configuration_data: Dict[str, Any],
        site_location: Optional[str] = None,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company site configuration.

        Args:
            company_id: ID of the company
            configuration_name: Name of the configuration
            configuration_type: Type of configuration
            configuration_data: Configuration parameters and settings
            site_location: Optional location identifier
            is_active: Whether the configuration is active
            **kwargs: Additional configuration fields

        Returns:
            Created site configuration data
        """
        config_data = {
            "CompanyID": company_id,
            "ConfigurationName": configuration_name,
            "ConfigurationType": configuration_type,
            "ConfigurationData": configuration_data,
            "IsActive": is_active,
            **kwargs,
        }

        if site_location:
            config_data["SiteLocation"] = site_location

        return self.create(config_data)

    def get_company_site_configurations(
        self,
        company_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all site configurations for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active configurations
            limit: Maximum number of configurations to return

        Returns:
            List of company site configurations
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_configurations_by_type(
        self,
        company_id: int,
        configuration_type: int,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company site configurations filtered by configuration type.

        Args:
            company_id: ID of the company
            configuration_type: Configuration type to filter by
            limit: Maximum number of configurations to return

        Returns:
            List of configurations matching the criteria
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="ConfigurationType", op="eq", value=configuration_type),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_configurations_by_location(
        self,
        company_id: int,
        site_location: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get company site configurations for a specific location.

        Args:
            company_id: ID of the company
            site_location: Site location to filter by
            limit: Maximum number of configurations to return

        Returns:
            List of configurations for the specified location
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="SiteLocation", op="eq", value=site_location),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def search_configurations_by_name(
        self,
        company_id: int,
        name: str,
        exact_match: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search site configurations by name.

        Args:
            company_id: ID of the company
            name: Configuration name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of configurations to return

        Returns:
            List of matching configurations
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if exact_match:
            filters.append(QueryFilter(field="ConfigurationName", op="eq", value=name))
        else:
            filters.append(
                QueryFilter(field="ConfigurationName", op="contains", value=name)
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_configuration_data(
        self, configuration_id: int, new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the configuration data for a site configuration.

        Args:
            configuration_id: ID of configuration to update
            new_data: New configuration data

        Returns:
            Updated configuration data
        """
        return self.update_by_id(configuration_id, {"ConfigurationData": new_data})

    def activate_configuration(self, configuration_id: int) -> Dict[str, Any]:
        """
        Activate a site configuration.

        Args:
            configuration_id: ID of configuration to activate

        Returns:
            Updated configuration data
        """
        return self.update_by_id(configuration_id, {"IsActive": True})

    def deactivate_configuration(self, configuration_id: int) -> Dict[str, Any]:
        """
        Deactivate a site configuration.

        Args:
            configuration_id: ID of configuration to deactivate

        Returns:
            Updated configuration data
        """
        return self.update_by_id(configuration_id, {"IsActive": False})

    def clone_configuration(
        self,
        source_configuration_id: int,
        new_name: str,
        target_company_id: Optional[int] = None,
        target_location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clone an existing site configuration to create a new one.

        Args:
            source_configuration_id: ID of configuration to clone
            new_name: Name for the cloned configuration
            target_company_id: Optional target company (uses source company if not specified)
            target_location: Optional target location

        Returns:
            Created configuration data
        """
        source_config = self.get(source_configuration_id)
        if not source_config:
            raise ValueError(
                f"Configuration with ID {source_configuration_id} not found"
            )

        new_config_data = {
            "CompanyID": target_company_id or source_config["CompanyID"],
            "ConfigurationName": new_name,
            "ConfigurationType": source_config["ConfigurationType"],
            "ConfigurationData": source_config["ConfigurationData"],
            "IsActive": True,
        }

        if target_location:
            new_config_data["SiteLocation"] = target_location
        elif source_config.get("SiteLocation"):
            new_config_data["SiteLocation"] = source_config["SiteLocation"]

        return self.create(new_config_data)

    def get_configuration_history(
        self,
        configuration_id: int,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the change history for a site configuration.

        Args:
            configuration_id: ID of the configuration
            limit: Maximum number of history records to return

        Returns:
            List of configuration change history records
        """
        # This would typically query a configuration history table
        filters = [
            QueryFilter(field="ConfigurationID", op="eq", value=configuration_id)
        ]

        # Assuming there's a related history entity
        try:
            response = self.client.query(
                "CompanySiteConfigurationHistory", filters=filters, max_records=limit
            )
            return response.get("items", [])
        except Exception:
            # If history table doesn't exist, return empty list
            return []

    def bulk_activate_configurations(
        self, configuration_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Activate multiple site configurations in bulk.

        Args:
            configuration_ids: List of configuration IDs to activate

        Returns:
            List of updated configuration data
        """
        update_data = [
            {"id": config_id, "IsActive": True} for config_id in configuration_ids
        ]
        return self.batch_update(update_data)

    def get_configurations_by_date_range(
        self,
        company_id: int,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get site configurations created within a specific date range.

        Args:
            company_id: ID of the company
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of configurations to return

        Returns:
            List of configurations within the date range
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="CreateDate", op="gte", value=start_date),
            QueryFilter(field="CreateDate", op="lte", value=end_date),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items
