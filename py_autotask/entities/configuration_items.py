"""
Configuration Items entity for Autotask API.

This module provides the ConfigurationItemsEntity class for managing
asset configuration tracking and change management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ConfigurationItemsEntity(BaseEntity):
    """
    Entity for managing Autotask Configuration Items.

    Configuration Items represent managed assets and their
    configuration tracking for change management and inventory.
    """

    def __init__(self, client, entity_name="ConfigurationItems"):
        """Initialize the Configuration Items entity."""
        super().__init__(client, entity_name)

    def create(self, ci_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new configuration item.

        Args:
            ci_data: Dictionary containing configuration item information
                Required fields:
                - accountID: ID of the account/company
                - configurationItemName: Name of the configuration item
                - configurationItemCategoryID: Category ID
                - configurationItemType: Type of configuration item
                Optional fields:
                - serialNumber: Serial number
                - manufacturer: Manufacturer name
                - model: Model information
                - location: Physical location
                - contactID: Primary contact ID
                - installedProductID: Installed product ID
                - warrantyExpirationDate: Warranty expiration
                - isActive: Whether the CI is active
                - notes: Additional notes

        Returns:
            CreateResponse: Response containing created CI data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = [
            "accountID",
            "configurationItemName",
            "configurationItemCategoryID",
            "configurationItemType",
        ]
        self._validate_required_fields(ci_data, required_fields)

        return self._create(ci_data)

    def get(self, ci_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a configuration item by ID.

        Args:
            ci_id: The configuration item ID

        Returns:
            Dictionary containing CI data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(ci_id)

    def update(self, ci_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing configuration item.

        Args:
            ci_id: The configuration item ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated CI data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(ci_id, update_data)

    def delete(self, ci_id: int) -> bool:
        """
        Delete a configuration item.

        Args:
            ci_id: The configuration item ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(ci_id)

    def get_by_account(
        self,
        account_id: int,
        ci_type: Optional[int] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration items for a specific account.

        Args:
            account_id: ID of the account
            ci_type: Optional filter by CI type
            active_only: Whether to include only active CIs
            limit: Maximum number of CIs to return

        Returns:
            List of configuration items
        """
        filters = [QueryFilter(field="accountID", op="eq", value=account_id)]

        if ci_type is not None:
            filters.append(
                QueryFilter(field="configurationItemType", op="eq", value=ci_type)
            )

        if active_only:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_by_serial_number(self, serial_number: str) -> List[Dict[str, Any]]:
        """
        Get configuration items by serial number.

        Args:
            serial_number: Serial number to search for

        Returns:
            List of configuration items with matching serial number
        """
        filters = [
            QueryFilter(field="serialNumber", op="eq", value=serial_number),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        return self.query(filters=filters)

    def get_by_manufacturer(
        self,
        manufacturer: str,
        model: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get configuration items by manufacturer.

        Args:
            manufacturer: Manufacturer name
            model: Optional model filter
            limit: Maximum number of CIs to return

        Returns:
            List of configuration items
        """
        filters = [
            QueryFilter(field="manufacturer", op="eq", value=manufacturer),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        if model:
            filters.append(QueryFilter(field="model", op="eq", value=model))

        return self.query(filters=filters, max_records=limit)

    def get_expiring_warranties(
        self, days_ahead: int = 30, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get configuration items with warranties expiring soon.

        Args:
            days_ahead: Number of days ahead to check for expiration
            account_id: Optional filter by account

        Returns:
            List of CIs with expiring warranties
        """
        from datetime import datetime, timedelta

        future_date = datetime.now() + timedelta(days=days_ahead)

        filters = [
            QueryFilter(
                field="warrantyExpirationDate", op="lte", value=future_date.isoformat()
            ),
            QueryFilter(
                field="warrantyExpirationDate",
                op="gte",
                value=datetime.now().isoformat(),
            ),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        if account_id:
            filters.append(QueryFilter(field="accountID", op="eq", value=account_id))

        return self.query(filters=filters)

    def get_by_location(
        self, location: str, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get configuration items by location.

        Args:
            location: Location to search for
            account_id: Optional filter by account

        Returns:
            List of configuration items at the location
        """
        filters = [
            QueryFilter(field="location", op="contains", value=location),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        if account_id:
            filters.append(QueryFilter(field="accountID", op="eq", value=account_id))

        return self.query(filters=filters)

    def get_ci_relationships(self, ci_id: int) -> Dict[str, Any]:
        """
        Get relationships for a configuration item.

        Args:
            ci_id: Configuration item ID

        Returns:
            Dictionary with related tickets, contracts, and other CIs
        """
        relationships = {
            "ci_id": ci_id,
            "tickets": [],
            "contracts": [],
            "time_entries": [],
            "parent_ci": None,
            "child_cis": [],
        }

        # Get related tickets
        ticket_filters = [
            QueryFilter(field="configurationItemID", op="eq", value=ci_id)
        ]
        relationships["tickets"] = self.client.query("Tickets", filters=ticket_filters)

        # Get related contracts
        contract_filters = [
            QueryFilter(field="configurationItemID", op="eq", value=ci_id)
        ]
        relationships["contracts"] = self.client.query(
            "Contracts", filters=contract_filters
        )

        # Get related time entries
        time_filters = [QueryFilter(field="configurationItemID", op="eq", value=ci_id)]
        relationships["time_entries"] = self.client.query(
            "TimeEntries", filters=time_filters
        )

        # Get CI hierarchy (simplified - actual implementation may vary)
        ci_data = self.get(ci_id)
        if ci_data:
            parent_id = ci_data.get("parentConfigurationItemID")
            if parent_id:
                relationships["parent_ci"] = self.get(parent_id)

            # Get child CIs
            child_filters = [
                QueryFilter(field="parentConfigurationItemID", op="eq", value=ci_id)
            ]
            relationships["child_cis"] = self.query(filters=child_filters)

        return relationships

    def update_warranty_info(
        self,
        ci_id: int,
        warranty_expiration: Union[datetime, str],
        warranty_notes: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Update warranty information for a configuration item.

        Args:
            ci_id: Configuration item ID
            warranty_expiration: Warranty expiration date
            warranty_notes: Optional warranty notes

        Returns:
            Updated CI data
        """
        update_data = {
            "warrantyExpirationDate": (
                warranty_expiration.isoformat()
                if hasattr(warranty_expiration, "isoformat")
                else warranty_expiration
            )
        }

        if warranty_notes:
            update_data["warrantyNotes"] = warranty_notes

        return self.update(ci_id, update_data)

    def deactivate_ci(
        self, ci_id: int, deactivation_reason: Optional[str] = None
    ) -> UpdateResponse:
        """
        Deactivate a configuration item.

        Args:
            ci_id: Configuration item ID
            deactivation_reason: Optional reason for deactivation

        Returns:
            Updated CI data
        """
        update_data = {
            "isActive": False,
            "deactivationDate": datetime.now().isoformat(),
        }

        if deactivation_reason:
            update_data["deactivationReason"] = deactivation_reason

        return self.update(ci_id, update_data)

    def reactivate_ci(self, ci_id: int) -> UpdateResponse:
        """
        Reactivate a configuration item.

        Args:
            ci_id: Configuration item ID

        Returns:
            Updated CI data
        """
        update_data = {"isActive": True, "reactivationDate": datetime.now().isoformat()}

        return self.update(ci_id, update_data)

    def bulk_update_location(
        self, ci_ids: List[int], new_location: str, update_reason: Optional[str] = None
    ) -> List[UpdateResponse]:
        """
        Update location for multiple configuration items.

        Args:
            ci_ids: List of CI IDs to update
            new_location: New location
            update_reason: Optional reason for the move

        Returns:
            List of update responses
        """
        results = []

        for ci_id in ci_ids:
            update_data = {
                "location": new_location,
                "lastLocationUpdate": datetime.now().isoformat(),
            }

            if update_reason:
                update_data["locationUpdateReason"] = update_reason

            try:
                result = self.update(ci_id, update_data)
                results.append(result)
            except Exception as e:
                self.client.logger.error(f"Failed to update CI {ci_id}: {e}")
                results.append({"error": str(e), "ci_id": ci_id})

        return results

    def get_ci_inventory_report(
        self, account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive inventory report.

        Args:
            account_id: Optional filter by account

        Returns:
            Dictionary with inventory statistics
        """
        filters = [QueryFilter(field="isActive", op="eq", value=True)]

        if account_id:
            filters.append(QueryFilter(field="accountID", op="eq", value=account_id))

        cis = self.query(filters=filters)

        report = {
            "total_cis": len(cis),
            "by_type": {},
            "by_manufacturer": {},
            "by_location": {},
            "warranty_status": {
                "active": 0,
                "expiring_30_days": 0,
                "expiring_90_days": 0,
                "expired": 0,
                "no_warranty": 0,
            },
            "age_analysis": {
                "under_1_year": 0,
                "under_3_years": 0,
                "under_5_years": 0,
                "over_5_years": 0,
                "unknown": 0,
            },
        }

        now = datetime.now()

        for ci in cis:
            ci_type = ci.get("configurationItemType", "Unknown")
            manufacturer = ci.get("manufacturer", "Unknown")
            location = ci.get("location", "Unknown")
            warranty_date = ci.get("warrantyExpirationDate")
            install_date = ci.get("installDate")

            # Count by type
            report["by_type"][ci_type] = report["by_type"].get(ci_type, 0) + 1

            # Count by manufacturer
            report["by_manufacturer"][manufacturer] = (
                report["by_manufacturer"].get(manufacturer, 0) + 1
            )

            # Count by location
            report["by_location"][location] = report["by_location"].get(location, 0) + 1

            # Warranty analysis
            if warranty_date:
                try:
                    warranty_exp = datetime.fromisoformat(
                        warranty_date.replace("Z", "+00:00")
                    )
                    days_to_expiry = (warranty_exp - now).days

                    if days_to_expiry < 0:
                        report["warranty_status"]["expired"] += 1
                    elif days_to_expiry <= 30:
                        report["warranty_status"]["expiring_30_days"] += 1
                    elif days_to_expiry <= 90:
                        report["warranty_status"]["expiring_90_days"] += 1
                    else:
                        report["warranty_status"]["active"] += 1
                except ValueError:
                    report["warranty_status"]["no_warranty"] += 1
            else:
                report["warranty_status"]["no_warranty"] += 1

            # Age analysis
            if install_date:
                try:
                    installed = datetime.fromisoformat(
                        install_date.replace("Z", "+00:00")
                    )
                    age_days = (now - installed).days
                    age_years = age_days / 365.25

                    if age_years < 1:
                        report["age_analysis"]["under_1_year"] += 1
                    elif age_years < 3:
                        report["age_analysis"]["under_3_years"] += 1
                    elif age_years < 5:
                        report["age_analysis"]["under_5_years"] += 1
                    else:
                        report["age_analysis"]["over_5_years"] += 1
                except ValueError:
                    report["age_analysis"]["unknown"] += 1
            else:
                report["age_analysis"]["unknown"] += 1

        return report

    def search_configuration_items(
        self, search_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search configuration items using multiple criteria.

        Args:
            search_criteria: Dictionary with search parameters
                - text: Text search across name, serial, model
                - manufacturer: Manufacturer filter
                - ci_type: Configuration item type
                - location: Location filter
                - account_id: Account filter
                - active_only: Whether to include only active CIs

        Returns:
            List of matching configuration items
        """
        filters = []

        # Text search (simplified - actual implementation may use full-text search)
        text_search = search_criteria.get("text")
        if text_search:
            # This would typically be implemented as a more sophisticated search
            filters.append(
                QueryFilter(
                    field="configurationItemName", op="contains", value=text_search
                )
            )

        # Specific field filters
        if search_criteria.get("manufacturer"):
            filters.append(
                QueryFilter(
                    field="manufacturer", op="eq", value=search_criteria["manufacturer"]
                )
            )

        if search_criteria.get("ci_type"):
            filters.append(
                QueryFilter(
                    field="configurationItemType",
                    op="eq",
                    value=search_criteria["ci_type"],
                )
            )

        if search_criteria.get("location"):
            filters.append(
                QueryFilter(
                    field="location", op="contains", value=search_criteria["location"]
                )
            )

        if search_criteria.get("account_id"):
            filters.append(
                QueryFilter(
                    field="accountID", op="eq", value=search_criteria["account_id"]
                )
            )

        # Active filter
        active_only = search_criteria.get("active_only", True)
        if active_only:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters=filters)

    def validate_ci_data(self, ci_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration item data.

        Args:
            ci_data: CI data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = [
            "accountID",
            "configurationItemName",
            "configurationItemCategoryID",
            "configurationItemType",
        ]
        for field in required_fields:
            if field not in ci_data or ci_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate name
        name = ci_data.get("configurationItemName", "")
        if name:
            if len(name) < 2:
                errors.append("CI name must be at least 2 characters")
            elif len(name) > 100:
                errors.append("CI name must not exceed 100 characters")

        # Validate dates
        warranty_date = ci_data.get("warrantyExpirationDate")
        if warranty_date:
            try:
                if isinstance(warranty_date, str):
                    warranty_exp = datetime.fromisoformat(
                        warranty_date.replace("Z", "+00:00")
                    )
                    if warranty_exp < datetime.now():
                        warnings.append("Warranty expiration date is in the past")
            except ValueError:
                errors.append("Warranty expiration date must be a valid date")

        install_date = ci_data.get("installDate")
        if install_date:
            try:
                if isinstance(install_date, str):
                    installed = datetime.fromisoformat(
                        install_date.replace("Z", "+00:00")
                    )
                    if installed > datetime.now():
                        warnings.append("Install date is in the future")
            except ValueError:
                errors.append("Install date must be a valid date")

        # Validate serial number uniqueness
        serial_number = ci_data.get("serialNumber")
        if serial_number:
            existing_cis = self.get_by_serial_number(serial_number)
            if existing_cis and len(existing_cis) > 0:
                # Check if it's not the same CI being updated
                ci_id = ci_data.get("id")
                if not ci_id or any(ci["id"] != ci_id for ci in existing_cis):
                    warnings.append(
                        f"Serial number '{serial_number}' is already in use"
                    )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
