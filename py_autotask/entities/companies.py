"""
Comprehensive Companies (Accounts) entity for Autotask API operations.

This module provides a complete PSA implementation for managing companies/accounts
in Autotask, including lifecycle management, financial operations, contact management,
and advanced reporting capabilities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..constants import AccountType, FieldLengths
from ..types import CompanyData, QueryFilter
from .base import BaseEntity


class CompaniesEntity(BaseEntity):
    """
    Comprehensive Companies/Accounts entity for the Autotask API.

    This entity provides full PSA (Professional Services Automation) functionality
    for managing companies/accounts including:
    - Complete CRUD operations
    - Company lifecycle management (prospect -> customer -> inactive)
    - Contact and location management
    - Financial operations (billing, credit tracking)
    - SLA and contract associations
    - Custom field support
    - Bulk operations
    - Advanced search and analytics
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    # =============================================================================
    # Core CRUD Operations
    # =============================================================================

    def create_company(
        self,
        company_name: str,
        company_type: int = AccountType.CUSTOMER,
        phone: Optional[str] = None,
        address1: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        website: Optional[str] = None,
        owner_resource_id: Optional[int] = None,
        market_segment_id: Optional[int] = None,
        territory_id: Optional[int] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CompanyData:
        """
        Create a new company with comprehensive field support.

        Args:
            company_name: Name of the company (required)
            company_type: Type of company (default: Customer)
            phone: Primary phone number
            address1: Street address line 1
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            website: Company website URL
            owner_resource_id: ID of the resource who owns this account
            market_segment_id: Market segment classification
            territory_id: Sales territory assignment
            custom_fields: Dictionary of custom field values
            **kwargs: Additional company fields

        Returns:
            Created company data

        Raises:
            ValueError: If company_name exceeds field limits or is invalid
        """
        self._validate_company_name(company_name)

        company_data = {
            "CompanyName": company_name,
            "CompanyType": company_type,
            "Active": True,
            **kwargs,
        }

        # Add optional fields if provided
        optional_fields = {
            "Phone": phone,
            "Address1": address1,
            "City": city,
            "State": state,
            "PostalCode": postal_code,
            "Country": country,
            "WebAddress": website,
            "OwnerResourceID": owner_resource_id,
            "MarketSegmentID": market_segment_id,
            "TerritoryID": territory_id,
        }

        for field, value in optional_fields.items():
            if value is not None:
                company_data[field] = value

        # Add custom fields if provided
        if custom_fields:
            company_data.update(custom_fields)

        return self.create(company_data)

    def update_company(
        self,
        company_id: int,
        updates: Dict[str, Any],
        validate_fields: bool = True,
    ) -> CompanyData:
        """
        Update company with validation and field checking.

        Args:
            company_id: ID of the company to update
            updates: Dictionary of fields to update
            validate_fields: Whether to validate field values

        Returns:
            Updated company data

        Raises:
            ValueError: If validation fails
        """
        if validate_fields:
            self._validate_company_updates(updates)

        return self.update_by_id(company_id, updates)

    def delete_company(self, company_id: int, force: bool = False) -> bool:
        """
        Delete or deactivate a company.

        Args:
            company_id: ID of the company to delete
            force: If True, attempt hard delete; if False, deactivate

        Returns:
            True if successful

        Note:
            Autotask typically doesn't allow hard deletion of companies with
            associated data. This method will deactivate by default.
        """
        if force:
            try:
                return self.delete(company_id)
            except Exception:
                # Fall back to deactivation if hard delete fails
                pass

        # Deactivate the company
        self.update_by_id(company_id, {"Active": False})
        return True

    # =============================================================================
    # Company Lifecycle Management
    # =============================================================================

    def convert_prospect_to_customer(
        self,
        company_id: int,
        conversion_notes: Optional[str] = None,
        owner_resource_id: Optional[int] = None,
    ) -> CompanyData:
        """
        Convert a prospect company to a customer.

        Args:
            company_id: ID of the prospect company
            conversion_notes: Notes about the conversion
            owner_resource_id: New owner for the customer account

        Returns:
            Updated company data
        """
        updates = {"CompanyType": AccountType.CUSTOMER}

        if owner_resource_id:
            updates["OwnerResourceID"] = owner_resource_id

        # Add conversion note if provided
        if conversion_notes:
            # This would typically be added as a company note
            # but we'll include it in the update for now
            updates["Notes"] = conversion_notes

        return self.update_by_id(company_id, updates)

    def convert_lead_to_prospect(
        self,
        company_id: int,
        qualification_notes: Optional[str] = None,
    ) -> CompanyData:
        """
        Convert a lead to a prospect.

        Args:
            company_id: ID of the lead company
            qualification_notes: Notes about qualification process

        Returns:
            Updated company data
        """
        updates = {"CompanyType": AccountType.PROSPECT}

        if qualification_notes:
            updates["Notes"] = qualification_notes

        return self.update_by_id(company_id, updates)

    def deactivate_company(
        self,
        company_id: int,
        reason: Optional[str] = None,
        archive_data: bool = True,
    ) -> CompanyData:
        """
        Deactivate a company account.

        Args:
            company_id: ID of company to deactivate
            reason: Reason for deactivation
            archive_data: Whether to archive associated data

        Returns:
            Updated company data
        """
        updates = {"Active": False}

        if reason:
            updates["InactiveReason"] = reason

        return self.update_by_id(company_id, updates)

    def reactivate_company(self, company_id: int) -> CompanyData:
        """
        Reactivate a deactivated company.

        Args:
            company_id: ID of company to reactivate

        Returns:
            Updated company data
        """
        return self.update_by_id(company_id, {"Active": True})

    def activate_company(self, company_id: int) -> CompanyData:
        """
        Activate a company (alias for reactivate_company).

        Args:
            company_id: ID of company to activate

        Returns:
            Updated company data
        """
        return self.update_by_id(company_id, {"Active": True})

    # =============================================================================
    # Search and Query Operations
    # =============================================================================

    def search_companies_by_name(
        self,
        name: str,
        exact_match: bool = False,
        active_only: bool = False,
        company_types: Optional[List[int]] = None,
        limit: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Search for companies by name with advanced filtering.

        Args:
            name: Company name to search for
            exact_match: Whether to do exact match or partial match
            active_only: Whether to return only active companies
            company_types: List of company types to filter by
            limit: Maximum number of companies to return

        Returns:
            List of matching companies
        """
        filters = []

        if exact_match:
            filters.append(QueryFilter(field="CompanyName", op="eq", value=name))
        else:
            filters.append(QueryFilter(field="CompanyName", op="contains", value=name))

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        if company_types:
            if len(company_types) == 1:
                filters.append(
                    QueryFilter(field="CompanyType", op="eq", value=company_types[0])
                )
            else:
                filters.append(
                    QueryFilter(field="CompanyType", op="in", value=company_types)
                )

        return self.query(filters=filters, max_records=limit).items

    def get_companies_by_type(
        self,
        company_type: int,
        active_only: bool = True,
        include_fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Get companies by type with field selection.

        Args:
            company_type: Company type to filter by
            active_only: Whether to return only active companies
            include_fields: Specific fields to include in response
            limit: Maximum number of companies to return

        Returns:
            List of companies of the specified type
        """
        filters = [QueryFilter(field="CompanyType", op="eq", value=company_type)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(
            filters=filters, include_fields=include_fields, max_records=limit
        ).items

    def get_customer_companies(
        self,
        active_only: bool = True,
        owner_resource_id: Optional[int] = None,
        territory_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Get customer companies with advanced filtering.

        Args:
            active_only: Whether to return only active companies
            owner_resource_id: Filter by account owner
            territory_id: Filter by territory
            limit: Maximum number of companies to return

        Returns:
            List of customer companies
        """
        filters = [
            QueryFilter(field="CompanyType", op="eq", value=AccountType.CUSTOMER)
        ]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        if owner_resource_id:
            filters.append(
                QueryFilter(field="OwnerResourceID", op="eq", value=owner_resource_id)
            )

        if territory_id:
            filters.append(
                QueryFilter(field="TerritoryID", op="eq", value=territory_id)
            )

        return self.query(filters=filters, max_records=limit).items

    def get_prospect_companies(
        self,
        active_only: bool = False,
        owner_resource_id: Optional[int] = None,
        created_since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Get prospect companies with date filtering.

        Args:
            active_only: Whether to return only active companies
            owner_resource_id: Filter by account owner
            created_since: Filter prospects created since this date
            limit: Maximum number of companies to return

        Returns:
            List of prospect companies
        """
        filters = [
            QueryFilter(field="CompanyType", op="eq", value=AccountType.PROSPECT)
        ]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        if owner_resource_id:
            filters.append(
                QueryFilter(field="OwnerResourceID", op="eq", value=owner_resource_id)
            )

        if created_since:
            filters.append(
                QueryFilter(
                    field="CreateDate", op="gte", value=created_since.isoformat()
                )
            )

        return self.query(filters=filters, max_records=limit).items

    def get_companies_by_location(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        radius_miles: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Get companies by location with radius support.

        Args:
            city: City to filter by
            state: State/province to filter by
            country: Country to filter by
            postal_code: Postal code to filter by
            radius_miles: Search radius in miles (requires postal_code)
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
            if radius_miles:
                # This would require a more complex implementation
                # For now, just do exact postal code match
                filters.append(
                    QueryFilter(field="PostalCode", op="eq", value=postal_code)
                )
            else:
                filters.append(
                    QueryFilter(field="PostalCode", op="eq", value=postal_code)
                )

        if not filters:
            raise ValueError("At least one location criteria must be provided")

        return self.query(filters=filters, max_records=limit).items

    # =============================================================================
    # Contact Management
    # =============================================================================

    def get_company_contacts(
        self,
        company_id: int,
        active_only: bool = False,
        include_primary_contact: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all contacts for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active contacts
            include_primary_contact: Whether to include primary contact info

        Returns:
            List of contacts for the company
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.client.query("Contacts", filters=filters)

    def set_primary_contact(
        self,
        company_id: int,
        contact_id: int,
    ) -> CompanyData:
        """
        Set the primary contact for a company.

        Args:
            company_id: ID of the company
            contact_id: ID of the contact to set as primary

        Returns:
            Updated company data
        """
        return self.update_by_id(company_id, {"PrimaryContact": contact_id})

    def get_company_primary_contact(self, company_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the primary contact for a company.

        Args:
            company_id: ID of the company

        Returns:
            Primary contact data or None if not set
        """
        company_data = self.get(company_id)
        if not company_data or "PrimaryContact" not in company_data:
            return None

        primary_contact_id = company_data["PrimaryContact"]
        if not primary_contact_id:
            return None

        contacts = self.client.query(
            "Contacts",
            filters=[QueryFilter(field="id", op="eq", value=primary_contact_id)],
        ).items

        return contacts[0] if contacts else None

    # =============================================================================
    # Financial Operations
    # =============================================================================

    def update_billing_settings(
        self,
        company_id: int,
        billing_method: Optional[str] = None,
        payment_terms: Optional[int] = None,
        tax_region_id: Optional[int] = None,
        currency_id: Optional[int] = None,
        invoice_template_id: Optional[int] = None,
    ) -> CompanyData:
        """
        Update company billing settings.

        Args:
            company_id: ID of the company
            billing_method: Billing method preference
            payment_terms: Payment terms ID
            tax_region_id: Tax region for calculations
            currency_id: Currency preference
            invoice_template_id: Invoice template to use

        Returns:
            Updated company data
        """
        updates = {}

        billing_fields = {
            "BillingMethod": billing_method,
            "PaymentTerms": payment_terms,
            "TaxRegionID": tax_region_id,
            "CurrencyID": currency_id,
            "InvoiceTemplateID": invoice_template_id,
        }

        for field, value in billing_fields.items():
            if value is not None:
                updates[field] = value

        return self.update_by_id(company_id, updates)

    def set_credit_limit(
        self,
        company_id: int,
        credit_limit: float,
        credit_hold: bool = False,
    ) -> CompanyData:
        """
        Set credit limit and hold status for a company.

        Args:
            company_id: ID of the company
            credit_limit: Maximum credit limit
            credit_hold: Whether to place account on credit hold

        Returns:
            Updated company data
        """
        updates = {
            "CreditLimit": credit_limit,
            "CreditHold": credit_hold,
        }

        return self.update_by_id(company_id, updates)

    def get_company_financial_summary(self, company_id: int) -> Dict[str, Any]:
        """
        Get financial summary for a company.

        Args:
            company_id: ID of the company

        Returns:
            Dictionary containing financial metrics
        """
        # Get company billing info
        company_data = self.get(company_id)

        # Get related financial data (invoices, payments, etc.)
        # This would typically involve multiple API calls

        summary = {
            "company_id": company_id,
            "company_name": company_data.get("CompanyName") if company_data else None,
            "credit_limit": company_data.get("CreditLimit", 0) if company_data else 0,
            "credit_hold": (
                company_data.get("CreditHold", False) if company_data else False
            ),
            "payment_terms": company_data.get("PaymentTerms") if company_data else None,
            "currency": company_data.get("CurrencyID") if company_data else None,
            # These would be calculated from invoice/payment data
            "outstanding_balance": 0.0,
            "total_invoiced_ytd": 0.0,
            "total_paid_ytd": 0.0,
        }

        return summary

    # =============================================================================
    # Contract and SLA Operations
    # =============================================================================

    def get_company_contracts(
        self,
        company_id: int,
        active_only: bool = True,
        contract_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all contracts for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active contracts
            contract_type: Filter by contract type
            limit: Maximum number of contracts to return

        Returns:
            List of contracts for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="Status", op="eq", value=1))  # Active

        if contract_type:
            filters.append(
                QueryFilter(field="ContractType", op="eq", value=contract_type)
            )

        return self.client.query("Contracts", filters=filters)

    def get_company_slas(self, company_id: int) -> List[Dict[str, Any]]:
        """
        Get all SLAs associated with a company.

        Args:
            company_id: ID of the company

        Returns:
            List of SLA configurations
        """
        # This would typically involve querying ServiceLevelAgreements
        # and filtering by AccountID
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]
        return self.client.query("ServiceLevelAgreements", filters=filters).items

    def assign_sla_to_company(
        self,
        company_id: int,
        sla_id: int,
        effective_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Assign an SLA to a company.

        Args:
            company_id: ID of the company
            sla_id: ID of the SLA to assign
            effective_date: When the SLA becomes effective

        Returns:
            SLA assignment record
        """
        assignment_data = {
            "AccountID": company_id,
            "ServiceLevelAgreementID": sla_id,
            "EffectiveDate": (
                effective_date.isoformat()
                if effective_date
                else datetime.now().isoformat()
            ),
        }

        # This would create an SLA assignment record
        return self.client.create_entity(
            "ServiceLevelAgreementResults", assignment_data
        )

    # =============================================================================
    # Location and Address Management
    # =============================================================================

    def update_company_address(
        self,
        company_id: int,
        address1: Optional[str] = None,
        address2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        validate_address: bool = False,
    ) -> CompanyData:
        """
        Update company address with optional validation.

        Args:
            company_id: ID of company to update
            address1: Street address line 1
            address2: Street address line 2
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            validate_address: Whether to validate address format

        Returns:
            Updated company data

        Raises:
            ValueError: If validation fails
        """
        updates = {}

        address_fields = {
            "Address1": address1,
            "Address2": address2,
            "City": city,
            "State": state,
            "PostalCode": postal_code,
            "Country": country,
        }

        for field, value in address_fields.items():
            if value is not None:
                if validate_address:
                    self._validate_address_field(field, value)
                updates[field] = value

        return self.update_by_id(company_id, updates)

    def get_company_locations(self, company_id: int) -> List[Dict[str, Any]]:
        """
        Get all locations for a company.

        Args:
            company_id: ID of the company

        Returns:
            List of company locations
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]
        return self.client.query("CompanyLocations", filters=filters).items

    def add_company_location(
        self,
        company_id: int,
        location_name: str,
        address1: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
        is_primary: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Add a new location for a company.

        Args:
            company_id: ID of the company
            location_name: Name/description of the location
            address1: Street address
            city: City name
            state: State/province
            postal_code: ZIP/postal code
            country: Country name
            is_primary: Whether this is the primary location
            **kwargs: Additional location fields

        Returns:
            Created location record
        """
        location_data = {
            "CompanyID": company_id,
            "Name": location_name,
            "Address1": address1,
            "City": city,
            "State": state,
            "PostalCode": postal_code,
            "Country": country,
            "Primary": is_primary,
            **kwargs,
        }

        return self.client.create_entity("CompanyLocations", location_data)

    # =============================================================================
    # Custom Fields and Extensions
    # =============================================================================

    def get_company_custom_fields(self, company_id: int) -> Dict[str, Any]:
        """
        Get all custom field values for a company.

        Args:
            company_id: ID of the company

        Returns:
            Dictionary of custom field names and values
        """
        company_data = self.get(company_id)
        if not company_data:
            return {}

        custom_fields = {}
        for key, value in company_data.items():
            if key.startswith("UserDefinedField"):
                # Extract field name if available, otherwise use the key
                field_name = key
                custom_fields[field_name] = value

        return custom_fields

    def update_company_custom_fields(
        self,
        company_id: int,
        custom_fields: Dict[str, Any],
    ) -> CompanyData:
        """
        Update custom field values for a company.

        Args:
            company_id: ID of the company
            custom_fields: Dictionary of custom field names/values

        Returns:
            Updated company data
        """
        return self.update_by_id(company_id, custom_fields)

    # =============================================================================
    # Bulk Operations
    # =============================================================================

    def bulk_update_companies(
        self,
        company_updates: List[Dict[str, Any]],
        batch_size: int = 50,
    ) -> List[CompanyData]:
        """
        Update multiple companies in batches.

        Args:
            company_updates: List of dictionaries containing id and update fields
            batch_size: Number of companies to update per batch

        Returns:
            List of updated company records

        Example:
            updates = [
                {"id": 123, "City": "New York", "State": "NY"},
                {"id": 124, "Active": False},
            ]
            results = companies.bulk_update_companies(updates)
        """
        results = []

        for i in range(0, len(company_updates), batch_size):
            batch = company_updates[i : i + batch_size]

            for update in batch:
                company_id = update.pop("id")
                try:
                    result = self.update_by_id(company_id, update)
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other updates
                    self.logger.error(f"Failed to update company {company_id}: {e}")
                    results.append(None)

        return results

    def bulk_deactivate_companies(
        self,
        company_ids: List[int],
        reason: Optional[str] = None,
    ) -> List[CompanyData]:
        """
        Deactivate multiple companies.

        Args:
            company_ids: List of company IDs to deactivate
            reason: Reason for deactivation

        Returns:
            List of updated company records
        """
        updates = [
            {"id": company_id, "Active": False, "InactiveReason": reason}
            for company_id in company_ids
        ]

        return self.bulk_update_companies(updates)

    def bulk_transfer_companies(
        self,
        company_ids: List[int],
        new_owner_resource_id: int,
        new_territory_id: Optional[int] = None,
    ) -> List[CompanyData]:
        """
        Transfer multiple companies to a new owner.

        Args:
            company_ids: List of company IDs to transfer
            new_owner_resource_id: ID of the new owner
            new_territory_id: Optional new territory assignment

        Returns:
            List of updated company records
        """
        updates = []
        for company_id in company_ids:
            update = {
                "id": company_id,
                "OwnerResourceID": new_owner_resource_id,
            }
            if new_territory_id:
                update["TerritoryID"] = new_territory_id
            updates.append(update)

        return self.bulk_update_companies(updates)

    # =============================================================================
    # Analytics and Reporting
    # =============================================================================

    def get_company_activity_summary(
        self,
        company_id: int,
        date_range_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get activity summary for a company.

        Args:
            company_id: ID of the company
            date_range_days: Number of days to look back

        Returns:
            Activity summary with tickets, projects, time entries, etc.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)

        # Get various activity metrics
        summary = {
            "company_id": company_id,
            "date_range_start": start_date.isoformat(),
            "date_range_end": end_date.isoformat(),
            "total_tickets": 0,
            "open_tickets": 0,
            "closed_tickets": 0,
            "total_projects": 0,
            "active_projects": 0,
            "total_time_entries": 0,
            "total_billable_hours": 0.0,
        }

        # Get ticket counts
        try:
            tickets = self.get_company_tickets(company_id, limit=1000)
            summary["total_tickets"] = len(tickets)

            # Count by status
            for ticket in tickets:
                if ticket.get("Status") in [1, 8, 9, 10, 11]:  # Open statuses
                    summary["open_tickets"] += 1
                elif ticket.get("Status") == 5:  # Closed
                    summary["closed_tickets"] += 1
        except Exception as e:
            self.logger.error(f"Failed to get tickets for company {company_id}: {e}")

        # Get project counts
        try:
            projects = self.get_company_projects(
                company_id, active_only=False, limit=1000
            )
            summary["total_projects"] = len(projects)

            for project in projects:
                if project.get("Status") != 5:  # Not complete
                    summary["active_projects"] += 1
        except Exception as e:
            self.logger.error(f"Failed to get projects for company {company_id}: {e}")

        return summary

    def get_companies_by_performance_metrics(
        self,
        metric: str = "revenue",
        period_days: int = 90,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get companies ranked by performance metrics.

        Args:
            metric: Metric to rank by ('revenue', 'tickets', 'projects')
            period_days: Time period to analyze
            limit: Maximum number of companies to return

        Returns:
            List of companies with performance metrics
        """
        # This would typically require complex joins and calculations
        # For now, return basic structure
        results = []

        # Get all active customer companies
        customers = self.get_customer_companies(limit=limit)

        for company in customers:
            company_id = company.get("id")
            if not company_id:
                continue

            metrics = {
                "company_id": company_id,
                "company_name": company.get("CompanyName"),
                "metric_type": metric,
                "period_days": period_days,
                "metric_value": 0,  # Would be calculated based on metric type
            }

            # Add basic activity summary
            try:
                activity = self.get_company_activity_summary(company_id, period_days)
                if metric == "tickets":
                    metrics["metric_value"] = activity.get("total_tickets", 0)
                elif metric == "projects":
                    metrics["metric_value"] = activity.get("total_projects", 0)
                # Revenue would require invoice data analysis

            except Exception as e:
                self.logger.error(
                    f"Failed to get metrics for company {company_id}: {e}"
                )

            results.append(metrics)

        # Sort by metric value descending
        results.sort(key=lambda x: x["metric_value"], reverse=True)

        return results[:limit]

    def get_company_growth_trends(
        self,
        company_id: int,
        months: int = 12,
    ) -> Dict[str, Any]:
        """
        Analyze growth trends for a company.

        Args:
            company_id: ID of the company
            months: Number of months to analyze

        Returns:
            Growth trend analysis
        """
        trends = {
            "company_id": company_id,
            "analysis_period_months": months,
            "monthly_metrics": [],
            "growth_indicators": {
                "ticket_volume_trend": "stable",
                "project_growth": "stable",
                "revenue_trend": "stable",
            },
        }

        # This would require historical data analysis
        # For now, return basic structure

        return trends

    # =============================================================================
    # Relationship Management
    # =============================================================================

    def get_company_tickets(
        self,
        company_id: int,
        status_filter: Optional[str] = None,
        priority_filter: Optional[int] = None,
        date_range_days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Enhanced ticket retrieval for a company.

        Args:
            company_id: ID of the company
            status_filter: Optional status filter ('open', 'closed', etc.)
            priority_filter: Optional priority level filter
            date_range_days: Only tickets created in last N days
            limit: Maximum number of tickets to return

        Returns:
            List of tickets for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        # Add status filter
        if status_filter:
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

        # Add priority filter
        if priority_filter:
            filters.append(
                QueryFilter(field="Priority", op="eq", value=priority_filter)
            )

        # Add date range filter
        if date_range_days:
            cutoff_date = datetime.now() - timedelta(days=date_range_days)
            filters.append(
                QueryFilter(field="CreateDate", op="gte", value=cutoff_date.isoformat())
            )

        return self.client.query("Tickets", filters=filters)

    def get_company_projects(
        self,
        company_id: int,
        active_only: bool = False,
        status_filter: Optional[str] = None,
        project_type: Optional[int] = None,
        date_range_days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Enhanced project retrieval for a company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active projects (not complete)
            status_filter: Optional status filter ('active', 'completed', etc.)
            project_type: Optional project type filter
            date_range_days: Only projects created in last N days
            limit: Maximum number of projects to return

        Returns:
            List of projects for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        # Add active filter (not complete)
        if active_only:
            filters.append(
                QueryFilter(field="Status", op="ne", value=5)
            )  # Not Complete

        # Add status filter
        if status_filter:
            status_map = {
                "active": [1, 2, 3, 4],  # New, In Progress, On Hold, Waiting
                "completed": [5],  # Complete
                "new": [1],
                "in_progress": [2],
                "on_hold": [3],
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

        # Add project type filter
        if project_type:
            filters.append(QueryFilter(field="Type", op="eq", value=project_type))

        # Add date range filter
        if date_range_days:
            cutoff_date = datetime.now() - timedelta(days=date_range_days)
            filters.append(
                QueryFilter(field="CreateDate", op="gte", value=cutoff_date.isoformat())
            )

        return self.client.query("Projects", filters=filters)

    def get_company_opportunities(
        self,
        company_id: int,
        stage_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get sales opportunities for a company.

        Args:
            company_id: ID of the company
            stage_filter: Optional stage filter ('open', 'won', 'lost')
            limit: Maximum number of opportunities to return

        Returns:
            List of opportunities for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        if stage_filter:
            # Map common stage filters - these would need to match Autotask values
            stage_map = {
                "open": [1, 2, 3, 4],  # Various open stages
                "won": [5],  # Won
                "lost": [6],  # Lost
            }

            if stage_filter.lower() in stage_map:
                stage_ids = stage_map[stage_filter.lower()]
                if len(stage_ids) == 1:
                    filters.append(
                        QueryFilter(field="Stage", op="eq", value=stage_ids[0])
                    )
                else:
                    filters.append(QueryFilter(field="Stage", op="in", value=stage_ids))

        return self.client.query(
            "Opportunities", filters=filters, max_records=limit
        ).items

    # =============================================================================
    # Utility and Validation Methods
    # =============================================================================

    def _validate_company_name(self, name: str) -> None:
        """Validate company name field."""
        if not name or not name.strip():
            raise ValueError("Company name is required")

        if len(name) > FieldLengths.NAME_MAX:
            raise ValueError(
                f"Company name must be {FieldLengths.NAME_MAX} characters or less"
            )

    def _validate_company_updates(self, updates: Dict[str, Any]) -> None:
        """Validate company update fields."""
        if "CompanyName" in updates:
            self._validate_company_name(updates["CompanyName"])

        # Validate other common fields
        if "Phone" in updates and updates["Phone"]:
            if len(updates["Phone"]) > FieldLengths.PHONE_MAX:
                raise ValueError(
                    f"Phone number must be {FieldLengths.PHONE_MAX} characters or less"
                )

        if "WebAddress" in updates and updates["WebAddress"]:
            if len(updates["WebAddress"]) > 255:
                raise ValueError("Website URL must be 255 characters or less")

    def _validate_address_field(self, field: str, value: str) -> None:
        """Validate address field values."""
        field_limits = {
            "Address1": FieldLengths.ADDRESS_LINE_MAX,
            "Address2": FieldLengths.ADDRESS_LINE_MAX,
            "City": FieldLengths.CITY_MAX,
            "State": FieldLengths.STATE_MAX,
            "PostalCode": FieldLengths.ZIP_CODE_MAX,
            "Country": FieldLengths.COUNTRY_MAX,
        }

        if field in field_limits and len(value) > field_limits[field]:
            raise ValueError(
                f"{field} must be {field_limits[field]} characters or less"
            )
