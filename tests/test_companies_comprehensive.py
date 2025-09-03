"""
Comprehensive tests for the enhanced CompaniesEntity class.

This test suite covers all aspects of the companies entity including:
- Core CRUD operations
- Company lifecycle management
- Contact management
- Financial operations
- SLA and contract associations
- Location and address management
- Custom field support
- Bulk operations
- Advanced search and filtering
- Analytics and reporting helpers
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from py_autotask.constants import AccountType, AccountStatus, FieldLengths
from py_autotask.entities.companies import CompaniesEntity
from py_autotask.exceptions import AutotaskValidationError
from py_autotask.types import QueryFilter


class TestCompaniesEntityComprehensive:
    """Comprehensive test cases for CompaniesEntity."""

    @pytest.fixture
    def mock_client(self):
        """Mock AutotaskClient for testing."""
        return Mock()

    @pytest.fixture
    def companies_entity(self, mock_client):
        """CompaniesEntity instance for testing."""
        return CompaniesEntity(mock_client, "Companies")

    @pytest.fixture
    def sample_company_data(self):
        """Sample company data for testing."""
        return {
            "id": 12345,
            "CompanyName": "Acme Corporation",
            "CompanyType": AccountType.CUSTOMER,
            "Active": True,
            "Phone": "555-123-4567",
            "Address1": "123 Business Ave",
            "City": "New York",
            "State": "NY",
            "PostalCode": "10001",
            "Country": "USA",
            "WebAddress": "https://acme-corp.com",
            "OwnerResourceID": 100,
            "TerritoryID": 5,
            "CreateDate": "2023-01-01T00:00:00Z",
            "LastModifiedDate": "2023-01-01T00:00:00Z",
        }

    @pytest.fixture
    def sample_contact_data(self):
        """Sample contact data for testing."""
        return {
            "id": 67890,
            "CompanyID": 12345,
            "FirstName": "John",
            "LastName": "Doe",
            "EmailAddress": "john.doe@acme-corp.com",
            "Active": True,
        }

    # =============================================================================
    # Core CRUD Operations Tests
    # =============================================================================

    def test_create_company_basic(self, companies_entity, mock_client):
        """Test basic company creation with required fields."""
        mock_client.create_entity.return_value = Mock(item_id=12345)
        
        result = companies_entity.create_company("Acme Corporation")
        
        mock_client.create_entity.assert_called_once()
        call_args = mock_client.create_entity.call_args[0]
        assert call_args[0] == "Companies"
        company_data = call_args[1]
        assert company_data["CompanyName"] == "Acme Corporation"
        assert company_data["CompanyType"] == AccountType.CUSTOMER
        assert company_data["Active"] is True

    def test_create_company_comprehensive(self, companies_entity, mock_client):
        """Test company creation with all optional fields."""
        mock_client.create_entity.return_value = Mock(item_id=12345)
        custom_fields = {"UserDefinedField1": "Custom Value"}
        
        result = companies_entity.create_company(
            company_name="Acme Corporation",
            company_type=AccountType.PROSPECT,
            phone="555-123-4567",
            address1="123 Business Ave",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA",
            website="https://acme-corp.com",
            owner_resource_id=100,
            market_segment_id=1,
            territory_id=5,
            custom_fields=custom_fields,
        )
        
        mock_client.create_entity.assert_called_once()
        company_data = mock_client.create_entity.call_args[0][1]
        assert company_data["CompanyName"] == "Acme Corporation"
        assert company_data["CompanyType"] == AccountType.PROSPECT
        assert company_data["Phone"] == "555-123-4567"
        assert company_data["Address1"] == "123 Business Ave"
        assert company_data["WebAddress"] == "https://acme-corp.com"
        assert company_data["OwnerResourceID"] == 100
        assert company_data["UserDefinedField1"] == "Custom Value"

    def test_create_company_validation_error(self, companies_entity):
        """Test company creation with invalid name raises validation error."""
        with pytest.raises(ValueError, match="Company name is required"):
            companies_entity.create_company("")

        long_name = "x" * (FieldLengths.NAME_MAX + 1)
        with pytest.raises(ValueError, match="Company name must be"):
            companies_entity.create_company(long_name)

    def test_update_company_basic(self, companies_entity, mock_client):
        """Test basic company update."""
        mock_client.update.return_value = Mock()
        updates = {"Phone": "555-999-8888", "City": "Los Angeles"}
        
        companies_entity.update_company(12345, updates)
        
        expected_data = {"id": 12345, **updates}
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_update_company_with_validation(self, companies_entity, mock_client):
        """Test company update with field validation."""
        mock_client.update.return_value = Mock()
        
        # Valid update should work
        updates = {"CompanyName": "Valid Name", "Phone": "555-123-4567"}
        companies_entity.update_company(12345, updates, validate_fields=True)
        mock_client.update.assert_called_once()

        # Invalid update should raise error
        long_phone = "x" * (FieldLengths.PHONE_MAX + 1)
        invalid_updates = {"Phone": long_phone}
        with pytest.raises(ValueError, match="Phone number must be"):
            companies_entity.update_company(12345, invalid_updates, validate_fields=True)

    def test_delete_company_soft_delete(self, companies_entity, mock_client):
        """Test company soft delete (deactivation)."""
        mock_client.update.return_value = Mock()
        
        result = companies_entity.delete_company(12345, force=False)
        
        assert result is True
        expected_data = {"id": 12345, "Active": False}
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_delete_company_hard_delete_fallback(self, companies_entity, mock_client):
        """Test company hard delete with fallback to soft delete."""
        mock_client.delete.side_effect = Exception("Cannot delete")
        mock_client.update.return_value = Mock()
        
        result = companies_entity.delete_company(12345, force=True)
        
        assert result is True
        mock_client.delete.assert_called_once_with("Companies", 12345)
        expected_data = {"id": 12345, "Active": False}
        mock_client.update.assert_called_once_with("Companies", expected_data)

    # =============================================================================
    # Company Lifecycle Management Tests
    # =============================================================================

    def test_convert_prospect_to_customer(self, companies_entity, mock_client):
        """Test converting prospect to customer."""
        mock_client.update.return_value = Mock()
        
        companies_entity.convert_prospect_to_customer(
            12345, 
            conversion_notes="Signed contract",
            owner_resource_id=200
        )
        
        expected_data = {
            "id": 12345,
            "CompanyType": AccountType.CUSTOMER,
            "OwnerResourceID": 200,
            "Notes": "Signed contract",
        }
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_convert_lead_to_prospect(self, companies_entity, mock_client):
        """Test converting lead to prospect."""
        mock_client.update.return_value = Mock()
        
        companies_entity.convert_lead_to_prospect(
            12345,
            qualification_notes="Qualified through discovery call"
        )
        
        expected_data = {
            "id": 12345,
            "CompanyType": AccountType.PROSPECT,
            "Notes": "Qualified through discovery call",
        }
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_deactivate_company(self, companies_entity, mock_client):
        """Test deactivating a company."""
        mock_client.update.return_value = Mock()
        
        companies_entity.deactivate_company(
            12345,
            reason="Contract ended",
            archive_data=True
        )
        
        expected_data = {
            "id": 12345,
            "Active": False,
            "InactiveReason": "Contract ended",
        }
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_reactivate_company(self, companies_entity, mock_client):
        """Test reactivating a company."""
        mock_client.update.return_value = Mock()
        
        companies_entity.reactivate_company(12345)
        
        expected_data = {"id": 12345, "Active": True}
        mock_client.update.assert_called_once_with("Companies", expected_data)

    # =============================================================================
    # Search and Query Operations Tests
    # =============================================================================

    def test_search_companies_by_name_exact_match(self, companies_entity, mock_client):
        """Test searching companies by exact name match."""
        mock_response = Mock()
        mock_response.items = [{"id": 12345, "CompanyName": "Acme Corporation"}]
        companies_entity.query = Mock(return_value=mock_response)
        
        result = companies_entity.search_companies_by_name("Acme Corporation", exact_match=True)
        
        # The entity's query method should be called
        companies_entity.query.assert_called_once()
        assert len(result) == 1

    def test_search_companies_by_name_partial_match(self, companies_entity, mock_client):
        """Test searching companies by partial name match."""
        mock_response = Mock()
        mock_response.items = [{"id": 12345, "CompanyName": "Acme Corporation"}]
        companies_entity.query = Mock(return_value=mock_response)
        
        result = companies_entity.search_companies_by_name(
            "Acme",
            exact_match=False,
            active_only=False,
            company_types=[AccountType.CUSTOMER, AccountType.PROSPECT]
        )
        
        companies_entity.query.assert_called_once()
        assert len(result) == 1

    def test_get_companies_by_type(self, companies_entity, mock_client):
        """Test getting companies by type."""
        mock_response = Mock()
        mock_response.items = [{"id": 12345, "CompanyType": AccountType.CUSTOMER}]
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_companies_by_type(
            AccountType.CUSTOMER,
            include_fields=["id", "CompanyName", "CompanyType"]
        )
        
        mock_client.query.assert_called_once()
        assert len(result) == 1

    def test_get_customer_companies_with_filters(self, companies_entity, mock_client):
        """Test getting customer companies with advanced filters."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_customer_companies(
            owner_resource_id=100,
            territory_id=5,
            limit=50
        )
        
        mock_client.query.assert_called_once()
        assert len(result) == 0

    def test_get_prospect_companies_with_date_filter(self, companies_entity, mock_client):
        """Test getting prospect companies with date filtering."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response
        created_since = datetime(2023, 1, 1)
        
        result = companies_entity.get_prospect_companies(
            owner_resource_id=100,
            created_since=created_since
        )
        
        mock_client.query.assert_called_once()
        assert len(result) == 0

    def test_get_companies_by_location(self, companies_entity, mock_client):
        """Test getting companies by location."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_companies_by_location(
            city="New York",
            state="NY",
            country="USA"
        )
        
        mock_client.query.assert_called_once()
        assert len(result) == 0

    def test_get_companies_by_location_no_criteria_error(self, companies_entity):
        """Test error when no location criteria provided."""
        with pytest.raises(ValueError, match="At least one location criteria must be provided"):
            companies_entity.get_companies_by_location()

    # =============================================================================
    # Contact Management Tests
    # =============================================================================

    def test_get_company_contacts(self, companies_entity, mock_client):
        """Test getting contacts for a company."""
        mock_response = Mock()
        mock_response.items = [
            {"id": 67890, "CompanyID": 12345, "FirstName": "John", "LastName": "Doe"}
        ]
        mock_client.query.return_value = mock_response
        mock_client.get.return_value = {"PrimaryContact": 67890}
        
        result = companies_entity.get_company_contacts(12345, include_primary_contact=True)
        
        mock_client.query.assert_called_once()
        mock_client.get.assert_called_once_with("Companies", 12345)
        assert result[0]["IsPrimaryContact"] is True

    def test_set_primary_contact(self, companies_entity, mock_client):
        """Test setting primary contact for a company."""
        mock_client.update.return_value = Mock()
        
        companies_entity.set_primary_contact(12345, 67890)
        
        expected_data = {"id": 12345, "PrimaryContact": 67890}
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_get_company_primary_contact(self, companies_entity, mock_client):
        """Test getting primary contact for a company."""
        mock_client.get.return_value = {"PrimaryContact": 67890}
        mock_response = Mock()
        mock_response.items = [
            {"id": 67890, "FirstName": "John", "LastName": "Doe"}
        ]
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_company_primary_contact(12345)
        
        mock_client.get.assert_called_once_with("Companies", 12345)
        mock_client.query.assert_called_once()
        assert result["id"] == 67890

    def test_get_company_primary_contact_not_set(self, companies_entity, mock_client):
        """Test getting primary contact when none is set."""
        mock_client.get.return_value = {"PrimaryContact": None}
        
        result = companies_entity.get_company_primary_contact(12345)
        
        assert result is None

    # =============================================================================
    # Financial Operations Tests
    # =============================================================================

    def test_update_billing_settings(self, companies_entity, mock_client):
        """Test updating company billing settings."""
        mock_client.update.return_value = Mock()
        
        companies_entity.update_billing_settings(
            12345,
            billing_method="Monthly",
            payment_terms=1,
            tax_region_id=10,
            currency_id=1,
            invoice_template_id=5
        )
        
        expected_data = {
            "id": 12345,
            "BillingMethod": "Monthly",
            "PaymentTerms": 1,
            "TaxRegionID": 10,
            "CurrencyID": 1,
            "InvoiceTemplateID": 5,
        }
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_set_credit_limit(self, companies_entity, mock_client):
        """Test setting credit limit for a company."""
        mock_client.update.return_value = Mock()
        
        companies_entity.set_credit_limit(12345, 50000.0, credit_hold=True)
        
        expected_data = {
            "id": 12345,
            "CreditLimit": 50000.0,
            "CreditHold": True,
        }
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_get_company_financial_summary(self, companies_entity, mock_client, sample_company_data):
        """Test getting financial summary for a company."""
        mock_client.get.return_value = sample_company_data
        
        result = companies_entity.get_company_financial_summary(12345)
        
        assert result["company_id"] == 12345
        assert result["company_name"] == "Acme Corporation"
        assert "credit_limit" in result
        assert "outstanding_balance" in result
        assert "total_invoiced_ytd" in result

    # =============================================================================
    # Contract and SLA Operations Tests
    # =============================================================================

    def test_get_company_contracts(self, companies_entity, mock_client):
        """Test getting contracts for a company."""
        mock_response = Mock()
        mock_response.items = [
            {"id": 111, "AccountID": 12345, "Status": 1}
        ]
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_company_contracts(
            12345,
            contract_type="Service Agreement",
            limit=10
        )
        
        mock_client.query.assert_called_once()
        assert len(result) == 1

    def test_get_company_slas(self, companies_entity, mock_client):
        """Test getting SLAs for a company."""
        mock_response = Mock()
        mock_response.items = [
            {"id": 222, "AccountID": 12345}
        ]
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_company_slas(12345)
        
        mock_client.query.assert_called_once()
        assert len(result) == 1

    def test_assign_sla_to_company(self, companies_entity, mock_client):
        """Test assigning SLA to a company."""
        mock_client.create_entity.return_value = Mock(item_id=333)
        effective_date = datetime(2023, 1, 1)
        
        companies_entity.assign_sla_to_company(12345, 222, effective_date)
        
        mock_client.create_entity.assert_called_once()
        call_args = mock_client.create_entity.call_args
        assert call_args[0][0] == "ServiceLevelAgreementResults"
        assignment_data = call_args[0][1]
        assert assignment_data["AccountID"] == 12345
        assert assignment_data["ServiceLevelAgreementID"] == 222
        assert assignment_data["EffectiveDate"] == effective_date.isoformat()

    # =============================================================================
    # Location and Address Management Tests
    # =============================================================================

    def test_update_company_address(self, companies_entity, mock_client):
        """Test updating company address."""
        mock_client.update.return_value = Mock()
        
        companies_entity.update_company_address(
            12345,
            address1="456 New Street",
            city="Los Angeles",
            state="CA",
            postal_code="90210",
            validate_address=False
        )
        
        expected_data = {
            "id": 12345,
            "Address1": "456 New Street",
            "City": "Los Angeles",
            "State": "CA",
            "PostalCode": "90210",
        }
        mock_client.update.assert_called_once_with("Companies", expected_data)

    def test_update_company_address_with_validation(self, companies_entity, mock_client):
        """Test updating company address with validation."""
        mock_client.update.return_value = Mock()
        
        # Valid address should work
        companies_entity.update_company_address(
            12345,
            address1="123 Valid Street",
            validate_address=True
        )
        mock_client.update.assert_called_once()

        # Invalid address should raise error
        long_address = "x" * (FieldLengths.ADDRESS_LINE_MAX + 1)
        with pytest.raises(ValueError, match="Address1 must be"):
            companies_entity.update_company_address(
                12345,
                address1=long_address,
                validate_address=True
            )

    def test_get_company_locations(self, companies_entity, mock_client):
        """Test getting company locations."""
        mock_response = Mock()
        mock_response.items = [
            {"id": 444, "CompanyID": 12345, "Name": "Headquarters"}
        ]
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_company_locations(12345)
        
        mock_client.query.assert_called_once()
        assert len(result) == 1

    def test_add_company_location(self, companies_entity, mock_client):
        """Test adding a company location."""
        mock_client.create_entity.return_value = Mock(item_id=444)
        
        companies_entity.add_company_location(
            12345,
            "Branch Office",
            "789 Branch Ave",
            "Chicago",
            "IL",
            "60601",
            "USA",
            is_primary=False
        )
        
        mock_client.create_entity.assert_called_once()
        call_args = mock_client.create_entity.call_args
        assert call_args[0][0] == "CompanyLocations"
        location_data = call_args[0][1]
        assert location_data["CompanyID"] == 12345
        assert location_data["Name"] == "Branch Office"
        assert location_data["Primary"] is False

    # =============================================================================
    # Custom Fields Tests
    # =============================================================================

    def test_get_company_custom_fields(self, companies_entity, mock_client):
        """Test getting company custom fields."""
        company_data = {
            "id": 12345,
            "CompanyName": "Acme Corp",
            "UserDefinedField1": "Custom Value 1",
            "UserDefinedField2": "Custom Value 2",
        }
        mock_client.get.return_value = company_data
        
        result = companies_entity.get_company_custom_fields(12345)
        
        mock_client.get.assert_called_once_with("Companies", 12345)
        assert result["UserDefinedField1"] == "Custom Value 1"
        assert result["UserDefinedField2"] == "Custom Value 2"
        assert "CompanyName" not in result

    def test_update_company_custom_fields(self, companies_entity, mock_client):
        """Test updating company custom fields."""
        mock_client.update.return_value = Mock()
        custom_fields = {
            "UserDefinedField1": "New Value 1",
            "UserDefinedField2": "New Value 2",
        }
        
        companies_entity.update_company_custom_fields(12345, custom_fields)
        
        expected_data = {"id": 12345, **custom_fields}
        mock_client.update.assert_called_once_with("Companies", expected_data)

    # =============================================================================
    # Bulk Operations Tests
    # =============================================================================

    def test_bulk_update_companies(self, companies_entity, mock_client):
        """Test bulk updating companies."""
        mock_client.update.side_effect = [Mock(), Mock()]
        
        updates = [
            {"id": 12345, "City": "New York", "State": "NY"},
            {"id": 12346, "Active": False},
        ]
        
        result = companies_entity.bulk_update_companies(updates)
        
        assert len(result) == 2
        assert mock_client.update.call_count == 2

    def test_bulk_deactivate_companies(self, companies_entity, mock_client):
        """Test bulk deactivating companies."""
        mock_client.update.side_effect = [Mock(), Mock()]
        
        companies_entity.bulk_deactivate_companies([12345, 12346], "Contract ended")
        
        assert mock_client.update.call_count == 2
        # Check that both calls include Active: False and the reason
        for call in mock_client.update.call_args_list:
            entity_data = call[0][1]  # Second argument is the entity data
            assert entity_data["Active"] is False
            assert entity_data["InactiveReason"] == "Contract ended"

    def test_bulk_transfer_companies(self, companies_entity, mock_client):
        """Test bulk transferring companies."""
        mock_client.update.side_effect = [Mock(), Mock()]
        
        companies_entity.bulk_transfer_companies([12345, 12346], 200, 10)
        
        assert mock_client.update.call_count == 2
        for call in mock_client.update.call_args_list:
            entity_data = call[0][1]  # Second argument is the entity data
            assert entity_data["OwnerResourceID"] == 200
            assert entity_data["TerritoryID"] == 10

    # =============================================================================
    # Analytics and Reporting Tests
    # =============================================================================

    def test_get_company_activity_summary(self, companies_entity, mock_client):
        """Test getting company activity summary."""
        # Mock ticket and project data
        tickets_data = [
            {"Status": 1}, {"Status": 5}, {"Status": 8}  # New, Closed, In Progress
        ]
        projects_data = [
            {"Status": 2}, {"Status": 5}  # In Progress, Complete
        ]
        
        with patch.object(companies_entity, 'get_company_tickets', return_value=tickets_data):
            with patch.object(companies_entity, 'get_company_projects', return_value=projects_data):
                result = companies_entity.get_company_activity_summary(12345, date_range_days=30)
        
        assert result["company_id"] == 12345
        assert result["total_tickets"] == 3
        assert result["open_tickets"] == 2  # Status 1 and 8
        assert result["closed_tickets"] == 1  # Status 5
        assert result["total_projects"] == 2
        assert result["active_projects"] == 1  # Status 2 (not complete)

    def test_get_companies_by_performance_metrics(self, companies_entity, mock_client):
        """Test getting companies by performance metrics."""
        customers_data = [
            {"id": 12345, "CompanyName": "Acme Corp"},
            {"id": 12346, "CompanyName": "Beta Corp"},
        ]
        
        with patch.object(companies_entity, 'get_customer_companies', return_value=customers_data):
            with patch.object(companies_entity, 'get_company_activity_summary') as mock_activity:
                mock_activity.side_effect = [
                    {"total_tickets": 10}, {"total_tickets": 5}
                ]
                
                result = companies_entity.get_companies_by_performance_metrics(
                    metric="tickets", limit=10
                )
        
        assert len(result) == 2
        assert result[0]["company_id"] == 12345  # Higher ticket count first
        assert result[0]["metric_value"] == 10
        assert result[1]["company_id"] == 12346
        assert result[1]["metric_value"] == 5

    def test_get_company_growth_trends(self, companies_entity):
        """Test getting company growth trends."""
        result = companies_entity.get_company_growth_trends(12345, months=6)
        
        assert result["company_id"] == 12345
        assert result["analysis_period_months"] == 6
        assert "monthly_metrics" in result
        assert "growth_indicators" in result

    # =============================================================================
    # Enhanced Relationship Management Tests
    # =============================================================================

    def test_get_company_tickets_enhanced(self, companies_entity, mock_client):
        """Test enhanced ticket retrieval with filters."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response
        cutoff_date = datetime.now() - timedelta(days=7)
        
        companies_entity.get_company_tickets(
            12345,
            status_filter="open",
            priority_filter=1,
            date_range_days=7,
            limit=100
        )
        
        # Verify filters include status, priority, and date range
        call_args = mock_client.query.call_args
        filters = call_args[1]["filters"]
        
        # Should have AccountID, Status (in), Priority, and CreateDate filters
        assert len(filters) >= 4
        account_filter = next(f for f in filters if f.field == "AccountID")
        assert account_filter.value == 12345

    def test_get_company_projects_enhanced(self, companies_entity, mock_client):
        """Test enhanced project retrieval with filters."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response
        
        companies_entity.get_company_projects(
            12345,
            status_filter="active",
            project_type=1,
            date_range_days=30
        )
        
        call_args = mock_client.query.call_args
        filters = call_args[1]["filters"]
        
        # Should have AccountID, Status, Type, and CreateDate filters
        assert len(filters) >= 4

    def test_get_company_opportunities(self, companies_entity, mock_client):
        """Test getting company opportunities."""
        mock_response = Mock()
        mock_response.items = [
            {"id": 555, "AccountID": 12345, "Stage": 1}
        ]
        mock_client.query.return_value = mock_response
        
        result = companies_entity.get_company_opportunities(12345, stage_filter="open")
        
        expected_filters = [
            QueryFilter(field="AccountID", op="eq", value=12345),
            QueryFilter(field="Stage", op="in", value=[1, 2, 3, 4]),
        ]
        mock_client.query.assert_called_once_with("Opportunities", filters=expected_filters, max_records=None)

    # =============================================================================
    # Validation Tests
    # =============================================================================

    def test_validate_company_name(self, companies_entity):
        """Test company name validation."""
        # Valid name should not raise error
        companies_entity._validate_company_name("Valid Company Name")
        
        # Empty name should raise error
        with pytest.raises(ValueError, match="Company name is required"):
            companies_entity._validate_company_name("")
        
        with pytest.raises(ValueError, match="Company name is required"):
            companies_entity._validate_company_name("   ")
        
        # Too long name should raise error
        long_name = "x" * (FieldLengths.NAME_MAX + 1)
        with pytest.raises(ValueError, match="Company name must be"):
            companies_entity._validate_company_name(long_name)

    def test_validate_company_updates(self, companies_entity):
        """Test company update validation."""
        # Valid updates should not raise error
        valid_updates = {
            "CompanyName": "Valid Name",
            "Phone": "555-123-4567",
            "WebAddress": "https://example.com"
        }
        companies_entity._validate_company_updates(valid_updates)
        
        # Invalid phone should raise error
        invalid_phone_updates = {"Phone": "x" * (FieldLengths.PHONE_MAX + 1)}
        with pytest.raises(ValueError, match="Phone number must be"):
            companies_entity._validate_company_updates(invalid_phone_updates)
        
        # Invalid website should raise error
        invalid_web_updates = {"WebAddress": "x" * 256}
        with pytest.raises(ValueError, match="Website URL must be"):
            companies_entity._validate_company_updates(invalid_web_updates)

    def test_validate_address_field(self, companies_entity):
        """Test address field validation."""
        # Valid address field should not raise error
        companies_entity._validate_address_field("Address1", "123 Main St")
        
        # Too long address should raise error
        long_address = "x" * (FieldLengths.ADDRESS_LINE_MAX + 1)
        with pytest.raises(ValueError, match="Address1 must be"):
            companies_entity._validate_address_field("Address1", long_address)
        
        # Test other address fields
        long_city = "x" * (FieldLengths.CITY_MAX + 1)
        with pytest.raises(ValueError, match="City must be"):
            companies_entity._validate_address_field("City", long_city)