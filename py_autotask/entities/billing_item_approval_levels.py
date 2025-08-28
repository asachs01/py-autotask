"""
BillingItemApprovalLevels entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class BillingItemApprovalLevelsEntity(BaseEntity):
    """
    Handles all BillingItemApprovalLevels-related operations for the Autotask API.

    BillingItemApprovalLevels define approval workflow levels for billing items,
    controlling who can approve billing items at different stages.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_approval_level(
        self,
        billing_item_id: int,
        approval_level: int,
        resource_id: Optional[int] = None,
        role_id: Optional[int] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new billing item approval level.

        Args:
            billing_item_id: ID of the billing item
            approval_level: Level number (1, 2, 3, etc.)
            resource_id: ID of the specific resource approver
            role_id: ID of the role that can approve
            **kwargs: Additional approval level properties

        Returns:
            Created billing item approval level data
        """
        approval_data = {
            "BillingItemID": billing_item_id,
            "ApprovalLevel": approval_level,
            **kwargs,
        }

        if resource_id:
            approval_data["ResourceID"] = resource_id
        if role_id:
            approval_data["RoleID"] = role_id

        return self.create(approval_data)

    def get_approval_levels_by_billing_item(
        self, billing_item_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all approval levels for a specific billing item.

        Args:
            billing_item_id: ID of the billing item
            limit: Maximum number of approval levels to return

        Returns:
            List of approval levels for the billing item, ordered by level
        """
        filters = [QueryFilter(field="BillingItemID", op="eq", value=billing_item_id)]
        response = self.query(filters=filters, max_records=limit)

        items = response.items if hasattr(response, "items") else response
        # Sort by approval level
        return sorted(items, key=lambda x: x.get("ApprovalLevel", 0))

    def get_approval_levels_by_resource(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all approval levels assigned to a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of approval levels to return

        Returns:
            List of approval levels assigned to the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_approval_levels_by_role(
        self, role_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all approval levels assigned to a specific role.

        Args:
            role_id: ID of the role
            limit: Maximum number of approval levels to return

        Returns:
            List of approval levels assigned to the role
        """
        filters = [QueryFilter(field="RoleID", op="eq", value=role_id)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def update_approval_level_resource(
        self, approval_level_id: int, resource_id: int
    ) -> EntityDict:
        """
        Update the resource assigned to an approval level.

        Args:
            approval_level_id: ID of the approval level
            resource_id: New resource ID

        Returns:
            Updated approval level data
        """
        return self.update_by_id(approval_level_id, {"ResourceID": resource_id})

    def get_next_approval_level(
        self, billing_item_id: int, current_level: int
    ) -> Optional[EntityDict]:
        """
        Get the next approval level for a billing item.

        Args:
            billing_item_id: ID of the billing item
            current_level: Current approval level

        Returns:
            Next approval level data or None if no higher level exists
        """
        filters = [
            QueryFilter(field="BillingItemID", op="eq", value=billing_item_id),
            QueryFilter(field="ApprovalLevel", op="gt", value=current_level),
        ]
        response = self.query(filters=filters, max_records=1)
        items = response.items if hasattr(response, "items") else response

        return items[0] if items else None

    def validate_approval_workflow(self, billing_item_id: int) -> Dict[str, Any]:
        """
        Validate the approval workflow for a billing item.

        Args:
            billing_item_id: ID of the billing item

        Returns:
            Dictionary containing validation results
        """
        approval_levels = self.get_approval_levels_by_billing_item(billing_item_id)

        issues = []
        levels = [level.get("ApprovalLevel", 0) for level in approval_levels]

        # Check for gaps in approval levels
        if levels:
            expected_levels = list(range(1, max(levels) + 1))
            missing_levels = set(expected_levels) - set(levels)
            if missing_levels:
                issues.append(f"Missing approval levels: {sorted(missing_levels)}")

        # Check for duplicate levels
        duplicate_levels = set([x for x in levels if levels.count(x) > 1])
        if duplicate_levels:
            issues.append(f"Duplicate approval levels: {sorted(duplicate_levels)}")

        # Check that each level has an approver assigned
        unassigned_levels = []
        for level in approval_levels:
            if not level.get("ResourceID") and not level.get("RoleID"):
                unassigned_levels.append(level.get("ApprovalLevel"))

        if unassigned_levels:
            issues.append(f"Levels without approvers: {sorted(unassigned_levels)}")

        return {
            "is_valid": len(issues) == 0,
            "level_count": len(approval_levels),
            "max_level": max(levels) if levels else 0,
            "issues": issues,
        }

    def bulk_create_approval_workflow(
        self, billing_item_id: int, workflow_config: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create a complete approval workflow for a billing item.

        Args:
            billing_item_id: ID of the billing item
            workflow_config: List of approval level configurations

        Returns:
            List of created approval level responses
        """
        approval_data = []
        for level_config in workflow_config:
            approval_item = {
                "BillingItemID": billing_item_id,
                "ApprovalLevel": level_config.get("level"),
                **level_config,
            }
            approval_data.append(approval_item)

        return self.batch_create(approval_data)

    def get_approver_workload(
        self, resource_id: int, active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get approval workload statistics for a resource.

        Args:
            resource_id: ID of the resource
            active_only: Whether to count only active/pending approvals

        Returns:
            Dictionary containing workload statistics
        """
        approval_levels = self.get_approval_levels_by_resource(resource_id)

        # Group by billing item
        billing_items = {}
        for level in approval_levels:
            billing_item_id = level.get("BillingItemID")
            if billing_item_id not in billing_items:
                billing_items[billing_item_id] = []
            billing_items[billing_item_id].append(level)

        return {
            "total_approval_levels": len(approval_levels),
            "unique_billing_items": len(billing_items),
            "avg_levels_per_item": len(approval_levels) / max(1, len(billing_items)),
            "billing_item_breakdown": billing_items,
        }

    def reassign_approval_levels(
        self, old_resource_id: int, new_resource_id: int
    ) -> List[EntityDict]:
        """
        Reassign all approval levels from one resource to another.

        Args:
            old_resource_id: ID of the current resource
            new_resource_id: ID of the new resource

        Returns:
            List of updated approval levels
        """
        approval_levels = self.get_approval_levels_by_resource(old_resource_id)

        updated_levels = []
        for level in approval_levels:
            if level.get("id"):
                updated = self.update_by_id(
                    level["id"], {"ResourceID": new_resource_id}
                )
                updated_levels.append(updated)

        return updated_levels
