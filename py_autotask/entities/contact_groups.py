"""
Contact Groups entity for Autotask API operations.
"""

from typing import Any, Dict, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class ContactGroupsEntity(BaseEntity):
    """
    Handles Contact Group operations for the Autotask API.

    Manages groupings of contacts for organizational purposes,
    enabling bulk operations and categorization of contacts.
    """

    def __init__(self, client, entity_name: str = "ContactGroups"):
        super().__init__(client, entity_name)

    def create_contact_group(
        self,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new contact group.

        Args:
            name: Group name
            description: Optional group description
            is_active: Whether the group is active
            **kwargs: Additional group fields

        Returns:
            Created contact group data
        """
        group_data = {
            "Name": name,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            group_data["Description"] = description

        return self.create(group_data)

    def get_active_groups(self) -> EntityList:
        """
        Get all active contact groups.

        Returns:
            List of active contact groups
        """
        filters = [{"field": "IsActive", "op": "eq", "value": "true"}]
        return self.query_all(filters=filters)

    def get_groups_by_name(self, name_pattern: str) -> EntityList:
        """
        Search contact groups by name pattern.

        Args:
            name_pattern: Name pattern to search for

        Returns:
            List of matching contact groups
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]
        return self.query_all(filters=filters)

    def update_group_status(
        self, group_id: int, is_active: bool
    ) -> Optional[EntityDict]:
        """
        Update the active status of a contact group.

        Args:
            group_id: Group ID to update
            is_active: New active status

        Returns:
            Updated group data
        """
        return self.update_by_id(group_id, {"IsActive": is_active})

    def update_group_details(
        self,
        group_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Update contact group name and description.

        Args:
            group_id: Group ID to update
            name: New group name
            description: New group description

        Returns:
            Updated group data
        """
        update_data = {}

        if name is not None:
            update_data["Name"] = name

        if description is not None:
            update_data["Description"] = description

        if update_data:
            return self.update_by_id(group_id, update_data)

        return None

    def get_group_members(self, group_id: int) -> EntityList:
        """
        Get all contacts that are members of a specific group.

        Note: This requires the ContactGroupContacts entity to be available.

        Args:
            group_id: Contact group ID

        Returns:
            List of contact group membership records
        """
        # This would typically query the ContactGroupContacts entity
        # Since we're implementing that separately, we'll use the client directly
        filters = [{"field": "ContactGroupID", "op": "eq", "value": str(group_id)}]

        try:
            return self.client.query("ContactGroupContacts", {"filter": filters}).items
        except Exception as e:
            self.logger.warning(f"Could not fetch group members: {e}")
            return []

    def get_member_count(self, group_id: int) -> int:
        """
        Get the count of members in a contact group.

        Args:
            group_id: Contact group ID

        Returns:
            Number of members in the group
        """
        members = self.get_group_members(group_id)
        return len(members)

    def find_groups_for_contact(self, contact_id: int) -> EntityList:
        """
        Find all groups that a contact belongs to.

        Args:
            contact_id: Contact ID to search for

        Returns:
            List of contact groups the contact belongs to
        """
        try:
            # Query the ContactGroupContacts entity for this contact
            filters = [{"field": "ContactID", "op": "eq", "value": str(contact_id)}]
            memberships = self.client.query(
                "ContactGroupContacts", {"filter": filters}
            ).items

            # Extract group IDs and fetch group details
            group_ids = [int(m["ContactGroupID"]) for m in memberships]

            if group_ids:
                group_filters = [
                    {
                        "field": "id",
                        "op": "in",
                        "value": [str(gid) for gid in group_ids],
                    }
                ]
                return self.query_all(filters=group_filters)

            return []

        except Exception as e:
            self.logger.warning(f"Could not find groups for contact: {e}")
            return []

    def get_group_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about contact groups.

        Returns:
            Dictionary with contact group statistics
        """
        all_groups = self.query_all()
        active_groups = self.get_active_groups()

        stats = {
            "total_groups": len(all_groups),
            "active_groups": len(active_groups),
            "inactive_groups": len(all_groups) - len(active_groups),
            "groups_with_members": 0,
            "empty_groups": 0,
            "total_memberships": 0,
            "average_group_size": 0.0,
        }

        # Calculate membership statistics
        groups_with_members = 0
        total_memberships = 0

        for group in all_groups:
            member_count = self.get_member_count(int(group["id"]))
            if member_count > 0:
                groups_with_members += 1
                total_memberships += member_count
            else:
                stats["empty_groups"] += 1

        stats["groups_with_members"] = groups_with_members
        stats["total_memberships"] = total_memberships

        if stats["total_groups"] > 0:
            stats["average_group_size"] = total_memberships / stats["total_groups"]

        return stats

    def cleanup_empty_groups(self, confirm: bool = False) -> Dict[str, Any]:
        """
        Identify and optionally deactivate empty contact groups.

        Args:
            confirm: Whether to actually deactivate empty groups

        Returns:
            Dictionary with cleanup results
        """
        all_groups = self.get_active_groups()
        empty_groups = []

        # Find empty groups
        for group in all_groups:
            member_count = self.get_member_count(int(group["id"]))
            if member_count == 0:
                empty_groups.append(group)

        result = {
            "empty_groups_found": len(empty_groups),
            "empty_group_ids": [int(g["id"]) for g in empty_groups],
            "deactivated": [],
            "errors": [],
        }

        if confirm and empty_groups:
            # Deactivate empty groups
            for group in empty_groups:
                try:
                    updated = self.update_group_status(int(group["id"]), False)
                    if updated:
                        result["deactivated"].append(int(group["id"]))
                except Exception as e:
                    result["errors"].append(
                        f"Failed to deactivate group {group['id']}: {e}"
                    )

        return result

    def duplicate_group(
        self,
        source_group_id: int,
        new_name: str,
        copy_members: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a duplicate of an existing contact group.

        Args:
            source_group_id: ID of group to duplicate
            new_name: Name for the new group
            copy_members: Whether to copy group members

        Returns:
            Dictionary with duplication results
        """
        result = {
            "new_group": None,
            "members_copied": 0,
            "errors": [],
        }

        try:
            # Get source group details
            source_group = self.get(source_group_id)
            if not source_group:
                result["errors"].append("Source group not found")
                return result

            # Create new group with similar properties
            new_group_data = {
                "Name": new_name,
                "Description": f"Copy of {source_group.get('Name', 'Unknown Group')}",
                "IsActive": source_group.get("IsActive", True),
            }

            # Copy additional fields if present
            for field in ["Color", "SortOrder", "Type"]:
                if field in source_group:
                    new_group_data[field] = source_group[field]

            new_group = self.create(new_group_data)
            result["new_group"] = new_group

            # Copy members if requested
            if copy_members:
                members = self.get_group_members(source_group_id)
                for member in members:
                    try:
                        # Create new membership record
                        member_data = {
                            "ContactGroupID": int(new_group["item_id"]),
                            "ContactID": member["ContactID"],
                        }
                        self.client.create_entity("ContactGroupContacts", member_data)
                        result["members_copied"] += 1
                    except Exception as e:
                        result["errors"].append(
                            f"Failed to copy member {member.get('ContactID')}: {e}"
                        )

        except Exception as e:
            result["errors"].append(f"Failed to duplicate group: {e}")

        return result

    def validate_group_name(
        self, name: str, exclude_group_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate that a group name is unique and meets requirements.

        Args:
            name: Group name to validate
            exclude_group_id: Optional group ID to exclude from uniqueness check

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Basic validation
        if not name or not name.strip():
            result["errors"].append("Group name cannot be empty")
            result["valid"] = False
            return result

        if len(name.strip()) < 2:
            result["errors"].append("Group name must be at least 2 characters")
            result["valid"] = False

        if len(name) > 100:  # Assuming max length limit
            result["errors"].append("Group name is too long (max 100 characters)")
            result["valid"] = False

        # Check for uniqueness
        try:
            existing_groups = self.get_groups_by_name(name.strip())
            matching_groups = [
                g for g in existing_groups if g["Name"].lower() == name.lower().strip()
            ]

            if exclude_group_id:
                matching_groups = [
                    g for g in matching_groups if int(g["id"]) != exclude_group_id
                ]

            if matching_groups:
                result["errors"].append("A group with this name already exists")
                result["valid"] = False

        except Exception as e:
            result["warnings"].append(f"Could not verify name uniqueness: {e}")

        return result
