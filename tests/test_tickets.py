"""
Tests for the TicketsEntity class.

This module tests ticket-specific operations and functionality.
"""

from unittest.mock import Mock

import pytest

from py_autotask.entities.tickets import TicketsEntity


class TestTicketsEntity:
    """Test cases for TicketsEntity."""

    @pytest.fixture
    def mock_client(self):
        """Mock AutotaskClient for testing."""
        return Mock()

    @pytest.fixture
    def tickets_entity(self, mock_client):
        """TicketsEntity instance for testing."""
        return TicketsEntity(mock_client, "Tickets")

    @pytest.fixture
    def sample_ticket_data(self):
        """Sample ticket data for testing."""
        return {
            "id": 12345,
            "accountID": 67890,
            "assignedResourceID": 111,
            "title": "Test Ticket",
            "description": "This is a test ticket",
            "status": 1,
            "priority": 2,
            "queueID": 5,
            "ticketType": 1,
            "createDate": "2023-01-01T00:00:00Z",
            "lastActivityDate": "2023-01-01T00:00:00Z",
            "dueDateTime": "2023-01-02T00:00:00Z",
        }

    def test_create_ticket_basic(self, tickets_entity, mock_client):
        """Test basic ticket creation."""
        mock_client.create_entity.return_value = Mock(item_id=12345)

        result = tickets_entity.create_ticket(
            title="Test Ticket", description="Test Description", account_id=67890
        )

        assert result.item_id == 12345
        mock_client.create_entity.assert_called_once()

        call_args = mock_client.create_entity.call_args
        assert call_args[0][0] == "Tickets"  # entity_type
        ticket_data = call_args[0][1]  # entity_data is second positional argument
        assert ticket_data["Title"] == "Test Ticket"
        assert ticket_data["Description"] == "Test Description"
        assert ticket_data["AccountID"] == 67890

    def test_create_ticket_with_optional_fields(self, tickets_entity, mock_client):
        """Test ticket creation with optional fields."""
        mock_client.create_entity.return_value = Mock(item_id=12345)

        _ = tickets_entity.create_ticket(
            title="Test Ticket",
            description="Test Description",
            account_id=67890,
            queue_id=5,
            priority=2,
            status=1,
            ticket_type=1,
        )

        call_args = mock_client.create_entity.call_args
        ticket_data = call_args[0][1]  # entity_data is second positional argument
        assert ticket_data["QueueID"] == 5
        assert ticket_data["Priority"] == 2
        assert ticket_data["Status"] == 1
        assert ticket_data["TicketType"] == 1

    def test_get_tickets_by_account(
        self, tickets_entity, mock_client, sample_ticket_data
    ):
        """Test getting tickets by account."""
        mock_response = Mock()
        mock_response.items = [sample_ticket_data]
        mock_client.query.return_value = mock_response

        result = tickets_entity.get_tickets_by_account(67890)

        assert result == mock_response
        call_args = mock_client.query.call_args
        # get_tickets_by_account calls self.query() which wraps in QueryRequest
        assert call_args[0][0] == "Tickets"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "AccountID"
        assert filters[0].op == "eq"
        assert filters[0].value == 67890

    def test_get_tickets_by_account_with_status_filter(
        self, tickets_entity, mock_client
    ):
        """Test getting tickets by account with status filter."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        tickets_entity.get_tickets_by_account(67890, status_filter="open")

        # Verify both AccountID and Status filters were applied
        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Tickets"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "AccountID"
        assert filters[0].value == 67890
        assert filters[1].field == "Status"
        assert filters[1].op == "in"
        assert filters[1].value == [1, 8, 9, 10, 11]

    def test_get_tickets_by_resource(self, tickets_entity, mock_client):
        """Test getting tickets by resource."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        tickets_entity.get_tickets_by_resource(111, include_completed=False)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Tickets"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "AssignedResourceID"
        assert filters[0].value == 111
        assert filters[1].field == "Status"
        assert filters[1].op == "ne"
        assert filters[1].value == 5  # Not completed

    def test_get_overdue_tickets(self, tickets_entity, mock_client):
        """Test getting overdue tickets."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        # The method imports datetime locally, no need to patch the module
        tickets_entity.get_overdue_tickets()

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Tickets"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        # Check for status filter (not completed)
        status_filter = next((f for f in filters if f.field == "Status"), None)
        assert status_filter is not None
        assert status_filter.op == "ne"
        assert status_filter.value == 5
        # Check for due date filter
        due_filter = next((f for f in filters if f.field == "DueDateTime"), None)
        assert due_filter is not None
        assert due_filter.op == "lt"

    def test_update_ticket_status(self, tickets_entity, mock_client):
        """Test updating ticket status."""
        mock_client.update.return_value = {}

        tickets_entity.update_ticket_status(12345, 2, "Moving to in progress")

        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        assert call_args[0][0] == "Tickets"  # entity_type
        entity_data = call_args[0][1]  # entity_data with id and update fields
        assert entity_data["id"] == 12345
        assert entity_data["Status"] == 2
        assert entity_data["LastActivityBy"] == "Moving to in progress"

    def test_assign_ticket(self, tickets_entity, mock_client):
        """Test assigning ticket to resource."""
        mock_client.update.return_value = {}

        tickets_entity.assign_ticket(12345, 111)

        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]  # entity_data with id and update fields
        assert entity_data["id"] == 12345
        assert entity_data["AssignedResourceID"] == 111

    def test_get_ticket_notes(self, tickets_entity, mock_client):
        """Test getting ticket notes."""
        mock_client.query.return_value = Mock(items=[])

        tickets_entity.get_ticket_notes(12345)

        call_args = mock_client.query.call_args
        assert call_args[0][0] == "TicketNotes"
        # get_ticket_notes calls client.query directly with filters=filters
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 1
        assert filters[0].field == "TicketID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345

    def test_add_ticket_note(self, tickets_entity, mock_client):
        """Test adding ticket note."""
        mock_client.create_entity.return_value = Mock(item_id=98765)

        _ = tickets_entity.add_ticket_note(
            12345, "This is a test note", note_type=1, title="Test Note"
        )

        mock_client.create_entity.assert_called_once()
        call_args = mock_client.create_entity.call_args
        assert call_args[0][0] == "TicketNotes"  # entity_type
        note_data = call_args[0][1]  # entity_data is second positional argument
        assert note_data["TicketID"] == 12345
        assert note_data["Description"] == "This is a test note"
        assert note_data["NoteType"] == 1
        assert note_data["Title"] == "Test Note"

    def test_get_tickets_by_queue(self, tickets_entity, mock_client):
        """Test getting tickets by queue."""
        mock_response = Mock()
        mock_response.items = []
        mock_client.query.return_value = mock_response

        tickets_entity.get_tickets_by_queue(5, status_filter="open")

        call_args = mock_client.query.call_args
        # get_tickets_by_queue calls self.query() which wraps in QueryRequest
        assert call_args[0][0] == "Tickets"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "QueueID"
        assert filters[0].value == 5
