"""
Tests for the constants module.

This module tests all constants, enums, and utility functions in the constants module
to ensure they provide correct values and maintain backward compatibility.
"""

import pytest

from py_autotask.constants import (  # API Configuration; Common Enums; Task Constants; Ticket Constants; Project Constants; Contract Constants; Resource Constants; Account Constants; Expense Report Constants; Time Entry Constants; Opportunity Constants; Quote Constants; Invoice Constants; Utility Functions; Legacy constants
    TASK_STATUS_COMPLETE,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_NEW,
    AccountStatus,
    AccountType,
    APILimits,
    ContractBillingType,
    ContractConstants,
    ContractStatus,
    ContractType,
    ExpenseReportConstants,
    ExpenseReportStatus,
    FieldLengths,
    InvoiceStatus,
    OpportunityStage,
    OpportunityStatus,
    Priority,
    PriorityMap,
    ProjectConstants,
    ProjectStatus,
    ProjectType,
    QuoteStatus,
    ResourceConstants,
    ResourceStatus,
    ResourceType,
    TaskConstants,
    TaskDependencyType,
    TaskPriority,
    TaskStatus,
    TicketConstants,
    TicketPriority,
    TicketStatus,
    TicketType,
    TimeEntryStatus,
    TimeEntryType,
    get_priority_description,
    get_status_name,
    validate_status_filter,
)


class TestAPIConfiguration:
    """Test API configuration constants."""

    def test_api_limits_values(self):
        """Test that API limits have reasonable values."""
        assert APILimits.MAX_QUERY_RESULTS == 500
        assert APILimits.MAX_BATCH_SIZE == 200
        assert APILimits.MAX_CONCURRENT_REQUESTS == 10
        assert APILimits.DEFAULT_TIMEOUT == 30
        assert APILimits.MAX_RETRIES == 3
        assert APILimits.RETRY_BACKOFF_FACTOR == 2

    def test_field_lengths_values(self):
        """Test that field lengths are reasonable."""
        assert FieldLengths.TITLE_MAX == 255
        assert FieldLengths.DESCRIPTION_MAX == 8000
        assert FieldLengths.NAME_MAX == 100
        assert FieldLengths.EMAIL_MAX == 254
        assert FieldLengths.PHONE_MAX == 25
        assert FieldLengths.ADDRESS_LINE_MAX == 128
        assert FieldLengths.CITY_MAX == 50
        assert FieldLengths.STATE_MAX == 25
        assert FieldLengths.ZIP_CODE_MAX == 10
        assert FieldLengths.COUNTRY_MAX == 100


class TestPriorityConstants:
    """Test priority-related constants."""

    def test_priority_enum_values(self):
        """Test that priority enum has correct values."""
        assert Priority.CRITICAL == 1
        assert Priority.HIGH == 2
        assert Priority.MEDIUM == 3
        assert Priority.LOW == 4

    def test_priority_map_completeness(self):
        """Test that all priorities have descriptions."""
        for priority in Priority:
            assert priority in PriorityMap.DESCRIPTIONS
            assert isinstance(PriorityMap.DESCRIPTIONS[priority], str)
            assert len(PriorityMap.DESCRIPTIONS[priority]) > 0


class TestTaskConstants:
    """Test task-related constants."""

    def test_task_status_values(self):
        """Test task status enum values."""
        assert TaskStatus.NEW == 1
        assert TaskStatus.IN_PROGRESS == 2
        assert TaskStatus.WAITING == 3
        assert TaskStatus.CANCELLED == 4
        assert TaskStatus.COMPLETE == 5

    def test_task_priority_values(self):
        """Test task priority enum values."""
        assert TaskPriority.CRITICAL == 1
        assert TaskPriority.HIGH == 2
        assert TaskPriority.MEDIUM == 3
        assert TaskPriority.LOW == 4

    def test_task_dependency_types(self):
        """Test task dependency type constants."""
        assert TaskDependencyType.FINISH_TO_START == "finish_to_start"
        assert TaskDependencyType.START_TO_START == "start_to_start"
        assert TaskDependencyType.FINISH_TO_FINISH == "finish_to_finish"
        assert TaskDependencyType.START_TO_FINISH == "start_to_finish"

    def test_task_status_groups(self):
        """Test task status groupings."""
        assert TaskStatus.NEW in TaskConstants.OPEN_STATUSES
        assert TaskStatus.IN_PROGRESS in TaskConstants.OPEN_STATUSES
        assert TaskStatus.WAITING in TaskConstants.OPEN_STATUSES
        assert TaskStatus.COMPLETE in TaskConstants.CLOSED_STATUSES
        assert TaskStatus.CANCELLED in TaskConstants.CLOSED_STATUSES
        assert TaskStatus.IN_PROGRESS in TaskConstants.ACTIVE_STATUSES

    def test_task_status_filters(self):
        """Test task status filters are properly defined."""
        assert "open" in TaskConstants.STATUS_FILTERS
        assert "closed" in TaskConstants.STATUS_FILTERS
        assert "active" in TaskConstants.STATUS_FILTERS
        assert "completed" in TaskConstants.STATUS_FILTERS
        assert "in_progress" in TaskConstants.STATUS_FILTERS

        # Check that filter values match expected statuses
        assert TaskStatus.COMPLETE in TaskConstants.STATUS_FILTERS["completed"]
        assert TaskStatus.IN_PROGRESS in TaskConstants.STATUS_FILTERS["in_progress"]

    def test_task_validation_constants(self):
        """Test task validation constants."""
        assert TaskConstants.MIN_ESTIMATED_HOURS == 0.01
        assert TaskConstants.MAX_ESTIMATED_HOURS == 9999.99
        assert TaskConstants.MIN_PERCENT_COMPLETE == 0
        assert TaskConstants.MAX_PERCENT_COMPLETE == 100
        assert TaskConstants.MIN_TITLE_LENGTH == 3
        assert TaskConstants.MAX_TITLE_LENGTH == FieldLengths.TITLE_MAX


class TestTicketConstants:
    """Test ticket-related constants."""

    def test_ticket_status_values(self):
        """Test ticket status enum values."""
        assert TicketStatus.NEW == 1
        assert TicketStatus.ASSIGNED == 2
        assert TicketStatus.IN_PROGRESS == 3
        assert TicketStatus.COMPLETE == 8
        assert TicketStatus.CANCELLED == 9

    def test_ticket_type_values(self):
        """Test ticket type enum values."""
        assert TicketType.INCIDENT == 1
        assert TicketType.PROBLEM == 2
        assert TicketType.CHANGE_REQUEST == 3
        assert TicketType.SERVICE_REQUEST == 4
        assert TicketType.MAINTENANCE == 5

    def test_ticket_priority_values(self):
        """Test ticket priority enum values."""
        assert TicketPriority.CRITICAL == 1
        assert TicketPriority.HIGH == 2
        assert TicketPriority.MEDIUM == 3
        assert TicketPriority.LOW == 4

    def test_ticket_status_groups(self):
        """Test ticket status groupings."""
        assert TicketStatus.NEW in TicketConstants.OPEN_STATUSES
        assert TicketStatus.IN_PROGRESS in TicketConstants.OPEN_STATUSES
        assert TicketStatus.COMPLETE in TicketConstants.CLOSED_STATUSES
        assert TicketStatus.CANCELLED in TicketConstants.CLOSED_STATUSES
        assert TicketStatus.ASSIGNED in TicketConstants.ACTIVE_STATUSES
        assert TicketStatus.IN_PROGRESS in TicketConstants.ACTIVE_STATUSES

    def test_ticket_sla_mappings(self):
        """Test SLA time mappings."""
        assert TicketPriority.CRITICAL in TicketConstants.SLA_RESPONSE_TIMES
        assert TicketPriority.CRITICAL in TicketConstants.SLA_RESOLUTION_TIMES

        # Critical tickets should have fastest response/resolution times
        critical_response = TicketConstants.SLA_RESPONSE_TIMES[TicketPriority.CRITICAL]
        low_response = TicketConstants.SLA_RESPONSE_TIMES[TicketPriority.LOW]
        assert critical_response < low_response


class TestProjectConstants:
    """Test project-related constants."""

    def test_project_status_values(self):
        """Test project status enum values."""
        assert ProjectStatus.NEW == 1
        assert ProjectStatus.IN_PROGRESS == 2
        assert ProjectStatus.ON_HOLD == 3
        assert ProjectStatus.CANCELLED == 4
        assert ProjectStatus.COMPLETE == 5

    def test_project_type_values(self):
        """Test project type enum values."""
        assert ProjectType.FIXED_PRICE == 1
        assert ProjectType.TIME_AND_MATERIALS == 2
        assert ProjectType.RETAINER == 3
        assert ProjectType.RECURRING_SERVICE == 4
        assert ProjectType.MILESTONE == 5

    def test_project_type_descriptions(self):
        """Test that all project types have descriptions."""
        for project_type in ProjectType:
            assert project_type in ProjectConstants.TYPE_DESCRIPTIONS
            assert isinstance(ProjectConstants.TYPE_DESCRIPTIONS[project_type], str)


class TestContractConstants:
    """Test contract-related constants."""

    def test_contract_status_values(self):
        """Test contract status enum values."""
        assert ContractStatus.DRAFT == 1
        assert ContractStatus.ACTIVE == 2
        assert ContractStatus.ON_HOLD == 3
        assert ContractStatus.EXPIRED == 4
        assert ContractStatus.CANCELLED == 5
        assert ContractStatus.COMPLETE == 6

    def test_contract_type_values(self):
        """Test contract type enum values."""
        assert ContractType.RECURRING_SERVICE == 1
        assert ContractType.BLOCK_HOURS == 2
        assert ContractType.TIME_AND_MATERIALS == 3
        assert ContractType.FIXED_PRICE == 4
        assert ContractType.MAINTENANCE == 5

    def test_contract_billing_type_values(self):
        """Test contract billing type enum values."""
        assert ContractBillingType.MONTHLY == 1
        assert ContractBillingType.QUARTERLY == 2
        assert ContractBillingType.SEMI_ANNUALLY == 3
        assert ContractBillingType.ANNUALLY == 4
        assert ContractBillingType.ONE_TIME == 5


class TestResourceConstants:
    """Test resource-related constants."""

    def test_resource_status_values(self):
        """Test resource status enum values."""
        assert ResourceStatus.ACTIVE == 1
        assert ResourceStatus.INACTIVE == 2
        assert ResourceStatus.TERMINATED == 3
        assert ResourceStatus.ON_LEAVE == 4

    def test_resource_type_values(self):
        """Test resource type enum values."""
        assert ResourceType.EMPLOYEE == 1
        assert ResourceType.CONTRACTOR == 2
        assert ResourceType.CONSULTANT == 3
        assert ResourceType.VENDOR == 4


class TestAccountConstants:
    """Test account-related constants."""

    def test_account_status_values(self):
        """Test account status enum values."""
        assert AccountStatus.ACTIVE == 1
        assert AccountStatus.INACTIVE == 2
        assert AccountStatus.PROSPECT == 3
        assert AccountStatus.FORMER_CLIENT == 4

    def test_account_type_values(self):
        """Test account type enum values."""
        assert AccountType.CUSTOMER == 1
        assert AccountType.PROSPECT == 2
        assert AccountType.PARTNER == 3
        assert AccountType.VENDOR == 4
        assert AccountType.LEAD == 5


class TestExpenseReportConstants:
    """Test expense report constants."""

    def test_expense_report_status_values(self):
        """Test expense report status enum values."""
        assert ExpenseReportStatus.DRAFT == 1
        assert ExpenseReportStatus.SUBMITTED == 2
        assert ExpenseReportStatus.APPROVED == 3
        assert ExpenseReportStatus.REJECTED == 4
        assert ExpenseReportStatus.PAID == 5


class TestTimeEntryConstants:
    """Test time entry constants."""

    def test_time_entry_type_values(self):
        """Test time entry type enum values."""
        assert TimeEntryType.REGULAR == 1
        assert TimeEntryType.OVERTIME == 2
        assert TimeEntryType.DOUBLE_TIME == 3
        assert TimeEntryType.HOLIDAY == 4
        assert TimeEntryType.PTO == 5
        assert TimeEntryType.SICK == 6
        assert TimeEntryType.TRAINING == 7

    def test_time_entry_status_values(self):
        """Test time entry status enum values."""
        assert TimeEntryStatus.DRAFT == 1
        assert TimeEntryStatus.SUBMITTED == 2
        assert TimeEntryStatus.APPROVED == 3
        assert TimeEntryStatus.REJECTED == 4
        assert TimeEntryStatus.INVOICED == 5


class TestOpportunityConstants:
    """Test opportunity constants."""

    def test_opportunity_status_values(self):
        """Test opportunity status enum values."""
        assert OpportunityStatus.OPEN == 1
        assert OpportunityStatus.WON == 2
        assert OpportunityStatus.LOST == 3
        assert OpportunityStatus.CANCELLED == 4

    def test_opportunity_stage_values(self):
        """Test opportunity stage enum values."""
        assert OpportunityStage.LEAD == 1
        assert OpportunityStage.QUALIFIED == 2
        assert OpportunityStage.PROPOSAL == 3
        assert OpportunityStage.NEGOTIATION == 4
        assert OpportunityStage.CLOSING == 5


class TestQuoteConstants:
    """Test quote constants."""

    def test_quote_status_values(self):
        """Test quote status enum values."""
        assert QuoteStatus.DRAFT == 1
        assert QuoteStatus.PENDING == 2
        assert QuoteStatus.ACCEPTED == 3
        assert QuoteStatus.REJECTED == 4
        assert QuoteStatus.EXPIRED == 5


class TestInvoiceConstants:
    """Test invoice constants."""

    def test_invoice_status_values(self):
        """Test invoice status enum values."""
        assert InvoiceStatus.DRAFT == 1
        assert InvoiceStatus.SENT == 2
        assert InvoiceStatus.PAID == 3
        assert InvoiceStatus.OVERDUE == 4
        assert InvoiceStatus.CANCELLED == 5


class TestUtilityFunctions:
    """Test utility functions in constants module."""

    def test_get_status_name_valid(self):
        """Test get_status_name with valid status values."""
        assert get_status_name(TaskStatus, 1) == "NEW"
        assert get_status_name(TaskStatus, 2) == "IN_PROGRESS"
        assert get_status_name(TaskStatus, 5) == "COMPLETE"

        assert get_status_name(TicketStatus, 1) == "NEW"
        assert get_status_name(TicketStatus, 8) == "COMPLETE"

    def test_get_status_name_invalid(self):
        """Test get_status_name with invalid status values."""
        assert get_status_name(TaskStatus, 999) == "UNKNOWN"
        assert get_status_name(TicketStatus, -1) == "UNKNOWN"

    def test_get_priority_description_valid(self):
        """Test get_priority_description with valid priorities."""
        desc = get_priority_description(Priority.CRITICAL)
        assert isinstance(desc, str)
        assert "Critical" in desc

        desc = get_priority_description(Priority.LOW)
        assert isinstance(desc, str)
        assert "Low" in desc

    def test_get_priority_description_invalid(self):
        """Test get_priority_description with invalid priorities."""
        desc = get_priority_description(999)
        assert "Unknown Priority" in desc
        assert "999" in desc

    def test_validate_status_filter_valid(self):
        """Test validate_status_filter with valid filters."""
        statuses = validate_status_filter(TaskConstants, "open")
        assert isinstance(statuses, list)
        assert len(statuses) > 0
        assert TaskStatus.NEW in statuses

        statuses = validate_status_filter(TaskConstants, "completed")
        assert TaskStatus.COMPLETE in statuses

    def test_validate_status_filter_invalid(self):
        """Test validate_status_filter with invalid filters."""
        with pytest.raises(ValueError) as exc_info:
            validate_status_filter(TaskConstants, "invalid_filter")
        assert "Invalid status filter" in str(exc_info.value)

    def test_validate_status_filter_case_insensitive(self):
        """Test that validate_status_filter is case insensitive."""
        statuses1 = validate_status_filter(TaskConstants, "OPEN")
        statuses2 = validate_status_filter(TaskConstants, "open")
        statuses3 = validate_status_filter(TaskConstants, "Open")

        assert statuses1 == statuses2 == statuses3


class TestLegacyCompatibility:
    """Test legacy constant compatibility."""

    def test_legacy_task_constants(self):
        """Test that legacy task constants still work."""
        assert TASK_STATUS_NEW == TaskStatus.NEW
        assert TASK_STATUS_IN_PROGRESS == TaskStatus.IN_PROGRESS
        assert TASK_STATUS_COMPLETE == TaskStatus.COMPLETE

    def test_legacy_constants_equal_new_constants(self):
        """Test that legacy constants equal their new counterparts."""
        # Task status constants
        assert TASK_STATUS_NEW == 1
        assert TASK_STATUS_IN_PROGRESS == 2
        assert TASK_STATUS_COMPLETE == 5


class TestEnumIntegrity:
    """Test enum integrity and consistency."""

    def test_no_duplicate_values_in_enums(self):
        """Test that enums don't have duplicate values."""
        enums_to_test = [
            TaskStatus,
            TaskPriority,
            TicketStatus,
            TicketType,
            TicketPriority,
            ProjectStatus,
            ProjectType,
            ContractStatus,
            ContractType,
            ContractBillingType,
            ResourceStatus,
            ResourceType,
            AccountStatus,
            AccountType,
            ExpenseReportStatus,
            TimeEntryType,
            TimeEntryStatus,
            OpportunityStatus,
            OpportunityStage,
            QuoteStatus,
            InvoiceStatus,
        ]

        for enum_class in enums_to_test:
            values = [item.value for item in enum_class]
            assert len(values) == len(
                set(values)
            ), f"Duplicate values in {enum_class.__name__}"

    def test_enum_values_are_positive_integers(self):
        """Test that all enum values are positive integers."""
        enums_to_test = [
            TaskStatus,
            TaskPriority,
            TicketStatus,
            TicketType,
            TicketPriority,
            ProjectStatus,
            ProjectType,
            ContractStatus,
            ContractType,
            ContractBillingType,
            ResourceStatus,
            ResourceType,
            AccountStatus,
            AccountType,
            ExpenseReportStatus,
            TimeEntryType,
            TimeEntryStatus,
            OpportunityStatus,
            OpportunityStage,
            QuoteStatus,
            InvoiceStatus,
        ]

        for enum_class in enums_to_test:
            for item in enum_class:
                assert isinstance(
                    item.value, int
                ), f"{enum_class.__name__}.{item.name} value is not int"
                assert (
                    item.value > 0
                ), f"{enum_class.__name__}.{item.name} value is not positive"


class TestStatusFilterConsistency:
    """Test that status filter mappings are consistent."""

    def test_status_filters_contain_valid_statuses(self):
        """Test that all status filter values are valid enum values."""
        constants_with_filters = [
            (TaskConstants, TaskStatus),
            (TicketConstants, TicketStatus),
            (ProjectConstants, ProjectStatus),
            (ContractConstants, ContractStatus),
            (ResourceConstants, ResourceStatus),
            (ExpenseReportConstants, ExpenseReportStatus),
        ]

        for constants_class, status_enum in constants_with_filters:
            if hasattr(constants_class, "STATUS_FILTERS"):
                status_filters = constants_class.STATUS_FILTERS
                valid_values = [item.value for item in status_enum]

                for filter_name, status_list in status_filters.items():
                    for status_value in status_list:
                        assert (
                            status_value in valid_values
                        ), f"{constants_class.__name__} filter '{filter_name}' contains invalid status {status_value}"


if __name__ == "__main__":
    pytest.main([__file__])
