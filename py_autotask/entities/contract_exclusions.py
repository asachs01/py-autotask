"""
Contract Exclusions entity for Autotask API.

This module provides the ContractExclusionsEntity class for managing
contract exclusions within the Autotask system.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ContractExclusionsEntity(BaseEntity):
    """
    Entity for managing Autotask Contract Exclusions.

    Contract Exclusions represent exclusion rules for contracts,
    including resource exclusions, service exclusions, and date-based exclusions.
    """

    def __init__(self, client, entity_name="ContractExclusions"):
        """Initialize the Contract Exclusions entity."""
        super().__init__(client, entity_name)

    def create(self, contract_exclusion_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new contract exclusion.

        Args:
            contract_exclusion_data: Dictionary containing contract exclusion information
                Required fields:
                - contractID: ID of the associated contract
                - exclusionType: Type of exclusion (Resource, Service, Date, etc.)
                Optional fields:
                - resourceID: ID of excluded resource (for resource exclusions)
                - serviceID: ID of excluded service (for service exclusions)
                - startDate: Start date of exclusion period
                - endDate: End date of exclusion period
                - description: Description of the exclusion
                - reason: Reason for the exclusion
                - isActive: Whether the exclusion is active

        Returns:
            CreateResponse: Response containing created contract exclusion data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["contractID", "exclusionType"]
        self._validate_required_fields(contract_exclusion_data, required_fields)

        # Validate exclusion-specific requirements
        self._validate_exclusion_requirements(contract_exclusion_data)

        return self._create(contract_exclusion_data)

    def get(self, contract_exclusion_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a contract exclusion by ID.

        Args:
            contract_exclusion_id: The contract exclusion ID

        Returns:
            Dictionary containing contract exclusion data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(contract_exclusion_id)

    def update(
        self, contract_exclusion_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing contract exclusion.

        Args:
            contract_exclusion_id: The contract exclusion ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated contract exclusion data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(contract_exclusion_id, update_data)

    def delete(self, contract_exclusion_id: int) -> bool:
        """
        Delete a contract exclusion.

        Args:
            contract_exclusion_id: The contract exclusion ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(contract_exclusion_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query contract exclusions with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing contract exclusion data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_contract(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get all contract exclusions for a specific contract.

        Args:
            contract_id: The contract ID

        Returns:
            List of contract exclusions for the specified contract

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]
        return self.query(filters)

    def get_by_type(
        self, exclusion_type: str, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contract exclusions by type, optionally filtered by contract.

        Args:
            exclusion_type: The exclusion type to filter by
            contract_id: Optional contract ID to filter by

        Returns:
            List of contract exclusions of the specified type

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="exclusionType", op="eq", value=exclusion_type)]

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        return self.query(filters)

    def get_resource_exclusions(
        self, contract_id: int, resource_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resource exclusions for a contract, optionally filtered by resource.

        Args:
            contract_id: The contract ID
            resource_id: Optional resource ID to filter by

        Returns:
            List of resource exclusions

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="contractID", op="eq", value=contract_id),
            QueryFilter(field="exclusionType", op="eq", value="Resource"),
        ]

        if resource_id:
            filters.append(QueryFilter(field="resourceID", op="eq", value=resource_id))

        return self.query(filters)

    def get_service_exclusions(
        self, contract_id: int, service_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get service exclusions for a contract, optionally filtered by service.

        Args:
            contract_id: The contract ID
            service_id: Optional service ID to filter by

        Returns:
            List of service exclusions

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="contractID", op="eq", value=contract_id),
            QueryFilter(field="exclusionType", op="eq", value="Service"),
        ]

        if service_id:
            filters.append(QueryFilter(field="serviceID", op="eq", value=service_id))

        return self.query(filters)

    def get_active_exclusions(
        self, contract_id: int, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active contract exclusions for a specific date.

        Args:
            contract_id: The contract ID
            as_of_date: Date to check exclusions for (default: today)

        Returns:
            List of active contract exclusions

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if as_of_date is None:
            as_of_date = date.today()

        filters = [
            QueryFilter(field="contractID", op="eq", value=contract_id),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        # Add date range filters if exclusion has date constraints
        all_exclusions = self.query(filters)
        active_exclusions = []

        for exclusion in all_exclusions:
            start_date = exclusion.get("startDate")
            end_date = exclusion.get("endDate")

            # If no date constraints, it's always active
            if not start_date and not end_date:
                active_exclusions.append(exclusion)
                continue

            # Check if current date falls within exclusion period
            is_in_period = True

            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(
                        start_date.replace("Z", "+00:00")
                    ).date()
                if as_of_date < start_date:
                    is_in_period = False

            if end_date and is_in_period:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(
                        end_date.replace("Z", "+00:00")
                    ).date()
                if as_of_date > end_date:
                    is_in_period = False

            if is_in_period:
                active_exclusions.append(exclusion)

        return active_exclusions

    def check_exclusion(
        self,
        contract_id: int,
        exclusion_type: str,
        resource_id: Optional[int] = None,
        service_id: Optional[int] = None,
        check_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Check if a specific resource or service is excluded from a contract.

        Args:
            contract_id: The contract ID
            exclusion_type: Type of exclusion to check (Resource, Service, etc.)
            resource_id: Resource ID to check (for resource exclusions)
            service_id: Service ID to check (for service exclusions)
            check_date: Date to check exclusions for (default: today)

        Returns:
            Dictionary with exclusion check results:
            - is_excluded: Boolean indicating if item is excluded
            - exclusion_count: Number of matching exclusions
            - exclusions: List of matching exclusions
            - reason: Reason for exclusion if excluded

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if check_date is None:
            check_date = date.today()

        # Get active exclusions for the contract
        active_exclusions = self.get_active_exclusions(contract_id, check_date)

        # Filter by exclusion type and specific IDs
        matching_exclusions = []
        for exclusion in active_exclusions:
            if exclusion.get("exclusionType") != exclusion_type:
                continue

            # Check resource exclusions
            if exclusion_type == "Resource" and resource_id:
                if exclusion.get("resourceID") == resource_id:
                    matching_exclusions.append(exclusion)

            # Check service exclusions
            elif exclusion_type == "Service" and service_id:
                if exclusion.get("serviceID") == service_id:
                    matching_exclusions.append(exclusion)

            # Check general exclusions (no specific ID required)
            elif exclusion_type not in ["Resource", "Service"]:
                matching_exclusions.append(exclusion)

        is_excluded = len(matching_exclusions) > 0
        reason = None

        if is_excluded and matching_exclusions:
            # Get the most specific reason
            reason = matching_exclusions[0].get("reason") or matching_exclusions[0].get(
                "description"
            )

        return {
            "is_excluded": is_excluded,
            "exclusion_count": len(matching_exclusions),
            "exclusions": matching_exclusions,
            "reason": reason,
            "check_date": check_date.isoformat(),
            "exclusion_type": exclusion_type,
        }

    def bulk_create_exclusions(
        self, contract_id: int, exclusions_data: List[Dict[str, Any]]
    ) -> List[CreateResponse]:
        """
        Create multiple contract exclusions in bulk.

        Args:
            contract_id: The contract ID
            exclusions_data: List of exclusion data dictionaries

        Returns:
            List of CreateResponse objects for each created exclusion

        Raises:
            AutotaskAPIError: If any API request fails
        """
        results = []

        for exclusion_data in exclusions_data:
            # Ensure contract ID is set
            exclusion_data["contractID"] = contract_id

            try:
                result = self.create(exclusion_data)
                results.append(result)
            except Exception as e:
                # Log error but continue with other exclusions
                self.logger.error(f"Failed to create exclusion: {e}")
                results.append({"error": str(e), "exclusion_data": exclusion_data})

        return results

    def get_exclusion_summary(self, contract_id: int) -> Dict[str, Any]:
        """
        Get a summary of all exclusions for a contract.

        Args:
            contract_id: The contract ID

        Returns:
            Dictionary with exclusion summary:
            - total_exclusions: Total number of exclusions
            - active_exclusions: Number of active exclusions
            - resource_exclusions: Number of resource exclusions
            - service_exclusions: Number of service exclusions
            - date_exclusions: Number of date-based exclusions
            - exclusion_types: List of unique exclusion types

        Raises:
            AutotaskAPIError: If the API request fails
        """
        all_exclusions = self.get_by_contract(contract_id)
        active_exclusions = self.get_active_exclusions(contract_id)

        summary = {
            "contract_id": contract_id,
            "total_exclusions": len(all_exclusions),
            "active_exclusions": len(active_exclusions),
            "resource_exclusions": 0,
            "service_exclusions": 0,
            "date_exclusions": 0,
            "exclusion_types": set(),
        }

        for exclusion in all_exclusions:
            exclusion_type = exclusion.get("exclusionType", "")
            summary["exclusion_types"].add(exclusion_type)

            # Count by type
            if exclusion_type == "Resource":
                summary["resource_exclusions"] += 1
            elif exclusion_type == "Service":
                summary["service_exclusions"] += 1
            elif exclusion.get("startDate") or exclusion.get("endDate"):
                summary["date_exclusions"] += 1

        # Convert set to list for JSON serialization
        summary["exclusion_types"] = list(summary["exclusion_types"])

        return summary

    def _validate_exclusion_requirements(self, exclusion_data: Dict[str, Any]) -> None:
        """
        Validate exclusion-specific requirements.

        Args:
            exclusion_data: Exclusion data to validate

        Raises:
            ValueError: If exclusion requirements are not met
        """
        exclusion_type = exclusion_data.get("exclusionType")

        if exclusion_type == "Resource":
            if not exclusion_data.get("resourceID"):
                raise ValueError("Resource ID is required for resource exclusions")

        elif exclusion_type == "Service":
            if not exclusion_data.get("serviceID"):
                raise ValueError("Service ID is required for service exclusions")

        # Validate date range if provided
        start_date = exclusion_data.get("startDate")
        end_date = exclusion_data.get("endDate")

        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                ).date()
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                ).date()

            if start_date >= end_date:
                raise ValueError("Exclusion end date must be after start date")

    def validate_exclusion_data(self, exclusion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate contract exclusion data.

        Args:
            exclusion_data: Exclusion data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["contractID", "exclusionType"]
        for field in required_fields:
            if field not in exclusion_data or exclusion_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate exclusion-specific requirements
        try:
            self._validate_exclusion_requirements(exclusion_data)
        except ValueError as e:
            errors.append(str(e))

        # Check for potential conflicts
        exclusion_type = exclusion_data.get("exclusionType")
        if exclusion_type == "Resource" and exclusion_data.get("serviceID"):
            warnings.append(
                "Service ID specified for resource exclusion (will be ignored)"
            )
        elif exclusion_type == "Service" and exclusion_data.get("resourceID"):
            warnings.append(
                "Resource ID specified for service exclusion (will be ignored)"
            )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
