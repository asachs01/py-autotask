#!/usr/bin/env python3
"""
Enhanced test suite for Resources entity with all new functionality.

This module tests the comprehensive resource management features including
capacity planning, skill tracking, scheduling, billing, and role management.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from py_autotask.entities.resources import ResourcesEntity


class TestResourcesEntityEnhanced:
    """Test suite for enhanced Resources entity functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.resources_entity = ResourcesEntity(self.mock_client)

    def test_resource_constants_defined(self):
        """Test that all required constants are defined."""
        # Check RESOURCE_TYPE constants
        assert hasattr(ResourcesEntity, "RESOURCE_TYPE")
        assert ResourcesEntity.RESOURCE_TYPE["EMPLOYEE"] == 1
        assert ResourcesEntity.RESOURCE_TYPE["CONTRACTOR"] == 2
        assert ResourcesEntity.RESOURCE_TYPE["VENDOR"] == 3
        assert ResourcesEntity.RESOURCE_TYPE["GENERIC"] == 4
        assert ResourcesEntity.RESOURCE_TYPE["SUBCONTRACTOR"] == 5

        # Check RESOURCE_STATUS constants
        assert hasattr(ResourcesEntity, "RESOURCE_STATUS")
        assert ResourcesEntity.RESOURCE_STATUS["INACTIVE"] == 0
        assert ResourcesEntity.RESOURCE_STATUS["ACTIVE"] == 1
        assert ResourcesEntity.RESOURCE_STATUS["DISABLED"] == 2
        assert ResourcesEntity.RESOURCE_STATUS["ON_LEAVE"] == 3
        assert ResourcesEntity.RESOURCE_STATUS["TERMINATED"] == 4

        # Check SECURITY_LEVEL constants
        assert hasattr(ResourcesEntity, "SECURITY_LEVEL")
        assert ResourcesEntity.SECURITY_LEVEL["ADMIN"] == 1
        assert ResourcesEntity.SECURITY_LEVEL["SUPER_USER"] == 2
        assert ResourcesEntity.SECURITY_LEVEL["USER"] == 3
        assert ResourcesEntity.SECURITY_LEVEL["RESTRICTED"] == 4

        # Check DEPARTMENT constants
        assert hasattr(ResourcesEntity, "DEPARTMENT")
        assert len(ResourcesEntity.DEPARTMENT) >= 8

        # Check RESOURCE_ROLE constants
        assert hasattr(ResourcesEntity, "RESOURCE_ROLE")
        assert len(ResourcesEntity.RESOURCE_ROLE) == 8

        # Check WORK_TYPE constants
        assert hasattr(ResourcesEntity, "WORK_TYPE")
        assert len(ResourcesEntity.WORK_TYPE) == 8

        # Check SKILL_LEVEL constants
        assert hasattr(ResourcesEntity, "SKILL_LEVEL")
        assert ResourcesEntity.SKILL_LEVEL["BEGINNER"] == 1
        assert ResourcesEntity.SKILL_LEVEL["INTERMEDIATE"] == 2
        assert ResourcesEntity.SKILL_LEVEL["ADVANCED"] == 3
        assert ResourcesEntity.SKILL_LEVEL["EXPERT"] == 4

    def test_get_resource_availability(self):
        """Test getting resource availability."""
        start_date = datetime(2024, 12, 1)
        end_date = datetime(2024, 12, 7)

        # Mock resource data
        self.resources_entity.get = Mock(
            return_value={"FirstName": "John", "LastName": "Doe"}
        )

        # Mock time entries
        self.resources_entity.get_resource_time_entries = Mock(
            return_value=[{"DateWorked": "2024-12-02", "HoursWorked": 8.0}]
        )

        # Mock scheduled tasks query
        self.mock_client.query = Mock(
            return_value=[
                {
                    "startDateTime": "2024-12-03T10:00:00",
                    "endDateTime": "2024-12-03T14:00:00",
                }
            ]
        )

        result = self.resources_entity.get_resource_availability(
            123, start_date, end_date
        )

        assert "available_slots" in result
        assert "busy_slots" in result
        assert "daily_summary" in result
        assert len(result["daily_summary"]) == 7  # 7 days

    def test_calculate_utilization(self):
        """Test calculating resource utilization."""
        period_start = datetime(2024, 12, 1)
        period_end = datetime(2024, 12, 31)

        # Mock resource data
        self.resources_entity.get = Mock(return_value={"workingHoursPerWeek": 40})

        # Mock time entries query
        self.resources_entity.get_resource_time_entries = Mock(
            return_value=[
                {"HoursWorked": 8.0, "DateWorked": "2024-12-02T09:00:00"},
                {"HoursWorked": 6.5, "DateWorked": "2024-12-03T09:00:00"},
            ]
        )

        result = self.resources_entity.calculate_utilization(
            123, period="custom", custom_start=period_start, custom_end=period_end
        )

        assert "utilization_percentage" in result
        assert "total_hours_worked" in result
        assert "total_available_hours" in result
        assert "period_days" in result
        self.resources_entity.get.assert_called_once_with(123)

    def test_get_workload_summary(self):
        """Test getting workload summary."""
        # Mock resource data
        self.resources_entity.get = Mock(
            return_value={"FirstName": "John", "LastName": "Doe"}
        )

        # Mock active tickets
        self.resources_entity.get_resource_tickets = Mock(
            return_value=[
                {"id": 1, "title": "Ticket 1"},
                {"id": 2, "title": "Ticket 2"},
            ]
        )

        # Mock active tasks query
        self.mock_client.query = Mock(
            return_value=[
                {"projectID": 100, "estimatedHours": 40, "hoursWorked": 25},
                {"projectID": 101, "estimatedHours": 20, "hoursWorked": 5},
            ]
        )

        # Mock calculate_utilization and get_resource_availability
        self.resources_entity.calculate_utilization = Mock(
            return_value={"utilization": {"total_utilization": 75.0}}
        )
        self.resources_entity.get_resource_availability = Mock(
            return_value={
                "utilization_percentage": 80.0,
                "status": "well_utilized",
                "hours_summary": {"free_hours": 20.0},
            }
        )

        result = self.resources_entity.get_workload_summary(123)

        assert "total_assignments" in result
        assert "total_estimated_hours" in result
        assert "total_hours_worked" in result
        assert "completion_percentage" in result
        assert "assignments" in result
        assert result["total_assignments"] == 2

    def test_add_skill(self):
        """Test adding a skill to a resource."""
        skill_data = {
            "skillID": 50,
            "skillLevel": ResourcesEntity.SKILL_LEVEL["INTERMEDIATE"],
            "yearsExperience": 3,
            "isCertified": True,
        }

        self.mock_client.create = Mock(return_value={"id": 789})

        result = self.resources_entity.add_skill(123, skill_data)

        assert result["id"] == 789
        self.mock_client.create.assert_called_once()
        call_args = self.mock_client.create.call_args[0][1]
        assert call_args["resourceID"] == 123
        assert call_args["skillID"] == 50

    def test_get_resources_by_skill(self):
        """Test getting resources by skill."""
        expected_resources = [
            {"id": 1, "firstName": "John", "lastName": "Doe"},
            {"id": 2, "firstName": "Jane", "lastName": "Smith"},
        ]
        self.resources_entity.query = Mock(return_value=expected_resources)

        result = self.resources_entity.get_resources_by_skill(50, minimum_level=3)

        assert result == expected_resources
        self.resources_entity.query.assert_called_once()
        filters = self.resources_entity.query.call_args[1]["filters"]
        assert any(f.field == "skillID" and f.value == 50 for f in filters)
        assert any(
            f.field == "skillLevel" and f.op == "gte" and f.value == 3 for f in filters
        )

    def test_match_resources_to_requirements(self):
        """Test matching resources to skill requirements."""
        requirements = [
            {"skillID": 50, "requiredLevel": 3, "weight": 0.8},
            {"skillID": 51, "requiredLevel": 4, "weight": 0.2},
        ]

        # Mock skill queries
        self.resources_entity.query = Mock(
            side_effect=[
                [{"resourceID": 1}, {"resourceID": 2}],  # Resources with skill 50
                [{"resourceID": 1}, {"resourceID": 3}],  # Resources with skill 51
            ]
        )

        # Mock resource details
        self.mock_client.get = Mock(
            side_effect=[
                {"id": 1, "firstName": "John", "lastName": "Doe"},
                {"id": 2, "firstName": "Jane", "lastName": "Smith"},
                {"id": 3, "firstName": "Bob", "lastName": "Wilson"},
            ]
        )

        result = self.resources_entity.match_resources_to_requirements(requirements)

        assert "matched_resources" in result
        assert "scoring_details" in result
        assert len(result["matched_resources"]) > 0

    def test_schedule_resource(self):
        """Test scheduling a resource to a task."""
        start_time = datetime(2024, 12, 15, 9, 0)
        end_time = datetime(2024, 12, 15, 17, 0)

        # Mock conflict check
        self.resources_entity.check_conflicts = Mock(
            return_value={"has_conflicts": False}
        )
        self.mock_client.create = Mock(return_value={"id": 456})

        result = self.resources_entity.schedule_resource(123, 789, start_time, end_time)

        assert result["id"] == 456
        self.resources_entity.check_conflicts.assert_called_once_with(
            123, start_time, end_time
        )
        self.mock_client.create.assert_called_once()

    def test_schedule_resource_with_conflict(self):
        """Test that scheduling fails when conflicts exist."""
        start_time = datetime(2024, 12, 15, 9, 0)
        end_time = datetime(2024, 12, 15, 17, 0)

        # Mock conflict check with conflicts
        self.resources_entity.check_conflicts = Mock(
            return_value={"has_conflicts": True}
        )

        with pytest.raises(ValueError, match="Resource has scheduling conflicts"):
            self.resources_entity.schedule_resource(123, 789, start_time, end_time)

    def test_get_resource_calendar(self):
        """Test getting resource calendar."""
        start_date = datetime(2024, 12, 1)
        end_date = datetime(2024, 12, 31)

        # Mock scheduled tasks and time entries
        self.resources_entity.query_scheduled_tasks = Mock(
            return_value=[
                {"id": 1, "taskID": 100, "startDateTime": "2024-12-02T09:00:00"},
            ]
        )
        self.resources_entity.query_time_entries = Mock(
            return_value=[
                {"id": 2, "ticketID": 200, "startDateTime": "2024-12-03T10:00:00"},
            ]
        )

        result = self.resources_entity.get_resource_calendar(123, start_date, end_date)

        assert "scheduled_tasks" in result
        assert "time_entries" in result
        assert "summary" in result

    def test_check_conflicts(self):
        """Test checking for scheduling conflicts."""
        start_time = datetime(2024, 12, 15, 9, 0)
        end_time = datetime(2024, 12, 15, 17, 0)

        # Mock existing schedules with conflict
        self.resources_entity.query = Mock(
            return_value=[
                {
                    "startDateTime": "2024-12-15T08:00:00",
                    "endDateTime": "2024-12-15T16:00:00",
                },
            ]
        )

        result = self.resources_entity.check_conflicts(123, start_time, end_time)

        assert result["has_conflicts"] is True
        assert len(result["conflicts"]) == 1

    def test_set_billing_rate(self):
        """Test setting billing rate for a resource."""
        rate_data = {
            "hourlyRate": 150.0,
            "costRate": 100.0,
            "effectiveDate": "2024-12-01",
            "currency": "USD",
        }

        self.mock_client.create = Mock(return_value={"id": 999})

        result = self.resources_entity.set_billing_rate(123, rate_data)

        assert result["id"] == 999
        self.mock_client.create.assert_called_once()
        call_args = self.mock_client.create.call_args[0][1]
        assert call_args["resourceID"] == 123
        assert call_args["hourlyRate"] == 150.0

    def test_calculate_resource_cost(self):
        """Test calculating resource cost."""
        # Mock current billing rate
        self.resources_entity.query = Mock(
            return_value=[
                {"hourlyRate": 150.0, "costRate": 100.0, "effectiveDate": "2024-12-01"},
            ]
        )

        result = self.resources_entity.calculate_resource_cost(123, 10.5)

        assert "billable_amount" in result
        assert "cost_amount" in result
        assert "margin" in result
        assert "hours" in result
        assert result["billable_amount"] == 1575.0  # 150 * 10.5
        assert result["cost_amount"] == 1050.0  # 100 * 10.5

    def test_get_rate_history(self):
        """Test getting rate history for a resource."""
        expected_rates = [
            {"hourlyRate": 150.0, "effectiveDate": "2024-12-01"},
            {"hourlyRate": 140.0, "effectiveDate": "2024-06-01"},
        ]
        self.resources_entity.query = Mock(return_value=expected_rates)

        result = self.resources_entity.get_rate_history(123)

        assert result == expected_rates
        self.resources_entity.query.assert_called_once()
        filters = self.resources_entity.query.call_args[1]["filters"]
        assert any(f.field == "resourceID" and f.value == 123 for f in filters)

    def test_assign_role(self):
        """Test assigning a role to a resource."""
        self.mock_client.update = Mock(return_value={"id": 123})

        self.resources_entity.assign_role(
            123, ResourcesEntity.RESOURCE_ROLE["PROJECT_MANAGER"]
        )

        call_args = self.mock_client.update.call_args[0][1]
        assert call_args["roleID"] == ResourcesEntity.RESOURCE_ROLE["PROJECT_MANAGER"]

    def test_get_resources_by_role(self):
        """Test getting resources by role."""
        expected_resources = [
            {"id": 1, "firstName": "John", "roleID": 5},
            {"id": 2, "firstName": "Jane", "roleID": 5},
        ]
        self.resources_entity.query = Mock(return_value=expected_resources)

        result = self.resources_entity.get_resources_by_role(
            ResourcesEntity.RESOURCE_ROLE["PROJECT_MANAGER"]
        )

        assert result == expected_resources
        self.resources_entity.query.assert_called_once()
        filters = self.resources_entity.query.call_args[1]["filters"]
        assert any(
            f.field == "roleID"
            and f.value == ResourcesEntity.RESOURCE_ROLE["PROJECT_MANAGER"]
            for f in filters
        )

    def test_validate_resource_data(self):
        """Test resource data validation."""
        # Valid resource data
        valid_data = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "resourceType": ResourcesEntity.RESOURCE_TYPE["EMPLOYEE"],
        }

        result = self.resources_entity.validate_resource_data(valid_data)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

        # Invalid resource data
        invalid_data = {
            "firstName": "John",
            "email": "invalid-email",
            "resourceType": 999,  # Invalid type
        }

        result = self.resources_entity.validate_resource_data(invalid_data)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_resource_schedule(self):
        """Test resource schedule validation."""
        start_time = datetime(2024, 12, 15, 9, 0)
        end_time = datetime(2024, 12, 15, 17, 0)

        # Mock no conflicts and valid capacity
        self.resources_entity.check_conflicts = Mock(
            return_value={"has_conflicts": False}
        )
        self.resources_entity.get_resource_availability = Mock(
            return_value={
                "daily_summary": [{"date": "2024-12-15", "available_hours": 8}]
            }
        )

        result = self.resources_entity.validate_resource_schedule(
            123, start_time, end_time, 8.0
        )

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_skill_assignment(self):
        """Test skill assignment validation."""
        # Valid skill data
        valid_skill = {
            "skillID": 50,
            "skillLevel": ResourcesEntity.SKILL_LEVEL["INTERMEDIATE"],
            "yearsExperience": 3,
        }

        result = self.resources_entity.validate_skill_assignment(valid_skill)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

        # Invalid skill data
        invalid_skill = {
            "skillLevel": 10,  # Invalid level
            "yearsExperience": -1,  # Negative years
        }

        result = self.resources_entity.validate_skill_assignment(invalid_skill)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_billing_rate(self):
        """Test billing rate validation."""
        # Valid rate data
        valid_rate = {
            "hourlyRate": 150.0,
            "costRate": 100.0,
            "effectiveDate": "2024-12-01",
            "currency": "USD",
        }

        result = self.resources_entity.validate_billing_rate(valid_rate)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

        # Invalid rate data
        invalid_rate = {
            "hourlyRate": -50.0,  # Negative rate
            "effectiveDate": "invalid-date",  # Invalid date
        }

        result = self.resources_entity.validate_billing_rate(invalid_rate)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_create_resource_with_validation(self):
        """Test creating a resource with validation."""
        resource_data = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "resourceType": ResourcesEntity.RESOURCE_TYPE["EMPLOYEE"],
        }

        expected_response = {"id": 456, **resource_data}
        self.mock_client.create = Mock(return_value=expected_response)

        result = self.resources_entity.create(resource_data)

        assert result == expected_response
        self.mock_client.create.assert_called_once()

    def test_create_resource_validation_failure(self):
        """Test that creating a resource with invalid data fails."""
        invalid_data = {
            "firstName": "John",
            "email": "invalid-email",
            "resourceType": 999,  # Invalid type
        }

        with pytest.raises(ValueError, match="Resource data validation failed"):
            self.resources_entity.create(invalid_data)

    def test_update_resource_prevents_email_conflicts(self):
        """Test that updating a resource prevents email conflicts."""
        # Mock existing resource with same email
        self.resources_entity.query = Mock(
            return_value=[{"id": 999, "email": "existing@example.com"}]
        )

        update_data = {"email": "existing@example.com"}

        with pytest.raises(ValueError, match="Email address already exists"):
            self.resources_entity.update(123, update_data)


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestResourcesEntityEnhanced()
    test_instance.setup_method()

    print("Running enhanced resource entity tests...")

    # Test constants
    test_instance.test_resource_constants_defined()
    print("✓ Resource constants defined correctly")

    # Test capacity planning
    test_instance.test_get_resource_availability()
    print("✓ Resource availability calculation works")

    test_instance.test_calculate_utilization()
    print("✓ Utilization calculation works")

    test_instance.test_get_workload_summary()
    print("✓ Workload summary works")

    # Test skill tracking
    test_instance.test_add_skill()
    print("✓ Skill addition works")

    test_instance.test_get_resources_by_skill()
    print("✓ Resource skill filtering works")

    test_instance.test_match_resources_to_requirements()
    print("✓ Resource matching works")

    # Test scheduling
    test_instance.test_schedule_resource()
    print("✓ Resource scheduling works")

    test_instance.test_get_resource_calendar()
    print("✓ Resource calendar works")

    test_instance.test_check_conflicts()
    print("✓ Conflict checking works")

    # Test billing
    test_instance.test_set_billing_rate()
    print("✓ Billing rate setting works")

    test_instance.test_calculate_resource_cost()
    print("✓ Resource cost calculation works")

    test_instance.test_get_rate_history()
    print("✓ Rate history retrieval works")

    # Test role assignment
    test_instance.test_assign_role()
    print("✓ Role assignment works")

    test_instance.test_get_resources_by_role()
    print("✓ Role filtering works")

    # Test validation
    test_instance.test_validate_resource_data()
    print("✓ Resource data validation works")

    test_instance.test_validate_resource_schedule()
    print("✓ Schedule validation works")

    test_instance.test_validate_skill_assignment()
    print("✓ Skill validation works")

    test_instance.test_validate_billing_rate()
    print("✓ Billing rate validation works")

    # Test integration
    test_instance.test_create_resource_with_validation()
    print("✓ Resource creation with validation works")

    print("\nAll enhanced resource tests passed!")
