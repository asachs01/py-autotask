"""
Tests for Ticket Note Attachments entity functionality.

This module tests file upload, download, and management operations
for Autotask ticket note attachments.
"""

from unittest.mock import MagicMock, Mock

import pytest

from py_autotask.entities.ticket_note_attachments import TicketNoteAttachmentsEntity


class TestTicketNoteAttachmentsEntity:
    """Test cases for TicketNoteAttachmentsEntity."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        mock_client = Mock()
        mock_client.auth = Mock()
        mock_client.auth.api_url = "https://api.autotask.net"
        mock_client.session = Mock()
        mock_client.config = Mock()
        mock_client.config.timeout = 30
        mock_client.logger = Mock()
        return mock_client

    @pytest.fixture
    def ticket_note_attachments_entity(self, mock_client):
        """Create TicketNoteAttachmentsEntity instance for testing."""
        return TicketNoteAttachmentsEntity(mock_client, "TicketNoteAttachments")

    @pytest.fixture
    def sample_attachment_response(self):
        """Sample attachment response data for testing."""
        return {
            "id": 12345,
            "ticketNoteID": 31983263,
            "title": "Test Attachment",
            "fullPath": "test.pdf",
            "contentType": "application/pdf",
            "attachDate": "2023-01-01T00:00:00Z",
            "attachmentType": "FILE_ATTACHMENT",
            "publish": 1,
        }

    def test_create_note_attachment_success(
        self, ticket_note_attachments_entity, mock_client, sample_attachment_response
    ):
        """Test successful attachment creation."""
        # Mock the create method
        ticket_note_attachments_entity.create = Mock(
            return_value=sample_attachment_response
        )

        result = ticket_note_attachments_entity.create_note_attachment(
            note_id=31983263,
            attachment_data="VGVzdCBjb250ZW50",  # base64 encoded
            file_name="test.pdf",
            content_type="application/pdf",
            title="Test Attachment",
            attachmentType="FILE_ATTACHMENT",
            publish=1,
        )

        assert result["id"] == 12345
        assert result["ticketNoteID"] == 31983263
        ticket_note_attachments_entity.create.assert_called_once()

        # Verify the payload structure
        call_args = ticket_note_attachments_entity.create.call_args[0][0]
        assert call_args["TicketNoteID"] == 31983263
        assert call_args["Data"] == "VGVzdCBjb250ZW50"
        assert call_args["FullPath"] == "test.pdf"
        assert call_args["ContentType"] == "application/pdf"
        assert call_args["Title"] == "Test Attachment"

    def test_create_note_attachment_with_attach_date(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test attachment creation with attach_date."""
        ticket_note_attachments_entity.create = Mock(
            return_value=sample_attachment_response
        )

        ticket_note_attachments_entity.create_note_attachment(
            note_id=31983263,
            attachment_data="VGVzdA==",
            file_name="test.txt",
            content_type="text/plain",
            attach_date="2023-06-15T10:30:00Z",
        )

        call_args = ticket_note_attachments_entity.create.call_args[0][0]
        assert call_args["AttachDate"] == "2023-06-15T10:30:00Z"

    def test_get_note_attachments(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test getting attachments for a ticket note."""
        # Mock query response
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_note_attachments(note_id=31983263)

        assert len(result) == 1
        assert result[0]["id"] == 12345
        ticket_note_attachments_entity.query.assert_called_once()

        # Verify filter was applied correctly
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert len(filters) == 1
        assert filters[0].field == "TicketNoteID"
        assert filters[0].op == "eq"
        assert filters[0].value == 31983263

    def test_get_ticket_note_attachments(
        self, ticket_note_attachments_entity, mock_client, sample_attachment_response
    ):
        """Test getting all note attachments for a ticket."""
        # Mock the client.query for ticket notes
        mock_client.query = Mock(
            return_value={
                "items": [
                    {"id": 31983263},
                    {"id": 31983264},
                ]
            }
        )

        # Mock query response for attachments
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_ticket_note_attachments(
            ticket_id=272164
        )

        assert len(result) == 1
        mock_client.query.assert_called_once()

    def test_get_ticket_note_attachments_no_notes(
        self, ticket_note_attachments_entity, mock_client
    ):
        """Test getting attachments when ticket has no notes."""
        mock_client.query = Mock(return_value={"items": []})

        result = ticket_note_attachments_entity.get_ticket_note_attachments(
            ticket_id=272164
        )

        assert result == []

    def test_get_attachments_by_type(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test filtering attachments by content type."""
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_attachments_by_type(
            note_id=31983263, content_type="application/pdf"
        )

        assert len(result) == 1
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert len(filters) == 2
        assert filters[1].field == "ContentType"
        assert filters[1].value == "application/pdf"

    def test_get_attachments_by_title_exact_match(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test searching attachments by exact title."""
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_attachments_by_title(
            note_id=31983263, title="Test Attachment", exact_match=True
        )

        assert len(result) == 1
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert filters[1].op == "eq"

    def test_get_attachments_by_title_partial_match(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test searching attachments by partial title."""
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_attachments_by_title(
            note_id=31983263, title="Test", exact_match=False
        )

        assert len(result) == 1
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert filters[1].op == "contains"

    def test_get_attachment_data(self, ticket_note_attachments_entity):
        """Test downloading attachment binary data."""
        ticket_note_attachments_entity.get = Mock(
            return_value={"id": 12345, "Data": b"test binary content"}
        )

        result = ticket_note_attachments_entity.get_attachment_data(attachment_id=12345)

        assert result == b"test binary content"
        ticket_note_attachments_entity.get.assert_called_once_with(12345)

    def test_get_attachment_data_not_found(self, ticket_note_attachments_entity):
        """Test downloading attachment when not found."""
        ticket_note_attachments_entity.get = Mock(return_value=None)

        with pytest.raises(ValueError, match="Attachment with ID 12345 not found"):
            ticket_note_attachments_entity.get_attachment_data(attachment_id=12345)

    def test_update_attachment_title(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test updating attachment title."""
        updated_response = sample_attachment_response.copy()
        updated_response["title"] = "New Title"
        ticket_note_attachments_entity.update_by_id = Mock(
            return_value=updated_response
        )

        result = ticket_note_attachments_entity.update_attachment_title(
            attachment_id=12345, new_title="New Title"
        )

        assert result["title"] == "New Title"
        ticket_note_attachments_entity.update_by_id.assert_called_once_with(
            12345, {"Title": "New Title"}
        )

    def test_get_attachments_by_date_range(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test filtering attachments by date range."""
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_attachments_by_date_range(
            note_id=31983263,
            start_date="2023-01-01",
            end_date="2023-12-31",
        )

        assert len(result) == 1
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert len(filters) == 3
        assert filters[1].field == "AttachDate"
        assert filters[1].op == "gte"
        assert filters[2].field == "AttachDate"
        assert filters[2].op == "lte"

    def test_get_image_attachments(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test getting image attachments only."""
        image_attachment = sample_attachment_response.copy()
        image_attachment["contentType"] = "image/png"
        mock_response = MagicMock()
        mock_response.items = [image_attachment]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_image_attachments(note_id=31983263)

        assert len(result) == 1
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert filters[1].field == "ContentType"
        assert filters[1].op == "beginsWith"
        assert filters[1].value == "image/"

    def test_get_document_attachments(
        self, ticket_note_attachments_entity, sample_attachment_response
    ):
        """Test getting document attachments only."""
        mock_response = MagicMock()
        mock_response.items = [sample_attachment_response]
        ticket_note_attachments_entity.query = Mock(return_value=mock_response)

        result = ticket_note_attachments_entity.get_document_attachments(
            note_id=31983263
        )

        assert len(result) == 1
        call_kwargs = ticket_note_attachments_entity.query.call_args[1]
        filters = call_kwargs["filters"]
        assert filters[1].field == "ContentType"
        assert filters[1].op == "in"

    def test_bulk_delete_attachments(self, ticket_note_attachments_entity):
        """Test bulk deletion of attachments."""
        ticket_note_attachments_entity.batch_delete = Mock(
            return_value=[True, True, False]
        )

        result = ticket_note_attachments_entity.bulk_delete_attachments(
            attachment_ids=[12345, 12346, 12347]
        )

        assert result == [True, True, False]
        ticket_note_attachments_entity.batch_delete.assert_called_once_with(
            [12345, 12346, 12347]
        )
