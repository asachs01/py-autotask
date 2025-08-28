"""
ResourceServiceDeskRoles entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ResourceServiceDeskRolesEntity(BaseEntity):
    """
    Handles all Resource Service Desk Role-related operations for the Autotask API.

    ResourceServiceDeskRoles in Autotask represent the specific service desk roles
    assigned to resources, defining their capabilities and permissions within the
    service desk environment, including ticket management, escalation rights,
    and specialized service desk functions.
    """

    def __init__(self, client, entity_name="ResourceServiceDeskRoles"):
        super().__init__(client, entity_name)

    def get_resource_service_desk_roles(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all service desk roles for a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of records to return

        Returns:
            List of service desk role assignments for the resource

        Example:
            roles = client.resource_service_desk_roles.get_resource_service_desk_roles(123)
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]
        return self.query(filters=filters, max_records=limit)

    def get_resources_by_service_desk_role(
        self,
        service_desk_role_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all resources assigned to a specific service desk role.

        Args:
            service_desk_role_id: ID of the service desk role
            active_only: Whether to return only active assignments
            limit: Maximum number of records to return

        Returns:
            List of resource assignments for the service desk role
        """
        filters = [
            QueryFilter(field="ServiceDeskRoleID", op="eq", value=service_desk_role_id)
        ]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_active_service_desk_assignments(
        self,
        resource_id: Optional[int] = None,
        service_desk_role_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all active service desk role assignments.

        Args:
            resource_id: Optional resource ID to filter by
            service_desk_role_id: Optional service desk role ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of active service desk assignments
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        if service_desk_role_id:
            filters.append(
                QueryFilter(
                    field="ServiceDeskRoleID", op="eq", value=service_desk_role_id
                )
            )

        return self.query(filters=filters, max_records=limit)

    def create_service_desk_role_assignment(
        self,
        resource_id: int,
        service_desk_role_id: int,
        is_primary: bool = False,
        active: bool = True,
        effective_date: Optional[str] = None,
        expiration_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new resource service desk role assignment.

        Args:
            resource_id: ID of the resource
            service_desk_role_id: ID of the service desk role
            is_primary: Whether this is the primary service desk role for the resource
            active: Whether the assignment is active
            effective_date: Optional effective date (YYYY-MM-DD)
            expiration_date: Optional expiration date (YYYY-MM-DD)

        Returns:
            Created assignment record

        Example:
            assignment = client.resource_service_desk_roles.create_service_desk_role_assignment(
                resource_id=123,
                service_desk_role_id=456,
                is_primary=True
            )
        """
        data = {
            "ResourceID": resource_id,
            "ServiceDeskRoleID": service_desk_role_id,
            "IsPrimary": is_primary,
            "Active": active,
        }

        if effective_date:
            data["EffectiveDate"] = effective_date

        if expiration_date:
            data["ExpirationDate"] = expiration_date

        return self.create(data)

    def get_primary_service_desk_roles(
        self, resource_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get primary service desk role assignments.

        Args:
            resource_id: Optional resource ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of primary service desk assignments
        """
        filters = [
            QueryFilter(field="IsPrimary", op="eq", value=True),
            QueryFilter(field="Active", op="eq", value=True),
        ]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def get_expiring_role_assignments(
        self, days_ahead: int = 30, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get service desk role assignments expiring within specified period.

        Args:
            days_ahead: Number of days ahead to check for expirations
            limit: Maximum number of records to return

        Returns:
            List of expiring assignments
        """
        from datetime import datetime, timedelta

        expiry_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        filters = [
            QueryFilter(field="ExpirationDate", op="isNotNull", value=None),
            QueryFilter(field="ExpirationDate", op="lte", value=expiry_date),
            QueryFilter(field="Active", op="eq", value=True),
        ]

        return self.query(filters=filters, max_records=limit)

    def bulk_assign_service_desk_role(
        self,
        resource_ids: List[int],
        service_desk_role_id: int,
        is_primary: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Assign multiple resources to a service desk role.

        Args:
            resource_ids: List of resource IDs to assign
            service_desk_role_id: ID of the service desk role
            is_primary: Whether this should be the primary role

        Returns:
            List of created assignment records
        """
        created_records = []

        for resource_id in resource_ids:
            try:
                assignment = self.create_service_desk_role_assignment(
                    resource_id=resource_id,
                    service_desk_role_id=service_desk_role_id,
                    is_primary=is_primary,
                )
                created_records.append(assignment)
            except Exception as e:
                self.logger.warning(
                    f"Failed to create service desk role assignment for resource {resource_id}: {e}"
                )

        return created_records

    def promote_to_primary_role(
        self, resource_id: int, new_primary_role_id: int
    ) -> Dict[str, Any]:
        """
        Promote a resource's service desk role to primary, demoting others.

        Args:
            resource_id: ID of the resource
            new_primary_role_id: ID of the role to promote to primary

        Returns:
            Result of the promotion operation
        """
        # Get current assignments for the resource
        current_assignments = self.get_resource_service_desk_roles(resource_id)

        # Find the assignment to promote
        target_assignment = None
        for assignment in current_assignments:
            if assignment.get("ServiceDeskRoleID") == new_primary_role_id:
                target_assignment = assignment
                break

        if not target_assignment:
            raise ValueError(
                f"Resource {resource_id} not assigned to service desk role {new_primary_role_id}"
            )

        # Demote all current primary roles
        demoted_count = 0
        for assignment in current_assignments:
            if assignment.get("IsPrimary") and assignment.get(
                "id"
            ) != target_assignment.get("id"):
                self.update(assignment["id"], {"IsPrimary": False})
                demoted_count += 1

        # Promote target assignment to primary
        updated_assignment = self.update(target_assignment["id"], {"IsPrimary": True})

        return {
            "promoted_assignment": updated_assignment,
            "demoted_assignments": demoted_count,
            "resource_id": resource_id,
            "new_primary_role": new_primary_role_id,
        }

    def get_service_desk_coverage_report(
        self, service_desk_role_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Generate a coverage report for service desk roles.

        Args:
            service_desk_role_ids: Optional list of role IDs to include

        Returns:
            Dictionary with coverage analysis
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]

        if service_desk_role_ids:
            filters.append(
                QueryFilter(
                    field="ServiceDeskRoleID", op="in", value=service_desk_role_ids
                )
            )

        assignments = self.query(filters=filters)

        if not assignments:
            return {
                "total_assignments": 0,
                "by_role": {},
                "primary_assignments": 0,
                "coverage_gaps": [],
                "recommendations": [],
            }

        by_role = {}
        primary_count = 0

        for assignment in assignments:
            role_id = assignment.get("ServiceDeskRoleID")
            is_primary = assignment.get("IsPrimary", False)

            if role_id not in by_role:
                by_role[role_id] = {"total": 0, "primary": 0}

            by_role[role_id]["total"] += 1

            if is_primary:
                by_role[role_id]["primary"] += 1
                primary_count += 1

        # Identify coverage gaps
        coverage_gaps = []
        for role_id, stats in by_role.items():
            if stats["total"] < 2:
                coverage_gaps.append(
                    f"Role {role_id} has insufficient coverage ({stats['total']} resource)"
                )
            if stats["primary"] == 0:
                coverage_gaps.append(f"Role {role_id} has no primary resource assigned")

        recommendations = self._generate_coverage_recommendations(
            by_role, coverage_gaps
        )

        return {
            "total_assignments": len(assignments),
            "by_role": by_role,
            "primary_assignments": primary_count,
            "coverage_gaps": coverage_gaps,
            "recommendations": recommendations,
        }

    def _generate_coverage_recommendations(
        self, by_role: Dict[int, Dict[str, int]], coverage_gaps: List[str]
    ) -> List[str]:
        """Generate recommendations for service desk coverage optimization."""
        recommendations = []

        if coverage_gaps:
            recommendations.append(
                "Address identified coverage gaps by assigning additional resources"
            )

        # Check for over-assignment
        over_assigned_roles = [
            role_id for role_id, stats in by_role.items() if stats["total"] > 10
        ]

        if over_assigned_roles:
            recommendations.append(
                "Consider redistributing resources from over-assigned roles"
            )

        # Check for roles without primary assignments
        no_primary_roles = [
            role_id for role_id, stats in by_role.items() if stats["primary"] == 0
        ]

        if no_primary_roles:
            recommendations.append(
                "Assign primary resources to roles without primary coverage"
            )

        return recommendations

    def transfer_service_desk_responsibilities(
        self,
        from_resource_id: int,
        to_resource_id: int,
        preserve_primary_status: bool = True,
    ) -> Dict[str, Any]:
        """
        Transfer service desk role assignments from one resource to another.

        Args:
            from_resource_id: Source resource ID
            to_resource_id: Target resource ID
            preserve_primary_status: Whether to preserve primary role status

        Returns:
            Result of the transfer operation
        """
        # Get source resource assignments
        source_assignments = self.get_resource_service_desk_roles(from_resource_id)

        if not source_assignments:
            raise ValueError(
                f"No service desk roles found for resource {from_resource_id}"
            )

        # Create new assignments for target resource
        transferred_roles = []
        for assignment in source_assignments:
            if assignment.get("Active"):
                try:
                    new_assignment = self.create_service_desk_role_assignment(
                        resource_id=to_resource_id,
                        service_desk_role_id=assignment.get("ServiceDeskRoleID"),
                        is_primary=(
                            assignment.get("IsPrimary", False)
                            if preserve_primary_status
                            else False
                        ),
                        effective_date=assignment.get("EffectiveDate"),
                        expiration_date=assignment.get("ExpirationDate"),
                    )
                    transferred_roles.append(new_assignment)

                    # Deactivate source assignment
                    self.update(assignment["id"], {"Active": False})

                except Exception as e:
                    self.logger.warning(
                        f"Failed to transfer role {assignment.get('ServiceDeskRoleID')}: {e}"
                    )

        return {
            "from_resource": from_resource_id,
            "to_resource": to_resource_id,
            "transferred_roles": len(transferred_roles),
            "preserve_primary": preserve_primary_status,
            "new_assignments": transferred_roles,
        }
