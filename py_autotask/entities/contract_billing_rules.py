"""
ContractBillingRules Entity for py-autotask

This module provides the ContractBillingRulesEntity class for managing contract billing rules
in Autotask. Contract billing rules define how billing is calculated and applied for specific
contracts, including billing frequency, rate calculations, and billing code applications.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractBillingRulesEntity(BaseEntity):
    """
    Manages Autotask ContractBillingRules - rules that govern contract billing behavior.

    Contract billing rules define how billing is calculated for contracts, including
    rate structures, billing frequencies, markup calculations, and special billing
    conditions that apply to specific contracts or contract types.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractBillingRules"

    # Core CRUD Operations

    def create_billing_rule(
        self,
        contract_id: int,
        rule_name: str,
        billing_code_id: int,
        rate_type: str,
        rate_amount: Union[float, Decimal],
        billing_frequency: str = "Monthly",
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract billing rule.

        Args:
            contract_id: ID of the contract
            rule_name: Name of the billing rule
            billing_code_id: ID of the associated billing code
            rate_type: Type of rate calculation (Fixed, Hourly, etc.)
            rate_amount: The rate amount
            billing_frequency: How often to apply the rule
            effective_date: When the rule becomes effective
            **kwargs: Additional fields for the billing rule

        Returns:
            Create response with new billing rule ID

        Example:
            rule = client.contract_billing_rules.create_billing_rule(
                contract_id=12345,
                rule_name="Monthly Monitoring",
                billing_code_id=678,
                rate_type="Fixed",
                rate_amount=299.00
            )
        """
        if effective_date is None:
            effective_date = date.today()

        rule_data = {
            "contractID": contract_id,
            "ruleName": rule_name,
            "billingCodeID": billing_code_id,
            "rateType": rate_type,
            "rateAmount": float(rate_amount),
            "billingFrequency": billing_frequency,
            "effectiveDate": effective_date.isoformat(),
            **kwargs,
        }

        return self.create(rule_data)

    def get_billing_rules_by_contract(
        self,
        contract_id: int,
        active_only: bool = True,
        effective_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing rules for a specific contract.

        Args:
            contract_id: ID of the contract
            active_only: Whether to return only active rules
            effective_date: Filter by effective date

        Returns:
            List of contract billing rules
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        if effective_date:
            filters.append(
                {
                    "field": "effectiveDate",
                    "op": "lte",
                    "value": effective_date.isoformat(),
                }
            )

        return self.query(filters=filters).items

    def get_rules_by_billing_code(self, billing_code_id: int) -> List[Dict[str, Any]]:
        """
        Get all billing rules that use a specific billing code.

        Args:
            billing_code_id: ID of the billing code

        Returns:
            List of billing rules using the billing code
        """
        filters = [{"field": "billingCodeID", "op": "eq", "value": billing_code_id}]
        return self.query(filters=filters).items

    # Business Logic Methods

    def calculate_billing_amount(
        self,
        rule_id: int,
        quantity: Union[float, Decimal],
        time_period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate billing amount based on rule and quantity.

        Args:
            rule_id: ID of the billing rule
            quantity: Quantity to calculate for
            time_period: Time period for calculation

        Returns:
            Calculated billing amount and details
        """
        rule = self.get(rule_id)
        if not rule:
            raise ValueError(f"Billing rule {rule_id} not found")

        rate_amount = Decimal(str(rule.get("rateAmount", 0)))
        quantity = Decimal(str(quantity))
        rate_type = rule.get("rateType", "Fixed")

        if rate_type == "Fixed":
            total_amount = rate_amount
            unit_amount = rate_amount
        elif rate_type == "Hourly":
            total_amount = rate_amount * quantity
            unit_amount = rate_amount
        elif rate_type == "Percentage":
            base_amount = quantity
            total_amount = base_amount * (rate_amount / 100)
            unit_amount = rate_amount / 100
        else:
            total_amount = rate_amount * quantity
            unit_amount = rate_amount

        return {
            "rule_id": rule_id,
            "rule_name": rule.get("ruleName"),
            "rate_type": rate_type,
            "rate_amount": rate_amount,
            "quantity": quantity,
            "unit_amount": unit_amount,
            "total_amount": total_amount,
            "time_period": time_period,
            "calculation_date": datetime.now().isoformat(),
        }

    def activate_billing_rule(
        self,
        rule_id: int,
        activation_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Activate a billing rule.

        Args:
            rule_id: ID of the billing rule
            activation_date: Date to activate the rule

        Returns:
            Update response
        """
        if activation_date is None:
            activation_date = date.today()

        update_data = {
            "isActive": True,
            "activationDate": activation_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        return self.update_by_id(rule_id, update_data)

    def deactivate_billing_rule(
        self,
        rule_id: int,
        deactivation_date: Optional[date] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deactivate a billing rule.

        Args:
            rule_id: ID of the billing rule
            deactivation_date: Date to deactivate the rule
            reason: Reason for deactivation

        Returns:
            Update response
        """
        if deactivation_date is None:
            deactivation_date = date.today()

        update_data = {
            "isActive": False,
            "deactivationDate": deactivation_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if reason:
            update_data["deactivationReason"] = reason

        return self.update_by_id(rule_id, update_data)

    def get_effective_rules(
        self,
        contract_id: int,
        effective_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all effective billing rules for a contract on a specific date.

        Args:
            contract_id: ID of the contract
            effective_date: Date to check effectiveness (defaults to today)

        Returns:
            List of effective billing rules
        """
        if effective_date is None:
            effective_date = date.today()

        filters = [
            {"field": "contractID", "op": "eq", "value": contract_id},
            {"field": "isActive", "op": "eq", "value": True},
            {
                "field": "effectiveDate",
                "op": "lte",
                "value": effective_date.isoformat(),
            },
        ]

        return self.query(filters=filters).items

    def copy_billing_rules(
        self,
        source_contract_id: int,
        target_contract_id: int,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Copy billing rules from one contract to another.

        Args:
            source_contract_id: ID of the source contract
            target_contract_id: ID of the target contract
            effective_date: Effective date for the copied rules

        Returns:
            Summary of the copy operation
        """
        source_rules = self.get_billing_rules_by_contract(source_contract_id)

        if effective_date is None:
            effective_date = date.today()

        results = []
        for rule in source_rules:
            try:
                # Create a new rule based on the source rule
                new_rule_data = {
                    "contractID": target_contract_id,
                    "ruleName": rule.get("ruleName"),
                    "billingCodeID": rule.get("billingCodeID"),
                    "rateType": rule.get("rateType"),
                    "rateAmount": rule.get("rateAmount"),
                    "billingFrequency": rule.get("billingFrequency"),
                    "effectiveDate": effective_date.isoformat(),
                    "description": f"Copied from contract {source_contract_id}",
                }

                result = self.create(new_rule_data)
                results.append(
                    {
                        "source_rule_id": rule.get("id"),
                        "success": True,
                        "new_rule_id": result.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "source_rule_id": rule.get("id"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "source_contract_id": source_contract_id,
            "target_contract_id": target_contract_id,
            "total_rules": len(source_rules),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def update_rule_rates(
        self,
        rule_ids: List[int],
        rate_adjustment: Union[float, Decimal],
        adjustment_type: str = "percentage",  # "percentage" or "fixed"
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update rates for multiple billing rules.

        Args:
            rule_ids: List of billing rule IDs
            rate_adjustment: Amount to adjust rates by
            adjustment_type: Type of adjustment (percentage or fixed amount)
            effective_date: Date the new rates become effective

        Returns:
            Summary of the update operation
        """
        if effective_date is None:
            effective_date = date.today()

        adjustment = Decimal(str(rate_adjustment))
        results = []

        for rule_id in rule_ids:
            try:
                rule = self.get(rule_id)
                if not rule:
                    results.append(
                        {
                            "rule_id": rule_id,
                            "success": False,
                            "error": "Rule not found",
                        }
                    )
                    continue

                current_rate = Decimal(str(rule.get("rateAmount", 0)))

                if adjustment_type == "percentage":
                    new_rate = current_rate * (1 + adjustment / 100)
                else:  # fixed
                    new_rate = current_rate + adjustment

                update_data = {
                    "rateAmount": float(new_rate),
                    "effectiveDate": effective_date.isoformat(),
                    "lastModifiedDate": datetime.now().isoformat(),
                }

                self.update_by_id(rule_id, update_data)
                results.append(
                    {
                        "rule_id": rule_id,
                        "success": True,
                        "old_rate": current_rate,
                        "new_rate": new_rate,
                        "adjustment": adjustment,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "rule_id": rule_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_rules": len(rule_ids),
            "successful": len(successful),
            "failed": len(failed),
            "adjustment_type": adjustment_type,
            "adjustment_amount": adjustment,
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def get_billing_rule_history(
        self,
        contract_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get billing rule change history for a contract.

        Args:
            contract_id: ID of the contract
            date_from: Start date for history
            date_to: End date for history

        Returns:
            History of billing rule changes
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if date_from:
            filters.append(
                {
                    "field": "lastModifiedDate",
                    "op": "gte",
                    "value": date_from.isoformat(),
                }
            )
        if date_to:
            filters.append(
                {"field": "lastModifiedDate", "op": "lte", "value": date_to.isoformat()}
            )

        rules = self.query(filters=filters).items

        # Sort by modification date
        rules.sort(key=lambda x: x.get("lastModifiedDate", ""), reverse=True)

        return {
            "contract_id": contract_id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "total_rules": len(rules),
            "rules": rules,
        }

    def validate_billing_rules(self, contract_id: int) -> Dict[str, Any]:
        """
        Validate billing rules for a contract.

        Args:
            contract_id: ID of the contract

        Returns:
            Validation results with any issues found
        """
        rules = self.get_billing_rules_by_contract(contract_id, active_only=False)

        issues = []
        warnings = []

        # Check for overlapping effective dates
        active_rules = [r for r in rules if r.get("isActive")]
        billing_codes = {}

        for rule in active_rules:
            billing_code_id = rule.get("billingCodeID")
            effective_date = rule.get("effectiveDate")

            if billing_code_id in billing_codes:
                issues.append(
                    {
                        "type": "duplicate_billing_code",
                        "message": f"Multiple active rules for billing code {billing_code_id}",
                        "rule_ids": [billing_codes[billing_code_id], rule.get("id")],
                    }
                )
            else:
                billing_codes[billing_code_id] = rule.get("id")

            # Check for missing required fields
            if not rule.get("rateAmount"):
                issues.append(
                    {
                        "type": "missing_rate",
                        "message": f"Rule {rule.get('id')} has no rate amount",
                        "rule_id": rule.get("id"),
                    }
                )

            # Check for future effective dates
            if effective_date and effective_date > date.today().isoformat():
                warnings.append(
                    {
                        "type": "future_effective_date",
                        "message": f"Rule {rule.get('id')} has future effective date",
                        "rule_id": rule.get("id"),
                        "effective_date": effective_date,
                    }
                )

        return {
            "contract_id": contract_id,
            "total_rules": len(rules),
            "active_rules": len(active_rules),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "warnings": warnings,
        }
