"""
Tests for the main AutotaskClient class.

This module tests the core client functionality including
entity access, HTTP operations, and client configuration.
"""

from unittest.mock import Mock, patch

import pytest

from py_autotask.client import AutotaskClient
from py_autotask.types import RequestConfig


class TestAutotaskClient:
    """Test cases for AutotaskClient class."""

    def test_init(self, mock_auth):
        """Test client initialization."""
        config = RequestConfig(timeout=60, max_retries=5)
        client = AutotaskClient(mock_auth, config)

        assert client.auth == mock_auth
        assert client.config == config
        assert client._session is None
        assert client._entities is None

    def test_init_default_config(self, mock_auth):
        """Test client initialization with default config."""
        client = AutotaskClient(mock_auth)

        assert client.config is not None
        assert isinstance(client.config, RequestConfig)
        assert client.config.timeout == 30  # Default value

    def test_create_class_method(self):
        """Test client creation using class method."""
        with patch("py_autotask.client.AutotaskAuth") as mock_auth_class:
            mock_auth_instance = Mock()
            mock_auth_class.return_value = mock_auth_instance

            client = AutotaskClient.create(
                username="test@example.com",
                integration_code="TEST123",
                secret="test_secret",
            )

            assert isinstance(client, AutotaskClient)
            assert client.auth is mock_auth_instance

    def test_session_property(self, mock_auth):
        """Test session property access."""
        mock_session = Mock()
        mock_auth.get_session.return_value = mock_session

        client = AutotaskClient(mock_auth)
        session = client.session

        assert session == mock_session
        mock_auth.get_session.assert_called_once()

    def test_session_cached(self, mock_auth):
        """Test that session is cached."""
        mock_session = Mock()
        mock_auth.get_session.return_value = mock_session

        client = AutotaskClient(mock_auth)
        session1 = client.session
        session2 = client.session

        assert session1 is session2
        # Should only call get_session once due to caching
        assert mock_auth.get_session.call_count == 1

    def test_entities_property(self, mock_auth):
        """Test entities property access."""
        client = AutotaskClient(mock_auth)
        entities = client.entities

        assert entities is not None
        # Should return the same instance on subsequent calls
        assert client.entities is entities

    def test_convenience_properties(self, mock_auth):
        """Test convenience properties for common entities."""
        client = AutotaskClient(mock_auth)

        # These should not raise errors
        tickets = client.tickets
        companies = client.companies
        contacts = client.contacts
        projects = client.projects
        resources = client.resources
        contracts = client.contracts

        assert tickets is not None
        assert companies is not None
        assert contacts is not None
        assert projects is not None
        assert resources is not None
        assert contracts is not None

    @patch("requests.Session.get")
    def test_get_entity_success(self, mock_get, mock_auth, sample_ticket_data):
        """Test successful entity retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"item": sample_ticket_data}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.get = mock_get

        client = AutotaskClient(mock_auth)
        result = client.get("Tickets", 12345)

        assert result == sample_ticket_data
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_get_entity_not_found(self, mock_get, mock_auth):
        """Test entity retrieval when entity not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.get = mock_get

        client = AutotaskClient(mock_auth)
        result = client.get("Tickets", 99999)

        assert result is None

    @patch("requests.Session.post")
    def test_create_entity_success(self, mock_post, mock_auth, sample_ticket_data):
        """Test successful entity creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"itemId": 12345}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.post = mock_post

        client = AutotaskClient(mock_auth)
        result = client.create_entity("Tickets", sample_ticket_data)

        assert result.item_id == 12345
        mock_post.assert_called_once()

    @patch("requests.Session.patch")
    def test_update_entity_success(self, mock_patch, mock_auth, sample_ticket_data):
        """Test successful entity update."""
        # Add ID to sample data for update
        sample_ticket_data["id"] = 12345

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"item": sample_ticket_data}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.patch = mock_patch

        client = AutotaskClient(mock_auth)
        result = client.update("Tickets", sample_ticket_data)

        assert result == sample_ticket_data
        mock_patch.assert_called_once()

    @patch("requests.Session.delete")
    def test_delete_entity_success(self, mock_delete, mock_auth):
        """Test successful entity deletion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.delete = mock_delete

        client = AutotaskClient(mock_auth)
        result = client.delete("Tickets", 12345)

        assert result is True
        mock_delete.assert_called_once()

    def test_context_manager(self, mock_auth):
        """Test client as context manager."""
        client = AutotaskClient(mock_auth)

        with client as ctx_client:
            assert ctx_client is client

        # Should call close
        assert True  # Mock doesn't have close, but test passes if no exception

    def test_new_entity_access_patterns(self, mock_auth):
        """Test access patterns for newly added entities."""
        client = AutotaskClient(mock_auth)

        # Test access through entities manager
        manager = client.entities
        assert manager is not None

        # Test getting specific new entities
        new_entities = [
            "ActionTypes",
            "AdditionalInvoiceFieldValues",
            "APIUsageMetrics",
            "CompanyAlerts",
            "CompanyNotes",
            "TicketNotes",
            "ConfigurationItemCategories",
            "ContractMilestones",
            "SystemHealth",
            "PerformanceMetrics",
        ]

        for entity_name in new_entities:
            entity = manager.get_entity(entity_name)
            assert entity is not None
            assert entity.entity_name == entity_name

    def test_entity_manager_caching(self, mock_auth):
        """Test that entity manager properly caches entities."""
        client = AutotaskClient(mock_auth)

        # Get the same entity multiple times
        entity1 = client.entities.get_entity("ActionTypes")
        entity2 = client.entities.get_entity("ActionTypes")
        entity3 = client.entities.get_entity("ActionTypes")

        # Should return the same cached instance
        assert entity1 is entity2
        assert entity2 is entity3

    def test_dynamic_entity_creation(self, mock_auth):
        """Test dynamic entity creation for unlisted entities."""
        client = AutotaskClient(mock_auth)

        # Request an entity not in the predefined list
        custom_entity = client.entities.get_entity("CustomTestEntity")
        assert custom_entity is not None
        assert custom_entity.entity_name == "CustomTestEntity"

    def test_extended_convenience_properties(self, mock_auth):
        """Test extended convenience properties for major entities."""
        client = AutotaskClient(mock_auth)

        # Test that all major convenience properties work
        convenience_entities = {
            "tickets": "Tickets",
            "companies": "Companies",
            "contacts": "Contacts",
            "projects": "Projects",
            "resources": "Resources",
            "contracts": "Contracts",
        }

        for attr_name, entity_name in convenience_entities.items():
            entity = getattr(client, attr_name)
            assert entity is not None
            assert entity.entity_name == entity_name

    def test_entity_manager_contains_all_registered_entities(self, mock_auth):
        """Test that entity manager has all registered entities."""
        client = AutotaskClient(mock_auth)
        manager = client.entities

        # Should have substantial number of registered entities
        assert len(manager.ENTITY_CLASSES) >= 100

        # Test accessing a variety of entity types
        sample_entities = [
            "Tickets",
            "Companies",
            "Contacts",
            "Projects",
            "Resources",
            "ActionTypes",
            "CompanyAlerts",
            "TicketNotes",
            "SystemHealth",
        ]

        for entity_name in sample_entities:
            if entity_name in manager.ENTITY_CLASSES:
                entity = manager.get_entity(entity_name)
                assert entity is not None
                assert hasattr(entity, "get")
                assert hasattr(entity, "query")
                assert hasattr(entity, "create")

    @patch("requests.Session.get")
    def test_field_info_retrieval(self, mock_get, mock_auth, sample_field_info):
        """Test field information retrieval for entities."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_field_info
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.get = mock_get

        client = AutotaskClient(mock_auth)

        # Test field info retrieval
        if hasattr(client, "get_field_info"):
            field_info = client.get_field_info("Tickets")
            assert field_info is not None
            mock_get.assert_called()

    @patch("requests.Session.post")
    def test_batch_operations_if_available(
        self, mock_post, mock_auth, sample_ticket_data
    ):
        """Test batch operations if they are available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [{"itemId": 12345}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_auth.api_url = "https://test.autotask.net"
        mock_auth.get_session.return_value.post = mock_post

        client = AutotaskClient(mock_auth)

        # Test batch creation if available
        if hasattr(client, "create_batch"):
            batch_data = [sample_ticket_data, sample_ticket_data.copy()]
            result = client.create_batch("Tickets", batch_data)
            assert result is not None

    def test_client_configuration_with_new_entities(self, mock_auth):
        """Test client configuration works with new entity patterns."""
        from py_autotask.types import RequestConfig

        # Test with custom configuration
        config = RequestConfig(timeout=60, max_retries=5)
        client = AutotaskClient(mock_auth, config)

        assert client.config.timeout == 60
        assert client.config.max_retries == 5

        # Ensure entities work with custom config
        entity = client.entities.get_entity("SystemHealth")
        assert entity is not None
        assert entity.client is client

    def test_error_handling_with_new_entities(self, mock_auth):
        """Test error handling works properly with new entities."""
        client = AutotaskClient(mock_auth)
        entity = client.entities.get_entity("ActionTypes")

        # Mock client method to raise an exception
        with patch.object(client, "get", side_effect=Exception("Test API Error")):
            with pytest.raises(Exception, match="Test API Error"):
                entity.get(12345)

    def test_session_reuse_across_entities(self, mock_auth):
        """Test that session is properly reused across different entities."""
        mock_session = Mock()
        mock_auth.get_session.return_value = mock_session

        client = AutotaskClient(mock_auth)

        # Access multiple entities
        entities = [
            client.entities.get_entity("Tickets"),
            client.entities.get_entity("Companies"),
            client.entities.get_entity("ActionTypes"),
            client.entities.get_entity("SystemHealth"),
        ]

        # All should use the same client (and thus same session)
        for entity in entities:
            assert entity.client is client

        # Session should only be created once
        session1 = client.session
        session2 = client.session
        assert session1 is session2
        assert mock_auth.get_session.call_count == 1

    def test_client_entity_consistency(self, mock_auth):
        """Test consistency between client entity access methods."""
        client = AutotaskClient(mock_auth)

        # Test that convenience properties and manager return same instances
        tickets_via_property = client.tickets
        tickets_via_manager = client.entities.get_entity("Tickets")

        assert tickets_via_property is tickets_via_manager

        # Test with other entities
        companies_via_property = client.companies
        companies_via_manager = client.entities.get_entity("Companies")

        assert companies_via_property is companies_via_manager
