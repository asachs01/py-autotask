"""
WorkTypes Entity for py-autotask

This module provides the WorkTypesEntity class for managing work types
in Autotask. Work types categorize different types of work for time tracking,
billing, and reporting purposes.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class WorkTypesEntity(BaseEntity):
    """
    Manages Autotask WorkTypes - work type classifications for time tracking.

    Work types define categories of work that can be performed and tracked
    in Autotask. They support time entry classification, billing categorization,
    and work analysis reporting.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "WorkTypes"

    def create_work_type(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        is_billable: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new work type.

        Args:
            name: Name of the work type
            description: Description of the work type
            is_active: Whether the work type is active
            is_billable: Whether work of this type is billable
            **kwargs: Additional fields for the work type

        Returns:
            Create response with new work type ID
        """
        work_type_data = {
            "name": name,
            "isActive": is_active,
            "isBillable": is_billable,
            **kwargs,
        }

        if description:
            work_type_data["description"] = description

        return self.create(work_type_data)

    def get_active_work_types(
        self, billable_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all active work types.

        Args:
            billable_only: Whether to only return billable work types

        Returns:
            List of active work types
        """
        filters = ["isActive eq true"]

        if billable_only:
            filters.append("isBillable eq true")

        return self.query(filter=" and ".join(filters))

    def get_billable_work_types(self) -> List[Dict[str, Any]]:
        """
        Get all billable work types.

        Returns:
            List of billable work types
        """
        return self.query(filter="isBillable eq true and isActive eq true")

    def get_non_billable_work_types(self) -> List[Dict[str, Any]]:
        """
        Get all non-billable work types.

        Returns:
            List of non-billable work types
        """
        return self.query(filter="isBillable eq false and isActive eq true")

    def search_work_types(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search work types by name or description.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching work types
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        filters = []
        for field in search_fields:
            filters.append(f"contains({field}, '{search_term}')")

        return self.query(filter=" or ".join(filters))

    def activate_work_type(self, work_type_id: int) -> Dict[str, Any]:
        """
        Activate a work type.

        Args:
            work_type_id: ID of the work type to activate

        Returns:
            Update response
        """
        return self.update(work_type_id, {"isActive": True})

    def deactivate_work_type(self, work_type_id: int) -> Dict[str, Any]:
        """
        Deactivate a work type.

        Args:
            work_type_id: ID of the work type to deactivate

        Returns:
            Update response
        """
        return self.update(work_type_id, {"isActive": False})

    def set_billability(self, work_type_id: int, is_billable: bool) -> Dict[str, Any]:
        """
        Set billability status for a work type.

        Args:
            work_type_id: ID of the work type
            is_billable: Whether the work type should be billable

        Returns:
            Update response
        """
        return self.update(work_type_id, {"isBillable": is_billable})

    def get_work_type_usage_summary(
        self,
        work_type_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get usage summary for a work type.

        Args:
            work_type_id: ID of the work type
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Work type usage summary
        """
        # This would typically query time entries using this work type
        # For now, return structure that could be populated

        return {
            "work_type_id": work_type_id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "usage_summary": {
                "total_time_entries": 0,  # Would count time entries
                "total_hours": Decimal("0"),  # Would sum hours
                "total_resources": 0,  # Would count unique resources
                "billable_hours": Decimal("0"),  # Would sum billable hours
                "non_billable_hours": Decimal("0"),  # Would sum non-billable hours
            },
        }

    def get_work_type_analytics(
        self, date_from: date, date_to: date, work_type_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for work types over a date range.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            work_type_ids: Optional list of specific work type IDs

        Returns:
            Work type analytics
        """
        if work_type_ids:
            work_type_filter = " or ".join(
                [f"id eq {wt_id}" for wt_id in work_type_ids]
            )
            work_types = self.query(filter=f"({work_type_filter})")
        else:
            work_types = self.get_active_work_types()

        analytics = []
        total_hours = Decimal("0")

        for work_type in work_types:
            work_type_id = work_type.get("id")

            # Would calculate actual usage from time entries
            usage_hours = Decimal("0")  # Placeholder

            analytics.append(
                {
                    "work_type_id": work_type_id,
                    "work_type_name": work_type.get("name"),
                    "is_billable": work_type.get("isBillable"),
                    "total_hours": usage_hours,
                    "percentage_of_total": 0.0,  # Would calculate percentage
                }
            )

            total_hours += usage_hours

        # Calculate percentages
        for item in analytics:
            if total_hours > 0:
                item["percentage_of_total"] = float(
                    item["total_hours"] / total_hours * 100
                )

        return {
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "summary": {
                "total_work_types": len(analytics),
                "total_hours": total_hours,
                "billable_work_types": len(
                    [wt for wt in work_types if wt.get("isBillable")]
                ),
            },
            "analytics": analytics,
        }

    def bulk_update_billability(
        self, billability_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update billability for multiple work types.

        Args:
            billability_updates: List of billability updates
                Each should contain: work_type_id, is_billable

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in billability_updates:
            work_type_id = update["work_type_id"]
            is_billable = update["is_billable"]

            try:
                result = self.set_billability(work_type_id, is_billable)
                results.append({"id": work_type_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": work_type_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(billability_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def copy_work_type(
        self,
        source_work_type_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing work type.

        Args:
            source_work_type_id: ID of the work type to copy
            new_name: Name for the new work type
            new_description: Description for the new work type

        Returns:
            Create response for the new work type
        """
        source_work_type = self.get(source_work_type_id)

        # Remove fields that shouldn't be copied
        copy_data = {
            k: v
            for k, v in source_work_type.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        copy_data["name"] = new_name
        if new_description:
            copy_data["description"] = new_description

        return self.create(copy_data)

    def get_work_type_trends(self, months_back: int = 12) -> Dict[str, Any]:
        """
        Get usage trends for work types over time.

        Args:
            months_back: Number of months to analyze

        Returns:
            Work type usage trends
        """
        # This would typically analyze time entry data over time
        # For now, return structure that could be populated

        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        return {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months": months_back,
            },
            "trends": {
                "most_used_work_types": [],  # Would rank by usage
                "growth_trends": [],  # Would show growth/decline
                "seasonal_patterns": [],  # Would identify patterns
            },
        }
