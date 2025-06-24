"""
Holiday Sets entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class HolidaySetsEntity(BaseEntity):
    """
    Handles all Holiday Set-related operations for the Autotask API.

    Holiday sets manage holiday calendar definitions for resource planning
    and scheduling, enabling proper consideration of holidays in project timelines.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_holiday_set(
        self,
        name: str,
        description: Optional[str] = None,
        country_code: Optional[str] = None,
        is_default: bool = False,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new holiday set.

        Args:
            name: Name of the holiday set
            description: Description of the holiday set
            country_code: Country code for holiday set (e.g., 'US', 'CA', 'UK')
            is_default: Whether this is the default holiday set
            is_active: Whether the holiday set is active
            **kwargs: Additional holiday set fields

        Returns:
            Created holiday set data

        Example:
            holiday_set = client.holiday_sets.create_holiday_set(
                "US Federal Holidays 2024",
                description="Standard US federal holidays for 2024",
                country_code="US"
            )
        """
        holiday_set_data = {
            "Name": name,
            "IsDefault": is_default,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            holiday_set_data["Description"] = description
        if country_code:
            holiday_set_data["CountryCode"] = country_code

        return self.create(holiday_set_data)

    def get_active_holiday_sets(
        self, country_code: Optional[str] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all active holiday sets.

        Args:
            country_code: Optional country filter
            limit: Maximum number of holiday sets to return

        Returns:
            List of active holiday sets

        Example:
            sets = client.holiday_sets.get_active_holiday_sets()
        """
        filters = [{"field": "IsActive", "op": "eq", "value": True}]

        if country_code:
            filters.append({"field": "CountryCode", "op": "eq", "value": country_code})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_default_holiday_set(self) -> Optional[EntityDict]:
        """
        Get the default holiday set.

        Returns:
            Default holiday set data or None if not found

        Example:
            default_set = client.holiday_sets.get_default_holiday_set()
        """
        filters = [
            {"field": "IsDefault", "op": "eq", "value": True},
            {"field": "IsActive", "op": "eq", "value": True},
        ]

        response = self.query(filters=filters, max_records=1)
        items = response.items if hasattr(response, "items") else response
        return items[0] if items else None

    def get_holiday_set_holidays(self, holiday_set_id: int) -> List[EntityDict]:
        """
        Get all holidays for a specific holiday set.

        Args:
            holiday_set_id: ID of the holiday set

        Returns:
            List of holidays in the set

        Example:
            holidays = client.holiday_sets.get_holiday_set_holidays(12345)
        """
        filters = [{"field": "HolidaySetID", "op": "eq", "value": holiday_set_id}]

        # Query holidays entity
        response = self.client.query("Holidays", filters)
        return response.items if hasattr(response, "items") else response

    def get_holidays_by_date_range(
        self,
        holiday_set_id: int,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get holidays within a specific date range for a holiday set.

        Args:
            holiday_set_id: ID of the holiday set
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of holidays to return

        Returns:
            List of holidays within the date range

        Example:
            holidays = client.holiday_sets.get_holidays_by_date_range(
                12345, "2024-01-01", "2024-12-31"
            )
        """
        filters = [
            {"field": "HolidaySetID", "op": "eq", "value": holiday_set_id},
            {"field": "HolidayDate", "op": "gte", "value": start_date},
            {"field": "HolidayDate", "op": "lte", "value": end_date},
        ]

        response = self.client.query("Holidays", filters)
        items = response.items if hasattr(response, "items") else response

        if limit:
            return items[:limit]
        return items

    def activate_holiday_set(self, holiday_set_id: int) -> EntityDict:
        """
        Activate a holiday set.

        Args:
            holiday_set_id: ID of holiday set to activate

        Returns:
            Updated holiday set data

        Example:
            activated = client.holiday_sets.activate_holiday_set(12345)
        """
        return self.update_by_id(holiday_set_id, {"IsActive": True})

    def deactivate_holiday_set(self, holiday_set_id: int) -> EntityDict:
        """
        Deactivate a holiday set.

        Args:
            holiday_set_id: ID of holiday set to deactivate

        Returns:
            Updated holiday set data

        Example:
            deactivated = client.holiday_sets.deactivate_holiday_set(12345)
        """
        return self.update_by_id(holiday_set_id, {"IsActive": False})

    def set_as_default(self, holiday_set_id: int) -> EntityDict:
        """
        Set a holiday set as the default.

        Args:
            holiday_set_id: ID of holiday set to set as default

        Returns:
            Updated holiday set data

        Example:
            default_set = client.holiday_sets.set_as_default(12345)
        """
        # First, unset any existing default
        try:
            current_default = self.get_default_holiday_set()
            if current_default and current_default.get("id") != holiday_set_id:
                self.update_by_id(current_default["id"], {"IsDefault": False})
        except Exception as e:
            self.logger.warning(f"Error unsetting current default: {e}")

        # Set new default
        return self.update_by_id(holiday_set_id, {"IsDefault": True, "IsActive": True})

    def clone_holiday_set(
        self,
        holiday_set_id: int,
        new_name: str,
        new_year: Optional[int] = None,
        copy_holidays: bool = True,
    ) -> EntityDict:
        """
        Clone a holiday set with optional year adjustment.

        Args:
            holiday_set_id: ID of holiday set to clone
            new_name: Name for the cloned holiday set
            new_year: Optional year to adjust holidays to
            copy_holidays: Whether to copy associated holidays

        Returns:
            Created cloned holiday set data

        Example:
            cloned = client.holiday_sets.clone_holiday_set(
                12345, "US Federal Holidays 2025", new_year=2025
            )
        """
        original = self.get(holiday_set_id)
        if not original:
            raise ValueError(f"Holiday set {holiday_set_id} not found")

        # Create new holiday set
        clone_data = {
            "Name": new_name,
            "Description": original.get("Description"),
            "CountryCode": original.get("CountryCode"),
            "IsDefault": False,  # Never clone as default
            "IsActive": True,
        }

        new_holiday_set = self.create(clone_data)
        new_holiday_set_id = new_holiday_set.get("item_id") or new_holiday_set.get("id")

        # Copy holidays if requested
        if copy_holidays and new_holiday_set_id:
            original_holidays = self.get_holiday_set_holidays(holiday_set_id)

            for holiday in original_holidays:
                holiday_data = {
                    "HolidaySetID": new_holiday_set_id,
                    "Name": holiday.get("Name"),
                    "Description": holiday.get("Description"),
                    "HolidayDate": holiday.get("HolidayDate"),
                }

                # Adjust year if specified
                if new_year and holiday.get("HolidayDate"):
                    try:
                        original_date = datetime.fromisoformat(holiday["HolidayDate"])
                        new_date = original_date.replace(year=new_year)
                        holiday_data["HolidayDate"] = new_date.isoformat()
                    except (ValueError, TypeError):
                        pass  # Keep original date if parsing fails

                try:
                    self.client.create_entity("Holidays", holiday_data)
                except Exception as e:
                    self.logger.error(
                        f"Failed to copy holiday {holiday.get('Name')}: {e}"
                    )

        return new_holiday_set

    def get_holiday_set_summary(self, holiday_set_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a holiday set.

        Args:
            holiday_set_id: ID of the holiday set

        Returns:
            Holiday set summary with statistics

        Example:
            summary = client.holiday_sets.get_holiday_set_summary(12345)
        """
        holiday_set = self.get(holiday_set_id)
        if not holiday_set:
            return {}

        holidays = self.get_holiday_set_holidays(holiday_set_id)

        # Analyze holidays by year
        holiday_years = {}
        for holiday in holidays:
            if holiday.get("HolidayDate"):
                try:
                    year = datetime.fromisoformat(holiday["HolidayDate"]).year
                    holiday_years[year] = holiday_years.get(year, 0) + 1
                except (ValueError, TypeError):
                    pass

        # Find next holiday
        today = datetime.now().date()
        upcoming_holidays = []
        for holiday in holidays:
            if holiday.get("HolidayDate"):
                try:
                    holiday_date = datetime.fromisoformat(holiday["HolidayDate"]).date()
                    if holiday_date >= today:
                        upcoming_holidays.append((holiday_date, holiday))
                except (ValueError, TypeError):
                    pass

        upcoming_holidays.sort(key=lambda x: x[0])
        next_holiday = upcoming_holidays[0][1] if upcoming_holidays else None

        return {
            "holiday_set_id": holiday_set_id,
            "name": holiday_set.get("Name"),
            "description": holiday_set.get("Description"),
            "country_code": holiday_set.get("CountryCode"),
            "is_default": holiday_set.get("IsDefault"),
            "is_active": holiday_set.get("IsActive"),
            "total_holidays": len(holidays),
            "holidays_by_year": holiday_years,
            "years_covered": list(holiday_years.keys()),
            "next_holiday": (
                {
                    "name": next_holiday.get("Name"),
                    "date": next_holiday.get("HolidayDate"),
                    "days_until": (
                        datetime.fromisoformat(next_holiday["HolidayDate"]).date()
                        - today
                    ).days,
                }
                if next_holiday
                else None
            ),
            "upcoming_holidays_count": len(upcoming_holidays),
        }

    def get_holiday_sets_by_country(
        self, country_code: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get holiday sets for a specific country.

        Args:
            country_code: Country code to filter by
            active_only: Whether to return only active sets
            limit: Maximum number of sets to return

        Returns:
            List of holiday sets for the country

        Example:
            us_sets = client.holiday_sets.get_holiday_sets_by_country("US")
        """
        filters = [{"field": "CountryCode", "op": "eq", "value": country_code}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_holiday_set(self, holiday_set_id: int) -> Dict[str, Any]:
        """
        Validate a holiday set for completeness and accuracy.

        Args:
            holiday_set_id: ID of the holiday set to validate

        Returns:
            Validation results with warnings and recommendations

        Example:
            validation = client.holiday_sets.validate_holiday_set(12345)
        """
        holiday_set = self.get(holiday_set_id)
        if not holiday_set:
            return {"error": f"Holiday set {holiday_set_id} not found"}

        holidays = self.get_holiday_set_holidays(holiday_set_id)
        warnings = []
        recommendations = []

        # Check for holidays
        if not holidays:
            warnings.append("No holidays defined in this set")
            recommendations.append("Add holidays to make the set useful")
        else:
            # Check for year coverage
            current_year = datetime.now().year
            years = set()
            for holiday in holidays:
                if holiday.get("HolidayDate"):
                    try:
                        year = datetime.fromisoformat(holiday["HolidayDate"]).year
                        years.add(year)
                    except (ValueError, TypeError):
                        warnings.append(
                            f"Invalid date format in holiday: {holiday.get('Name')}"
                        )

            if current_year not in years:
                warnings.append(
                    f"No holidays defined for current year ({current_year})"
                )
                recommendations.append("Add holidays for the current year")

            if len(years) == 1:
                warnings.append("Only one year of holidays defined")
                recommendations.append("Consider adding holidays for multiple years")

        # Check if active but not used
        if holiday_set.get("IsActive"):
            # Could check for resource assignments, project usage, etc.
            pass

        return {
            "holiday_set_id": holiday_set_id,
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": recommendations,
            "holiday_count": len(holidays),
            "years_covered": len(
                set(
                    datetime.fromisoformat(h["HolidayDate"]).year
                    for h in holidays
                    if h.get("HolidayDate")
                )
            ),
        }

    def get_holidays_impacting_date_range(
        self, holiday_set_id: int, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Get holidays that impact a specific date range for planning.

        Args:
            holiday_set_id: ID of the holiday set
            start_date: Start date of the range (ISO format)
            end_date: End date of the range (ISO format)

        Returns:
            Holiday impact analysis for the date range

        Example:
            impact = client.holiday_sets.get_holidays_impacting_date_range(
                12345, "2024-06-01", "2024-08-31"
            )
        """
        holidays = self.get_holidays_by_date_range(holiday_set_id, start_date, end_date)

        # Calculate impact
        try:
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
            total_days = (end - start).days + 1

            # Count weekdays
            weekdays = 0
            current = start
            while current <= end:
                if current.weekday() < 5:  # Monday to Friday
                    weekdays += 1
                current += timedelta(days=1)

            # Count holidays that fall on weekdays
            weekday_holidays = 0
            holiday_details = []

            for holiday in holidays:
                if holiday.get("HolidayDate"):
                    try:
                        holiday_date = datetime.fromisoformat(
                            holiday["HolidayDate"]
                        ).date()
                        if holiday_date.weekday() < 5:  # Weekday holiday
                            weekday_holidays += 1

                        holiday_details.append(
                            {
                                "name": holiday.get("Name"),
                                "date": holiday.get("HolidayDate"),
                                "weekday": holiday_date.strftime("%A"),
                                "impacts_workday": holiday_date.weekday() < 5,
                            }
                        )
                    except (ValueError, TypeError):
                        pass

            working_days = weekdays - weekday_holidays

        except (ValueError, TypeError):
            return {"error": "Invalid date format"}

        return {
            "holiday_set_id": holiday_set_id,
            "date_range": {
                "start": start_date,
                "end": end_date,
                "total_days": total_days,
                "weekdays": weekdays,
                "working_days": working_days,
            },
            "holidays": {
                "total_holidays": len(holidays),
                "weekday_holidays": weekday_holidays,
                "holiday_details": holiday_details,
            },
            "impact_percentage": round(
                (weekday_holidays / weekdays * 100) if weekdays > 0 else 0, 2
            ),
        }

    def bulk_update_holiday_sets(
        self, updates: List[Dict[str, Any]], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Update multiple holiday sets in batches.

        Args:
            updates: List of update data (must include 'id' field)
            batch_size: Number of sets to update per batch

        Returns:
            List of updated holiday set data

        Example:
            updates = [
                {'id': 12345, 'IsActive': True},
                {'id': 12346, 'IsActive': False}
            ]
            results = client.holiday_sets.bulk_update_holiday_sets(updates)
        """
        results = []

        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]

            for update in batch:
                try:
                    set_id = update.pop("id")
                    result = self.update_by_id(set_id, update)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update holiday set {update.get('id')}: {e}"
                    )
                    continue

        return results

    def get_country_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of holiday sets by country.

        Returns:
            Distribution statistics by country

        Example:
            distribution = client.holiday_sets.get_country_distribution()
        """
        all_sets = self.query_all()

        country_counts = {}
        active_country_counts = {}

        for holiday_set in all_sets:
            country = holiday_set.get("CountryCode", "Unknown")
            country_counts[country] = country_counts.get(country, 0) + 1

            if holiday_set.get("IsActive"):
                active_country_counts[country] = (
                    active_country_counts.get(country, 0) + 1
                )

        return {
            "total_sets": len(all_sets),
            "active_sets": sum(active_country_counts.values()),
            "countries": list(country_counts.keys()),
            "country_distribution": country_counts,
            "active_country_distribution": active_country_counts,
            "countries_with_active_sets": len(
                [c for c in active_country_counts.values() if c > 0]
            ),
        }
