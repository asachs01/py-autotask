"""
Pytest configuration and fixtures for py-autotask tests.

This module provides common fixtures and configuration for all tests,
including mock clients, sample data, and test utilities.
"""

from typing import Any, Dict
from unittest.mock import Mock

import pytest
import responses
from requests import Session

from py_autotask import AutotaskClient
from py_autotask.auth import AutotaskAuth
from py_autotask.types import AuthCredentials, ZoneInfo


@pytest.fixture(autouse=True)
def clear_auth_cache():
    """Clear authentication cache before each test."""
    # Clear the cache before each test
    AutotaskAuth.clear_zone_cache()
    yield
    # Optionally clear after test as well
    AutotaskAuth.clear_zone_cache()


@pytest.fixture
def sample_credentials():
    """Sample authentication credentials for testing."""
    return AuthCredentials(
        username="test@example.com",
        integration_code="TEST123",
        secret="test_secret",
        api_url=None,
    )


@pytest.fixture
def sample_zone_info():
    """Sample zone information for testing."""
    return ZoneInfo(
        url="https://webservices123.autotask.net/atservicesrest",
        dataBaseType="Production",
        ciLevel=1,
    )


@pytest.fixture
def mock_auth(sample_credentials, sample_zone_info):
    """Mock authentication object for testing."""
    auth = Mock(spec=AutotaskAuth)
    auth.credentials = sample_credentials
    auth.zone_info = sample_zone_info
    auth.api_url = sample_zone_info.url
    auth.get_session.return_value = Mock(spec=Session)
    auth.validate_credentials.return_value = True
    return auth


@pytest.fixture
def mock_client(mock_auth):
    """Mock AutotaskClient for testing."""
    client = Mock(spec=AutotaskClient)
    client.auth = mock_auth
    client.session = Mock(spec=Session)

    # Mock entity managers
    client.tickets = Mock()
    client.companies = Mock()
    client.contacts = Mock()
    client.projects = Mock()
    client.resources = Mock()
    client.contracts = Mock()

    return client


@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "id": 12345,
        "title": "Test Ticket",
        "description": "This is a test ticket",
        "status": 1,
        "priority": 3,
        "accountID": 67890,
        "assignedResourceID": 111,
        "createdDateTime": "2023-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "id": 67890,
        "companyName": "Test Company",
        "companyType": 1,
        "isActive": True,
        "ownerResourceID": 111,
        "createdDate": "2023-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_query_response(sample_ticket_data):
    """Sample query response for testing."""
    return {
        "items": [sample_ticket_data],
        "pageDetails": {
            "count": 1,
            "requestCount": 50,
            "nextPageUrl": None,
            "prevPageUrl": None,
        },
    }


@pytest.fixture
def sample_field_info():
    """Sample field information for testing."""
    return {
        "fields": [
            {
                "name": "id",
                "dataType": "integer",
                "length": 0,
                "isRequired": False,
                "isReadOnly": True,
                "isQueryable": True,
                "isReference": False,
                "referenceEntityType": "",
                "isPickList": False,
                "picklistValues": None,
                "picklistParentValueField": "",
            },
            {
                "name": "title",
                "dataType": "string",
                "length": 255,
                "isRequired": True,
                "isReadOnly": False,
                "isQueryable": True,
                "isReference": False,
                "referenceEntityType": "",
                "isPickList": False,
                "picklistValues": None,
                "picklistParentValueField": "",
            },
        ]
    }


@pytest.fixture
def responses_mock():
    """Responses mock for HTTP testing."""
    with responses.RequestsMock() as rsps:
        # Mock zone detection
        rsps.add(
            responses.GET,
            "https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation",
            json={
                "url": "https://webservices123.autotask.net/atservicesrest",
                "dataBaseType": "Production",
                "ciLevel": 1,
            },
            status=200,
        )
        yield rsps


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        "AUTOTASK_USERNAME": "test@example.com",
        "AUTOTASK_INTEGRATION_CODE": "TEST123",
        "AUTOTASK_SECRET": "test_secret",
        "AUTOTASK_API_URL": "https://webservices123.autotask.net/atservicesrest",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_response():
    """Factory for creating mock responses."""
    return MockResponse


# Test data constants
TEST_API_URL = "https://webservices123.autotask.net/atservicesrest"
TEST_USERNAME = "test@example.com"
TEST_INTEGRATION_CODE = "TEST123"
TEST_SECRET = "test_secret"
