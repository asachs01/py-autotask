"""
QuoteLocations entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class QuoteLocationsEntity(BaseEntity):
    """
    Handles all Quote Location-related operations for the Autotask API.

    Quote Locations represent delivery or service locations associated with quotes.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_quote_location(
        self,
        quote_id: int,
        name: str,
        address1: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
        address2: Optional[str] = None,
        is_primary: bool = False,
        is_tax_exempt: bool = False,
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new quote location.

        Args:
            quote_id: ID of the quote
            name: Name/description of the location
            address1: Street address line 1
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            address2: Street address line 2
            is_primary: Whether this is the primary location for the quote
            is_tax_exempt: Whether this location is tax exempt
            contact_name: Name of contact at this location
            contact_phone: Phone number for this location
            contact_email: Email address for this location
            **kwargs: Additional location fields

        Returns:
            Created quote location data
        """
        location_data = {
            "QuoteID": quote_id,
            "Name": name,
            "Address1": address1,
            "City": city,
            "State": state,
            "PostalCode": postal_code,
            "Country": country,
            "IsPrimary": is_primary,
            "IsTaxExempt": is_tax_exempt,
            **kwargs,
        }

        if address2:
            location_data["Address2"] = address2
        if contact_name:
            location_data["ContactName"] = contact_name
        if contact_phone:
            location_data["ContactPhone"] = contact_phone
        if contact_email:
            location_data["ContactEmail"] = contact_email

        return self.create(location_data)

    def get_locations_by_quote(
        self, quote_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all locations for a specific quote.

        Args:
            quote_id: ID of the quote
            limit: Maximum number of records to return

        Returns:
            List of locations for the quote
        """
        filters = [QueryFilter(field="QuoteID", op="eq", value=quote_id)]

        return self.query(filters=filters, max_records=limit)

    def get_primary_location(self, quote_id: int) -> Optional[EntityDict]:
        """
        Get the primary location for a quote.

        Args:
            quote_id: ID of the quote

        Returns:
            Primary location data or None if not found
        """
        filters = [
            QueryFilter(field="QuoteID", op="eq", value=quote_id),
            QueryFilter(field="IsPrimary", op="eq", value=True),
        ]

        results = self.query(filters=filters, max_records=1)
        return results[0] if results else None

    def search_locations_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for quote locations by name.

        Args:
            name: Location name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching locations
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_locations_by_city(
        self, city: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get quote locations in a specific city.

        Args:
            city: City name to filter by
            limit: Maximum number of records to return

        Returns:
            List of locations in the specified city
        """
        filters = [QueryFilter(field="City", op="eq", value=city)]

        return self.query(filters=filters, max_records=limit)

    def get_locations_by_state(
        self, state: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get quote locations in a specific state/province.

        Args:
            state: State/province to filter by
            limit: Maximum number of records to return

        Returns:
            List of locations in the specified state
        """
        filters = [QueryFilter(field="State", op="eq", value=state)]

        return self.query(filters=filters, max_records=limit)

    def get_tax_exempt_locations(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all tax-exempt quote locations.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of tax-exempt locations
        """
        filters = [QueryFilter(field="IsTaxExempt", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def update_location_address(
        self,
        location_id: int,
        address1: Optional[str] = None,
        address2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
    ) -> EntityDict:
        """
        Update the address of a quote location.

        Args:
            location_id: ID of the location
            address1: Street address line 1
            address2: Street address line 2
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name

        Returns:
            Updated location data
        """
        update_data = {}

        if address1 is not None:
            update_data["Address1"] = address1
        if address2 is not None:
            update_data["Address2"] = address2
        if city is not None:
            update_data["City"] = city
        if state is not None:
            update_data["State"] = state
        if postal_code is not None:
            update_data["PostalCode"] = postal_code
        if country is not None:
            update_data["Country"] = country

        return self.update_by_id(location_id, update_data)

    def update_location_contact(
        self,
        location_id: int,
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
    ) -> EntityDict:
        """
        Update the contact information for a quote location.

        Args:
            location_id: ID of the location
            contact_name: Contact name
            contact_phone: Contact phone number
            contact_email: Contact email address

        Returns:
            Updated location data
        """
        update_data = {}

        if contact_name is not None:
            update_data["ContactName"] = contact_name
        if contact_phone is not None:
            update_data["ContactPhone"] = contact_phone
        if contact_email is not None:
            update_data["ContactEmail"] = contact_email

        return self.update_by_id(location_id, update_data)

    def set_primary_location(self, quote_id: int, location_id: int) -> EntityDict:
        """
        Set a location as the primary location for a quote.

        Args:
            quote_id: ID of the quote
            location_id: ID of the location to set as primary

        Returns:
            Updated location data
        """
        # First, unset any existing primary location for this quote
        existing_locations = self.get_locations_by_quote(quote_id)
        for location in existing_locations:
            if location.get("IsPrimary", False) and location["id"] != location_id:
                self.update_by_id(location["id"], {"IsPrimary": False})

        # Set the new primary location
        return self.update_by_id(location_id, {"IsPrimary": True})

    def set_tax_exempt_status(
        self, location_id: int, is_tax_exempt: bool
    ) -> EntityDict:
        """
        Update the tax exempt status of a location.

        Args:
            location_id: ID of the location
            is_tax_exempt: Whether the location should be tax exempt

        Returns:
            Updated location data
        """
        return self.update_by_id(location_id, {"IsTaxExempt": is_tax_exempt})

    def get_location_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about quote locations.

        Returns:
            Dictionary containing location statistics
        """
        all_locations = self.query()

        # Group by state/country
        state_counts = {}
        country_counts = {}
        for location in all_locations:
            state = location.get("State", "Unknown")
            country = location.get("Country", "Unknown")

            state_counts[state] = state_counts.get(state, 0) + 1
            country_counts[country] = country_counts.get(country, 0) + 1

        stats = {
            "total_locations": len(all_locations),
            "primary_locations": len(
                [loc for loc in all_locations if loc.get("IsPrimary", False)]
            ),
            "tax_exempt_locations": len(
                [loc for loc in all_locations if loc.get("IsTaxExempt", False)]
            ),
            "locations_with_contact": len(
                [loc for loc in all_locations if loc.get("ContactName")]
            ),
            "unique_states": len(state_counts),
            "unique_countries": len(country_counts),
            "top_states": sorted(
                state_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "top_countries": sorted(
                country_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

        return stats

    def get_quote_location_summary(self, quote_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of locations for a specific quote.

        Args:
            quote_id: ID of the quote

        Returns:
            Dictionary with location summary for the quote
        """
        quote_locations = self.get_locations_by_quote(quote_id)

        primary_location = next(
            (loc for loc in quote_locations if loc.get("IsPrimary", False)), None
        )

        # Group by country/state
        countries = set(loc.get("Country") for loc in quote_locations)
        states = set(loc.get("State") for loc in quote_locations)

        summary = {
            "quote_id": quote_id,
            "total_locations": len(quote_locations),
            "primary_location": {
                "id": primary_location.get("id") if primary_location else None,
                "name": primary_location.get("Name") if primary_location else None,
                "city": primary_location.get("City") if primary_location else None,
                "state": primary_location.get("State") if primary_location else None,
            },
            "tax_exempt_locations": len(
                [loc for loc in quote_locations if loc.get("IsTaxExempt", False)]
            ),
            "locations_with_contacts": len(
                [loc for loc in quote_locations if loc.get("ContactName")]
            ),
            "geographic_spread": {
                "countries": len(countries),
                "states": len(states),
            },
            "locations": [
                {
                    "id": loc.get("id"),
                    "name": loc.get("Name"),
                    "city": loc.get("City"),
                    "state": loc.get("State"),
                    "is_primary": loc.get("IsPrimary", False),
                    "is_tax_exempt": loc.get("IsTaxExempt", False),
                }
                for loc in quote_locations
            ],
        }

        return summary
