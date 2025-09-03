"""
BusinessDivisions Entity for py-autotask

This module provides the BusinessDivisionsEntity class for managing business divisions
in Autotask. Business divisions represent high-level organizational units for
financial reporting, resource allocation, and business segmentation.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity
from .query_helpers import (
    build_equality_filter,
    build_search_filters,
    build_active_filter,
    combine_filters,
)
from ..types import QueryFilter


class BusinessDivisionsEntity(BaseEntity):
    """
    Manages Autotask BusinessDivisions - organizational division management.

    Business divisions represent high-level organizational units within
    Autotask for financial reporting, resource allocation, and business
    segmentation. They support division-based analytics and management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "BusinessDivisions"

    def create_division(
        self,
        name: str,
        description: Optional[str] = None,
        division_manager_resource_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new business division.

        Args:
            name: Name of the division
            description: Description of the division
            division_manager_resource_id: ID of the division manager
            is_active: Whether the division is active
            **kwargs: Additional fields for the division

        Returns:
            Create response with new division ID
        """
        division_data = {"name": name, "isActive": is_active, **kwargs}

        if description:
            division_data["description"] = description
        if division_manager_resource_id:
            division_data["divisionManagerResourceID"] = division_manager_resource_id

        return self.create(division_data)

    def get_active_divisions(self) -> List[Dict[str, Any]]:
        """
        Get all active business divisions.

        Returns:
            List of active divisions
        """
        filters = [build_active_filter(True)]
        return self.query(filters=combine_filters(filters))

    def get_divisions_by_manager(
        self, manager_resource_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get divisions managed by a specific resource.

        Args:
            manager_resource_id: ID of the division manager

        Returns:
            List of divisions managed by the resource
        """
        filters = [
            build_equality_filter("divisionManagerResourceID", manager_resource_id)
        ]
        return self.query(filters=combine_filters(filters))

    def search_divisions(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search divisions by name or description.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching divisions
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        # Note: For OR logic with multiple fields, we need to make separate queries
        # and combine results, as Autotask API treats list filters as AND logic
        all_results = []
        for field in search_fields:
            search_filters = build_search_filters(search_term, [field])
            results = self.query(filters=search_filters)
            if hasattr(results, "items"):
                all_results.extend(results.items)
            else:
                all_results.extend(results)

        # Remove duplicates based on ID
        seen_ids = set()
        unique_results = []
        for division in all_results:
            division_id = division.get("id")
            if division_id and division_id not in seen_ids:
                seen_ids.add(division_id)
                unique_results.append(division)

        return unique_results

    def get_division_summary(self, division_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary for a division.

        Args:
            division_id: ID of the division

        Returns:
            Division summary with related data
        """
        division = self.get(division_id)

        # This would typically query related entities
        # For now, return structure with placeholder data

        return {
            "division": division,
            "summary": {
                "division_id": division_id,
                "total_resources": 0,  # Would count resources in division
                "active_projects": 0,  # Would count active projects
                "total_revenue": Decimal("0"),  # Would calculate division revenue
                "open_tickets": 0,  # Would count tickets
                "departments": 0,  # Would count departments in division
            },
        }

    def update_division_manager(
        self, division_id: int, new_manager_resource_id: int
    ) -> Dict[str, Any]:
        """
        Update division manager.

        Args:
            division_id: ID of the division
            new_manager_resource_id: ID of the new division manager

        Returns:
            Update response
        """
        return self.update(
            division_id, {"divisionManagerResourceID": new_manager_resource_id}
        )

    def get_division_performance_metrics(
        self, division_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a division.

        Args:
            division_id: ID of the division
            date_from: Start date for metrics
            date_to: End date for metrics

        Returns:
            Division performance metrics
        """
        # This would typically analyze various performance data
        # For now, return structure that could be populated

        return {
            "division_id": division_id,
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "performance_metrics": {
                "total_revenue": Decimal("0"),  # Would calculate from projects/invoices
                "total_costs": Decimal("0"),  # Would calculate costs
                "profit_margin": Decimal("0"),  # Would calculate profit
                "resource_utilization": 0.0,  # Would calculate utilization
                "project_completion_rate": 0.0,  # Would calculate completion rate
                "customer_satisfaction": 0.0,  # Would calculate satisfaction
            },
        }
