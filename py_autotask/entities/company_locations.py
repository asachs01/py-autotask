"""
Company Locations entity for Autotask API operations.
"""

from typing import Any, Dict, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class CompanyLocationsEntity(BaseEntity):
    """
    Handles Company Location operations for the Autotask API.

    Manages multiple physical locations for companies, including
    addresses, contact information, and location-specific settings.
    """

    def __init__(self, client, entity_name: str = "CompanyLocations"):
        super().__init__(client, entity_name)

    def create_location(
        self,
        company_id: int,
        name: str,
        address1: str,
        city: str,
        state: str,
        postal_code: str,
        country: str = "United States",
        address2: Optional[str] = None,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        is_primary: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new company location.

        Args:
            company_id: ID of the company
            name: Location name/identifier
            address1: Primary address line
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            address2: Secondary address line
            phone: Phone number
            fax: Fax number
            is_primary: Whether this is the primary location
            **kwargs: Additional location fields

        Returns:
            Created company location data
        """
        location_data = {
            "CompanyID": company_id,
            "Name": name,
            "Address1": address1,
            "City": city,
            "State": state,
            "PostalCode": postal_code,
            "Country": country,
            "IsPrimary": is_primary,
            **kwargs,
        }

        if address2:
            location_data["Address2"] = address2
        if phone:
            location_data["Phone"] = phone
        if fax:
            location_data["Fax"] = fax

        return self.create(location_data)

    def get_locations_by_company(
        self,
        company_id: int,
        active_only: bool = True,
    ) -> EntityList:
        """
        Get all locations for a specific company.

        Args:
            company_id: Company ID to filter by
            active_only: Whether to include only active locations

        Returns:
            List of company locations
        """
        filters = [{"field": "CompanyID", "op": "eq", "value": str(company_id)}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_primary_location(self, company_id: int) -> Optional[EntityDict]:
        """
        Get the primary location for a company.

        Args:
            company_id: Company ID

        Returns:
            Primary location data or None if not found
        """
        filters = [
            {"field": "CompanyID", "op": "eq", "value": str(company_id)},
            {"field": "IsPrimary", "op": "eq", "value": "true"},
        ]

        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def set_primary_location(self, company_id: int, location_id: int) -> Dict[str, Any]:
        """
        Set a location as the primary location for a company.

        Args:
            company_id: Company ID
            location_id: Location ID to set as primary

        Returns:
            Dictionary with operation results
        """
        results = {"updated_locations": [], "errors": []}

        # First, unset any existing primary location
        current_primary = self.get_primary_location(company_id)
        if current_primary and int(current_primary["id"]) != location_id:
            try:
                updated = self.update_by_id(
                    int(current_primary["id"]), {"IsPrimary": False}
                )
                results["updated_locations"].append(updated)
            except Exception as e:
                results["errors"].append(f"Failed to unset current primary: {e}")

        # Set new primary location
        try:
            updated = self.update_by_id(location_id, {"IsPrimary": True})
            results["updated_locations"].append(updated)
        except Exception as e:
            results["errors"].append(f"Failed to set new primary: {e}")

        return results

    def search_locations_by_city(
        self,
        city: str,
        state: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> EntityList:
        """
        Search locations by city name.

        Args:
            city: City name to search
            state: Optional state filter
            company_id: Optional company filter

        Returns:
            List of matching locations
        """
        filters = [{"field": "City", "op": "eq", "value": city}]

        if state:
            filters.append({"field": "State", "op": "eq", "value": state})

        if company_id:
            filters.append({"field": "CompanyID", "op": "eq", "value": str(company_id)})

        return self.query_all(filters=filters)

    def search_locations_by_postal_code(
        self,
        postal_code: str,
        company_id: Optional[int] = None,
    ) -> EntityList:
        """
        Search locations by postal code.

        Args:
            postal_code: Postal code to search
            company_id: Optional company filter

        Returns:
            List of matching locations
        """
        filters = [{"field": "PostalCode", "op": "eq", "value": postal_code}]

        if company_id:
            filters.append({"field": "CompanyID", "op": "eq", "value": str(company_id)})

        return self.query_all(filters=filters)

    def update_location_address(
        self,
        location_id: int,
        address1: str,
        city: str,
        state: str,
        postal_code: str,
        address2: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Update address information for a location.

        Args:
            location_id: Location ID to update
            address1: New primary address
            city: New city
            state: New state
            postal_code: New postal code
            address2: New secondary address
            country: New country

        Returns:
            Updated location data
        """
        update_data = {
            "Address1": address1,
            "City": city,
            "State": state,
            "PostalCode": postal_code,
        }

        if address2 is not None:
            update_data["Address2"] = address2

        if country:
            update_data["Country"] = country

        return self.update_by_id(location_id, update_data)

    def update_location_contact_info(
        self,
        location_id: int,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Update contact information for a location.

        Args:
            location_id: Location ID to update
            phone: New phone number
            fax: New fax number
            email: New email address

        Returns:
            Updated location data
        """
        update_data = {}

        if phone is not None:
            update_data["Phone"] = phone

        if fax is not None:
            update_data["Fax"] = fax

        if email is not None:
            update_data["Email"] = email

        if update_data:
            return self.update_by_id(location_id, update_data)

        return None

    def deactivate_location(self, location_id: int) -> Optional[EntityDict]:
        """
        Deactivate a company location.

        Args:
            location_id: Location ID to deactivate

        Returns:
            Updated location data
        """
        return self.update_by_id(location_id, {"IsActive": False})

    def activate_location(self, location_id: int) -> Optional[EntityDict]:
        """
        Activate a company location.

        Args:
            location_id: Location ID to activate

        Returns:
            Updated location data
        """
        return self.update_by_id(location_id, {"IsActive": True})

    def get_location_statistics(self, company_id: int) -> Dict[str, Any]:
        """
        Get statistics about locations for a company.

        Args:
            company_id: Company ID

        Returns:
            Dictionary with location statistics
        """
        all_locations = self.get_locations_by_company(company_id, active_only=False)

        stats = {
            "total_locations": len(all_locations),
            "active_locations": 0,
            "inactive_locations": 0,
            "has_primary": False,
            "countries": set(),
            "states": set(),
            "cities": set(),
        }

        for location in all_locations:
            # Count active/inactive
            if location.get("IsActive", True):
                stats["active_locations"] += 1
            else:
                stats["inactive_locations"] += 1

            # Check for primary
            if location.get("IsPrimary", False):
                stats["has_primary"] = True

            # Collect geographic data
            if location.get("Country"):
                stats["countries"].add(location["Country"])
            if location.get("State"):
                stats["states"].add(location["State"])
            if location.get("City"):
                stats["cities"].add(location["City"])

        # Convert sets to counts
        stats["unique_countries"] = len(stats["countries"])
        stats["unique_states"] = len(stats["states"])
        stats["unique_cities"] = len(stats["cities"])

        # Remove sets from final output
        del stats["countries"]
        del stats["states"]
        del stats["cities"]

        return stats

    def validate_location_data(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate location data before creation/update.

        Args:
            location_data: Location data to validate

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Required fields check
        required_fields = [
            "CompanyID",
            "Name",
            "Address1",
            "City",
            "State",
            "PostalCode",
        ]
        for field in required_fields:
            if field not in location_data or not location_data[field]:
                result["errors"].append(f"Missing required field: {field}")
                result["valid"] = False

        # Format validations
        if "PostalCode" in location_data:
            postal_code = str(location_data["PostalCode"])
            if len(postal_code) < 3:
                result["warnings"].append("Postal code seems too short")

        if "Phone" in location_data and location_data["Phone"]:
            phone = str(location_data["Phone"])
            if len(phone) < 10:
                result["warnings"].append("Phone number seems too short")

        return result
