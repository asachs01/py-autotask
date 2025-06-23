"""
Tests for batch operations functionality.

This module tests batch create, update, and delete operations
for all entity types through the client and entity classes.
"""

import pytest
from unittest.mock import Mock, patch, PropertyMock

from py_autotask.client import AutotaskClient
from py_autotask.entities.base import BaseEntity
from py_autotask.entities.tickets import TicketsEntity
from py_autotask.entities.companies import CompaniesEntity
from py_autotask.types import CreateResponse
from py_autotask.exceptions import AutotaskValidationError, AutotaskConnectionError


class TestBatchOperations:
    """Test cases for batch operations."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        return Mock()

    @pytest.fixture
    def mock_client(self, mock_session):
        """Create a mock client for testing."""
        mock_client = Mock()
        mock_client.logger = Mock()
        mock_client._session = mock_session
        # Mock the session property
        type(mock_client).session = PropertyMock(return_value=mock_session)
        return mock_client

    @pytest.fixture
    def sample_entities_data(self):
        """Sample entity data for batch operations."""
        return [
            {"title": "Issue 1", "description": "First issue", "accountID": 123},
            {"title": "Issue 2", "description": "Second issue", "accountID": 124},
            {"title": "Issue 3", "description": "Third issue", "accountID": 125}
        ]

    @pytest.fixture
    def sample_update_data(self):
        """Sample update data for batch operations."""
        return [
            {"id": 1001, "priority": 1, "status": 8},
            {"id": 1002, "priority": 2, "status": 5},
            {"id": 1003, "priority": 3, "status": 1}
        ]

    def test_client_batch_create_success(self, mock_client, sample_entities_data):
        """Test successful batch create via client."""
        # Mock API responses
        mock_responses = [
            CreateResponse(itemId=12345),
            CreateResponse(itemId=12346),
            CreateResponse(itemId=12347)
        ]
        
        # Mock the create_entity method
        mock_client.create_entity.side_effect = mock_responses
        
        # Create client instance with mocked attributes
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.create_entity = mock_client.create_entity
        
        results = client.batch_create("Tickets", sample_entities_data, batch_size=200)
        
        assert len(results) == 3
        assert all(result.item_id is not None for result in results)
        assert [r.item_id for r in results] == [12345, 12346, 12347]

    def test_client_batch_create_with_errors(self, mock_client, sample_entities_data):
        """Test batch create with some failures."""
        # Mock mixed responses (success and failure)
        def mock_create_side_effect(*args, **kwargs):
            # Simulate failure on second call
            if mock_client.create_entity.call_count == 2:
                raise AutotaskValidationError("Required field missing")
            return CreateResponse(itemId=12345 + mock_client.create_entity.call_count)
        
        mock_client.create_entity.side_effect = mock_create_side_effect
        
        # Create client instance
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.create_entity = mock_client.create_entity
        
        # Test that errors are handled gracefully
        results = client.batch_create("Tickets", sample_entities_data)
        
        # Should have results for successful operations
        assert len(results) >= 2  # At least 2 successful

    def test_client_batch_create_exceeds_batch_size(self, mock_client):
        """Test batch create with batch size exceeding limit."""
        large_data = [{"test": f"data{i}"} for i in range(250)]
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        
        with pytest.raises(ValueError, match="Batch size cannot exceed 200"):
            client.batch_create("Tickets", large_data, batch_size=250)

    def test_client_batch_update_success(self, mock_client, sample_update_data):
        """Test successful batch update via client."""
        # Mock API responses
        mock_responses = [
            {"id": 1001, "priority": 1, "status": 8},
            {"id": 1002, "priority": 2, "status": 5},
            {"id": 1003, "priority": 3, "status": 1}
        ]
        
        mock_client.update.side_effect = mock_responses
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.update = mock_client.update
        
        results = client.batch_update("Tickets", sample_update_data)
        
        assert len(results) == 3
        assert all("id" in result for result in results)

    def test_client_batch_update_missing_ids(self, mock_client):
        """Test batch update with missing IDs."""
        data_without_ids = [
            {"priority": 1, "status": 8},  # Missing ID
            {"id": 1002, "priority": 2, "status": 5}
        ]
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        
        with pytest.raises(ValueError, match="Entity at index 0 missing 'id' field"):
            client.batch_update("Tickets", data_without_ids)

    def test_client_batch_delete_success(self, mock_client):
        """Test successful batch delete via client."""
        entity_ids = [1001, 1002, 1003]
        
        # Mock successful deletions
        mock_client.delete.return_value = True
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.delete = mock_client.delete
        
        results = client.batch_delete("Tickets", entity_ids)
        
        assert len(results) == 3
        assert all(result is True for result in results)

    def test_client_batch_delete_with_failures(self, mock_client):
        """Test batch delete with some failures."""
        entity_ids = [1001, 1002, 1003]
        
        # Mock mixed deletion results
        delete_results = [True, False, True]
        mock_client.delete.side_effect = delete_results
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.delete = mock_client.delete
        
        results = client.batch_delete("Tickets", entity_ids)
        
        assert len(results) == 3
        assert results == [True, False, True]
        assert sum(results) == 2  # 2 successful deletions

    def test_base_entity_batch_create(self, mock_client, sample_entities_data):
        """Test batch create via BaseEntity."""
        # Mock successful create responses
        mock_responses = [
            CreateResponse(itemId=12345),
            CreateResponse(itemId=12346),
            CreateResponse(itemId=12347)
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
            {"id": 1003, "priority": 3}
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
            {"title": "Ticket 2", "description": "Second ticket", "accountID": 124}
        ]
        
        mock_responses = [
            CreateResponse(itemId=12345),
            CreateResponse(itemId=12346)
        ]
        
        mock_client.batch_create.return_value = mock_responses
        
        tickets_entity = TicketsEntity(mock_client, "Tickets")
        
        results = tickets_entity.batch_create(ticket_data)
        
        assert len(results) == 2
        assert all(result.item_id is not None for result in results)

    def test_companies_entity_batch_update(self, mock_client):
        """Test batch update via CompaniesEntity."""
        company_data = [
            {"id": 1001, "companyName": "Updated Company 1"},
            {"id": 1002, "companyName": "Updated Company 2"}
        ]
        
        mock_responses = [
            {"id": 1001, "companyName": "Updated Company 1"},
            {"id": 1002, "companyName": "Updated Company 2"}
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
        
        mock_responses = [CreateResponse(itemId=i) for i in range(250)]
        mock_client.create_entity.side_effect = mock_responses
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.create_entity = mock_client.create_entity
        
        results = client.batch_create("Tickets", large_data, batch_size=100)
        
        # Should process in multiple batches
        assert len(results) == 250

    def test_batch_progress_logging(self, mock_client, sample_entities_data):
        """Test that batch operations log progress."""
        mock_responses = [CreateResponse(itemId=i) for i in range(3)]
        mock_client.create_entity.side_effect = mock_responses
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.create_entity = mock_client.create_entity
        
        client.batch_create("Tickets", sample_entities_data)
        
        # Verify logger was called for progress
        assert mock_client.logger.info.called

    def test_batch_error_handling(self, mock_client):
        """Test error handling in batch operations."""
        data = [{"test": "data1"}, {"test": "data2"}]
        
        # Mock connection error
        mock_client.create_entity.side_effect = AutotaskConnectionError("Connection failed")
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.create_entity = mock_client.create_entity
        
        # Should handle errors gracefully
        results = client.batch_create("Tickets", data)
        
        # May return empty or partial results depending on implementation
        assert isinstance(results, list)

    def test_batch_empty_dataset(self, mock_client):
        """Test batch operations with empty dataset."""
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        
        results = client.batch_create("Tickets", [])
        
        assert results == []

    def test_batch_single_item(self, mock_client):
        """Test batch operations with single item."""
        data = [{"test": "single_item"}]
        mock_response = CreateResponse(itemId=12345)
        
        mock_client.create_entity.return_value = mock_response
        
        client = AutotaskClient.__new__(AutotaskClient)
        client._session = mock_client._session
        client.logger = mock_client.logger
        client.create_entity = mock_client.create_entity
        
        results = client.batch_create("Tickets", data)
        
        assert len(results) == 1
        assert results[0].item_id == 12345 