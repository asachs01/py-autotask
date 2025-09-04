"""
Comprehensive test suite for TimeEntriesEntity.

This test suite covers all aspects of the time entries functionality:
- CRUD operations
- Time tracking and management
- Billing and invoicing
- Approval workflows
- Integration with tickets, tasks, and projects
- Bulk operations
- Time sheet generation
- Overtime and holiday tracking
- Advanced search and filtering
- Analytics and reporting
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from py_autotask.constants import (
    TimeEntryConstants,
    TimeEntryStatus,
    TimeEntryType,
)
from py_autotask.entities.time_entries import TimeEntriesEntity


class TestTimeEntriesEntity:
    """Comprehensive test class for TimeEntriesEntity."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Autotask client."""
        client = Mock()
        return client

    @pytest.fixture
    def time_entries_entity(self, mock_client):
        """Create TimeEntriesEntity instance with mock client."""
        return TimeEntriesEntity(mock_client)

    @pytest.fixture
    def sample_time_entry(self):
        """Sample time entry data for testing."""
        return {
            "id": 12345,
            "ResourceID": 101,
            "DateWorked": "2023-12-01",
            "HoursWorked": 8.0,
            "TicketID": 5001,
            "ProjectID": 2001,
            "TaskID": 3001,
            "BillableToAccount": True,
            "Status": TimeEntryStatus.DRAFT,
            "Type": TimeEntryType.REGULAR,
            "Description": "Development work on feature X",
            "InternalNotes": "Working on bug fixes",
            "SummaryNotes": "Feature development",
        }

    # =============================================================================
    # CRUD Operations Tests
    # =============================================================================

    def test_create_time_entry_basic(self, time_entries_entity, sample_time_entry):
        """Test basic time entry creation."""
        time_entries_entity.create = Mock(return_value=sample_time_entry)

        result = time_entries_entity.create_time_entry(
            resource_id=101,
            date_worked="2023-12-01",
            hours_worked=8.0,
            ticket_id=5001,
            description="Development work",
        )

        assert result == sample_time_entry
        time_entries_entity.create.assert_called_once()

    def test_create_time_entry_comprehensive(
        self, time_entries_entity, sample_time_entry
    ):
        """Test comprehensive time entry creation with all fields."""
        time_entries_entity.create = Mock(return_value=sample_time_entry)

        result = time_entries_entity.create_time_entry(
            resource_id=101,
            date_worked="2023-12-01",
            hours_worked=8.0,
            ticket_id=5001,
            project_id=2001,
            task_id=3001,
            account_id=1001,
            role_id=201,
            billing_code_id=301,
            entry_type=TimeEntryType.REGULAR,
            billable=True,
            description="Development work",
            internal_notes="Bug fixes",
            summary_notes="Feature work",
        )

        assert result == sample_time_entry
        time_entries_entity.create.assert_called_once()

    def test_create_time_entry_validation_hours_too_low(self, time_entries_entity):
        """Test time entry creation with invalid hours (too low)."""
        with pytest.raises(ValueError, match="Hours must be at least"):
            time_entries_entity.create_time_entry(
                resource_id=101,
                date_worked="2023-12-01",
                hours_worked=0.0,  # Invalid: below minimum
                ticket_id=5001,
            )

    def test_create_time_entry_validation_hours_too_high(self, time_entries_entity):
        """Test time entry creation with invalid hours (too high)."""
        with pytest.raises(ValueError, match="Hours cannot exceed"):
            time_entries_entity.create_time_entry(
                resource_id=101,
                date_worked="2023-12-01",
                hours_worked=25.0,  # Invalid: above maximum
                ticket_id=5001,
            )

    def test_create_time_entry_validation_no_associations(self, time_entries_entity):
        """Test time entry creation with no work associations."""
        with pytest.raises(ValueError, match="Time entry must be associated"):
            time_entries_entity.create_time_entry(
                resource_id=101,
                date_worked="2023-12-01",
                hours_worked=8.0,
                # No ticket_id, project_id, or task_id
            )

    def test_update_time_entry(self, time_entries_entity, sample_time_entry):
        """Test time entry update."""
        updated_entry = {**sample_time_entry, "HoursWorked": 6.5}
        time_entries_entity.update_by_id = Mock(return_value=updated_entry)

        result = time_entries_entity.update_time_entry(
            time_entry_id=12345,
            hours_worked=6.5,
            description="Updated description",
        )

        assert result == updated_entry
        time_entries_entity.update_by_id.assert_called_once()

    def test_update_time_entry_no_fields(self, time_entries_entity):
        """Test update with no fields provided."""
        with pytest.raises(ValueError, match="No fields provided to update"):
            time_entries_entity.update_time_entry(time_entry_id=12345)

    def test_get_time_entry(self, time_entries_entity, sample_time_entry):
        """Test getting a single time entry."""
        time_entries_entity.get = Mock(return_value=sample_time_entry)

        result = time_entries_entity.get_time_entry(12345)

        assert result == sample_time_entry
        time_entries_entity.get.assert_called_once_with(12345)

    def test_delete_time_entry_success(self, time_entries_entity):
        """Test successful time entry deletion."""
        time_entries_entity.delete = Mock(return_value=True)

        result = time_entries_entity.delete_time_entry(12345)

        assert result is True
        time_entries_entity.delete.assert_called_once_with(12345)

    def test_delete_time_entry_failure(self, time_entries_entity):
        """Test time entry deletion failure."""
        time_entries_entity.delete = Mock(side_effect=Exception("Cannot delete"))

        result = time_entries_entity.delete_time_entry(12345)

        assert result is False

    # =============================================================================
    # Query and Search Operations Tests
    # =============================================================================

    def test_get_time_entries_by_resource(self, time_entries_entity, sample_time_entry):
        """Test getting time entries by resource."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.get_time_entries_by_resource(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
        )

        assert result == [sample_time_entry]
        time_entries_entity.query.assert_called_once()

    def test_get_time_entries_by_resource_with_status_filter(self, time_entries_entity):
        """Test getting time entries with status filter."""
        time_entries_entity.query = Mock(return_value=[])

        with patch(
            "py_autotask.entities.time_entries.validate_status_filter"
        ) as mock_validate:
            mock_validate.return_value = [TimeEntryStatus.APPROVED]

            time_entries_entity.get_time_entries_by_resource(
                resource_id=101,
                status_filter="approved",
            )

            mock_validate.assert_called_once_with(TimeEntryConstants, "approved")

    def test_get_time_entries_by_ticket(self, time_entries_entity, sample_time_entry):
        """Test getting time entries by ticket."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.get_time_entries_by_ticket(
            ticket_id=5001,
            resource_id=101,
        )

        assert result == [sample_time_entry]

    def test_get_time_entries_by_project(self, time_entries_entity, sample_time_entry):
        """Test getting time entries by project."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.get_time_entries_by_project(
            project_id=2001,
            resource_id=101,
            billable_only=True,
        )

        assert result == [sample_time_entry]

    def test_get_billable_time_entries(self, time_entries_entity, sample_time_entry):
        """Test getting billable time entries."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.get_billable_time_entries(
            resource_id=101,
            unbilled_only=True,
        )

        assert result == [sample_time_entry]

    def test_search_time_entries(self, time_entries_entity, sample_time_entry):
        """Test searching time entries by text."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.search_time_entries(
            search_text="development",
            resource_id=101,
        )

        assert result == [sample_time_entry]

    # =============================================================================
    # Time Tracking and Management Tests
    # =============================================================================

    def test_start_time_tracking(self, time_entries_entity, sample_time_entry):
        """Test starting time tracking session."""
        time_entries_entity.create = Mock(return_value=sample_time_entry)

        with patch("py_autotask.entities.time_entries.datetime") as mock_datetime:
            mock_now = Mock()
            mock_now.strftime.return_value = "2023-12-01"
            mock_now.isoformat.return_value = "2023-12-01T09:00:00"
            mock_datetime.now.return_value = mock_now

            result = time_entries_entity.start_time_tracking(
                resource_id=101,
                ticket_id=5001,
                description="Working on feature X",
            )

            assert result["resource_id"] == 101
            assert result["status"] == "running"
            assert result["ticket_id"] == 5001

    def test_stop_time_tracking(self, time_entries_entity, sample_time_entry):
        """Test stopping time tracking session."""
        # Mock the current entry with start time
        entry_with_start = {
            **sample_time_entry,
            "StartDateTime": "2023-12-01T09:00:00",
        }
        time_entries_entity.get_time_entry = Mock(return_value=entry_with_start)
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        with patch("py_autotask.entities.time_entries.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 12, 1, 17, 0, 0)
            mock_datetime.fromisoformat.return_value = datetime(2023, 12, 1, 9, 0, 0)

            result = time_entries_entity.stop_time_tracking(
                time_entry_id=12345,
                description="Completed feature X",
            )

            assert result == sample_time_entry
            time_entries_entity.update_time_entry.assert_called_once()

    def test_stop_time_tracking_no_entry(self, time_entries_entity):
        """Test stopping time tracking with non-existent entry."""
        time_entries_entity.get_time_entry = Mock(return_value=None)

        with pytest.raises(ValueError, match="Time entry .* not found"):
            time_entries_entity.stop_time_tracking(time_entry_id=99999)

    def test_stop_time_tracking_no_start_time(
        self, time_entries_entity, sample_time_entry
    ):
        """Test stopping time tracking without start time."""
        time_entries_entity.get_time_entry = Mock(return_value=sample_time_entry)

        with pytest.raises(ValueError, match="Time entry does not have a start time"):
            time_entries_entity.stop_time_tracking(time_entry_id=12345)

    def test_calculate_duration(self, time_entries_entity):
        """Test duration calculation between times."""
        result = time_entries_entity.calculate_duration(
            "2023-12-01T09:00:00", "2023-12-01T17:00:00"
        )

        assert result == 8.0

    def test_round_hours_default_increment(self, time_entries_entity):
        """Test hours rounding with default increment."""
        result = time_entries_entity.round_hours(7.83)
        assert result == 7.75  # Rounded to nearest 0.25

    def test_round_hours_custom_increment(self, time_entries_entity):
        """Test hours rounding with custom increment."""
        result = time_entries_entity.round_hours(7.83, increment=0.5)
        assert result == 8.0  # Rounded to nearest 0.5

    # =============================================================================
    # Approval Workflow Tests
    # =============================================================================

    def test_submit_for_approval_single(self, time_entries_entity, sample_time_entry):
        """Test submitting a single time entry for approval."""
        time_entries_entity.get_time_entry = Mock(return_value=sample_time_entry)
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        result = time_entries_entity.submit_for_approval(
            time_entry_ids=12345,
            submission_notes="Ready for review",
        )

        assert len(result) == 1
        time_entries_entity.update_time_entry.assert_called_once()

    def test_submit_for_approval_multiple(self, time_entries_entity, sample_time_entry):
        """Test submitting multiple time entries for approval."""
        time_entries_entity.get_time_entry = Mock(return_value=sample_time_entry)
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        result = time_entries_entity.submit_for_approval(
            time_entry_ids=[12345, 12346, 12347],
            submission_notes="Weekly submission",
        )

        assert len(result) == 3
        assert time_entries_entity.update_time_entry.call_count == 3

    def test_approve_time_entries(self, time_entries_entity, sample_time_entry):
        """Test approving time entries."""
        time_entries_entity.get_time_entry = Mock(return_value=sample_time_entry)
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        result = time_entries_entity.approve_time_entries(
            time_entry_ids=[12345],
            approver_resource_id=201,
            approval_notes="Approved for billing",
        )

        assert len(result) == 1
        time_entries_entity.update_time_entry.assert_called_once()

    def test_reject_time_entries(self, time_entries_entity, sample_time_entry):
        """Test rejecting time entries."""
        time_entries_entity.get_time_entry = Mock(return_value=sample_time_entry)
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        result = time_entries_entity.reject_time_entries(
            time_entry_ids=[12345],
            rejection_reason="Insufficient detail",
            rejector_resource_id=201,
        )

        assert len(result) == 1
        time_entries_entity.update_time_entry.assert_called_once()

    def test_get_pending_approvals(self, time_entries_entity, sample_time_entry):
        """Test getting pending approvals."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.get_pending_approvals(
            start_date="2023-12-01",
            end_date="2023-12-07",
        )

        assert result == [sample_time_entry]

    # =============================================================================
    # Bulk Operations Tests
    # =============================================================================

    def test_bulk_create_time_entries(self, time_entries_entity, sample_time_entry):
        """Test bulk creation of time entries."""
        time_entries_entity.create = Mock(return_value=sample_time_entry)

        entries_data = [
            {
                "ResourceID": 101,
                "DateWorked": "2023-12-01",
                "HoursWorked": 8.0,
                "TicketID": 5001,
            },
            {
                "ResourceID": 102,
                "DateWorked": "2023-12-01",
                "HoursWorked": 6.0,
                "ProjectID": 2001,
            },
        ]

        result = time_entries_entity.bulk_create_time_entries(entries_data)

        assert len(result) == 2
        assert time_entries_entity.create.call_count == 2

    def test_bulk_create_time_entries_with_errors(
        self, time_entries_entity, sample_time_entry
    ):
        """Test bulk creation with some entries failing."""

        def create_side_effect(data):
            if data.get("ResourceID") == 102:
                raise Exception("Resource not found")
            return sample_time_entry

        time_entries_entity.create = Mock(side_effect=create_side_effect)

        entries_data = [
            {
                "ResourceID": 101,
                "DateWorked": "2023-12-01",
                "HoursWorked": 8.0,
                "TicketID": 5001,
            },
            {
                "ResourceID": 102,  # This will fail
                "DateWorked": "2023-12-01",
                "HoursWorked": 6.0,
                "ProjectID": 2001,
            },
        ]

        result = time_entries_entity.bulk_create_time_entries(entries_data)

        assert len(result) == 1  # Only one succeeded

    def test_bulk_update_time_entries(self, time_entries_entity, sample_time_entry):
        """Test bulk update of time entries."""
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        updates = [
            {"id": 12345, "hours_worked": 7.5},
            {"id": 12346, "description": "Updated description"},
        ]

        result = time_entries_entity.bulk_update_time_entries(updates)

        assert len(result) == 2
        assert time_entries_entity.update_time_entry.call_count == 2

    def test_bulk_submit_for_approval(self, time_entries_entity, sample_time_entry):
        """Test bulk submission for approval."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])
        time_entries_entity.submit_for_approval = Mock(return_value=[sample_time_entry])

        result = time_entries_entity.bulk_submit_for_approval(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
        )

        assert result == [sample_time_entry]

    def test_bulk_delete_time_entries(self, time_entries_entity):
        """Test bulk deletion of time entries."""
        time_entries_entity.delete_time_entry = Mock(return_value=True)

        result = time_entries_entity.bulk_delete_time_entries([12345, 12346, 12347])

        assert result["deleted_count"] == 3
        assert result["failed_count"] == 0
        assert time_entries_entity.delete_time_entry.call_count == 3

    def test_bulk_delete_time_entries_with_failures(self, time_entries_entity):
        """Test bulk deletion with some failures."""

        def delete_side_effect(entry_id):
            return entry_id != 12346  # 12346 will fail

        time_entries_entity.delete_time_entry = Mock(side_effect=delete_side_effect)

        result = time_entries_entity.bulk_delete_time_entries([12345, 12346, 12347])

        assert result["deleted_count"] == 2
        assert result["failed_count"] == 1

    # =============================================================================
    # Time Sheet Operations Tests
    # =============================================================================

    def test_get_time_sheet(self, time_entries_entity, sample_time_entry):
        """Test getting time sheet for a week."""
        # Mock multiple entries for different days
        entries = [
            {**sample_time_entry, "DateWorked": "2023-12-01", "HoursWorked": 8.0},
            {**sample_time_entry, "DateWorked": "2023-12-02", "HoursWorked": 6.0},
            {**sample_time_entry, "DateWorked": "2023-12-03", "HoursWorked": 7.5},
        ]
        time_entries_entity.query = Mock(return_value=entries)

        result = time_entries_entity.get_time_sheet(
            resource_id=101,
            week_ending_date="2023-12-02",  # Saturday
        )

        assert result["resource_id"] == 101
        assert result["totals"]["total_hours"] == 21.5
        assert result["entry_count"] == 3
        assert len(result["daily_breakdown"]) == 3

    def test_generate_time_sheet_report_summary(
        self, time_entries_entity, sample_time_entry
    ):
        """Test generating summary time sheet report."""
        entries = [sample_time_entry]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.generate_time_sheet_report(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
            format="summary",
        )

        assert result["resource_id"] == 101
        assert result["format"] == "summary"
        assert "totals" in result

    def test_generate_time_sheet_report_detailed(
        self, time_entries_entity, sample_time_entry
    ):
        """Test generating detailed time sheet report."""
        entries = [sample_time_entry]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.generate_time_sheet_report(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
            format="detailed",
        )

        assert result["format"] == "detailed"
        assert "entries" in result

    def test_generate_time_sheet_report_weekly(
        self, time_entries_entity, sample_time_entry
    ):
        """Test generating weekly time sheet report."""
        entries = [sample_time_entry]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)
        time_entries_entity.get_time_sheet = Mock(return_value={"test": "data"})

        result = time_entries_entity.generate_time_sheet_report(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
            format="weekly",
        )

        assert result["format"] == "weekly"
        assert "weekly_data" in result

    # =============================================================================
    # Overtime and Holiday Tracking Tests
    # =============================================================================

    def test_calculate_overtime(self, time_entries_entity, sample_time_entry):
        """Test overtime calculation for a single day."""
        # Mock 10 hours of work (2 hours overtime)
        entries = [
            {**sample_time_entry, "HoursWorked": 10.0},
        ]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.calculate_overtime(
            resource_id=101,
            date="2023-12-01",
        )

        assert result["total_hours"] == 10.0
        assert (
            result["regular_hours"] == 8.0
        )  # TimeEntryConstants.OVERTIME_DAILY_THRESHOLD
        assert result["overtime_hours"] == 2.0
        assert result["double_time_hours"] == 0.0

    def test_calculate_overtime_with_double_time(
        self, time_entries_entity, sample_time_entry
    ):
        """Test overtime calculation with double time."""
        # Mock 14 hours of work (8 regular + 4 overtime + 2 double time)
        entries = [
            {**sample_time_entry, "HoursWorked": 14.0},
        ]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.calculate_overtime(
            resource_id=101,
            date="2023-12-01",
        )

        assert result["total_hours"] == 14.0
        assert result["regular_hours"] == 8.0
        assert (
            result["overtime_hours"] == 4.0
        )  # (14-8) - 2 = 4 (adjusted for double time)
        assert result["double_time_hours"] == 2.0  # 14 - 12 (DOUBLE_TIME_THRESHOLD)

    def test_calculate_weekly_overtime(self, time_entries_entity, sample_time_entry):
        """Test weekly overtime calculation."""
        # Mock 45 hours for the week (5 hours overtime)
        entries = [
            {**sample_time_entry, "HoursWorked": 45.0},
        ]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.calculate_weekly_overtime(
            resource_id=101,
            week_ending_date="2023-12-02",
        )

        assert result["total_weekly_hours"] == 45.0
        assert (
            result["regular_hours"] == 40.0
        )  # TimeEntryConstants.OVERTIME_WEEKLY_THRESHOLD
        assert result["overtime_hours"] == 5.0

    def test_mark_holiday_entries(self, time_entries_entity, sample_time_entry):
        """Test marking entries as holiday entries."""
        time_entries_entity.query = Mock(return_value=[sample_time_entry])
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        result = time_entries_entity.mark_holiday_entries(
            date="2023-12-25",
            resource_ids=[101, 102],
        )

        assert len(result) == 1
        time_entries_entity.update_time_entry.assert_called_once()

    def test_get_holiday_hours(self, time_entries_entity, sample_time_entry):
        """Test getting holiday hours for a resource."""
        holiday_entries = [
            {
                **sample_time_entry,
                "DateWorked": "2023-12-25",
                "HoursWorked": 8.0,
                "Type": TimeEntryType.HOLIDAY,
            },
            {
                **sample_time_entry,
                "DateWorked": "2023-12-26",
                "HoursWorked": 4.0,
                "Type": TimeEntryType.HOLIDAY,
            },
        ]
        time_entries_entity.query = Mock(return_value=holiday_entries)

        result = time_entries_entity.get_holiday_hours(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-31",
        )

        assert result["total_holiday_hours"] == 12.0
        assert result["holiday_days"] == 2
        assert len(result["by_date"]) == 2

    # =============================================================================
    # Analytics and Reporting Tests
    # =============================================================================

    def test_get_utilization_report(self, time_entries_entity, sample_time_entry):
        """Test utilization report generation."""
        entries = [
            {**sample_time_entry, "HoursWorked": 40.0, "BillableToAccount": True},
            {**sample_time_entry, "HoursWorked": 5.0, "BillableToAccount": False},
        ]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.get_utilization_report(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
            target_hours_per_week=40.0,
        )

        assert result["metrics"]["total_hours"] == 45.0
        assert result["metrics"]["billable_hours"] == 40.0
        assert result["metrics"]["utilization_percentage"] == 100.0  # 40/40 target
        assert result["metrics"]["efficiency_percentage"] > 85.0  # 40/45

    def test_get_billability_analysis(self, time_entries_entity, sample_time_entry):
        """Test billability analysis."""
        entries = [
            {
                **sample_time_entry,
                "HoursWorked": 30.0,
                "BillableToAccount": True,
                "Type": TimeEntryType.REGULAR,
            },
            {
                **sample_time_entry,
                "HoursWorked": 10.0,
                "BillableToAccount": False,
                "Type": TimeEntryType.TRAINING,
            },
        ]
        time_entries_entity.query = Mock(return_value=entries)

        result = time_entries_entity.get_billability_analysis(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
        )

        assert result["totals"]["total_hours"] == 40.0
        assert result["totals"]["billable_hours"] == 30.0
        assert result["totals"]["non_billable_hours"] == 10.0
        assert result["totals"]["billability_percentage"] == 75.0

    def test_get_productivity_metrics(self, time_entries_entity, sample_time_entry):
        """Test productivity metrics calculation."""
        entries = [
            {
                **sample_time_entry,
                "DateWorked": "2023-12-01",
                "HoursWorked": 8.0,
                "BillableToAccount": True,
                "ProjectID": 1001,
                "TicketID": 5001,
            },
            {
                **sample_time_entry,
                "DateWorked": "2023-12-01",
                "HoursWorked": 2.0,
                "BillableToAccount": False,
                "ProjectID": 1002,
                "TicketID": 5002,
            },
            {
                **sample_time_entry,
                "DateWorked": "2023-12-02",
                "HoursWorked": 7.0,
                "BillableToAccount": True,
                "ProjectID": 1001,
                "TicketID": 5003,
            },
        ]
        time_entries_entity.get_time_entries_by_resource = Mock(return_value=entries)

        result = time_entries_entity.get_productivity_metrics(
            resource_id=101,
            start_date="2023-12-01",
            end_date="2023-12-07",
        )

        assert result["summary"]["total_days_worked"] == 2
        assert result["summary"]["total_hours"] == 17.0
        assert result["summary"]["total_billable_hours"] == 15.0
        assert result["summary"]["total_entries"] == 3
        assert len(result["daily_breakdown"]) == 2

    def test_get_time_distribution(self, time_entries_entity, sample_time_entry):
        """Test time distribution analysis."""
        entries = [
            {
                **sample_time_entry,
                "HoursWorked": 20.0,
                "ProjectID": 1001,
                "BillableToAccount": True,
            },
            {
                **sample_time_entry,
                "HoursWorked": 15.0,
                "ProjectID": 1002,
                "BillableToAccount": True,
            },
            {
                **sample_time_entry,
                "HoursWorked": 5.0,
                "ProjectID": 1003,
                "BillableToAccount": False,
            },
        ]
        time_entries_entity.query = Mock(return_value=entries)

        result = time_entries_entity.get_time_distribution(
            resource_id=101,
            group_by="project",
        )

        assert result["total_hours"] == 40.0
        assert result["group_count"] == 3
        assert 1001 in result["distribution"]
        assert result["distribution"][1001]["total_hours"] == 20.0
        assert result["distribution"][1001]["percentage"] == 50.0

    def test_get_time_distribution_by_type(
        self, time_entries_entity, sample_time_entry
    ):
        """Test time distribution by entry type."""
        entries = [
            {**sample_time_entry, "HoursWorked": 30.0, "Type": TimeEntryType.REGULAR},
            {**sample_time_entry, "HoursWorked": 8.0, "Type": TimeEntryType.OVERTIME},
            {**sample_time_entry, "HoursWorked": 2.0, "Type": TimeEntryType.TRAINING},
        ]
        time_entries_entity.query = Mock(return_value=entries)

        result = time_entries_entity.get_time_distribution(
            group_by="type",
        )

        assert result["total_hours"] == 40.0
        assert TimeEntryType.REGULAR in result["distribution"]
        assert result["distribution"][TimeEntryType.REGULAR]["percentage"] == 75.0

    # =============================================================================
    # Helper and Utility Method Tests
    # =============================================================================

    def test_get_summary_for_period(self, time_entries_entity, sample_time_entry):
        """Test comprehensive period summary."""
        entries = [
            {
                **sample_time_entry,
                "HoursWorked": 8.0,
                "Status": TimeEntryStatus.APPROVED,
                "Type": TimeEntryType.REGULAR,
            },
            {
                **sample_time_entry,
                "HoursWorked": 6.0,
                "Status": TimeEntryStatus.DRAFT,
                "Type": TimeEntryType.OVERTIME,
            },
            {
                **sample_time_entry,
                "HoursWorked": 4.0,
                "Status": TimeEntryStatus.SUBMITTED,
                "Type": TimeEntryType.REGULAR,
            },
        ]
        time_entries_entity.query = Mock(return_value=entries)

        result = time_entries_entity.get_summary_for_period(
            start_date="2023-12-01",
            end_date="2023-12-07",
            resource_id=101,
        )

        assert result["totals"]["total_hours"] == 18.0
        assert result["totals"]["entry_count"] == 3
        assert result["breakdowns"]["by_status"][TimeEntryStatus.APPROVED] == 1
        assert result["breakdowns"]["by_type"][TimeEntryType.REGULAR] == 2

    def test_validate_hours_helper_valid(self, time_entries_entity):
        """Test hours validation with valid value."""
        # Should not raise exception
        time_entries_entity._validate_hours(8.0)

    def test_validate_hours_helper_too_low(self, time_entries_entity):
        """Test hours validation with too low value."""
        with pytest.raises(ValueError, match="Hours must be at least"):
            time_entries_entity._validate_hours(0.0)

    def test_validate_hours_helper_too_high(self, time_entries_entity):
        """Test hours validation with too high value."""
        with pytest.raises(ValueError, match="Hours cannot exceed"):
            time_entries_entity._validate_hours(25.0)

    def test_validate_work_associations_valid(self, time_entries_entity):
        """Test work associations validation with valid associations."""
        # Should not raise exception
        time_entries_entity._validate_work_associations(ticket_id=5001)
        time_entries_entity._validate_work_associations(project_id=2001)
        time_entries_entity._validate_work_associations(task_id=3001)

    def test_validate_work_associations_none(self, time_entries_entity):
        """Test work associations validation with no associations."""
        with pytest.raises(ValueError, match="Time entry must be associated"):
            time_entries_entity._validate_work_associations()

    # =============================================================================
    # Integration Tests
    # =============================================================================

    def test_complete_workflow_create_submit_approve(
        self, time_entries_entity, sample_time_entry
    ):
        """Test complete workflow: create -> submit -> approve."""
        # Mock all required methods
        time_entries_entity.create = Mock(return_value=sample_time_entry)
        time_entries_entity.get_time_entry = Mock(return_value=sample_time_entry)
        time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

        # Step 1: Create time entry
        created_entry = time_entries_entity.create_time_entry(
            resource_id=101,
            date_worked="2023-12-01",
            hours_worked=8.0,
            ticket_id=5001,
            description="Development work",
        )

        # Step 2: Submit for approval
        submitted_entries = time_entries_entity.submit_for_approval(
            time_entry_ids=created_entry["id"],
            submission_notes="Ready for approval",
        )

        # Step 3: Approve
        approved_entries = time_entries_entity.approve_time_entries(
            time_entry_ids=created_entry["id"],
            approver_resource_id=201,
            approval_notes="Approved",
        )

        assert len(submitted_entries) == 1
        assert len(approved_entries) == 1

    def test_time_tracking_session_workflow(
        self, time_entries_entity, sample_time_entry
    ):
        """Test complete time tracking session workflow."""
        # Mock datetime and methods
        with patch("py_autotask.entities.time_entries.datetime") as mock_datetime:
            # Start time tracking
            mock_now_start = Mock()
            mock_now_start.strftime.return_value = "2023-12-01"
            mock_now_start.isoformat.return_value = "2023-12-01T09:00:00"
            mock_datetime.now.return_value = mock_now_start

            time_entries_entity.create = Mock(
                return_value={**sample_time_entry, "id": 12345}
            )

            session = time_entries_entity.start_time_tracking(
                resource_id=101,
                ticket_id=5001,
                description="Working on feature",
            )

            # Stop time tracking
            mock_datetime.now.return_value = datetime(2023, 12, 1, 17, 0, 0)
            mock_datetime.fromisoformat.return_value = datetime(2023, 12, 1, 9, 0, 0)

            time_entries_entity.get_time_entry = Mock(
                return_value={
                    **sample_time_entry,
                    "StartDateTime": "2023-12-01T09:00:00",
                }
            )
            time_entries_entity.update_time_entry = Mock(return_value=sample_time_entry)

            final_entry = time_entries_entity.stop_time_tracking(
                time_entry_id=session["time_entry_id"],
                description="Completed feature work",
            )

            assert session["status"] == "running"
            assert final_entry == sample_time_entry

    def test_weekly_time_sheet_and_overtime_analysis(self, time_entries_entity):
        """Test weekly time sheet with overtime analysis."""
        # Mock week's worth of entries with some overtime
        week_entries = [
            {
                "DateWorked": "2023-11-27",
                "HoursWorked": 8.0,
                "BillableToAccount": True,
                "Type": TimeEntryType.REGULAR,
            },
            {
                "DateWorked": "2023-11-28",
                "HoursWorked": 9.0,
                "BillableToAccount": True,
                "Type": TimeEntryType.REGULAR,
            },
            {
                "DateWorked": "2023-11-29",
                "HoursWorked": 8.5,
                "BillableToAccount": True,
                "Type": TimeEntryType.REGULAR,
            },
            {
                "DateWorked": "2023-11-30",
                "HoursWorked": 10.0,
                "BillableToAccount": True,
                "Type": TimeEntryType.OVERTIME,
            },
            {
                "DateWorked": "2023-12-01",
                "HoursWorked": 7.0,
                "BillableToAccount": True,
                "Type": TimeEntryType.REGULAR,
            },
        ]
        time_entries_entity.query = Mock(return_value=week_entries)

        # Get time sheet
        time_sheet = time_entries_entity.get_time_sheet(
            resource_id=101,
            week_ending_date="2023-12-02",  # Saturday
        )

        # Calculate weekly overtime
        time_entries_entity.get_time_entries_by_resource = Mock(
            return_value=week_entries
        )
        overtime_calc = time_entries_entity.calculate_weekly_overtime(
            resource_id=101,
            week_ending_date="2023-12-02",
        )

        assert time_sheet["totals"]["total_hours"] == 42.5
        assert time_sheet["overtime_eligible"] is True  # Over 40 hours
        assert overtime_calc["total_weekly_hours"] == 42.5
        assert overtime_calc["overtime_hours"] == 2.5  # 42.5 - 40

    # =============================================================================
    # Edge Cases and Error Handling Tests
    # =============================================================================

    def test_empty_query_results(self, time_entries_entity):
        """Test handling of empty query results."""
        time_entries_entity.query = Mock(return_value=[])

        result = time_entries_entity.get_time_entries_by_resource(resource_id=999)

        assert result == []

    def test_invalid_date_format_handling(self, time_entries_entity):
        """Test handling of invalid date formats in calculations."""
        with pytest.raises(ValueError):
            time_entries_entity.calculate_duration(
                "invalid-date", "2023-12-01T17:00:00"
            )

    def test_bulk_operations_with_empty_lists(self, time_entries_entity):
        """Test bulk operations with empty input lists."""
        result = time_entries_entity.bulk_create_time_entries([])
        assert result == []

        result = time_entries_entity.bulk_update_time_entries([])
        assert result == []

        result = time_entries_entity.bulk_delete_time_entries([])
        assert result["deleted_count"] == 0

    def test_analytics_with_zero_hours(self, time_entries_entity):
        """Test analytics calculations with zero hours."""
        time_entries_entity.query = Mock(return_value=[])

        result = time_entries_entity.get_billability_analysis()

        assert result["totals"]["total_hours"] == 0
        assert result["totals"]["billability_percentage"] == 0
        assert result["entry_count"] == 0

    def test_time_sheet_empty_week(self, time_entries_entity):
        """Test time sheet generation for week with no entries."""
        time_entries_entity.query = Mock(return_value=[])

        result = time_entries_entity.get_time_sheet(
            resource_id=101,
            week_ending_date="2023-12-02",
        )

        assert result["totals"]["total_hours"] == 0
        assert result["entry_count"] == 0
        assert result["overtime_eligible"] is False


# Additional test classes for specific functionality areas could be added here
# to maintain organization and readability


class TestTimeEntryValidation:
    """Additional tests focused specifically on validation logic."""

    def test_hours_precision_validation(self):
        """Test hours validation with various precision levels."""
        entity = TimeEntriesEntity(Mock())

        # Test valid precision
        entity._validate_hours(8.25)  # Quarter hour
        entity._validate_hours(8.5)  # Half hour
        entity._validate_hours(8.01)  # Minimum valid
        entity._validate_hours(23.99)  # Just under max

        # Test boundary conditions
        with pytest.raises(ValueError):
            entity._validate_hours(0.001)  # Below minimum

        with pytest.raises(ValueError):
            entity._validate_hours(24.01)  # Above maximum


class TestTimeEntryConstants:
    """Tests for time entry constants and their usage."""

    def test_constant_values(self):
        """Test that constants have expected values."""
        assert TimeEntryConstants.MIN_HOURS == 0.01
        assert TimeEntryConstants.MAX_HOURS_PER_ENTRY == 24.0
        assert TimeEntryConstants.DEFAULT_INCREMENT == 0.25
        assert TimeEntryConstants.OVERTIME_DAILY_THRESHOLD == 8.0
        assert TimeEntryConstants.OVERTIME_WEEKLY_THRESHOLD == 40.0

    def test_status_filter_mappings(self):
        """Test status filter mappings."""
        assert "pending" in TimeEntryConstants.STATUS_FILTERS
        assert "approved" in TimeEntryConstants.STATUS_FILTERS
        assert TimeEntryStatus.DRAFT in TimeEntryConstants.STATUS_FILTERS["pending"]
