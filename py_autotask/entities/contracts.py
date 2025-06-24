"""
Contracts entity for Autotask API operations.
"""

from typing import List, Optional

from ..types import ContractData, QueryFilter
from .base import BaseEntity


class ContractsEntity(BaseEntity):
    """
    Handles all Contract-related operations for the Autotask API.

    Contracts in Autotask represent service agreements, maintenance
    contracts, and other ongoing service arrangements with customers.
    """

    def __init__(self, client, entity_name: str = "Contracts"):
        super().__init__(client, entity_name)

    def create_contract(
        self,
        contract_name: str,
        account_id: int,
        contract_type: int = 1,  # 1 = Recurring Service
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract_value: Optional[float] = None,
        **kwargs,
    ) -> ContractData:
        """
        Create a new contract with required and optional fields.

        Args:
            contract_name: Name of the contract
            account_id: ID of the associated account/company
            contract_type: Type of contract (1=Recurring Service, etc.)
            start_date: Contract start date (ISO format)
            end_date: Contract end date (ISO format)
            contract_value: Total value of the contract
            **kwargs: Additional contract fields

        Returns:
            Created contract data
        """
        contract_data = {
            "ContractName": contract_name,
            "AccountID": account_id,
            "ContractType": contract_type,
            **kwargs,
        }

        if start_date:
            contract_data["StartDate"] = start_date
        if end_date:
            contract_data["EndDate"] = end_date
        if contract_value is not None:
            contract_data["ContractValue"] = contract_value

        return self.create(contract_data)

    def get_contracts_by_account(
        self, account_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[ContractData]:
        """
        Get all contracts for a specific account.

        Args:
            account_id: Account ID to filter by
            active_only: Whether to return only active contracts
            limit: Maximum number of contracts to return

        Returns:
            List of contracts for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        if active_only:
            filters.append(QueryFilter(field="Status", op="eq", value=1))  # Active

        return self.query(filters=filters, max_records=limit)

    def get_active_contracts(self, limit: Optional[int] = None) -> List[ContractData]:
        """
        Get all active contracts.

        Args:
            limit: Maximum number of contracts to return

        Returns:
            List of active contracts
        """
        filters = [QueryFilter(field="Status", op="eq", value=1)]  # Active
        return self.query(filters=filters, max_records=limit)

    def get_expiring_contracts(
        self, days_ahead: int = 30, limit: Optional[int] = None
    ) -> List[ContractData]:
        """
        Get contracts expiring within a specified number of days.

        Args:
            days_ahead: Number of days to look ahead for expiring contracts
            limit: Maximum number of contracts to return

        Returns:
            List of expiring contracts
        """
        from datetime import datetime, timedelta

        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

        filters = [
            QueryFilter(field="EndDate", op="lte", value=future_date),
            QueryFilter(field="Status", op="eq", value=1),  # Active
        ]

        return self.query(filters=filters, max_records=limit)
