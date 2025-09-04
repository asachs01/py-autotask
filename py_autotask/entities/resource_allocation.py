"""
Resource Allocation entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ResourceAllocationEntity(BaseEntity):
    """
    Handles all Resource Allocation-related operations for the Autotask API.

    Resource allocation manages resource assignment and capacity planning
    across projects, tasks, and time periods.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_resource_allocation(
        self,
        resource_id: int,
        start_date: str,
        end_date: str,
        hours_per_day: float = 8.0,
        project_id: Optional[int] = None,
        task_id: Optional[int] = None,
        allocation_percentage: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new resource allocation.

        Args:
            resource_id: ID of the resource being allocated
            start_date: Start date of allocation (ISO format)
            end_date: End date of allocation (ISO format)
            hours_per_day: Hours per day for this allocation
            project_id: Optional project ID for allocation
            task_id: Optional task ID for allocation
            allocation_percentage: Percentage of resource capacity (0-100)
            **kwargs: Additional allocation fields

        Returns:
            Created resource allocation data

        Example:
            allocation = client.resource_allocation.create_resource_allocation(
                12345,
                "2024-01-01",
                "2024-03-31",
                hours_per_day=6.0,
                project_id=67890,
                allocation_percentage=75.0
            )
        """
        allocation_data = {
            "ResourceID": resource_id,
            "StartDate": start_date,
            "EndDate": end_date,
            "HoursPerDay": hours_per_day,
            **kwargs,
        }

        if project_id:
            allocation_data["ProjectID"] = project_id
        if task_id:
            allocation_data["TaskID"] = task_id
        if allocation_percentage is not None:
            allocation_data["AllocationPercentage"] = allocation_percentage

        return self.create(allocation_data)

    def get_resource_allocations(
        self,
        resource_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get allocations for a specific resource.

        Args:
            resource_id: Resource ID to filter by
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            limit: Maximum number of allocations to return

        Returns:
            List of resource allocations

        Example:
            allocations = client.resource_allocation.get_resource_allocations(12345)
        """
        filters = [{"field": "ResourceID", "op": "eq", "value": resource_id}]

        if start_date:
            filters.append({"field": "EndDate", "op": "gte", "value": start_date})
        if end_date:
            filters.append({"field": "StartDate", "op": "lte", "value": end_date})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_project_allocations(
        self, project_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all resource allocations for a specific project.

        Args:
            project_id: Project ID to filter by
            active_only: Whether to return only active allocations
            limit: Maximum number of allocations to return

        Returns:
            List of project resource allocations

        Example:
            allocations = client.resource_allocation.get_project_allocations(67890)
        """
        filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        if active_only:
            today = datetime.now().isoformat()
            filters.append({"field": "EndDate", "op": "gte", "value": today})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_resource_capacity(
        self, resource_id: int, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Calculate resource capacity and utilization for a date range.

        Args:
            resource_id: Resource ID to analyze
            start_date: Start date of analysis (ISO format)
            end_date: End date of analysis (ISO format)

        Returns:
            Resource capacity analysis

        Example:
            capacity = client.resource_allocation.get_resource_capacity(
                12345, "2024-01-01", "2024-01-31"
            )
        """
        allocations = self.get_resource_allocations(resource_id, start_date, end_date)

        # Calculate total allocated hours
        total_allocated_hours = 0.0
        allocation_details = []

        for allocation in allocations:
            try:
                alloc_start = max(
                    datetime.fromisoformat(start_date).date(),
                    datetime.fromisoformat(allocation["StartDate"]).date(),
                )
                alloc_end = min(
                    datetime.fromisoformat(end_date).date(),
                    datetime.fromisoformat(allocation["EndDate"]).date(),
                )

                if alloc_start <= alloc_end:
                    days = (alloc_end - alloc_start).days + 1
                    hours_per_day = float(allocation.get("HoursPerDay", 8.0))
                    allocation_hours = days * hours_per_day
                    total_allocated_hours += allocation_hours

                    allocation_details.append(
                        {
                            "allocation_id": allocation.get("id"),
                            "project_id": allocation.get("ProjectID"),
                            "start_date": allocation.get("StartDate"),
                            "end_date": allocation.get("EndDate"),
                            "hours_per_day": hours_per_day,
                            "total_hours": allocation_hours,
                        }
                    )
            except (ValueError, TypeError):
                continue

        # Calculate available capacity (assuming 8 hours per day, 5 days per week)
        try:
            period_start = datetime.fromisoformat(start_date).date()
            period_end = datetime.fromisoformat(end_date).date()

            # Count business days
            business_days = 0
            current = period_start
            while current <= period_end:
                if current.weekday() < 5:  # Monday to Friday
                    business_days += 1
                current += timedelta(days=1)

            available_hours = business_days * 8.0  # 8 hours per business day
            utilization_percentage = (
                (total_allocated_hours / available_hours * 100)
                if available_hours > 0
                else 0
            )

        except (ValueError, TypeError):
            available_hours = 0
            utilization_percentage = 0

        return {
            "resource_id": resource_id,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "business_days": business_days,
            },
            "capacity": {
                "available_hours": available_hours,
                "allocated_hours": total_allocated_hours,
                "remaining_hours": available_hours - total_allocated_hours,
                "utilization_percentage": round(utilization_percentage, 2),
            },
            "allocations": allocation_details,
        }

    def find_available_resources(
        self,
        start_date: str,
        end_date: str,
        required_hours_per_day: float = 8.0,
        min_utilization: float = 0.0,
        max_utilization: float = 80.0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find resources available for allocation in a date range.

        Args:
            start_date: Start date to check (ISO format)
            end_date: End date to check (ISO format)
            required_hours_per_day: Required hours per day
            min_utilization: Minimum utilization threshold (%)
            max_utilization: Maximum utilization threshold (%)
            limit: Maximum number of resources to return

        Returns:
            List of available resources with capacity info

        Example:
            available = client.resource_allocation.find_available_resources(
                "2024-02-01", "2024-02-29", required_hours_per_day=6.0, max_utilization=70.0
            )
        """
        # Get all resources
        try:
            resources_response = self.client.query("Resources", [])
            resources = (
                resources_response.items
                if hasattr(resources_response, "items")
                else resources_response
            )
        except Exception:
            resources = []

        available_resources = []

        for resource in resources:
            resource_id = resource.get("id")
            if not resource_id:
                continue

            # Check resource capacity
            capacity = self.get_resource_capacity(resource_id, start_date, end_date)
            utilization = capacity["capacity"]["utilization_percentage"]

            # Check if resource meets criteria
            if min_utilization <= utilization <= max_utilization:
                remaining_hours = capacity["capacity"]["remaining_hours"]

                try:
                    period_start = datetime.fromisoformat(start_date).date()
                    period_end = datetime.fromisoformat(end_date).date()
                    days = (period_end - period_start).days + 1
                    required_total_hours = days * required_hours_per_day

                    if remaining_hours >= required_total_hours:
                        available_resources.append(
                            {
                                "resource_id": resource_id,
                                "resource_name": resource.get("FirstName", "")
                                + " "
                                + resource.get("LastName", ""),
                                "current_utilization": utilization,
                                "remaining_hours": remaining_hours,
                                "can_accommodate_hours": required_total_hours,
                                "capacity_details": capacity,
                            }
                        )
                except (ValueError, TypeError):
                    continue

            if limit and len(available_resources) >= limit:
                break

        # Sort by utilization (ascending - less utilized first)
        available_resources.sort(key=lambda x: x["current_utilization"])

        return available_resources

    def allocate_resource_to_project(
        self,
        resource_id: int,
        project_id: int,
        start_date: str,
        end_date: str,
        hours_per_day: float,
        validate_capacity: bool = True,
    ) -> EntityDict:
        """
        Allocate a resource to a project with capacity validation.

        Args:
            resource_id: Resource ID to allocate
            project_id: Project ID to allocate to
            start_date: Start date of allocation (ISO format)
            end_date: End date of allocation (ISO format)
            hours_per_day: Hours per day for allocation
            validate_capacity: Whether to validate available capacity

        Returns:
            Created allocation data

        Example:
            allocation = client.resource_allocation.allocate_resource_to_project(
                12345, 67890, "2024-01-01", "2024-03-31", 6.0
            )
        """
        if validate_capacity:
            capacity = self.get_resource_capacity(resource_id, start_date, end_date)

            try:
                period_start = datetime.fromisoformat(start_date).date()
                period_end = datetime.fromisoformat(end_date).date()
                days = (period_end - period_start).days + 1
                required_hours = days * hours_per_day

                if required_hours > capacity["capacity"]["remaining_hours"]:
                    raise ValueError(
                        f"Insufficient capacity: need {required_hours} hours, "
                        f"only {capacity['capacity']['remaining_hours']} available"
                    )
            except (ValueError, TypeError) as e:
                if validate_capacity:
                    raise e

        return self.create_resource_allocation(
            resource_id=resource_id,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            hours_per_day=hours_per_day,
        )

    def get_allocation_conflicts(
        self, resource_id: int, start_date: str, end_date: str, hours_per_day: float
    ) -> List[Dict[str, Any]]:
        """
        Check for allocation conflicts for a resource.

        Args:
            resource_id: Resource ID to check
            start_date: Start date to check (ISO format)
            end_date: End date to check (ISO format)
            hours_per_day: Proposed hours per day

        Returns:
            List of conflicting allocations

        Example:
            conflicts = client.resource_allocation.get_allocation_conflicts(
                12345, "2024-02-01", "2024-02-15", 8.0
            )
        """
        existing_allocations = self.get_resource_allocations(
            resource_id, start_date, end_date
        )
        conflicts = []

        try:
            check_start = datetime.fromisoformat(start_date).date()
            check_end = datetime.fromisoformat(end_date).date()
        except (ValueError, TypeError):
            return conflicts

        for allocation in existing_allocations:
            try:
                alloc_start = datetime.fromisoformat(allocation["StartDate"]).date()
                alloc_end = datetime.fromisoformat(allocation["EndDate"]).date()

                # Check for overlap
                if not (check_end < alloc_start or check_start > alloc_end):
                    # Calculate overlap details
                    overlap_start = max(check_start, alloc_start)
                    overlap_end = min(check_end, alloc_end)
                    overlap_days = (overlap_end - overlap_start).days + 1

                    existing_hours = float(allocation.get("HoursPerDay", 8.0))
                    total_hours = hours_per_day + existing_hours

                    conflicts.append(
                        {
                            "allocation_id": allocation.get("id"),
                            "project_id": allocation.get("ProjectID"),
                            "existing_start": allocation.get("StartDate"),
                            "existing_end": allocation.get("EndDate"),
                            "existing_hours_per_day": existing_hours,
                            "proposed_hours_per_day": hours_per_day,
                            "total_hours_per_day": total_hours,
                            "overlap_start": overlap_start.isoformat(),
                            "overlap_end": overlap_end.isoformat(),
                            "overlap_days": overlap_days,
                            "is_overallocation": total_hours > 8.0,
                        }
                    )
            except (ValueError, TypeError):
                continue

        return conflicts

    def bulk_allocate_resources(
        self,
        allocations: List[Dict[str, Any]],
        validate_capacity: bool = True,
        batch_size: int = 20,
    ) -> List[EntityDict]:
        """
        Create multiple resource allocations in batches.

        Args:
            allocations: List of allocation data
            validate_capacity: Whether to validate capacity for each allocation
            batch_size: Number of allocations to process per batch

        Returns:
            List of created allocation data

        Example:
            allocations_data = [
                {
                    'resource_id': 12345,
                    'project_id': 67890,
                    'start_date': '2024-01-01',
                    'end_date': '2024-03-31',
                    'hours_per_day': 6.0
                }
            ]
            results = client.resource_allocation.bulk_allocate_resources(allocations_data)
        """
        results = []

        for i in range(0, len(allocations), batch_size):
            batch = allocations[i : i + batch_size]

            for allocation_data in batch:
                try:
                    if validate_capacity:
                        # Check capacity before creating
                        capacity = self.get_resource_capacity(
                            allocation_data["resource_id"],
                            allocation_data["start_date"],
                            allocation_data["end_date"],
                        )

                        try:
                            period_start = datetime.fromisoformat(
                                allocation_data["start_date"]
                            ).date()
                            period_end = datetime.fromisoformat(
                                allocation_data["end_date"]
                            ).date()
                            days = (period_end - period_start).days + 1
                            required_hours = days * allocation_data["hours_per_day"]

                            if required_hours > capacity["capacity"]["remaining_hours"]:
                                self.logger.warning(
                                    f"Skipping allocation for resource {allocation_data['resource_id']}: "
                                    f"insufficient capacity"
                                )
                                continue
                        except (ValueError, TypeError):
                            continue

                    result = self.create_resource_allocation(**allocation_data)
                    results.append(result)

                except Exception as e:
                    self.logger.error(f"Failed to create allocation: {e}")
                    continue

        return results

    def get_team_allocation_summary(
        self, resource_ids: List[int], start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """
        Get allocation summary for a team of resources.

        Args:
            resource_ids: List of resource IDs to analyze
            start_date: Start date of analysis (ISO format)
            end_date: End date of analysis (ISO format)

        Returns:
            Team allocation summary

        Example:
            summary = client.resource_allocation.get_team_allocation_summary(
                [12345, 12346, 12347], "2024-01-01", "2024-01-31"
            )
        """
        team_summary = {
            "period": {"start_date": start_date, "end_date": end_date},
            "team_size": len(resource_ids),
            "resources": [],
            "totals": {
                "available_hours": 0,
                "allocated_hours": 0,
                "remaining_hours": 0,
                "average_utilization": 0,
            },
        }

        utilizations = []

        for resource_id in resource_ids:
            capacity = self.get_resource_capacity(resource_id, start_date, end_date)

            resource_summary = {
                "resource_id": resource_id,
                "capacity": capacity["capacity"],
                "allocation_count": len(capacity["allocations"]),
            }

            team_summary["resources"].append(resource_summary)
            team_summary["totals"]["available_hours"] += capacity["capacity"][
                "available_hours"
            ]
            team_summary["totals"]["allocated_hours"] += capacity["capacity"][
                "allocated_hours"
            ]
            team_summary["totals"]["remaining_hours"] += capacity["capacity"][
                "remaining_hours"
            ]

            utilizations.append(capacity["capacity"]["utilization_percentage"])

        # Calculate average utilization
        if utilizations:
            team_summary["totals"]["average_utilization"] = round(
                sum(utilizations) / len(utilizations), 2
            )

        # Calculate team utilization percentage
        if team_summary["totals"]["available_hours"] > 0:
            team_summary["totals"]["team_utilization_percentage"] = round(
                team_summary["totals"]["allocated_hours"]
                / team_summary["totals"]["available_hours"]
                * 100,
                2,
            )
        else:
            team_summary["totals"]["team_utilization_percentage"] = 0

        return team_summary

    def optimize_resource_allocation(
        self,
        project_id: int,
        required_hours: float,
        start_date: str,
        end_date: str,
        preferred_resources: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Suggest optimal resource allocation for a project.

        Args:
            project_id: Project ID to allocate resources for
            required_hours: Total hours needed
            start_date: Start date for allocation (ISO format)
            end_date: End date for allocation (ISO format)
            preferred_resources: Optional list of preferred resource IDs

        Returns:
            Optimization suggestions

        Example:
            optimization = client.resource_allocation.optimize_resource_allocation(
                67890, 240.0, "2024-02-01", "2024-02-29"
            )
        """
        try:
            period_start = datetime.fromisoformat(start_date).date()
            period_end = datetime.fromisoformat(end_date).date()
            total_days = (period_end - period_start).days + 1
            business_days = sum(
                1
                for i in range(total_days)
                if (period_start + timedelta(days=i)).weekday() < 5
            )
        except (ValueError, TypeError):
            return {"error": "Invalid date format"}

        # Find available resources
        available_resources = self.find_available_resources(
            start_date, end_date, max_utilization=90.0
        )

        # Filter by preferred resources if specified
        if preferred_resources:
            available_resources = [
                r
                for r in available_resources
                if r["resource_id"] in preferred_resources
            ]

        # Calculate allocation scenarios
        scenarios = []

        # Scenario 1: Single resource (if possible)
        hours_per_day = required_hours / business_days if business_days > 0 else 0
        if hours_per_day <= 8.0:
            suitable_resources = [
                r for r in available_resources if r["remaining_hours"] >= required_hours
            ]

            if suitable_resources:
                scenarios.append(
                    {
                        "scenario": "single_resource",
                        "resources": [suitable_resources[0]["resource_id"]],
                        "allocation": [
                            {
                                "resource_id": suitable_resources[0]["resource_id"],
                                "hours_per_day": hours_per_day,
                                "total_hours": required_hours,
                            }
                        ],
                        "total_resources": 1,
                        "efficiency_score": 100
                        - suitable_resources[0]["current_utilization"],
                    }
                )

        # Scenario 2: Multiple resources
        if len(available_resources) >= 2:
            multi_allocation = []
            remaining_hours = required_hours

            for resource in available_resources:
                if remaining_hours <= 0:
                    break

                max_hours_for_resource = min(
                    resource["remaining_hours"], business_days * 8.0, remaining_hours
                )

                if max_hours_for_resource > 0:
                    hours_per_day_for_resource = max_hours_for_resource / business_days
                    multi_allocation.append(
                        {
                            "resource_id": resource["resource_id"],
                            "hours_per_day": round(hours_per_day_for_resource, 2),
                            "total_hours": max_hours_for_resource,
                        }
                    )
                    remaining_hours -= max_hours_for_resource

            if remaining_hours <= 0:
                avg_utilization = sum(
                    r["current_utilization"]
                    for r in available_resources[: len(multi_allocation)]
                ) / len(multi_allocation)
                scenarios.append(
                    {
                        "scenario": "multiple_resources",
                        "resources": [a["resource_id"] for a in multi_allocation],
                        "allocation": multi_allocation,
                        "total_resources": len(multi_allocation),
                        "efficiency_score": 100 - avg_utilization,
                    }
                )

        # Sort scenarios by efficiency score
        scenarios.sort(key=lambda x: x["efficiency_score"], reverse=True)

        return {
            "project_id": project_id,
            "requirements": {
                "total_hours": required_hours,
                "start_date": start_date,
                "end_date": end_date,
                "business_days": business_days,
            },
            "available_resources_count": len(available_resources),
            "scenarios": scenarios,
            "recommendation": scenarios[0] if scenarios else None,
        }
