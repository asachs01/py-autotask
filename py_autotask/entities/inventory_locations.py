"""
InventoryLocations entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class InventoryLocationsEntity(BaseEntity):
    """
    Handles all Inventory Location-related operations for the Autotask API.

    Inventory Locations represent physical locations where inventory items are stored.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_inventory_location(
        self,
        name: str,
        is_default: bool = False,
        is_pick: bool = True,
        is_ship: bool = True,
        address1: Optional[str] = None,
        address2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new inventory location.

        Args:
            name: Name of the inventory location
            is_default: Whether this is the default location
            is_pick: Whether items can be picked from this location
            is_ship: Whether items can be shipped from this location
            address1: Street address line 1
            address2: Street address line 2
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            **kwargs: Additional inventory location fields

        Returns:
            Created inventory location data
        """
        location_data = {
            "Name": name,
            "IsDefault": is_default,
            "IsPick": is_pick,
            "IsShip": is_ship,
            **kwargs,
        }

        # Add optional address fields if provided
        if address1:
            location_data["Address1"] = address1
        if address2:
            location_data["Address2"] = address2
        if city:
            location_data["City"] = city
        if state:
            location_data["State"] = state
        if postal_code:
            location_data["PostalCode"] = postal_code
        if country:
            location_data["Country"] = country

        return self.create(location_data)

    def get_default_location(self) -> Optional[EntityDict]:
        """
        Get the default inventory location.

        Returns:
            Default inventory location data or None if not found
        """
        filters = [QueryFilter(field="IsDefault", op="eq", value=True)]
        results = self.query(filters=filters, max_records=1)

        return results[0] if results else None

    def get_pick_locations(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all locations where items can be picked.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of pick-enabled locations
        """
        filters = [QueryFilter(field="IsPick", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def get_ship_locations(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all locations where items can be shipped from.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of ship-enabled locations
        """
        filters = [QueryFilter(field="IsShip", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def search_locations_by_name(
        self, name: str, exact_match: bool = False
    ) -> List[EntityDict]:
        """
        Search for inventory locations by name.

        Args:
            name: Location name to search for
            exact_match: Whether to do exact match or partial match

        Returns:
            List of matching locations
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters)

    def get_locations_by_city(
        self, city: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get inventory locations in a specific city.

        Args:
            city: City name to filter by
            limit: Maximum number of records to return

        Returns:
            List of locations in the specified city
        """
        filters = [QueryFilter(field="City", op="eq", value=city)]

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
        Update the address of an inventory location.

        Args:
            location_id: ID of the location to update
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

    def set_as_default(self, location_id: int) -> EntityDict:
        """
        Set a location as the default inventory location.

        Args:
            location_id: ID of the location to set as default

        Returns:
            Updated location data
        """
        # First, unset any existing default location
        current_default = self.get_default_location()
        if current_default and current_default["id"] != location_id:
            self.update_by_id(current_default["id"], {"IsDefault": False})

        # Set the new default
        return self.update_by_id(location_id, {"IsDefault": True})

    def enable_pick_ship(
        self, location_id: int, enable_pick: bool = True, enable_ship: bool = True
    ) -> EntityDict:
        """
        Enable or disable pick and ship capabilities for a location.

        Args:
            location_id: ID of the location
            enable_pick: Whether to enable picking
            enable_ship: Whether to enable shipping

        Returns:
            Updated location data
        """
        return self.update_by_id(
            location_id, {"IsPick": enable_pick, "IsShip": enable_ship}
        )

    def get_location_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about inventory locations.

        Returns:
            Dictionary containing location statistics
        """
        all_locations = self.query()

        stats = {
            "total_locations": len(all_locations),
            "pick_enabled_locations": len(
                [loc for loc in all_locations if loc.get("IsPick", False)]
            ),
            "ship_enabled_locations": len(
                [loc for loc in all_locations if loc.get("IsShip", False)]
            ),
            "locations_with_address": len(
                [loc for loc in all_locations if loc.get("Address1")]
            ),
            "default_location": next(
                (loc["Name"] for loc in all_locations if loc.get("IsDefault", False)),
                "None",
            ),
        }

        return stats
