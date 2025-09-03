"""
ContractExclusionBillingCodes Entity for py-autotask

This module provides the ContractExclusionBillingCodesEntity class for managing
billing code exclusions in contract exclusion sets. These exclusions determine
which billing codes are not covered by specific contract exclusions.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ContractExclusionBillingCodesEntity(BaseEntity):
    """
    Manages Autotask ContractExclusionBillingCodes - billing codes excluded from contract coverage.

    Contract exclusion billing codes define specific billing codes that are excluded
    from contract coverage. When time is tracked against these billing codes,
    it will not be covered under the contract and will be billed separately.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractExclusionBillingCodes"

    # Core CRUD Operations

    def create_exclusion_billing_code(
        self,
        contract_exclusion_id: int,
        billing_code_id: int,
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new billing code exclusion for a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            billing_code_id: ID of the billing code to exclude
            exclusion_reason: Reason for the exclusion
            effective_date: When the exclusion becomes effective
            **kwargs: Additional fields for the exclusion

        Returns:
            Create response with new exclusion ID

        Example:
            exclusion = client.contract_exclusion_billing_codes.create_exclusion_billing_code(
                contract_exclusion_id=12345,
                billing_code_id=678,
                exclusion_reason="Billable project work"
            )
        """
        if effective_date is None:
            effective_date = date.today()

        exclusion_data = {
            "contractExclusionID": contract_exclusion_id,
            "billingCodeID": billing_code_id,
            "effectiveDate": effective_date.isoformat(),
            **kwargs,
        }

        if exclusion_reason:
            exclusion_data["exclusionReason"] = exclusion_reason

        return self.create(exclusion_data)

    def get_exclusions_by_contract_exclusion(
        self,
        contract_exclusion_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get billing code exclusions for a specific contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            active_only: Whether to return only active exclusions

        Returns:
            List of billing code exclusions
        """
        filters = [
            {"field": "contractExclusionID", "op": "eq", "value": contract_exclusion_id}
        ]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    def get_exclusions_by_billing_code(
        self,
        billing_code_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get contract exclusions that exclude a specific billing code.

        Args:
            billing_code_id: ID of the billing code
            active_only: Whether to return only active exclusions

        Returns:
            List of exclusions affecting this billing code
        """
        filters = [{"field": "billingCodeID", "op": "eq", "value": billing_code_id}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    # Business Logic Methods

    def is_billing_code_excluded(
        self,
        contract_exclusion_id: int,
        billing_code_id: int,
        check_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Check if a billing code is excluded from a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            billing_code_id: ID of the billing code to check
            check_date: Date to check exclusion for (defaults to today)

        Returns:
            Dictionary with exclusion status and details
        """
        if check_date is None:
            check_date = date.today()

        filters = [
            {
                "field": "contractExclusionID",
                "op": "eq",
                "value": contract_exclusion_id,
            },
            {"field": "billingCodeID", "op": "eq", "value": billing_code_id},
            {"field": "isActive", "op": "eq", "value": True},
            {"field": "effectiveDate", "op": "lte", "value": check_date.isoformat()},
        ]

        exclusions = self.query(filters=filters).items

        # Check for unexpired exclusions
        active_exclusions = []
        for exclusion in exclusions:
            expiration_date = exclusion.get("expirationDate")
            if not expiration_date or expiration_date >= check_date.isoformat():
                active_exclusions.append(exclusion)

        is_excluded = len(active_exclusions) > 0

        return {
            "contract_exclusion_id": contract_exclusion_id,
            "billing_code_id": billing_code_id,
            "check_date": check_date.isoformat(),
            "is_excluded": is_excluded,
            "exclusion_count": len(active_exclusions),
            "exclusions": active_exclusions,
        }

    def add_billing_codes_to_exclusion(
        self,
        contract_exclusion_id: int,
        billing_code_ids: List[int],
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Add multiple billing codes to a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            billing_code_ids: List of billing code IDs to exclude
            exclusion_reason: Reason for the exclusions
            effective_date: When the exclusions become effective

        Returns:
            Summary of the batch operation
        """
        if effective_date is None:
            effective_date = date.today()

        results = []
        for billing_code_id in billing_code_ids:
            try:
                result = self.create_exclusion_billing_code(
                    contract_exclusion_id=contract_exclusion_id,
                    billing_code_id=billing_code_id,
                    exclusion_reason=exclusion_reason,
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "billing_code_id": billing_code_id,
                        "success": True,
                        "exclusion_id": result.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "billing_code_id": billing_code_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_exclusion_id": contract_exclusion_id,
            "total_billing_codes": len(billing_code_ids),
            "successful": len(successful),
            "failed": len(failed),
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def remove_billing_codes_from_exclusion(
        self,
        contract_exclusion_id: int,
        billing_code_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Remove billing codes from a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            billing_code_ids: List of billing code IDs to remove

        Returns:
            Summary of the removal operation
        """
        results = []

        for billing_code_id in billing_code_ids:
            try:
                # Find the exclusion record
                filters = [
                    {
                        "field": "contractExclusionID",
                        "op": "eq",
                        "value": contract_exclusion_id,
                    },
                    {"field": "billingCodeID", "op": "eq", "value": billing_code_id},
                    {"field": "isActive", "op": "eq", "value": True},
                ]

                exclusions = self.query(filters=filters).items

                if exclusions:
                    exclusion_id = exclusions[0].get("id")
                    # Deactivate the exclusion
                    update_result = self.update_by_id(
                        exclusion_id,
                        {
                            "isActive": False,
                            "deactivationDate": date.today().isoformat(),
                            "lastModifiedDate": datetime.now().isoformat(),
                        },
                    )

                    results.append(
                        {
                            "billing_code_id": billing_code_id,
                            "success": True,
                            "exclusion_id": exclusion_id,
                        }
                    )
                else:
                    results.append(
                        {
                            "billing_code_id": billing_code_id,
                            "success": False,
                            "error": "No active exclusion found",
                        }
                    )
            except Exception as e:
                results.append(
                    {
                        "billing_code_id": billing_code_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_exclusion_id": contract_exclusion_id,
            "total_billing_codes": len(billing_code_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_excluded_billing_codes_summary(
        self,
        contract_exclusion_id: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of excluded billing codes for a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion

        Returns:
            Summary of excluded billing codes
        """
        exclusions = self.get_exclusions_by_contract_exclusion(
            contract_exclusion_id, active_only=True
        )

        # Group by billing code
        billing_code_summary = {}
        for exclusion in exclusions:
            billing_code_id = exclusion.get("billingCodeID")
            if billing_code_id not in billing_code_summary:
                billing_code_summary[billing_code_id] = {
                    "billing_code_id": billing_code_id,
                    "exclusion_count": 0,
                    "earliest_effective_date": None,
                    "latest_effective_date": None,
                    "exclusion_reasons": set(),
                }

            summary = billing_code_summary[billing_code_id]
            summary["exclusion_count"] += 1

            effective_date = exclusion.get("effectiveDate")
            if effective_date:
                if (
                    not summary["earliest_effective_date"]
                    or effective_date < summary["earliest_effective_date"]
                ):
                    summary["earliest_effective_date"] = effective_date
                if (
                    not summary["latest_effective_date"]
                    or effective_date > summary["latest_effective_date"]
                ):
                    summary["latest_effective_date"] = effective_date

            exclusion_reason = exclusion.get("exclusionReason")
            if exclusion_reason:
                summary["exclusion_reasons"].add(exclusion_reason)

        # Convert sets to lists for JSON serialization
        for summary in billing_code_summary.values():
            summary["exclusion_reasons"] = list(summary["exclusion_reasons"])

        return {
            "contract_exclusion_id": contract_exclusion_id,
            "total_excluded_billing_codes": len(billing_code_summary),
            "total_exclusion_records": len(exclusions),
            "excluded_billing_codes": list(billing_code_summary.values()),
        }

    def copy_exclusions_to_another_contract_exclusion(
        self,
        source_contract_exclusion_id: int,
        target_contract_exclusion_id: int,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Copy billing code exclusions from one contract exclusion to another.

        Args:
            source_contract_exclusion_id: ID of the source contract exclusion
            target_contract_exclusion_id: ID of the target contract exclusion
            effective_date: Effective date for the copied exclusions

        Returns:
            Summary of the copy operation
        """
        source_exclusions = self.get_exclusions_by_contract_exclusion(
            source_contract_exclusion_id, active_only=True
        )

        if effective_date is None:
            effective_date = date.today()

        results = []
        for exclusion in source_exclusions:
            try:
                new_exclusion = self.create_exclusion_billing_code(
                    contract_exclusion_id=target_contract_exclusion_id,
                    billing_code_id=exclusion.get("billingCodeID"),
                    exclusion_reason=f"Copied from contract exclusion {source_contract_exclusion_id}",
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "source_exclusion_id": exclusion.get("id"),
                        "billing_code_id": exclusion.get("billingCodeID"),
                        "success": True,
                        "new_exclusion_id": new_exclusion.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "source_exclusion_id": exclusion.get("id"),
                        "billing_code_id": exclusion.get("billingCodeID"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "source_contract_exclusion_id": source_contract_exclusion_id,
            "target_contract_exclusion_id": target_contract_exclusion_id,
            "total_exclusions": len(source_exclusions),
            "successful": len(successful),
            "failed": len(failed),
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def get_contract_exclusions_for_billing_codes(
        self,
        billing_code_ids: List[int],
        active_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Get contract exclusions that affect multiple billing codes.

        Args:
            billing_code_ids: List of billing code IDs to check
            active_only: Whether to return only active exclusions

        Returns:
            Contract exclusions affecting the billing codes
        """
        results = {}

        for billing_code_id in billing_code_ids:
            exclusions = self.get_exclusions_by_billing_code(
                billing_code_id, active_only
            )

            contract_exclusion_ids = list(
                set(
                    e.get("contractExclusionID")
                    for e in exclusions
                    if e.get("contractExclusionID")
                )
            )

            results[billing_code_id] = {
                "billing_code_id": billing_code_id,
                "exclusion_count": len(exclusions),
                "contract_exclusion_ids": contract_exclusion_ids,
                "exclusions": exclusions,
            }

        return {
            "billing_code_ids": billing_code_ids,
            "results": results,
        }

    def validate_exclusion_configuration(
        self, contract_exclusion_id: int
    ) -> Dict[str, Any]:
        """
        Validate the billing code exclusion configuration.

        Args:
            contract_exclusion_id: ID of the contract exclusion

        Returns:
            Validation results with any issues found
        """
        exclusions = self.get_exclusions_by_contract_exclusion(
            contract_exclusion_id, active_only=False
        )

        issues = []
        warnings = []

        # Check for duplicate billing code exclusions
        billing_codes = {}
        for exclusion in exclusions:
            if not exclusion.get("isActive"):
                continue

            billing_code_id = exclusion.get("billingCodeID")
            effective_date = exclusion.get("effectiveDate")

            if billing_code_id in billing_codes:
                issues.append(
                    {
                        "type": "duplicate_billing_code",
                        "message": f"Multiple active exclusions for billing code {billing_code_id}",
                        "exclusion_ids": [
                            billing_codes[billing_code_id],
                            exclusion.get("id"),
                        ],
                    }
                )
            else:
                billing_codes[billing_code_id] = exclusion.get("id")

            # Check for future effective dates
            if effective_date and effective_date > date.today().isoformat():
                warnings.append(
                    {
                        "type": "future_effective_date",
                        "message": f"Exclusion {exclusion.get('id')} has future effective date",
                        "exclusion_id": exclusion.get("id"),
                        "effective_date": effective_date,
                    }
                )

        return {
            "contract_exclusion_id": contract_exclusion_id,
            "total_exclusions": len(exclusions),
            "active_exclusions": len([e for e in exclusions if e.get("isActive")]),
            "unique_billing_codes": len(billing_codes),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "warnings": warnings,
        }
