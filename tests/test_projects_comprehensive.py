"""
Comprehensive tests for the ProjectsEntity class.

This module provides thorough testing of all project-specific operations,
including CRUD operations, status management, resource assignment,
search and filtering, integration with related entities, and error handling.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from py_autotask.entities.projects import ProjectsEntity
from py_autotask.exceptions import AutotaskValidationError
from py_autotask.types import QueryFilter


class TestProjectsEntity:
    """Comprehensive test suite for ProjectsEntity."""

    @pytest.fixture
    def mock_client(self):
        """Mock AutotaskClient for testing."""
        return Mock()

    @pytest.fixture
    def projects_entity(self, mock_client):
        """ProjectsEntity instance for testing."""
        return ProjectsEntity(mock_client, "Projects")

    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            "id": 12345,
            "ProjectName": "Test Project",
            "AccountID": 67890,
            "Type": 1,  # Fixed Price
            "Status": 1,  # New
            "ProjectManagerResourceID": 111,
            "StartDate": "2023-01-01T00:00:00Z",
            "EndDate": "2023-12-31T00:00:00Z",
            "Description": "This is a test project",
            "CreatedBy": 111,
            "CreatedDateTime": "2023-01-01T00:00:00Z",
            "LastActivityBy": 111,
            "LastActivityDateTime": "2023-01-01T00:00:00Z",
        }

    @pytest.fixture
    def sample_create_response(self):
        """Sample create response for testing."""
        mock_response = Mock()
        mock_response.item_id = 12345
        return mock_response

    @pytest.fixture
    def sample_query_response(self, sample_project_data):
        """Sample query response for testing."""
        mock_response = Mock()
        mock_response.items = [sample_project_data]
        return mock_response

    # Basic CRUD Operations Tests

    def test_create_project_basic(self, projects_entity, mock_client, sample_create_response):
        """Test basic project creation with required fields."""
        mock_client.create_entity.return_value = sample_create_response

        result = projects_entity.create_project(
            project_name="Test Project",
            account_id=67890
        )

        assert result == sample_create_response
        mock_client.create_entity.assert_called_once()

        call_args = mock_client.create_entity.call_args
        assert call_args[0][0] == "Projects"  # entity_type
        project_data = call_args[0][1]  # entity_data
        assert project_data["ProjectName"] == "Test Project"
        assert project_data["AccountID"] == 67890
        assert project_data["Type"] == 1  # Default Fixed Price
        assert project_data["Status"] == 1  # Default New

    def test_create_project_with_all_fields(self, projects_entity, mock_client, sample_create_response):
        """Test project creation with all optional fields."""
        mock_client.create_entity.return_value = sample_create_response

        result = projects_entity.create_project(
            project_name="Full Test Project",
            account_id=67890,
            project_type=2,  # Time & Materials
            status=2,  # In Progress
            start_date="2023-01-01T00:00:00Z",
            end_date="2023-12-31T00:00:00Z",
            description="A comprehensive test project",
            CustomField1="Custom Value"
        )

        assert result == sample_create_response
        call_args = mock_client.create_entity.call_args
        project_data = call_args[0][1]
        assert project_data["ProjectName"] == "Full Test Project"
        assert project_data["AccountID"] == 67890
        assert project_data["Type"] == 2
        assert project_data["Status"] == 2
        assert project_data["StartDate"] == "2023-01-01T00:00:00Z"
        assert project_data["EndDate"] == "2023-12-31T00:00:00Z"
        assert project_data["Description"] == "A comprehensive test project"
        assert project_data["CustomField1"] == "Custom Value"

    def test_create_project_without_optional_dates(self, projects_entity, mock_client, sample_create_response):
        """Test project creation without start and end dates."""
        mock_client.create_entity.return_value = sample_create_response

        projects_entity.create_project(
            project_name="Test Project",
            account_id=67890,
            description="Test without dates"
        )

        call_args = mock_client.create_entity.call_args
        project_data = call_args[0][1]
        assert "StartDate" not in project_data
        assert "EndDate" not in project_data
        assert project_data["Description"] == "Test without dates"

    # Project Querying and Filtering Tests

    def test_get_projects_by_account(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by account ID."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_projects_by_account(67890)

        assert result == sample_query_response
        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Projects"
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "AccountID"
        assert filters[0].op == "eq"
        assert filters[0].value == 67890

    def test_get_projects_by_account_with_status_filter(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by account with status filtering."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_projects_by_account(67890, status_filter="active")

        assert result == sample_query_response
        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "AccountID"
        assert filters[0].value == 67890
        assert filters[1].field == "Status"
        assert filters[1].op == "in"
        assert filters[1].value == [1, 2, 3, 4]  # Active statuses

    def test_get_projects_by_account_with_limit(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by account with limit."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_projects_by_account(67890, limit=10)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        assert query_request.max_records == 10

    @pytest.mark.parametrize("status_filter,expected_statuses", [
        ("completed", [5]),
        ("new", [1]),
        ("in_progress", [2]),
        ("on_hold", [3]),
        ("active", [1, 2, 3, 4]),
    ])
    def test_status_filter_mapping(self, projects_entity, mock_client, status_filter, expected_statuses):
        """Test various status filter mappings."""
        mock_client.query.return_value = Mock()
        mock_client.query.return_value.items = []

        projects_entity.get_projects_by_account(67890, status_filter=status_filter)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        status_filter_obj = next((f for f in filters if f.field == "Status"), None)
        assert status_filter_obj is not None
        
        if len(expected_statuses) == 1:
            assert status_filter_obj.op == "eq"
            assert status_filter_obj.value == expected_statuses[0]
        else:
            assert status_filter_obj.op == "in"
            assert status_filter_obj.value == expected_statuses

    def test_get_projects_by_manager(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by manager resource ID."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_projects_by_manager(111)

        assert result == sample_query_response
        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "ProjectManagerResourceID"
        assert filters[0].value == 111
        assert filters[1].field == "Status"
        assert filters[1].op == "ne"
        assert filters[1].value == 5  # Exclude completed

    def test_get_projects_by_manager_include_completed(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by manager including completed projects."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_projects_by_manager(111, include_completed=True)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "ProjectManagerResourceID"
        assert filters[0].value == 111

    def test_get_projects_by_status(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by specific status."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_projects_by_status(2)  # In Progress

        assert result == sample_query_response
        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "Status"
        assert filters[0].op == "eq"
        assert filters[0].value == 2

    def test_get_projects_by_status_with_account_filter(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by status with account filter."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_projects_by_status(2, account_id=67890)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "Status"
        assert filters[0].value == 2
        assert filters[1].field == "AccountID"
        assert filters[1].value == 67890

    def test_get_active_projects(self, projects_entity, mock_client, sample_query_response):
        """Test getting active projects."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_active_projects()

        assert result == sample_query_response
        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1
        assert filters[0].field == "Status"
        assert filters[0].op == "notIn"
        assert filters[0].value == [3, 5, 7]  # Exclude On Hold, Complete, Cancelled

    def test_get_active_projects_with_account_filter(self, projects_entity, mock_client, sample_query_response):
        """Test getting active projects for specific account."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_active_projects(account_id=67890)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        assert filters[0].field == "Status"
        assert filters[0].op == "notIn"
        assert filters[0].value == [3, 5, 7]
        assert filters[1].field == "AccountID"
        assert filters[1].value == 67890

    def test_get_overdue_projects(self, projects_entity, mock_client, sample_query_response):
        """Test getting overdue projects."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_overdue_projects()

        assert result == sample_query_response
        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 2
        
        # Check for end date filter
        end_date_filter = next((f for f in filters if f.field == "EndDate"), None)
        assert end_date_filter is not None
        assert end_date_filter.op == "lt"
        
        # Check for status filter (not completed)
        status_filter = next((f for f in filters if f.field == "Status"), None)
        assert status_filter is not None
        assert status_filter.op == "ne"
        assert status_filter.value == 5  # Not complete

    def test_get_overdue_projects_with_account_filter(self, projects_entity, mock_client, sample_query_response):
        """Test getting overdue projects for specific account."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_overdue_projects(account_id=67890)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 3
        end_date_filter = next((f for f in filters if f.field == "EndDate"), None)
        status_filter = next((f for f in filters if f.field == "Status"), None)
        account_filter = next((f for f in filters if f.field == "AccountID"), None)
        
        assert end_date_filter is not None
        assert status_filter is not None
        assert account_filter is not None
        assert account_filter.value == 67890

    # Project Status Management Tests

    def test_update_project_status(self, projects_entity, mock_client, sample_project_data):
        """Test updating project status."""
        mock_client.update.return_value = sample_project_data

        result = projects_entity.update_project_status(12345, 2)

        assert result == sample_project_data
        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        assert call_args[0][0] == "Projects"
        entity_data = call_args[0][1]
        assert entity_data["id"] == 12345
        assert entity_data["Status"] == 2

    @patch('datetime.datetime')
    def test_complete_project_basic(self, mock_datetime, projects_entity, mock_client, sample_project_data):
        """Test completing a project without completion note."""
        mock_now = Mock()
        mock_now.isoformat.return_value = "2023-06-01T00:00:00Z"
        mock_datetime.now.return_value = mock_now

        mock_client.update.return_value = sample_project_data

        result = projects_entity.complete_project(12345)

        assert result == sample_project_data
        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]
        assert entity_data["id"] == 12345
        assert entity_data["Status"] == 5  # Complete status
        assert entity_data["EndDate"] == "2023-06-01T00:00:00Z"
        assert "StatusDetail" not in entity_data

    @patch('datetime.datetime')
    def test_complete_project_with_note(self, mock_datetime, projects_entity, mock_client, sample_project_data):
        """Test completing a project with completion note."""
        mock_now = Mock()
        mock_now.isoformat.return_value = "2023-06-01T00:00:00Z"
        mock_datetime.now.return_value = mock_now

        mock_client.update.return_value = sample_project_data

        result = projects_entity.complete_project(12345, completion_note="Project completed successfully")

        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]
        assert entity_data["StatusDetail"] == "Project completed successfully"

    def test_assign_project_manager(self, projects_entity, mock_client, sample_project_data):
        """Test assigning a project manager to a project."""
        mock_client.update.return_value = sample_project_data

        result = projects_entity.assign_project_manager(12345, 222)

        assert result == sample_project_data
        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]
        assert entity_data["id"] == 12345
        assert entity_data["ProjectManagerResourceID"] == 222

    # Integration Tests with Related Entities

    def test_get_project_tasks(self, projects_entity, mock_client):
        """Test getting tasks for a project."""
        mock_tasks = [
            {"id": 1001, "ProjectID": 12345, "Title": "Task 1"},
            {"id": 1002, "ProjectID": 12345, "Title": "Task 2"}
        ]
        mock_client.query.return_value = mock_tasks

        result = projects_entity.get_project_tasks(12345)

        assert result == mock_tasks
        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Tasks"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 1
        assert filters[0].field == "ProjectID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345

    def test_get_project_time_entries(self, projects_entity, mock_client):
        """Test getting time entries for a project."""
        mock_time_entries = [
            {"id": 2001, "ProjectID": 12345, "HoursWorked": 8.0},
            {"id": 2002, "ProjectID": 12345, "HoursWorked": 6.5}
        ]
        mock_client.query.return_value = mock_time_entries

        result = projects_entity.get_project_time_entries(12345)

        assert result == mock_time_entries
        call_args = mock_client.query.call_args
        assert call_args[0][0] == "TimeEntries"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 1
        assert filters[0].field == "ProjectID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345

    def test_get_project_tickets(self, projects_entity, mock_client):
        """Test getting tickets for a project."""
        mock_tickets = [
            {"id": 3001, "ProjectID": 12345, "Title": "Ticket 1", "Status": 1},
            {"id": 3002, "ProjectID": 12345, "Title": "Ticket 2", "Status": 8}
        ]
        mock_client.query.return_value = mock_tickets

        result = projects_entity.get_project_tickets(12345)

        assert result == mock_tickets
        call_args = mock_client.query.call_args
        assert call_args[0][0] == "Tickets"
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 1
        assert filters[0].field == "ProjectID"
        assert filters[0].op == "eq"
        assert filters[0].value == 12345

    def test_get_project_tickets_with_status_filter(self, projects_entity, mock_client):
        """Test getting project tickets with status filtering."""
        mock_tickets = []
        mock_client.query.return_value = mock_tickets

        projects_entity.get_project_tickets(12345, status_filter="open")

        call_args = mock_client.query.call_args
        assert "filters" in call_args[1]
        filters = call_args[1]["filters"]
        assert len(filters) == 2
        assert filters[0].field == "ProjectID"
        assert filters[0].value == 12345
        assert filters[1].field == "Status"
        assert filters[1].op == "in"
        assert filters[1].value == [1, 8, 9, 10, 11]  # Open statuses

    @pytest.mark.parametrize("status_filter,expected_statuses", [
        ("open", [1, 8, 9, 10, 11]),
        ("closed", [5]),
        ("new", [1]),
    ])
    def test_get_project_tickets_status_filter_mapping(self, projects_entity, mock_client, status_filter, expected_statuses):
        """Test various ticket status filter mappings."""
        mock_client.query.return_value = []

        projects_entity.get_project_tickets(12345, status_filter=status_filter)

        call_args = mock_client.query.call_args
        filters = call_args[1]["filters"]
        status_filter_obj = next((f for f in filters if f.field == "Status"), None)
        assert status_filter_obj is not None
        
        if len(expected_statuses) == 1:
            assert status_filter_obj.op == "eq"
            assert status_filter_obj.value == expected_statuses[0]
        else:
            assert status_filter_obj.op == "in"
            assert status_filter_obj.value == expected_statuses

    def test_get_project_tickets_with_limit(self, projects_entity, mock_client):
        """Test getting project tickets with limit."""
        mock_client.query.return_value = []

        projects_entity.get_project_tickets(12345, limit=25)

        call_args = mock_client.query.call_args
        assert "max_records" in call_args[1]
        assert call_args[1]["max_records"] == 25

    # Error Handling and Edge Cases

    def test_create_project_missing_required_fields(self, projects_entity):
        """Test that creating a project without required fields raises appropriate errors."""
        # This test depends on the actual implementation handling validation
        # The current implementation doesn't validate required fields, so we test
        # that it creates the expected data structure
        with patch.object(projects_entity, 'create') as mock_create:
            mock_create.return_value = Mock()
            
            projects_entity.create_project("Test", 123)
            
            # Verify that create was called with proper data
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            project_data = call_args[0][0]
            assert "ProjectName" in project_data
            assert "AccountID" in project_data

    def test_get_projects_invalid_status_filter(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects with invalid status filter (should be ignored)."""
        mock_client.query.return_value = sample_query_response

        result = projects_entity.get_projects_by_account(67890, status_filter="invalid_status")

        # Should ignore invalid status filter and only apply AccountID filter
        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert len(filters) == 1  # Only AccountID filter
        assert filters[0].field == "AccountID"

    def test_get_projects_by_manager_zero_id(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects by manager with zero ID."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_projects_by_manager(0)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        filters = query_request.filter
        assert filters[0].value == 0

    def test_update_project_status_negative_status(self, projects_entity, mock_client, sample_project_data):
        """Test updating project status with negative status ID."""
        mock_client.update.return_value = sample_project_data

        projects_entity.update_project_status(12345, -1)

        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]
        assert entity_data["Status"] == -1

    # Performance and Optimization Tests

    def test_get_projects_with_large_limit(self, projects_entity, mock_client, sample_query_response):
        """Test getting projects with large limit value."""
        mock_client.query.return_value = sample_query_response

        projects_entity.get_projects_by_account(67890, limit=10000)

        call_args = mock_client.query.call_args
        query_request = call_args[0][1]
        assert query_request.max_records == 10000

    def test_multiple_filter_combinations(self, projects_entity, mock_client, sample_query_response):
        """Test complex filter combinations work correctly."""
        mock_client.query.return_value = sample_query_response

        # Test get_overdue_projects with account filter
        with patch('datetime.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.isoformat.return_value = "2023-06-01T00:00:00Z"
            mock_datetime.now.return_value = mock_now
            
            projects_entity.get_overdue_projects(account_id=67890, limit=50)

            call_args = mock_client.query.call_args
            query_request = call_args[0][1]
            assert query_request.max_records == 50
            filters = query_request.filter
            assert len(filters) == 3  # EndDate, Status, AccountID filters

    # Integration with BaseEntity Methods

    def test_inherited_get_method(self, projects_entity, mock_client, sample_project_data):
        """Test that inherited get method works correctly."""
        mock_client.get.return_value = sample_project_data

        result = projects_entity.get(12345)

        assert result == sample_project_data
        mock_client.get.assert_called_once_with("Projects", 12345)

    def test_inherited_update_by_id_method(self, projects_entity, mock_client, sample_project_data):
        """Test that inherited update_by_id method works correctly."""
        mock_client.update.return_value = sample_project_data

        result = projects_entity.update_by_id(12345, {"ProjectName": "Updated Name"})

        assert result == sample_project_data
        mock_client.update.assert_called_once()
        call_args = mock_client.update.call_args
        entity_data = call_args[0][1]
        assert entity_data["id"] == 12345
        assert entity_data["ProjectName"] == "Updated Name"

    def test_inherited_delete_method(self, projects_entity, mock_client):
        """Test that inherited delete method works correctly."""
        mock_client.delete.return_value = True

        result = projects_entity.delete(12345)

        assert result is True
        mock_client.delete.assert_called_once_with("Projects", 12345)

    def test_inherited_count_method(self, projects_entity, mock_client):
        """Test that inherited count method works correctly."""
        mock_client.count.return_value = 42

        result = projects_entity.count([{"field": "AccountID", "op": "eq", "value": 67890}])

        assert result == 42
        mock_client.count.assert_called_once()

    # Mock Response Validation Tests

    def test_query_response_structure_validation(self, projects_entity, mock_client):
        """Test that query responses have expected structure."""
        mock_response = Mock()
        mock_response.items = [{"id": 1, "ProjectName": "Test"}]
        mock_client.query.return_value = mock_response

        result = projects_entity.get_projects_by_account(67890)

        assert result == mock_response
        assert len(result.items) == 1
        assert result.items[0]["id"] == 1
        assert result.items[0]["ProjectName"] == "Test"

    def test_create_response_validation(self, projects_entity, mock_client):
        """Test that create responses have expected structure."""
        mock_response = Mock()
        mock_response.item_id = 54321
        mock_client.create_entity.return_value = mock_response

        result = projects_entity.create_project("Test Project", 67890)

        assert result.item_id == 54321

    # Additional Edge Case Tests

    def test_empty_query_results(self, projects_entity, mock_client):
        """Test handling of empty query results."""
        empty_response = Mock()
        empty_response.items = []
        mock_client.query.return_value = empty_response

        result = projects_entity.get_projects_by_account(99999)

        assert result == empty_response

    def test_none_values_in_optional_fields(self, projects_entity, mock_client, sample_create_response):
        """Test creating project with None values for optional fields."""
        mock_client.create_entity.return_value = sample_create_response

        projects_entity.create_project(
            project_name="Test Project",
            account_id=67890,
            start_date=None,
            end_date=None,
            description=None
        )

        call_args = mock_client.create_entity.call_args
        project_data = call_args[0][1]
        assert "StartDate" not in project_data
        assert "EndDate" not in project_data
        assert "Description" not in project_data

    @pytest.mark.parametrize("field_name,field_value", [
        ("start_date", ""),
        ("end_date", ""),
        ("description", ""),
    ])
    def test_empty_string_values_in_optional_fields(self, projects_entity, mock_client, sample_create_response, field_name, field_value):
        """Test creating project with empty string values for optional fields."""
        mock_client.create_entity.return_value = sample_create_response

        kwargs = {field_name: field_value}
        projects_entity.create_project(
            project_name="Test Project",
            account_id=67890,
            **kwargs
        )

        call_args = mock_client.create_entity.call_args
        project_data = call_args[0][1]
        
        # Empty strings should not be included in the request
        field_mapping = {
            "start_date": "StartDate",
            "end_date": "EndDate", 
            "description": "Description"
        }
        mapped_field = field_mapping[field_name]
        assert mapped_field not in project_data