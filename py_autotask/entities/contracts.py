"""
Contracts entity for Autotask API operations.

This module provides comprehensive PSA (Professional Services Automation) features
for contract management including billing, service tracking, milestones, renewals, usage tracking, and modifications.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..constants import ContractStatus, ContractType
from ..types import ContractData, CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


# Re-export constants with names expected by tests and external code
class ContractTypes:
    """Contract type constants."""

    RECURRING_SERVICE = 1
    FIXED_PRICE = 2
    TIME_AND_MATERIALS = 3
    MILESTONE = 4
    SUBSCRIPTION = 5
    MAINTENANCE = 6
    RETAINER = 7


class ContractStatuses:
    """Contract status constants."""

    INACTIVE = 0
    ACTIVE = 1
    CANCELLED = 2
    EXPIRED = 3
    ON_HOLD = 4
    PENDING_APPROVAL = 5
    DRAFT = 6


class BillingMethods:
    """Billing method constants."""

    FIXED_PRICE = 1
    TIME_AND_MATERIALS = 2
    MILESTONE_BILLING = 3
    RECURRING_BILLING = 4
    USAGE_BASED = 5
    RETAINER = 6


class ServiceTypes:
    """Constants for service types."""

    PROFESSIONAL_SERVICES = 1
    MANAGED_SERVICES = 2
    SUPPORT_SERVICES = 3
    CONSULTING = 4
    IMPLEMENTATION = 5
    MAINTENANCE = 6
    TRAINING = 7


class SLAThresholds:
    """Constants for SLA compliance thresholds."""

    EXCELLENT_COMPLIANCE = 95
    GOOD_COMPLIANCE = 90
    POOR_COMPLIANCE = 80
    DEFAULT_EVALUATION_DAYS = 30
    DEFAULT_INVOICE_DUE_DAYS = 30


class ContractDefaults:
    """Default values for contract operations."""

    DEFAULT_MILESTONE_STATUS = "pending"
    DEFAULT_MILESTONE_PROGRESS = 0
    DEFAULT_AMENDMENT_STATUS = "pending"
    DEFAULT_AMENDMENT_APPROVAL_REQUIRED = True
    DEFAULT_RENEWAL_DAYS_AHEAD = 60
    DEFAULT_USAGE_PERIOD = "month"


class ContractsEntity(BaseEntity):
    """
    Enhanced Contracts entity with comprehensive PSA features.

    Provides advanced contract management capabilities including:
    - Billing and invoicing integration
    - Service level tracking and SLA compliance
    - Milestone management
    - Renewal management
    - Usage tracking and limits
    - Contract modifications and amendments
    - Comprehensive validation and analytics
    """

    def __init__(self, client, entity_name: str = "Contracts"):
        """Initialize the enhanced Contracts entity."""
        super().__init__(client, entity_name)

    def create_contract(
        self,
        contract_name: str,
        account_id: int,
        contract_type: int = ContractType.RECURRING_SERVICE,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract_value: Optional[float] = None,
        **kwargs,
    ) -> ContractData:
        """
        Create a new contract with required and optional fields.

        Args:
            contract_name: Name of the contract
            account_id: ID of the associated account/company
            contract_type: Type of contract (use ContractType enum)
            start_date: Contract start date (ISO format)
            end_date: Contract end date (ISO format)
            contract_value: Total value of the contract
            **kwargs: Additional contract fields

        Returns:
            Created contract data
        """
        contract_data = {
            "ContractName": contract_name,
            "AccountID": account_id,
            "ContractType": contract_type,
            **kwargs,
        }

        if start_date:
            contract_data["StartDate"] = start_date
        if end_date:
            contract_data["EndDate"] = end_date
        if contract_value is not None:
            contract_data["ContractValue"] = contract_value

        return self.create(contract_data)

    def get_contracts_by_account(
        self, account_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[ContractData]:
        """
        Get all contracts for a specific account.

        Args:
            account_id: Account ID to filter by
            active_only: Whether to return only active contracts
            limit: Maximum number of contracts to return

        Returns:
            List of contracts for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        if active_only:
            filters.append(QueryFilter(field="Status", op="eq", value=1))  # Active

        return self.query(filters=filters, max_records=limit)

    def get_active_contracts(self, limit: Optional[int] = None) -> List[ContractData]:
        """
        Get all active contracts.

        Args:
            limit: Maximum number of contracts to return

        Returns:
            List of active contracts
        """
        filters = [QueryFilter(field="Status", op="eq", value=1)]  # Active
        return self.query(filters=filters, max_records=limit)

    # ======================================== Billing and Invoicing Integration
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def generate_invoice(
        self,
        contract_id: int,
        period: Optional[Dict[str, str]] = None,
        invoice_data: Optional[Dict[str, Any]] = None,
    ) -> CreateResponse:
        """
        Generate an invoice for a contract billing period.

        Args:
            contract_id: Contract ID to generate invoice for
            period: Dictionary with 'start_date' and 'end_date' for billing period
            invoice_data: Additional invoice data and line items

        Returns:
            Created invoice data

        Raises:
            ValueError: If contract not found or billing period invalid
            AutotaskAPIError: If the API request fails
        """
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        if not period:
            period = self._get_default_billing_period()

        invoice_request = {
            "contractID": contract_id,
            "billingPeriodStart": period["start_date"],
            "billingPeriodEnd": period["end_date"],
            "invoiceDate": datetime.now().isoformat(),
            "dueDate": (
                datetime.now() + timedelta(days=SLAThresholds.DEFAULT_INVOICE_DUE_DAYS)
            ).isoformat(),
            **(invoice_data or {}),
        }

        return self.client.create("Invoices", invoice_request)

    def _get_default_billing_period(self) -> Dict[str, str]:
        """Get default billing period (current month)."""
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_of_month = start_of_month.replace(
                year=now.year + 1, month=1
            ) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=now.month + 1) - timedelta(
                days=1
            )

        return {
            "start_date": start_of_month.isoformat(),
            "end_date": end_of_month.isoformat(),
        }

    def get_billing_history(
        self,
        contract_id: int,
        limit: Optional[int] = None,
        date_range: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing history for a contract.

        Args:
            contract_id: Contract ID to get history for
            limit: Maximum number of billing records to return
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            List of billing history records
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="invoiceDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="invoiceDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        return self.client.query("Invoices", filters=filters, max_records=limit)

    def calculate_contract_value(
        self,
        contract_id: int,
        include_pending: bool = True,
        date_range: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Calculate total contract value including actual vs. projected billing.

        Args:
            contract_id: Contract ID to calculate value for
            include_pending: Include pending/unbilled amounts
            date_range: Optional date range for calculations

        Returns:
            Dictionary with contract value breakdown
        """
        contract = self._get_contract_or_raise(contract_id)
        billing_history = self.get_billing_history(contract_id, date_range=date_range)

        value_breakdown = self._initialize_value_breakdown(contract_id, contract)
        total_billed = self._calculate_billed_amounts(billing_history, value_breakdown)
        self._calculate_utilization_metrics(contract, total_billed, value_breakdown)

        if include_pending:
            self._add_pending_billing(contract_id, value_breakdown)

        return value_breakdown

    def _get_contract_or_raise(self, contract_id: int) -> Dict[str, Any]:
        """Get contract by ID or raise ValueError if not found."""
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        return contract

    def _initialize_value_breakdown(
        self, contract_id: int, contract: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initialize the value breakdown dictionary structure."""
        return {
            "contract_id": contract_id,
            "contract_value": contract.get("ContractValue", 0),
            "billed_to_date": 0,
            "pending_billing": 0,
            "remaining_value": 0,
            "billing_utilization": 0,
            "by_period": {},
            "payment_status": {"paid": 0, "outstanding": 0, "overdue": 0},
        }

    def _calculate_billed_amounts(
        self, billing_history: List[Dict[str, Any]], value_breakdown: Dict[str, Any]
    ) -> float:
        """Calculate total billed amounts and update breakdown by payment status and period."""
        total_billed = 0

        for invoice in billing_history:
            amount = float(invoice.get("amount", 0))
            total_billed += amount

            self._update_payment_status(invoice, amount, value_breakdown)
            self._update_period_breakdown(invoice, amount, value_breakdown)

        value_breakdown["billed_to_date"] = total_billed
        return total_billed

    def _update_payment_status(
        self, invoice: Dict[str, Any], amount: float, value_breakdown: Dict[str, Any]
    ) -> None:
        """Update payment status breakdown for an invoice."""
        status = invoice.get("status", "").lower()
        if status == "paid":
            value_breakdown["payment_status"]["paid"] += amount
        elif status in ["overdue", "past_due"]:
            value_breakdown["payment_status"]["overdue"] += amount
        else:
            value_breakdown["payment_status"]["outstanding"] += amount

    def _update_period_breakdown(
        self, invoice: Dict[str, Any], amount: float, value_breakdown: Dict[str, Any]
    ) -> None:
        """Update period breakdown for an invoice."""
        invoice_date = invoice.get("invoiceDate", "")
        if invoice_date:
            try:
                period_key = datetime.fromisoformat(
                    invoice_date.replace("Z", "+00:00")
                ).strftime("%Y-%m")
                if period_key not in value_breakdown["by_period"]:
                    value_breakdown["by_period"][period_key] = 0
                value_breakdown["by_period"][period_key] += amount
            except ValueError:
                pass

    def _calculate_utilization_metrics(
        self,
        contract: Dict[str, Any],
        total_billed: float,
        value_breakdown: Dict[str, Any],
    ) -> None:
        """Calculate remaining value and billing utilization."""
        contract_value = float(contract.get("ContractValue", 0))
        if contract_value > 0:
            value_breakdown["remaining_value"] = contract_value - total_billed
            value_breakdown["billing_utilization"] = (
                total_billed / contract_value
            ) * 100

    def _add_pending_billing(
        self, contract_id: int, value_breakdown: Dict[str, Any]
    ) -> None:
        """Add pending billing amounts to value breakdown."""
        pending_filters = [
            QueryFilter(field="contractID", op="eq", value=contract_id),
            QueryFilter(field="invoiced", op="eq", value=False),
        ]

        try:
            pending_time_entries = self.client.query(
                "TimeEntries", filters=pending_filters
            )
            pending_amount = sum(
                float(entry.get("billingAmount", 0)) for entry in pending_time_entries
            )
            value_breakdown["pending_billing"] = pending_amount
        except Exception:
            # Fallback if TimeEntries query fails
            value_breakdown["pending_billing"] = 0

        # This section was moved to _add_pending_billing method

    # ======================================== Service Level Tracking
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def track_service_delivery(
        self, contract_id: int, service_data: Dict[str, Any]
    ) -> CreateResponse:
        """
        Track service delivery metrics for a contract.

        Args:
            contract_id: Contract ID to track services for
            service_data: Dictionary containing service metrics
                Required fields:
                - service_type: Type of service delivered
                - delivery_date: When service was delivered
                - metrics: Performance metrics
                Optional fields:
                - sla_target: SLA target for this service
                - actual_performance: Actual performance metrics
                - notes: Additional service notes

        Returns:
            Created service delivery record

        Raises:
            ValueError: If required fields are missing
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["service_type", "delivery_date", "metrics"]
        missing_fields = [
            field for field in required_fields if field not in service_data
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        service_record = {
            "contractID": contract_id,
            "serviceType": service_data["service_type"],
            "deliveryDate": service_data["delivery_date"],
            "metrics": service_data["metrics"],
            "recordedDate": datetime.now().isoformat(),
            **{k: v for k, v in service_data.items() if k not in required_fields},
        }

        return self.client.create("ServiceDeliveryRecords", service_record)

    def get_service_metrics(
        self,
        contract_id: int,
        date_range: Optional[tuple] = None,
        service_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get service delivery metrics for a contract.

        Args:
            contract_id: Contract ID to get metrics for
            date_range: Optional date range filter
            service_type: Optional service type filter

        Returns:
            Dictionary with service metrics and analytics
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="deliveryDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="deliveryDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if service_type:
            filters.append(
                QueryFilter(field="serviceType", op="eq", value=service_type)
            )

        try:
            service_records = self.client.query(
                "ServiceDeliveryRecords", filters=filters
            )
        except Exception:
            # Fallback if ServiceDeliveryRecords doesn't exist
            service_records = []

        metrics_summary = self._initialize_metrics_summary(contract_id, service_records)
        self._process_service_records(service_records, metrics_summary)
        self._calculate_compliance_rate(metrics_summary)

        return metrics_summary

    def _initialize_metrics_summary(
        self, contract_id: int, service_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Initialize the metrics summary structure."""
        return {
            "contract_id": contract_id,
            "total_services": len(service_records),
            "by_service_type": {},
            "sla_compliance": {"total_slas": 0, "met_slas": 0, "compliance_rate": 0},
            "performance_trends": [],
            "summary_metrics": {},
        }

    def _process_service_records(
        self, service_records: List[Dict[str, Any]], metrics_summary: Dict[str, Any]
    ) -> None:
        """Process service records and update metrics."""
        for record in service_records:
            service_type_key = record.get("serviceType", "Unknown")
            self._ensure_service_type_entry(service_type_key, metrics_summary)

            metrics_summary["by_service_type"][service_type_key]["count"] += 1
            self._track_sla_compliance(record, metrics_summary)

    def _ensure_service_type_entry(
        self, service_type: str, metrics_summary: Dict[str, Any]
    ) -> None:
        """Ensure service type entry exists in metrics summary."""
        if service_type not in metrics_summary["by_service_type"]:
            metrics_summary["by_service_type"][service_type] = {
                "count": 0,
                "avg_performance": 0,
                "sla_compliance": 0,
            }

    def _track_sla_compliance(
        self, record: Dict[str, Any], metrics_summary: Dict[str, Any]
    ) -> None:
        """Track SLA compliance for a service record."""
        sla_target = record.get("slaTarget")
        actual_performance = record.get("actualPerformance")

        if sla_target and actual_performance:
            metrics_summary["sla_compliance"]["total_slas"] += 1
            if float(actual_performance) >= float(sla_target):
                metrics_summary["sla_compliance"]["met_slas"] += 1

    def _calculate_compliance_rate(self, metrics_summary: Dict[str, Any]) -> None:
        """Calculate overall compliance rate."""
        if metrics_summary["sla_compliance"]["total_slas"] > 0:
            metrics_summary["sla_compliance"]["compliance_rate"] = (
                metrics_summary["sla_compliance"]["met_slas"]
                / metrics_summary["sla_compliance"]["total_slas"]
            ) * 100

    def check_sla_compliance(
        self,
        contract_id: int,
        sla_thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Check SLA compliance for a contract.

        Args:
            contract_id: Contract ID to check compliance for
            sla_thresholds: Optional custom SLA thresholds

        Returns:
            Dictionary with SLA compliance status and violations
        """
        self._get_contract_or_raise(contract_id)

        # Get recent service metrics (default evaluation period)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=SLAThresholds.DEFAULT_EVALUATION_DAYS)

        metrics = self.get_service_metrics(
            contract_id, date_range=(start_date, end_date)
        )

        compliance_status = {
            "contract_id": contract_id,
            "evaluation_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "overall_compliance": metrics["sla_compliance"]["compliance_rate"],
            "compliant": metrics["sla_compliance"]["compliance_rate"]
            >= SLAThresholds.EXCELLENT_COMPLIANCE,
            "violations": [],
            "warnings": [],
            "recommendations": [],
        }

        # Check for violations
        if compliance_status["overall_compliance"] < SLAThresholds.EXCELLENT_COMPLIANCE:
            severity = (
                "high"
                if compliance_status["overall_compliance"]
                < SLAThresholds.GOOD_COMPLIANCE
                else "medium"
            )
            compliance_status["violations"].append(
                {
                    "type": "overall_compliance",
                    "severity": severity,
                    "message": f"Overall SLA compliance at {compliance_status['overall_compliance']:.1f}%",
                }
            )

        # Service-specific compliance checks
        for service_type, service_metrics in metrics["by_service_type"].items():
            if service_metrics["sla_compliance"] < SLAThresholds.GOOD_COMPLIANCE:
                compliance_status["violations"].append(
                    {
                        "type": "service_compliance",
                        "service_type": service_type,
                        "severity": "high",
                        "message": f"{service_type} SLA compliance below {SLAThresholds.GOOD_COMPLIANCE}%",
                    }
                )

        # Add recommendations
        if compliance_status["violations"]:
            compliance_status["recommendations"].extend(
                [
                    "Review service delivery processes",
                    "Consider additional resource allocation",
                    "Implement proactive monitoring",
                    "Schedule client review meeting",
                ]
            )

        return compliance_status

    # ======================================== Milestone Management
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def add_milestone(
        self, contract_id: int, milestone_data: Dict[str, Any]
    ) -> CreateResponse:
        """
        Add a milestone to a contract.

        Args:
            contract_id: Contract ID to add milestone to
            milestone_data: Dictionary containing milestone information
                Required fields:
                - title: Milestone title
                - description: Milestone description
                - due_date: Milestone due date
                - value: Milestone financial value
                Optional fields:
                - dependencies: List of dependent milestones
                - deliverables: List of deliverable items
                - acceptance_criteria: Acceptance criteria
                - status: Initial status (default: 'pending')

        Returns:
            Created milestone data

        Raises:
            ValueError: If required fields are missing
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["title", "description", "due_date", "value"]
        missing_fields = [
            field for field in required_fields if field not in milestone_data
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        milestone_record = {
            "contractID": contract_id,
            "title": milestone_data["title"],
            "description": milestone_data["description"],
            "dueDate": milestone_data["due_date"],
            "value": milestone_data["value"],
            "status": milestone_data.get("status", "pending"),
            "createdDate": datetime.now().isoformat(),
            "progress": 0,
            **{
                k: v
                for k, v in milestone_data.items()
                if k not in required_fields + ["status"]
            },
        }

        return self.client.create("ContractMilestones", milestone_record)

    def update_milestone_progress(
        self,
        milestone_id: int,
        progress: int,
        progress_notes: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Update milestone progress.

        Args:
            milestone_id: Milestone ID to update
            progress: Progress percentage (0-100)
            progress_notes: Optional progress notes

        Returns:
            Updated milestone data

        Raises:
            ValueError: If progress is not between 0-100
            AutotaskAPIError: If the API request fails
        """
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100")

        update_data = {
            "progress": progress,
            "lastUpdated": datetime.now().isoformat(),
        }

        # Auto-complete milestone if 100%
        if progress == 100:
            update_data["status"] = "completed"
            update_data["completedDate"] = datetime.now().isoformat()
        elif progress > 0:
            # Mark as in progress if not already
            milestone = self.client.get("ContractMilestones", milestone_id)
            if milestone and milestone.get("status") == "pending":
                update_data["status"] = "in_progress"
                update_data["startedDate"] = datetime.now().isoformat()

        if progress_notes:
            update_data["progressNotes"] = progress_notes

        return self.client.update("ContractMilestones", milestone_id, update_data)

    def get_upcoming_milestones(
        self,
        contract_id: int,
        days_ahead: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming milestones for a contract.

        Args:
            contract_id: Contract ID to get milestones for
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming milestones
        """
        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

        filters = [
            QueryFilter(field="contractID", op="eq", value=contract_id),
            QueryFilter(field="dueDate", op="lte", value=future_date),
            QueryFilter(field="status", op="in", value=["pending", "in_progress"]),
        ]

        try:
            milestones = self.client.query("ContractMilestones", filters=filters)
        except Exception:
            # Fallback if ContractMilestones doesn't exist
            milestones = []

        # Sort by due date
        milestones.sort(key=lambda x: x.get("dueDate", ""))

        return milestones

    def get_milestone_analytics(
        self,
        contract_id: int,
        date_range: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Get milestone analytics for a contract.

        Args:
            contract_id: Contract ID to analyze
            date_range: Optional date range filter

        Returns:
            Dictionary with milestone analytics
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="dueDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="dueDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        try:
            milestones = self.client.query("ContractMilestones", filters=filters)
        except Exception:
            milestones = []

        analytics = {
            "contract_id": contract_id,
            "total_milestones": len(milestones),
            "by_status": {
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "overdue": 0,
                "cancelled": 0,
            },
            "total_value": 0,
            "completed_value": 0,
            "pending_value": 0,
            "completion_rate": 0,
            "value_realization": 0,
            "overdue_milestones": [],
            "avg_completion_time": 0,
            "upcoming_deadlines": [],
        }

        now = datetime.now()
        completion_times = []
        one_week = now + timedelta(weeks=1)

        for milestone in milestones:
            status = milestone.get("status", "pending")
            value = float(milestone.get("value", 0))
            due_date = milestone.get("dueDate")

            analytics["total_value"] += value

            # Status tracking
            if status in analytics["by_status"]:
                analytics["by_status"][status] += 1

            # Value tracking
            if status == "completed":
                analytics["completed_value"] += value

                # Completion time calculation
                started_date = milestone.get("startedDate")
                completed_date = milestone.get("completedDate")
                if started_date and completed_date:
                    try:
                        started = datetime.fromisoformat(
                            started_date.replace("Z", "+00:00")
                        )
                        completed = datetime.fromisoformat(
                            completed_date.replace("Z", "+00:00")
                        )
                        completion_time = (
                            completed - started
                        ).total_seconds() / 86400  # Days
                        completion_times.append(completion_time)
                    except ValueError:
                        pass
            else:
                analytics["pending_value"] += value

            # Overdue tracking
            if due_date and status not in ["completed", "cancelled"]:
                try:
                    deadline = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                    if deadline < now:
                        analytics["by_status"]["overdue"] += 1
                        analytics["overdue_milestones"].append(
                            {
                                "id": milestone.get("id"),
                                "title": milestone.get("title", ""),
                                "due_date": due_date,
                                "days_overdue": (now - deadline).days,
                                "value": value,
                            }
                        )
                    elif deadline <= one_week:
                        analytics["upcoming_deadlines"].append(
                            {
                                "id": milestone.get("id"),
                                "title": milestone.get("title", ""),
                                "due_date": due_date,
                                "days_remaining": (deadline - now).days,
                                "value": value,
                            }
                        )
                except ValueError:
                    pass

        # Calculate rates
        if analytics["total_milestones"] > 0:
            analytics["completion_rate"] = (
                analytics["by_status"]["completed"] / analytics["total_milestones"]
            ) * 100

        if analytics["total_value"] > 0:
            analytics["value_realization"] = (
                analytics["completed_value"] / analytics["total_value"]
            ) * 100

        if completion_times:
            analytics["avg_completion_time"] = sum(completion_times) / len(
                completion_times
            )

        return analytics

    # ======================================== Renewal Management
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def schedule_renewal_alert(
        self, contract_id: int, alert_data: Dict[str, Any]
    ) -> CreateResponse:
        """
        Schedule a renewal alert for a contract.

        Args:
            contract_id: Contract ID to schedule alert for
            alert_data: Dictionary containing alert information
                Required fields:
                - alert_date: When to trigger the alert
                - alert_type: Type of alert ('email', 'notification', 'task')
                - recipients: List of recipient IDs or email addresses
                Optional fields:
                - message: Custom alert message
                - escalation_rules: Escalation rules if no response
                - auto_renew: Whether to auto-renew if conditions met

        Returns:
            Created renewal alert record

        Raises:
            ValueError: If required fields are missing
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["alert_date", "alert_type", "recipients"]
        missing_fields = [field for field in required_fields if field not in alert_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        alert_record = {
            "contractID": contract_id,
            "alertDate": alert_data["alert_date"],
            "alertType": alert_data["alert_type"],
            "recipients": alert_data["recipients"],
            "status": "scheduled",
            "createdDate": datetime.now().isoformat(),
            **{k: v for k, v in alert_data.items() if k not in required_fields},
        }

        return self.client.create("ContractRenewalAlerts", alert_record)

    def get_expiring_contracts(
        self,
        days_ahead: int = 60,
        account_id: Optional[int] = None,
        include_auto_renew: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get contracts expiring within a specified timeframe.

        Args:
            days_ahead: Number of days to look ahead for expiring contracts
            account_id: Optional filter by specific account
            include_auto_renew: Include contracts with auto-renewal enabled

        Returns:
            List of expiring contracts with renewal status
        """
        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

        filters = [
            QueryFilter(field="EndDate", op="lte", value=future_date),
            QueryFilter(field="Status", op="eq", value=ContractStatus.ACTIVE),
        ]

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        contracts = self.query(filters=filters)

        # Enhance with renewal status
        enhanced_contracts = []
        for contract in contracts:
            end_date = contract.get("EndDate", "")
            if end_date:
                try:
                    contract_end = datetime.fromisoformat(
                        end_date.replace("Z", "+00:00")
                    )
                    days_until_expiry = (contract_end - datetime.now()).days

                    # Check auto-renewal status
                    auto_renew = contract.get("autoRenew", False)
                    if not include_auto_renew and auto_renew:
                        continue

                    enhanced_contract = {
                        **contract,
                        "days_until_expiry": days_until_expiry,
                        "renewal_priority": self._calculate_renewal_priority(
                            contract, days_until_expiry
                        ),
                        "renewal_status": self._get_renewal_status(contract),
                        "auto_renew_enabled": auto_renew,
                    }

                    enhanced_contracts.append(enhanced_contract)
                except ValueError:
                    # Skip contracts with invalid dates
                    continue

        # Sort by expiry date (soonest first)
        enhanced_contracts.sort(key=lambda x: x.get("days_until_expiry", float("inf")))

        return enhanced_contracts

    def renew_contract(
        self,
        contract_id: int,
        renewal_data: Dict[str, Any],
    ) -> CreateResponse:
        """
        Renew a contract with new terms.

        Args:
            contract_id: Original contract ID to renew
            renewal_data: Dictionary containing renewal terms
                Optional fields:
                - new_start_date: New contract start date
                - new_end_date: New contract end date
                - new_value: Updated contract value
                - renewal_terms: Modified terms and conditions
                - auto_renew: Enable auto-renewal for new contract
                - billing_changes: Changes to billing terms

        Returns:
            Created renewal contract data

        Raises:
            ValueError: If original contract not found
            AutotaskAPIError: If the API request fails
        """
        original_contract = self.get(contract_id)
        if not original_contract:
            raise ValueError(f"Original contract {contract_id} not found")

        # Default renewal terms
        now = datetime.now()
        current_end = original_contract.get("EndDate")

        if current_end:
            try:
                end_date = datetime.fromisoformat(current_end.replace("Z", "+00:00"))
                new_start = end_date + timedelta(days=1)
            except ValueError:
                new_start = now
        else:
            new_start = now

        new_end = new_start + timedelta(days=365)  # Default 1-year renewal

        # Build renewal contract
        renewal_contract = {
            "ContractName": f"{original_contract.get('ContractName', '')} - Renewal {now.year}",
            "AccountID": original_contract.get("AccountID"),
            "ContractType": original_contract.get("ContractType"),
            "StartDate": renewal_data.get("new_start_date", new_start.isoformat()),
            "EndDate": renewal_data.get("new_end_date", new_end.isoformat()),
            "ContractValue": renewal_data.get(
                "new_value", original_contract.get("ContractValue")
            ),
            "Status": ContractStatus.ACTIVE,
            "ParentContractID": contract_id,
            "RenewalDate": now.isoformat(),
            **{
                k: v
                for k, v in renewal_data.items()
                if k not in ["new_start_date", "new_end_date", "new_value"]
            },
        }

        # Create the renewal contract
        renewal_response = self.create(renewal_contract)

        # Update original contract status
        if renewal_response.get("success"):
            self.update(
                contract_id,
                {
                    "Status": ContractStatus.EXPIRED,
                    "RenewalContractID": renewal_response.get("id"),
                    "RenewalDate": now.isoformat(),
                },
            )

        return renewal_response

    def get_renewal_analytics(
        self,
        date_range: Optional[tuple] = None,
        account_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get contract renewal analytics and trends.

        Args:
            date_range: Optional date range for analysis
            account_id: Optional filter by account

        Returns:
            Dictionary with renewal analytics
        """
        # Get expiring contracts for next 90 days
        expiring_contracts = self.get_expiring_contracts(
            days_ahead=90, account_id=account_id
        )

        # Get recently renewed contracts
        filters = [QueryFilter(field="ParentContractID", op="isNotNull", value=None)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="RenewalDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="RenewalDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        renewed_contracts = self.query(filters=filters)

        analytics = {
            "renewal_pipeline": {
                "next_30_days": 0,
                "next_60_days": 0,
                "next_90_days": 0,
                "total_pipeline_value": 0,
                "high_priority_renewals": 0,
            },
            "renewal_performance": {
                "total_renewed": len(renewed_contracts),
                "renewal_rate": 0,
                "avg_renewal_value": 0,
                "value_growth": 0,
                "renewal_cycle_time": 0,
            },
            "by_priority": {"high": 0, "medium": 0, "low": 0},
            "at_risk_renewals": [],
            "top_renewal_opportunities": [],
        }

        # Pipeline analysis
        total_pipeline_value = 0
        for contract in expiring_contracts:
            days_until_expiry = contract.get("days_until_expiry", 0)
            value = float(contract.get("ContractValue", 0))
            priority = contract.get("renewal_priority", "low")

            total_pipeline_value += value

            if days_until_expiry <= 30:
                analytics["renewal_pipeline"]["next_30_days"] += 1
            if days_until_expiry <= 60:
                analytics["renewal_pipeline"]["next_60_days"] += 1
            if days_until_expiry <= 90:
                analytics["renewal_pipeline"]["next_90_days"] += 1

            # Priority breakdown
            if priority in analytics["by_priority"]:
                analytics["by_priority"][priority] += 1

            if priority == "high":
                analytics["renewal_pipeline"]["high_priority_renewals"] += 1

            # At-risk renewals
            if priority == "high" and days_until_expiry <= 30:
                analytics["at_risk_renewals"].append(
                    {
                        "contract_id": contract.get("id"),
                        "name": contract.get("ContractName", ""),
                        "account_id": contract.get("AccountID"),
                        "value": value,
                        "days_until_expiry": days_until_expiry,
                    }
                )

            # Top opportunities
            if value > 50000:  # High-value contracts
                analytics["top_renewal_opportunities"].append(
                    {
                        "contract_id": contract.get("id"),
                        "name": contract.get("ContractName", ""),
                        "value": value,
                        "days_until_expiry": days_until_expiry,
                    }
                )

        analytics["renewal_pipeline"]["total_pipeline_value"] = total_pipeline_value

        # Performance analysis
        if renewed_contracts:
            total_renewed_value = sum(
                float(contract.get("ContractValue", 0))
                for contract in renewed_contracts
            )
            analytics["renewal_performance"]["avg_renewal_value"] = (
                total_renewed_value / len(renewed_contracts)
            )

        # Sort opportunities by value
        analytics["top_renewal_opportunities"].sort(
            key=lambda x: x["value"], reverse=True
        )
        analytics["top_renewal_opportunities"] = analytics["top_renewal_opportunities"][
            :10
        ]

        return analytics

    def _calculate_renewal_priority(
        self, contract: Dict[str, Any], days_until_expiry: int
    ) -> str:
        """Calculate renewal priority based on contract characteristics."""
        value = float(contract.get("ContractValue", 0))

        # High priority: High value or expiring soon
        if value > 100000 or days_until_expiry <= 30:
            return "high"
        # Medium priority: Medium value or expiring within 60 days
        elif value > 25000 or days_until_expiry <= 60:
            return "medium"
        else:
            return "low"

    def _get_renewal_status(self, contract: Dict[str, Any]) -> str:
        """Get current renewal status for a contract."""
        # This would typically check for existing renewal activities
        # For now, return a simple status based on expiry
        end_date = contract.get("EndDate", "")
        if end_date:
            try:
                contract_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                days_until_expiry = (contract_end - datetime.now()).days

                if days_until_expiry <= 14:
                    return "urgent"
                elif days_until_expiry <= 30:
                    return "in_progress"
                else:
                    return "planned"
            except ValueError:
                pass

        return "unknown"

    # ======================================== Usage Tracking
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def track_usage(
        self, contract_id: int, usage_data: Dict[str, Any]
    ) -> CreateResponse:
        """
        Track usage metrics for a contract.

        Args:
            contract_id: Contract ID to track usage for
            usage_data: Dictionary containing usage information
                Required fields:
                - usage_type: Type of usage ('hours', 'storage', 'transactions', etc.)
                - amount: Usage amount
                - period: Usage period (month, week, day)
                - date: Usage date
                Optional fields:
                - unit_cost: Cost per unit
                - billable: Whether usage is billable
                - category: Usage category
                - description: Usage description

        Returns:
            Created usage record

        Raises:
            ValueError: If required fields are missing
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["usage_type", "amount", "period", "date"]
        missing_fields = [field for field in required_fields if field not in usage_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        usage_record = {
            "contractID": contract_id,
            "usageType": usage_data["usage_type"],
            "amount": usage_data["amount"],
            "period": usage_data["period"],
            "usageDate": usage_data["date"],
            "recordedDate": datetime.now().isoformat(),
            "billable": usage_data.get("billable", True),
            **{k: v for k, v in usage_data.items() if k not in required_fields},
        }

        return self.client.create("ContractUsageRecords", usage_record)

    def check_usage_limits(
        self,
        contract_id: int,
        period: str = "month",
    ) -> Dict[str, Any]:
        """
        Check usage against contract limits.

        Args:
            contract_id: Contract ID to check limits for
            period: Period to check ('month', 'year', 'quarter')

        Returns:
            Dictionary with usage limit status
        """
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Get usage limits from contract
        usage_limits = contract.get("usageLimits", {})
        if not usage_limits:
            return {
                "contract_id": contract_id,
                "has_limits": False,
                "message": "No usage limits defined for this contract",
            }

        # Calculate period start/end
        now = datetime.now()
        if period == "month":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "quarter":
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            period_start = now.replace(
                month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif period == "year":
            period_start = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Unsupported period: {period}")

        # Get usage for period
        current_usage = self.get_usage_report(contract_id, period=(period_start, now))

        limit_status = {
            "contract_id": contract_id,
            "period": period,
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat(),
            "has_limits": True,
            "limits": {},
            "violations": [],
            "warnings": [],
            "total_usage": current_usage.get("total_usage", {}),
        }

        # Check each limit
        for usage_type, limit_data in usage_limits.items():
            limit_amount = float(limit_data.get("amount", 0))
            warning_threshold = float(
                limit_data.get("warning_threshold", 0.8)
            )  # 80% default

            current_amount = 0
            for usage_record in current_usage.get("usage_records", []):
                if usage_record.get("usageType") == usage_type:
                    current_amount += float(usage_record.get("amount", 0))

            usage_percentage = (
                (current_amount / limit_amount * 100) if limit_amount > 0 else 0
            )

            limit_info = {
                "limit": limit_amount,
                "current_usage": current_amount,
                "remaining": max(0, limit_amount - current_amount),
                "percentage_used": usage_percentage,
                "status": "ok",
            }

            # Check for violations and warnings
            if current_amount > limit_amount:
                limit_info["status"] = "exceeded"
                limit_status["violations"].append(
                    {
                        "usage_type": usage_type,
                        "limit": limit_amount,
                        "current_usage": current_amount,
                        "overage": current_amount - limit_amount,
                        "message": f"{usage_type} usage exceeded limit by {current_amount - limit_amount: .2f}",
                    }
                )
            elif usage_percentage >= (warning_threshold * 100):
                limit_info["status"] = "warning"
                limit_status["warnings"].append(
                    {
                        "usage_type": usage_type,
                        "limit": limit_amount,
                        "current_usage": current_amount,
                        "percentage": usage_percentage,
                        "message": f"{usage_type} usage at {usage_percentage: .1f}% of limit",
                    }
                )

            limit_status["limits"][usage_type] = limit_info

        return limit_status

    def get_usage_report(
        self,
        contract_id: int,
        period: Optional[tuple] = None,
        usage_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get usage report for a contract.

        Args:
            contract_id: Contract ID to get usage for
            period: Optional tuple of (start_date, end_date)
            usage_type: Optional filter by usage type

        Returns:
            Dictionary with usage report data
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]

        if period:
            start_date, end_date = period
            filters.extend(
                [
                    QueryFilter(
                        field="usageDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="usageDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if usage_type:
            filters.append(QueryFilter(field="usageType", op="eq", value=usage_type))

        try:
            usage_records = self.client.query("ContractUsageRecords", filters=filters)
        except Exception:
            # Fallback if ContractUsageRecords doesn't exist
            usage_records = []

        report = {
            "contract_id": contract_id,
            "period": (
                {
                    "start": (
                        period[0].isoformat()
                        if period and hasattr(period[0], "isoformat")
                        else period[0] if period else None
                    ),
                    "end": (
                        period[1].isoformat()
                        if period and hasattr(period[1], "isoformat")
                        else period[1] if period else None
                    ),
                }
                if period
                else None
            ),
            "total_records": len(usage_records),
            "usage_records": usage_records,
            "by_type": {},
            "by_period": {},
            "total_usage": {},
            "billable_usage": {},
            "cost_summary": {
                "total_cost": 0,
                "billable_cost": 0,
                "non_billable_cost": 0,
            },
        }

        for record in usage_records:
            usage_type_key = record.get("usageType", "unknown")
            amount = float(record.get("amount", 0))
            unit_cost = float(record.get("unitCost", 0))
            billable = record.get("billable", True)
            usage_date = record.get("usageDate", "")

            # By type aggregation
            if usage_type_key not in report["by_type"]:
                report["by_type"][usage_type_key] = {
                    "total_amount": 0,
                    "total_cost": 0,
                    "record_count": 0,
                    "billable_amount": 0,
                    "non_billable_amount": 0,
                }

            report["by_type"][usage_type_key]["total_amount"] += amount
            report["by_type"][usage_type_key]["total_cost"] += amount * unit_cost
            report["by_type"][usage_type_key]["record_count"] += 1

            if billable:
                report["by_type"][usage_type_key]["billable_amount"] += amount
            else:
                report["by_type"][usage_type_key]["non_billable_amount"] += amount

            # Total usage aggregation
            if usage_type_key not in report["total_usage"]:
                report["total_usage"][usage_type_key] = 0
            report["total_usage"][usage_type_key] += amount

            # Billable usage aggregation
            if billable:
                if usage_type_key not in report["billable_usage"]:
                    report["billable_usage"][usage_type_key] = 0
                report["billable_usage"][usage_type_key] += amount

            # Cost summary
            cost = amount * unit_cost
            report["cost_summary"]["total_cost"] += cost
            if billable:
                report["cost_summary"]["billable_cost"] += cost
            else:
                report["cost_summary"]["non_billable_cost"] += cost

            # By period aggregation
            if usage_date:
                try:
                    date_obj = datetime.fromisoformat(usage_date.replace("Z", "+00:00"))
                    period_key = date_obj.strftime("%Y-%m")

                    if period_key not in report["by_period"]:
                        report["by_period"][period_key] = {
                            "total_amount": 0,
                            "total_cost": 0,
                            "by_type": {},
                        }

                    report["by_period"][period_key]["total_amount"] += amount
                    report["by_period"][period_key]["total_cost"] += cost

                    if usage_type_key not in report["by_period"][period_key]["by_type"]:
                        report["by_period"][period_key]["by_type"][usage_type_key] = 0
                    report["by_period"][period_key]["by_type"][usage_type_key] += amount

                except ValueError:
                    pass

        return report

    def get_usage_analytics(
        self,
        contract_id: int,
        date_range: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Get advanced usage analytics for a contract.

        Args:
            contract_id: Contract ID to analyze
            date_range: Optional date range for analysis

        Returns:
            Dictionary with usage analytics and trends
        """
        usage_report = self.get_usage_report(contract_id, period=date_range)
        usage_limits = self.check_usage_limits(contract_id)

        analytics = {
            "contract_id": contract_id,
            "summary": {
                "total_usage_types": len(usage_report["by_type"]),
                "total_cost": usage_report["cost_summary"]["total_cost"],
                "billable_percentage": 0,
                "avg_daily_usage": {},
                "peak_usage_day": None,
            },
            "trends": {"monthly_growth": {}, "usage_patterns": {}, "cost_trends": {}},
            "efficiency_metrics": {
                "cost_per_unit": {},
                "utilization_rates": {},
                "waste_indicators": [],
            },
            "forecasts": {
                "projected_monthly_cost": 0,
                "limit_breach_risk": {},
                "optimization_opportunities": [],
            },
        }

        # Summary calculations
        total_cost = usage_report["cost_summary"]["total_cost"]
        billable_cost = usage_report["cost_summary"]["billable_cost"]

        if total_cost > 0:
            analytics["summary"]["billable_percentage"] = (
                billable_cost / total_cost
            ) * 100

        # Calculate daily averages
        if date_range:
            start_date, end_date = date_range
            days = (
                (end_date - start_date).days + 1
                if hasattr(start_date, "total_seconds")
                else 30
            )

            for usage_type, total_amount in usage_report["total_usage"].items():
                analytics["summary"]["avg_daily_usage"][usage_type] = (
                    total_amount / days
                )

        # Trend analysis
        periods = list(usage_report["by_period"].keys())
        periods.sort()

        if len(periods) >= 2:
            for i in range(1, len(periods)):
                current_period = periods[i]
                previous_period = periods[i - 1]

                current_cost = usage_report["by_period"][current_period]["total_cost"]
                previous_cost = usage_report["by_period"][previous_period]["total_cost"]

                if previous_cost > 0:
                    growth_rate = ((current_cost - previous_cost) / previous_cost) * 100
                    analytics["trends"]["monthly_growth"][current_period] = growth_rate

        # Efficiency metrics
        for usage_type, type_data in usage_report["by_type"].items():
            if type_data["total_amount"] > 0:
                analytics["efficiency_metrics"]["cost_per_unit"][usage_type] = (
                    type_data["total_cost"] / type_data["total_amount"]
                )

        # Limit analysis and forecasting
        if usage_limits.get("has_limits"):
            for usage_type, limit_info in usage_limits["limits"].items():
                current_usage = limit_info["current_usage"]
                limit_amount = limit_info["limit"]

                # Calculate breach risk (simple linear projection)
                if date_range and hasattr(date_range[0], "total_seconds"):
                    days_in_period = (date_range[1] - date_range[0]).days + 1
                    days_in_month = 30  # Approximate
                    projected_monthly = (current_usage / days_in_period) * days_in_month

                    breach_risk = "low"
                    if projected_monthly > limit_amount:
                        breach_risk = "high"
                    elif projected_monthly > (limit_amount * 0.9):
                        breach_risk = "medium"

                    analytics["forecasts"]["limit_breach_risk"][usage_type] = {
                        "projected_monthly": projected_monthly,
                        "risk_level": breach_risk,
                    }

        # Optimization opportunities
        if analytics["summary"]["billable_percentage"] < 80:
            analytics["forecasts"]["optimization_opportunities"].append(
                "Consider reviewing non-billable usage allocation"
            )

        for usage_type, growth_rate in analytics["trends"]["monthly_growth"].items():
            if growth_rate > 20:  # More than 20% growth
                analytics["forecasts"]["optimization_opportunities"].append(
                    f"Monitor {usage_type} usage growth trend ({growth_rate: .1f}% increase)"
                )

        return analytics

    # ======================================== Contract Modifications and Amendments
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def add_amendment(
        self, contract_id: int, amendment_data: Dict[str, Any]
    ) -> CreateResponse:
        """
        Add an amendment to a contract.

        Args:
            contract_id: Contract ID to amend
            amendment_data: Dictionary containing amendment information
                Required fields:
                - amendment_type: Type of amendment ('value_change', 'scope_change', 'term_extension', etc.)
                - description: Description of the amendment
                - effective_date: When the amendment takes effect
                Optional fields:
                - value_change: New contract value (for value changes)
                - end_date_change: New end date (for term extensions)
                - approval_required: Whether amendment requires approval
                - approver_ids: List of required approver IDs
                - justification: Business justification for change

        Returns:
            Created amendment record

        Raises:
            ValueError: If required fields are missing
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["amendment_type", "description", "effective_date"]
        missing_fields = [
            field for field in required_fields if field not in amendment_data
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate the contract exists
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        amendment_record = {
            "contractID": contract_id,
            "amendmentType": amendment_data["amendment_type"],
            "description": amendment_data["description"],
            "effectiveDate": amendment_data["effective_date"],
            "status": "pending",
            "createdDate": datetime.now().isoformat(),
            "createdBy": amendment_data.get("created_by", "system"),
            "approvalRequired": amendment_data.get("approval_required", True),
            **{k: v for k, v in amendment_data.items() if k not in required_fields},
        }

        return self.client.create("ContractAmendments", amendment_record)

    def approve_amendment(
        self,
        amendment_id: int,
        approver_id: int,
        approval_notes: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Approve a contract amendment.

        Args:
            amendment_id: Amendment ID to approve
            approver_id: ID of the approving user
            approval_notes: Optional approval notes

        Returns:
            Updated amendment data

        Raises:
            ValueError: If amendment not found
            AutotaskAPIError: If the API request fails
        """
        try:
            amendment = self.client.get("ContractAmendments", amendment_id)
        except Exception:
            raise ValueError(f"Amendment {amendment_id} not found")

        if not amendment:
            raise ValueError(f"Amendment {amendment_id} not found")

        update_data = {
            "status": "approved",
            "approvedBy": approver_id,
            "approvedDate": datetime.now().isoformat(),
        }

        if approval_notes:
            update_data["approvalNotes"] = approval_notes

        # Apply the amendment to the contract
        amendment_response = self.client.update(
            "ContractAmendments", amendment_id, update_data
        )

        if amendment_response.get("success"):
            self._apply_amendment(amendment)

        return amendment_response

    def _apply_amendment(self, amendment: Dict[str, Any]) -> None:
        """Apply an approved amendment to the contract."""
        contract_id = amendment.get("contractID")
        amendment_type = amendment.get("amendmentType")

        contract_updates = {
            "lastModified": datetime.now().isoformat(),
            "amendmentCount": (amendment.get("amendmentCount", 0)) + 1,
        }

        # Apply specific amendment types
        if amendment_type == "value_change" and amendment.get("valueChange"):
            contract_updates["ContractValue"] = amendment["valueChange"]
        elif amendment_type == "term_extension" and amendment.get("endDateChange"):
            contract_updates["EndDate"] = amendment["endDateChange"]
        elif amendment_type == "scope_change":
            # Add scope change details to contract notes
            existing_notes = self.get(contract_id).get("contractNotes", "")
            scope_change = f"\n\nScope Amendment ({datetime.now().strftime('%Y-%m-%d')}): {amendment.get('description', '')}"
            contract_updates["contractNotes"] = existing_notes + scope_change

        # Update the contract with amendment changes
        if contract_updates:
            self.update(contract_id, contract_updates)

    def get_contract_history(
        self,
        contract_id: int,
        include_amendments: bool = True,
        include_renewals: bool = True,
    ) -> Dict[str, Any]:
        """
        Get complete history of a contract including amendments and renewals.

        Args:
            contract_id: Contract ID to get history for
            include_amendments: Include amendment history
            include_renewals: Include renewal history

        Returns:
            Dictionary with complete contract history
        """
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        history = {
            "contract_id": contract_id,
            "contract_name": contract.get("ContractName", ""),
            "current_status": contract.get("Status"),
            "created_date": contract.get("CreateDate"),
            "timeline": [],
            "amendments": [],
            "renewals": [],
            "value_changes": [],
            "status_changes": [],
        }

        # Add contract creation to timeline
        if contract.get("CreateDate"):
            history["timeline"].append(
                {
                    "date": contract["CreateDate"],
                    "type": "creation",
                    "description": f"Contract '{contract.get('ContractName', '')}' created",
                    "value": contract.get("ContractValue"),
                }
            )

        # Get amendments if requested
        if include_amendments:
            amendment_filters = [
                QueryFilter(field="contractID", op="eq", value=contract_id)
            ]
            try:
                amendments = self.client.query(
                    "ContractAmendments", filters=amendment_filters
                )
                history["amendments"] = amendments

                # Add amendments to timeline
                for amendment in amendments:
                    history["timeline"].append(
                        {
                            "date": amendment.get("effectiveDate"),
                            "type": "amendment",
                            "amendment_type": amendment.get("amendmentType"),
                            "description": amendment.get("description"),
                            "status": amendment.get("status"),
                            "value_change": amendment.get("valueChange"),
                        }
                    )

                    # Track value changes
                    if amendment.get("valueChange"):
                        history["value_changes"].append(
                            {
                                "date": amendment.get("effectiveDate"),
                                "old_value": contract.get("ContractValue"),
                                "new_value": amendment["valueChange"],
                                "reason": amendment.get("description"),
                            }
                        )
            except Exception:
                # Fallback if ContractAmendments doesn't exist
                pass

        # Get renewals if requested
        if include_renewals:
            renewal_filters = [
                QueryFilter(field="ParentContractID", op="eq", value=contract_id)
            ]
            try:
                renewals = self.query(filters=renewal_filters)
                history["renewals"] = renewals

                # Add renewals to timeline
                for renewal in renewals:
                    history["timeline"].append(
                        {
                            "date": renewal.get("RenewalDate"),
                            "type": "renewal",
                            "description": f"Contract renewed as {renewal.get('ContractName', '')}",
                            "new_contract_id": renewal.get("id"),
                            "value": renewal.get("ContractValue"),
                        }
                    )
            except Exception:
                pass

        # Sort timeline by date
        history["timeline"].sort(key=lambda x: x.get("date", "") or "")

        # Calculate history metrics
        history["metrics"] = {
            "total_amendments": len(history["amendments"]),
            "total_renewals": len(history["renewals"]),
            "contract_age_days": self._calculate_contract_age(contract),
            "average_amendment_frequency": self._calculate_amendment_frequency(
                history["amendments"]
            ),
            "value_volatility": self._calculate_value_volatility(
                history["value_changes"]
            ),
        }

        return history

    def get_amendment_analytics(
        self,
        contract_id: Optional[int] = None,
        date_range: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Get analytics on contract amendments.

        Args:
            contract_id: Optional filter by specific contract
            date_range: Optional date range for analysis

        Returns:
            Dictionary with amendment analytics
        """
        filters = []

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createdDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createdDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        try:
            amendments = self.client.query("ContractAmendments", filters=filters)
        except Exception:
            amendments = []

        analytics = {
            "total_amendments": len(amendments),
            "by_type": {},
            "by_status": {"pending": 0, "approved": 0, "rejected": 0, "cancelled": 0},
            "approval_metrics": {
                "approval_rate": 0,
                "avg_approval_time": 0,
                "pending_approvals": 0,
            },
            "value_impact": {
                "total_value_increase": 0,
                "total_value_decrease": 0,
                "net_value_change": 0,
            },
            "trends": {"monthly_amendments": {}, "most_common_types": []},
        }

        approval_times = []
        value_changes = []

        for amendment in amendments:
            # Type analysis
            amendment_type = amendment.get("amendmentType", "unknown")
            if amendment_type not in analytics["by_type"]:
                analytics["by_type"][amendment_type] = 0
            analytics["by_type"][amendment_type] += 1

            # Status analysis
            status = amendment.get("status", "pending")
            if status in analytics["by_status"]:
                analytics["by_status"][status] += 1

            # Approval time calculation
            created_date = amendment.get("createdDate")
            approved_date = amendment.get("approvedDate")

            if created_date and approved_date:
                try:
                    created = datetime.fromisoformat(
                        created_date.replace("Z", "+00:00")
                    )
                    approved = datetime.fromisoformat(
                        approved_date.replace("Z", "+00:00")
                    )
                    approval_time = (approved - created).total_seconds() / 86400  # Days
                    approval_times.append(approval_time)
                except ValueError:
                    pass

            # Value impact analysis
            value_change = amendment.get("valueChange")
            if value_change:
                change_amount = float(value_change) - float(
                    amendment.get("originalValue", value_change)
                )
                value_changes.append(change_amount)

                if change_amount > 0:
                    analytics["value_impact"]["total_value_increase"] += change_amount
                else:
                    analytics["value_impact"]["total_value_decrease"] += abs(
                        change_amount
                    )

            # Monthly trends
            if created_date:
                try:
                    month_key = datetime.fromisoformat(
                        created_date.replace("Z", "+00:00")
                    ).strftime("%Y-%m")
                    if month_key not in analytics["trends"]["monthly_amendments"]:
                        analytics["trends"]["monthly_amendments"][month_key] = 0
                    analytics["trends"]["monthly_amendments"][month_key] += 1
                except ValueError:
                    pass

        # Calculate metrics
        total_amendments = len(amendments)
        if total_amendments > 0:
            approved_count = analytics["by_status"]["approved"]
            analytics["approval_metrics"]["approval_rate"] = (
                approved_count / total_amendments
            ) * 100
            analytics["approval_metrics"]["pending_approvals"] = analytics["by_status"][
                "pending"
            ]

        if approval_times:
            analytics["approval_metrics"]["avg_approval_time"] = sum(
                approval_times
            ) / len(approval_times)

        if value_changes:
            analytics["value_impact"]["net_value_change"] = sum(value_changes)

        # Most common amendment types
        type_counts = [
            (type_name, count) for type_name, count in analytics["by_type"].items()
        ]
        type_counts.sort(key=lambda x: x[1], reverse=True)
        analytics["trends"]["most_common_types"] = type_counts[:5]

        return analytics

    def _calculate_contract_age(self, contract: Dict[str, Any]) -> int:
        """Calculate contract age in days."""
        created_date = contract.get("CreateDate")
        if not created_date:
            return 0

        try:
            created = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
            # Convert to naive datetime for comparison
            created_naive = created.replace(tzinfo=None)
            return (datetime.now() - created_naive).days
        except ValueError:
            return 0

    def _calculate_amendment_frequency(self, amendments: List[Dict[str, Any]]) -> float:
        """Calculate average days between amendments."""
        if len(amendments) < 2:
            return 0

        dates = []
        for amendment in amendments:
            created_date = amendment.get("createdDate")
            if created_date:
                try:
                    dates.append(
                        datetime.fromisoformat(created_date.replace("Z", "+00:00"))
                    )
                except ValueError:
                    pass

        if len(dates) < 2:
            return 0

        dates.sort()
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i - 1]).days
            intervals.append(interval)

        return sum(intervals) / len(intervals) if intervals else 0

    def _calculate_value_volatility(self, value_changes: List[Dict[str, Any]]) -> float:
        """Calculate contract value volatility as standard deviation of changes."""
        if not value_changes:
            return 0

        changes = []
        for change in value_changes:
            old_val = float(change.get("old_value", 0))
            new_val = float(change.get("new_value", 0))
            if old_val > 0:
                pct_change = ((new_val - old_val) / old_val) * 100
                changes.append(pct_change)

        if not changes:
            return 0

        mean_change = sum(changes) / len(changes)
        variance = sum((x - mean_change) ** 2 for x in changes) / len(changes)
        return variance**0.5  # Standard deviation

    # ======================================== Validation and Helper Methods
    # =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =  =
    def validate_contract_data(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate contract data before creation or update.

        Args:
            contract_data: Contract data to validate

        Returns:
            Dictionary with validation results including errors and warnings
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
        }

        # Required field validation
        required_fields = ["ContractName", "AccountID"]
        for field in required_fields:
            if field not in contract_data or not contract_data[field]:
                validation_result["errors"].append(
                    f"Required field '{field}' is missing or empty"
                )

        # Contract name validation
        contract_name = contract_data.get("ContractName", "")
        if contract_name:
            if len(contract_name) < 3:
                validation_result["errors"].append(
                    "Contract name must be at least 3 characters long"
                )
            elif len(contract_name) > 255:
                validation_result["errors"].append(
                    "Contract name cannot exceed 255 characters"
                )

        # Date validation
        start_date = contract_data.get("StartDate")
        end_date = contract_data.get("EndDate")

        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if end_dt <= start_dt:
                    validation_result["errors"].append(
                        "End date must be after start date"
                    )

                # Check for reasonable contract duration
                duration_days = (end_dt - start_dt).days
                if duration_days > 3650:  # More than 10 years
                    validation_result["warnings"].append(
                        f"Contract duration is very long ({duration_days} days). Consider shorter terms with renewal options."
                    )
                elif duration_days < 30:  # Less than a month
                    validation_result["warnings"].append(
                        f"Contract duration is very short ({duration_days} days). Consider if this is intentional."
                    )

            except ValueError as e:
                validation_result["errors"].append(f"Invalid date format: {e}")

        # Contract value validation
        contract_value = contract_data.get("ContractValue")
        if contract_value is not None:
            try:
                value = float(contract_value)
                if value < 0:
                    validation_result["errors"].append(
                        "Contract value cannot be negative"
                    )
                elif value == 0:
                    validation_result["warnings"].append(
                        "Contract value is zero. Consider if this is intentional."
                    )
                elif value > 10000000:  # More than $10M
                    validation_result["warnings"].append(
                        "Contract value is very high. Ensure proper approval processes are followed."
                    )
            except (ValueError, TypeError):
                validation_result["errors"].append(
                    "Contract value must be a valid number"
                )

        # Contract type validation
        contract_type = contract_data.get("ContractType")
        if contract_type is not None:
            valid_types = [
                ContractType.RECURRING_SERVICE,
                ContractType.TIME_AND_MATERIALS,
                ContractType.FIXED_PRICE,
            ]
            if contract_type not in valid_types:
                validation_result["errors"].append(
                    f"Invalid contract type: {contract_type}"
                )

        # Status validation
        status = contract_data.get("Status")
        if status is not None:
            valid_statuses = [
                ContractStatus.ACTIVE,
                ContractStatus.DRAFT,
                ContractStatus.ON_HOLD,
            ]
            if status not in valid_statuses:
                validation_result["errors"].append(f"Invalid contract status: {status}")

        # Business logic recommendations
        if contract_type == ContractType.TIME_AND_MATERIALS and not contract_data.get(
            "milestones"
        ):
            validation_result["recommendations"].append(
                "Milestone-based contracts should have defined milestones"
            )

        if contract_type == ContractType.RECURRING_SERVICE and not contract_data.get(
            "billingFrequency"
        ):
            validation_result["recommendations"].append(
                "Recurring service contracts should specify billing frequency"
            )

        # Set overall validity
        validation_result["is_valid"] = len(validation_result["errors"]) == 0

        return validation_result

    def get_contract_summary(self, contract_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a contract.

        Args:
            contract_id: Contract ID to summarize

        Returns:
            Dictionary with contract summary information
        """
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        # Get related data
        try:
            billing_data = self.calculate_contract_value(contract_id)
        except Exception:
            billing_data = {"billed_to_date": 0, "remaining_value": 0}

        try:
            service_metrics = self.get_service_metrics(contract_id)
        except Exception:
            service_metrics = {"sla_compliance": {"compliance_rate": 0}}

        try:
            milestone_analytics = self.get_milestone_analytics(contract_id)
        except Exception:
            milestone_analytics = {"completion_rate": 0, "total_milestones": 0}

        summary = {
            "contract_id": contract_id,
            "basic_info": {
                "name": contract.get("ContractName", ""),
                "account_id": contract.get("AccountID"),
                "status": contract.get("Status"),
                "type": contract.get("ContractType"),
                "start_date": contract.get("StartDate"),
                "end_date": contract.get("EndDate"),
                "value": contract.get("ContractValue", 0),
            },
            "financial_summary": {
                "total_value": billing_data.get("contract_value", 0),
                "billed_to_date": billing_data.get("billed_to_date", 0),
                "remaining_value": billing_data.get("remaining_value", 0),
                "billing_utilization": billing_data.get("billing_utilization", 0),
            },
            "performance_summary": {
                "sla_compliance_rate": service_metrics.get("sla_compliance", {}).get(
                    "compliance_rate", 0
                ),
                "milestone_completion_rate": milestone_analytics.get(
                    "completion_rate", 0
                ),
                "total_milestones": milestone_analytics.get("total_milestones", 0),
            },
            "key_metrics": {},
            "health_indicators": {},
            "recommendations": [],
        }

        # Calculate key metrics
        contract_value = float(summary["basic_info"]["value"] or 0)
        billed_amount = summary["financial_summary"]["billed_to_date"]

        if contract_value > 0:
            summary["key_metrics"]["revenue_recognition"] = (
                billed_amount / contract_value
            ) * 100
        else:
            summary["key_metrics"]["revenue_recognition"] = 0

        # Health indicators
        sla_compliance = summary["performance_summary"]["sla_compliance_rate"]
        if sla_compliance >= 95:
            summary["health_indicators"]["sla_health"] = "excellent"
        elif sla_compliance >= 90:
            summary["health_indicators"]["sla_health"] = "good"
        elif sla_compliance >= 80:
            summary["health_indicators"]["sla_health"] = "needs_attention"
        else:
            summary["health_indicators"]["sla_health"] = "critical"

        # Contract lifecycle status
        end_date = contract.get("EndDate")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                days_remaining = (end_dt - datetime.now()).days

                if days_remaining <= 30:
                    summary["health_indicators"]["renewal_urgency"] = "urgent"
                elif days_remaining <= 90:
                    summary["health_indicators"]["renewal_urgency"] = "soon"
                else:
                    summary["health_indicators"]["renewal_urgency"] = "normal"

                summary["key_metrics"]["days_until_expiry"] = days_remaining
            except ValueError:
                summary["health_indicators"]["renewal_urgency"] = "unknown"

        # Generate recommendations
        if summary["health_indicators"].get("sla_health") in [
            "needs_attention",
            "critical",
        ]:
            summary["recommendations"].append(
                "Review service delivery processes to improve SLA compliance"
            )

        if summary["health_indicators"].get("renewal_urgency") == "urgent":
            summary["recommendations"].append("Schedule renewal discussion immediately")

        if summary["financial_summary"]["billing_utilization"] < 50:
            summary["recommendations"].append(
                "Review billing processes - low utilization rate"
            )

        return summary

    def get_contract_health_check(self, contract_id: int) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on a contract.

        Args:
            contract_id: Contract ID to check

        Returns:
            Dictionary with health check results and recommendations
        """
        contract = self.get(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        health_check = {
            "contract_id": contract_id,
            "overall_health": "unknown",
            "health_score": 0,
            "checks": {
                "financial_health": {"status": "unknown", "score": 0, "issues": []},
                "operational_health": {"status": "unknown", "score": 0, "issues": []},
                "compliance_health": {"status": "unknown", "score": 0, "issues": []},
                "lifecycle_health": {"status": "unknown", "score": 0, "issues": []},
            },
            "critical_issues": [],
            "recommendations": [],
            "action_items": [],
        }

        # Financial health check
        try:
            billing_data = self.calculate_contract_value(contract_id)
            utilization = billing_data.get("billing_utilization", 0)

            financial_score = 100
            if utilization > 100:
                health_check["checks"]["financial_health"]["issues"].append(
                    "Billing over contract value"
                )
                financial_score -= 30
            elif utilization < 25:
                health_check["checks"]["financial_health"]["issues"].append(
                    "Low billing utilization"
                )
                financial_score -= 20

            payment_status = billing_data.get("payment_status", {})
            overdue_amount = payment_status.get("overdue", 0)
            if overdue_amount > 0:
                health_check["checks"]["financial_health"]["issues"].append(
                    f"Overdue payments: ${overdue_amount: , .2f}"
                )
                financial_score -= 25

            health_check["checks"]["financial_health"]["score"] = max(
                0, financial_score
            )

        except Exception:
            health_check["checks"]["financial_health"]["issues"].append(
                "Unable to retrieve financial data"
            )

        # Operational health check
        try:
            service_metrics = self.get_service_metrics(contract_id)
            sla_compliance = service_metrics.get("sla_compliance", {}).get(
                "compliance_rate", 0
            )

            operational_score = sla_compliance
            if sla_compliance < 90:
                health_check["checks"]["operational_health"]["issues"].append(
                    f"SLA compliance at {sla_compliance: .1f}%"
                )
            if sla_compliance < 80:
                health_check["critical_issues"].append("Critical SLA compliance issue")

            health_check["checks"]["operational_health"]["score"] = operational_score

        except Exception:
            health_check["checks"]["operational_health"]["issues"].append(
                "Unable to retrieve service metrics"
            )

        # Compliance health check
        compliance_score = 100
        try:
            validation_result = self.validate_contract_data(contract)
            if not validation_result["is_valid"]:
                health_check["checks"]["compliance_health"]["issues"].extend(
                    validation_result["errors"]
                )
                compliance_score = 50  # Failed validation

            health_check["checks"]["compliance_health"]["score"] = compliance_score

        except Exception:
            health_check["checks"]["compliance_health"]["issues"].append(
                "Unable to validate contract data"
            )

        # Lifecycle health check
        lifecycle_score = 100
        end_date = contract.get("EndDate")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                days_remaining = (end_dt - datetime.now()).days

                if days_remaining <= 0:
                    health_check["checks"]["lifecycle_health"]["issues"].append(
                        "Contract has expired"
                    )
                    health_check["critical_issues"].append("Contract expired")
                    lifecycle_score = 0
                elif days_remaining <= 30:
                    health_check["checks"]["lifecycle_health"]["issues"].append(
                        f"Contract expires in {days_remaining} days"
                    )
                    lifecycle_score = 60
                elif days_remaining <= 90:
                    health_check["checks"]["lifecycle_health"]["issues"].append(
                        "Contract renewal needed soon"
                    )
                    lifecycle_score = 80

                health_check["checks"]["lifecycle_health"]["score"] = lifecycle_score

            except ValueError:
                health_check["checks"]["lifecycle_health"]["issues"].append(
                    "Invalid contract end date"
                )

        # Calculate overall health
        scores = [check["score"] for check in health_check["checks"].values()]
        valid_scores = [s for s in scores if s > 0]

        if valid_scores:
            health_check["health_score"] = sum(valid_scores) / len(valid_scores)
        else:
            health_check["health_score"] = 0

        # Determine overall health status
        if health_check["health_score"] >= 90:
            health_check["overall_health"] = "excellent"
        elif health_check["health_score"] >= 75:
            health_check["overall_health"] = "good"
        elif health_check["health_score"] >= 60:
            health_check["overall_health"] = "needs_attention"
        else:
            health_check["overall_health"] = "critical"

        # Generate recommendations and action items
        if health_check["overall_health"] in ["needs_attention", "critical"]:
            health_check["recommendations"].append("Schedule immediate contract review")
            health_check["action_items"].append(
                "Investigate root causes of health issues"
            )

        for check_name, check_data in health_check["checks"].items():
            if check_data["score"] < 70:
                health_check["action_items"].append(
                    f"Address {check_name.replace('_', ' ')} issues"
                )

        # Set health status for each check
        for check_data in health_check["checks"].values():
            score = check_data["score"]
            if score >= 90:
                check_data["status"] = "excellent"
            elif score >= 75:
                check_data["status"] = "good"
            elif score >= 60:
                check_data["status"] = "needs_attention"
            else:
                check_data["status"] = "critical"

        return health_check

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Helper method to validate required fields."""
        missing_fields = [
            field
            for field in required_fields
            if field not in data or data[field] is None
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
