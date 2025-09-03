"""
ContractRoles Entity for py-autotask

This module provides the ContractRolesEntity class for managing contract roles
in Autotask. Contract roles define which resource roles are associated with
a contract and their specific billing rates, permissions, and responsibilities.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractRolesEntity(BaseEntity):
    """
    Manages Autotask ContractRoles - resource roles associated with contracts.

    Contract roles define the relationship between resource roles and contracts,
    including specific billing rates, permissions, and responsibilities that
    apply when resources in those roles work on the contract.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractRoles"

    # Core CRUD Operations

    def create_contract_role(
        self,
        contract_id: int,
        resource_role_id: int,
        hourly_rate: Union[float, Decimal],
        is_active: bool = True,
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract role association.

        Args:
            contract_id: ID of the contract
            resource_role_id: ID of the resource role
            hourly_rate: Billing rate for this role on this contract
            is_active: Whether the role is currently active
            effective_date: When this role becomes effective
            **kwargs: Additional fields for the contract role

        Returns:
            Create response with new contract role ID

        Example:
            contract_role = client.contract_roles.create_contract_role(
                contract_id=12345,
                resource_role_id=678,
                hourly_rate=150.00,
                effective_date=date(2024, 1, 1)
            )
        """
        if effective_date is None:
            effective_date = date.today()

        contract_role_data = {
            "contractID": contract_id,
            "resourceRoleID": resource_role_id,
            "hourlyRate": float(hourly_rate),
            "isActive": is_active,
            "effectiveDate": effective_date.isoformat(),
            **kwargs,
        }

        return self.create(contract_role_data)

    def get_roles_by_contract(
        self,
        contract_id: int,
        active_only: bool = True,
        effective_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get resource roles associated with a specific contract.

        Args:
            contract_id: ID of the contract
            active_only: Whether to return only active roles
            effective_date: Date to check role effectiveness for

        Returns:
            List of contract roles
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

    def get_contracts_by_role(
        self,
        resource_role_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get contracts that use a specific resource role.

        Args:
            resource_role_id: ID of the resource role
            active_only: Whether to return only active contract roles

        Returns:
            List of contract roles for the specified resource role
        """
        filters = [{"field": "resourceRoleID", "op": "eq", "value": resource_role_id}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    # Business Logic Methods

    def update_role_rate(
        self,
        contract_role_id: int,
        new_hourly_rate: Union[float, Decimal],
        effective_date: Optional[date] = None,
        rate_change_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the hourly rate for a contract role.

        Args:
            contract_role_id: ID of the contract role
            new_hourly_rate: New billing rate
            effective_date: When the new rate becomes effective
            rate_change_reason: Reason for the rate change

        Returns:
            Update response with rate change details
        """
        if effective_date is None:
            effective_date = date.today()

        # Get current rate for comparison
        contract_role = self.get(contract_role_id)
        old_rate = contract_role.get("hourlyRate", 0) if contract_role else 0

        update_data = {
            "hourlyRate": float(new_hourly_rate),
            "effectiveDate": effective_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
            "previousRate": old_rate,
            "rateChangeDate": datetime.now().isoformat(),
        }

        if rate_change_reason:
            update_data["rateChangeReason"] = rate_change_reason

        result = self.update_by_id(contract_role_id, update_data)

        return {
            "contract_role_id": contract_role_id,
            "old_rate": Decimal(str(old_rate)),
            "new_rate": Decimal(str(new_hourly_rate)),
            "rate_change": Decimal(str(new_hourly_rate)) - Decimal(str(old_rate)),
            "effective_date": effective_date.isoformat(),
            "update_result": result,
        }

    def activate_contract_role(
        self,
        contract_role_id: int,
        activation_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Activate a contract role.

        Args:
            contract_role_id: ID of the contract role
            activation_date: Date to activate the role

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

        return self.update_by_id(contract_role_id, update_data)

    def deactivate_contract_role(
        self,
        contract_role_id: int,
        deactivation_date: Optional[date] = None,
        deactivation_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deactivate a contract role.

        Args:
            contract_role_id: ID of the contract role
            deactivation_date: Date to deactivate the role
            deactivation_reason: Reason for deactivation

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

        if deactivation_reason:
            update_data["deactivationReason"] = deactivation_reason

        return self.update_by_id(contract_role_id, update_data)

    def get_role_rate_for_contract(
        self,
        contract_id: int,
        resource_role_id: int,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get the billing rate for a specific role on a specific contract.

        Args:
            contract_id: ID of the contract
            resource_role_id: ID of the resource role
            effective_date: Date to check rate for (defaults to today)

        Returns:
            Rate information for the role on the contract
        """
        if effective_date is None:
            effective_date = date.today()

        filters = [
            {"field": "contractID", "op": "eq", "value": contract_id},
            {"field": "resourceRoleID", "op": "eq", "value": resource_role_id},
            {"field": "isActive", "op": "eq", "value": True},
            {
                "field": "effectiveDate",
                "op": "lte",
                "value": effective_date.isoformat(),
            },
        ]

        contract_roles = self.query(filters=filters).items

        if not contract_roles:
            return {
                "contract_id": contract_id,
                "resource_role_id": resource_role_id,
                "effective_date": effective_date.isoformat(),
                "rate_found": False,
                "hourly_rate": None,
                "message": "No active contract role found for this combination",
            }

        # Get the most recent effective rate
        contract_roles.sort(key=lambda x: x.get("effectiveDate", ""), reverse=True)
        current_role = contract_roles[0]

        return {
            "contract_id": contract_id,
            "resource_role_id": resource_role_id,
            "effective_date": effective_date.isoformat(),
            "rate_found": True,
            "contract_role_id": current_role.get("id"),
            "hourly_rate": Decimal(str(current_role.get("hourlyRate", 0))),
            "role_effective_date": current_role.get("effectiveDate"),
            "role_details": current_role,
        }

    def bulk_update_role_rates(
        self,
        contract_id: int,
        rate_adjustments: Dict[int, Union[float, Decimal]],  # role_id -> new_rate
        adjustment_type: str = "absolute",  # "absolute" or "percentage"
        effective_date: Optional[date] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update rates for multiple contract roles in bulk.

        Args:
            contract_id: ID of the contract
            rate_adjustments: Dictionary mapping resource role IDs to new rates or adjustments
            adjustment_type: Whether adjustments are absolute rates or percentage changes
            effective_date: When the new rates become effective
            reason: Reason for the rate changes

        Returns:
            Summary of the bulk update operation
        """
        if effective_date is None:
            effective_date = date.today()

        results = []
        contract_roles = self.get_roles_by_contract(contract_id, active_only=True)

        for contract_role in contract_roles:
            resource_role_id = contract_role.get("resourceRoleID")
            contract_role_id = contract_role.get("id")

            if resource_role_id in rate_adjustments:
                try:
                    current_rate = Decimal(str(contract_role.get("hourlyRate", 0)))
                    adjustment = Decimal(str(rate_adjustments[resource_role_id]))

                    if adjustment_type == "percentage":
                        new_rate = current_rate * (1 + adjustment / 100)
                    else:  # absolute
                        new_rate = adjustment

                    update_result = self.update_role_rate(
                        contract_role_id=contract_role_id,
                        new_hourly_rate=float(new_rate),
                        effective_date=effective_date,
                        rate_change_reason=reason,
                    )

                    results.append(
                        {
                            "resource_role_id": resource_role_id,
                            "contract_role_id": contract_role_id,
                            "success": True,
                            "old_rate": current_rate,
                            "new_rate": new_rate,
                            "adjustment": adjustment,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "resource_role_id": resource_role_id,
                            "contract_role_id": contract_role_id,
                            "success": False,
                            "error": str(e),
                        }
                    )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_id": contract_id,
            "adjustment_type": adjustment_type,
            "effective_date": effective_date.isoformat(),
            "total_roles_processed": len(results),
            "successful_updates": len(successful),
            "failed_updates": len(failed),
            "reason": reason,
            "results": results,
        }

    def copy_roles_to_contract(
        self,
        source_contract_id: int,
        target_contract_id: int,
        effective_date: Optional[date] = None,
        rate_adjustment: Optional[Union[float, Decimal]] = None,
        adjustment_type: str = "percentage",
    ) -> Dict[str, Any]:
        """
        Copy contract roles from one contract to another.

        Args:
            source_contract_id: ID of the source contract
            target_contract_id: ID of the target contract
            effective_date: Effective date for the copied roles
            rate_adjustment: Optional rate adjustment to apply
            adjustment_type: Type of rate adjustment (percentage or absolute)

        Returns:
            Summary of the copy operation
        """
        if effective_date is None:
            effective_date = date.today()

        source_roles = self.get_roles_by_contract(source_contract_id, active_only=True)
        results = []

        for source_role in source_roles:
            try:
                original_rate = Decimal(str(source_role.get("hourlyRate", 0)))

                if rate_adjustment is not None:
                    adjustment = Decimal(str(rate_adjustment))
                    if adjustment_type == "percentage":
                        new_rate = original_rate * (1 + adjustment / 100)
                    else:  # absolute
                        new_rate = original_rate + adjustment
                else:
                    new_rate = original_rate

                new_role = self.create_contract_role(
                    contract_id=target_contract_id,
                    resource_role_id=source_role.get("resourceRoleID"),
                    hourly_rate=float(new_rate),
                    effective_date=effective_date,
                    copiedFromContractRoleID=source_role.get("id"),
                    originalContractID=source_contract_id,
                )

                results.append(
                    {
                        "source_role_id": source_role.get("id"),
                        "resource_role_id": source_role.get("resourceRoleID"),
                        "success": True,
                        "new_contract_role_id": new_role.item_id,
                        "original_rate": original_rate,
                        "new_rate": new_rate,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "source_role_id": source_role.get("id"),
                        "resource_role_id": source_role.get("resourceRoleID"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "source_contract_id": source_contract_id,
            "target_contract_id": target_contract_id,
            "total_roles": len(source_roles),
            "successful_copies": len(successful),
            "failed_copies": len(failed),
            "effective_date": effective_date.isoformat(),
            "rate_adjustment": rate_adjustment,
            "adjustment_type": adjustment_type,
            "results": results,
        }

    def get_contract_role_summary(
        self,
        contract_id: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of all roles associated with a contract.

        Args:
            contract_id: ID of the contract

        Returns:
            Summary of contract roles with rate statistics
        """
        all_roles = self.get_roles_by_contract(contract_id, active_only=False)
        active_roles = [role for role in all_roles if role.get("isActive")]

        if not all_roles:
            return {
                "contract_id": contract_id,
                "total_roles": 0,
                "active_roles": 0,
                "message": "No roles configured for this contract",
            }

        # Calculate rate statistics for active roles
        active_rates = [
            Decimal(str(role.get("hourlyRate", 0))) for role in active_roles
        ]

        if active_rates:
            min_rate = min(active_rates)
            max_rate = max(active_rates)
            avg_rate = sum(active_rates) / len(active_rates)
        else:
            min_rate = max_rate = avg_rate = Decimal("0")

        # Group by status
        status_counts = {}
        for role in all_roles:
            status = "Active" if role.get("isActive") else "Inactive"
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "contract_id": contract_id,
            "total_roles": len(all_roles),
            "active_roles": len(active_roles),
            "inactive_roles": len(all_roles) - len(active_roles),
            "rate_statistics": {
                "minimum_rate": min_rate,
                "maximum_rate": max_rate,
                "average_rate": avg_rate,
            },
            "status_breakdown": status_counts,
            "roles": all_roles,
        }

    def get_role_rate_history(
        self,
        contract_role_id: int,
    ) -> Dict[str, Any]:
        """
        Get the rate change history for a contract role.

        Args:
            contract_role_id: ID of the contract role

        Returns:
            Rate change history with timestamps and reasons
        """
        contract_role = self.get(contract_role_id)
        if not contract_role:
            return {
                "contract_role_id": contract_role_id,
                "error": "Contract role not found",
            }

        # This would typically involve querying audit logs or change history
        # For now, we'll return the current state and any stored previous rate
        current_rate = contract_role.get("hourlyRate")
        previous_rate = contract_role.get("previousRate")
        rate_change_date = contract_role.get("rateChangeDate")
        rate_change_reason = contract_role.get("rateChangeReason")

        history = [
            {
                "rate": current_rate,
                "effective_date": contract_role.get("effectiveDate"),
                "change_date": rate_change_date or contract_role.get("effectiveDate"),
                "reason": rate_change_reason or "Initial rate",
                "is_current": True,
            }
        ]

        if previous_rate and previous_rate != current_rate:
            history.append(
                {
                    "rate": previous_rate,
                    "effective_date": "Unknown",
                    "change_date": "Unknown",
                    "reason": "Previous rate",
                    "is_current": False,
                }
            )

        # Sort by change date (most recent first)
        history.sort(key=lambda x: x.get("change_date", ""), reverse=True)

        return {
            "contract_role_id": contract_role_id,
            "contract_id": contract_role.get("contractID"),
            "resource_role_id": contract_role.get("resourceRoleID"),
            "current_rate": current_rate,
            "rate_changes": len(history) - 1,
            "history": history,
        }

    def validate_contract_roles(self, contract_id: int) -> Dict[str, Any]:
        """
        Validate the contract role configuration.

        Args:
            contract_id: ID of the contract

        Returns:
            Validation results with any issues found
        """
        contract_roles = self.get_roles_by_contract(contract_id, active_only=False)

        issues = []
        warnings = []

        # Check for duplicate resource roles
        resource_roles = {}
        for role in contract_roles:
            if not role.get("isActive"):
                continue

            resource_role_id = role.get("resourceRoleID")
            if resource_role_id in resource_roles:
                issues.append(
                    {
                        "type": "duplicate_resource_role",
                        "message": f"Multiple active contract roles for resource role {resource_role_id}",
                        "contract_role_ids": [
                            resource_roles[resource_role_id],
                            role.get("id"),
                        ],
                    }
                )
            else:
                resource_roles[resource_role_id] = role.get("id")

            # Check for missing or zero rates
            hourly_rate = role.get("hourlyRate", 0)
            if not hourly_rate or hourly_rate <= 0:
                issues.append(
                    {
                        "type": "missing_or_zero_rate",
                        "message": f"Contract role {role.get('id')} has no valid hourly rate",
                        "contract_role_id": role.get("id"),
                    }
                )

            # Check for future effective dates
            effective_date = role.get("effectiveDate")
            if effective_date and effective_date > date.today().isoformat():
                warnings.append(
                    {
                        "type": "future_effective_date",
                        "message": f"Contract role {role.get('id')} has future effective date",
                        "contract_role_id": role.get("id"),
                        "effective_date": effective_date,
                    }
                )

        return {
            "contract_id": contract_id,
            "total_contract_roles": len(contract_roles),
            "active_contract_roles": len(
                [r for r in contract_roles if r.get("isActive")]
            ),
            "unique_resource_roles": len(resource_roles),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "warnings": warnings,
        }
