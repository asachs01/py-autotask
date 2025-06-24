"""
ResourceRoles Entity for py-autotask

This module provides the ResourceRolesEntity class for managing resource roles
in Autotask. Resource roles define permissions and access levels for resources
within the system.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ResourceRolesEntity(BaseEntity):
    """
    Manages Autotask ResourceRoles - role definitions and permissions.

    Resource roles define permission sets and access levels for resources
    within Autotask. They control what actions resources can perform and
    what data they can access.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ResourceRoles"

    def create_resource_role(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        hourly_rate: Optional[Union[float, Decimal]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new resource role.

        Args:
            name: Name of the role
            description: Description of the role
            is_active: Whether the role is active
            hourly_rate: Default hourly rate for this role
            **kwargs: Additional fields for the role

        Returns:
            Create response with new role ID
        """
        role_data = {"name": name, "isActive": is_active, **kwargs}

        if description:
            role_data["description"] = description
        if hourly_rate is not None:
            role_data["hourlyRate"] = float(hourly_rate)

        return self.create(role_data)

    def get_active_roles(self) -> List[Dict[str, Any]]:
        """
        Get all active resource roles.

        Returns:
            List of active resource roles
        """
        return self.query(filter="isActive eq true")

    def get_roles_by_rate_range(
        self,
        min_rate: Optional[Union[float, Decimal]] = None,
        max_rate: Optional[Union[float, Decimal]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get roles within a rate range.

        Args:
            min_rate: Minimum hourly rate
            max_rate: Maximum hourly rate

        Returns:
            List of roles within the rate range
        """
        filters = []

        if min_rate is not None:
            filters.append(f"hourlyRate ge {float(min_rate)}")
        if max_rate is not None:
            filters.append(f"hourlyRate le {float(max_rate)}")

        if not filters:
            return []

        return self.query(filter=" and ".join(filters))

    def search_roles(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search roles by name or description.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching roles
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        filters = []
        for field in search_fields:
            filters.append(f"contains({field}, '{search_term}')")

        return self.query(filter=" or ".join(filters))

    def update_role_rate(
        self,
        role_id: int,
        new_hourly_rate: Union[float, Decimal],
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update role hourly rate.

        Args:
            role_id: ID of the role
            new_hourly_rate: New hourly rate
            effective_date: When the new rate becomes effective

        Returns:
            Update response
        """
        update_data = {"hourlyRate": float(new_hourly_rate)}

        if effective_date:
            update_data["effectiveDate"] = effective_date.isoformat()

        return self.update(role_id, update_data)

    def activate_role(self, role_id: int) -> Dict[str, Any]:
        """
        Activate a resource role.

        Args:
            role_id: ID of the role to activate

        Returns:
            Update response
        """
        return self.update(role_id, {"isActive": True})

    def deactivate_role(self, role_id: int) -> Dict[str, Any]:
        """
        Deactivate a resource role.

        Args:
            role_id: ID of the role to deactivate

        Returns:
            Update response
        """
        return self.update(role_id, {"isActive": False})

    def get_role_usage_summary(self, role_id: int) -> Dict[str, Any]:
        """
        Get usage summary for a role.

        Args:
            role_id: ID of the role

        Returns:
            Role usage summary
        """
        # This would typically query resources using this role
        # For now, return structure that could be populated

        return {
            "role_id": role_id,
            "usage_summary": {
                "total_resources": 0,  # Would query resources with this role
                "active_resources": 0,  # Would query active resources
                "recent_assignments": 0,  # Would count recent assignments
                "avg_utilization": 0.0,  # Would calculate utilization
            },
        }

    def get_roles_with_permissions(
        self, permission_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get roles with specific permissions.

        Args:
            permission_type: Type of permission to filter by

        Returns:
            List of roles with the specified permissions
        """
        # This would typically query role permissions
        # For now, return basic role data

        roles = self.get_active_roles()

        # Would enhance with permission data
        for role in roles:
            role["permissions"] = []  # Would populate with actual permissions

        return roles

    def bulk_update_rates(self, rate_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update rates for multiple roles.

        Args:
            rate_updates: List of rate updates
                Each should contain: role_id, hourly_rate

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in rate_updates:
            role_id = update["role_id"]
            hourly_rate = update["hourly_rate"]

            try:
                result = self.update_role_rate(role_id, hourly_rate)
                results.append({"id": role_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": role_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(rate_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def copy_role(
        self, source_role_id: int, new_name: str, new_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing role.

        Args:
            source_role_id: ID of the role to copy
            new_name: Name for the new role
            new_description: Description for the new role

        Returns:
            Create response for the new role
        """
        source_role = self.get(source_role_id)

        # Remove fields that shouldn't be copied
        copy_data = {
            k: v
            for k, v in source_role.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        copy_data["name"] = new_name
        if new_description:
            copy_data["description"] = new_description

        return self.create(copy_data)

    def get_role_hierarchy(self) -> Dict[str, Any]:
        """
        Get role hierarchy based on rates and permissions.

        Returns:
            Role hierarchy structure
        """
        roles = self.get_active_roles()

        # Sort by hourly rate (descending)
        sorted_roles = sorted(roles, key=lambda x: x.get("hourlyRate", 0), reverse=True)

        return {
            "roles": sorted_roles,
            "hierarchy_levels": {
                "executive": [r for r in sorted_roles if r.get("hourlyRate", 0) >= 200],
                "senior": [
                    r for r in sorted_roles if 100 <= r.get("hourlyRate", 0) < 200
                ],
                "mid": [r for r in sorted_roles if 50 <= r.get("hourlyRate", 0) < 100],
                "junior": [r for r in sorted_roles if r.get("hourlyRate", 0) < 50],
            },
        }

    def get_role_cost_analysis(
        self, date_from: date, date_to: date, role_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get cost analysis for roles over a date range.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            role_ids: Optional list of specific role IDs

        Returns:
            Cost analysis by role
        """
        # This would typically query time entries and calculate costs
        # For now, return structure that could be populated

        if role_ids:
            role_filter = " or ".join([f"id eq {role_id}" for role_id in role_ids])
            roles = self.query(filter=f"({role_filter})")
        else:
            roles = self.get_active_roles()

        cost_analysis = []
        total_cost = Decimal("0")

        for role in roles:
            role_cost = Decimal("0")  # Would calculate from time entries
            cost_analysis.append(
                {
                    "role_id": role.get("id"),
                    "role_name": role.get("name"),
                    "hourly_rate": Decimal(str(role.get("hourlyRate", 0))),
                    "total_hours": Decimal("0"),  # Would calculate from time entries
                    "total_cost": role_cost,
                }
            )
            total_cost += role_cost

        return {
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "summary": {
                "total_roles": len(cost_analysis),
                "total_cost": total_cost,
                "average_rate": (
                    sum(Decimal(str(r.get("hourlyRate", 0))) for r in roles)
                    / len(roles)
                    if roles
                    else Decimal("0")
                ),
            },
            "by_role": cost_analysis,
        }
