"""
Comprehensive tests for enhanced ContractsEntity.

Tests all PSA features including billing, service tracking, milestones, renewals, usage tracking, amendments, and validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from py_autotask.entities.contracts import (
    ContractsEntity, ContractTypes, ContractStatuses, BillingMethods, ServiceTypes, )
from py_autotask.types import QueryFilter


class TestContractConstants:
    """Test contract constant definitions."""

    def test_contract_types_constants(self):
        """Test that all contract type constants are defined."""
        assert ContractTypes.RECURRING_SERVICE == 1
        assert ContractTypes.FIXED_PRICE == 2
        assert ContractTypes.TIME_AND_MATERIALS == 3
        assert ContractTypes.MILESTONE == 4
        assert ContractTypes.SUBSCRIPTION == 5
        assert ContractTypes.MAINTENANCE == 6
        assert ContractTypes.RETAINER == 7

    def test_contract_statuses_constants(self):
        """Test that all contract status constants are defined."""
        assert ContractStatuses.ACTIVE == 1
        assert ContractStatuses.INACTIVE == 0
        assert ContractStatuses.CANCELLED == 2
        assert ContractStatuses.EXPIRED == 3
        assert ContractStatuses.ON_HOLD == 4
        assert ContractStatuses.PENDING_APPROVAL == 5
        assert ContractStatuses.DRAFT == 6

    def test_billing_methods_constants(self):
        """Test that all billing method constants are defined."""
        assert BillingMethods.FIXED_PRICE == 1
        assert BillingMethods.TIME_AND_MATERIALS == 2
        assert BillingMethods.MILESTONE_BILLING == 3
        assert BillingMethods.RECURRING_BILLING == 4
        assert BillingMethods.USAGE_BASED == 5
        assert BillingMethods.RETAINER == 6

    def test_service_types_constants(self):
        """Test that all service type constants are defined."""
        assert ServiceTypes.PROFESSIONAL_SERVICES == 1
        assert ServiceTypes.MANAGED_SERVICES == 2
        assert ServiceTypes.SUPPORT_SERVICES == 3
        assert ServiceTypes.CONSULTING == 4
        assert ServiceTypes.IMPLEMENTATION == 5
        assert ServiceTypes.MAINTENANCE == 6
        assert ServiceTypes.TRAINING == 7


class TestBillingAndInvoicing:
    """Test billing and invoicing integration methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_generate_invoice_success(self):
        """Test successful invoice generation."""
        # Mock contract exists
        self.contracts.get = MagicMock(return_value = {"id": 123, "ContractName": "Test Contract"})

        # Mock invoice creation
        self.client.create.return_value = {"success": True, "id": 456}

        period = {
            "start_date": "2024-01-01T00: 00: 00Z", "end_date": "2024-01-31T23: 59: 59Z"
        }

        result = self.contracts.generate_invoice(123, period)

        assert result["success"] is True
        self.client.create.assert_called_once()

        # Check that the invoice data includes correct fields
        call_args = self.client.create.call_args[0]
        assert call_args[0] == "Invoices"
        invoice_data = call_args[1]
        assert invoice_data["contractID"] == 123
        assert invoice_data["billingPeriodStart"] == period["start_date"]
        assert invoice_data["billingPeriodEnd"] == period["end_date"]

    def test_generate_invoice_contract_not_found(self):
        """Test invoice generation with non-existent contract."""
        self.contracts.get = MagicMock(return_value = None)

        with pytest.raises(ValueError, match = "Contract 123 not found"):
            self.contracts.generate_invoice(123)

    def test_generate_invoice_default_period(self):
        """Test invoice generation with default period."""
        self.contracts.get = MagicMock(return_value = {"id": 123})
        self.client.create.return_value = {"success": True}

        result = self.contracts.generate_invoice(123)

        # Check that default period was used
        call_args = self.client.create.call_args[0][1]
        assert "billingPeriodStart" in call_args
        assert "billingPeriodEnd" in call_args

    def test_get_billing_history(self):
        """Test getting billing history for a contract."""
        mock_invoices = [
            {"id": 1, "amount": 1000, "invoiceDate": "2024-01-01"}, {"id": 2, "amount": 1500, "invoiceDate": "2024-02-01"}, ]
        self.client.query.return_value = mock_invoices

        result = self.contracts.get_billing_history(123)

        assert result == mock_invoices
        self.client.query.assert_called_once_with("Invoices", filters = [
            QueryFilter(field = "contractID", op = "eq", value = 123)
        ], max_records = None)

    def test_calculate_contract_value(self):
        """Test contract value calculation."""
        # Mock contract
        mock_contract = {
            "id": 123, "ContractValue": 50000
        }
        self.contracts.get = MagicMock(return_value = mock_contract)

        # Mock billing history
        mock_invoices = [
            {"amount": 10000, "status": "paid", "invoiceDate": "2024-01-01"}, {"amount": 15000, "status": "outstanding", "invoiceDate": "2024-02-01"}, ]
        self.contracts.get_billing_history = MagicMock(return_value = mock_invoices)

        # Mock pending time entries
        self.client.query.return_value = [
            {"billingAmount": 5000}
        ]

        result = self.contracts.calculate_contract_value(123)

        assert result["contract_id"] == 123
        assert result["contract_value"] == 50000
        assert result["billed_to_date"] == 25000
        assert result["remaining_value"] == 25000
        assert result["billing_utilization"] == 50.0
        assert result["payment_status"]["paid"] == 10000
        assert result["payment_status"]["outstanding"] == 15000
        assert result["pending_billing"] == 5000


class TestServiceLevelTracking:
    """Test service level tracking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_track_service_delivery_success(self):
        """Test successful service delivery tracking."""
        service_data = {
            "service_type": "support", "delivery_date": "2024-01-01T12: 00: 00Z", "metrics": {"response_time": 30, "resolution_time": 120}, "sla_target": 60, "actual_performance": 50
        }

        self.client.create.return_value = {"success": True, "id": 789}

        result = self.contracts.track_service_delivery(123, service_data)

        assert result["success"] is True

        # Verify call was made with correct arguments (except timestamp)
        self.client.create.assert_called_once()
        args, kwargs = self.client.create.call_args
        assert args[0] == "ServiceDeliveryRecords"

        expected_data = {
            "contractID": 123, "serviceType": "support", "deliveryDate": "2024-01-01T12: 00: 00Z", "metrics": {"response_time": 30, "resolution_time": 120}, "sla_target": 60, "actual_performance": 50
        }

        # Check all fields except recordedDate
        for key, value in expected_data.items():
            assert args[1][key] == value

        # Check recordedDate is close to now
        recorded_time = datetime.fromisoformat(args[1]["recordedDate"].replace('Z', '+00: 00'))
        now = datetime.now()
        time_diff = abs((recorded_time.replace(tzinfo = None) - now).total_seconds())
        assert time_diff < 2  # Within 2 seconds

    def test_track_service_delivery_missing_fields(self):
        """Test service delivery tracking with missing required fields."""
        incomplete_data = {
            "service_type": "support"
            # Missing required fields: delivery_date, metrics
        }

        with pytest.raises(ValueError, match = "Missing required fields"):
            self.contracts.track_service_delivery(123, incomplete_data)

    def test_get_service_metrics(self):
        """Test getting service metrics for a contract."""
        mock_records = [
            {
                "serviceType": "support", "slaTarget": 60, "actualPerformance": 45
            }, {
                "serviceType": "support", "slaTarget": 60, "actualPerformance": 70
            }, {
                "serviceType": "maintenance", "slaTarget": 30, "actualPerformance": 25
            }
        ]
        self.client.query.return_value = mock_records

        result = self.contracts.get_service_metrics(123)

        assert result["contract_id"] == 123
        assert result["total_services"] == 3
        assert "support" in result["by_service_type"]
        assert "maintenance" in result["by_service_type"]
        assert result["sla_compliance"]["total_slas"] == 3
        assert result["sla_compliance"]["met_slas"] == 1  # Only maintenance met SLA
        assert result["sla_compliance"]["compliance_rate"] == pytest.approx(33.33, abs = 0.1)

    def test_check_sla_compliance(self):
        """Test SLA compliance checking."""
        mock_contract = {"id": 123, "ContractName": "Test Contract"}
        self.contracts.get = MagicMock(return_value = mock_contract)

        mock_metrics = {
            "sla_compliance": {"compliance_rate": 85}, "by_service_type": {
                "support": {"sla_compliance": 80}, "maintenance": {"sla_compliance": 95}
            }
        }
        self.contracts.get_service_metrics = MagicMock(return_value = mock_metrics)

        result = self.contracts.check_sla_compliance(123)

        assert result["contract_id"] == 123
        assert result["overall_compliance"] == 85
        assert result["compliant"] is False  # Below 95%
        assert len(result["violations"]) == 2  # Overall and support violations
        assert len(result["recommendations"]) > 0


class TestMilestoneManagement:
    """Test milestone management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_add_milestone_success(self):
        """Test successful milestone addition."""
        milestone_data = {
            "title": "Phase 1 Completion", "description": "Complete initial development phase", "due_date": "2024-06-01T00: 00: 00Z", "value": 25000
        }

        self.client.create.return_value = {"success": True, "id": 456}

        result = self.contracts.add_milestone(123, milestone_data)

        assert result["success"] is True

        # Verify call was made with correct arguments (except timestamp)
        self.client.create.assert_called_once()
        args, kwargs = self.client.create.call_args
        assert args[0] == "ContractMilestones"

        expected_data = {
            "contractID": 123, "title": "Phase 1 Completion", "description": "Complete initial development phase", "dueDate": "2024-06-01T00: 00: 00Z", "value": 25000, "status": "pending", "progress": 0
        }

        # Check all fields except createdDate
        for key, value in expected_data.items():
            assert args[1][key] == value

        # Check createdDate is close to now
        created_time = datetime.fromisoformat(args[1]["createdDate"].replace('Z', '+00: 00'))
        now = datetime.now()
        time_diff = abs((created_time.replace(tzinfo = None) - now).total_seconds())
        assert time_diff < 2  # Within 2 seconds

    def test_add_milestone_missing_fields(self):
        """Test milestone addition with missing required fields."""
        incomplete_data = {
            "title": "Phase 1"
            # Missing: description, due_date, value
        }

        with pytest.raises(ValueError, match = "Missing required fields"):
            self.contracts.add_milestone(123, incomplete_data)

    def test_update_milestone_progress_completion(self):
        """Test updating milestone progress to completion."""
        mock_milestone = {"id": 456, "status": "in_progress"}
        self.client.get.return_value = mock_milestone
        self.client.update.return_value = {"success": True}

        result = self.contracts.update_milestone_progress(456, 100, "Completed ahead of schedule")

        assert result["success"] is True

        # Check update data
        call_args = self.client.update.call_args[0]
        assert call_args[0] == "ContractMilestones"
        assert call_args[1] == 456
        update_data = call_args[2]
        assert update_data["progress"] == 100
        assert update_data["status"] == "completed"
        assert "completedDate" in update_data
        assert update_data["progressNotes"] == "Completed ahead of schedule"

    def test_update_milestone_progress_invalid_range(self):
        """Test updating milestone progress with invalid percentage."""
        with pytest.raises(ValueError, match = "Progress must be between 0 and 100"):
            self.contracts.update_milestone_progress(456, 150)

    def test_get_upcoming_milestones(self):
        """Test getting upcoming milestones."""
        mock_milestones = [
            {
                "id": 1, "title": "Phase 1", "dueDate": "2024-03-15T00: 00: 00Z", "status": "pending"
            }, {
                "id": 2, "title": "Phase 2", "dueDate": "2024-04-01T00: 00: 00Z", "status": "in_progress"
            }
        ]
        self.client.query.return_value = mock_milestones

        result = self.contracts.get_upcoming_milestones(123, days_ahead = 60)

        assert len(result) == 2
        assert result[0]["title"] == "Phase 1"  # Should be sorted by due date

    def test_get_milestone_analytics(self):
        """Test milestone analytics generation."""
        now = datetime.now()
        past_date = (now - timedelta(days = 10)).isoformat()
        future_date = (now + timedelta(days = 10)).isoformat()

        mock_milestones = [
            {
                "id": 1, "status": "completed", "value": 10000, "dueDate": past_date, "startedDate": (now - timedelta(days = 20)).isoformat(), "completedDate": past_date
            }, {
                "id": 2, "status": "pending", "value": 15000, "dueDate": future_date
            }, {
                "id": 3, "status": "overdue", "value": 5000, "dueDate": (now - timedelta(days = 5)).isoformat()
            }
        ]
        self.client.query.return_value = mock_milestones

        result = self.contracts.get_milestone_analytics(123)

        assert result["contract_id"] == 123
        assert result["total_milestones"] == 3
        assert result["by_status"]["completed"] == 1
        assert result["by_status"]["pending"] == 1
        assert result["total_value"] == 30000
        assert result["completed_value"] == 10000
        assert result["completion_rate"] == pytest.approx(33.33, abs = 0.1)
        assert result["value_realization"] == pytest.approx(33.33, abs = 0.1)


class TestRenewalManagement:
    """Test renewal management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_schedule_renewal_alert_success(self):
        """Test successful renewal alert scheduling."""
        alert_data = {
            "alert_date": "2024-05-01T00: 00: 00Z", "alert_type": "email", "recipients": ["manager@company.com", "sales@company.com"], "message": "Contract renewal due in 30 days"
        }

        self.client.create.return_value = {"success": True, "id": 789}

        result = self.contracts.schedule_renewal_alert(123, alert_data)

        assert result["success"] is True

        # Verify call was made with correct arguments (except timestamp)
        self.client.create.assert_called_once()
        args, kwargs = self.client.create.call_args
        assert args[0] == "ContractRenewalAlerts"

        expected_data = {
            "contractID": 123, "alertDate": "2024-05-01T00: 00: 00Z", "alertType": "email", "recipients": ["manager@company.com", "sales@company.com"], "status": "scheduled", "message": "Contract renewal due in 30 days"
        }

        # Check all fields except createdDate
        for key, value in expected_data.items():
            assert args[1][key] == value

        # Check createdDate is close to now
        created_time = datetime.fromisoformat(args[1]["createdDate"].replace('Z', '+00: 00'))
        now = datetime.now()
        time_diff = abs((created_time.replace(tzinfo = None) - now).total_seconds())
        assert time_diff < 2  # Within 2 seconds

    def test_get_expiring_contracts(self):
        """Test getting expiring contracts."""
        future_date = datetime.now() + timedelta(days = 45)

        mock_contracts = [
            {
                "id": 1, "ContractName": "Contract A", "EndDate": future_date.isoformat(), "ContractValue": 50000, "autoRenew": False
            }, {
                "id": 2, "ContractName": "Contract B", "EndDate": (datetime.now() + timedelta(days = 15)).isoformat(), "ContractValue": 100000, "autoRenew": False
            }
        ]
        self.contracts.query = MagicMock(return_value = mock_contracts)

        result = self.contracts.get_expiring_contracts(days_ahead = 60)

        assert len(result) == 2
        # Should be sorted by expiry date (soonest first)
        assert result[0]["days_until_expiry"] < result[1]["days_until_expiry"]
        assert "renewal_priority" in result[0]
        assert "renewal_status" in result[0]

    def test_renew_contract_success(self):
        """Test successful contract renewal."""
        original_contract = {
            "id": 123, "ContractName": "Original Contract", "AccountID": 456, "ContractType": ContractTypes.RECURRING_SERVICE, "EndDate": "2024-03-31T23: 59: 59Z", "ContractValue": 50000
        }
        self.contracts.get = MagicMock(return_value = original_contract)
        self.contracts.create = MagicMock(return_value = {"success": True, "id": 789})
        self.contracts.update = MagicMock(return_value = {"success": True})

        renewal_data = {
            "new_value": 60000
        }

        result = self.contracts.renew_contract(123, renewal_data)

        assert result["success"] is True

        # Check that new contract was created with correct data
        create_call = self.contracts.create.call_args[0][0]
        assert create_call["AccountID"] == 456
        assert create_call["ContractType"] == ContractTypes.RECURRING_SERVICE
        assert create_call["ContractValue"] == 60000
        assert create_call["ParentContractID"] == 123
        assert "Renewal" in create_call["ContractName"]

        # Check that original contract was updated
        self.contracts.update.assert_called_once()

    def test_get_renewal_analytics(self):
        """Test renewal analytics generation."""
        # Mock expiring contracts
        self.contracts.get_expiring_contracts = MagicMock(return_value = [
            {
                "id": 1, "days_until_expiry": 15, "ContractValue": 100000, "renewal_priority": "high"
            }, {
                "id": 2, "days_until_expiry": 45, "ContractValue": 50000, "renewal_priority": "medium"
            }
        ])

        # Mock renewed contracts
        self.contracts.query = MagicMock(return_value = [
            {"ContractValue": 75000}, {"ContractValue": 125000}
        ])

        result = self.contracts.get_renewal_analytics()

        assert "renewal_pipeline" in result
        assert "renewal_performance" in result
        assert result["renewal_pipeline"]["next_30_days"] == 1
        assert result["renewal_pipeline"]["next_60_days"] == 2
        assert result["renewal_pipeline"]["high_priority_renewals"] == 1
        assert result["renewal_performance"]["total_renewed"] == 2


class TestUsageTracking:
    """Test usage tracking functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_track_usage_success(self):
        """Test successful usage tracking."""
        usage_data = {
            "usage_type": "hours", "amount": 40, "period": "week", "date": "2024-01-15T00: 00: 00Z", "unit_cost": 100, "billable": True
        }

        self.client.create.return_value = {"success": True, "id": 456}

        result = self.contracts.track_usage(123, usage_data)

        assert result["success"] is True

        # Verify call was made with correct arguments (except timestamp)
        self.client.create.assert_called_once()
        args, kwargs = self.client.create.call_args
        assert args[0] == "ContractUsageRecords"

        expected_data = {
            "contractID": 123, "usageType": "hours", "amount": 40, "period": "week", "usageDate": "2024-01-15T00: 00: 00Z", "billable": True, "unit_cost": 100
        }

        # Check all fields except recordedDate
        for key, value in expected_data.items():
            assert args[1][key] == value

        # Check recordedDate is close to now
        recorded_time = datetime.fromisoformat(args[1]["recordedDate"].replace('Z', '+00: 00'))
        now = datetime.now()
        time_diff = abs((recorded_time.replace(tzinfo = None) - now).total_seconds())
        assert time_diff < 2  # Within 2 seconds

    def test_check_usage_limits_no_limits(self):
        """Test usage limit checking with no limits defined."""
        mock_contract = {"id": 123, "usageLimits": {}}
        self.contracts.get = MagicMock(return_value = mock_contract)

        result = self.contracts.check_usage_limits(123)

        assert result["contract_id"] == 123
        assert result["has_limits"] is False
        assert "No usage limits defined" in result["message"]

    def test_check_usage_limits_with_violations(self):
        """Test usage limit checking with violations."""
        mock_contract = {
            "id": 123, "usageLimits": {
                "hours": {"amount": 100, "warning_threshold": 0.8}
            }
        }
        self.contracts.get = MagicMock(return_value = mock_contract)

        mock_usage_report = {
            "usage_records": [
                {"usageType": "hours", "amount": 120}  # Over limit
            ]
        }
        self.contracts.get_usage_report = MagicMock(return_value = mock_usage_report)

        result = self.contracts.check_usage_limits(123)

        assert result["has_limits"] is True
        assert len(result["violations"]) == 1
        assert result["violations"][0]["usage_type"] == "hours"
        assert result["violations"][0]["overage"] == 20

    def test_get_usage_report(self):
        """Test usage report generation."""
        mock_records = [
            {
                "usageType": "hours", "amount": 40, "unitCost": 100, "billable": True, "usageDate": "2024-01-01T00: 00: 00Z"
            }, {
                "usageType": "hours", "amount": 30, "unitCost": 100, "billable": False, "usageDate": "2024-01-15T00: 00: 00Z"
            }
        ]
        self.client.query.return_value = mock_records

        result = self.contracts.get_usage_report(123)

        assert result["contract_id"] == 123
        assert result["total_records"] == 2
        assert result["by_type"]["hours"]["total_amount"] == 70
        assert result["by_type"]["hours"]["billable_amount"] == 40
        assert result["by_type"]["hours"]["non_billable_amount"] == 30
        assert result["cost_summary"]["total_cost"] == 7000
        assert result["cost_summary"]["billable_cost"] == 4000

    def test_get_usage_analytics(self):
        """Test usage analytics generation."""
        mock_usage_report = {
            "by_type": {"hours": {"total_amount": 100, "total_cost": 10000}}, "total_usage": {"hours": 100}, "cost_summary": {"total_cost": 10000, "billable_cost": 8000}, "by_period": {
                "2024-01": {"total_cost": 4000}, "2024-02": {"total_cost": 6000}
            }
        }
        self.contracts.get_usage_report = MagicMock(return_value = mock_usage_report)

        mock_limits = {"has_limits": False}
        self.contracts.check_usage_limits = MagicMock(return_value = mock_limits)

        result = self.contracts.get_usage_analytics(123)

        assert result["contract_id"] == 123
        assert result["summary"]["total_cost"] == 10000
        assert result["summary"]["billable_percentage"] == 80
        assert result["trends"]["monthly_growth"]["2024-02"] == 50  # 50% growth


class TestContractModifications:
    """Test contract modification and amendment functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_add_amendment_success(self):
        """Test successful amendment addition."""
        mock_contract = {"id": 123, "ContractName": "Test Contract"}
        self.contracts.get = MagicMock(return_value = mock_contract)

        amendment_data = {
            "amendment_type": "value_change", "description": "Increase contract value due to scope expansion", "effective_date": "2024-03-01T00: 00: 00Z", "value_change": 75000
        }

        self.client.create.return_value = {"success": True, "id": 456}

        result = self.contracts.add_amendment(123, amendment_data)

        assert result["success"] is True

        # Verify call was made with correct arguments (except timestamp)
        self.client.create.assert_called_once()
        args, kwargs = self.client.create.call_args
        assert args[0] == "ContractAmendments"

        expected_data = {
            "contractID": 123, "amendmentType": "value_change", "description": "Increase contract value due to scope expansion", "effectiveDate": "2024-03-01T00: 00: 00Z", "status": "pending", "createdBy": "system", "approvalRequired": True, "value_change": 75000
        }

        # Check all fields except createdDate
        for key, value in expected_data.items():
            assert args[1][key] == value

        # Check createdDate is close to now
        created_time = datetime.fromisoformat(args[1]["createdDate"].replace('Z', '+00: 00'))
        now = datetime.now()
        time_diff = abs((created_time.replace(tzinfo = None) - now).total_seconds())
        assert time_diff < 2  # Within 2 seconds

    def test_approve_amendment_success(self):
        """Test successful amendment approval."""
        mock_amendment = {
            "id": 456, "contractID": 123, "amendmentType": "value_change", "valueChange": 75000
        }
        self.client.get.return_value = mock_amendment
        self.client.update.return_value = {"success": True}
        self.contracts._apply_amendment = MagicMock()

        result = self.contracts.approve_amendment(456, 789, "Approved by management")

        assert result["success"] is True

        # Check update call
        update_call = self.client.update.call_args[0]
        assert update_call[0] == "ContractAmendments"
        assert update_call[1] == 456
        update_data = update_call[2]
        assert update_data["status"] == "approved"
        assert update_data["approvedBy"] == 789
        assert update_data["approvalNotes"] == "Approved by management"

        # Check that amendment was applied
        self.contracts._apply_amendment.assert_called_once_with(mock_amendment)

    def test_get_contract_history(self):
        """Test getting complete contract history."""
        mock_contract = {
            "id": 123, "ContractName": "Test Contract", "CreateDate": "2023-01-01T00: 00: 00Z", "Status": ContractStatuses.ACTIVE, "ContractValue": 50000
        }
        self.contracts.get = MagicMock(return_value = mock_contract)

        # Mock amendments
        mock_amendments = [
            {
                "effectiveDate": "2023-06-01T00: 00: 00Z", "amendmentType": "value_change", "description": "Value increase", "status": "approved", "valueChange": 60000
            }
        ]
        self.client.query.return_value = mock_amendments

        # Mock renewals
        mock_renewals = [
            {
                "id": 789, "ContractName": "Test Contract - Renewal 2024", "RenewalDate": "2024-01-01T00: 00: 00Z", "ContractValue": 65000
            }
        ]
        self.contracts.query = MagicMock(return_value = mock_renewals)

        result = self.contracts.get_contract_history(123)

        assert result["contract_id"] == 123
        assert result["contract_name"] == "Test Contract"
        assert len(result["timeline"]) == 3  # Creation, amendment, renewal
        assert len(result["amendments"]) == 1
        assert len(result["renewals"]) == 1
        assert len(result["value_changes"]) == 1
        assert result["metrics"]["total_amendments"] == 1
        assert result["metrics"]["total_renewals"] == 1

    def test_get_amendment_analytics(self):
        """Test amendment analytics generation."""
        mock_amendments = [
            {
                "amendmentType": "value_change", "status": "approved", "createdDate": "2024-01-15T00: 00: 00Z", "approvedDate": "2024-01-20T00: 00: 00Z", "valueChange": 60000, "originalValue": 50000
            }, {
                "amendmentType": "term_extension", "status": "pending", "createdDate": "2024-02-01T00: 00: 00Z"
            }
        ]
        self.client.query.return_value = mock_amendments

        result = self.contracts.get_amendment_analytics()

        assert result["total_amendments"] == 2
        assert result["by_type"]["value_change"] == 1
        assert result["by_type"]["term_extension"] == 1
        assert result["by_status"]["approved"] == 1
        assert result["by_status"]["pending"] == 1
        assert result["approval_metrics"]["approval_rate"] == 50
        assert result["approval_metrics"]["avg_approval_time"] == 5  # 5 days
        assert result["value_impact"]["total_value_increase"] == 10000


class TestValidationAndHelpers:
    """Test validation and helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.contracts = ContractsEntity(self.client)

    def test_validate_contract_data_valid(self):
        """Test validation with valid contract data."""
        valid_data = {
            "ContractName": "Test Contract", "AccountID": 123, "StartDate": "2024-01-01T00: 00: 00Z", "EndDate": "2024-12-31T23: 59: 59Z", "ContractValue": 50000, "ContractType": ContractTypes.RECURRING_SERVICE, "Status": ContractStatuses.ACTIVE
        }

        result = self.contracts.validate_contract_data(valid_data)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_contract_data_missing_required(self):
        """Test validation with missing required fields."""
        invalid_data = {
            "ContractValue": 50000
            # Missing ContractName and AccountID
        }

        result = self.contracts.validate_contract_data(invalid_data)

        assert result["is_valid"] is False
        assert len(result["errors"]) == 2
        assert any("ContractName" in error for error in result["errors"])
        assert any("AccountID" in error for error in result["errors"])

    def test_validate_contract_data_invalid_dates(self):
        """Test validation with invalid date range."""
        invalid_data = {
            "ContractName": "Test Contract", "AccountID": 123, "StartDate": "2024-06-01T00: 00: 00Z", "EndDate": "2024-01-01T00: 00: 00Z"  # End before start
        }

        result = self.contracts.validate_contract_data(invalid_data)

        assert result["is_valid"] is False
        assert any("End date must be after start date" in error for error in result["errors"])

    def test_get_contract_summary(self):
        """Test contract summary generation."""
        mock_contract = {
            "id": 123, "ContractName": "Test Contract", "AccountID": 456, "Status": ContractStatuses.ACTIVE, "ContractValue": 100000, "EndDate": (datetime.now() + timedelta(days = 45)).isoformat()
        }
        self.contracts.get = MagicMock(return_value = mock_contract)

        # Mock related data
        self.contracts.calculate_contract_value = MagicMock(return_value = {
            "contract_value": 100000, "billed_to_date": 40000, "remaining_value": 60000, "billing_utilization": 40
        })

        self.contracts.get_service_metrics = MagicMock(return_value = {
            "sla_compliance": {"compliance_rate": 92}
        })

        self.contracts.get_milestone_analytics = MagicMock(return_value = {
            "completion_rate": 60, "total_milestones": 5
        })

        result = self.contracts.get_contract_summary(123)

        assert result["contract_id"] == 123
        assert result["basic_info"]["name"] == "Test Contract"
        assert result["financial_summary"]["total_value"] == 100000
        assert result["performance_summary"]["sla_compliance_rate"] == 92
        assert result["health_indicators"]["sla_health"] == "good"
        assert result["health_indicators"]["renewal_urgency"] == "soon"

    def test_get_contract_health_check(self):
        """Test comprehensive contract health check."""
        mock_contract = {
            "id": 123, "ContractName": "Test Contract", "EndDate": (datetime.now() + timedelta(days = 15)).isoformat()
        }
        self.contracts.get = MagicMock(return_value = mock_contract)

        # Mock financial health data
        self.contracts.calculate_contract_value = MagicMock(return_value = {
            "billing_utilization": 85, "payment_status": {"overdue": 0}
        })

        # Mock service metrics
        self.contracts.get_service_metrics = MagicMock(return_value = {
            "sla_compliance": {"compliance_rate": 88}
        })

        # Mock validation
        self.contracts.validate_contract_data = MagicMock(return_value = {
            "is_valid": True, "errors": []
        })

        result = self.contracts.get_contract_health_check(123)

        assert result["contract_id"] == 123
        assert result["overall_health"] in ["good", "needs_attention"]
        assert "financial_health" in result["checks"]
        assert "operational_health" in result["checks"]
        assert "compliance_health" in result["checks"]
        assert "lifecycle_health" in result["checks"]

        # Lifecycle should be concerning due to expiry in 15 days
        assert result["checks"]["lifecycle_health"]["score"] == 60

    def test_validate_required_fields_helper(self):
        """Test the helper method for required field validation."""
        data = {"field1": "value1"}
        required_fields = ["field1", "field2", "field3"]

        with pytest.raises(ValueError, match = "Missing required fields: field2, field3"):
            self.contracts._validate_required_fields(data, required_fields)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
