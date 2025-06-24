"""
Workflow Rules entity for Autotask API operations.
"""

import logging
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class WorkflowRulesEntity(BaseEntity):
    """
    Handles all Workflow Rule-related operations for the Autotask API.

    Workflow rules enable automation of business processes through
    configurable triggers and actions that respond to entity changes.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_workflow_rule(
        self,
        name: str,
        entity_type: str,
        trigger_event: str,
        is_active: bool = True,
        description: Optional[str] = None,
        execution_order: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new workflow rule.

        Args:
            name: Name of the workflow rule
            entity_type: Entity type this rule applies to (e.g., 'Tickets', 'Projects')
            trigger_event: Event that triggers the rule ('Create', 'Update', 'Delete')
            is_active: Whether the rule is active
            description: Description of the workflow rule
            execution_order: Order of execution when multiple rules apply
            **kwargs: Additional workflow rule fields

        Returns:
            Created workflow rule data

        Example:
            rule = client.workflow_rules.create_workflow_rule(
                "Auto-assign Priority Tickets",
                "Tickets",
                "Create",
                description="Automatically assign high priority tickets to senior staff"
            )
        """
        rule_data = {
            "Name": name,
            "EntityType": entity_type,
            "TriggerEvent": trigger_event,
            "IsActive": is_active,
            "ExecutionOrder": execution_order,
            **kwargs,
        }

        if description:
            rule_data["Description"] = description

        return self.create(rule_data)

    def get_active_workflow_rules(
        self,
        entity_type: Optional[str] = None,
        trigger_event: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all active workflow rules.

        Args:
            entity_type: Optional entity type filter
            trigger_event: Optional trigger event filter
            limit: Maximum number of rules to return

        Returns:
            List of active workflow rules

        Example:
            rules = client.workflow_rules.get_active_workflow_rules("Tickets")
        """
        filters = [{"field": "IsActive", "op": "eq", "value": True}]

        if entity_type:
            filters.append({"field": "EntityType", "op": "eq", "value": entity_type})
        if trigger_event:
            filters.append(
                {"field": "TriggerEvent", "op": "eq", "value": trigger_event}
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_rules_by_entity_type(
        self, entity_type: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get workflow rules for a specific entity type.

        Args:
            entity_type: Entity type to filter by
            active_only: Whether to return only active rules
            limit: Maximum number of rules to return

        Returns:
            List of workflow rules for the entity type

        Example:
            ticket_rules = client.workflow_rules.get_rules_by_entity_type("Tickets")
        """
        filters = [{"field": "EntityType", "op": "eq", "value": entity_type}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def activate_workflow_rule(self, rule_id: int) -> EntityDict:
        """
        Activate a workflow rule.

        Args:
            rule_id: ID of workflow rule to activate

        Returns:
            Updated workflow rule data

        Example:
            activated = client.workflow_rules.activate_workflow_rule(12345)
        """
        return self.update_by_id(rule_id, {"IsActive": True})

    def deactivate_workflow_rule(self, rule_id: int) -> EntityDict:
        """
        Deactivate a workflow rule.

        Args:
            rule_id: ID of workflow rule to deactivate

        Returns:
            Updated workflow rule data

        Example:
            deactivated = client.workflow_rules.deactivate_workflow_rule(12345)
        """
        return self.update_by_id(rule_id, {"IsActive": False})

    def get_workflow_rule_conditions(self, rule_id: int) -> List[EntityDict]:
        """
        Get all conditions for a specific workflow rule.

        Args:
            rule_id: ID of the workflow rule

        Returns:
            List of rule conditions

        Example:
            conditions = client.workflow_rules.get_workflow_rule_conditions(12345)
        """
        filters = [{"field": "WorkflowRuleID", "op": "eq", "value": rule_id}]

        # Query workflow rule conditions entity
        response = self.client.query("WorkflowRuleConditions", filters)
        return response.items if hasattr(response, "items") else response

    def get_workflow_rule_actions(self, rule_id: int) -> List[EntityDict]:
        """
        Get all actions for a specific workflow rule.

        Args:
            rule_id: ID of the workflow rule

        Returns:
            List of rule actions

        Example:
            actions = client.workflow_rules.get_workflow_rule_actions(12345)
        """
        filters = [{"field": "WorkflowRuleID", "op": "eq", "value": rule_id}]

        # Query workflow rule actions entity
        response = self.client.query("WorkflowRuleActions", filters)
        return response.items if hasattr(response, "items") else response

    def clone_workflow_rule(
        self,
        rule_id: int,
        new_name: str,
        copy_conditions: bool = True,
        copy_actions: bool = True,
    ) -> EntityDict:
        """
        Clone a workflow rule with its conditions and actions.

        Args:
            rule_id: ID of workflow rule to clone
            new_name: Name for the cloned rule
            copy_conditions: Whether to copy rule conditions
            copy_actions: Whether to copy rule actions

        Returns:
            Created cloned workflow rule data

        Example:
            cloned = client.workflow_rules.clone_workflow_rule(
                12345, "Copy of Auto-assign Rule"
            )
        """
        original = self.get(rule_id)
        if not original:
            raise ValueError(f"Workflow rule {rule_id} not found")

        # Create new workflow rule
        clone_data = {
            "Name": new_name,
            "EntityType": original.get("EntityType"),
            "TriggerEvent": original.get("TriggerEvent"),
            "Description": original.get("Description"),
            "ExecutionOrder": original.get("ExecutionOrder", 1),
            "IsActive": False,  # Start inactive for safety
        }

        new_rule = self.create(clone_data)
        new_rule_id = new_rule.get("item_id") or new_rule.get("id")

        # Copy conditions if requested
        if copy_conditions and new_rule_id:
            conditions = self.get_workflow_rule_conditions(rule_id)
            for condition in conditions:
                condition_data = {
                    "WorkflowRuleID": new_rule_id,
                    "FieldName": condition.get("FieldName"),
                    "Operator": condition.get("Operator"),
                    "Value": condition.get("Value"),
                    "LogicalOperator": condition.get("LogicalOperator"),
                }

                try:
                    self.client.create_entity("WorkflowRuleConditions", condition_data)
                except Exception as e:
                    self.logger.error(f"Failed to copy condition: {e}")

        # Copy actions if requested
        if copy_actions and new_rule_id:
            actions = self.get_workflow_rule_actions(rule_id)
            for action in actions:
                action_data = {
                    "WorkflowRuleID": new_rule_id,
                    "ActionType": action.get("ActionType"),
                    "FieldName": action.get("FieldName"),
                    "Value": action.get("Value"),
                    "ExecutionOrder": action.get("ExecutionOrder"),
                }

                try:
                    self.client.create_entity("WorkflowRuleActions", action_data)
                except Exception as e:
                    self.logger.error(f"Failed to copy action: {e}")

        return new_rule

    def get_workflow_rule_summary(self, rule_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a workflow rule.

        Args:
            rule_id: ID of the workflow rule

        Returns:
            Workflow rule summary with conditions and actions

        Example:
            summary = client.workflow_rules.get_workflow_rule_summary(12345)
        """
        rule = self.get(rule_id)
        if not rule:
            return {}

        conditions = self.get_workflow_rule_conditions(rule_id)
        actions = self.get_workflow_rule_actions(rule_id)

        return {
            "rule_id": rule_id,
            "name": rule.get("Name"),
            "description": rule.get("Description"),
            "entity_type": rule.get("EntityType"),
            "trigger_event": rule.get("TriggerEvent"),
            "is_active": rule.get("IsActive"),
            "execution_order": rule.get("ExecutionOrder"),
            "created_date": rule.get("CreateDate"),
            "last_modified_date": rule.get("LastModifiedDate"),
            "conditions_count": len(conditions),
            "actions_count": len(actions),
            "conditions": conditions,
            "actions": actions,
        }

    def update_execution_order(self, rule_id: int, new_order: int) -> EntityDict:
        """
        Update the execution order of a workflow rule.

        Args:
            rule_id: ID of workflow rule to update
            new_order: New execution order

        Returns:
            Updated workflow rule data

        Example:
            updated = client.workflow_rules.update_execution_order(12345, 5)
        """
        return self.update_by_id(rule_id, {"ExecutionOrder": new_order})

    def bulk_activate_rules(
        self, rule_ids: List[int], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Activate multiple workflow rules in batches.

        Args:
            rule_ids: List of workflow rule IDs to activate
            batch_size: Number of rules to process per batch

        Returns:
            List of updated workflow rule data

        Example:
            activated = client.workflow_rules.bulk_activate_rules([12345, 12346, 12347])
        """
        results = []

        for i in range(0, len(rule_ids), batch_size):
            batch = rule_ids[i : i + batch_size]

            for rule_id in batch:
                try:
                    result = self.activate_workflow_rule(rule_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to activate workflow rule {rule_id}: {e}"
                    )
                    continue

        return results

    def bulk_deactivate_rules(
        self, rule_ids: List[int], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Deactivate multiple workflow rules in batches.

        Args:
            rule_ids: List of workflow rule IDs to deactivate
            batch_size: Number of rules to process per batch

        Returns:
            List of updated workflow rule data

        Example:
            deactivated = client.workflow_rules.bulk_deactivate_rules([12345, 12346, 12347])
        """
        results = []

        for i in range(0, len(rule_ids), batch_size):
            batch = rule_ids[i : i + batch_size]

            for rule_id in batch:
                try:
                    result = self.deactivate_workflow_rule(rule_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to deactivate workflow rule {rule_id}: {e}"
                    )
                    continue

        return results

    def get_workflow_rules_by_trigger(
        self,
        trigger_event: str,
        entity_type: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get workflow rules by trigger event.

        Args:
            trigger_event: Trigger event to filter by
            entity_type: Optional entity type filter
            active_only: Whether to return only active rules
            limit: Maximum number of rules to return

        Returns:
            List of workflow rules for the trigger event

        Example:
            create_rules = client.workflow_rules.get_workflow_rules_by_trigger("Create")
        """
        filters = [{"field": "TriggerEvent", "op": "eq", "value": trigger_event}]

        if entity_type:
            filters.append({"field": "EntityType", "op": "eq", "value": entity_type})
        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_workflow_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Validate a workflow rule for completeness and potential issues.

        Args:
            rule_id: ID of the workflow rule to validate

        Returns:
            Validation results with warnings and recommendations

        Example:
            validation = client.workflow_rules.validate_workflow_rule(12345)
        """
        rule = self.get(rule_id)
        if not rule:
            return {"error": f"Workflow rule {rule_id} not found"}

        conditions = self.get_workflow_rule_conditions(rule_id)
        actions = self.get_workflow_rule_actions(rule_id)
        warnings = []
        recommendations = []

        # Check for conditions
        if not conditions:
            warnings.append("No conditions defined for this rule")
            recommendations.append("Add conditions to control when the rule executes")

        # Check for actions
        if not actions:
            warnings.append("No actions defined for this rule")
            recommendations.append("Add actions to define what the rule should do")

        # Check if active but incomplete
        if rule.get("IsActive") and (not conditions or not actions):
            warnings.append("Active rule without proper conditions or actions")
            recommendations.append("Complete rule configuration before activating")

        # Check execution order
        if rule.get("ExecutionOrder", 0) <= 0:
            warnings.append("Invalid execution order")
            recommendations.append("Set a positive execution order value")

        return {
            "rule_id": rule_id,
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": recommendations,
            "conditions_count": len(conditions),
            "actions_count": len(actions),
            "is_active": rule.get("IsActive"),
        }

    def get_entity_type_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of workflow rules by entity type.

        Returns:
            Distribution statistics by entity type

        Example:
            distribution = client.workflow_rules.get_entity_type_distribution()
        """
        all_rules = self.query_all()

        entity_counts = {}
        active_entity_counts = {}
        trigger_counts = {}

        for rule in all_rules:
            entity_type = rule.get("EntityType", "Unknown")
            trigger_event = rule.get("TriggerEvent", "Unknown")

            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            trigger_counts[trigger_event] = trigger_counts.get(trigger_event, 0) + 1

            if rule.get("IsActive"):
                active_entity_counts[entity_type] = (
                    active_entity_counts.get(entity_type, 0) + 1
                )

        return {
            "total_rules": len(all_rules),
            "active_rules": sum(active_entity_counts.values()),
            "entity_types": list(entity_counts.keys()),
            "trigger_events": list(trigger_counts.keys()),
            "entity_type_distribution": entity_counts,
            "active_entity_distribution": active_entity_counts,
            "trigger_event_distribution": trigger_counts,
        }

    def search_workflow_rules(
        self, name_pattern: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search workflow rules by name pattern.

        Args:
            name_pattern: Pattern to search for in rule names
            active_only: Whether to return only active rules
            limit: Maximum number of rules to return

        Returns:
            List of matching workflow rules

        Example:
            rules = client.workflow_rules.search_workflow_rules("priority")
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response
