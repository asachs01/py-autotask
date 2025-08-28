"""
ResourceRoleDepartments entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ResourceRoleDepartmentsEntity(BaseEntity):
    """
    Handles all Resource Role Department-related operations for the Autotask API.

    ResourceRoleDepartments in Autotask represent the association between resources,
    roles, and departments, defining what roles a resource can perform within
    specific departments of the organization.
    """

    def __init__(self, client, entity_name="ResourceRoleDepartments"):
        super().__init__(client, entity_name)

    def get_resource_department_roles(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all department roles for a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of records to return

        Returns:
            List of resource department role assignments

        Example:
            roles = client.resource_role_departments.get_resource_department_roles(123)
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]
        return self.query(filters=filters, max_records=limit)

    def get_department_resources(
        self,
        department_id: int,
        role_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all resources assigned to a specific department, optionally filtered by role.

        Args:
            department_id: ID of the department
            role_id: Optional role ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of resource assignments for the department
        """
        filters = [QueryFilter(field="DepartmentID", op="eq", value=department_id)]

        if role_id:
            filters.append(QueryFilter(field="RoleID", op="eq", value=role_id))

        return self.query(filters=filters, max_records=limit)

    def get_role_assignments(
        self,
        role_id: int,
        department_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all resources assigned to a specific role, optionally filtered by department.

        Args:
            role_id: ID of the role
            department_id: Optional department ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of resource role assignments
        """
        filters = [QueryFilter(field="RoleID", op="eq", value=role_id)]

        if department_id:
            filters.append(
                QueryFilter(field="DepartmentID", op="eq", value=department_id)
            )

        return self.query(filters=filters, max_records=limit)

    def get_active_assignments(
        self,
        department_id: Optional[int] = None,
        role_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all active resource role department assignments.

        Args:
            department_id: Optional department ID to filter by
            role_id: Optional role ID to filter by
            resource_id: Optional resource ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of active assignments
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]

        if department_id:
            filters.append(
                QueryFilter(field="DepartmentID", op="eq", value=department_id)
            )

        if role_id:
            filters.append(QueryFilter(field="RoleID", op="eq", value=role_id))

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def create_role_assignment(
        self,
        resource_id: int,
        department_id: int,
        role_id: int,
        is_default: bool = False,
        active: bool = True,
        effective_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new resource role department assignment.

        Args:
            resource_id: ID of the resource
            department_id: ID of the department
            role_id: ID of the role
            is_default: Whether this is the default role for the resource in this department
            active: Whether the assignment is active
            effective_date: Optional effective date (YYYY-MM-DD)

        Returns:
            Created assignment record

        Example:
            assignment = client.resource_role_departments.create_role_assignment(
                resource_id=123,
                department_id=456,
                role_id=789,
                is_default=True
            )
        """
        data = {
            "ResourceID": resource_id,
            "DepartmentID": department_id,
            "RoleID": role_id,
            "IsDefault": is_default,
            "Active": active,
        }

        if effective_date:
            data["EffectiveDate"] = effective_date

        return self.create(data)

    def get_default_assignments(
        self,
        resource_id: Optional[int] = None,
        department_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get default role assignments for resources in departments.

        Args:
            resource_id: Optional resource ID to filter by
            department_id: Optional department ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of default assignments
        """
        filters = [QueryFilter(field="IsDefault", op="eq", value=True)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        if department_id:
            filters.append(
                QueryFilter(field="DepartmentID", op="eq", value=department_id)
            )

        return self.query(filters=filters, max_records=limit)

    def bulk_assign_role_to_department(
        self,
        resource_ids: List[int],
        department_id: int,
        role_id: int,
        is_default: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Assign multiple resources to a role within a department.

        Args:
            resource_ids: List of resource IDs
            department_id: ID of the department
            role_id: ID of the role
            is_default: Whether this should be the default role

        Returns:
            List of created assignment records
        """
        created_records = []

        for resource_id in resource_ids:
            try:
                assignment = self.create_role_assignment(
                    resource_id=resource_id,
                    department_id=department_id,
                    role_id=role_id,
                    is_default=is_default,
                )
                created_records.append(assignment)
            except Exception as e:
                self.logger.warning(
                    f"Failed to create assignment for resource {resource_id}: {e}"
                )

        return created_records

    def transfer_resource_between_departments(
        self,
        resource_id: int,
        from_department_id: int,
        to_department_id: int,
        new_role_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Transfer a resource from one department to another.

        Args:
            resource_id: ID of the resource to transfer
            from_department_id: Current department ID
            to_department_id: Target department ID
            new_role_id: Optional new role ID (keeps current role if not specified)

        Returns:
            Result of the transfer operation
        """
        # Get current assignments in the old department
        current_assignments = self.get_resource_department_roles(resource_id)
        old_assignments = [
            a
            for a in current_assignments
            if a.get("DepartmentID") == from_department_id
        ]

        if not old_assignments:
            raise ValueError(
                f"Resource {resource_id} not found in department {from_department_id}"
            )

        # Deactivate old assignments
        for assignment in old_assignments:
            self.update(assignment["id"], {"Active": False})

        # Create new assignment in target department
        role_id = new_role_id or old_assignments[0].get("RoleID")
        is_default = any(a.get("IsDefault", False) for a in old_assignments)

        new_assignment = self.create_role_assignment(
            resource_id=resource_id,
            department_id=to_department_id,
            role_id=role_id,
            is_default=is_default,
        )

        return {
            "transferred_resource": resource_id,
            "from_department": from_department_id,
            "to_department": to_department_id,
            "new_assignment": new_assignment,
            "deactivated_assignments": len(old_assignments),
        }

    def get_department_role_matrix(
        self, department_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get a matrix view of resources, roles, and departments.

        Args:
            department_ids: Optional list of department IDs to include

        Returns:
            Dictionary with matrix information
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]

        if department_ids:
            filters.append(
                QueryFilter(field="DepartmentID", op="in", value=department_ids)
            )

        assignments = self.query(filters=filters)

        matrix = {}
        department_totals = {}
        role_totals = {}

        for assignment in assignments:
            dept_id = assignment.get("DepartmentID")
            role_id = assignment.get("RoleID")
            resource_id = assignment.get("ResourceID")

            # Initialize nested structure
            if dept_id not in matrix:
                matrix[dept_id] = {}
                department_totals[dept_id] = 0

            if role_id not in matrix[dept_id]:
                matrix[dept_id][role_id] = []

            matrix[dept_id][role_id].append(resource_id)

            # Update totals
            department_totals[dept_id] += 1
            role_totals[role_id] = role_totals.get(role_id, 0) + 1

        return {
            "matrix": matrix,
            "department_totals": department_totals,
            "role_totals": role_totals,
            "total_assignments": len(assignments),
        }

    def validate_role_department_compatibility(
        self, role_id: int, department_id: int
    ) -> Dict[str, Any]:
        """
        Validate if a role can be assigned within a specific department.

        Args:
            role_id: ID of the role to validate
            department_id: ID of the department

        Returns:
            Dictionary with validation results
        """
        # Check existing assignments
        existing = self.get_role_assignments(role_id, department_id)

        # Get all assignments for this role in other departments
        all_role_assignments = self.get_role_assignments(role_id)
        other_depts = set(
            a.get("DepartmentID")
            for a in all_role_assignments
            if a.get("DepartmentID") != department_id
        )

        return {
            "is_valid": True,  # Basic validation - could be enhanced with business rules
            "existing_assignments": len(existing),
            "role_used_in_other_departments": list(other_depts),
            "can_assign": True,
            "warnings": [],
            "recommendations": [
                "Verify role permissions are appropriate for department",
                "Consider department-specific training requirements",
            ],
        }
