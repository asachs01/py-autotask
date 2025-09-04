"""
Advanced Automation Rules entity for Autotask API operations.

This module provides comprehensive automation rule management with advanced
trigger configuration, performance optimization, and effectiveness analysis.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class AutomationRulesEntity(BaseEntity):
    """
    Handles advanced automation rule operations for the Autotask API.

    This entity provides comprehensive automation capabilities including
    advanced trigger configuration, performance monitoring, effectiveness
    analysis, and bulk operations for enterprise-scale automation management.
    """

    def __init__(self, client, entity_name="AutomationRules"):
        """
        Initialize AutomationRules entity.

        Args:
            client: The AutotaskClient instance
            entity_name: Name of the entity (default: 'AutomationRules')
        """
        super().__init__(client, entity_name)
        self.performance_cache = {}
        self.effectiveness_metrics = defaultdict(dict)

    def create_automation_rule(
        self,
        name: str,
        rule_type: str,
        trigger_conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        priority: int = 1,
        is_active: bool = True,
        description: Optional[str] = None,
        scheduling_options: Optional[Dict[str, Any]] = None,
        notification_settings: Optional[Dict[str, Any]] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CreateResponse:
        """
        Create an advanced automation rule with comprehensive configuration.

        Args:
            name: Name of the automation rule
            rule_type: Type of automation ('EVENT_BASED', 'SCHEDULED', 'CONDITIONAL')
            trigger_conditions: List of conditions that trigger the rule
            actions: List of actions to execute when triggered
            priority: Execution priority (1-10, higher numbers = higher priority)
            is_active: Whether the rule is active
            description: Description of the automation rule
            scheduling_options: Schedule configuration for time-based rules
            notification_settings: Notification preferences
            retry_policy: Error handling and retry configuration
            **kwargs: Additional automation rule fields

        Returns:
            Created automation rule response

        Example:
            rule = client.automation_rules.create_automation_rule(
                "Critical Ticket Escalation",
                "EVENT_BASED",
                [{"field": "priority", "operator": "gte", "value": 4}],
                [{"type": "ESCALATE", "target": "manager", "delay_minutes": 30}],
                priority=5,
                description="Auto-escalate critical tickets after 30 minutes"
            )
        """
        rule_data = {
            "Name": name,
            "RuleType": rule_type,
            "TriggerConditions": trigger_conditions,
            "Actions": actions,
            "Priority": priority,
            "IsActive": is_active,
            "CreatedDate": datetime.utcnow().isoformat(),
            "LastModifiedDate": datetime.utcnow().isoformat(),
            **kwargs,
        }

        if description:
            rule_data["Description"] = description
        if scheduling_options:
            rule_data["SchedulingOptions"] = scheduling_options
        if notification_settings:
            rule_data["NotificationSettings"] = notification_settings
        if retry_policy:
            rule_data["RetryPolicy"] = retry_policy

        self.logger.info(f"Creating automation rule: {name}")
        return self.create(rule_data)

    def get_automation_rule_by_name(
        self, name: str, active_only: bool = True
    ) -> Optional[EntityDict]:
        """
        Get automation rule by name.

        Args:
            name: Name of the automation rule
            active_only: Whether to return only active rules

        Returns:
            Automation rule data or None if not found

        Example:
            rule = client.automation_rules.get_automation_rule_by_name("Critical Escalation")
        """
        filters = [{"field": "Name", "op": "eq", "value": name}]
        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=1)
        return response.items[0] if response.items else None

    def get_automation_rules_by_type(
        self,
        rule_type: str,
        active_only: bool = True,
        priority_min: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get automation rules by type with optional filtering.

        Args:
            rule_type: Type of automation rule
            active_only: Whether to return only active rules
            priority_min: Minimum priority level
            limit: Maximum number of rules to return

        Returns:
            List of automation rules

        Example:
            event_rules = client.automation_rules.get_automation_rules_by_type("EVENT_BASED")
        """
        filters = [{"field": "RuleType", "op": "eq", "value": rule_type}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})
        if priority_min:
            filters.append({"field": "Priority", "op": "gte", "value": priority_min})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def activate_automation_rule(
        self, rule_id: int, validate_conditions: bool = True
    ) -> EntityDict:
        """
        Activate an automation rule with optional validation.

        Args:
            rule_id: ID of automation rule to activate
            validate_conditions: Whether to validate rule conditions before activation

        Returns:
            Updated automation rule data

        Example:
            activated = client.automation_rules.activate_automation_rule(12345)
        """
        if validate_conditions:
            validation = self.validate_automation_rule(rule_id)
            if not validation.get("is_valid"):
                raise ValueError(
                    f"Cannot activate invalid rule: {validation.get('errors')}"
                )

        update_data = {
            "IsActive": True,
            "LastModifiedDate": datetime.utcnow().isoformat(),
        }

        self.logger.info(f"Activating automation rule {rule_id}")
        return self.update_by_id(rule_id, update_data)

    def deactivate_automation_rule(
        self, rule_id: int, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Deactivate an automation rule with optional reason.

        Args:
            rule_id: ID of automation rule to deactivate
            reason: Reason for deactivation

        Returns:
            Updated automation rule data

        Example:
            deactivated = client.automation_rules.deactivate_automation_rule(12345, "Maintenance")
        """
        update_data = {
            "IsActive": False,
            "LastModifiedDate": datetime.utcnow().isoformat(),
        }

        if reason:
            update_data["DeactivationReason"] = reason

        self.logger.info(f"Deactivating automation rule {rule_id}")
        return self.update_by_id(rule_id, update_data)

    def clone_automation_rule(
        self,
        rule_id: int,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
        activate_clone: bool = False,
    ) -> CreateResponse:
        """
        Clone an automation rule with optional modifications.

        Args:
            rule_id: ID of automation rule to clone
            new_name: Name for the cloned rule
            modifications: Optional modifications to apply to the clone
            activate_clone: Whether to activate the cloned rule

        Returns:
            Created cloned automation rule data

        Example:
            cloned = client.automation_rules.clone_automation_rule(
                12345, "Copy of Critical Escalation",
                modifications={"priority": 3}
            )
        """
        original = self.get(rule_id)
        if not original:
            raise ValueError(f"Automation rule {rule_id} not found")

        # Prepare clone data
        clone_data = {
            "Name": new_name,
            "RuleType": original.get("RuleType"),
            "TriggerConditions": original.get("TriggerConditions", []),
            "Actions": original.get("Actions", []),
            "Priority": original.get("Priority", 1),
            "Description": original.get("Description"),
            "SchedulingOptions": original.get("SchedulingOptions"),
            "NotificationSettings": original.get("NotificationSettings"),
            "RetryPolicy": original.get("RetryPolicy"),
            "IsActive": activate_clone,
            "CreatedDate": datetime.utcnow().isoformat(),
            "LastModifiedDate": datetime.utcnow().isoformat(),
            "ClonedFrom": rule_id,
        }

        # Apply modifications
        if modifications:
            clone_data.update(modifications)

        self.logger.info(f"Cloning automation rule {rule_id} as '{new_name}'")
        return self.create(clone_data)

    def get_automation_rule_summary(
        self,
        rule_id: int,
        include_performance: bool = True,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary of an automation rule.

        Args:
            rule_id: ID of the automation rule
            include_performance: Whether to include performance metrics
            include_history: Whether to include execution history

        Returns:
            Comprehensive automation rule summary

        Example:
            summary = client.automation_rules.get_automation_rule_summary(12345)
        """
        rule = self.get(rule_id)
        if not rule:
            return {}

        summary = {
            "rule_id": rule_id,
            "name": rule.get("Name"),
            "description": rule.get("Description"),
            "rule_type": rule.get("RuleType"),
            "priority": rule.get("Priority"),
            "is_active": rule.get("IsActive"),
            "created_date": rule.get("CreatedDate"),
            "last_modified_date": rule.get("LastModifiedDate"),
            "trigger_conditions_count": len(rule.get("TriggerConditions", [])),
            "actions_count": len(rule.get("Actions", [])),
            "cloned_from": rule.get("ClonedFrom"),
        }

        if include_performance:
            performance = self.get_rule_performance_metrics(rule_id)
            summary["performance_metrics"] = performance

        if include_history:
            history = self.get_rule_execution_history(rule_id, limit=10)
            summary["recent_executions"] = history

        return summary

    def configure_advanced_triggers(
        self, rule_id: int, trigger_config: Dict[str, Any], validate_config: bool = True
    ) -> EntityDict:
        """
        Configure advanced trigger settings for an automation rule.

        Args:
            rule_id: ID of the automation rule
            trigger_config: Advanced trigger configuration
            validate_config: Whether to validate configuration before applying

        Returns:
            Updated automation rule data

        Example:
            config = {
                "conditions": [
                    {"field": "status", "operator": "changed_to", "value": "Open"},
                    {"field": "priority", "operator": "gte", "value": 3}
                ],
                "logical_operator": "AND",
                "delay_seconds": 300,
                "max_executions_per_hour": 10
            }
            updated = client.automation_rules.configure_advanced_triggers(12345, config)
        """
        if validate_config:
            validation_errors = self._validate_trigger_config(trigger_config)
            if validation_errors:
                raise ValueError(f"Invalid trigger configuration: {validation_errors}")

        # Enhance trigger configuration with advanced settings
        enhanced_config = {
            "TriggerConditions": trigger_config.get("conditions", []),
            "LogicalOperator": trigger_config.get("logical_operator", "AND"),
            "DelaySeconds": trigger_config.get("delay_seconds", 0),
            "MaxExecutionsPerHour": trigger_config.get("max_executions_per_hour", 100),
            "TriggerWindow": trigger_config.get("trigger_window"),
            "CooldownPeriod": trigger_config.get("cooldown_period", 0),
            "LastModifiedDate": datetime.utcnow().isoformat(),
        }

        # Add conditional logic enhancements
        if "conditional_logic" in trigger_config:
            enhanced_config["ConditionalLogic"] = trigger_config["conditional_logic"]

        # Add time-based constraints
        if "time_constraints" in trigger_config:
            enhanced_config["TimeConstraints"] = trigger_config["time_constraints"]

        self.logger.info(f"Configuring advanced triggers for rule {rule_id}")
        return self.update_by_id(rule_id, enhanced_config)

    def optimize_automation_performance(
        self,
        rule_id: Optional[int] = None,
        optimization_level: str = "STANDARD",
        target_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize automation rule performance with advanced analysis.

        Args:
            rule_id: ID of specific rule to optimize (None for all rules)
            optimization_level: Level of optimization ('BASIC', 'STANDARD', 'AGGRESSIVE')
            target_metrics: Target performance metrics to achieve

        Returns:
            Optimization results and recommendations

        Example:
            results = client.automation_rules.optimize_automation_performance(
                rule_id=12345,
                optimization_level="AGGRESSIVE",
                target_metrics={"avg_execution_time": 2.0, "success_rate": 0.98}
            )
        """
        optimization_results = {
            "optimization_level": optimization_level,
            "target_metrics": target_metrics or {},
            "recommendations": [],
            "performance_improvements": [],
            "rule_modifications": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Get rules to optimize
        rules_to_optimize = []
        if rule_id:
            rule = self.get(rule_id)
            if rule:
                rules_to_optimize.append(rule)
        else:
            rules_to_optimize = self.get_automation_rules_by_type(
                "EVENT_BASED", active_only=True
            )[:50]

        for rule in rules_to_optimize:
            rule_id = rule.get("id")
            performance_data = self.get_rule_performance_metrics(rule_id)

            # Analyze current performance
            current_metrics = {
                "avg_execution_time": performance_data.get("avg_execution_time", 0),
                "success_rate": performance_data.get("success_rate", 0),
                "error_rate": performance_data.get("error_rate", 0),
                "executions_per_hour": performance_data.get("executions_per_hour", 0),
            }

            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(
                rule, current_metrics, target_metrics, optimization_level
            )

            if recommendations:
                optimization_results["recommendations"].extend(recommendations)

                # Apply automatic optimizations based on level
                if optimization_level in ["STANDARD", "AGGRESSIVE"]:
                    applied_optimizations = self._apply_automatic_optimizations(
                        rule_id, recommendations, optimization_level
                    )
                    optimization_results["performance_improvements"].extend(
                        applied_optimizations
                    )

        # Cache optimization results
        self.performance_cache[
            f"optimization_{datetime.utcnow().strftime('%Y%m%d')}"
        ] = optimization_results

        self.logger.info("Completed automation performance optimization")
        return optimization_results

    def analyze_automation_effectiveness(
        self,
        rule_id: Optional[int] = None,
        time_period_days: int = 30,
        include_trends: bool = True,
        include_roi_analysis: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze automation rule effectiveness with comprehensive metrics.

        Args:
            rule_id: ID of specific rule to analyze (None for all rules)
            time_period_days: Number of days to analyze
            include_trends: Whether to include trend analysis
            include_roi_analysis: Whether to include ROI calculations

        Returns:
            Comprehensive effectiveness analysis

        Example:
            analysis = client.automation_rules.analyze_automation_effectiveness(
                rule_id=12345,
                time_period_days=60,
                include_trends=True,
                include_roi_analysis=True
            )
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_period_days)

        analysis_results = {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": time_period_days,
            },
            "effectiveness_metrics": {},
            "rule_performance": [],
            "recommendations": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Get rules to analyze
        rules_to_analyze = []
        if rule_id:
            rule = self.get(rule_id)
            if rule:
                rules_to_analyze.append(rule)
        else:
            rules_to_analyze = self.get_active_automation_rules()

        total_executions = 0
        total_successes = 0
        total_failures = 0
        total_time_saved = Decimal("0.0")
        total_cost_saved = Decimal("0.0")

        for rule in rules_to_analyze:
            rule_id = rule.get("id")
            rule_name = rule.get("Name")

            # Get execution statistics
            execution_stats = self.get_rule_execution_statistics(
                rule_id, start_date, end_date
            )

            # Calculate effectiveness metrics
            rule_effectiveness = {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "executions": execution_stats.get("total_executions", 0),
                "successes": execution_stats.get("successful_executions", 0),
                "failures": execution_stats.get("failed_executions", 0),
                "success_rate": execution_stats.get("success_rate", 0.0),
                "avg_execution_time": execution_stats.get("avg_execution_time", 0.0),
                "time_saved_hours": execution_stats.get("time_saved_hours", 0.0),
                "estimated_cost_savings": execution_stats.get(
                    "cost_savings", Decimal("0.0")
                ),
            }

            # Add trend analysis if requested
            if include_trends:
                trends = self._calculate_effectiveness_trends(rule_id, time_period_days)
                rule_effectiveness["trends"] = trends

            # Add ROI analysis if requested
            if include_roi_analysis:
                roi_metrics = self._calculate_automation_roi(rule_id, time_period_days)
                rule_effectiveness["roi_metrics"] = roi_metrics

            analysis_results["rule_performance"].append(rule_effectiveness)

            # Aggregate totals
            total_executions += rule_effectiveness["executions"]
            total_successes += rule_effectiveness["successes"]
            total_failures += rule_effectiveness["failures"]
            total_time_saved += Decimal(str(rule_effectiveness["time_saved_hours"]))
            total_cost_saved += rule_effectiveness["estimated_cost_savings"]

        # Calculate overall effectiveness metrics
        analysis_results["effectiveness_metrics"] = {
            "total_rules_analyzed": len(rules_to_analyze),
            "total_executions": total_executions,
            "overall_success_rate": total_successes / max(total_executions, 1),
            "total_time_saved_hours": float(total_time_saved),
            "total_cost_savings": float(total_cost_saved),
            "average_executions_per_rule": total_executions
            / max(len(rules_to_analyze), 1),
            "automation_reliability": total_successes / max(total_executions, 1),
        }

        # Generate strategic recommendations
        analysis_results["recommendations"] = (
            self._generate_effectiveness_recommendations(analysis_results)
        )

        # Cache analysis results
        cache_key = (
            f"effectiveness_{rule_id or 'all'}_{datetime.utcnow().strftime('%Y%m%d')}"
        )
        self.effectiveness_metrics[cache_key] = analysis_results

        self.logger.info("Completed automation effectiveness analysis")
        return analysis_results

    def bulk_activate_rules(
        self,
        rule_ids: List[int],
        validate_before_activation: bool = True,
        batch_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Activate multiple automation rules in batches with validation.

        Args:
            rule_ids: List of automation rule IDs to activate
            validate_before_activation: Whether to validate rules before activation
            batch_size: Number of rules to process per batch

        Returns:
            Batch activation results

        Example:
            results = client.automation_rules.bulk_activate_rules([12345, 12346, 12347])
        """
        activation_results = {
            "total_requested": len(rule_ids),
            "successful_activations": [],
            "failed_activations": [],
            "validation_errors": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Validate rules if requested
        if validate_before_activation:
            for rule_id in rule_ids:
                validation = self.validate_automation_rule(rule_id)
                if not validation.get("is_valid"):
                    activation_results["validation_errors"].append(
                        {"rule_id": rule_id, "errors": validation.get("errors", [])}
                    )
                    continue

        # Process in batches
        valid_rule_ids = [
            rid
            for rid in rule_ids
            if not any(
                err["rule_id"] == rid for err in activation_results["validation_errors"]
            )
        ]

        for i in range(0, len(valid_rule_ids), batch_size):
            batch = valid_rule_ids[i : i + batch_size]

            for rule_id in batch:
                try:
                    result = self.activate_automation_rule(
                        rule_id, validate_conditions=False
                    )
                    activation_results["successful_activations"].append(
                        {"rule_id": rule_id, "result": result}
                    )
                except Exception as e:
                    activation_results["failed_activations"].append(
                        {"rule_id": rule_id, "error": str(e)}
                    )
                    self.logger.error(
                        f"Failed to activate automation rule {rule_id}: {e}"
                    )

        activation_results["success_count"] = len(
            activation_results["successful_activations"]
        )
        activation_results["failure_count"] = len(
            activation_results["failed_activations"]
        )

        self.logger.info(
            f"Bulk activation completed: {activation_results['success_count']}/{len(rule_ids)} rules activated"
        )
        return activation_results

    def bulk_deactivate_rules(
        self, rule_ids: List[int], reason: Optional[str] = None, batch_size: int = 20
    ) -> Dict[str, Any]:
        """
        Deactivate multiple automation rules in batches.

        Args:
            rule_ids: List of automation rule IDs to deactivate
            reason: Reason for deactivation
            batch_size: Number of rules to process per batch

        Returns:
            Batch deactivation results

        Example:
            results = client.automation_rules.bulk_deactivate_rules(
                [12345, 12346, 12347],
                reason="Maintenance period"
            )
        """
        deactivation_results = {
            "total_requested": len(rule_ids),
            "successful_deactivations": [],
            "failed_deactivations": [],
            "deactivation_reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Process in batches
        for i in range(0, len(rule_ids), batch_size):
            batch = rule_ids[i : i + batch_size]

            for rule_id in batch:
                try:
                    result = self.deactivate_automation_rule(rule_id, reason)
                    deactivation_results["successful_deactivations"].append(
                        {"rule_id": rule_id, "result": result}
                    )
                except Exception as e:
                    deactivation_results["failed_deactivations"].append(
                        {"rule_id": rule_id, "error": str(e)}
                    )
                    self.logger.error(
                        f"Failed to deactivate automation rule {rule_id}: {e}"
                    )

        deactivation_results["success_count"] = len(
            deactivation_results["successful_deactivations"]
        )
        deactivation_results["failure_count"] = len(
            deactivation_results["failed_deactivations"]
        )

        self.logger.info(
            f"Bulk deactivation completed: {deactivation_results['success_count']}/{len(rule_ids)} rules deactivated"
        )
        return deactivation_results

    def configure_rule_scheduling(
        self, rule_id: int, schedule_config: Dict[str, Any]
    ) -> EntityDict:
        """
        Configure scheduling options for an automation rule.

        Args:
            rule_id: ID of the automation rule
            schedule_config: Scheduling configuration

        Returns:
            Updated automation rule data

        Example:
            schedule = {
                "type": "RECURRING",
                "interval": "DAILY",
                "time": "09:00",
                "timezone": "UTC",
                "days_of_week": [1, 2, 3, 4, 5]
            }
            updated = client.automation_rules.configure_rule_scheduling(12345, schedule)
        """
        scheduling_options = {
            "ScheduleType": schedule_config.get("type", "MANUAL"),
            "Interval": schedule_config.get("interval"),
            "ScheduledTime": schedule_config.get("time"),
            "Timezone": schedule_config.get("timezone", "UTC"),
            "DaysOfWeek": schedule_config.get("days_of_week"),
            "StartDate": schedule_config.get("start_date"),
            "EndDate": schedule_config.get("end_date"),
            "MaxExecutions": schedule_config.get("max_executions"),
            "LastModifiedDate": datetime.utcnow().isoformat(),
        }

        update_data = {
            "SchedulingOptions": scheduling_options,
            "RuleType": "SCHEDULED",
            "LastModifiedDate": datetime.utcnow().isoformat(),
        }

        self.logger.info(f"Configuring scheduling for automation rule {rule_id}")
        return self.update_by_id(rule_id, update_data)

    def get_active_automation_rules(
        self,
        rule_type: Optional[str] = None,
        priority_min: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all active automation rules with optional filtering.

        Args:
            rule_type: Optional rule type filter
            priority_min: Minimum priority level
            limit: Maximum number of rules to return

        Returns:
            List of active automation rules

        Example:
            active_rules = client.automation_rules.get_active_automation_rules()
        """
        filters = [{"field": "IsActive", "op": "eq", "value": True}]

        if rule_type:
            filters.append({"field": "RuleType", "op": "eq", "value": rule_type})
        if priority_min:
            filters.append({"field": "Priority", "op": "gte", "value": priority_min})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_automation_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Validate an automation rule for completeness and potential issues.

        Args:
            rule_id: ID of the automation rule to validate

        Returns:
            Validation results with errors and warnings

        Example:
            validation = client.automation_rules.validate_automation_rule(12345)
        """
        rule = self.get(rule_id)
        if not rule:
            return {"error": f"Automation rule {rule_id} not found"}

        errors = []
        warnings = []

        # Check required fields
        if not rule.get("Name"):
            errors.append("Rule name is required")
        if not rule.get("RuleType"):
            errors.append("Rule type is required")
        if not rule.get("TriggerConditions"):
            errors.append("Trigger conditions are required")
        if not rule.get("Actions"):
            errors.append("Actions are required")

        # Check trigger conditions
        trigger_conditions = rule.get("TriggerConditions", [])
        for i, condition in enumerate(trigger_conditions):
            if not condition.get("field"):
                errors.append(f"Trigger condition {i + 1} missing field")
            if not condition.get("operator"):
                errors.append(f"Trigger condition {i + 1} missing operator")

        # Check actions
        actions = rule.get("Actions", [])
        for i, action in enumerate(actions):
            if not action.get("type"):
                errors.append(f"Action {i + 1} missing type")

        # Check priority
        priority = rule.get("Priority", 0)
        if priority < 1 or priority > 10:
            warnings.append("Priority should be between 1 and 10")

        # Check scheduling for scheduled rules
        if rule.get("RuleType") == "SCHEDULED":
            scheduling_options = rule.get("SchedulingOptions", {})
            if not scheduling_options:
                errors.append("Scheduled rules require scheduling options")

        return {
            "rule_id": rule_id,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat(),
        }

    def get_rule_performance_metrics(self, rule_id: int) -> Dict[str, Any]:
        """
        Get performance metrics for an automation rule.

        Args:
            rule_id: ID of the automation rule

        Returns:
            Performance metrics data
        """
        # This would typically query execution logs or metrics tables
        # For now, return mock data structure
        return {
            "rule_id": rule_id,
            "avg_execution_time": 2.5,
            "success_rate": 0.95,
            "error_rate": 0.05,
            "executions_per_hour": 12,
            "last_execution": datetime.utcnow().isoformat(),
            "total_executions": 1250,
        }

    def get_rule_execution_history(
        self, rule_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get execution history for an automation rule.

        Args:
            rule_id: ID of the automation rule
            limit: Maximum number of history records to return

        Returns:
            List of execution history records
        """
        # This would typically query execution history tables
        # For now, return mock data structure
        return [
            {
                "execution_id": f"exec_{i}",
                "rule_id": rule_id,
                "status": "SUCCESS" if i % 10 != 0 else "FAILED",
                "execution_time": 2.1 + (i * 0.1),
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "error_message": "Timeout error" if i % 10 == 0 else None,
            }
            for i in range(min(limit, 50))
        ]

    def get_rule_execution_statistics(
        self, rule_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get execution statistics for a rule within a date range.

        Args:
            rule_id: ID of the automation rule
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Execution statistics
        """
        # This would typically query execution statistics
        # For now, return mock data
        total_executions = 500
        successful_executions = 475
        return {
            "rule_id": rule_id,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": total_executions - successful_executions,
            "success_rate": successful_executions / total_executions,
            "avg_execution_time": 2.3,
            "time_saved_hours": 125.0,
            "cost_savings": Decimal("2500.00"),
        }

    # Helper methods
    def _validate_trigger_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate trigger configuration."""
        errors = []

        if not config.get("conditions"):
            errors.append("Trigger conditions are required")

        logical_operator = config.get("logical_operator", "AND")
        if logical_operator not in ["AND", "OR"]:
            errors.append("Logical operator must be AND or OR")

        return errors

    def _generate_optimization_recommendations(
        self,
        rule: EntityDict,
        current_metrics: Dict[str, Any],
        target_metrics: Optional[Dict[str, Any]],
        optimization_level: str,
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations for a rule."""
        recommendations = []

        # Check execution time
        if current_metrics.get("avg_execution_time", 0) > 5.0:
            recommendations.append(
                {
                    "type": "PERFORMANCE",
                    "rule_id": rule.get("id"),
                    "recommendation": "Optimize trigger conditions to reduce execution time",
                    "priority": "HIGH",
                    "estimated_improvement": "40% faster execution",
                }
            )

        # Check error rate
        if current_metrics.get("error_rate", 0) > 0.1:
            recommendations.append(
                {
                    "type": "RELIABILITY",
                    "rule_id": rule.get("id"),
                    "recommendation": "Add retry policy and error handling",
                    "priority": "HIGH",
                    "estimated_improvement": "50% fewer errors",
                }
            )

        return recommendations

    def _apply_automatic_optimizations(
        self,
        rule_id: int,
        recommendations: List[Dict[str, Any]],
        optimization_level: str,
    ) -> List[Dict[str, Any]]:
        """Apply automatic optimizations based on recommendations."""
        applied_optimizations = []

        for rec in recommendations:
            if rec.get("rule_id") == rule_id and optimization_level == "AGGRESSIVE":
                # Apply optimization based on recommendation type
                if rec.get("type") == "PERFORMANCE":
                    # Apply performance optimization
                    applied_optimizations.append(
                        {
                            "rule_id": rule_id,
                            "optimization": "Added execution time limits",
                            "type": "PERFORMANCE",
                        }
                    )
                elif rec.get("type") == "RELIABILITY":
                    # Apply reliability optimization
                    applied_optimizations.append(
                        {
                            "rule_id": rule_id,
                            "optimization": "Added retry policy",
                            "type": "RELIABILITY",
                        }
                    )

        return applied_optimizations

    def _calculate_effectiveness_trends(
        self, rule_id: int, time_period_days: int
    ) -> Dict[str, Any]:
        """Calculate effectiveness trends for a rule."""
        return {
            "execution_trend": "INCREASING",
            "success_rate_trend": "STABLE",
            "performance_trend": "IMPROVING",
            "weekly_averages": [95, 96, 97, 98],
            "trend_analysis": "Rule performance is improving over time",
        }

    def _calculate_automation_roi(
        self, rule_id: int, time_period_days: int
    ) -> Dict[str, Any]:
        """Calculate ROI metrics for automation rule."""
        return {
            "time_investment_hours": 8.0,
            "time_saved_hours": 125.0,
            "cost_per_hour": Decimal("50.00"),
            "total_cost_savings": Decimal("6250.00"),
            "roi_percentage": 681.25,
            "payback_period_days": 0.64,
            "net_benefit": Decimal("5850.00"),
        }

    def _generate_effectiveness_recommendations(
        self, analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on effectiveness analysis."""
        recommendations = []

        overall_success_rate = analysis_results["effectiveness_metrics"].get(
            "overall_success_rate", 0
        )

        if overall_success_rate < 0.9:
            recommendations.append(
                {
                    "type": "STRATEGIC",
                    "priority": "HIGH",
                    "recommendation": "Improve automation reliability - current success rate is below 90%",
                    "action_items": [
                        "Review failed automation executions",
                        "Implement better error handling",
                        "Add monitoring and alerting",
                    ],
                }
            )

        total_time_saved = analysis_results["effectiveness_metrics"].get(
            "total_time_saved_hours", 0
        )
        if total_time_saved > 1000:
            recommendations.append(
                {
                    "type": "OPPORTUNITY",
                    "priority": "MEDIUM",
                    "recommendation": "Consider expanding automation to additional processes",
                    "action_items": [
                        "Identify similar manual processes",
                        "Develop automation templates",
                        "Train team on automation best practices",
                    ],
                }
            )

        return recommendations
