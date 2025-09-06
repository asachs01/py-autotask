"""
Contracts entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ..types import ContractData, EntityDict, QueryFilter
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ContractStatus(Enum):
    """Contract status values from Autotask API."""

    ACTIVE = 1
    INACTIVE = 2
    CANCELLED = 3
    EXPIRED = 4
    PENDING = 5
    DRAFT = 6
    APPROVED = 7
    REJECTED = 8


class ContractType(Enum):
    """Contract type values from Autotask API."""

    RECURRING_SERVICE = 1
    BLOCK_HOURS = 2
    FIXED_PRICE = 3
    RETAINER = 4
    TIME_AND_MATERIALS = 5
    MAINTENANCE = 6
    SUBSCRIPTION = 7


class ServiceLevelStatus(Enum):
    """Service level compliance status."""

    MEETING = "meeting"
    WARNING = "warning"
    BREACH = "breach"
    NOT_APPLICABLE = "not_applicable"


class ContractsEntity(BaseEntity):
    """
    Handles all Contract-related operations for the Autotask API.

    Contracts in Autotask represent service agreements, maintenance
    contracts, and other ongoing service arrangements with customers.
    This entity provides comprehensive contract management including billing,
    service level tracking, milestone management, renewal alerts, and usage tracking.
    """

    def __init__(self, client, entity_name: str = "Contracts"):
        super().__init__(client, entity_name)
        self.logger = logging.getLogger(f"{__name__}.{entity_name}")

    def create_contract(
        self,
        contract_name: str,
        account_id: int,
        contract_type: int = 1,  # 1 = Recurring Service
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
            contract_type: Type of contract (1=Recurring Service, etc.)
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

    def get_expiring_contracts(
        self, days_ahead: int = 30, limit: Optional[int] = None
    ) -> List[ContractData]:
        """
        Get contracts expiring within a specified number of days.

        Args:
            days_ahead: Number of days to look ahead for expiring contracts
            limit: Maximum number of contracts to return

        Returns:
            List of expiring contracts
        """
        from datetime import datetime, timedelta

        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

        filters = [
            QueryFilter(field="EndDate", op="lte", value=future_date),
            QueryFilter(field="Status", op="eq", value=1),  # Active
        ]

        return self.query(filters=filters, max_records=limit)

    # Contract Billing Integration Methods

    def get_contract_billing_summary(self, contract_id: int) -> Dict[str, Any]:
        """
        Get comprehensive billing summary for a contract.

        Args:
            contract_id: Contract ID to get billing summary for

        Returns:
            Dictionary containing billing summary information including:
            - total_contract_value: Total value of the contract
            - billed_to_date: Amount billed to date
            - remaining_value: Remaining contract value
            - billing_schedule: Next billing dates
            - payment_status: Current payment status
            - line_items: List of contract line items

        Example:
            billing_summary = client.contracts.get_contract_billing_summary(12345)
            print(f"Remaining value: ${billing_summary['remaining_value']}")
        """
        self.logger.info(f"Getting billing summary for contract {contract_id}")

        try:
            # Get the contract details
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            # Get contract line items for detailed billing breakdown
            line_items_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract_id)
            ]

            # Query ContractServices for line items
            line_items_response = self.client.query(
                "ContractServices",
                {"filter": [f.model_dump() for f in line_items_filters]},
            )

            line_items = line_items_response.items if line_items_response.items else []

            # Calculate billing totals
            total_contract_value = float(contract.get("ContractValue", 0))
            billed_to_date = sum(
                float(item.get("InvoicedAmount", 0)) for item in line_items
            )
            remaining_value = total_contract_value - billed_to_date

            # Get billing schedule information
            billing_schedule = self._get_contract_billing_schedule(contract)

            # Determine payment status
            payment_status = self._determine_payment_status(contract, line_items)

            billing_summary = {
                "contract_id": contract_id,
                "contract_name": contract.get("ContractName"),
                "total_contract_value": total_contract_value,
                "billed_to_date": billed_to_date,
                "remaining_value": remaining_value,
                "billing_percentage": (
                    (billed_to_date / total_contract_value * 100)
                    if total_contract_value > 0
                    else 0
                ),
                "billing_schedule": billing_schedule,
                "payment_status": payment_status,
                "line_items_count": len(line_items),
                "line_items": line_items,
                "currency": contract.get("Currency", "USD"),
                "last_updated": datetime.now().isoformat(),
            }

            self.logger.info(f"Billing summary calculated for contract {contract_id}")
            return billing_summary

        except Exception as e:
            self.logger.error(
                f"Error getting billing summary for contract {contract_id}: {e}"
            )
            raise

    def generate_contract_invoice(
        self,
        contract_id: int,
        billing_period_start: Optional[str] = None,
        billing_period_end: Optional[str] = None,
        include_usage: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate invoice data for a contract billing period.

        Args:
            contract_id: Contract ID to generate invoice for
            billing_period_start: Start date for billing period (ISO format)
            billing_period_end: End date for billing period (ISO format)
            include_usage: Whether to include usage-based billing items

        Returns:
            Dictionary containing invoice data ready for billing system

        Example:
            invoice_data = client.contracts.generate_contract_invoice(
                12345,
                billing_period_start="2024-01-01",
                billing_period_end="2024-01-31"
            )
        """
        self.logger.info(f"Generating invoice for contract {contract_id}")

        try:
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            # Set default billing period if not provided
            if not billing_period_end:
                billing_period_end = datetime.now().isoformat()
            if not billing_period_start:
                period_start = datetime.fromisoformat(
                    billing_period_end.replace("Z", "")
                ) - timedelta(days=30)
                billing_period_start = period_start.isoformat()

            # Get billable items for the period
            invoice_items = []

            # Add recurring service charges
            if contract.get("ContractType") == ContractType.RECURRING_SERVICE.value:
                recurring_items = self._get_recurring_charges(
                    contract, billing_period_start, billing_period_end
                )
                invoice_items.extend(recurring_items)

            # Add usage-based charges if enabled
            if include_usage:
                usage_items = self._get_usage_charges(
                    contract_id, billing_period_start, billing_period_end
                )
                invoice_items.extend(usage_items)

            # Add milestone-based charges
            milestone_items = self._get_milestone_charges(
                contract_id, billing_period_start, billing_period_end
            )
            invoice_items.extend(milestone_items)

            # Calculate totals
            subtotal = sum(item.get("amount", 0) for item in invoice_items)
            tax_rate = float(contract.get("TaxRate", 0))
            tax_amount = subtotal * (tax_rate / 100)
            total_amount = subtotal + tax_amount

            invoice_data = {
                "contract_id": contract_id,
                "contract_name": contract.get("ContractName"),
                "account_id": contract.get("AccountID"),
                "billing_period": {
                    "start": billing_period_start,
                    "end": billing_period_end,
                },
                "invoice_items": invoice_items,
                "subtotal": subtotal,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "currency": contract.get("Currency", "USD"),
                "generated_date": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            }

            self.logger.info(
                f"Invoice generated for contract {contract_id}, total: ${total_amount}"
            )
            return invoice_data

        except Exception as e:
            self.logger.error(
                f"Error generating invoice for contract {contract_id}: {e}"
            )
            raise

    # Service Level Tracking Methods

    def get_contract_service_levels(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get service levels associated with a contract.

        Args:
            contract_id: Contract ID to get service levels for

        Returns:
            List of service level agreements with current status

        Example:
            slas = client.contracts.get_contract_service_levels(12345)
            for sla in slas:
                print(f"SLA: {sla['name']}, Status: {sla['compliance_status']}")
        """
        self.logger.info(f"Getting service levels for contract {contract_id}")

        try:
            # Query ContractServiceLevelAgreements for this contract
            filters = [QueryFilter(field="ContractID", op="eq", value=contract_id)]
            sla_response = self.client.query(
                "ContractServiceLevelAgreements",
                {"filter": [f.model_dump() for f in filters]},
            )

            service_levels = []
            for sla in sla_response.items if sla_response.items else []:
                # Calculate current compliance status
                compliance_status = self._check_sla_compliance(sla)

                service_level = {
                    "sla_id": sla.get("id"),
                    "name": sla.get("Name"),
                    "description": sla.get("Description"),
                    "metric_type": sla.get("MetricType"),
                    "target_value": sla.get("TargetValue"),
                    "warning_threshold": sla.get("WarningThreshold"),
                    "breach_threshold": sla.get("BreachThreshold"),
                    "measurement_period": sla.get("MeasurementPeriod"),
                    "compliance_status": compliance_status,
                    "current_performance": self._get_current_sla_performance(sla),
                    "last_measured": sla.get("LastMeasured"),
                    "active": sla.get("IsActive", True),
                }
                service_levels.append(service_level)

            self.logger.info(
                f"Retrieved {len(service_levels)} service levels for contract {contract_id}"
            )
            return service_levels

        except Exception as e:
            self.logger.error(
                f"Error getting service levels for contract {contract_id}: {e}"
            )
            raise

    def check_service_level_compliance(
        self, contract_id: int, sla_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if service levels are being met for a contract.

        Args:
            contract_id: Contract ID to check compliance for
            sla_id: Specific SLA ID to check (optional, checks all if not provided)

        Returns:
            Dictionary with compliance status and details

        Example:
            compliance = client.contracts.check_service_level_compliance(12345)
            if compliance['overall_status'] == ServiceLevelStatus.BREACH.value:
                print("SLA breach detected!")
        """
        self.logger.info(
            f"Checking service level compliance for contract {contract_id}"
        )

        try:
            service_levels = self.get_contract_service_levels(contract_id)

            if sla_id:
                # Filter to specific SLA
                service_levels = [
                    sla for sla in service_levels if sla["sla_id"] == sla_id
                ]
                if not service_levels:
                    raise ValueError(
                        f"SLA {sla_id} not found for contract {contract_id}"
                    )

            # Analyze compliance across all SLAs
            compliance_results = []
            breach_count = 0
            warning_count = 0
            meeting_count = 0

            for sla in service_levels:
                status = sla["compliance_status"]
                compliance_results.append(
                    {
                        "sla_id": sla["sla_id"],
                        "name": sla["name"],
                        "status": status,
                        "current_performance": sla["current_performance"],
                        "target_value": sla["target_value"],
                    }
                )

                if status == ServiceLevelStatus.BREACH.value:
                    breach_count += 1
                elif status == ServiceLevelStatus.WARNING.value:
                    warning_count += 1
                elif status == ServiceLevelStatus.MEETING.value:
                    meeting_count += 1

            # Determine overall compliance status
            if breach_count > 0:
                overall_status = ServiceLevelStatus.BREACH.value
            elif warning_count > 0:
                overall_status = ServiceLevelStatus.WARNING.value
            else:
                overall_status = ServiceLevelStatus.MEETING.value

            compliance_report = {
                "contract_id": contract_id,
                "overall_status": overall_status,
                "total_slas": len(service_levels),
                "meeting_count": meeting_count,
                "warning_count": warning_count,
                "breach_count": breach_count,
                "compliance_percentage": (
                    (meeting_count / len(service_levels) * 100)
                    if service_levels
                    else 100
                ),
                "sla_details": compliance_results,
                "checked_at": datetime.now().isoformat(),
            }

            self.logger.info(
                f"Service level compliance checked for contract {contract_id}: {overall_status}"
            )
            return compliance_report

        except Exception as e:
            self.logger.error(
                f"Error checking service level compliance for contract {contract_id}: {e}"
            )
            raise

    # Milestone Management Methods

    def add_contract_milestone(
        self,
        contract_id: int,
        milestone_name: str,
        due_date: str,
        description: Optional[str] = None,
        deliverables: Optional[List[str]] = None,
        milestone_value: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Add a milestone to a contract.

        Args:
            contract_id: Contract ID to add milestone to
            milestone_name: Name of the milestone
            due_date: Due date for milestone completion (ISO format)
            description: Optional description of the milestone
            deliverables: List of deliverable descriptions
            milestone_value: Financial value of the milestone
            **kwargs: Additional milestone fields

        Returns:
            Created milestone data

        Example:
            milestone = client.contracts.add_contract_milestone(
                12345,
                "Phase 1 Completion",
                "2024-03-31",
                description="Complete initial implementation phase",
                milestone_value=25000.00
            )
        """
        self.logger.info(
            f"Adding milestone '{milestone_name}' to contract {contract_id}"
        )

        try:
            milestone_data = {
                "ContractID": contract_id,
                "MilestoneName": milestone_name,
                "DueDate": due_date,
                "Status": "Not Started",
                "IsActive": True,
                **kwargs,
            }

            if description:
                milestone_data["Description"] = description
            if milestone_value is not None:
                milestone_data["MilestoneValue"] = milestone_value
            if deliverables:
                milestone_data["Deliverables"] = "; ".join(deliverables)

            # Create milestone using ContractMilestones entity
            milestone = self.client.create_entity("ContractMilestones", milestone_data)

            self.logger.info(
                f"Milestone '{milestone_name}' added to contract {contract_id}"
            )
            return milestone

        except Exception as e:
            self.logger.error(f"Error adding milestone to contract {contract_id}: {e}")
            raise

    def get_upcoming_milestones(
        self,
        days_ahead: int = 30,
        contract_id: Optional[int] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming milestones across contracts or for a specific contract.

        Args:
            days_ahead: Number of days to look ahead for milestones
            contract_id: Specific contract ID (optional, gets all contracts if not provided)
            status_filter: Filter by milestone status (optional)

        Returns:
            List of upcoming milestones with contract information

        Example:
            upcoming = client.contracts.get_upcoming_milestones(14)
            for milestone in upcoming:
                print(f"Milestone: {milestone['name']}, Due: {milestone['due_date']}")
        """
        self.logger.info(f"Getting upcoming milestones for next {days_ahead} days")

        try:
            future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

            filters = [
                QueryFilter(field="DueDate", op="lte", value=future_date),
                QueryFilter(
                    field="DueDate", op="gte", value=datetime.now().isoformat()
                ),
                QueryFilter(field="IsActive", op="eq", value="true"),
            ]

            if contract_id:
                filters.append(
                    QueryFilter(field="ContractID", op="eq", value=contract_id)
                )

            if status_filter:
                filters.append(
                    QueryFilter(field="Status", op="eq", value=status_filter)
                )

            milestone_response = self.client.query(
                "ContractMilestones", {"filter": [f.model_dump() for f in filters]}
            )

            milestones = []
            for milestone in (
                milestone_response.items if milestone_response.items else []
            ):
                # Get contract information
                contract = self.get(milestone.get("ContractID"))

                milestone_info = {
                    "milestone_id": milestone.get("id"),
                    "name": milestone.get("MilestoneName"),
                    "description": milestone.get("Description"),
                    "due_date": milestone.get("DueDate"),
                    "status": milestone.get("Status"),
                    "milestone_value": milestone.get("MilestoneValue"),
                    "deliverables": (
                        milestone.get("Deliverables", "").split("; ")
                        if milestone.get("Deliverables")
                        else []
                    ),
                    "contract_id": milestone.get("ContractID"),
                    "contract_name": contract.get("ContractName") if contract else None,
                    "account_id": contract.get("AccountID") if contract else None,
                    "days_until_due": (
                        datetime.fromisoformat(
                            milestone.get("DueDate").replace("Z", "")
                        )
                        - datetime.now()
                    ).days,
                    "progress_percentage": milestone.get("ProgressPercentage", 0),
                    "is_critical": milestone.get("IsCritical", False),
                }
                milestones.append(milestone_info)

            # Sort by due date
            milestones.sort(key=lambda x: x["due_date"])

            self.logger.info(f"Retrieved {len(milestones)} upcoming milestones")
            return milestones

        except Exception as e:
            self.logger.error(f"Error getting upcoming milestones: {e}")
            raise

    # Renewal Management Methods

    def get_contracts_expiring_soon(
        self,
        days_ahead: int = 60,
        include_auto_renewing: bool = False,
        account_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get contracts expiring within specified days with renewal information.

        Args:
            days_ahead: Number of days to look ahead for expiring contracts
            include_auto_renewing: Whether to include auto-renewing contracts
            account_id: Filter by specific account ID (optional)

        Returns:
            List of expiring contracts with renewal details

        Example:
            expiring = client.contracts.get_contracts_expiring_soon(30)
            for contract in expiring:
                print(f"Contract: {contract['name']}, Expires: {contract['end_date']}")
        """
        self.logger.info(f"Getting contracts expiring in next {days_ahead} days")

        try:
            future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

            filters = [
                QueryFilter(field="EndDate", op="lte", value=future_date),
                QueryFilter(
                    field="EndDate", op="gte", value=datetime.now().isoformat()
                ),
                QueryFilter(field="Status", op="eq", value=ContractStatus.ACTIVE.value),
            ]

            if account_id:
                filters.append(
                    QueryFilter(field="AccountID", op="eq", value=account_id)
                )

            if not include_auto_renewing:
                filters.append(
                    QueryFilter(field="IsAutoRenewing", op="ne", value="true")
                )

            expiring_response = self.query(filters=filters)

            expiring_contracts = []
            for contract in expiring_response.items if expiring_response.items else []:
                contract_info = {
                    "contract_id": contract.get("id"),
                    "name": contract.get("ContractName"),
                    "account_id": contract.get("AccountID"),
                    "start_date": contract.get("StartDate"),
                    "end_date": contract.get("EndDate"),
                    "contract_value": contract.get("ContractValue"),
                    "contract_type": contract.get("ContractType"),
                    "is_auto_renewing": contract.get("IsAutoRenewing", False),
                    "renewal_term": contract.get("RenewalTerm"),
                    "days_until_expiry": (
                        datetime.fromisoformat(contract.get("EndDate").replace("Z", ""))
                        - datetime.now()
                    ).days,
                    "renewal_alert_sent": contract.get("RenewalAlertSent", False),
                    "renewal_probability": self._calculate_renewal_probability(
                        contract
                    ),
                    "last_modified": contract.get("LastModifiedDateTime"),
                    "urgency_level": self._determine_renewal_urgency(
                        contract, days_ahead
                    ),
                }
                expiring_contracts.append(contract_info)

            # Sort by days until expiry
            expiring_contracts.sort(key=lambda x: x["days_until_expiry"])

            self.logger.info(f"Retrieved {len(expiring_contracts)} expiring contracts")
            return expiring_contracts

        except Exception as e:
            self.logger.error(f"Error getting expiring contracts: {e}")
            raise

    def set_renewal_alert(
        self,
        contract_id: int,
        alert_days_before: int = 60,
        alert_type: str = "email",
        recipients: Optional[List[str]] = None,
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Configure renewal alerts for a contract.

        Args:
            contract_id: Contract ID to set alerts for
            alert_days_before: Days before expiry to send alert
            alert_type: Type of alert (email, notification, etc.)
            recipients: List of recipient email addresses or user IDs
            custom_message: Custom alert message

        Returns:
            Alert configuration details

        Example:
            alert_config = client.contracts.set_renewal_alert(
                12345,
                alert_days_before=30,
                recipients=["manager@company.com"]
            )
        """
        self.logger.info(f"Setting renewal alert for contract {contract_id}")

        try:
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            # Calculate alert date
            end_date = datetime.fromisoformat(contract.get("EndDate").replace("Z", ""))
            alert_date = end_date - timedelta(days=alert_days_before)

            alert_config = {
                "contract_id": contract_id,
                "alert_date": alert_date.isoformat(),
                "alert_days_before": alert_days_before,
                "alert_type": alert_type,
                "recipients": recipients or [],
                "custom_message": custom_message,
                "created_date": datetime.now().isoformat(),
                "is_active": True,
                "contract_end_date": contract.get("EndDate"),
            }

            # Store alert configuration (would typically be in a separate alerts table)
            # For now, update the contract with alert information
            update_data = {
                "id": contract_id,
                "RenewalAlertDays": alert_days_before,
                "RenewalAlertType": alert_type,
                "RenewalAlertRecipients": ", ".join(recipients) if recipients else "",
                "CustomRenewalMessage": custom_message,
            }

            self.update(update_data)

            self.logger.info(f"Renewal alert configured for contract {contract_id}")
            return alert_config

        except Exception as e:
            self.logger.error(
                f"Error setting renewal alert for contract {contract_id}: {e}"
            )
            raise

    # Usage Tracking Methods

    def track_contract_usage(
        self,
        contract_id: int,
        usage_type: str,
        usage_amount: float,
        usage_date: Optional[str] = None,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Track usage against contract limits.

        Args:
            contract_id: Contract ID to track usage for
            usage_type: Type of usage (hours, licenses, storage, etc.)
            usage_amount: Amount of usage to track
            usage_date: Date of usage (ISO format, defaults to now)
            resource_id: Resource ID associated with usage (optional)
            description: Description of the usage

        Returns:
            Usage tracking record with current totals

        Example:
            usage_record = client.contracts.track_contract_usage(
                12345,
                "hours",
                8.5,
                description="Development work on Project Alpha"
            )
        """
        self.logger.info(
            f"Tracking usage for contract {contract_id}: {usage_amount} {usage_type}"
        )

        try:
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            if not usage_date:
                usage_date = datetime.now().isoformat()

            # Create usage record
            usage_data = {
                "ContractID": contract_id,
                "UsageType": usage_type,
                "UsageAmount": usage_amount,
                "UsageDate": usage_date,
                "Description": description or "",
                "ResourceID": resource_id,
                "CreatedDateTime": datetime.now().isoformat(),
            }

            # Store usage record (would typically be in ContractUsage table)
            usage_record = self.client.create_entity("ContractUsage", usage_data)

            # Get updated usage summary
            usage_summary = self.get_contract_usage_summary(contract_id)

            tracking_result = {
                "usage_record_id": (
                    usage_record.item_id if hasattr(usage_record, "item_id") else None
                ),
                "contract_id": contract_id,
                "usage_type": usage_type,
                "usage_amount": usage_amount,
                "usage_date": usage_date,
                "current_total": usage_summary.get("usage_totals", {}).get(
                    usage_type, 0
                ),
                "remaining_allocation": usage_summary.get(
                    "remaining_allocations", {}
                ).get(usage_type, 0),
                "utilization_percentage": usage_summary.get(
                    "utilization_percentages", {}
                ).get(usage_type, 0),
                "is_over_limit": usage_summary.get("over_limit_types", []),
                "recorded_at": datetime.now().isoformat(),
            }

            self.logger.info(f"Usage tracked for contract {contract_id}")
            return tracking_result

        except Exception as e:
            self.logger.error(f"Error tracking usage for contract {contract_id}: {e}")
            raise

    def get_contract_usage_summary(self, contract_id: int) -> Dict[str, Any]:
        """
        Get summary of usage against contract limits.

        Args:
            contract_id: Contract ID to get usage summary for

        Returns:
            Dictionary containing usage summary with allocations and utilization

        Example:
            usage_summary = client.contracts.get_contract_usage_summary(12345)
            for usage_type, percentage in usage_summary['utilization_percentages'].items():
                print(f"{usage_type}: {percentage}% utilized")
        """
        self.logger.info(f"Getting usage summary for contract {contract_id}")

        try:
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            # Get contract allocations/limits
            allocations = self._get_contract_allocations(contract)

            # Get usage records for this contract
            usage_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract_id)
            ]
            usage_response = self.client.query(
                "ContractUsage", {"filter": [f.model_dump() for f in usage_filters]}
            )

            usage_records = usage_response.items if usage_response.items else []

            # Calculate usage totals by type
            usage_totals = {}
            for record in usage_records:
                usage_type = record.get("UsageType", "unknown")
                usage_amount = float(record.get("UsageAmount", 0))
                usage_totals[usage_type] = (
                    usage_totals.get(usage_type, 0) + usage_amount
                )

            # Calculate remaining allocations and utilization percentages
            remaining_allocations = {}
            utilization_percentages = {}
            over_limit_types = []

            for usage_type, allocated in allocations.items():
                used = usage_totals.get(usage_type, 0)
                remaining = max(0, allocated - used)
                remaining_allocations[usage_type] = remaining

                if allocated > 0:
                    utilization_pct = (used / allocated) * 100
                    utilization_percentages[usage_type] = utilization_pct

                    if used > allocated:
                        over_limit_types.append(usage_type)

            # Get recent usage trends
            usage_trends = self._calculate_usage_trends(usage_records)

            usage_summary = {
                "contract_id": contract_id,
                "contract_name": contract.get("ContractName"),
                "allocations": allocations,
                "usage_totals": usage_totals,
                "remaining_allocations": remaining_allocations,
                "utilization_percentages": utilization_percentages,
                "over_limit_types": over_limit_types,
                "usage_trends": usage_trends,
                "total_records": len(usage_records),
                "summary_date": datetime.now().isoformat(),
            }

            self.logger.info(f"Usage summary calculated for contract {contract_id}")
            return usage_summary

        except Exception as e:
            self.logger.error(
                f"Error getting usage summary for contract {contract_id}: {e}"
            )
            raise

    # Contract Modification Methods

    def amend_contract(
        self,
        contract_id: int,
        amendment_type: str,
        changes: Dict[str, Any],
        effective_date: Optional[str] = None,
        amendment_reason: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a contract amendment.

        Args:
            contract_id: Contract ID to amend
            amendment_type: Type of amendment (value_change, term_extension, scope_change, etc.)
            changes: Dictionary of changes to make
            effective_date: Date when amendment becomes effective (ISO format)
            amendment_reason: Reason for the amendment
            **kwargs: Additional amendment fields

        Returns:
            Amendment details with original and new values

        Example:
            amendment = client.contracts.amend_contract(
                12345,
                "value_change",
                {"ContractValue": 150000},
                amendment_reason="Scope expansion approved"
            )
        """
        self.logger.info(f"Creating amendment for contract {contract_id}")

        try:
            original_contract = self.get(contract_id)
            if not original_contract:
                raise ValueError(f"Contract {contract_id} not found")

            if not effective_date:
                effective_date = datetime.now().isoformat()

            # Create amendment record
            amendment_data = {
                "ContractID": contract_id,
                "AmendmentType": amendment_type,
                "AmendmentReason": amendment_reason or "",
                "EffectiveDate": effective_date,
                "CreatedDateTime": datetime.now().isoformat(),
                "Status": "Pending",
                **kwargs,
            }

            # Store original values for audit trail
            original_values = {}
            for field, new_value in changes.items():
                original_values[field] = original_contract.get(field)

            amendment_data["OriginalValues"] = str(original_values)  # JSON string
            amendment_data["NewValues"] = str(changes)  # JSON string

            # Create amendment record
            amendment_record = self.client.create_entity(
                "ContractAmendments", amendment_data
            )

            # Apply changes to contract if auto-approved
            if kwargs.get("auto_approve", False):
                update_data = {"id": contract_id, **changes}
                self.update(update_data)

                # Update amendment status
                self.client.update(
                    "ContractAmendments",
                    {"id": amendment_record.item_id, "Status": "Applied"},
                )

            amendment_result = {
                "amendment_id": (
                    amendment_record.item_id
                    if hasattr(amendment_record, "item_id")
                    else None
                ),
                "contract_id": contract_id,
                "amendment_type": amendment_type,
                "amendment_reason": amendment_reason,
                "effective_date": effective_date,
                "original_values": original_values,
                "new_values": changes,
                "status": "Applied" if kwargs.get("auto_approve", False) else "Pending",
                "created_at": datetime.now().isoformat(),
            }

            self.logger.info(f"Amendment created for contract {contract_id}")
            return amendment_result

        except Exception as e:
            self.logger.error(
                f"Error creating amendment for contract {contract_id}: {e}"
            )
            raise

    def get_contract_history(
        self,
        contract_id: int,
        include_amendments: bool = True,
        include_usage: bool = False,
        include_milestones: bool = False,
    ) -> Dict[str, Any]:
        """
        Get history of contract changes and activities.

        Args:
            contract_id: Contract ID to get history for
            include_amendments: Whether to include amendment history
            include_usage: Whether to include usage history
            include_milestones: Whether to include milestone history

        Returns:
            Comprehensive contract history with timeline

        Example:
            history = client.contracts.get_contract_history(12345, include_amendments=True)
            for event in history['timeline']:
                print(f"{event['date']}: {event['description']}")
        """
        self.logger.info(f"Getting history for contract {contract_id}")

        try:
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            timeline = []

            # Add contract creation event
            timeline.append(
                {
                    "date": contract.get("CreateDate", ""),
                    "event_type": "contract_created",
                    "description": f"Contract '{contract.get('ContractName')}' created",
                    "details": {
                        "contract_value": contract.get("ContractValue"),
                        "start_date": contract.get("StartDate"),
                        "end_date": contract.get("EndDate"),
                    },
                }
            )

            # Add amendments if requested
            if include_amendments:
                amendment_filters = [
                    QueryFilter(field="ContractID", op="eq", value=contract_id)
                ]
                amendment_response = self.client.query(
                    "ContractAmendments",
                    {"filter": [f.model_dump() for f in amendment_filters]},
                )

                for amendment in (
                    amendment_response.items if amendment_response.items else []
                ):
                    timeline.append(
                        {
                            "date": amendment.get("EffectiveDate", ""),
                            "event_type": "amendment",
                            "description": f"Amendment: {amendment.get('AmendmentType', 'Unknown')}",
                            "details": {
                                "amendment_id": amendment.get("id"),
                                "reason": amendment.get("AmendmentReason"),
                                "status": amendment.get("Status"),
                                "original_values": amendment.get("OriginalValues"),
                                "new_values": amendment.get("NewValues"),
                            },
                        }
                    )

            # Add usage history if requested
            if include_usage:
                usage_filters = [
                    QueryFilter(field="ContractID", op="eq", value=contract_id)
                ]
                usage_response = self.client.query(
                    "ContractUsage", {"filter": [f.model_dump() for f in usage_filters]}
                )

                for usage in usage_response.items if usage_response.items else []:
                    timeline.append(
                        {
                            "date": usage.get("UsageDate", ""),
                            "event_type": "usage",
                            "description": f"Usage: {usage.get('UsageAmount')} {usage.get('UsageType')}",
                            "details": {
                                "usage_id": usage.get("id"),
                                "usage_type": usage.get("UsageType"),
                                "usage_amount": usage.get("UsageAmount"),
                                "resource_id": usage.get("ResourceID"),
                                "description": usage.get("Description"),
                            },
                        }
                    )

            # Add milestone history if requested
            if include_milestones:
                milestone_filters = [
                    QueryFilter(field="ContractID", op="eq", value=contract_id)
                ]
                milestone_response = self.client.query(
                    "ContractMilestones",
                    {"filter": [f.model_dump() for f in milestone_filters]},
                )

                for milestone in (
                    milestone_response.items if milestone_response.items else []
                ):
                    timeline.append(
                        {
                            "date": milestone.get("DueDate", ""),
                            "event_type": "milestone",
                            "description": f"Milestone: {milestone.get('MilestoneName')}",
                            "details": {
                                "milestone_id": milestone.get("id"),
                                "status": milestone.get("Status"),
                                "milestone_value": milestone.get("MilestoneValue"),
                                "progress_percentage": milestone.get(
                                    "ProgressPercentage"
                                ),
                            },
                        }
                    )

            # Sort timeline by date
            timeline.sort(key=lambda x: x["date"])

            contract_history = {
                "contract_id": contract_id,
                "contract_name": contract.get("ContractName"),
                "timeline": timeline,
                "summary": {
                    "total_events": len(timeline),
                    "amendments_count": len(
                        [e for e in timeline if e["event_type"] == "amendment"]
                    ),
                    "usage_events_count": len(
                        [e for e in timeline if e["event_type"] == "usage"]
                    ),
                    "milestone_events_count": len(
                        [e for e in timeline if e["event_type"] == "milestone"]
                    ),
                    "first_event_date": timeline[0]["date"] if timeline else None,
                    "last_event_date": timeline[-1]["date"] if timeline else None,
                },
                "generated_at": datetime.now().isoformat(),
            }

            self.logger.info(
                f"History retrieved for contract {contract_id}: {len(timeline)} events"
            )
            return contract_history

        except Exception as e:
            self.logger.error(f"Error getting history for contract {contract_id}: {e}")
            raise

    # Helper Methods

    def get_active_contracts_by_account(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get all active contracts for a specific account with enhanced information.

        Args:
            account_id: Account ID to get contracts for

        Returns:
            List of active contracts with billing and status information

        Example:
            contracts = client.contracts.get_active_contracts_by_account(67890)
            for contract in contracts:
                print(f"Contract: {contract['name']}, Value: ${contract['value']}")
        """
        self.logger.info(f"Getting active contracts for account {account_id}")

        try:
            filters = [
                QueryFilter(field="AccountID", op="eq", value=account_id),
                QueryFilter(field="Status", op="eq", value=ContractStatus.ACTIVE.value),
            ]

            contracts_response = self.query(filters=filters)

            enhanced_contracts = []
            for contract in (
                contracts_response.items if contracts_response.items else []
            ):
                # Get billing summary
                try:
                    billing_summary = self.get_contract_billing_summary(
                        contract.get("id")
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Could not get billing summary for contract {contract.get('id')}: {e}"
                    )
                    billing_summary = {}

                # Calculate days remaining
                end_date = contract.get("EndDate")
                days_remaining = 0
                if end_date:
                    try:
                        end_dt = datetime.fromisoformat(end_date.replace("Z", ""))
                        days_remaining = (end_dt - datetime.now()).days
                    except Exception:
                        pass

                enhanced_contract = {
                    "contract_id": contract.get("id"),
                    "name": contract.get("ContractName"),
                    "value": contract.get("ContractValue", 0),
                    "start_date": contract.get("StartDate"),
                    "end_date": contract.get("EndDate"),
                    "days_remaining": days_remaining,
                    "contract_type": contract.get("ContractType"),
                    "is_auto_renewing": contract.get("IsAutoRenewing", False),
                    "billing_summary": billing_summary,
                    "status": contract.get("Status"),
                    "last_modified": contract.get("LastModifiedDateTime"),
                }
                enhanced_contracts.append(enhanced_contract)

            # Sort by contract value (highest first)
            enhanced_contracts.sort(key=lambda x: x["value"], reverse=True)

            self.logger.info(
                f"Retrieved {len(enhanced_contracts)} active contracts for account {account_id}"
            )
            return enhanced_contracts

        except Exception as e:
            self.logger.error(
                f"Error getting active contracts for account {account_id}: {e}"
            )
            raise

    def calculate_contract_value(
        self,
        contract_id: int,
        include_amendments: bool = True,
        as_of_date: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Calculate total contract value including amendments and usage.

        Args:
            contract_id: Contract ID to calculate value for
            include_amendments: Whether to include amendment value changes
            as_of_date: Calculate value as of specific date (ISO format)

        Returns:
            Dictionary with various value calculations

        Example:
            value_calc = client.contracts.calculate_contract_value(12345)
            print(f"Total value: ${value_calc['total_value']}")
        """
        self.logger.info(f"Calculating contract value for contract {contract_id}")

        try:
            contract = self.get(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            base_value = float(contract.get("ContractValue", 0))

            # Start with base contract value
            calculations = {
                "base_value": base_value,
                "amendment_adjustments": 0.0,
                "usage_charges": 0.0,
                "milestone_values": 0.0,
                "total_value": base_value,
            }

            # Add amendment value changes if requested
            if include_amendments:
                amendment_filters = [
                    QueryFilter(field="ContractID", op="eq", value=contract_id)
                ]
                if as_of_date:
                    amendment_filters.append(
                        QueryFilter(field="EffectiveDate", op="lte", value=as_of_date)
                    )

                amendment_response = self.client.query(
                    "ContractAmendments",
                    {"filter": [f.model_dump() for f in amendment_filters]},
                )

                amendment_total = 0.0
                for amendment in (
                    amendment_response.items if amendment_response.items else []
                ):
                    if amendment.get("Status") == "Applied":
                        # Parse new values to get value changes
                        try:
                            new_values_str = amendment.get("NewValues", "{}")
                            new_values = eval(new_values_str) if new_values_str else {}
                            if "ContractValue" in new_values:
                                # This would need more sophisticated logic to handle incremental vs absolute changes
                                value_change = (
                                    float(new_values["ContractValue"]) - base_value
                                )
                                amendment_total += value_change
                        except Exception:
                            pass

                calculations["amendment_adjustments"] = amendment_total
                calculations["total_value"] += amendment_total

            # Add milestone values
            milestone_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract_id)
            ]
            if as_of_date:
                milestone_filters.append(
                    QueryFilter(field="DueDate", op="lte", value=as_of_date)
                )

            milestone_response = self.client.query(
                "ContractMilestones",
                {"filter": [f.model_dump() for f in milestone_filters]},
            )

            milestone_total = 0.0
            for milestone in (
                milestone_response.items if milestone_response.items else []
            ):
                milestone_value = float(milestone.get("MilestoneValue", 0))
                milestone_total += milestone_value

            calculations["milestone_values"] = milestone_total

            # Get usage charges (if applicable for contract type)
            if contract.get("ContractType") in [
                ContractType.TIME_AND_MATERIALS.value,
                ContractType.BLOCK_HOURS.value,
            ]:
                try:
                    usage_summary = self.get_contract_usage_summary(contract_id)
                    # Calculate usage charges based on rates (simplified)
                    usage_charges = sum(
                        float(total)
                        * 100  # Assuming $100/hour rate - would be more sophisticated
                        for usage_type, total in usage_summary.get(
                            "usage_totals", {}
                        ).items()
                        if usage_type == "hours"
                    )
                    calculations["usage_charges"] = usage_charges
                    calculations["total_value"] += usage_charges
                except Exception as e:
                    self.logger.warning(
                        f"Could not calculate usage charges for contract {contract_id}: {e}"
                    )

            calculations["calculation_date"] = as_of_date or datetime.now().isoformat()

            self.logger.info(
                f"Contract value calculated for {contract_id}: ${calculations['total_value']}"
            )
            return calculations

        except Exception as e:
            self.logger.error(
                f"Error calculating contract value for {contract_id}: {e}"
            )
            raise

    # Private Helper Methods

    def _get_contract_billing_schedule(
        self, contract: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Get billing schedule for a contract."""
        # Simplified billing schedule calculation
        billing_schedule = []
        contract_type = contract.get("ContractType")

        if contract_type == ContractType.RECURRING_SERVICE.value:
            # Monthly billing
            start_date = contract.get("StartDate")
            end_date = contract.get("EndDate")

            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date.replace("Z", ""))
                    end = datetime.fromisoformat(end_date.replace("Z", ""))
                    current = start

                    while (
                        current <= end and len(billing_schedule) < 12
                    ):  # Limit to 12 periods
                        billing_schedule.append(
                            {
                                "period_start": current.isoformat(),
                                "period_end": (
                                    current.replace(month=current.month + 1)
                                    if current.month < 12
                                    else current.replace(year=current.year + 1, month=1)
                                ).isoformat(),
                                "billing_date": (
                                    current + timedelta(days=30)
                                ).isoformat(),
                                "status": "scheduled",
                            }
                        )
                        current = (
                            current.replace(month=current.month + 1)
                            if current.month < 12
                            else current.replace(year=current.year + 1, month=1)
                        )

                except Exception as e:
                    self.logger.warning(f"Error calculating billing schedule: {e}")

        return billing_schedule

    def _determine_payment_status(
        self, contract: Dict[str, Any], line_items: List[Dict[str, Any]]
    ) -> str:
        """Determine the overall payment status for a contract."""
        # Simplified payment status logic
        total_invoiced = sum(
            float(item.get("InvoicedAmount", 0)) for item in line_items
        )
        total_paid = sum(float(item.get("PaidAmount", 0)) for item in line_items)

        if total_invoiced == 0:
            return "no_invoices"
        elif total_paid >= total_invoiced:
            return "paid_in_full"
        elif total_paid > 0:
            return "partially_paid"
        else:
            return "unpaid"

    def _get_recurring_charges(
        self, contract: Dict[str, Any], start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get recurring service charges for a billing period."""
        charges = []

        # Get contract services
        try:
            services_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract.get("id"))
            ]
            services_response = self.client.query(
                "ContractServices",
                {"filter": [f.model_dump() for f in services_filters]},
            )

            for service in services_response.items if services_response.items else []:
                charge = {
                    "item_type": "recurring_service",
                    "description": service.get("ServiceName", "Recurring Service"),
                    "quantity": 1,
                    "rate": float(service.get("Price", 0)),
                    "amount": float(service.get("Price", 0)),
                    "service_id": service.get("id"),
                }
                charges.append(charge)

        except Exception as e:
            self.logger.warning(f"Error getting recurring charges: {e}")

        return charges

    def _get_usage_charges(
        self, contract_id: int, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get usage-based charges for a billing period."""
        charges = []

        try:
            # Get usage records for the period
            usage_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract_id),
                QueryFilter(field="UsageDate", op="gte", value=start_date),
                QueryFilter(field="UsageDate", op="lte", value=end_date),
            ]

            usage_response = self.client.query(
                "ContractUsage", {"filter": [f.model_dump() for f in usage_filters]}
            )

            # Group usage by type and calculate charges
            usage_totals = {}
            for usage in usage_response.items if usage_response.items else []:
                usage_type = usage.get("UsageType", "hours")
                amount = float(usage.get("UsageAmount", 0))
                usage_totals[usage_type] = usage_totals.get(usage_type, 0) + amount

            # Convert usage to charges (simplified rates)
            usage_rates = {"hours": 100.0, "licenses": 50.0, "storage": 0.10}

            for usage_type, total_amount in usage_totals.items():
                rate = usage_rates.get(usage_type, 100.0)
                charge = {
                    "item_type": "usage_charge",
                    "description": f"{usage_type.title()} Usage",
                    "quantity": total_amount,
                    "rate": rate,
                    "amount": total_amount * rate,
                    "usage_type": usage_type,
                }
                charges.append(charge)

        except Exception as e:
            self.logger.warning(f"Error getting usage charges: {e}")

        return charges

    def _get_milestone_charges(
        self, contract_id: int, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Get milestone-based charges for a billing period."""
        charges = []

        try:
            # Get milestones completed in the period
            milestone_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract_id),
                QueryFilter(field="CompletedDate", op="gte", value=start_date),
                QueryFilter(field="CompletedDate", op="lte", value=end_date),
                QueryFilter(field="Status", op="eq", value="Completed"),
            ]

            milestone_response = self.client.query(
                "ContractMilestones",
                {"filter": [f.model_dump() for f in milestone_filters]},
            )

            for milestone in (
                milestone_response.items if milestone_response.items else []
            ):
                milestone_value = float(milestone.get("MilestoneValue", 0))
                if milestone_value > 0:
                    charge = {
                        "item_type": "milestone_charge",
                        "description": f"Milestone: {milestone.get('MilestoneName')}",
                        "quantity": 1,
                        "rate": milestone_value,
                        "amount": milestone_value,
                        "milestone_id": milestone.get("id"),
                    }
                    charges.append(charge)

        except Exception as e:
            self.logger.warning(f"Error getting milestone charges: {e}")

        return charges

    def _check_sla_compliance(self, sla: Dict[str, Any]) -> str:
        """Check compliance status for a single SLA."""
        try:
            target_value = float(sla.get("TargetValue", 100))
            current_performance = self._get_current_sla_performance(sla)
            warning_threshold = float(sla.get("WarningThreshold", 90))
            breach_threshold = float(sla.get("BreachThreshold", 80))

            if current_performance >= target_value:
                return ServiceLevelStatus.MEETING.value
            elif current_performance >= warning_threshold:
                return ServiceLevelStatus.MEETING.value
            elif current_performance >= breach_threshold:
                return ServiceLevelStatus.WARNING.value
            else:
                return ServiceLevelStatus.BREACH.value

        except Exception as e:
            self.logger.warning(f"Error checking SLA compliance: {e}")
            return ServiceLevelStatus.NOT_APPLICABLE.value

    def _get_current_sla_performance(self, sla: Dict[str, Any]) -> float:
        """Get current performance value for an SLA."""
        # Simplified performance calculation
        # In a real implementation, this would query actual performance metrics
        metric_type = sla.get("MetricType", "availability")

        # Mock performance values - in reality this would query actual metrics
        mock_performance = {
            "availability": 99.5,
            "response_time": 95.0,
            "resolution_time": 87.0,
            "customer_satisfaction": 92.0,
        }

        return mock_performance.get(metric_type, 95.0)

    def _calculate_renewal_probability(self, contract: Dict[str, Any]) -> float:
        """Calculate renewal probability based on contract history and performance."""
        # Simplified renewal probability calculation
        base_probability = 0.7  # 70% base probability

        # Adjust based on contract performance
        contract_value = float(contract.get("ContractValue", 0))
        if contract_value > 100000:
            base_probability += 0.1  # Higher value contracts more likely to renew

        # Check if there have been recent amendments (engagement indicator)
        try:
            amendment_filters = [
                QueryFilter(field="ContractID", op="eq", value=contract.get("id"))
            ]
            amendment_response = self.client.query(
                "ContractAmendments",
                {"filter": [f.model_dump() for f in amendment_filters]},
            )

            if amendment_response.items:
                base_probability += 0.15  # Recent amendments indicate engagement

        except Exception:
            pass

        return min(1.0, base_probability)  # Cap at 100%

    def _determine_renewal_urgency(
        self, contract: Dict[str, Any], days_ahead: int
    ) -> str:
        """Determine renewal urgency level."""
        end_date = contract.get("EndDate")
        if not end_date:
            return "unknown"

        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", ""))
            days_until_expiry = (end_dt - datetime.now()).days

            if days_until_expiry <= 30:
                return "critical"
            elif days_until_expiry <= 60:
                return "high"
            elif days_until_expiry <= 90:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"

    def _get_contract_allocations(self, contract: Dict[str, Any]) -> Dict[str, float]:
        """Get contract allocations/limits by type."""
        # Simplified allocation extraction
        # In reality, this would be more sophisticated based on contract terms
        allocations = {}

        contract_type = contract.get("ContractType")

        if contract_type == ContractType.BLOCK_HOURS.value:
            allocations["hours"] = float(contract.get("HourAllocation", 0))
        elif contract_type == ContractType.SUBSCRIPTION.value:
            allocations["licenses"] = float(contract.get("LicenseCount", 0))
            allocations["storage"] = float(contract.get("StorageGB", 0))
        elif contract_type == ContractType.TIME_AND_MATERIALS.value:
            # No specific allocations for T&M contracts
            allocations["hours"] = 999999  # Unlimited

        return allocations

    def _calculate_usage_trends(
        self, usage_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate usage trends from usage records."""
        trends = {
            "monthly_usage": {},
            "daily_average": 0.0,
            "peak_usage_day": None,
            "trend_direction": "stable",
        }

        if not usage_records:
            return trends

        # Group usage by month
        monthly_totals = {}
        daily_totals = {}

        for record in usage_records:
            try:
                usage_date = datetime.fromisoformat(
                    record.get("UsageDate", "").replace("Z", "")
                )
                month_key = usage_date.strftime("%Y-%m")
                day_key = usage_date.strftime("%Y-%m-%d")
                usage_amount = float(record.get("UsageAmount", 0))

                monthly_totals[month_key] = (
                    monthly_totals.get(month_key, 0) + usage_amount
                )
                daily_totals[day_key] = daily_totals.get(day_key, 0) + usage_amount

            except Exception:
                continue

        trends["monthly_usage"] = monthly_totals

        if daily_totals:
            trends["daily_average"] = sum(daily_totals.values()) / len(daily_totals)
            trends["peak_usage_day"] = max(daily_totals, key=daily_totals.get)

        # Determine trend direction (simplified)
        if len(monthly_totals) >= 2:
            monthly_values = list(monthly_totals.values())
            recent_avg = sum(monthly_values[-2:]) / 2
            older_avg = sum(monthly_values[:-2]) / max(1, len(monthly_values) - 2)

            if recent_avg > older_avg * 1.1:
                trends["trend_direction"] = "increasing"
            elif recent_avg < older_avg * 0.9:
                trends["trend_direction"] = "decreasing"
            else:
                trends["trend_direction"] = "stable"

        return trends
