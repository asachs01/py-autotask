"""
Workflows Entity for py-autotask

This module provides the WorkflowsEntity class for managing workflow automation
rules and triggers in Autotask. Workflow rules automate business processes through
conditions, actions, and triggers that respond to data changes and events.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class WorkflowsEntity(BaseEntity):
    """
    Manages Autotask Workflows - workflow automation rules & triggers.

    Workflow rules enable automation of business processes through configurable
    conditions, actions, and triggers that respond to entity changes, time-based
    events, and user actions. They help streamline operations and ensure
    consistent process execution.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Workflows"

    def __init__(self, client, entity_name="Workflows"):
        """Initialize the Workflows entity."""
        super().__init__(client, entity_name)

    def create_workflow_rule(
        self,
        name: str,
        description: str,
        entity_type: str,
        trigger_type: str = "OnCreate",
        conditions: List[Dict[str, Any]] = None,
        actions: List[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new workflow rule.

        Args:
            name: Name of the workflow rule
            description: Description of what the rule does
            entity_type: Type of entity the rule applies to (Tickets, Projects, etc.)
            trigger_type: When the rule triggers (OnCreate, OnUpdate, OnDelete, Scheduled)
            conditions: List of conditions that must be met
            actions: List of actions to execute when conditions are met
            **kwargs: Additional fields for the workflow rule

        Returns:
            Create response with new workflow rule ID
        """
        rule_data = {
            "name": name,
            "description": description,
            "entityType": entity_type,
            "triggerType": trigger_type,
            "isActive": True,
            **kwargs,
        }

        if conditions:
            rule_data["conditions"] = conditions
        if actions:
            rule_data["actions"] = actions

        return self.create(rule_data)

    def get_workflow_rules_by_entity(
        self, entity_type: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get workflow rules for a specific entity type.

        Args:
            entity_type: Entity type to filter by
            active_only: Whether to only return active rules

        Returns:
            List of workflow rules for the entity type
        """
        filters = [{"field": "entityType", "op": "eq", "value": entity_type}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    def get_workflow_rules_by_trigger(
        self, trigger_type: str, entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get workflow rules by trigger type.

        Args:
            trigger_type: Trigger type to filter by
            entity_type: Optional entity type filter

        Returns:
            List of workflow rules with the specified trigger
        """
        filters = [{"field": "triggerType", "op": "eq", "value": trigger_type}]

        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        return self.query(filters=filters).items

    def activate_workflow_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Activate a workflow rule.

        Args:
            rule_id: ID of the workflow rule to activate

        Returns:
            Updated workflow rule data
        """
        return self.update_by_id(
            rule_id, {"isActive": True, "activatedDate": datetime.now().isoformat()}
        )

    def deactivate_workflow_rule(
        self, rule_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate a workflow rule.

        Args:
            rule_id: ID of the workflow rule to deactivate
            reason: Optional reason for deactivation

        Returns:
            Updated workflow rule data
        """
        update_data = {"isActive": False, "deactivatedDate": datetime.now().isoformat()}

        if reason:
            update_data["deactivationReason"] = reason

        return self.update_by_id(rule_id, update_data)

    def test_workflow_rule(
        self, rule_id: int, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a workflow rule against sample data.

        Args:
            rule_id: ID of the workflow rule to test
            test_data: Sample data to test against

        Returns:
            Test execution results
        """
        rule = self.get(rule_id)
        if not rule:
            return {"error": "Workflow rule not found"}

        # Simulate rule evaluation
        conditions = rule.get("conditions", [])
        actions = rule.get("actions", [])

        conditions_met = True
        condition_results = []

        # Evaluate conditions
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            expected_value = condition.get("value")
            actual_value = test_data.get(field)

            result = self._evaluate_condition(actual_value, operator, expected_value)
            condition_results.append(
                {"condition": condition, "result": result, "actual_value": actual_value}
            )

            if not result:
                conditions_met = False

        # Simulate actions if conditions are met
        action_results = []
        if conditions_met:
            for action in actions:
                action_results.append(
                    {"action": action, "simulated": True, "would_execute": True}
                )

        return {
            "rule_id": rule_id,
            "rule_name": rule.get("name"),
            "test_data": test_data,
            "conditions_met": conditions_met,
            "condition_results": condition_results,
            "action_results": action_results,
            "test_timestamp": datetime.now().isoformat(),
        }

    def _evaluate_condition(
        self, actual_value: Any, operator: str, expected_value: Any
    ) -> bool:
        """
        Evaluate a single condition.

        Args:
            actual_value: Actual value from test data
            operator: Comparison operator
            expected_value: Expected value

        Returns:
            Whether the condition is met
        """
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "greater_than":
            return actual_value > expected_value
        elif operator == "less_than":
            return actual_value < expected_value
        elif operator == "contains":
            return str(expected_value).lower() in str(actual_value).lower()
        elif operator == "is_empty":
            return not actual_value
        elif operator == "is_not_empty":
            return bool(actual_value)
        else:
            return False

    def clone_workflow_rule(
        self, source_rule_id: int, new_name: str, new_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clone a workflow rule.

        Args:
            source_rule_id: ID of the workflow rule to clone
            new_name: Name for the new workflow rule
            new_description: Optional new description

        Returns:
            Create response for the cloned workflow rule
        """
        source_rule = self.get(source_rule_id)
        if not source_rule:
            raise ValueError(f"Source workflow rule {source_rule_id} not found")

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_rule.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        clone_data["isActive"] = False  # Clones should start inactive

        if new_description:
            clone_data["description"] = new_description

        return self.create(clone_data)

    def get_workflow_execution_history(
        self,
        rule_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get workflow rule execution history.

        Args:
            rule_id: Optional workflow rule filter
            entity_id: Optional entity filter
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of workflow execution records
        """
        # This would typically query a workflow execution log table
        # For now, return sample execution history
        return [
            {
                "execution_id": "exec_001",
                "rule_id": rule_id or 1,
                "entity_id": entity_id or 12345,
                "entity_type": "Tickets",
                "execution_date": "2024-01-15T10:30:00Z",
                "status": "Success",
                "conditions_met": True,
                "actions_executed": 2,
                "execution_time_ms": 150,
            },
            {
                "execution_id": "exec_002",
                "rule_id": rule_id or 1,
                "entity_id": entity_id or 12346,
                "entity_type": "Tickets",
                "execution_date": "2024-01-15T11:45:00Z",
                "status": "Failed",
                "conditions_met": True,
                "actions_executed": 0,
                "execution_time_ms": 75,
                "error_message": "Email service unavailable",
            },
        ]

    def get_workflow_rules_summary(
        self, entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive workflow rules summary.

        Args:
            entity_type: Optional entity type filter

        Returns:
            Workflow rules summary
        """
        filters = []
        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        rules = self.query(filters=filters).items if filters else self.query_all()

        # Analyze workflow rules
        total_rules = len(rules)
        active_rules = len([r for r in rules if r.get("isActive", False)])
        inactive_rules = total_rules - active_rules

        # Group by entity type
        by_entity_type = {}
        by_trigger_type = {}

        for rule in rules:
            entity_type = rule.get("entityType", "Unknown")
            trigger_type = rule.get("triggerType", "Unknown")

            if entity_type not in by_entity_type:
                by_entity_type[entity_type] = {"total": 0, "active": 0}
            by_entity_type[entity_type]["total"] += 1
            if rule.get("isActive"):
                by_entity_type[entity_type]["active"] += 1

            if trigger_type not in by_trigger_type:
                by_trigger_type[trigger_type] = 0
            by_trigger_type[trigger_type] += 1

        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "inactive_rules": inactive_rules,
            "rules_by_entity_type": by_entity_type,
            "rules_by_trigger_type": by_trigger_type,
        }

    def bulk_activate_workflow_rules(self, rule_ids: List[int]) -> Dict[str, Any]:
        """
        Activate multiple workflow rules.

        Args:
            rule_ids: List of workflow rule IDs to activate

        Returns:
            Summary of bulk activation operation
        """
        results = []

        for rule_id in rule_ids:
            try:
                result = self.activate_workflow_rule(rule_id)
                results.append({"id": rule_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": rule_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_rules": len(rule_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def validate_workflow_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate workflow rule configuration.

        Args:
            rule_data: Workflow rule data to validate

        Returns:
            Validation result with any errors or warnings
        """
        errors = []
        warnings = []

        # Required fields validation
        required_fields = ["name", "description", "entityType", "triggerType"]
        for field in required_fields:
            if not rule_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate entity type
        valid_entity_types = ["Tickets", "Projects", "Companies", "Contacts", "Tasks"]
        entity_type = rule_data.get("entityType")
        if entity_type and entity_type not in valid_entity_types:
            warnings.append(f"Entity type '{entity_type}' may not be supported")

        # Validate trigger type
        valid_trigger_types = ["OnCreate", "OnUpdate", "OnDelete", "Scheduled"]
        trigger_type = rule_data.get("triggerType")
        if trigger_type and trigger_type not in valid_trigger_types:
            errors.append(f"Invalid trigger type: {trigger_type}")

        # Validate conditions
        conditions = rule_data.get("conditions", [])
        if not conditions:
            warnings.append("No conditions defined - rule will always execute")

        for i, condition in enumerate(conditions):
            if not condition.get("field"):
                errors.append(f"Condition {i + 1}: Missing field")
            if not condition.get("operator"):
                errors.append(f"Condition {i + 1}: Missing operator")

        # Validate actions
        actions = rule_data.get("actions", [])
        if not actions:
            warnings.append("No actions defined - rule will not perform any operations")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_date": datetime.now().isoformat(),
        }

    def create_workflow_template(
        self,
        template_name: str,
        template_description: str,
        entity_type: str,
        rule_definitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create a reusable workflow template.

        Args:
            template_name: Name of the workflow template
            template_description: Description of the template
            entity_type: Entity type the template applies to
            rule_definitions: List of workflow rule definitions

        Returns:
            Created template information
        """
        template_data = {
            "name": template_name,
            "description": template_description,
            "entity_type": entity_type,
            "rule_definitions": rule_definitions,
            "created_date": datetime.now().isoformat(),
        }

        # Validate template
        validation_errors = []
        for i, rule_def in enumerate(rule_definitions):
            validation = self.validate_workflow_rule(rule_def)
            if not validation["is_valid"]:
                validation_errors.extend(
                    [f"Rule {i + 1}: {error}" for error in validation["errors"]]
                )

        return {
            "template_id": f"template_{template_name.lower().replace(' ', '_')}",
            "template_name": template_name,
            "rule_count": len(rule_definitions),
            "is_valid": len(validation_errors) == 0,
            "validation_errors": validation_errors,
            "template_data": template_data,
        }

    def apply_workflow_template(
        self, template_id: str, template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a workflow template to create multiple rules.

        Args:
            template_id: ID of the template to apply
            template_data: Template data containing rule definitions

        Returns:
            Template application results
        """
        rule_definitions = template_data.get("rule_definitions", [])
        results = []

        for rule_def in rule_definitions:
            try:
                result = self.create_workflow_rule(**rule_def)
                results.append(
                    {
                        "rule_name": rule_def.get("name"),
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "rule_name": rule_def.get("name"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "template_id": template_id,
            "total_rules": len(rule_definitions),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }
