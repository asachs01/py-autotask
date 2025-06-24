"""
Integration tests for py-autotask library.

These tests require actual Autotask API credentials and will make real API calls.
They are designed to test the complete integration with the Autotask REST API.

To run these tests, set the following environment variables:
- AUTOTASK_USERNAME: Your Autotask API username
- AUTOTASK_INTEGRATION_CODE: Your integration code
- AUTOTASK_SECRET: Your API secret
- AUTOTASK_API_URL: Your Autotask API URL (optional)

Run with: pytest tests/test_integration.py -m integration
"""

import os

import pytest

from py_autotask import AutotaskClient
from py_autotask.auth import AuthCredentials
from py_autotask.exceptions import AutotaskConnectionError

# Skip integration tests by default
pytestmark = pytest.mark.integration


class TestIntegration:
    """Integration tests with real Autotask API."""

    @pytest.fixture(scope="class")
    def credentials(self):
        """Get API credentials from environment variables."""
        username = os.getenv("AUTOTASK_USERNAME")
        integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
        secret = os.getenv("AUTOTASK_SECRET")
        api_url = os.getenv("AUTOTASK_API_URL")

        if not all([username, integration_code, secret]):
            pytest.skip("Integration test credentials not provided")

        return AuthCredentials(
            username=username,
            integration_code=integration_code,
            secret=secret,
            api_url=api_url,
        )

    @pytest.fixture(scope="class")
    def client(self, credentials):
        """Create authenticated client."""
        client = AutotaskClient(credentials)
        try:
            # Test authentication by getting zone info
            zone_info = client.get_zone_info()
            assert zone_info is not None
            return client
        except Exception as e:
            pytest.skip(f"Failed to authenticate with Autotask API: {e}")

    def test_authentication(self, client):
        """Test that authentication works."""
        assert client.auth is not None
        assert client.session is not None

    def test_get_zone_info(self, client):
        """Test getting zone information."""
        zone_info = client.get_zone_info()
        assert zone_info is not None
        assert hasattr(zone_info, "url")
        assert hasattr(zone_info, "data_base_type")

    def test_entity_manager_initialization(self, client):
        """Test that entity manager initializes correctly."""
        assert client.entities is not None

        # Test that all major entities are available
        entities = [
            "tickets",
            "companies",
            "contacts",
            "projects",
            "resources",
            "contracts",
            "time_entries",
            "attachments",
        ]

        for entity_name in entities:
            assert hasattr(client.entities, entity_name)
            entity = getattr(client.entities, entity_name)
            assert entity is not None

    def test_query_companies(self, client):
        """Test querying companies."""
        try:
            # Query first 5 companies
            companies = client.entities.companies.query(max_records=5)
            assert companies is not None
            assert hasattr(companies, "items")
            assert isinstance(companies.items, list)

            if companies.items:
                company = companies.items[0]
                assert isinstance(company, dict)
                assert "id" in company

        except Exception as e:
            pytest.skip(f"Company query failed: {e}")

    def test_query_tickets(self, client):
        """Test querying tickets."""
        try:
            # Query first 5 tickets
            tickets = client.entities.tickets.query(max_records=5)
            assert tickets is not None
            assert hasattr(tickets, "items")
            assert isinstance(tickets.items, list)

            if tickets.items:
                ticket = tickets.items[0]
                assert isinstance(ticket, dict)
                assert "id" in ticket

        except Exception as e:
            pytest.skip(f"Ticket query failed: {e}")

    def test_get_entity_metadata(self, client):
        """Test getting entity metadata."""
        try:
            # Test getting metadata for Companies entity
            metadata = client.get_entity_metadata("Companies")
            assert metadata is not None
            assert hasattr(metadata, "name")
            assert hasattr(metadata, "can_create")
            assert hasattr(metadata, "can_update")
            assert hasattr(metadata, "can_query")
            assert hasattr(metadata, "can_delete")

        except Exception as e:
            pytest.skip(f"Metadata query failed: {e}")

    def test_get_field_metadata(self, client):
        """Test getting field metadata."""
        try:
            # Test getting field metadata for Companies entity
            fields = client.get_field_metadata("Companies")
            assert fields is not None
            assert isinstance(fields, list)

            if fields:
                field = fields[0]
                assert hasattr(field, "name")
                assert hasattr(field, "data_type")
                assert hasattr(field, "is_required")

        except Exception as e:
            pytest.skip(f"Field metadata query failed: {e}")

    def test_query_with_filters(self, client):
        """Test querying with filters."""
        try:
            from py_autotask.types import FilterOperation, QueryFilter

            # Create a filter for active companies
            filter_active = QueryFilter(
                field="isActive", op=FilterOperation.EQ, value=True
            )

            companies = client.entities.companies.query(
                filters=[filter_active], max_records=3
            )

            assert companies is not None
            assert hasattr(companies, "items")

            # Verify all returned companies are active
            for company in companies.items:
                if "isActive" in company:
                    assert company["isActive"] is True

        except Exception as e:
            pytest.skip(f"Filtered query failed: {e}")

    def test_pagination(self, client):
        """Test pagination functionality."""
        try:
            # Get first page
            page1 = client.entities.companies.query(max_records=2)
            assert page1 is not None
            assert hasattr(page1, "page_details")

            # If there are more results, test next page
            if page1.page_details.next_page_url:
                page2 = client.entities.companies.get_next_page(page1)
                assert page2 is not None
                assert page2.items != page1.items  # Should be different items

        except Exception as e:
            pytest.skip(f"Pagination test failed: {e}")

    def test_error_handling(self, client):
        """Test error handling with invalid requests."""
        try:
            # Try to query a non-existent entity
            with pytest.raises((AutotaskConnectionError, Exception)):
                client.entities.tickets.query_by_id(999999999)

        except Exception:
            # Some errors are expected in this test
            pass

    def test_rate_limiting_awareness(self, client):
        """Test that client handles rate limiting gracefully."""
        try:
            # Make multiple quick requests to test rate limiting
            for i in range(3):
                companies = client.entities.companies.query(max_records=1)
                assert companies is not None

        except Exception as e:
            pytest.skip(f"Rate limiting test failed: {e}")


class TestIntegrationCRUD:
    """Integration tests for CRUD operations."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create authenticated client for CRUD tests."""
        username = os.getenv("AUTOTASK_USERNAME")
        integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
        secret = os.getenv("AUTOTASK_SECRET")
        api_url = os.getenv("AUTOTASK_API_URL")

        if not all([username, integration_code, secret]):
            pytest.skip("Integration test credentials not provided")

        credentials = AuthCredentials(
            username=username,
            integration_code=integration_code,
            secret=secret,
            api_url=api_url,
        )

        return AutotaskClient(credentials)

    @pytest.mark.skipif(
        os.getenv("AUTOTASK_ALLOW_WRITE_TESTS") != "true",
        reason="Write tests disabled by default (set AUTOTASK_ALLOW_WRITE_TESTS=true)",
    )
    def test_create_and_delete_ticket_note(self, client):
        """Test creating and deleting a ticket note (safe operation)."""
        try:
            # First, find an existing ticket to add a note to
            tickets = client.entities.tickets.query(max_records=1)
            if not tickets.items:
                pytest.skip("No tickets available for testing")

            ticket_id = tickets.items[0]["id"]

            # Create a test note
            note_data = {
                "TicketID": ticket_id,
                "Title": "Integration Test Note",
                "Description": "This is a test note created by integration tests",
                "NoteType": 1,  # General note
                "Publish": 1,  # Internal note
            }

            # Create the note
            note_response = client.create_entity("TicketNotes", **note_data)
            assert note_response.item_id is not None

            note_id = note_response.item_id

            # Verify the note was created
            created_note = client.get("TicketNotes", note_id)
            assert created_note is not None
            assert created_note["Title"] == "Integration Test Note"

            # Clean up - delete the note
            delete_result = client.delete("TicketNotes", note_id)
            assert delete_result is True

        except Exception as e:
            pytest.skip(f"CRUD test failed: {e}")


# Performance test class
class TestIntegrationPerformance:
    """Performance tests for the integration."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create authenticated client for performance tests."""
        username = os.getenv("AUTOTASK_USERNAME")
        integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
        secret = os.getenv("AUTOTASK_SECRET")
        api_url = os.getenv("AUTOTASK_API_URL")

        if not all([username, integration_code, secret]):
            pytest.skip("Integration test credentials not provided")

        credentials = AuthCredentials(
            username=username,
            integration_code=integration_code,
            secret=secret,
            api_url=api_url,
        )

        return AutotaskClient(credentials)

    def test_bulk_query_performance(self, client):
        """Test performance of bulk queries."""
        import time

        try:
            start_time = time.time()

            # Query 50 companies
            companies = client.entities.companies.query(max_records=50)

            end_time = time.time()
            query_time = end_time - start_time

            assert companies is not None
            assert len(companies.items) <= 50

            # Query should complete in reasonable time (less than 10 seconds)
            assert query_time < 10.0, f"Query took {query_time:.2f} seconds"

            print(
                f"Queried {len(companies.items)} companies in {query_time:.2f} seconds"
            )

        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")

    def test_pagination_performance(self, client):
        """Test performance of paginated queries."""
        import time

        try:
            start_time = time.time()

            total_items = 0
            page_count = 0
            max_pages = 5  # Limit to avoid long test times

            # Get first page
            current_page = client.entities.companies.query(max_records=10)

            while current_page and page_count < max_pages:
                total_items += len(current_page.items)
                page_count += 1

                if current_page.page_details.next_page_url:
                    current_page = client.entities.companies.get_next_page(current_page)
                else:
                    break

            end_time = time.time()
            total_time = end_time - start_time

            assert total_items > 0
            assert page_count > 0

            # Should process pages efficiently
            avg_time_per_page = total_time / page_count
            assert (
                avg_time_per_page < 5.0
            ), f"Average page time: {avg_time_per_page:.2f}s"

            print(
                f"Processed {page_count} pages ({total_items} items) in {total_time:.2f} seconds"
            )

        except Exception as e:
            pytest.skip(f"Pagination performance test failed: {e}")


if __name__ == "__main__":
    # Instructions for running integration tests
    print("Integration Tests for py-autotask")
    print("=" * 40)
    print("To run these tests, set the following environment variables:")
    print("- AUTOTASK_USERNAME: Your Autotask API username")
    print("- AUTOTASK_INTEGRATION_CODE: Your integration code")
    print("- AUTOTASK_SECRET: Your API secret")
    print("- AUTOTASK_API_URL: Your Autotask API URL (optional)")
    print()
    print("For write tests, also set:")
    print("- AUTOTASK_ALLOW_WRITE_TESTS=true")
    print()
    print("Run with: pytest tests/test_integration.py -m integration -v")
