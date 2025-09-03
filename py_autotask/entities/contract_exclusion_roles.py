"""
ContractExclusionRoles Entity for py-autotask

This module provides the ContractExclusionRolesEntity class for managing
role exclusions in contract exclusion sets. These exclusions determine
which resource roles are not covered by specific contract exclusions.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ContractExclusionRolesEntity(BaseEntity):
    """
    Manages Autotask ContractExclusionRoles - resource roles excluded from contract coverage.

    Contract exclusion roles define specific resource roles that are excluded
    from contract coverage. When time is tracked by resources in these roles,
    it will not be covered under the contract and will be billed separately.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractExclusionRoles"

    # Core CRUD Operations

    def create_exclusion_role(
        self,
        contract_exclusion_id: int,
        resource_role_id: int,
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new role exclusion for a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            resource_role_id: ID of the resource role to exclude
            exclusion_reason: Reason for the exclusion
            effective_date: When the exclusion becomes effective
            **kwargs: Additional fields for the exclusion

        Returns:
            Create response with new exclusion ID

        Example:
            exclusion = client.contract_exclusion_roles.create_exclusion_role(
                contract_exclusion_id=12345,
                resource_role_id=678,
                exclusion_reason="Senior consultants billed separately"
            )
        """
        if effective_date is None:
            effective_date = date.today()

        exclusion_data = {
            "contractExclusionID": contract_exclusion_id,
            "resourceRoleID": resource_role_id,
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
        Get role exclusions for a specific contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            active_only: Whether to return only active exclusions

        Returns:
            List of role exclusions
        """
        filters = [
            {"field": "contractExclusionID", "op": "eq", "value": contract_exclusion_id}
        ]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    def get_exclusions_by_resource_role(
        self,
        resource_role_id: int,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get contract exclusions that exclude a specific resource role.

        Args:
            resource_role_id: ID of the resource role
            active_only: Whether to return only active exclusions

        Returns:
            List of exclusions affecting this resource role
        """
        filters = [{"field": "resourceRoleID", "op": "eq", "value": resource_role_id}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        return self.query(filters=filters).items

    # Business Logic Methods

    def is_resource_role_excluded(
        self,
        contract_exclusion_id: int,
        resource_role_id: int,
        check_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Check if a resource role is excluded from a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            resource_role_id: ID of the resource role to check
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
            "contract_exclusion_id": contract_exclusion_id,
            "resource_role_id": resource_role_id,
            "check_date": check_date.isoformat(),
            "is_excluded": is_excluded,
            "exclusion_count": len(active_exclusions),
            "exclusions": active_exclusions,
        }

    def add_resource_roles_to_exclusion(
        self,
        contract_exclusion_id: int,
        resource_role_ids: List[int],
        exclusion_reason: Optional[str] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Add multiple resource roles to a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
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
                result = self.create_exclusion_role(
                    contract_exclusion_id=contract_exclusion_id,
                    resource_role_id=resource_role_id,
                    exclusion_reason=exclusion_reason,
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "resource_role_id": resource_role_id,
                        "success": True,
                        "exclusion_id": result.item_id,
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
            "contract_exclusion_id": contract_exclusion_id,
            "total_resource_roles": len(resource_role_ids),
            "successful": len(successful),
            "failed": len(failed),
            "effective_date": effective_date.isoformat(),
            "results": results,
        }

    def remove_resource_roles_from_exclusion(
        self,
        contract_exclusion_id: int,
        resource_role_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Remove resource roles from a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion
            resource_role_ids: List of resource role IDs to remove

        Returns:
            Summary of the removal operation
        """
        results = []

        for resource_role_id in resource_role_ids:
            try:
                # Find the exclusion record
                filters = [
                    {
                        "field": "contractExclusionID",
                        "op": "eq",
                        "value": contract_exclusion_id,
                    },
                    {"field": "resourceRoleID", "op": "eq", "value": resource_role_id},
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
                            "resource_role_id": resource_role_id,
                            "success": True,
                            "exclusion_id": exclusion_id,
                        }
                    )
                else:
                    results.append(
                        {
                            "resource_role_id": resource_role_id,
                            "success": False,
                            "error": "No active exclusion found",
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
            "contract_exclusion_id": contract_exclusion_id,
            "total_resource_roles": len(resource_role_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_excluded_resource_roles_summary(
        self,
        contract_exclusion_id: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of excluded resource roles for a contract exclusion.

        Args:
            contract_exclusion_id: ID of the contract exclusion

        Returns:
            Summary of excluded resource roles
        """
        exclusions = self.get_exclusions_by_contract_exclusion(
            contract_exclusion_id, active_only=True
        )

        # Group by resource role
        resource_role_summary = {}
        for exclusion in exclusions:
            resource_role_id = exclusion.get("resourceRoleID")
            if resource_role_id not in resource_role_summary:
                resource_role_summary[resource_role_id] = {
                    "resource_role_id": resource_role_id,
                    "exclusion_count": 0,
                    "earliest_effective_date": None,
                    "latest_effective_date": None,
                    "exclusion_reasons": set(),
                }

            summary = resource_role_summary[resource_role_id]
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
        for summary in resource_role_summary.values():
            summary["exclusion_reasons"] = list(summary["exclusion_reasons"])

        return {
            "contract_exclusion_id": contract_exclusion_id,
            "total_excluded_resource_roles": len(resource_role_summary),
            "total_exclusion_records": len(exclusions),
            "excluded_resource_roles": list(resource_role_summary.values()),
        }

    def copy_exclusions_to_another_contract_exclusion(
        self,
        source_contract_exclusion_id: int,
        target_contract_exclusion_id: int,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Copy role exclusions from one contract exclusion to another.

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
                new_exclusion = self.create_exclusion_role(
                    contract_exclusion_id=target_contract_exclusion_id,
                    resource_role_id=exclusion.get("resourceRoleID"),
                    exclusion_reason=f"Copied from contract exclusion {source_contract_exclusion_id}",
                    effective_date=effective_date,
                )
                results.append(
                    {
                        "source_exclusion_id": exclusion.get("id"),
                        "resource_role_id": exclusion.get("resourceRoleID"),
                        "success": True,
                        "new_exclusion_id": new_exclusion.item_id,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "source_exclusion_id": exclusion.get("id"),
                        "resource_role_id": exclusion.get("resourceRoleID"),
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

    def get_contract_exclusions_for_resource_roles(
        self,
        resource_role_ids: List[int],
        active_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Get contract exclusions that affect multiple resource roles.

        Args:
            resource_role_ids: List of resource role IDs to check
            active_only: Whether to return only active exclusions

        Returns:
            Contract exclusions affecting the resource roles
        """
        results = {}

        for resource_role_id in resource_role_ids:
            exclusions = self.get_exclusions_by_resource_role(
                resource_role_id, active_only
            )

            contract_exclusion_ids = list(
                set(
                    e.get("contractExclusionID")
                    for e in exclusions
                    if e.get("contractExclusionID")
                )
            )

            results[resource_role_id] = {
                "resource_role_id": resource_role_id,
                "exclusion_count": len(exclusions),
                "contract_exclusion_ids": contract_exclusion_ids,
                "exclusions": exclusions,
            }

        return {
            "resource_role_ids": resource_role_ids,
            "results": results,
        }

    def get_role_exclusion_impact_analysis(
        self,
        resource_role_ids: List[int],
        date_from: date,
        date_to: date,
    ) -> Dict[str, Any]:
        """
        Analyze the impact of role exclusions over a time period.

        Args:
            resource_role_ids: List of resource role IDs to analyze
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Impact analysis of role exclusions
        """
        analysis_results = {}

        for resource_role_id in resource_role_ids:
            exclusions = self.get_exclusions_by_resource_role(
                resource_role_id, active_only=False
            )

            # Filter exclusions by date range
            relevant_exclusions = []
            for exclusion in exclusions:
                effective_date = exclusion.get("effectiveDate")
                expiration_date = exclusion.get("expirationDate")

                # Check if exclusion was active during the analysis period
                if effective_date and effective_date <= date_to.isoformat():
                    if not expiration_date or expiration_date >= date_from.isoformat():
                        relevant_exclusions.append(exclusion)

            contract_exclusion_ids = list(
                set(
                    e.get("contractExclusionID")
                    for e in relevant_exclusions
                    if e.get("contractExclusionID")
                )
            )

            analysis_results[resource_role_id] = {
                "resource_role_id": resource_role_id,
                "total_exclusions": len(relevant_exclusions),
                "affected_contract_exclusions": len(contract_exclusion_ids),
                "contract_exclusion_ids": contract_exclusion_ids,
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

    def validate_exclusion_configuration(
        self, contract_exclusion_id: int
    ) -> Dict[str, Any]:
        """
        Validate the resource role exclusion configuration.

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

        # Check for duplicate resource role exclusions
        resource_roles = {}
        for exclusion in exclusions:
            if not exclusion.get("isActive"):
                continue

            resource_role_id = exclusion.get("resourceRoleID")
            effective_date = exclusion.get("effectiveDate")

            if resource_role_id in resource_roles:
                issues.append(
                    {
                        "type": "duplicate_resource_role",
                        "message": f"Multiple active exclusions for resource role {resource_role_id}",
                        "exclusion_ids": [
                            resource_roles[resource_role_id],
                            exclusion.get("id"),
                        ],
                    }
                )
            else:
                resource_roles[resource_role_id] = exclusion.get("id")

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
            "unique_resource_roles": len(resource_roles),
            "validation_status": "valid" if not issues else "invalid",
            "issues": issues,
            "warnings": warnings,
        }
