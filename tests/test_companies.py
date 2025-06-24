"""
Tests for the CompaniesEntity class.

This module tests company/account-specific operations and functionality.
"""

from unittest.mock import Mock

import pytest

from py_autotask.entities.companies import CompaniesEntity


class TestCompaniesEntity:
    """Test cases for CompaniesEntity."""

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
            "companyName": "Test Company",
            "companyType": 1,
            "phone": "555-1234",
            "address1": "123 Main St",
            "city": "Anytown",
            "state": "NY",
            "postalCode": "12345",
            "country": "USA",
            "active": True,
            "createDate": "2023-01-01T00:00:00Z",
            "lastModifiedDate": "2023-01-01T00:00:00Z",
        }

    def test_create_company_basic(self, companies_entity, mock_client):
        """Test basic company creation."""
        mock_client.create_entity.return_value = Mock(item_id=12345)

        result = companies_entity.create_company("Acme Corp")

        assert result.item_id == 12345
        mock_client.create_entity.assert_called_once()

        call_args = mock_client.create_entity.call_args
        assert call_args[0][0] == "Companies"  # entity_type
        company_data = call_args[0][1]  # entity_data is the second positional argument
        assert company_data["CompanyName"] == "Acme Corp"

    def test_create_company_with_address(self, companies_entity, mock_client):
        """Test company creation with address."""
        mock_client.create_entity.return_value = Mock(item_id=12345)

        _ = companies_entity.create_company(
            company_name="Acme Corp",
            phone="555-1234",
            address1="123 Main St",
            city="Anytown",
            state="NY",
            postal_code="12345",
            country="USA",
        )

        call_args = mock_client.create_entity.call_args
        company_data = call_args[0][1]  # entity_data is the second positional argument
        assert company_data["Phone"] == "555-1234"
        assert company_data["Address1"] == "123 Main St"
        assert company_data["City"] == "Anytown"
        assert company_data["State"] == "NY"
        assert company_data["PostalCode"] == "12345"
        assert company_data["Country"] == "USA"

    def test_search_companies_by_name_exact(self, companies_entity, mock_client):
        """Test exact name search."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        companies_entity.search_companies_by_name("Acme Corp", exact_match=True)

        call_args = mock_client.query.call_args
        # query() is called with entity_name and QueryRequest object
        assert call_args[0][0] == "Companies"
        query_request = call_args[0][1]
        assert hasattr(query_request, "filter")
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "CompanyName"
        assert filters[0].op == "eq"
        assert filters[0].value == "Acme Corp"

    def test_search_companies_by_name_partial(self, companies_entity, mock_client):
        """Test partial name search."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        companies_entity.search_companies_by_name("Acme", exact_match=False)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Companies"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "CompanyName"
        assert filters[0].op == "contains"
        assert filters[0].value == "Acme"

    def test_get_companies_by_type(self, companies_entity, mock_client):
        """Test getting companies by type."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        companies_entity.get_companies_by_type(1, active_only=True)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Companies"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "CompanyType"
        assert filters[0].value == 1
        assert filters[1].field == "Active"
        assert filters[1].value is True

    def test_get_customer_companies(self, companies_entity, mock_client):
        """Test getting customer companies."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        companies_entity.get_customer_companies(active_only=True)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Companies"
        query_request = call_args[0][1]
        filters = query_request.filter
        # Should call get_companies_by_type with type 1 (Customer)
        assert filters[0].field == "CompanyType"
        assert filters[0].value == 1

    def test_get_prospect_companies(self, companies_entity, mock_client):
        """Test getting prospect companies."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        companies_entity.get_prospect_companies(active_only=False)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Companies"
        query_request = call_args[0][1]
        filters = query_request.filter
        # Should call get_companies_by_type with type 3 (Prospect)
        assert filters[0].field == "CompanyType"
        assert filters[0].value == 3

    def test_get_company_contacts(self, companies_entity, mock_client):
        """Test getting company contacts."""
        mock_client.query.return_value = []

        companies_entity.get_company_contacts(12345)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Contacts"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 1
        assert filters[0].field == "CompanyID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345

    def test_get_company_tickets(self, companies_entity, mock_client):
        """Test getting company tickets."""
        mock_client.query.return_value = []

        companies_entity.get_company_tickets(12345, status_filter="open")

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Tickets"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 2
        assert filters[0].field == "AccountID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345
        assert filters[1].field == "Status"
        assert filters[1].op == "in"
        assert filters[1].value == [1, 8, 9, 10, 11]

    def test_get_company_projects(self, companies_entity, mock_client):
        """Test getting company projects."""
        mock_client.query.return_value = []

        companies_entity.get_company_projects(12345, active_only=True)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Projects"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 2
        assert filters[0].field == "AccountID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345
        assert filters[1].field == "Status"
        assert filters[1].op == "ne"
        assert filters[1].value == 5  # Not Complete

    def test_get_company_contracts(self, companies_entity, mock_client):
        """Test getting company contracts."""
        mock_client.query.return_value = []

        companies_entity.get_company_contracts(12345, active_only=True)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Contracts"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 2
        assert filters[0].field == "AccountID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345
        assert filters[1].field == "Status"
        assert filters[1].op == "eq"
        assert filters[1].value == 1  # Active

    def test_update_company_address(self, companies_entity, mock_client):
        """Test updating company address."""
        mock_client.update.return_value = {}

        companies_entity.update_company_address(
            12345,
            address1="456 Oak St",
            city="New City",
            state="CA",
            postal_code="90210",
        )

        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        assert call_args[0][0] == "Companies"  # entity_type
        entity_data = call_args[0][1]  # entity_data is second positional argument
        assert entity_data["id"] == 12345
        assert entity_data["Address1"] == "456 Oak St"
        assert entity_data["City"] == "New City"
        assert entity_data["State"] == "CA"
        assert entity_data["PostalCode"] == "90210"

    def test_activate_company(self, companies_entity, mock_client):
        """Test activating a company."""
        mock_client.update.return_value = {}

        companies_entity.activate_company(12345)

        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]  # entity_data is second positional argument
        assert entity_data["id"] == 12345
        assert entity_data["Active"] is True

    def test_deactivate_company(self, companies_entity, mock_client):
        """Test deactivating a company."""
        mock_client.update.return_value = {}

        companies_entity.deactivate_company(12345)

        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]  # entity_data is second positional argument
        assert entity_data["id"] == 12345
        assert entity_data["Active"] is False

    def test_get_companies_by_location(self, companies_entity, mock_client):
        """Test getting companies by location."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        companies_entity.get_companies_by_location(
            city="Anytown", state="NY", country="USA"
        )

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Companies"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 3

        # Check that all location filters are present
        fields = [f.field for f in filters]
        assert "City" in fields
        assert "State" in fields
        assert "Country" in fields
