"""
Accounts Entity for py-autotask

This module provides the AccountsEntity class for managing accounts
in Autotask. Accounts represent organizational entities that can include
companies, divisions, and other business units.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class AccountsEntity(BaseEntity):
    """
    Manages Autotask Accounts - organizational account structures.

    Accounts represent organizational entities in Autotask that can include
    companies, divisions, departments, and other business units. They provide
    hierarchical organization and relationship management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Accounts"

    def create_account(
        self,
        account_name: str,
        account_type: str,
        phone: Optional[str] = None,
        address1: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new account.

        Args:
            account_name: Name of the account
            account_type: Type of account (Customer, Lead, Prospect, etc.)
            phone: Primary phone number
            address1: Address line 1
            city: City
            state: State/province
            postal_code: Postal code
            country: Country
            **kwargs: Additional fields for the account

        Returns:
            Create response with new account ID
        """
        account_data = {
            "accountName": account_name,
            "accountType": account_type,
            **kwargs,
        }

        if phone:
            account_data["phone"] = phone
        if address1:
            account_data["address1"] = address1
        if city:
            account_data["city"] = city
        if state:
            account_data["state"] = state
        if postal_code:
            account_data["postalCode"] = postal_code
        if country:
            account_data["country"] = country

        return self.create(account_data)

    def get_accounts_by_type(
        self, account_type: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get accounts by type.

        Args:
            account_type: Type of accounts to retrieve
            active_only: Whether to only return active accounts

        Returns:
            List of accounts of the specified type
        """
        filters = [build_equality_filter("accountType", account_type)]

        if active_only:
            filters.append(build_active_filter(True))

        return self.query(filters=combine_filters(filters))

    def get_customer_accounts(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get customer accounts.

        Args:
            include_inactive: Whether to include inactive accounts

        Returns:
            List of customer accounts
        """
        filters = [build_equality_filter("accountType", "Customer")]

        if not include_inactive:
            filters.append(build_active_filter(True))

        return self.query(filters=combine_filters(filters))

    def get_prospect_accounts(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get prospect accounts.

        Args:
            include_inactive: Whether to include inactive accounts

        Returns:
            List of prospect accounts
        """
        filters = [build_equality_filter("accountType", "Prospect")]

        if not include_inactive:
            filters.append(build_active_filter(True))

        return self.query(filters=combine_filters(filters))

    def search_accounts(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search accounts by name or other fields.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to accountName)

        Returns:
            List of matching accounts
        """
        if search_fields is None:
            search_fields = ["accountName"]

        # Note: For OR logic with multiple fields, we need to make separate queries
        # and combine results, as Autotask API treats list filters as AND logic
        all_results = []
        for field in search_fields:
            search_filters = build_search_filters(search_term, [field])
            results = self.query(filters=search_filters)
            if hasattr(results, "items"):
                all_results.extend(results.items)
            else:
                all_results.extend(results)

        # Remove duplicates based on ID
        seen_ids = set()
        unique_results = []
        for account in all_results:
            account_id = account.get("id")
            if account_id and account_id not in seen_ids:
                seen_ids.add(account_id)
                unique_results.append(account)

        return unique_results

    def get_account_hierarchy(
        self, parent_account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get account hierarchy starting from a parent account.

        Args:
            parent_account_id: ID of parent account (None for root level)

        Returns:
            List of accounts in hierarchy
        """
        if parent_account_id is None:
            
            filters = [build_null_filter("parentAccountID", is_null=True)]
        else:
            filters = [build_equality_filter("parentAccountID", parent_account_id)]

        return self.query(filters=combine_filters(filters))

    def update_account_status(self, account_id: int, is_active: bool) -> Dict[str, Any]:
        """
        Update account active status.

        Args:
            account_id: ID of the account
            is_active: Whether account should be active

        Returns:
            Update response
        """
        return self.update(account_id, {"isActive": is_active})

    def get_accounts_by_territory(
        self, territory_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get accounts by territory.

        Args:
            territory_id: ID of the territory
            active_only: Whether to only return active accounts

        Returns:
            List of accounts in the territory
        """
        filters = [build_equality_filter("territoryID", territory_id)]

        if active_only:
            filters.append(build_active_filter(True))

        return self.query(filters=combine_filters(filters))

    def get_accounts_by_owner(
        self, owner_resource_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get accounts by owner resource.

        Args:
            owner_resource_id: ID of the owner resource
            active_only: Whether to only return active accounts

        Returns:
            List of accounts owned by the resource
        """
        filters = [build_equality_filter("ownerResourceID", owner_resource_id)]

        if active_only:
            filters.append(build_active_filter(True))

        return self.query(filters=combine_filters(filters))

    def get_account_summary(self, account_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary for an account.

        Args:
            account_id: ID of the account

        Returns:
            Account summary with related data
        """
        account = self.get(account_id)

        # This would typically query related entities
        # For now, return the account with placeholder related data

        return {
            "account": account,
            "summary": {
                "account_id": account_id,
                "related_contacts": 0,  # Would query contacts
                "active_projects": 0,  # Would query projects
                "open_tickets": 0,  # Would query tickets
                "active_contracts": 0,  # Would query contracts
                "total_revenue": Decimal("0"),  # Would calculate from invoices
            },
        }

    def convert_lead_to_customer(
        self, account_id: int, customer_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a lead account to a customer account.

        Args:
            account_id: ID of the lead account
            customer_type: Optional specific customer type

        Returns:
            Update response
        """
        update_data = {"accountType": "Customer"}

        if customer_type:
            update_data["customerType"] = customer_type

        return self.update(account_id, update_data)

    def bulk_update_territories(
        self, account_territory_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update territories for multiple accounts.

        Args:
            account_territory_updates: List of updates
                Each should contain: account_id, territory_id

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in account_territory_updates:
            account_id = update["account_id"]
            territory_id = update["territory_id"]

            try:
                result = self.update(account_id, {"territoryID": territory_id})
                results.append({"id": account_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": account_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(account_territory_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_accounts_by_location(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get accounts by location criteria.

        Args:
            city: Filter by city
            state: Filter by state
            country: Filter by country
            postal_code: Filter by postal code

        Returns:
            List of accounts matching location criteria
        """
        filters = []

        if city:
            filters.append(build_equality_filter("city", city))
        if state:
            filters.append(build_equality_filter("state", state))
        if country:
            filters.append(build_equality_filter("country", country))
        if postal_code:
            filters.append(build_equality_filter("postalCode", postal_code))

        if not filters:
            return []

        return self.query(filters=combine_filters(filters))

    def get_account_activity_summary(
        self,
        account_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get activity summary for an account.

        Args:
            account_id: ID of the account
            date_from: Start date for activity summary
            date_to: End date for activity summary

        Returns:
            Account activity summary
        """
        # This would typically query related activities from various entities
        # For now, return structure that could be populated

        return {
            "account_id": account_id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "activity_summary": {
                "ticket_count": 0,  # Would query tickets
                "project_count": 0,  # Would query projects
                "invoice_count": 0,  # Would query invoices
                "time_entries": 0,  # Would query time entries
                "last_activity_date": None,
            },
        }
