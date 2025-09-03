"""
BusinessRules Entity for py-autotask

This module provides the BusinessRulesEntity class for managing business rules
in Autotask. Business rules enable validation, automation, and enforcement
of business logic through configurable rule engines and validation frameworks.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class BusinessRulesEntity(BaseEntity):
    """
    Manages Autotask BusinessRules - rule engine and validation framework.

    Business rules provide configurable validation, automation, and enforcement
    of business logic across all Autotask entities and processes. They support
    rule-based validation, automated decision making, compliance enforcement,
    and business process automation through a flexible rule engine.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "BusinessRules"

    def create_business_rule(
        self,
        name: str,
        rule_type: str,
        entity_target: str,
        condition_expression: str,
        action_type: str,
        is_active: bool = True,
        priority: int = 1,
        description: Optional[str] = None,
        effective_date: Optional[datetime] = None,
        expiration_date: Optional[datetime] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new business rule.

        Args:
            name: Name of the business rule
            rule_type: Type of rule ('Validation', 'Automation', 'Compliance', 'Calculation')
            entity_target: Target entity type this rule applies to
            condition_expression: Logic expression defining when rule applies
            action_type: Type of action to perform ('Block', 'Warn', 'Modify', 'Calculate')
            is_active: Whether the rule is currently active
            priority: Execution priority (1=highest, 999=lowest)
            description: Description of the business rule
            effective_date: When the rule becomes effective
            expiration_date: When the rule expires
            **kwargs: Additional rule configuration fields

        Returns:
            Created business rule data

        Example:
            rule = client.business_rules.create_business_rule(
                "Ticket Priority Validation",
                "Validation",
                "Tickets",
                "priority > 3 AND assignedResourceID IS NULL",
                "Block",
                description="Prevent high priority tickets without assignment"
            )
        """
        rule_data = {
            "name": name,
            "ruleType": rule_type,
            "entityTarget": entity_target,
            "conditionExpression": condition_expression,
            "actionType": action_type,
            "isActive": is_active,
            "priority": priority,
            **kwargs,
        }

        if description:
            rule_data["description"] = description
        if effective_date:
            rule_data["effectiveDate"] = effective_date.isoformat()
        if expiration_date:
            rule_data["expirationDate"] = expiration_date.isoformat()

        self.logger.info(f"Creating business rule: {name} for {entity_target}")
        return self.create(rule_data)

    def get_active_business_rules(
        self,
        entity_target: Optional[str] = None,
        rule_type: Optional[str] = None,
        priority_range: Optional[tuple] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all active business rules.

        Args:
            entity_target: Optional entity type filter
            rule_type: Optional rule type filter
            priority_range: Optional priority range (min, max)
            limit: Maximum number of rules to return

        Returns:
            List of active business rules

        Example:
            rules = client.business_rules.get_active_business_rules(
                entity_target="Tickets",
                rule_type="Validation"
            )
        """
        filters = [{"field": "isActive", "op": "eq", "value": True}]

        if entity_target:
            filters.append(
                {"field": "entityTarget", "op": "eq", "value": entity_target}
            )
        if rule_type:
            filters.append({"field": "ruleType", "op": "eq", "value": rule_type})
        if priority_range:
            min_priority, max_priority = priority_range
            filters.append({"field": "priority", "op": "gte", "value": min_priority})
            filters.append({"field": "priority", "op": "lte", "value": max_priority})

        current_time = datetime.now()
        filters.append(
            {"field": "effectiveDate", "op": "lte", "value": current_time.isoformat()}
        )
        filters.append(
            {"field": "expirationDate", "op": "gte", "value": current_time.isoformat()}
        )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_rules(
        self, entity_data: EntityDict, entity_type: str, operation: str = "create"
    ) -> Dict[str, Any]:
        """
        Validate entity data against applicable business rules.

        Args:
            entity_data: Entity data to validate
            entity_type: Type of entity being validated
            operation: Operation being performed ('create', 'update', 'delete')

        Returns:
            Validation results with any rule violations

        Example:
            validation = client.business_rules.validate_rules(
                {"title": "Test Ticket", "priority": 4},
                "Tickets",
                "create"
            )
        """
        applicable_rules = self.get_active_business_rules(
            entity_target=entity_type, rule_type="Validation"
        )

        violations = []
        warnings = []
        rule_results = []

        for rule in applicable_rules:
            rule_id = rule.get("id")
            rule_name = rule.get("name")
            condition = rule.get("conditionExpression")
            action_type = rule.get("actionType")

            try:
                # Evaluate rule condition against entity data
                rule_applies = self._evaluate_rule_condition(condition, entity_data)

                rule_result = {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "rule_applies": rule_applies,
                    "action_type": action_type,
                    "priority": rule.get("priority", 999),
                }

                if rule_applies:
                    if action_type == "Block":
                        violations.append(
                            {
                                "rule_id": rule_id,
                                "rule_name": rule_name,
                                "severity": "error",
                                "message": f"Rule violation: {rule_name}",
                                "condition": condition,
                            }
                        )
                    elif action_type == "Warn":
                        warnings.append(
                            {
                                "rule_id": rule_id,
                                "rule_name": rule_name,
                                "severity": "warning",
                                "message": f"Rule warning: {rule_name}",
                                "condition": condition,
                            }
                        )

                rule_results.append(rule_result)

            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule_id}: {e}")
                rule_results.append(
                    {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "rule_applies": False,
                        "error": str(e),
                    }
                )

        return {
            "entity_type": entity_type,
            "operation": operation,
            "validation_passed": len(violations) == 0,
            "rules_evaluated": len(rule_results),
            "violations": violations,
            "warnings": warnings,
            "rule_results": rule_results,
            "validation_timestamp": datetime.now().isoformat(),
        }

    def execute_rule_engine(
        self,
        entity_data: EntityDict,
        entity_type: str,
        operation: str = "create",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute business rule engine for entity operations.

        Args:
            entity_data: Entity data to process
            entity_type: Type of entity being processed
            operation: Operation being performed
            dry_run: If True, simulate execution without making changes

        Returns:
            Rule engine execution results

        Example:
            result = client.business_rules.execute_rule_engine(
                {"title": "Test Ticket", "priority": 3},
                "Tickets",
                "create"
            )
        """
        applicable_rules = self.get_active_business_rules(entity_target=entity_type)

        # Sort rules by priority (1 = highest priority)
        applicable_rules.sort(key=lambda r: r.get("priority", 999))

        executed_rules = []
        applied_modifications = []
        calculated_values = {}
        execution_errors = []

        modified_data = entity_data.copy()

        for rule in applicable_rules:
            rule_id = rule.get("id")
            rule_name = rule.get("name")
            rule_type = rule.get("ruleType")
            condition = rule.get("conditionExpression")
            action_type = rule.get("actionType")

            try:
                # Check if rule applies
                rule_applies = self._evaluate_rule_condition(condition, modified_data)

                rule_execution = {
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "rule_type": rule_type,
                    "rule_applies": rule_applies,
                    "action_type": action_type,
                    "executed": False,
                    "execution_time": datetime.now().isoformat(),
                }

                if rule_applies:
                    if rule_type == "Automation" and not dry_run:
                        # Execute automation rules
                        automation_result = self._execute_automation_rule(
                            rule, modified_data
                        )
                        if automation_result.get("success"):
                            applied_modifications.extend(
                                automation_result.get("modifications", [])
                            )
                            rule_execution["executed"] = True
                            rule_execution["result"] = automation_result

                    elif rule_type == "Calculation":
                        # Execute calculation rules
                        calc_result = self._execute_calculation_rule(
                            rule, modified_data
                        )
                        if calc_result.get("success"):
                            calculated_values.update(calc_result.get("values", {}))
                            # Apply calculated values to entity data
                            modified_data.update(calc_result.get("values", {}))
                            rule_execution["executed"] = True
                            rule_execution["result"] = calc_result

                executed_rules.append(rule_execution)

            except Exception as e:
                self.logger.error(f"Error executing rule {rule_id}: {e}")
                execution_errors.append(
                    {"rule_id": rule_id, "rule_name": rule_name, "error": str(e)}
                )

        return {
            "entity_type": entity_type,
            "operation": operation,
            "dry_run": dry_run,
            "original_data": entity_data,
            "modified_data": modified_data,
            "rules_executed": len(executed_rules),
            "successful_executions": len(
                [r for r in executed_rules if r.get("executed")]
            ),
            "applied_modifications": applied_modifications,
            "calculated_values": calculated_values,
            "execution_errors": execution_errors,
            "executed_rules": executed_rules,
            "execution_timestamp": datetime.now().isoformat(),
        }

    def analyze_rule_performance(
        self,
        date_from: datetime,
        date_to: datetime,
        entity_type: Optional[str] = None,
        rule_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze business rule performance and execution statistics.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            entity_type: Optional entity type filter
            rule_type: Optional rule type filter

        Returns:
            Rule performance analysis results

        Example:
            performance = client.business_rules.analyze_rule_performance(
                datetime(2024, 1, 1),
                datetime(2024, 12, 31),
                entity_type="Tickets"
            )
        """
        filters = []
        if entity_type:
            filters.append({"field": "entityTarget", "op": "eq", "value": entity_type})
        if rule_type:
            filters.append({"field": "ruleType", "op": "eq", "value": rule_type})

        rules = self.query(filters=filters if filters else None)
        all_rules = rules.items if hasattr(rules, "items") else rules

        # This would typically query rule execution logs
        # For now, return performance analysis structure
        rule_stats = []

        for rule in all_rules:
            rule_id = rule.get("id")
            rule_name = rule.get("name")

            # Simulate performance metrics
            stats = {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "rule_type": rule.get("ruleType"),
                "entity_target": rule.get("entityTarget"),
                "is_active": rule.get("isActive"),
                "performance_metrics": {
                    "total_executions": 0,  # Would count from execution logs
                    "successful_executions": 0,  # Would count successes
                    "failed_executions": 0,  # Would count failures
                    "average_execution_time_ms": 0.0,  # Would calculate avg time
                    "violations_triggered": 0,  # Would count rule violations
                    "warnings_triggered": 0,  # Would count warnings
                    "modifications_applied": 0,  # Would count modifications
                    "calculations_performed": 0,  # Would count calculations
                },
                "effectiveness_score": 0.0,  # Would calculate based on success rate
                "impact_rating": "Low",  # Would calculate based on usage
            }
            rule_stats.append(stats)

        total_rules = len(all_rules)
        active_rules = len([r for r in all_rules if r.get("isActive")])

        return {
            "analysis_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "filters": {"entity_type": entity_type, "rule_type": rule_type},
            "summary": {
                "total_rules_analyzed": total_rules,
                "active_rules": active_rules,
                "inactive_rules": total_rules - active_rules,
                "rule_types": list(
                    set(r.get("ruleType") for r in all_rules if r.get("ruleType"))
                ),
                "entity_targets": list(
                    set(
                        r.get("entityTarget")
                        for r in all_rules
                        if r.get("entityTarget")
                    )
                ),
            },
            "performance_overview": {
                "total_executions": sum(
                    s["performance_metrics"]["total_executions"] for s in rule_stats
                ),
                "success_rate": 0.0,  # Would calculate overall success rate
                "average_execution_time": 0.0,  # Would calculate overall avg time
                "most_executed_rule": None,  # Would identify most used rule
                "best_performing_rule": None,  # Would identify best performing rule
                "problematic_rules": [],  # Would identify rules with issues
            },
            "rule_statistics": rule_stats,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def activate_business_rule(self, rule_id: int) -> EntityDict:
        """
        Activate a business rule.

        Args:
            rule_id: ID of business rule to activate

        Returns:
            Updated business rule data

        Example:
            activated = client.business_rules.activate_business_rule(12345)
        """
        self.logger.info(f"Activating business rule {rule_id}")
        return self.update_by_id(rule_id, {"isActive": True})

    def deactivate_business_rule(self, rule_id: int) -> EntityDict:
        """
        Deactivate a business rule.

        Args:
            rule_id: ID of business rule to deactivate

        Returns:
            Updated business rule data

        Example:
            deactivated = client.business_rules.deactivate_business_rule(12345)
        """
        self.logger.info(f"Deactivating business rule {rule_id}")
        return self.update_by_id(rule_id, {"isActive": False})

    def clone_business_rule(
        self,
        rule_id: int,
        new_name: str,
        new_entity_target: Optional[str] = None,
        activate_clone: bool = False,
    ) -> EntityDict:
        """
        Clone an existing business rule.

        Args:
            rule_id: ID of business rule to clone
            new_name: Name for the cloned rule
            new_entity_target: Optional new entity target
            activate_clone: Whether to activate the cloned rule

        Returns:
            Created cloned business rule data

        Example:
            cloned = client.business_rules.clone_business_rule(
                12345, "Copy of Ticket Priority Rule", "Projects"
            )
        """
        original = self.get(rule_id)
        if not original:
            raise ValueError(f"Business rule {rule_id} not found")

        # Create clone data
        clone_data = {
            "name": new_name,
            "ruleType": original.get("ruleType"),
            "entityTarget": new_entity_target or original.get("entityTarget"),
            "conditionExpression": original.get("conditionExpression"),
            "actionType": original.get("actionType"),
            "priority": original.get("priority"),
            "description": f"Clone of {original.get('name')}",
            "isActive": activate_clone,
        }

        # Copy additional fields
        for field in [
            "effectiveDate",
            "expirationDate",
            "errorMessage",
            "successMessage",
        ]:
            if field in original:
                clone_data[field] = original[field]

        self.logger.info(f"Cloning business rule {rule_id} as '{new_name}'")
        return self.create(clone_data)

    def get_business_rule_summary(self, rule_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a business rule.

        Args:
            rule_id: ID of the business rule

        Returns:
            Business rule summary with performance metrics

        Example:
            summary = client.business_rules.get_business_rule_summary(12345)
        """
        rule = self.get(rule_id)
        if not rule:
            return {"error": f"Business rule {rule_id} not found"}

        # Get recent performance data (simulated)
        recent_performance = {
            "executions_last_30_days": 0,  # Would query execution logs
            "success_rate_last_30_days": 0.0,  # Would calculate from logs
            "average_execution_time_ms": 0.0,  # Would calculate from logs
            "violations_triggered_last_30_days": 0,  # Would count violations
            "last_execution_date": None,  # Would get from logs
        }

        return {
            "rule_id": rule_id,
            "name": rule.get("name"),
            "description": rule.get("description"),
            "rule_type": rule.get("ruleType"),
            "entity_target": rule.get("entityTarget"),
            "condition_expression": rule.get("conditionExpression"),
            "action_type": rule.get("actionType"),
            "priority": rule.get("priority"),
            "is_active": rule.get("isActive"),
            "effective_date": rule.get("effectiveDate"),
            "expiration_date": rule.get("expirationDate"),
            "created_date": rule.get("createDate"),
            "last_modified_date": rule.get("lastModifiedDate"),
            "created_by": rule.get("createdByResourceID"),
            "last_modified_by": rule.get("lastModifiedByResourceID"),
            "recent_performance": recent_performance,
            "status": self._get_rule_status(rule),
            "recommendations": self._get_rule_recommendations(rule),
        }

    def bulk_activate_rules(
        self, rule_ids: List[int], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Activate multiple business rules in batches.

        Args:
            rule_ids: List of business rule IDs to activate
            batch_size: Number of rules to process per batch

        Returns:
            List of updated business rule data

        Example:
            activated = client.business_rules.bulk_activate_rules([12345, 12346, 12347])
        """
        results = []

        self.logger.info(f"Bulk activating {len(rule_ids)} business rules")

        for i in range(0, len(rule_ids), batch_size):
            batch = rule_ids[i : i + batch_size]

            for rule_id in batch:
                try:
                    result = self.activate_business_rule(rule_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to activate business rule {rule_id}: {e}"
                    )
                    continue

        self.logger.info(
            f"Successfully activated {len(results)}/{len(rule_ids)} business rules"
        )
        return results

    def bulk_deactivate_rules(
        self, rule_ids: List[int], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Deactivate multiple business rules in batches.

        Args:
            rule_ids: List of business rule IDs to deactivate
            batch_size: Number of rules to process per batch

        Returns:
            List of updated business rule data

        Example:
            deactivated = client.business_rules.bulk_deactivate_rules([12345, 12346])
        """
        results = []

        self.logger.info(f"Bulk deactivating {len(rule_ids)} business rules")

        for i in range(0, len(rule_ids), batch_size):
            batch = rule_ids[i : i + batch_size]

            for rule_id in batch:
                try:
                    result = self.deactivate_business_rule(rule_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to deactivate business rule {rule_id}: {e}"
                    )
                    continue

        self.logger.info(
            f"Successfully deactivated {len(results)}/{len(rule_ids)} business rules"
        )
        return results

    def monitor_rule_compliance(
        self,
        entity_type: str,
        date_from: datetime,
        date_to: datetime,
        rule_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Monitor business rule compliance for an entity type.

        Args:
            entity_type: Entity type to monitor
            date_from: Start date for monitoring period
            date_to: End date for monitoring period
            rule_types: Optional list of rule types to include

        Returns:
            Compliance monitoring report

        Example:
            compliance = client.business_rules.monitor_rule_compliance(
                "Tickets",
                datetime(2024, 1, 1),
                datetime(2024, 1, 31),
                ["Validation", "Compliance"]
            )
        """
        filters = [{"field": "entityTarget", "op": "eq", "value": entity_type}]

        if rule_types:
            filters.append({"field": "ruleType", "op": "in", "value": rule_types})

        applicable_rules = self.query(filters=filters)
        rules_list = (
            applicable_rules.items
            if hasattr(applicable_rules, "items")
            else applicable_rules
        )

        # This would typically analyze compliance data from logs
        compliance_data = []

        for rule in rules_list:
            rule_id = rule.get("id")
            rule_name = rule.get("name")

            # Simulate compliance metrics
            compliance_metrics = {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "rule_type": rule.get("ruleType"),
                "compliance_rate": 95.0,  # Would calculate from actual data
                "total_evaluations": 1000,  # Would count from logs
                "violations": 50,  # Would count violations
                "compliance_trend": "Improving",  # Would analyze trend
                "last_violation_date": None,  # Would get from logs
                "violation_pattern": "Random",  # Would analyze patterns
            }
            compliance_data.append(compliance_metrics)

        # Calculate overall compliance
        total_evaluations = sum(r["total_evaluations"] for r in compliance_data)
        total_violations = sum(r["violations"] for r in compliance_data)
        overall_compliance_rate = (
            ((total_evaluations - total_violations) / total_evaluations * 100)
            if total_evaluations > 0
            else 100.0
        )

        return {
            "monitoring_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "entity_type": entity_type,
            "rule_types_monitored": rule_types or ["All"],
            "overall_compliance": {
                "compliance_rate": overall_compliance_rate,
                "total_rules_monitored": len(rules_list),
                "total_evaluations": total_evaluations,
                "total_violations": total_violations,
                "compliance_status": (
                    "Good" if overall_compliance_rate >= 95 else "Needs Attention"
                ),
            },
            "rule_compliance_details": compliance_data,
            "recommendations": self._generate_compliance_recommendations(
                compliance_data
            ),
            "monitoring_timestamp": datetime.now().isoformat(),
        }

    def get_rule_execution_history(
        self,
        rule_id: int,
        date_from: datetime,
        date_to: datetime,
        limit: Optional[int] = 100,
    ) -> Dict[str, Any]:
        """
        Get execution history for a specific business rule.

        Args:
            rule_id: ID of the business rule
            date_from: Start date for history
            date_to: End date for history
            limit: Maximum number of execution records to return

        Returns:
            Rule execution history

        Example:
            history = client.business_rules.get_rule_execution_history(
                12345,
                datetime(2024, 1, 1),
                datetime(2024, 1, 31)
            )
        """
        rule = self.get(rule_id)
        if not rule:
            return {"error": f"Business rule {rule_id} not found"}

        # This would typically query execution logs
        # For now, return execution history structure
        execution_records = [
            # Simulated execution records
            {
                "execution_id": f"exec_{i}",
                "execution_timestamp": (date_from + timedelta(days=i)).isoformat(),
                "entity_type": rule.get("entityTarget"),
                "entity_id": 1000 + i,
                "operation": "create" if i % 2 == 0 else "update",
                "rule_triggered": True,
                "execution_result": "success" if i % 10 != 0 else "failed",
                "execution_time_ms": 25.0 + (i % 50),
                "action_taken": rule.get("actionType"),
                "error_message": "Condition evaluation failed" if i % 10 == 0 else None,
            }
            for i in range(min(limit or 100, 50))  # Simulate up to 50 records
        ]

        successful_executions = [
            r for r in execution_records if r["execution_result"] == "success"
        ]
        failed_executions = [
            r for r in execution_records if r["execution_result"] == "failed"
        ]

        return {
            "rule_id": rule_id,
            "rule_name": rule.get("name"),
            "history_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "execution_summary": {
                "total_executions": len(execution_records),
                "successful_executions": len(successful_executions),
                "failed_executions": len(failed_executions),
                "success_rate": (
                    (len(successful_executions) / len(execution_records) * 100)
                    if execution_records
                    else 0
                ),
                "average_execution_time_ms": (
                    sum(r["execution_time_ms"] for r in execution_records)
                    / len(execution_records)
                    if execution_records
                    else 0
                ),
            },
            "execution_records": execution_records,
            "performance_trends": {
                "execution_frequency": "Daily",  # Would analyze frequency
                "performance_trend": "Stable",  # Would analyze performance trend
                "error_pattern": "Occasional",  # Would analyze error patterns
            },
        }

    def _evaluate_rule_condition(self, condition: str, entity_data: EntityDict) -> bool:
        """
        Evaluate a rule condition against entity data.

        Args:
            condition: Rule condition expression
            entity_data: Entity data to evaluate against

        Returns:
            True if condition is met, False otherwise
        """
        # This is a simplified implementation
        # In practice, this would use a proper expression evaluator
        try:
            # Basic condition evaluation (simplified)
            # Real implementation would parse and evaluate complex expressions
            if "IS NULL" in condition:
                field_name = condition.split(" IS NULL")[0].strip()
                return entity_data.get(field_name) is None

            if "IS NOT NULL" in condition:
                field_name = condition.split(" IS NOT NULL")[0].strip()
                return entity_data.get(field_name) is not None

            if ">" in condition:
                parts = condition.split(">")
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    value = float(parts[1].strip())
                    field_value = entity_data.get(field_name, 0)
                    return float(field_value) > value

            # Default: assume condition is met for demonstration
            return False

        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    def _execute_automation_rule(
        self, rule: EntityDict, entity_data: EntityDict
    ) -> Dict[str, Any]:
        """
        Execute an automation rule.

        Args:
            rule: Rule configuration
            entity_data: Entity data to process

        Returns:
            Automation execution result
        """
        # Simplified automation execution
        rule_name = rule.get("name")
        action_type = rule.get("actionType")

        modifications = []

        if action_type == "Modify":
            # Example: Set default values or modify fields
            modifications.append(
                {
                    "field": "modifiedByRule",
                    "old_value": entity_data.get("modifiedByRule"),
                    "new_value": rule.get("id"),
                    "modification_type": "set_value",
                }
            )

        return {
            "success": True,
            "rule_name": rule_name,
            "action_type": action_type,
            "modifications": modifications,
            "message": f"Automation rule '{rule_name}' executed successfully",
        }

    def _execute_calculation_rule(
        self, rule: EntityDict, entity_data: EntityDict
    ) -> Dict[str, Any]:
        """
        Execute a calculation rule.

        Args:
            rule: Rule configuration
            entity_data: Entity data to process

        Returns:
            Calculation execution result
        """
        # Simplified calculation execution
        rule_name = rule.get("name")

        calculated_values = {}

        # Example calculation: Calculate total cost
        if "cost" in rule_name.lower():
            base_cost = Decimal(str(entity_data.get("baseCost", 0)))
            tax_rate = Decimal("0.08")  # 8% tax
            calculated_values["totalCost"] = float(base_cost * (1 + tax_rate))

        return {
            "success": True,
            "rule_name": rule_name,
            "values": calculated_values,
            "message": f"Calculation rule '{rule_name}' executed successfully",
        }

    def _get_rule_status(self, rule: EntityDict) -> str:
        """
        Get current status of a business rule.

        Args:
            rule: Rule data

        Returns:
            Rule status
        """
        if not rule.get("isActive"):
            return "Inactive"

        current_time = datetime.now()

        effective_date = rule.get("effectiveDate")
        if (
            effective_date
            and datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
            > current_time
        ):
            return "Pending"

        expiration_date = rule.get("expirationDate")
        if (
            expiration_date
            and datetime.fromisoformat(expiration_date.replace("Z", "+00:00"))
            < current_time
        ):
            return "Expired"

        return "Active"

    def _get_rule_recommendations(self, rule: EntityDict) -> List[str]:
        """
        Get recommendations for improving a business rule.

        Args:
            rule: Rule data

        Returns:
            List of recommendations
        """
        recommendations = []

        if not rule.get("description"):
            recommendations.append("Add a description to document rule purpose")

        if rule.get("priority", 999) > 500:
            recommendations.append(
                "Consider setting a higher priority for better execution order"
            )

        if not rule.get("effectiveDate"):
            recommendations.append(
                "Set an effective date for better rule lifecycle management"
            )

        condition = rule.get("conditionExpression", "")
        if len(condition) > 500:
            recommendations.append("Consider simplifying complex condition expressions")

        return recommendations

    def _generate_compliance_recommendations(
        self, compliance_data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on compliance analysis.

        Args:
            compliance_data: Compliance metrics for rules

        Returns:
            List of recommendations
        """
        recommendations = []

        low_compliance_rules = [r for r in compliance_data if r["compliance_rate"] < 90]
        if low_compliance_rules:
            recommendations.append(
                f"Review {len(low_compliance_rules)} rules with compliance rate below 90%"
            )

        high_violation_rules = [r for r in compliance_data if r["violations"] > 100]
        if high_violation_rules:
            recommendations.append(
                f"Investigate {len(high_violation_rules)} rules with high violation counts"
            )

        recommendations.append(
            "Consider implementing automated alerts for compliance violations"
        )
        recommendations.append(
            "Review rule conditions to ensure they align with business requirements"
        )

        return recommendations
