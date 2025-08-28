"""
Roles entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class RolesEntity(BaseEntity):
    """
    Handles Role operations for the Autotask API.

    Manages user roles, permissions, and access control
    within the Autotask system.
    """

    def __init__(self, client, entity_name: str = "Roles"):
        super().__init__(client, entity_name)

    def create_role(
        self,
        name: str,
        description: str,
        is_active: bool = True,
        is_system_role: bool = False,
        permissions: Optional[List[str]] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new role.

        Args:
            name: Role name
            description: Role description
            is_active: Whether the role is active
            is_system_role: Whether this is a system-defined role
            permissions: Optional list of permissions
            **kwargs: Additional role fields

        Returns:
            Created role data
        """
        role_data = {
            "Name": name,
            "Description": description,
            "IsActive": is_active,
            "IsSystemRole": is_system_role,
            **kwargs,
        }

        if permissions:
            role_data["Permissions"] = permissions

        return self.create(role_data)

    def get_active_roles(self) -> EntityList:
        """
        Get all active roles.

        Returns:
            List of active roles
        """
        filters = [{"field": "IsActive", "op": "eq", "value": "true"}]
        return self.query_all(filters=filters)

    def get_custom_roles(self) -> EntityList:
        """
        Get all custom (non-system) roles.

        Returns:
            List of custom roles
        """
        filters = [{"field": "IsSystemRole", "op": "eq", "value": "false"}]
        return self.query_all(filters=filters)

    def get_system_roles(self) -> EntityList:
        """
        Get all system-defined roles.

        Returns:
            List of system roles
        """
        filters = [{"field": "IsSystemRole", "op": "eq", "value": "true"}]
        return self.query_all(filters=filters)

    def search_roles_by_name(self, name_pattern: str) -> EntityList:
        """
        Search roles by name pattern.

        Args:
            name_pattern: Name pattern to search for

        Returns:
            List of matching roles
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]
        return self.query_all(filters=filters)

    def get_role_by_name(self, role_name: str) -> Optional[EntityDict]:
        """
        Get a role by its exact name.

        Args:
            role_name: Role name

        Returns:
            Role data or None if not found
        """
        filters = [{"field": "Name", "op": "eq", "value": role_name}]
        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def get_roles_with_permission(self, permission: str) -> EntityList:
        """
        Get roles that have a specific permission.

        Args:
            permission: Permission to search for

        Returns:
            List of roles with the permission
        """
        # This would depend on how permissions are stored
        # For now, search in description or a permissions field
        filters = [{"field": "Permissions", "op": "contains", "value": permission}]
        return self.query_all(filters=filters)

    def activate_role(self, role_id: int) -> Optional[EntityDict]:
        """
        Activate a role.

        Args:
            role_id: Role ID to activate

        Returns:
            Updated role data
        """
        return self.update_by_id(role_id, {"IsActive": True})

    def deactivate_role(self, role_id: int) -> Optional[EntityDict]:
        """
        Deactivate a role.

        Args:
            role_id: Role ID to deactivate

        Returns:
            Updated role data
        """
        return self.update_by_id(role_id, {"IsActive": False})

    def update_role_permissions(
        self, role_id: int, permissions: List[str]
    ) -> Optional[EntityDict]:
        """
        Update permissions for a role.

        Args:
            role_id: Role ID to update
            permissions: New list of permissions

        Returns:
            Updated role data
        """
        return self.update_by_id(role_id, {"Permissions": permissions})

    def add_permission_to_role(
        self, role_id: int, permission: str
    ) -> Optional[EntityDict]:
        """
        Add a permission to a role.

        Args:
            role_id: Role ID
            permission: Permission to add

        Returns:
            Updated role data
        """
        role = self.get(role_id)
        if not role:
            return None

        current_permissions = role.get("Permissions", [])
        if isinstance(current_permissions, str):
            # Handle case where permissions are stored as string
            current_permissions = current_permissions.split(",")

        if permission not in current_permissions:
            current_permissions.append(permission)
            return self.update_role_permissions(role_id, current_permissions)

        return role  # Permission already exists

    def remove_permission_from_role(
        self, role_id: int, permission: str
    ) -> Optional[EntityDict]:
        """
        Remove a permission from a role.

        Args:
            role_id: Role ID
            permission: Permission to remove

        Returns:
            Updated role data
        """
        role = self.get(role_id)
        if not role:
            return None

        current_permissions = role.get("Permissions", [])
        if isinstance(current_permissions, str):
            current_permissions = current_permissions.split(",")

        if permission in current_permissions:
            current_permissions.remove(permission)
            return self.update_role_permissions(role_id, current_permissions)

        return role  # Permission didn't exist

    def get_users_with_role(self, role_id: int) -> EntityList:
        """
        Get users that have a specific role.

        Note: This would typically query a user-role relationship table.

        Args:
            role_id: Role ID

        Returns:
            List of users with the role
        """
        try:
            # This would query user-role associations
            filters = [{"field": "RoleID", "op": "eq", "value": str(role_id)}]
            return self.client.query("UserRoles", {"filter": filters}).items
        except Exception as e:
            self.logger.warning(f"Could not fetch users for role: {e}")
            return []

    def assign_role_to_user(self, role_id: int, user_id: int) -> Dict[str, Any]:
        """
        Assign a role to a user.

        Args:
            role_id: Role ID
            user_id: User ID

        Returns:
            Assignment result dictionary
        """
        result = {
            "success": False,
            "role_id": role_id,
            "user_id": user_id,
            "error": None,
        }

        try:
            # Check if role exists and is active
            role = self.get(role_id)
            if not role:
                result["error"] = "Role not found"
                return result

            if not role.get("IsActive", True):
                result["error"] = "Role is not active"
                return result

            # Create user-role association
            assignment_data = {
                "RoleID": role_id,
                "UserID": user_id,
            }

            # This would typically use a UserRoles entity
            assignment = self.client.create_entity("UserRoles", assignment_data)
            if assignment:
                result["success"] = True
                result["assignment"] = assignment
            else:
                result["error"] = "Failed to create role assignment"

        except Exception as e:
            result["error"] = f"Assignment error: {str(e)}"

        return result

    def remove_role_from_user(self, role_id: int, user_id: int) -> Dict[str, Any]:
        """
        Remove a role from a user.

        Args:
            role_id: Role ID
            user_id: User ID

        Returns:
            Removal result dictionary
        """
        result = {
            "success": False,
            "role_id": role_id,
            "user_id": user_id,
            "error": None,
        }

        try:
            # Find the user-role association
            filters = [
                {"field": "RoleID", "op": "eq", "value": str(role_id)},
                {"field": "UserID", "op": "eq", "value": str(user_id)},
            ]

            assignments = self.client.query("UserRoles", {"filter": filters}).items
            if assignments:
                assignment_id = assignments[0]["id"]
                if self.client.delete("UserRoles", int(assignment_id)):
                    result["success"] = True
                else:
                    result["error"] = "Failed to delete role assignment"
            else:
                result["error"] = "Role assignment not found"

        except Exception as e:
            result["error"] = f"Removal error: {str(e)}"

        return result

    def get_role_hierarchy(self) -> Dict[str, Any]:
        """
        Get the role hierarchy structure.

        Returns:
            Dictionary representing role hierarchy
        """
        all_roles = self.query_all()

        hierarchy = {
            "system_roles": [],
            "custom_roles": [],
            "inactive_roles": [],
            "role_levels": {},
        }

        for role in all_roles:
            if not role.get("IsActive", True):
                hierarchy["inactive_roles"].append(role)
            elif role.get("IsSystemRole", False):
                hierarchy["system_roles"].append(role)
            else:
                hierarchy["custom_roles"].append(role)

            # Group by level if available
            level = role.get("Level", "Unknown")
            if level not in hierarchy["role_levels"]:
                hierarchy["role_levels"][level] = []
            hierarchy["role_levels"][level].append(role)

        return hierarchy

    def get_role_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about roles in the system.

        Returns:
            Dictionary with role statistics
        """
        all_roles = self.query_all()
        active_roles = self.get_active_roles()

        stats = {
            "total_roles": len(all_roles),
            "active_roles": len(active_roles),
            "inactive_roles": len(all_roles) - len(active_roles),
            "system_roles": 0,
            "custom_roles": 0,
            "roles_with_users": 0,
            "orphaned_roles": 0,  # Roles with no users
        }

        for role in all_roles:
            if role.get("IsSystemRole", False):
                stats["system_roles"] += 1
            else:
                stats["custom_roles"] += 1

            # Check if role has users (this would require additional queries)
            role_id = int(role["id"])
            users_with_role = self.get_users_with_role(role_id)
            if users_with_role:
                stats["roles_with_users"] += 1
            else:
                stats["orphaned_roles"] += 1

        return stats

    def validate_role_permissions(
        self, role_id: int, required_permissions: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that a role has required permissions.

        Args:
            role_id: Role ID to validate
            required_permissions: List of required permissions

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "role_id": role_id,
            "has_permissions": [],
            "missing_permissions": [],
            "error": None,
        }

        try:
            role = self.get(role_id)
            if not role:
                result["valid"] = False
                result["error"] = "Role not found"
                return result

            role_permissions = role.get("Permissions", [])
            if isinstance(role_permissions, str):
                role_permissions = role_permissions.split(",")

            for permission in required_permissions:
                if permission in role_permissions:
                    result["has_permissions"].append(permission)
                else:
                    result["missing_permissions"].append(permission)

            if result["missing_permissions"]:
                result["valid"] = False

        except Exception as e:
            result["valid"] = False
            result["error"] = f"Validation error: {str(e)}"

        return result

    def clone_role(
        self,
        source_role_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> EntityDict:
        """
        Create a copy of an existing role.

        Args:
            source_role_id: ID of role to clone
            new_name: Name for the new role
            new_description: Optional description for new role

        Returns:
            Created role data
        """
        source_role = self.get(source_role_id)
        if not source_role:
            raise ValueError(f"Source role {source_role_id} not found")

        new_role_data = {
            "Name": new_name,
            "Description": new_description
            or f"Copy of {source_role.get('Name', 'Role')}",
            "IsActive": True,
            "IsSystemRole": False,  # Cloned roles are always custom
            "Permissions": source_role.get("Permissions", []),
        }

        # Copy other relevant fields
        for field in ["Level", "Category", "Priority"]:
            if field in source_role:
                new_role_data[field] = source_role[field]

        return self.create(new_role_data)

    def get_permission_usage_report(self) -> Dict[str, Any]:
        """
        Generate a report showing permission usage across roles.

        Returns:
            Dictionary with permission usage statistics
        """
        all_roles = self.get_active_roles()

        report = {
            "total_roles_analyzed": len(all_roles),
            "permission_usage": {},
            "most_common_permissions": [],
            "unused_permissions": [],
            "roles_by_permission_count": {"0-5": 0, "6-10": 0, "11-20": 0, "20+": 0},
        }

        all_permissions = set()
        permission_counts = {}

        for role in all_roles:
            role_permissions = role.get("Permissions", [])
            if isinstance(role_permissions, str):
                role_permissions = role_permissions.split(",")

            permission_count = len(role_permissions)

            # Categorize by permission count
            if permission_count <= 5:
                report["roles_by_permission_count"]["0-5"] += 1
            elif permission_count <= 10:
                report["roles_by_permission_count"]["6-10"] += 1
            elif permission_count <= 20:
                report["roles_by_permission_count"]["11-20"] += 1
            else:
                report["roles_by_permission_count"]["20+"] += 1

            for permission in role_permissions:
                all_permissions.add(permission)
                if permission not in permission_counts:
                    permission_counts[permission] = 0
                permission_counts[permission] += 1

        # Sort permissions by usage
        sorted_permissions = sorted(
            permission_counts.items(), key=lambda x: x[1], reverse=True
        )

        report["permission_usage"] = dict(sorted_permissions)
        report["most_common_permissions"] = sorted_permissions[:10]

        return report
