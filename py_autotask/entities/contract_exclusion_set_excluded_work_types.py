"""
ContractExclusionSetExcludedWorkTypes Entity for py-autotask

This module provides the ContractExclusionSetExcludedWorkTypesEntity class for managing
excluded work types within contract exclusion sets. These entities define which work
types are excluded from specific exclusion sets, allowing for granular control
over contract coverage rules based on the type of work being performed.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ContractExclusionSetExcludedWorkTypesEntity(BaseEntity):
    """
    Manages Autotask ContractExclusionSetExcludedWorkTypes - work types excluded from contract exclusion sets.

    Contract exclusion set excluded work types define specific work types that are
    excluded from contract exclusion sets. This provides fine-grained control over
    which types of work are affected by exclusion rules within a contract exclusion set.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractExclusionSetExcludedWorkTypes"

    # Core CRUD Operations

    def create_excluded_work_type(
        self,
        contract_exclusion_set_id: int,
        work_type_id: int,
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new excluded work type for a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            work_type_id: ID of the work type to exclude
            exclusion_reason: Reason for the exclusion
            effective_date: When the exclusion becomes effective
            **kwargs: Additional fields for the excluded work type

        Returns:
            Create response with new excluded work type ID

        Example:
            excluded_work_type = client.contract_exclusion_set_excluded_work_types.create_excluded_work_type(
                contract_exclusion_set_id=12345,
                work_type_id=678,
                exclusion_reason="Specialized work billed at premium rates"
            )
        """
        if effective_date is None:
            effective_date = date.today()

        excluded_work_type_data = {
            "contractExclusionSetID": contract_exclusion_set_id,
            "workTypeID": work_type_id,
            "effectiveDate": effective_date.isoformat(),
            **kwargs,
        }

        if exclusion_reason:
            excluded_work_type_data["exclusionReason"] = exclusion_reason

        return self.create(excluded_work_type_data)

    def get_excluded_work_types_by_exclusion_set(
        self,
        contract_exclusion_set_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get excluded work types for a specific contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            active_only: Whether to return only active exclusions

        Returns:
            List of excluded work types
        """
        filters = [
            {
                "field": "contractExclusionSetID",
                "op": "eq",
                "value": contract_exclusion_set_id,
            }
        ]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    def get_exclusion_sets_by_work_type(
        self,
        work_type_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get contract exclusion sets that exclude a specific work type.

        Args:
            work_type_id: ID of the work type
            active_only: Whether to return only active exclusions

        Returns:
            List of exclusion sets affecting this work type
        """
        filters = [{"field": "workTypeID", "op": "eq", "value": work_type_id}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    # Business Logic Methods

    def is_work_type_excluded_from_set(
        self,
        contract_exclusion_set_id: int,
        work_type_id: int,
        check_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Check if a work type is excluded from a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            work_type_id: ID of the work type to check
            check_date: Date to check exclusion for (defaults to today)

        Returns:
            Dictionary with exclusion status and details
        """
        if check_date is None:
            check_date = date.today()

        filters = [
            {
                "field": "contractExclusionSetID",
                "op": "eq",
                "value": contract_exclusion_set_id,
            },
            {"field": "workTypeID", "op": "eq", "value": work_type_id},
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
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "work_type_id": work_type_id,
            "check_date": check_date.isoformat(),
            "is_excluded": is_excluded,
            "exclusion_count": len(active_exclusions),
            "exclusions": active_exclusions,
        }

    def add_work_types_to_exclusion_set(
        self,
        contract_exclusion_set_id: int,
        work_type_ids: List[int],
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Add multiple work types to a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            work_type_ids: List of work type IDs to exclude
            exclusion_reason: Reason for the exclusions
            effective_date: When the exclusions become effective

        Returns:
            Summary of the batch operation
        """
        if effective_date is None:
            effective_date = date.today()

        results = []
        for work_type_id in work_type_ids:
            try:
                result = self.create_excluded_work_type(
                    contract_exclusion_set_id=contract_exclusion_set_id,
                    work_type_id=work_type_id,
                    exclusion_reason=exclusion_reason,
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "work_type_id": work_type_id,
                        "success": True,
                        "excluded_work_type_id": result.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "work_type_id": work_type_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_work_types": len(work_type_ids),
            "successful": len(successful),
            "failed": len(failed),
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def remove_work_types_from_exclusion_set(
        self,
        contract_exclusion_set_id: int,
        work_type_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Remove work types from a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            work_type_ids: List of work type IDs to remove

        Returns:
            Summary of the removal operation
        """
        results = []

        for work_type_id in work_type_ids:
            try:
                # Find the excluded work type record
                filters = [
                    {
                        "field": "contractExclusionSetID",
                        "op": "eq",
                        "value": contract_exclusion_set_id,
                    },
                    {"field": "workTypeID", "op": "eq", "value": work_type_id},
                    {"field": "isActive", "op": "eq", "value": True},
                ]

                excluded_work_types = self.query(filters=filters).items

                if excluded_work_types:
                    excluded_work_type_id = excluded_work_types[0].get("id")
                    # Deactivate the excluded work type
                    update_result = self.update_by_id(
                        excluded_work_type_id,
                        {
                            "isActive": False,
                            "deactivationDate": date.today().isoformat(),
                            "lastModifiedDate": datetime.now().isoformat(),
                        },
                    )

                    results.append(
                        {
                            "work_type_id": work_type_id,
                            "success": True,
                            "excluded_work_type_id": excluded_work_type_id,
                        }
                    )
                else:
                    results.append(
                        {
                            "work_type_id": work_type_id,
                            "success": False,
                            "error": "No active excluded work type found",
                        }
                    )
            except Exception as e:
                results.append(
                    {
                        "work_type_id": work_type_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_work_types": len(work_type_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_work_type_exclusion_matrix(
        self,
        exclusion_set_ids: List[int],
        work_type_ids: List[int],
        check_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get a matrix showing which work types are excluded from which exclusion sets.

        Args:
            exclusion_set_ids: List of contract exclusion set IDs
            work_type_ids: List of work type IDs
            check_date: Date to check exclusions for

        Returns:
            Matrix showing exclusion relationships
        """
        if check_date is None:
            check_date = date.today()

        matrix = {}

        for exclusion_set_id in exclusion_set_ids:
            matrix[exclusion_set_id] = {}

            for work_type_id in work_type_ids:
                exclusion_status = self.is_work_type_excluded_from_set(
                    exclusion_set_id, work_type_id, check_date
                )
                matrix[exclusion_set_id][work_type_id] = exclusion_status["is_excluded"]

        return {
            "check_date": check_date.isoformat(),
            "exclusion_set_ids": exclusion_set_ids,
            "work_type_ids": work_type_ids,
            "exclusion_matrix": matrix,
        }

    def get_work_type_coverage_report(
        self,
        work_type_ids: List[int],
        date_from: date,
        date_to: date,
    ) -> Dict[str, Any]:
        """
        Generate a coverage report for work types across exclusion sets.

        Args:
            work_type_ids: List of work type IDs to analyze
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Coverage report with exclusion statistics
        """
        report = {}

        for work_type_id in work_type_ids:
            exclusion_sets = self.get_exclusion_sets_by_work_type(
                work_type_id, active_only=False
            )

            # Filter by date range
            relevant_exclusions = []
            for exclusion in exclusion_sets:
                effective_date = exclusion.get("effectiveDate")
                expiration_date = exclusion.get("expirationDate")

                # Check if exclusion was active during the analysis period
                if effective_date and effective_date <= date_to.isoformat():
                    if not expiration_date or expiration_date >= date_from.isoformat():
                        relevant_exclusions.append(exclusion)

            exclusion_set_ids = list(
                set(
                    e.get("contractExclusionSetID")
                    for e in relevant_exclusions
                    if e.get("contractExclusionSetID")
                )
            )

            report[work_type_id] = {
                "work_type_id": work_type_id,
                "total_exclusions": len(relevant_exclusions),
                "affected_exclusion_sets": len(exclusion_set_ids),
                "exclusion_set_ids": exclusion_set_ids,
                "exclusions": relevant_exclusions,
            }

        return {
            "analysis_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "work_type_ids": work_type_ids,
            "total_analyzed_work_types": len(work_type_ids),
            "results": report,
        }

    def validate_work_type_exclusion_configuration(
        self, contract_exclusion_set_id: int
    ) -> Dict[str, Any]:
        """
        Validate the work type exclusion configuration for a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set

        Returns:
            Validation results with any issues found
        """
        excluded_work_types = self.get_excluded_work_types_by_exclusion_set(
            contract_exclusion_set_id, active_only=False
        )

        issues = []
        warnings = []

        # Check for duplicate work type exclusions
        work_types = {}
        for excluded_work_type in excluded_work_types:
            if not excluded_work_type.get("isActive"):
                continue

            work_type_id = excluded_work_type.get("workTypeID")
            effective_date = excluded_work_type.get("effectiveDate")

            if work_type_id in work_types:
                issues.append(
                    {
                        "type": "duplicate_work_type",
                        "message": f"Multiple active exclusions for work type {work_type_id}",
                        "excluded_work_type_ids": [
                            work_types[work_type_id],
                            excluded_work_type.get("id"),
                        ],
                    }
                )
            else:
                work_types[work_type_id] = excluded_work_type.get("id")

            # Check for future effective dates
            if effective_date and effective_date > date.today().isoformat():
                warnings.append(
                    {
                        "type": "future_effective_date",
                        "message": f"Excluded work type {excluded_work_type.get('id')} has future effective date",
                        "excluded_work_type_id": excluded_work_type.get("id"),
                        "effective_date": effective_date,
                    }
                )

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_excluded_work_types": len(excluded_work_types),
            "active_excluded_work_types": len(
                [ewt for ewt in excluded_work_types if ewt.get("isActive")]
            ),
            "unique_work_types": len(work_types),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "warnings": warnings,
        }
