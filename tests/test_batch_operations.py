"""
Tests for batch operations functionality.

This module tests batch create, update, and delete operations
for all entity types through the client and entity classes.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from py_autotask.client import AutotaskClient
from py_autotask.entities.base import BaseEntity
from py_autotask.entities.companies import CompaniesEntity
from py_autotask.entities.tickets import TicketsEntity
from py_autotask.exceptions import (
    AutotaskAPIError,
)
from py_autotask.types import CreateResponse


class TestBatchOperations:
    """Test cases for batch operations."""

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        session = Mock(spec=requests.Session)
        session.post.return_value = Mock(status_code=200)
        session.patch.return_value = Mock(status_code=200)
        session.delete.return_value = Mock(status_code=200)
        return session

    @pytest.fixture
    def mock_client(self, mock_session):
        """Mock AutotaskClient with properly configured attributes."""
        client = Mock(spec=AutotaskClient)
        client._session = mock_session
        client.session = mock_session
        client.logger = Mock()

        # Mock auth with api_url
        client.auth = Mock()
        client.auth.api_url = "https://api.autotask.net"
        client.auth.close = Mock()

        # Mock config
        client.config = Mock()
        client.config.timeout = 30

        return client

    @pytest.fixture
    def sample_entities_data(self):
        """Sample entity data for testing."""
        return [
            {
                "title": "Test Ticket 1",
                "description": "First test ticket",
                "accountID": 123,
            },
            {
                "title": "Test Ticket 2",
                "description": "Second test ticket",
                "accountID": 124,
            },
            {
                "title": "Test Ticket 3",
                "description": "Third test ticket",
                "accountID": 125,
            },
        ]

    @pytest.fixture
    def sample_update_data(self):
        """Sample entity update data for testing."""
        return [
            {"id": 1001, "priority": 1, "status": 8},
            {"id": 1002, "priority": 2, "status": 5},
            {"id": 1003, "priority": 3, "status": 1},
        ]

    def test_client_batch_create_success(self, mock_client, sample_entities_data):
        """Test successful batch create via client."""
        # Mock the HTTP response for the batch API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"itemId": 12345},
            {"itemId": 12346},
            {"itemId": 12347},
        ]

        mock_client._session.post.return_value = mock_response

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_create("Tickets", sample_entities_data, batch_size=200)

        assert len(results) == 3
        assert all(result.item_id is not None for result in results)
        assert [r.item_id for r in results] == [12345, 12346, 12347]

    def test_client_batch_create_with_errors(self, mock_client, sample_entities_data):
        """Test batch create with some failures."""
        # Mock HTTP error on batch request
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Bad Request"
        )

        mock_client._session.post.return_value = mock_response

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        # Test that HTTP errors are handled
        with pytest.raises((requests.exceptions.HTTPError, AutotaskAPIError)):
            client.batch_create("Tickets", sample_entities_data)

    def test_client_batch_create_exceeds_batch_size(self, mock_client):
        """Test batch create with batch size exceeding limit."""
        large_data = [{"test": f"data{i}"} for i in range(250)]

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        with pytest.raises(ValueError, match="Batch size cannot exceed 200"):
            client.batch_create("Tickets", large_data, batch_size=250)

    def test_client_batch_update_success(self, mock_client, sample_update_data):
        """Test successful batch update via client."""
        # Mock the HTTP response for the batch update API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id": 1001, "priority": 1, "status": 8},
            {"id": 1002, "priority": 2, "status": 5},
            {"id": 1003, "priority": 3, "status": 1},
        ]

        mock_client._session.patch.return_value = mock_response

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_update("Tickets", sample_update_data)

        assert len(results) == 3
        assert all("id" in result for result in results)

    def test_client_batch_update_missing_ids(self, mock_client):
        """Test batch update with missing IDs."""
        data_without_ids = [
            {"priority": 1, "status": 8},  # Missing ID
            {"id": 1002, "priority": 2, "status": 5},
        ]

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        with pytest.raises(ValueError, match="Entity at index 0 missing 'id' field"):
            client.batch_update("Tickets", data_without_ids)

    def test_client_batch_delete_success(self, mock_client):
        """Test successful batch delete via client."""
        entity_ids = [1001, 1002, 1003]

        # Mock successful delete response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        mock_client._session.delete.return_value = mock_response

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_delete("Tickets", entity_ids)

        assert len(results) == 3
        assert all(result is True for result in results)

    def test_client_batch_delete_with_failures(self, mock_client):
        """Test batch delete with some failures."""
        entity_ids = [1001, 1002, 1003]

        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Not Found"
        )

        mock_client._session.delete.return_value = mock_response

        # Create properly mocked client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_delete("Tickets", entity_ids)

        # Batch delete handles errors gracefully and returns False for failed deletions
        assert len(results) == 3
        assert all(result is False for result in results)  # All should fail

    def test_base_entity_batch_create(self, mock_client, sample_entities_data):
        """Test batch create via BaseEntity."""
        # Mock successful create responses
        mock_responses = [
            CreateResponse(itemId=12345),
            CreateResponse(itemId=12346),
            CreateResponse(itemId=12347),
        ]

        mock_client.batch_create.return_value = mock_responses

        entity = BaseEntity(mock_client, "Tickets")

        results = entity.batch_create(sample_entities_data)

        assert len(results) == 3
        assert all(result.item_id is not None for result in results)

    def test_base_entity_batch_update(self, mock_client, sample_update_data):
        """Test batch update via BaseEntity."""
        mock_responses = [
            {"id": 1001, "priority": 1},
            {"id": 1002, "priority": 2},
            {"id": 1003, "priority": 3},
        ]

        mock_client.batch_update.return_value = mock_responses

        entity = BaseEntity(mock_client, "Tickets")

        results = entity.batch_update(sample_update_data)

        assert len(results) == 3
        assert all("id" in result for result in results)

    def test_base_entity_batch_delete(self, mock_client):
        """Test batch delete via BaseEntity."""
        entity_ids = [1001, 1002, 1003]

        mock_client.batch_delete.return_value = [True, True, True]

        entity = BaseEntity(mock_client, "Tickets")

        results = entity.batch_delete(entity_ids)

        assert len(results) == 3
        assert all(result is True for result in results)

    def test_tickets_entity_batch_create(self, mock_client):
        """Test batch create via TicketsEntity."""
        ticket_data = [
            {"title": "Ticket 1", "description": "First ticket", "accountID": 123},
            {"title": "Ticket 2", "description": "Second ticket", "accountID": 124},
        ]

        mock_responses = [CreateResponse(itemId=12345), CreateResponse(itemId=12346)]

        mock_client.batch_create.return_value = mock_responses

        tickets_entity = TicketsEntity(mock_client, "Tickets")

        results = tickets_entity.batch_create(ticket_data)

        assert len(results) == 2
        assert all(result.item_id is not None for result in results)

    def test_companies_entity_batch_update(self, mock_client):
        """Test batch update via CompaniesEntity."""
        company_data = [
            {"id": 1001, "companyName": "Updated Company 1"},
            {"id": 1002, "companyName": "Updated Company 2"},
        ]

        mock_responses = [
            {"id": 1001, "companyName": "Updated Company 1"},
            {"id": 1002, "companyName": "Updated Company 2"},
        ]

        mock_client.batch_update.return_value = mock_responses

        companies_entity = CompaniesEntity(mock_client, "Companies")

        results = companies_entity.batch_update(company_data)

        assert len(results) == 2
        assert all("id" in result for result in results)

    def test_batch_create_with_batching(self, mock_client):
        """Test batch create with automatic batching."""
        # Create data that exceeds batch size
        large_data = [{"test": f"data{i}"} for i in range(250)]

        # Mock HTTP response for batch API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"itemId": i} for i in range(100)
        ]  # Return 100 items per batch

        mock_client._session.post.return_value = mock_response

        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_create("Tickets", large_data, batch_size=100)

        # Should process in multiple batches (3 batches of 100, 100, 50 items each)
        assert len(results) == 300  # 3 batches * 100 returned items per batch

    @patch("py_autotask.client.logger")
    def test_batch_progress_logging(
        self, mock_logger, mock_client, sample_entities_data
    ):
        """Test that batch operations log progress."""
        # Mock HTTP response for batch API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"itemId": 12345},
            {"itemId": 12346},
            {"itemId": 12347},
        ]

        mock_client._session.post.return_value = mock_response

        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        client.batch_create("Tickets", sample_entities_data)

        # Verify module-level logger was called for progress
        assert mock_logger.info.called

    def test_batch_error_handling(self, mock_client):
        """Test error handling in batch operations."""
        data = [{"test": "data1"}, {"test": "data2"}]

        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Server Error"
        )

        mock_client._session.post.return_value = mock_response

        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        # Should handle errors gracefully
        with pytest.raises((requests.exceptions.HTTPError, AutotaskAPIError)):
            client.batch_create("Tickets", data)

    def test_batch_empty_dataset(self, mock_client):
        """Test batch operations with empty dataset."""
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_create("Tickets", [])

        assert results == []

    def test_batch_single_item(self, mock_client):
        """Test batch operations with single item."""
        data = [{"test": "single_item"}]

        # Mock HTTP response for batch API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"itemId": 12345}]

        mock_client._session.post.return_value = mock_response

        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.auth = mock_client.auth
        client.config = mock_client.config

        results = client.batch_create("Tickets", data)

        assert len(results) == 1
        assert results[0].item_id == 12345
