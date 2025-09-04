"""
Contract Blocks entity for Autotask API.

This module provides the ContractBlocksEntity class for managing
contract billing blocks within the Autotask system.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ContractBlocksEntity(BaseEntity):
    """
    Entity for managing Autotask Contract Blocks.

    Contract Blocks represent billing blocks associated with contracts,
    including time blocks, expense blocks, and other billable units.
    """

    def __init__(self, client, entity_name="ContractBlocks"):
        """Initialize the Contract Blocks entity."""
        super().__init__(client, entity_name)

    def create(self, contract_block_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new contract block.

        Args:
            contract_block_data: Dictionary containing contract block information
                Required fields:
                - contractID: ID of the associated contract
                - blockType: Type of block (1=Time, 2=Money, 3=Both)
                - dateBegin: Start date of the block
                - dateEnd: End date of the block
                Optional fields:
                - hours: Number of hours in the block
                - hourlyRate: Hourly rate for time blocks
                - blockValue: Monetary value of the block
                - isPaid: Whether the block is paid
                - paymentTerms: Payment terms
                - paymentType: Payment type
                - status: Block status

        Returns:
            CreateResponse: Response containing created contract block data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["contractID", "blockType", "dateBegin", "dateEnd"]
        self._validate_required_fields(contract_block_data, required_fields)

        # Validate date range
        self._validate_date_range(contract_block_data)

        return self._create(contract_block_data)

    def get(self, contract_block_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a contract block by ID.

        Args:
            contract_block_id: The contract block ID

        Returns:
            Dictionary containing contract block data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(contract_block_id)

    def update(
        self, contract_block_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing contract block.

        Args:
            contract_block_id: The contract block ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated contract block data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        # Validate date range if dates are being updated
        if "dateBegin" in update_data or "dateEnd" in update_data:
            # Get current data to validate complete date range
            current_block = self.get(contract_block_id)
            if current_block:
                merged_data = {**current_block, **update_data}
                self._validate_date_range(merged_data)

        return self._update(contract_block_id, update_data)

    def delete(self, contract_block_id: int) -> bool:
        """
        Delete a contract block.

        Args:
            contract_block_id: The contract block ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(contract_block_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query contract blocks with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing contract block data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_contract(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get all contract blocks for a specific contract.

        Args:
            contract_id: The contract ID

        Returns:
            List of contract blocks for the specified contract

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]
        return self.query(filters)

    def get_active_blocks(
        self, contract_id: Optional[int] = None, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active contract blocks, optionally filtered by contract and date.

        Args:
            contract_id: Optional contract ID to filter by
            as_of_date: Optional date to check block activity (default: today)

        Returns:
            List of active contract blocks

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = []

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        # Filter by date range if specified
        if as_of_date is None:
            as_of_date = date.today()

        filters.extend(
            [
                QueryFilter(field="dateBegin", op="lte", value=as_of_date.isoformat()),
                QueryFilter(field="dateEnd", op="gte", value=as_of_date.isoformat()),
            ]
        )

        return self.query(filters)

    def get_blocks_by_type(
        self, contract_id: int, block_type: int
    ) -> List[Dict[str, Any]]:
        """
        Get contract blocks by type for a specific contract.

        Args:
            contract_id: The contract ID
            block_type: Block type (1=Time, 2=Money, 3=Both)

        Returns:
            List of contract blocks of the specified type

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="contractID", op="eq", value=contract_id),
            QueryFilter(field="blockType", op="eq", value=block_type),
        ]
        return self.query(filters)

    def get_time_blocks(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get time blocks for a specific contract.

        Args:
            contract_id: The contract ID

        Returns:
            List of time blocks (blockType = 1 or 3)

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get blocks where blockType is 1 (Time) or 3 (Both)
        time_blocks = []
        time_blocks.extend(self.get_blocks_by_type(contract_id, 1))  # Time only
        time_blocks.extend(self.get_blocks_by_type(contract_id, 3))  # Both
        return time_blocks

    def get_money_blocks(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get money blocks for a specific contract.

        Args:
            contract_id: The contract ID

        Returns:
            List of money blocks (blockType = 2 or 3)

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get blocks where blockType is 2 (Money) or 3 (Both)
        money_blocks = []
        money_blocks.extend(self.get_blocks_by_type(contract_id, 2))  # Money only
        money_blocks.extend(self.get_blocks_by_type(contract_id, 3))  # Both
        return money_blocks

    def calculate_block_utilization(
        self,
        contract_block_data: Dict[str, Any],
        used_hours: Optional[float] = None,
        used_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate utilization for a contract block.

        Args:
            contract_block_data: Contract block data
            used_hours: Hours used against the block (for time blocks)
            used_amount: Amount used against the block (for money blocks)

        Returns:
            Dictionary with utilization metrics:
            - block_type: Type of block
            - total_hours: Total hours in block (if applicable)
            - used_hours: Hours used (if applicable)
            - remaining_hours: Hours remaining (if applicable)
            - hours_utilization_pct: Percentage of hours used
            - total_value: Total monetary value (if applicable)
            - used_value: Value used (if applicable)
            - remaining_value: Value remaining (if applicable)
            - value_utilization_pct: Percentage of value used

        Raises:
            ValueError: If required data is missing
        """
        block_type = contract_block_data.get("blockType")
        if not block_type:
            raise ValueError("Block type is required")

        result = {
            "block_type": block_type,
            "block_id": contract_block_data.get("id"),
            "contract_id": contract_block_data.get("contractID"),
        }

        # Handle time blocks (type 1 or 3)
        if block_type in [1, 3]:
            total_hours = contract_block_data.get("hours", 0)
            used_hours = used_hours or 0
            remaining_hours = max(0, total_hours - used_hours)
            hours_utilization = (
                (used_hours / total_hours * 100) if total_hours > 0 else 0
            )

            result.update(
                {
                    "total_hours": total_hours,
                    "used_hours": used_hours,
                    "remaining_hours": remaining_hours,
                    "hours_utilization_pct": hours_utilization,
                }
            )

        # Handle money blocks (type 2 or 3)
        if block_type in [2, 3]:
            total_value = contract_block_data.get("blockValue", 0)
            used_value = used_amount or 0
            remaining_value = max(0, total_value - used_value)
            value_utilization = (
                (used_value / total_value * 100) if total_value > 0 else 0
            )

            result.update(
                {
                    "total_value": total_value,
                    "used_value": used_value,
                    "remaining_value": remaining_value,
                    "value_utilization_pct": value_utilization,
                }
            )

        return result

    def get_block_summary(self, contract_id: int) -> Dict[str, Any]:
        """
        Get a summary of all blocks for a contract.

        Args:
            contract_id: The contract ID

        Returns:
            Dictionary with block summary:
            - total_blocks: Total number of blocks
            - active_blocks: Number of active blocks
            - time_blocks: Number of time blocks
            - money_blocks: Number of money blocks
            - total_hours: Total hours across all time blocks
            - total_value: Total value across all money blocks

        Raises:
            AutotaskAPIError: If the API request fails
        """
        all_blocks = self.get_by_contract(contract_id)
        active_blocks = self.get_active_blocks(contract_id)

        summary = {
            "contract_id": contract_id,
            "total_blocks": len(all_blocks),
            "active_blocks": len(active_blocks),
            "time_blocks": 0,
            "money_blocks": 0,
            "total_hours": 0,
            "total_value": 0,
        }

        for block in all_blocks:
            block_type = block.get("blockType", 0)

            # Count block types
            if block_type in [1, 3]:  # Time blocks
                summary["time_blocks"] += 1
                summary["total_hours"] += block.get("hours", 0)

            if block_type in [2, 3]:  # Money blocks
                summary["money_blocks"] += 1
                summary["total_value"] += block.get("blockValue", 0)

        return summary

    def _validate_date_range(self, block_data: Dict[str, Any]) -> None:
        """
        Validate that the date range is valid.

        Args:
            block_data: Block data containing dateBegin and dateEnd

        Raises:
            ValueError: If date range is invalid
        """
        date_begin = block_data.get("dateBegin")
        date_end = block_data.get("dateEnd")

        if not date_begin or not date_end:
            return  # Skip validation if dates are missing

        # Convert to date objects if they're strings
        if isinstance(date_begin, str):
            date_begin = datetime.fromisoformat(
                date_begin.replace("Z", "+00:00")
            ).date()
        elif isinstance(date_begin, datetime):
            date_begin = date_begin.date()

        if isinstance(date_end, str):
            date_end = datetime.fromisoformat(date_end.replace("Z", "+00:00")).date()
        elif isinstance(date_end, datetime):
            date_end = date_end.date()

        if date_begin >= date_end:
            raise ValueError("Block end date must be after begin date")

    def validate_block_data(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate contract block data.

        Args:
            block_data: Block data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate block type
        block_type = block_data.get("blockType")
        if not block_type or block_type not in [1, 2, 3]:
            errors.append("Block type must be 1 (Time), 2 (Money), or 3 (Both)")

        # Validate date range
        try:
            self._validate_date_range(block_data)
        except ValueError as e:
            errors.append(str(e))

        # Validate time block specific fields
        if block_type in [1, 3]:
            hours = block_data.get("hours")
            if hours is not None and hours <= 0:
                errors.append("Hours must be greater than 0 for time blocks")

            hourly_rate = block_data.get("hourlyRate")
            if hourly_rate is not None and hourly_rate < 0:
                errors.append("Hourly rate cannot be negative")

        # Validate money block specific fields
        if block_type in [2, 3]:
            block_value = block_data.get("blockValue")
            if block_value is not None and block_value <= 0:
                errors.append("Block value must be greater than 0 for money blocks")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
