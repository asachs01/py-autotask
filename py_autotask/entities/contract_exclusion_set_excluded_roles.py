"""
ContractExclusionSetExcludedRoles Entity for py-autotask

This module provides the ContractExclusionSetExcludedRolesEntity class for managing
excluded roles within contract exclusion sets. These entities define which resource
roles are excluded from specific exclusion sets, allowing for granular control
over contract coverage rules.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ContractExclusionSetExcludedRolesEntity(BaseEntity):
    """
    Manages Autotask ContractExclusionSetExcludedRoles - roles excluded from contract exclusion sets.

    Contract exclusion set excluded roles define specific resource roles that are
    excluded from contract exclusion sets. This provides fine-grained control over
    which roles are affected by exclusion rules within a contract exclusion set.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractExclusionSetExcludedRoles"

    # Core CRUD Operations

    def create_excluded_role(
        self,
        contract_exclusion_set_id: int,
        resource_role_id: int,
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new excluded role for a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            resource_role_id: ID of the resource role to exclude
            exclusion_reason: Reason for the exclusion
            effective_date: When the exclusion becomes effective
            **kwargs: Additional fields for the excluded role

        Returns:
            Create response with new excluded role ID

        Example:
            excluded_role = client.contract_exclusion_set_excluded_roles.create_excluded_role(
                contract_exclusion_set_id=12345,
                resource_role_id=678,
                exclusion_reason="Senior roles billed at premium rates"
            )
        """
        if effective_date is None:
            effective_date = date.today()

        excluded_role_data = {
            "contractExclusionSetID": contract_exclusion_set_id,
            "resourceRoleID": resource_role_id,
            "effectiveDate": effective_date.isoformat(),
            **kwargs,
        }

        if exclusion_reason:
            excluded_role_data["exclusionReason"] = exclusion_reason

        return self.create(excluded_role_data)

    def get_excluded_roles_by_exclusion_set(
        self,
        contract_exclusion_set_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get excluded roles for a specific contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            active_only: Whether to return only active exclusions

        Returns:
            List of excluded roles
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

    def get_exclusion_sets_by_resource_role(
        self,
        resource_role_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get contract exclusion sets that exclude a specific resource role.

        Args:
            resource_role_id: ID of the resource role
            active_only: Whether to return only active exclusions

        Returns:
            List of exclusion sets affecting this resource role
        """
        filters = [{"field": "resourceRoleID", "op": "eq", "value": resource_role_id}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    # Business Logic Methods

    def is_role_excluded_from_set(
        self,
        contract_exclusion_set_id: int,
        resource_role_id: int,
        check_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Check if a resource role is excluded from a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            resource_role_id: ID of the resource role to check
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
            {"field": "resourceRoleID", "op": "eq", "value": resource_role_id},
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
            "resource_role_id": resource_role_id,
            "check_date": check_date.isoformat(),
            "is_excluded": is_excluded,
            "exclusion_count": len(active_exclusions),
            "exclusions": active_exclusions,
        }

    def add_roles_to_exclusion_set(
        self,
        contract_exclusion_set_id: int,
        resource_role_ids: List[int],
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Add multiple resource roles to a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            resource_role_ids: List of resource role IDs to exclude
            exclusion_reason: Reason for the exclusions
            effective_date: When the exclusions become effective

        Returns:
            Summary of the batch operation
        """
        if effective_date is None:
            effective_date = date.today()

        results = []
        for resource_role_id in resource_role_ids:
            try:
                result = self.create_excluded_role(
                    contract_exclusion_set_id=contract_exclusion_set_id,
                    resource_role_id=resource_role_id,
                    exclusion_reason=exclusion_reason,
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "resource_role_id": resource_role_id,
                        "success": True,
                        "excluded_role_id": result.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "resource_role_id": resource_role_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_resource_roles": len(resource_role_ids),
            "successful": len(successful),
            "failed": len(failed),
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def remove_roles_from_exclusion_set(
        self,
        contract_exclusion_set_id: int,
        resource_role_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Remove resource roles from a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set
            resource_role_ids: List of resource role IDs to remove

        Returns:
            Summary of the removal operation
        """
        results = []

        for resource_role_id in resource_role_ids:
            try:
                # Find the excluded role record
                filters = [
                    {
                        "field": "contractExclusionSetID",
                        "op": "eq",
                        "value": contract_exclusion_set_id,
                    },
                    {"field": "resourceRoleID", "op": "eq", "value": resource_role_id},
                    {"field": "isActive", "op": "eq", "value": True},
                ]

                excluded_roles = self.query(filters=filters).items

                if excluded_roles:
                    excluded_role_id = excluded_roles[0].get("id")
                    # Deactivate the excluded role
                    update_result = self.update_by_id(
                        excluded_role_id,
                        {
                            "isActive": False,
                            "deactivationDate": date.today().isoformat(),
                            "lastModifiedDate": datetime.now().isoformat(),
                        },
                    )

                    results.append(
                        {
                            "resource_role_id": resource_role_id,
                            "success": True,
                            "excluded_role_id": excluded_role_id,
                        }
                    )
                else:
                    results.append(
                        {
                            "resource_role_id": resource_role_id,
                            "success": False,
                            "error": "No active excluded role found",
                        }
                    )
            except Exception as e:
                results.append(
                    {
                        "resource_role_id": resource_role_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_resource_roles": len(resource_role_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_excluded_roles_summary(
        self,
        contract_exclusion_set_id: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of excluded roles for a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set

        Returns:
            Summary of excluded roles
        """
        excluded_roles = self.get_excluded_roles_by_exclusion_set(
            contract_exclusion_set_id, active_only=True
        )

        # Group by resource role
        role_summary = {}
        for excluded_role in excluded_roles:
            resource_role_id = excluded_role.get("resourceRoleID")
            if resource_role_id not in role_summary:
                role_summary[resource_role_id] = {
                    "resource_role_id": resource_role_id,
                    "exclusion_count": 0,
                    "earliest_effective_date": None,
                    "latest_effective_date": None,
                    "exclusion_reasons": set(),
                }

            summary = role_summary[resource_role_id]
            summary["exclusion_count"] += 1

            effective_date = excluded_role.get("effectiveDate")
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

            exclusion_reason = excluded_role.get("exclusionReason")
            if exclusion_reason:
                summary["exclusion_reasons"].add(exclusion_reason)

        # Convert sets to lists for JSON serialization
        for summary in role_summary.values():
            summary["exclusion_reasons"] = list(summary["exclusion_reasons"])

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_excluded_roles": len(role_summary),
            "total_exclusion_records": len(excluded_roles),
            "excluded_roles": list(role_summary.values()),
        }

    def copy_excluded_roles_to_another_set(
        self,
        source_exclusion_set_id: int,
        target_exclusion_set_id: int,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Copy excluded roles from one contract exclusion set to another.

        Args:
            source_exclusion_set_id: ID of the source contract exclusion set
            target_exclusion_set_id: ID of the target contract exclusion set
            effective_date: Effective date for the copied exclusions

        Returns:
            Summary of the copy operation
        """
        source_excluded_roles = self.get_excluded_roles_by_exclusion_set(
            source_exclusion_set_id, active_only=True
        )

        if effective_date is None:
            effective_date = date.today()

        results = []
        for excluded_role in source_excluded_roles:
            try:
                new_excluded_role = self.create_excluded_role(
                    contract_exclusion_set_id=target_exclusion_set_id,
                    resource_role_id=excluded_role.get("resourceRoleID"),
                    exclusion_reason=f"Copied from exclusion set {source_exclusion_set_id}",
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "source_excluded_role_id": excluded_role.get("id"),
                        "resource_role_id": excluded_role.get("resourceRoleID"),
                        "success": True,
                        "new_excluded_role_id": new_excluded_role.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "source_excluded_role_id": excluded_role.get("id"),
                        "resource_role_id": excluded_role.get("resourceRoleID"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "source_exclusion_set_id": source_exclusion_set_id,
            "target_exclusion_set_id": target_exclusion_set_id,
            "total_excluded_roles": len(source_excluded_roles),
            "successful": len(successful),
            "failed": len(failed),
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def get_role_exclusion_coverage_analysis(
        self,
        resource_role_ids: List[int],
        date_from: date,
        date_to: date,
    ) -> Dict[str, Any]:
        """
        Analyze role exclusion coverage across multiple exclusion sets.

        Args:
            resource_role_ids: List of resource role IDs to analyze
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Analysis of role exclusion coverage
        """
        analysis_results = {}

        for resource_role_id in resource_role_ids:
            exclusion_sets = self.get_exclusion_sets_by_resource_role(
                resource_role_id, active_only=False
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

            analysis_results[resource_role_id] = {
                "resource_role_id": resource_role_id,
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
            "resource_role_ids": resource_role_ids,
            "total_analyzed_roles": len(resource_role_ids),
            "results": analysis_results,
        }

    def bulk_update_excluded_roles(
        self,
        updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update multiple excluded roles in batch.

        Args:
            updates: List of updates, each containing excluded_role_id and update data

        Returns:
            Summary of the bulk update operation
        """
        results = []

        for update in updates:
            excluded_role_id = update.get("excluded_role_id")
            update_data = update.get("update_data", {})

            try:
                result = self.update_by_id(excluded_role_id, update_data)
                results.append(
                    {
                        "excluded_role_id": excluded_role_id,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "excluded_role_id": excluded_role_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def validate_exclusion_set_configuration(
        self, contract_exclusion_set_id: int
    ) -> Dict[str, Any]:
        """
        Validate the excluded role configuration for a contract exclusion set.

        Args:
            contract_exclusion_set_id: ID of the contract exclusion set

        Returns:
            Validation results with any issues found
        """
        excluded_roles = self.get_excluded_roles_by_exclusion_set(
            contract_exclusion_set_id, active_only=False
        )

        issues = []
        warnings = []

        # Check for duplicate resource role exclusions
        resource_roles = {}
        for excluded_role in excluded_roles:
            if not excluded_role.get("isActive"):
                continue

            resource_role_id = excluded_role.get("resourceRoleID")
            effective_date = excluded_role.get("effectiveDate")

            if resource_role_id in resource_roles:
                issues.append(
                    {
                        "type": "duplicate_resource_role",
                        "message": f"Multiple active exclusions for resource role {resource_role_id}",
                        "excluded_role_ids": [
                            resource_roles[resource_role_id],
                            excluded_role.get("id"),
                        ],
                    }
                )
            else:
                resource_roles[resource_role_id] = excluded_role.get("id")

            # Check for future effective dates
            if effective_date and effective_date > date.today().isoformat():
                warnings.append(
                    {
                        "type": "future_effective_date",
                        "message": f"Excluded role {excluded_role.get('id')} has future effective date",
                        "excluded_role_id": excluded_role.get("id"),
                        "effective_date": effective_date,
                    }
                )

        return {
            "contract_exclusion_set_id": contract_exclusion_set_id,
            "total_excluded_roles": len(excluded_roles),
            "active_excluded_roles": len(
                [er for er in excluded_roles if er.get("isActive")]
            ),
            "unique_resource_roles": len(resource_roles),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "warnings": warnings,
        }
