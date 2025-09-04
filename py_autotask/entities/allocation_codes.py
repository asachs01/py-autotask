"""
Allocation Codes entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class AllocationCodesEntity(BaseEntity):
    """
    Handles all Allocation Code-related operations for the Autotask API.

    Allocation codes are used for resource allocation and time categorization,
    enabling better tracking of how resources are utilized across projects and activities.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_allocation_code(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        department_id: Optional[int] = None,
        allocation_type: int = 1,  # 1 = Project, 2 = Internal, 3 = Training
        **kwargs,
    ) -> EntityDict:
        """
        Create a new allocation code.

        Args:
            name: Name of the allocation code
            description: Description of the allocation code
            is_active: Whether the allocation code is active
            department_id: Optional department ID
            allocation_type: Type of allocation (1=Project, 2=Internal, 3=Training)
            **kwargs: Additional allocation code fields

        Returns:
            Created allocation code data

        Example:
            code = client.allocation_codes.create_allocation_code(
                "Software Development",
                description="Time spent on software development activities",
                allocation_type=1
            )
        """
        allocation_data = {
            "Name": name,
            "IsActive": is_active,
            "AllocationType": allocation_type,
            **kwargs,
        }

        if description:
            allocation_data["Description"] = description
        if department_id:
            allocation_data["DepartmentID"] = department_id

        return self.create(allocation_data)

    def get_active_allocation_codes(
        self,
        allocation_type: Optional[int] = None,
        department_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all active allocation codes.

        Args:
            allocation_type: Optional type filter (1=Project, 2=Internal, 3=Training)
            department_id: Optional department filter
            limit: Maximum number of codes to return

        Returns:
            List of active allocation codes

        Example:
            codes = client.allocation_codes.get_active_allocation_codes()
        """
        filters = [{"field": "IsActive", "op": "eq", "value": True}]

        if allocation_type:
            filters.append(
                {"field": "AllocationType", "op": "eq", "value": allocation_type}
            )
        if department_id:
            filters.append(
                {"field": "DepartmentID", "op": "eq", "value": department_id}
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_allocation_codes_by_type(
        self,
        allocation_type: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get allocation codes by type.

        Args:
            allocation_type: Type of allocation (1=Project, 2=Internal, 3=Training)
            active_only: Whether to return only active codes
            limit: Maximum number of codes to return

        Returns:
            List of allocation codes of specified type

        Example:
            project_codes = client.allocation_codes.get_allocation_codes_by_type(1)
        """
        filters = [{"field": "AllocationType", "op": "eq", "value": allocation_type}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_allocation_code_usage(self, code_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for an allocation code.

        Args:
            code_id: ID of the allocation code

        Returns:
            Usage statistics for the allocation code

        Example:
            usage = client.allocation_codes.get_allocation_code_usage(12345)
        """
        # Get time entries using this allocation code
        time_filters = [{"field": "AllocationCodeID", "op": "eq", "value": code_id}]
        time_response = self.client.query("TimeEntries", time_filters)
        time_entries = (
            time_response.items if hasattr(time_response, "items") else time_response
        )

        # Calculate usage statistics
        total_hours = sum(float(entry.get("HoursWorked", 0)) for entry in time_entries)
        billable_hours = sum(
            float(entry.get("HoursToBill", 0))
            for entry in time_entries
            if entry.get("BillableToAccount")
        )
        unique_resources = len(
            set(
                entry.get("ResourceID")
                for entry in time_entries
                if entry.get("ResourceID")
            )
        )
        unique_projects = len(
            set(
                entry.get("ProjectID")
                for entry in time_entries
                if entry.get("ProjectID")
            )
        )

        # Get date range
        dates = [
            entry.get("DateWorked") for entry in time_entries if entry.get("DateWorked")
        ]
        first_used = min(dates) if dates else None
        last_used = max(dates) if dates else None

        return {
            "allocation_code_id": code_id,
            "total_entries": len(time_entries),
            "total_hours": round(total_hours, 2),
            "billable_hours": round(billable_hours, 2),
            "non_billable_hours": round(total_hours - billable_hours, 2),
            "unique_resources": unique_resources,
            "unique_projects": unique_projects,
            "first_used": first_used,
            "last_used": last_used,
            "utilization_percentage": round(
                (billable_hours / total_hours * 100) if total_hours > 0 else 0, 2
            ),
        }

    def activate_allocation_code(self, code_id: int) -> EntityDict:
        """
        Activate an allocation code.

        Args:
            code_id: ID of allocation code to activate

        Returns:
            Updated allocation code data

        Example:
            activated = client.allocation_codes.activate_allocation_code(12345)
        """
        return self.update_by_id(code_id, {"IsActive": True})

    def deactivate_allocation_code(self, code_id: int) -> EntityDict:
        """
        Deactivate an allocation code.

        Args:
            code_id: ID of allocation code to deactivate

        Returns:
            Updated allocation code data

        Example:
            deactivated = client.allocation_codes.deactivate_allocation_code(12345)
        """
        return self.update_by_id(code_id, {"IsActive": False})

    def get_allocation_codes_by_department(
        self, department_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get allocation codes for a specific department.

        Args:
            department_id: Department ID to filter by
            active_only: Whether to return only active codes
            limit: Maximum number of codes to return

        Returns:
            List of department allocation codes

        Example:
            dept_codes = client.allocation_codes.get_allocation_codes_by_department(12345)
        """
        filters = [{"field": "DepartmentID", "op": "eq", "value": department_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def search_allocation_codes(
        self, name_pattern: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search allocation codes by name pattern.

        Args:
            name_pattern: Pattern to search for in allocation code names
            active_only: Whether to return only active codes
            limit: Maximum number of codes to return

        Returns:
            List of matching allocation codes

        Example:
            codes = client.allocation_codes.search_allocation_codes("development")
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def clone_allocation_code(
        self, code_id: int, new_name: str, new_description: Optional[str] = None
    ) -> EntityDict:
        """
        Clone an allocation code with a new name.

        Args:
            code_id: ID of allocation code to clone
            new_name: Name for the cloned allocation code
            new_description: Optional new description

        Returns:
            Created cloned allocation code data

        Example:
            cloned = client.allocation_codes.clone_allocation_code(
                12345, "Development - Frontend", "Frontend development tasks"
            )
        """
        original = self.get(code_id)
        if not original:
            raise ValueError(f"Allocation code {code_id} not found")

        clone_data = {
            "Name": new_name,
            "Description": new_description or original.get("Description"),
            "AllocationType": original.get("AllocationType"),
            "DepartmentID": original.get("DepartmentID"),
            "IsActive": True,
        }

        return self.create(clone_data)

    def get_allocation_code_summary(self, code_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of an allocation code.

        Args:
            code_id: ID of the allocation code

        Returns:
            Allocation code summary with usage metrics

        Example:
            summary = client.allocation_codes.get_allocation_code_summary(12345)
        """
        code = self.get(code_id)
        if not code:
            return {}

        usage_stats = self.get_allocation_code_usage(code_id)

        return {
            "allocation_code_id": code_id,
            "name": code.get("Name"),
            "description": code.get("Description"),
            "allocation_type": code.get("AllocationType"),
            "department_id": code.get("DepartmentID"),
            "is_active": code.get("IsActive"),
            "created_date": code.get("CreateDate"),
            "last_modified_date": code.get("LastModifiedDate"),
            "usage_statistics": usage_stats,
        }

    def bulk_activate_codes(
        self, code_ids: List[int], batch_size: int = 50
    ) -> List[EntityDict]:
        """
        Activate multiple allocation codes in batches.

        Args:
            code_ids: List of allocation code IDs to activate
            batch_size: Number of codes to process per batch

        Returns:
            List of updated allocation code data

        Example:
            activated = client.allocation_codes.bulk_activate_codes([12345, 12346, 12347])
        """
        results = []

        for i in range(0, len(code_ids), batch_size):
            batch = code_ids[i : i + batch_size]

            for code_id in batch:
                try:
                    result = self.activate_allocation_code(code_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to activate allocation code {code_id}: {e}"
                    )
                    continue

        return results

    def bulk_deactivate_codes(
        self, code_ids: List[int], batch_size: int = 50
    ) -> List[EntityDict]:
        """
        Deactivate multiple allocation codes in batches.

        Args:
            code_ids: List of allocation code IDs to deactivate
            batch_size: Number of codes to process per batch

        Returns:
            List of updated allocation code data

        Example:
            deactivated = client.allocation_codes.bulk_deactivate_codes([12345, 12346, 12347])
        """
        results = []

        for i in range(0, len(code_ids), batch_size):
            batch = code_ids[i : i + batch_size]

            for code_id in batch:
                try:
                    result = self.deactivate_allocation_code(code_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to deactivate allocation code {code_id}: {e}"
                    )
                    continue

        return results

    def get_unused_allocation_codes(
        self, days_threshold: int = 90, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get allocation codes that haven't been used in specified days.

        Args:
            days_threshold: Number of days to look back for usage
            limit: Maximum number of codes to return

        Returns:
            List of unused allocation codes

        Example:
            unused = client.allocation_codes.get_unused_allocation_codes(180)
        """
        threshold_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()

        # Get all active allocation codes
        all_codes = self.get_active_allocation_codes()
        unused_codes = []

        for code in all_codes:
            code_id = code.get("id")
            if not code_id:
                continue

            # Check for recent time entries
            time_filters = [
                {"field": "AllocationCodeID", "op": "eq", "value": code_id},
                {"field": "DateWorked", "op": "gte", "value": threshold_date},
            ]

            try:
                time_response = self.client.query("TimeEntries", time_filters)
                time_entries = (
                    time_response.items
                    if hasattr(time_response, "items")
                    else time_response
                )

                if not time_entries:
                    unused_codes.append(code)

                if limit and len(unused_codes) >= limit:
                    break

            except Exception as e:
                self.logger.error(
                    f"Error checking usage for allocation code {code_id}: {e}"
                )
                continue

        return unused_codes

    def get_allocation_type_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of allocation codes by type.

        Returns:
            Distribution statistics by allocation type

        Example:
            distribution = client.allocation_codes.get_allocation_type_distribution()
        """
        all_codes = self.query_all()

        type_counts = {}
        active_type_counts = {}

        type_names = {1: "Project", 2: "Internal", 3: "Training"}

        for code in all_codes:
            allocation_type = code.get("AllocationType", 0)
            type_name = type_names.get(allocation_type, f"Type_{allocation_type}")

            type_counts[type_name] = type_counts.get(type_name, 0) + 1

            if code.get("IsActive"):
                active_type_counts[type_name] = active_type_counts.get(type_name, 0) + 1

        return {
            "total_codes": len(all_codes),
            "active_codes": sum(active_type_counts.values()),
            "type_distribution": type_counts,
            "active_type_distribution": active_type_counts,
            "type_percentages": (
                {
                    type_name: round(count / len(all_codes) * 100, 2)
                    for type_name, count in type_counts.items()
                }
                if all_codes
                else {}
            ),
        }

    def validate_allocation_code_usage(self, code_id: int) -> Dict[str, Any]:
        """
        Validate allocation code usage and identify potential issues.

        Args:
            code_id: ID of the allocation code to validate

        Returns:
            Validation results with warnings and recommendations

        Example:
            validation = client.allocation_codes.validate_allocation_code_usage(12345)
        """
        code = self.get(code_id)
        if not code:
            return {"error": f"Allocation code {code_id} not found"}

        usage_stats = self.get_allocation_code_usage(code_id)
        warnings = []
        recommendations = []

        # Check for inactivity
        if usage_stats["total_entries"] == 0:
            warnings.append("No time entries found for this allocation code")
            recommendations.append("Consider deactivating if not needed")
        elif usage_stats["last_used"]:
            try:
                last_used_date = datetime.fromisoformat(usage_stats["last_used"])
                days_since_use = (datetime.now() - last_used_date).days

                if days_since_use > 90:
                    warnings.append(f"No usage in {days_since_use} days")
                    recommendations.append("Review if allocation code is still needed")
            except (ValueError, TypeError):
                pass

        # Check utilization
        if (
            usage_stats["utilization_percentage"] < 50
            and usage_stats["total_hours"] > 0
        ):
            warnings.append(
                f'Low billable utilization: {usage_stats["utilization_percentage"]}%'
            )
            recommendations.append("Review time categorization practices")

        # Check if active but unused
        if code.get("IsActive") and usage_stats["total_entries"] == 0:
            warnings.append("Active allocation code with no usage")
            recommendations.append("Consider deactivating to reduce clutter")

        return {
            "allocation_code_id": code_id,
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": recommendations,
            "usage_summary": usage_stats,
        }
