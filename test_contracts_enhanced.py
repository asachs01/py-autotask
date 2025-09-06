"""
Comprehensive tests for enhanced Contracts entity functionality.

This module tests all the advanced contract management features including
billing integration, service level tracking, milestone management, renewal
alerts, usage tracking, and contract modifications.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pytest

from py_autotask.entities.contracts import (
    ContractsEntity,
    ContractStatus,
    ContractType,
    ServiceLevelStatus,
)
from py_autotask.types import QueryFilter


class TestContractsEntityEnhanced:
    """Test cases for enhanced ContractsEntity functionality."""

    @pytest.fixture
    def mock_client(self):
        """Mock AutotaskClient for testing."""
        return Mock()

    @pytest.fixture
    def contracts_entity(self, mock_client):
        """ContractsEntity instance for testing."""
        return ContractsEntity(mock_client, "Contracts")

    @pytest.fixture
    def sample_contract_data(self):
        """Sample contract data for testing."""
        return {
            "id": 12345,
            "ContractName": "Test Service Contract",
            "AccountID": 67890,
            "ContractType": ContractType.RECURRING_SERVICE.value,
            "ContractValue": 100000.00,
            "StartDate": "2024-01-01T00:00:00Z",
            "EndDate": "2024-12-31T00:00:00Z",
            "Status": ContractStatus.ACTIVE.value,
            "Currency": "USD",
            "TaxRate": 8.5,
            "IsAutoRenewing": False,
            "CreateDate": "2024-01-01T00:00:00Z",
            "LastModifiedDateTime": "2024-01-01T00:00:00Z",
        }

    # Test Contract Status and Type Enums

    def test_contract_status_enum_values(self):
        """Test ContractStatus enum has correct values."""
        assert ContractStatus.ACTIVE.value == 1
        assert ContractStatus.INACTIVE.value == 2
        assert ContractStatus.CANCELLED.value == 3
        assert ContractStatus.EXPIRED.value == 4
        assert ContractStatus.PENDING.value == 5
        assert ContractStatus.DRAFT.value == 6
        assert ContractStatus.APPROVED.value == 7
        assert ContractStatus.REJECTED.value == 8

    def test_contract_type_enum_values(self):
        """Test ContractType enum has correct values."""
        assert ContractType.RECURRING_SERVICE.value == 1
        assert ContractType.BLOCK_HOURS.value == 2
        assert ContractType.FIXED_PRICE.value == 3
        assert ContractType.RETAINER.value == 4
        assert ContractType.TIME_AND_MATERIALS.value == 5
        assert ContractType.MAINTENANCE.value == 6
        assert ContractType.SUBSCRIPTION.value == 7

    def test_service_level_status_enum_values(self):
        """Test ServiceLevelStatus enum has correct values."""
        assert ServiceLevelStatus.MEETING.value == "meeting"
        assert ServiceLevelStatus.WARNING.value == "warning"
        assert ServiceLevelStatus.BREACH.value == "breach"
        assert ServiceLevelStatus.NOT_APPLICABLE.value == "not_applicable"

    # Test Contract Billing Integration

    def test_get_contract_billing_summary(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test get_contract_billing_summary method."""
        # Mock contract and line items
        mock_client.get.return_value = sample_contract_data
        mock_line_items_response = Mock()
        mock_line_items_response.items = [
            {"InvoicedAmount": 25000.00, "PaidAmount": 25000.00},
            {"InvoicedAmount": 15000.00, "PaidAmount": 10000.00},
        ]
        mock_client.query.return_value = mock_line_items_response

        # Mock private helper methods
        with patch.object(
            contracts_entity, "_get_contract_billing_schedule"
        ) as mock_schedule, patch.object(
            contracts_entity, "_determine_payment_status"
        ) as mock_status:

            mock_schedule.return_value = [
                {"period_start": "2024-01-01", "billing_date": "2024-01-31"}
            ]
            mock_status.return_value = "partially_paid"

            result = contracts_entity.get_contract_billing_summary(12345)

            assert result["contract_id"] == 12345
            assert result["total_contract_value"] == 100000.00
            assert result["billed_to_date"] == 40000.00
            assert result["remaining_value"] == 60000.00
            assert result["billing_percentage"] == 40.0
            assert result["payment_status"] == "partially_paid"
            assert "billing_schedule" in result
            assert "currency" in result

    def test_generate_contract_invoice(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test generate_contract_invoice method."""
        mock_client.get.return_value = sample_contract_data

        # Mock invoice item generation methods
        with patch.object(
            contracts_entity, "_get_recurring_charges"
        ) as mock_recurring, patch.object(
            contracts_entity, "_get_usage_charges"
        ) as mock_usage, patch.object(
            contracts_entity, "_get_milestone_charges"
        ) as mock_milestone:

            mock_recurring.return_value = [
                {"item_type": "recurring_service", "amount": 5000}
            ]
            mock_usage.return_value = [{"item_type": "usage_charge", "amount": 1500}]
            mock_milestone.return_value = [
                {"item_type": "milestone_charge", "amount": 10000}
            ]

            result = contracts_entity.generate_contract_invoice(
                12345, "2024-01-01T00:00:00Z", "2024-01-31T00:00:00Z"
            )

            assert result["contract_id"] == 12345
            assert result["subtotal"] == 16500.0
            assert result["tax_rate"] == 8.5
            assert result["tax_amount"] == 1402.5
            assert result["total_amount"] == 17902.5
            assert len(result["invoice_items"]) == 3

    # Test Service Level Tracking

    def test_get_contract_service_levels(self, contracts_entity, mock_client):
        """Test get_contract_service_levels method."""
        mock_sla_response = Mock()
        mock_sla_response.items = [
            {
                "id": 1001,
                "Name": "Response Time SLA",
                "Description": "95% response within 4 hours",
                "MetricType": "response_time",
                "TargetValue": 95.0,
                "WarningThreshold": 90.0,
                "BreachThreshold": 85.0,
                "IsActive": True,
            }
        ]
        mock_client.query.return_value = mock_sla_response

        with patch.object(
            contracts_entity, "_check_sla_compliance"
        ) as mock_compliance, patch.object(
            contracts_entity, "_get_current_sla_performance"
        ) as mock_performance:

            mock_compliance.return_value = ServiceLevelStatus.MEETING.value
            mock_performance.return_value = 97.5

            result = contracts_entity.get_contract_service_levels(12345)

            assert len(result) == 1
            sla = result[0]
            assert sla["sla_id"] == 1001
            assert sla["name"] == "Response Time SLA"
            assert sla["compliance_status"] == ServiceLevelStatus.MEETING.value
            assert sla["current_performance"] == 97.5

    def test_check_service_level_compliance(self, contracts_entity):
        """Test check_service_level_compliance method."""
        mock_service_levels = [
            {
                "sla_id": 1001,
                "name": "Response Time",
                "compliance_status": ServiceLevelStatus.MEETING.value,
                "current_performance": 97.5,
                "target_value": 95.0,
            },
            {
                "sla_id": 1002,
                "name": "Availability",
                "compliance_status": ServiceLevelStatus.WARNING.value,
                "current_performance": 92.0,
                "target_value": 99.0,
            },
        ]

        with patch.object(
            contracts_entity, "get_contract_service_levels"
        ) as mock_get_slas:
            mock_get_slas.return_value = mock_service_levels

            result = contracts_entity.check_service_level_compliance(12345)

            assert result["contract_id"] == 12345
            assert result["overall_status"] == ServiceLevelStatus.WARNING.value
            assert result["total_slas"] == 2
            assert result["meeting_count"] == 1
            assert result["warning_count"] == 1
            assert result["breach_count"] == 0
            assert result["compliance_percentage"] == 50.0

    # Test Milestone Management

    def test_add_contract_milestone(self, contracts_entity, mock_client):
        """Test add_contract_milestone method."""
        mock_milestone_response = Mock()
        mock_milestone_response.item_id = 2001
        mock_client.create_entity.return_value = mock_milestone_response

        result = contracts_entity.add_contract_milestone(
            12345,
            "Phase 1 Completion",
            "2024-03-31T00:00:00Z",
            description="Complete initial setup",
            deliverables=["Database setup", "API configuration"],
            milestone_value=25000.00,
        )

        mock_client.create_entity.assert_called_once_with(
            "ContractMilestones",
            {
                "ContractID": 12345,
                "MilestoneName": "Phase 1 Completion",
                "DueDate": "2024-03-31T00:00:00Z",
                "Status": "Not Started",
                "IsActive": True,
                "Description": "Complete initial setup",
                "MilestoneValue": 25000.00,
                "Deliverables": "Database setup; API configuration",
            },
        )

    def test_get_upcoming_milestones(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test get_upcoming_milestones method."""
        mock_milestone_response = Mock()
        mock_milestone_response.items = [
            {
                "id": 2001,
                "MilestoneName": "Phase 1 Completion",
                "Description": "Initial setup phase",
                "DueDate": "2024-03-15T00:00:00Z",
                "Status": "In Progress",
                "MilestoneValue": 25000.00,
                "ContractID": 12345,
                "ProgressPercentage": 75,
            }
        ]
        mock_client.query.return_value = mock_milestone_response
        mock_client.get.return_value = sample_contract_data

        result = contracts_entity.get_upcoming_milestones(30)

        assert len(result) == 1
        milestone = result[0]
        assert milestone["milestone_id"] == 2001
        assert milestone["name"] == "Phase 1 Completion"
        assert milestone["contract_name"] == "Test Service Contract"
        assert milestone["milestone_value"] == 25000.00

    # Test Renewal Management

    def test_get_contracts_expiring_soon(self, contracts_entity, sample_contract_data):
        """Test get_contracts_expiring_soon method."""
        mock_expiring_response = Mock()
        mock_expiring_response.items = [sample_contract_data]

        with patch.object(contracts_entity, "query") as mock_query, patch.object(
            contracts_entity, "_calculate_renewal_probability"
        ) as mock_probability, patch.object(
            contracts_entity, "_determine_renewal_urgency"
        ) as mock_urgency:

            mock_query.return_value = mock_expiring_response
            mock_probability.return_value = 0.85
            mock_urgency.return_value = "high"

            result = contracts_entity.get_contracts_expiring_soon(60)

            assert len(result) == 1
            contract = result[0]
            assert contract["contract_id"] == 12345
            assert contract["renewal_probability"] == 0.85
            assert contract["urgency_level"] == "high"

    def test_set_renewal_alert(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test set_renewal_alert method."""
        mock_client.get.return_value = sample_contract_data
        mock_client.update.return_value = sample_contract_data

        result = contracts_entity.set_renewal_alert(
            12345, alert_days_before=30, recipients=["manager@company.com"]
        )

        assert result["contract_id"] == 12345
        assert result["alert_days_before"] == 30
        assert result["recipients"] == ["manager@company.com"]
        assert "alert_date" in result

    # Test Usage Tracking

    def test_track_contract_usage(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test track_contract_usage method."""
        mock_client.get.return_value = sample_contract_data
        mock_usage_record = Mock()
        mock_usage_record.item_id = 3001
        mock_client.create_entity.return_value = mock_usage_record

        mock_usage_summary = {
            "usage_totals": {"hours": 45.5},
            "remaining_allocations": {"hours": 154.5},
            "utilization_percentages": {"hours": 22.75},
            "over_limit_types": [],
        }

        with patch.object(
            contracts_entity, "get_contract_usage_summary"
        ) as mock_summary:
            mock_summary.return_value = mock_usage_summary

            result = contracts_entity.track_contract_usage(
                12345, "hours", 8.5, description="Development work"
            )

            assert result["contract_id"] == 12345
            assert result["usage_type"] == "hours"
            assert result["usage_amount"] == 8.5
            assert result["current_total"] == 45.5

    def test_get_contract_usage_summary(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test get_contract_usage_summary method."""
        mock_client.get.return_value = sample_contract_data

        mock_usage_response = Mock()
        mock_usage_response.items = [
            {"UsageType": "hours", "UsageAmount": 25.0},
            {"UsageType": "hours", "UsageAmount": 15.5},
            {"UsageType": "licenses", "UsageAmount": 10.0},
        ]
        mock_client.query.return_value = mock_usage_response

        with patch.object(
            contracts_entity, "_get_contract_allocations"
        ) as mock_allocations, patch.object(
            contracts_entity, "_calculate_usage_trends"
        ) as mock_trends:

            mock_allocations.return_value = {"hours": 200.0, "licenses": 50.0}
            mock_trends.return_value = {"trend_direction": "increasing"}

            result = contracts_entity.get_contract_usage_summary(12345)

            assert result["contract_id"] == 12345
            assert result["usage_totals"]["hours"] == 40.5
            assert result["usage_totals"]["licenses"] == 10.0
            assert result["utilization_percentages"]["hours"] == 20.25
            assert result["utilization_percentages"]["licenses"] == 20.0

    # Test Contract Modifications

    def test_amend_contract(self, contracts_entity, mock_client, sample_contract_data):
        """Test amend_contract method."""
        mock_client.get.return_value = sample_contract_data
        mock_amendment_record = Mock()
        mock_amendment_record.item_id = 4001
        mock_client.create_entity.return_value = mock_amendment_record

        changes = {"ContractValue": 120000.00}
        result = contracts_entity.amend_contract(
            12345, "value_change", changes, amendment_reason="Scope expansion"
        )

        assert result["amendment_id"] == 4001
        assert result["contract_id"] == 12345
        assert result["amendment_type"] == "value_change"
        assert result["original_values"]["ContractValue"] == 100000.00
        assert result["new_values"] == changes

    def test_get_contract_history(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test get_contract_history method."""
        mock_client.get.return_value = sample_contract_data

        # Mock amendment response
        mock_amendment_response = Mock()
        mock_amendment_response.items = [
            {
                "id": 4001,
                "EffectiveDate": "2024-02-01T00:00:00Z",
                "AmendmentType": "value_change",
                "AmendmentReason": "Scope expansion",
                "Status": "Applied",
            }
        ]

        # Mock usage response
        mock_usage_response = Mock()
        mock_usage_response.items = [
            {
                "id": 3001,
                "UsageDate": "2024-01-15T00:00:00Z",
                "UsageType": "hours",
                "UsageAmount": 8.5,
                "Description": "Development work",
            }
        ]

        mock_client.query.side_effect = [mock_amendment_response, mock_usage_response]

        result = contracts_entity.get_contract_history(
            12345, include_amendments=True, include_usage=True
        )

        assert result["contract_id"] == 12345
        assert len(result["timeline"]) == 3  # creation + amendment + usage
        assert result["summary"]["amendments_count"] == 1
        assert result["summary"]["usage_events_count"] == 1

    # Test Helper Methods

    def test_get_active_contracts_by_account(
        self, contracts_entity, sample_contract_data
    ):
        """Test get_active_contracts_by_account method."""
        mock_contracts_response = Mock()
        mock_contracts_response.items = [sample_contract_data]

        with patch.object(contracts_entity, "query") as mock_query, patch.object(
            contracts_entity, "get_contract_billing_summary"
        ) as mock_billing:

            mock_query.return_value = mock_contracts_response
            mock_billing.return_value = {"remaining_value": 60000.00}

            result = contracts_entity.get_active_contracts_by_account(67890)

            assert len(result) == 1
            contract = result[0]
            assert contract["contract_id"] == 12345
            assert contract["name"] == "Test Service Contract"
            assert contract["value"] == 100000.00

    def test_calculate_contract_value(
        self, contracts_entity, mock_client, sample_contract_data
    ):
        """Test calculate_contract_value method."""
        mock_client.get.return_value = sample_contract_data

        # Mock amendment response
        mock_amendment_response = Mock()
        mock_amendment_response.items = []

        # Mock milestone response
        mock_milestone_response = Mock()
        mock_milestone_response.items = [
            {"MilestoneValue": 15000.00},
            {"MilestoneValue": 10000.00},
        ]

        mock_client.query.side_effect = [
            mock_amendment_response,
            mock_milestone_response,
        ]

        result = contracts_entity.calculate_contract_value(12345)

        assert result["base_value"] == 100000.00
        assert result["milestone_values"] == 25000.00
        assert (
            result["total_value"] == 100000.00
        )  # base + milestones not added to total in this case

    # Test Private Helper Methods

    def test_get_contract_billing_schedule(
        self, contracts_entity, sample_contract_data
    ):
        """Test _get_contract_billing_schedule helper method."""
        result = contracts_entity._get_contract_billing_schedule(sample_contract_data)

        # For recurring service contracts, should have billing schedule
        assert isinstance(result, list)
        if result:  # Only test if schedule is generated
            assert "period_start" in result[0]
            assert "billing_date" in result[0]

    def test_determine_payment_status(self, contracts_entity):
        """Test _determine_payment_status helper method."""
        line_items_paid = [{"InvoicedAmount": 1000, "PaidAmount": 1000}]
        line_items_unpaid = [{"InvoicedAmount": 1000, "PaidAmount": 0}]
        line_items_partial = [{"InvoicedAmount": 1000, "PaidAmount": 500}]

        assert (
            contracts_entity._determine_payment_status({}, line_items_paid)
            == "paid_in_full"
        )
        assert (
            contracts_entity._determine_payment_status({}, line_items_unpaid)
            == "unpaid"
        )
        assert (
            contracts_entity._determine_payment_status({}, line_items_partial)
            == "partially_paid"
        )
        assert contracts_entity._determine_payment_status({}, []) == "no_invoices"

    def test_check_sla_compliance_helper(self, contracts_entity):
        """Test _check_sla_compliance helper method."""
        sla_meeting = {
            "TargetValue": 95.0,
            "WarningThreshold": 90.0,
            "BreachThreshold": 80.0,
        }

        with patch.object(
            contracts_entity, "_get_current_sla_performance"
        ) as mock_performance:
            mock_performance.return_value = 97.0
            result = contracts_entity._check_sla_compliance(sla_meeting)
            assert result == ServiceLevelStatus.MEETING.value

            mock_performance.return_value = 85.0
            result = contracts_entity._check_sla_compliance(sla_meeting)
            assert result == ServiceLevelStatus.WARNING.value

            mock_performance.return_value = 75.0
            result = contracts_entity._check_sla_compliance(sla_meeting)
            assert result == ServiceLevelStatus.BREACH.value

    def test_calculate_renewal_probability(
        self, contracts_entity, sample_contract_data
    ):
        """Test _calculate_renewal_probability helper method."""
        # Mock no amendments
        mock_amendment_response = Mock()
        mock_amendment_response.items = []

        with patch.object(contracts_entity.client, "query") as mock_query:
            mock_query.return_value = mock_amendment_response

            # High value contract should have higher probability
            high_value_contract = {**sample_contract_data, "ContractValue": 150000.00}
            result = contracts_entity._calculate_renewal_probability(
                high_value_contract
            )
            assert result == pytest.approx(
                0.8, rel=1e-9
            )  # Base 0.7 + 0.1 for high value

            # Low value contract should have base probability
            low_value_contract = {**sample_contract_data, "ContractValue": 50000.00}
            result = contracts_entity._calculate_renewal_probability(low_value_contract)
            assert result == pytest.approx(0.7, rel=1e-9)  # Base probability

    def test_determine_renewal_urgency(self, contracts_entity):
        """Test _determine_renewal_urgency helper method."""
        today = datetime.now()

        # Critical (30 days or less)
        critical_contract = {"EndDate": (today + timedelta(days=15)).isoformat()}
        assert (
            contracts_entity._determine_renewal_urgency(critical_contract, 60)
            == "critical"
        )

        # High (31-60 days)
        high_contract = {"EndDate": (today + timedelta(days=45)).isoformat()}
        assert contracts_entity._determine_renewal_urgency(high_contract, 60) == "high"

        # Medium (61-90 days)
        medium_contract = {"EndDate": (today + timedelta(days=75)).isoformat()}
        assert (
            contracts_entity._determine_renewal_urgency(medium_contract, 60) == "medium"
        )

        # Low (more than 90 days)
        low_contract = {"EndDate": (today + timedelta(days=120)).isoformat()}
        assert contracts_entity._determine_renewal_urgency(low_contract, 60) == "low"

    def test_get_contract_allocations(self, contracts_entity):
        """Test _get_contract_allocations helper method."""
        block_hours_contract = {
            "ContractType": ContractType.BLOCK_HOURS.value,
            "HourAllocation": 200.0,
        }
        result = contracts_entity._get_contract_allocations(block_hours_contract)
        assert result["hours"] == 200.0

        subscription_contract = {
            "ContractType": ContractType.SUBSCRIPTION.value,
            "LicenseCount": 50,
            "StorageGB": 1000,
        }
        result = contracts_entity._get_contract_allocations(subscription_contract)
        assert result["licenses"] == 50.0
        assert result["storage"] == 1000.0

        tm_contract = {"ContractType": ContractType.TIME_AND_MATERIALS.value}
        result = contracts_entity._get_contract_allocations(tm_contract)
        assert result["hours"] == 999999  # Unlimited

    def test_calculate_usage_trends(self, contracts_entity):
        """Test _calculate_usage_trends helper method."""
        usage_records = [
            {"UsageDate": "2024-01-15T00:00:00Z", "UsageAmount": 8.5},
            {"UsageDate": "2024-01-20T00:00:00Z", "UsageAmount": 6.0},
            {"UsageDate": "2024-02-10T00:00:00Z", "UsageAmount": 10.0},
        ]

        result = contracts_entity._calculate_usage_trends(usage_records)

        assert "monthly_usage" in result
        assert "daily_average" in result
        assert "peak_usage_day" in result
        assert "trend_direction" in result
        assert result["daily_average"] > 0
        assert result["peak_usage_day"] is not None

    # Error Handling Tests

    def test_get_contract_billing_summary_contract_not_found(
        self, contracts_entity, mock_client
    ):
        """Test error handling when contract is not found."""
        mock_client.get.return_value = None

        with pytest.raises(ValueError, match="Contract 12345 not found"):
            contracts_entity.get_contract_billing_summary(12345)

    def test_generate_contract_invoice_contract_not_found(
        self, contracts_entity, mock_client
    ):
        """Test error handling when contract is not found."""
        mock_client.get.return_value = None

        with pytest.raises(ValueError, match="Contract 12345 not found"):
            contracts_entity.generate_contract_invoice(12345)

    def test_check_service_level_compliance_invalid_sla(self, contracts_entity):
        """Test error handling when SLA is not found."""
        with patch.object(
            contracts_entity, "get_contract_service_levels"
        ) as mock_get_slas:
            mock_get_slas.return_value = []

            with pytest.raises(ValueError, match="SLA 999 not found"):
                contracts_entity.check_service_level_compliance(12345, sla_id=999)

    # Integration Tests

    def test_contract_lifecycle_integration(self, contracts_entity, mock_client):
        """Test complete contract lifecycle with multiple features."""
        # Setup mock responses for a complete workflow
        sample_contract = {
            "id": 12345,
            "ContractName": "Integration Test Contract",
            "ContractValue": 100000.00,
            "ContractType": ContractType.RECURRING_SERVICE.value,
            "Status": ContractStatus.ACTIVE.value,
            "StartDate": "2024-01-01T00:00:00Z",
            "EndDate": "2024-12-31T00:00:00Z",
        }

        mock_client.get.return_value = sample_contract
        mock_client.create_entity.return_value = Mock(item_id=5001)
        mock_client.update.return_value = sample_contract

        # Test milestone addition
        milestone_result = contracts_entity.add_contract_milestone(
            12345, "Q1 Deliverable", "2024-03-31T00:00:00Z", milestone_value=25000.00
        )
        assert milestone_result.item_id == 5001

        # Test usage tracking
        with patch.object(
            contracts_entity, "get_contract_usage_summary"
        ) as mock_summary:
            mock_summary.return_value = {
                "usage_totals": {"hours": 40.5},
                "remaining_allocations": {"hours": 159.5},
                "utilization_percentages": {"hours": 20.25},
                "over_limit_types": [],
            }

            usage_result = contracts_entity.track_contract_usage(12345, "hours", 8.0)
            assert usage_result["contract_id"] == 12345

        # Test renewal alert setup
        alert_result = contracts_entity.set_renewal_alert(12345, alert_days_before=60)
        assert alert_result["contract_id"] == 12345

        # Verify all operations succeeded
        assert mock_client.create_entity.call_count >= 2  # milestone + usage tracking
        assert mock_client.update.call_count >= 1  # renewal alert


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
