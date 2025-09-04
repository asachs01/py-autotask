"""
Countries entity for Autotask API operations.
"""

from typing import Any, Dict, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class CountriesEntity(BaseEntity):
    """
    Handles Country reference data operations for the Autotask API.

    Manages country codes, names, and related geographical information
    used throughout the Autotask system.
    """

    def __init__(self, client, entity_name: str = "Countries"):
        super().__init__(client, entity_name)

    def get_all_countries(self, active_only: bool = True) -> EntityList:
        """
        Get all countries in the system.

        Args:
            active_only: Whether to include only active countries

        Returns:
            List of countries
        """
        filters = []
        if active_only:
            filters = [{"field": "IsActive", "op": "eq", "value": "true"}]

        return self.query_all(filters=filters)

    def get_country_by_code(self, country_code: str) -> Optional[EntityDict]:
        """
        Get a country by its ISO country code.

        Args:
            country_code: ISO country code (e.g., 'US', 'CA', 'GB')

        Returns:
            Country data or None if not found
        """
        filters = [{"field": "CountryCode", "op": "eq", "value": country_code.upper()}]
        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def get_country_by_name(self, country_name: str) -> Optional[EntityDict]:
        """
        Get a country by its name.

        Args:
            country_name: Country name

        Returns:
            Country data or None if not found
        """
        filters = [{"field": "Name", "op": "eq", "value": country_name}]
        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def search_countries_by_name(self, name_pattern: str) -> EntityList:
        """
        Search countries by name pattern.

        Args:
            name_pattern: Name pattern to search for

        Returns:
            List of matching countries
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]
        return self.query_all(filters=filters)

    def get_countries_by_region(self, region: str) -> EntityList:
        """
        Get countries in a specific region.

        Args:
            region: Region name (e.g., 'North America', 'Europe')

        Returns:
            List of countries in the region
        """
        filters = [{"field": "Region", "op": "eq", "value": region}]
        return self.query_all(filters=filters)

    def get_countries_by_currency(self, currency_code: str) -> EntityList:
        """
        Get countries that use a specific currency.

        Args:
            currency_code: Currency code (e.g., 'USD', 'EUR', 'GBP')

        Returns:
            List of countries using the currency
        """
        filters = [
            {"field": "CurrencyCode", "op": "eq", "value": currency_code.upper()}
        ]
        return self.query_all(filters=filters)

    def validate_country_code(self, country_code: str) -> Dict[str, Any]:
        """
        Validate if a country code is valid and active.

        Args:
            country_code: Country code to validate

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": False,
            "country_code": country_code.upper(),
            "country_data": None,
            "is_active": False,
            "warnings": [],
        }

        country = self.get_country_by_code(country_code)
        if country:
            result["valid"] = True
            result["country_data"] = country
            result["is_active"] = country.get("IsActive", True)

            if not result["is_active"]:
                result["warnings"].append("Country is not currently active")
        else:
            result["warnings"].append("Country code not found in system")

        return result

    def get_popular_countries(self, limit: int = 20) -> EntityList:
        """
        Get commonly used countries.

        Note: This would typically be based on usage statistics.

        Args:
            limit: Maximum number of countries to return

        Returns:
            List of popular countries
        """
        # Common countries based on typical business usage
        popular_codes = [
            "US",
            "CA",
            "GB",
            "AU",
            "DE",
            "FR",
            "IT",
            "ES",
            "NL",
            "BE",
            "CH",
            "AT",
            "SE",
            "DK",
            "NO",
            "FI",
            "JP",
            "KR",
            "SG",
            "HK",
        ]

        popular_countries = []
        for code in popular_codes[:limit]:
            country = self.get_country_by_code(code)
            if country:
                popular_countries.append(country)

        return popular_countries

    def get_country_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about countries in the system.

        Returns:
            Dictionary with country statistics
        """
        all_countries = self.query_all()
        active_countries = self.get_all_countries(active_only=True)

        stats = {
            "total_countries": len(all_countries),
            "active_countries": len(active_countries),
            "inactive_countries": len(all_countries) - len(active_countries),
            "by_region": {},
            "by_currency": {},
            "countries_with_states": 0,
            "countries_without_states": 0,
        }

        for country in all_countries:
            # Count by region
            region = country.get("Region", "Unknown")
            if region not in stats["by_region"]:
                stats["by_region"][region] = 0
            stats["by_region"][region] += 1

            # Count by currency
            currency = country.get("CurrencyCode", "Unknown")
            if currency not in stats["by_currency"]:
                stats["by_currency"][currency] = 0
            stats["by_currency"][currency] += 1

            # Count states/provinces
            if country.get("HasStatesProvinces", False):
                stats["countries_with_states"] += 1
            else:
                stats["countries_without_states"] += 1

        return stats

    def get_timezone_countries(self, timezone: str) -> EntityList:
        """
        Get countries in a specific timezone.

        Args:
            timezone: Timezone identifier (e.g., 'America/New_York')

        Returns:
            List of countries in the timezone
        """
        filters = [{"field": "Timezone", "op": "eq", "value": timezone}]
        return self.query_all(filters=filters)

    def get_countries_requiring_states(self) -> EntityList:
        """
        Get countries that require state/province information.

        Returns:
            List of countries requiring states
        """
        filters = [{"field": "HasStatesProvinces", "op": "eq", "value": "true"}]
        return self.query_all(filters=filters)

    def format_country_display_name(
        self, country_data: EntityDict, include_code: bool = True
    ) -> str:
        """
        Format a country name for display.

        Args:
            country_data: Country data dictionary
            include_code: Whether to include the country code

        Returns:
            Formatted country display name
        """
        name = country_data.get("Name", "Unknown Country")
        code = country_data.get("CountryCode", "")

        if include_code and code:
            return f"{name} ({code})"
        else:
            return name

    def get_country_localization_info(self, country_code: str) -> Dict[str, Any]:
        """
        Get localization information for a country.

        Args:
            country_code: ISO country code

        Returns:
            Dictionary with localization information
        """
        country = self.get_country_by_code(country_code)
        if not country:
            return {"error": "Country not found"}

        info = {
            "country_code": country_code.upper(),
            "country_name": country.get("Name", ""),
            "currency_code": country.get("CurrencyCode", ""),
            "currency_symbol": country.get("CurrencySymbol", ""),
            "date_format": country.get("DateFormat", "MM/dd/yyyy"),
            "time_format": country.get("TimeFormat", "12"),  # 12 or 24 hour
            "decimal_separator": country.get("DecimalSeparator", "."),
            "thousands_separator": country.get("ThousandsSeparator", ","),
            "address_format": country.get("AddressFormat", ""),
            "postal_code_required": country.get("PostalCodeRequired", False),
            "postal_code_format": country.get("PostalCodeFormat", ""),
            "phone_number_format": country.get("PhoneNumberFormat", ""),
            "tax_id_format": country.get("TaxIdFormat", ""),
        }

        return info

    def get_neighboring_countries(self, country_code: str) -> EntityList:
        """
        Get countries that neighbor the specified country.

        Note: This would require geographical relationship data.

        Args:
            country_code: ISO country code

        Returns:
            List of neighboring countries
        """
        # This would typically require a separate geographic relationships table
        # For now, return empty list with a note
        self.logger.warning(
            "Neighboring countries feature requires geographic relationship data"
        )
        return []

    def validate_address_format(
        self, country_code: str, address_components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate address components against country requirements.

        Args:
            country_code: ISO country code
            address_components: Dictionary with address components

        Returns:
            Validation result dictionary
        """
        country = self.get_country_by_code(country_code)
        if not country:
            return {"valid": False, "error": "Country not found"}

        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "country": country.get("Name", ""),
        }

        # Check postal code requirement
        if country.get("PostalCodeRequired", False):
            if not address_components.get("postal_code"):
                result["errors"].append("Postal code is required for this country")
                result["valid"] = False

        # Check state/province requirement
        if country.get("HasStatesProvinces", False):
            if not address_components.get("state"):
                result["warnings"].append(
                    "State/province information recommended for this country"
                )

        # Validate postal code format if provided
        postal_code = address_components.get("postal_code")
        postal_format = country.get("PostalCodeFormat")
        if postal_code and postal_format:
            # This would implement regex validation based on postal_format
            # For now, just check basic length
            if len(postal_code) < 3:
                result["warnings"].append(
                    "Postal code may be too short for this country"
                )

        return result
