"""
Contract Adjustments entity for Autotask API.

This module provides the ContractAdjustmentsEntity class for managing
contract adjustments within the Autotask system.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ContractAdjustmentsEntity(BaseEntity):
    """
    Entity for managing Autotask Contract Adjustments.

    Contract Adjustments represent modifications to contracts,
    including pricing adjustments, service changes, and other contract modifications.
    """

    def __init__(self, client, entity_name="ContractAdjustments"):
        """Initialize the Contract Adjustments entity."""
        super().__init__(client, entity_name)

    def create(self, contract_adjustment_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new contract adjustment.

        Args:
            contract_adjustment_data: Dictionary containing contract adjustment information
                Required fields:
                - contractID: ID of the associated contract
                - adjustmentType: Type of adjustment
                - effectiveDate: Date when adjustment becomes effective
                - amount: Adjustment amount
                Optional fields:
                - description: Description of the adjustment
                - reason: Reason for the adjustment
                - approvedBy: User who approved the adjustment
                - approvalDate: Date of approval
                - status: Adjustment status
                - notes: Additional notes

        Returns:
            CreateResponse: Response containing created contract adjustment data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["contractID", "adjustmentType", "effectiveDate", "amount"]
        self._validate_required_fields(contract_adjustment_data, required_fields)

        return self._create(contract_adjustment_data)

    def get(self, contract_adjustment_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a contract adjustment by ID.

        Args:
            contract_adjustment_id: The contract adjustment ID

        Returns:
            Dictionary containing contract adjustment data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(contract_adjustment_id)

    def update(
        self, contract_adjustment_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing contract adjustment.

        Args:
            contract_adjustment_id: The contract adjustment ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated contract adjustment data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(contract_adjustment_id, update_data)

    def delete(self, contract_adjustment_id: int) -> bool:
        """
        Delete a contract adjustment.

        Args:
            contract_adjustment_id: The contract adjustment ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(contract_adjustment_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query contract adjustments with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing contract adjustment data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_contract(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get all contract adjustments for a specific contract.

        Args:
            contract_id: The contract ID

        Returns:
            List of contract adjustments for the specified contract

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]
        return self.query(filters)

    def get_by_type(
        self, adjustment_type: str, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contract adjustments by type, optionally filtered by contract.

        Args:
            adjustment_type: The adjustment type to filter by
            contract_id: Optional contract ID to filter by

        Returns:
            List of contract adjustments of the specified type

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="adjustmentType", op="eq", value=adjustment_type)]

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        return self.query(filters)

    def get_pending_adjustments(
        self, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending contract adjustments, optionally filtered by contract.

        Args:
            contract_id: Optional contract ID to filter by

        Returns:
            List of pending contract adjustments

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="eq", value="Pending")]

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        return self.query(filters)

    def get_approved_adjustments(
        self, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get approved contract adjustments, optionally filtered by contract.

        Args:
            contract_id: Optional contract ID to filter by

        Returns:
            List of approved contract adjustments

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="eq", value="Approved")]

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        return self.query(filters)

    def get_adjustments_by_date_range(
        self, start_date: date, end_date: date, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contract adjustments within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            contract_id: Optional contract ID to filter by

        Returns:
            List of contract adjustments within the date range

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="effectiveDate", op="gte", value=start_date.isoformat()),
            QueryFilter(field="effectiveDate", op="lte", value=end_date.isoformat()),
        ]

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        return self.query(filters)

    def approve_adjustment(
        self,
        contract_adjustment_id: int,
        approved_by: int,
        approval_notes: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Approve a contract adjustment.

        Args:
            contract_adjustment_id: The contract adjustment ID to approve
            approved_by: User ID of the approver
            approval_notes: Optional approval notes

        Returns:
            UpdateResponse: Response containing updated contract adjustment data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {
            "status": "Approved",
            "approvedBy": approved_by,
            "approvalDate": datetime.now().isoformat(),
        }

        if approval_notes:
            update_data["notes"] = approval_notes

        return self.update(contract_adjustment_id, update_data)

    def reject_adjustment(
        self,
        contract_adjustment_id: int,
        rejected_by: int,
        rejection_reason: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Reject a contract adjustment.

        Args:
            contract_adjustment_id: The contract adjustment ID to reject
            rejected_by: User ID of the rejector
            rejection_reason: Optional rejection reason

        Returns:
            UpdateResponse: Response containing updated contract adjustment data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {
            "status": "Rejected",
            "rejectedBy": rejected_by,
            "rejectionDate": datetime.now().isoformat(),
        }

        if rejection_reason:
            update_data["rejectionReason"] = rejection_reason

        return self.update(contract_adjustment_id, update_data)

    def calculate_adjustment_impact(
        self, contract_adjustment_data: Dict[str, Any], contract_value: float
    ) -> Dict[str, Any]:
        """
        Calculate the impact of a contract adjustment.

        Args:
            contract_adjustment_data: Contract adjustment data
            contract_value: Current contract value

        Returns:
            Dictionary with impact calculations:
            - adjustment_amount: The adjustment amount
            - adjustment_percentage: Percentage change
            - new_contract_value: New contract value after adjustment
            - impact_type: Type of impact (increase/decrease)

        Raises:
            ValueError: If required data is missing
        """
        adjustment_amount = contract_adjustment_data.get("amount")
        if adjustment_amount is None:
            raise ValueError("Adjustment amount is required")

        adjustment_amount = float(adjustment_amount)
        new_contract_value = contract_value + adjustment_amount

        # Calculate percentage change
        if contract_value != 0:
            adjustment_percentage = (adjustment_amount / contract_value) * 100
        else:
            adjustment_percentage = 0

        # Determine impact type
        if adjustment_amount > 0:
            impact_type = "increase"
        elif adjustment_amount < 0:
            impact_type = "decrease"
        else:
            impact_type = "neutral"

        return {
            "adjustment_amount": adjustment_amount,
            "adjustment_percentage": adjustment_percentage,
            "new_contract_value": new_contract_value,
            "original_contract_value": contract_value,
            "impact_type": impact_type,
            "adjustment_type": contract_adjustment_data.get("adjustmentType"),
            "effective_date": contract_adjustment_data.get("effectiveDate"),
        }

    def get_adjustment_summary(self, contract_id: int) -> Dict[str, Any]:
        """
        Get a summary of all adjustments for a contract.

        Args:
            contract_id: The contract ID

        Returns:
            Dictionary with adjustment summary:
            - total_adjustments: Total number of adjustments
            - pending_adjustments: Number of pending adjustments
            - approved_adjustments: Number of approved adjustments
            - rejected_adjustments: Number of rejected adjustments
            - total_adjustment_amount: Sum of all approved adjustments
            - positive_adjustments: Number of positive adjustments
            - negative_adjustments: Number of negative adjustments

        Raises:
            AutotaskAPIError: If the API request fails
        """
        all_adjustments = self.get_by_contract(contract_id)

        summary = {
            "contract_id": contract_id,
            "total_adjustments": len(all_adjustments),
            "pending_adjustments": 0,
            "approved_adjustments": 0,
            "rejected_adjustments": 0,
            "total_adjustment_amount": 0,
            "positive_adjustments": 0,
            "negative_adjustments": 0,
        }

        for adjustment in all_adjustments:
            status = adjustment.get("status", "").lower()
            amount = float(adjustment.get("amount", 0))

            # Count by status
            if status == "pending":
                summary["pending_adjustments"] += 1
            elif status == "approved":
                summary["approved_adjustments"] += 1
                summary["total_adjustment_amount"] += amount
            elif status == "rejected":
                summary["rejected_adjustments"] += 1

            # Count by amount direction
            if amount > 0:
                summary["positive_adjustments"] += 1
            elif amount < 0:
                summary["negative_adjustments"] += 1

        return summary

    def validate_adjustment_data(
        self, adjustment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate contract adjustment data.

        Args:
            adjustment_data: Adjustment data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["contractID", "adjustmentType", "effectiveDate", "amount"]
        for field in required_fields:
            if field not in adjustment_data or adjustment_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate amount
        amount = adjustment_data.get("amount")
        if amount is not None:
            try:
                amount_float = float(amount)
                if amount_float == 0:
                    warnings.append("Adjustment amount is zero")
            except (ValueError, TypeError):
                errors.append("Amount must be a valid number")

        # Validate effective date
        effective_date = adjustment_data.get("effectiveDate")
        if effective_date:
            try:
                if isinstance(effective_date, str):
                    datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Effective date must be a valid date")

        # Validate adjustment type
        adjustment_type = adjustment_data.get("adjustmentType")
        if adjustment_type and not isinstance(adjustment_type, str):
            errors.append("Adjustment type must be a string")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
