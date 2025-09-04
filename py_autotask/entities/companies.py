"""
Companies (Accounts) entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import CompanyData, QueryFilter
from .base import BaseEntity


class CompaniesEntity(BaseEntity):
    """
    Handles all Company/Account-related operations for the Autotask API.

    Companies in Autotask represent customer accounts, prospects, and
    internal companies.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company(
        self,
        company_name: str,
        company_type: int = 1,  # 1 = Customer
        phone: Optional[str] = None,
        address1: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        **kwargs,
    ) -> CompanyData:
        """
        Create a new company with required and optional fields.

        Args:
            company_name: Name of the company
            company_type: Type of company (1=Customer, 2=Lead, 3=Prospect, etc.)
            phone: Primary phone number
            address1: Street address
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            **kwargs: Additional company fields

        Returns:
            Created company data
        """
        company_data = {
            "CompanyName": company_name,
            "CompanyType": company_type,
            **kwargs,
        }

        # Add optional address fields if provided
        if phone:
            company_data["Phone"] = phone
        if address1:
            company_data["Address1"] = address1
        if city:
            company_data["City"] = city
        if state:
            company_data["State"] = state
        if postal_code:
            company_data["PostalCode"] = postal_code
        if country:
            company_data["Country"] = country

        return self.create(company_data)

    def search_companies_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[CompanyData]:
        """
        Search for companies by name.

        Args:
            name: Company name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of companies to return

        Returns:
            List of matching companies
        """
        if exact_match:
            filters = [QueryFilter(field="CompanyName", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="CompanyName", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_companies_by_type(
        self, company_type: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[CompanyData]:
        """
        Get companies by type.

        Args:
            company_type: Company type (1=Customer, 2=Lead, 3=Prospect, etc.)
            active_only: Whether to return only active companies
            limit: Maximum number of companies to return

        Returns:
            List of companies of the specified type
        """
        filters = [QueryFilter(field="CompanyType", op="eq", value=company_type)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_customer_companies(
        self, active_only: bool = True, limit: Optional[int] = None
    ) -> List[CompanyData]:
        """
        Get all customer companies.

        Args:
            active_only: Whether to return only active companies
            limit: Maximum number of companies to return

        Returns:
            List of customer companies
        """
        return self.get_companies_by_type(
            company_type=1, active_only=active_only, limit=limit  # Customer type
        )

    def get_prospect_companies(
        self, active_only: bool = True, limit: Optional[int] = None
    ) -> List[CompanyData]:
        """
        Get all prospect companies.

        Args:
            active_only: Whether to return only active companies
            limit: Maximum number of companies to return

        Returns:
            List of prospect companies
        """
        return self.get_companies_by_type(
            company_type=3, active_only=active_only, limit=limit  # Prospect type
        )

    def get_company_contacts(self, company_id: int) -> List[Dict[str, Any]]:
        """
        Get all contacts for a specific company.

        Args:
            company_id: ID of the company

        Returns:
            List of contacts for the company
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]
        return self.client.query("Contacts", filters=filters)

    def get_company_tickets(
        self,
        company_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all tickets for a specific company.

        Args:
            company_id: ID of the company
            status_filter: Optional status filter ('open', 'closed', etc.)
            limit: Maximum number of tickets to return

        Returns:
            List of tickets for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        if status_filter:
            # Map common status filters to Autotask status IDs
            status_map = {
                "open": [1, 8, 9, 10, 11],
                "closed": [5],
                "new": [1],
                "in_progress": [8, 9, 10, 11],
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        return self.client.query("Tickets", filters=filters, max_records=limit)

    def get_company_projects(
        self, company_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all projects for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active projects
            limit: Maximum number of projects to return

        Returns:
            List of projects for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        if active_only:
            filters.append(
                QueryFilter(field="Status", op="ne", value=5)
            )  # Not Complete

        return self.client.query("Projects", filters=filters, max_records=limit)

    def get_company_contracts(
        self, company_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all contracts for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active contracts
            limit: Maximum number of contracts to return

        Returns:
            List of contracts for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="Status", op="eq", value=1))  # Active

        return self.client.query("Contracts", filters=filters, max_records=limit)

    def update_company_address(
        self,
        company_id: int,
        address1: Optional[str] = None,
        address2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
    ) -> CompanyData:
        """
        Update company address information.

        Args:
            company_id: ID of company to update
            address1: Street address line 1
            address2: Street address line 2
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name

        Returns:
            Updated company data
        """
        update_data = {}

        if address1 is not None:
            update_data["Address1"] = address1
        if address2 is not None:
            update_data["Address2"] = address2
        if city is not None:
            update_data["City"] = city
        if state is not None:
            update_data["State"] = state
        if postal_code is not None:
            update_data["PostalCode"] = postal_code
        if country is not None:
            update_data["Country"] = country

        return self.update_by_id(company_id, update_data)

    def activate_company(self, company_id: int) -> CompanyData:
        """
        Activate a company.

        Args:
            company_id: ID of company to activate

        Returns:
            Updated company data
        """
        return self.update_by_id(company_id, {"Active": True})

    def deactivate_company(self, company_id: int) -> CompanyData:
        """
        Deactivate a company.

        Args:
            company_id: ID of company to deactivate

        Returns:
            Updated company data
        """
        return self.update_by_id(company_id, {"Active": False})

    def get_companies_by_location(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Get companies by location criteria.

        Args:
            city: City to filter by
            state: State/province to filter by
            country: Country to filter by
            postal_code: Postal code to filter by
            limit: Maximum number of companies to return

        Returns:
            List of companies matching location criteria
        """
        filters = []

        if city:
            filters.append(QueryFilter(field="City", op="eq", value=city))
        if state:
            filters.append(QueryFilter(field="State", op="eq", value=state))
        if country:
            filters.append(QueryFilter(field="Country", op="eq", value=country))
        if postal_code:
            filters.append(QueryFilter(field="PostalCode", op="eq", value=postal_code))

        if not filters:
            raise ValueError("At least one location criteria must be provided")

        return self.query(filters=filters, max_records=limit)
