"""
ContractServiceAdjustments Entity for py-autotask

This module provides the ContractServiceAdjustmentsEntity class for managing
contract service adjustments in Autotask. Service adjustments represent changes
to contract services, including modifications to quantities, rates, or terms.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractServiceAdjustmentsEntity(BaseEntity):
    """
    Manages Autotask ContractServiceAdjustments - modifications to contract services.

    Contract service adjustments track changes made to contract services over time,
    including quantity changes, rate adjustments, service upgrades/downgrades,
    and other modifications that affect the contracted services.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractServiceAdjustments"

    # Core CRUD Operations

    def create_service_adjustment(
        self,
        contract_id: int,
        contract_service_id: int,
        adjustment_type: str,
        adjustment_reason: str,
        effective_date: Optional[date] = None,
        quantity_adjustment: Optional[Union[float, Decimal]] = None,
        rate_adjustment: Optional[Union[float, Decimal]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract service adjustment.

        Args:
            contract_id: ID of the contract
            contract_service_id: ID of the contract service being adjusted
            adjustment_type: Type of adjustment (Quantity, Rate, Upgrade, Downgrade, etc.)
            adjustment_reason: Reason for the adjustment
            effective_date: When the adjustment becomes effective
            quantity_adjustment: Change in service quantity
            rate_adjustment: Change in service rate
            **kwargs: Additional fields for the adjustment

        Returns:
            Create response with new adjustment ID

        Example:
            adjustment = client.contract_service_adjustments.create_service_adjustment(
                contract_id=12345,
                contract_service_id=678,
                adjustment_type="Quantity",
                adjustment_reason="Client requested additional licenses",
                quantity_adjustment=5.0,
                effective_date=date(2024, 2, 1)
            )
        """
        if effective_date is None:
            effective_date = date.today()

        adjustment_data = {
            "contractID": contract_id,
            "contractServiceID": contract_service_id,
            "adjustmentType": adjustment_type,
            "adjustmentReason": adjustment_reason,
            "effectiveDate": effective_date.isoformat(),
            "status": "Pending",
            "createdDate": datetime.now().isoformat(),
            **kwargs,
        }

        if quantity_adjustment is not None:
            adjustment_data["quantityAdjustment"] = float(quantity_adjustment)

        if rate_adjustment is not None:
            adjustment_data["rateAdjustment"] = float(rate_adjustment)

        return self.create(adjustment_data)

    def get_adjustments_by_contract(
        self,
        contract_id: int,
        status_filter: Optional[str] = None,
        adjustment_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get service adjustments for a specific contract.

        Args:
            contract_id: ID of the contract
            status_filter: Filter by adjustment status
            adjustment_type: Filter by adjustment type

        Returns:
            List of contract service adjustments
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if status_filter:
            filters.append({"field": "status", "op": "eq", "value": status_filter})

        if adjustment_type:
            filters.append(
                {"field": "adjustmentType", "op": "eq", "value": adjustment_type}
            )

        return self.query(filters=filters).items

    def get_adjustments_by_service(
        self,
        contract_service_id: int,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get adjustments for a specific contract service.

        Args:
            contract_service_id: ID of the contract service
            status_filter: Filter by adjustment status

        Returns:
            List of adjustments for the service
        """
        filters = [
            {"field": "contractServiceID", "op": "eq", "value": contract_service_id}
        ]

        if status_filter:
            filters.append({"field": "status", "op": "eq", "value": status_filter})

        return self.query(filters=filters).items

    # Business Logic Methods

    def approve_adjustment(
        self,
        adjustment_id: int,
        approved_by_resource_id: int,
        approval_notes: Optional[str] = None,
        approval_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Approve a service adjustment.

        Args:
            adjustment_id: ID of the adjustment
            approved_by_resource_id: ID of the approving resource
            approval_notes: Notes about the approval
            approval_date: Date of approval (defaults to today)

        Returns:
            Update response with approval details
        """
        if approval_date is None:
            approval_date = date.today()

        update_data = {
            "status": "Approved",
            "approvedByResourceID": approved_by_resource_id,
            "approvalDate": approval_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if approval_notes:
            update_data["approvalNotes"] = approval_notes

        return self.update_by_id(adjustment_id, update_data)

    def reject_adjustment(
        self,
        adjustment_id: int,
        rejected_by_resource_id: int,
        rejection_reason: str,
        rejection_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Reject a service adjustment.

        Args:
            adjustment_id: ID of the adjustment
            rejected_by_resource_id: ID of the rejecting resource
            rejection_reason: Reason for rejection
            rejection_date: Date of rejection (defaults to today)

        Returns:
            Update response with rejection details
        """
        if rejection_date is None:
            rejection_date = date.today()

        update_data = {
            "status": "Rejected",
            "rejectedByResourceID": rejected_by_resource_id,
            "rejectionReason": rejection_reason,
            "rejectionDate": rejection_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        return self.update_by_id(adjustment_id, update_data)

    def implement_adjustment(
        self,
        adjustment_id: int,
        implemented_by_resource_id: int,
        implementation_date: Optional[date] = None,
        implementation_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark an adjustment as implemented.

        Args:
            adjustment_id: ID of the adjustment
            implemented_by_resource_id: ID of the implementing resource
            implementation_date: Date of implementation (defaults to today)
            implementation_notes: Notes about the implementation

        Returns:
            Update response with implementation details
        """
        if implementation_date is None:
            implementation_date = date.today()

        update_data = {
            "status": "Implemented",
            "implementedByResourceID": implemented_by_resource_id,
            "implementationDate": implementation_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if implementation_notes:
            update_data["implementationNotes"] = implementation_notes

        return self.update_by_id(adjustment_id, update_data)

    def calculate_adjustment_impact(
        self,
        adjustment_id: int,
    ) -> Dict[str, Any]:
        """
        Calculate the financial impact of a service adjustment.

        Args:
            adjustment_id: ID of the adjustment

        Returns:
            Financial impact calculation
        """
        adjustment = self.get(adjustment_id)
        if not adjustment:
            raise ValueError(f"Adjustment {adjustment_id} not found")

        quantity_adjustment = Decimal(str(adjustment.get("quantityAdjustment", 0)))
        rate_adjustment = Decimal(str(adjustment.get("rateAdjustment", 0)))

        # Would typically need to get current service details to calculate full impact
        # For now, we'll calculate based on the adjustment values provided

        monthly_impact = Decimal("0")
        annual_impact = Decimal("0")

        # If we have rate adjustment and quantity info
        if rate_adjustment != 0:
            # Assuming monthly billing - would need service details for actual calculation
            monthly_impact += rate_adjustment
            annual_impact += rate_adjustment * 12

        if quantity_adjustment != 0:
            # Would need unit price from service to calculate properly
            # This is a placeholder calculation
            estimated_unit_price = Decimal(
                str(adjustment.get("estimatedUnitPrice", 100))
            )
            quantity_impact = quantity_adjustment * estimated_unit_price
            monthly_impact += quantity_impact
            annual_impact += quantity_impact * 12

        return {
            "adjustment_id": adjustment_id,
            "contract_id": adjustment.get("contractID"),
            "contract_service_id": adjustment.get("contractServiceID"),
            "adjustment_type": adjustment.get("adjustmentType"),
            "quantity_change": quantity_adjustment,
            "rate_change": rate_adjustment,
            "estimated_monthly_impact": monthly_impact,
            "estimated_annual_impact": annual_impact,
            "effective_date": adjustment.get("effectiveDate"),
            "calculation_date": datetime.now().isoformat(),
        }

    def create_quantity_adjustment(
        self,
        contract_id: int,
        contract_service_id: int,
        quantity_change: Union[float, Decimal],
        adjustment_reason: str,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a quantity-specific adjustment.

        Args:
            contract_id: ID of the contract
            contract_service_id: ID of the contract service
            quantity_change: Change in quantity (positive for increase, negative for decrease)
            adjustment_reason: Reason for the quantity change
            effective_date: When the adjustment becomes effective

        Returns:
            Create response
        """
        adjustment_type = (
            "Quantity Increase" if quantity_change > 0 else "Quantity Decrease"
        )

        return self.create_service_adjustment(
            contract_id=contract_id,
            contract_service_id=contract_service_id,
            adjustment_type=adjustment_type,
            adjustment_reason=adjustment_reason,
            effective_date=effective_date,
            quantity_adjustment=quantity_change,
        )

    def create_rate_adjustment(
        self,
        contract_id: int,
        contract_service_id: int,
        rate_change: Union[float, Decimal],
        adjustment_reason: str,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a rate-specific adjustment.

        Args:
            contract_id: ID of the contract
            contract_service_id: ID of the contract service
            rate_change: Change in rate (positive for increase, negative for decrease)
            adjustment_reason: Reason for the rate change
            effective_date: When the adjustment becomes effective

        Returns:
            Create response
        """
        adjustment_type = "Rate Increase" if rate_change > 0 else "Rate Decrease"

        return self.create_service_adjustment(
            contract_id=contract_id,
            contract_service_id=contract_service_id,
            adjustment_type=adjustment_type,
            adjustment_reason=adjustment_reason,
            effective_date=effective_date,
            rate_adjustment=rate_change,
        )

    def get_pending_adjustments(
        self,
        contract_id: Optional[int] = None,
        days_ahead: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get pending adjustments that are scheduled to take effect soon.

        Args:
            contract_id: Optional filter by specific contract
            days_ahead: Number of days to look ahead for effective dates

        Returns:
            List of pending adjustments
        """
        from datetime import timedelta

        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        filters = [
            {"field": "status", "op": "in", "value": ["Pending", "Approved"]},
            {"field": "effectiveDate", "op": "lte", "value": future_date.isoformat()},
        ]

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        return self.query(filters=filters).items

    def get_adjustment_summary(
        self,
        contract_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get a summary of service adjustments for a contract.

        Args:
            contract_id: ID of the contract
            date_from: Start date for the summary period
            date_to: End date for the summary period

        Returns:
            Summary of adjustments with statistics
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if date_from:
            filters.append(
                {"field": "effectiveDate", "op": "gte", "value": date_from.isoformat()}
            )
        if date_to:
            filters.append(
                {"field": "effectiveDate", "op": "lte", "value": date_to.isoformat()}
            )

        adjustments = self.query(filters=filters).items

        # Categorize adjustments
        by_type = {}
        by_status = {}
        total_quantity_changes = Decimal("0")
        total_rate_changes = Decimal("0")
        total_financial_impact = Decimal("0")

        for adjustment in adjustments:
            adjustment_type = adjustment.get("adjustmentType", "Unknown")
            status = adjustment.get("status", "Unknown")

            by_type[adjustment_type] = by_type.get(adjustment_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

            quantity_adj = adjustment.get("quantityAdjustment", 0)
            rate_adj = adjustment.get("rateAdjustment", 0)

            if quantity_adj:
                total_quantity_changes += Decimal(str(quantity_adj))
            if rate_adj:
                total_rate_changes += Decimal(str(rate_adj))

            # Calculate financial impact if available
            impact = self.calculate_adjustment_impact(adjustment.get("id"))
            if impact:
                total_financial_impact += impact.get("estimated_monthly_impact", 0)

        return {
            "contract_id": contract_id,
            "summary_period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "totals": {
                "total_adjustments": len(adjustments),
                "pending_adjustments": by_status.get("Pending", 0),
                "approved_adjustments": by_status.get("Approved", 0),
                "implemented_adjustments": by_status.get("Implemented", 0),
                "rejected_adjustments": by_status.get("Rejected", 0),
                "total_quantity_changes": total_quantity_changes,
                "total_rate_changes": total_rate_changes,
                "estimated_monthly_impact": total_financial_impact,
            },
            "by_type": by_type,
            "by_status": by_status,
            "adjustments": adjustments,
        }

    def bulk_approve_adjustments(
        self,
        adjustment_ids: List[int],
        approved_by_resource_id: int,
        approval_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve multiple adjustments in bulk.

        Args:
            adjustment_ids: List of adjustment IDs to approve
            approved_by_resource_id: ID of the approving resource
            approval_notes: Notes about the bulk approval

        Returns:
            Summary of the bulk approval operation
        """
        results = []

        for adjustment_id in adjustment_ids:
            try:
                result = self.approve_adjustment(
                    adjustment_id=adjustment_id,
                    approved_by_resource_id=approved_by_resource_id,
                    approval_notes=approval_notes,
                )
                results.append(
                    {
                        "adjustment_id": adjustment_id,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "adjustment_id": adjustment_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_adjustments": len(adjustment_ids),
            "successful_approvals": len(successful),
            "failed_approvals": len(failed),
            "approved_by_resource_id": approved_by_resource_id,
            "approval_date": date.today().isoformat(),
            "results": results,
        }

    def get_adjustment_workflow_status(
        self,
        adjustment_id: int,
    ) -> Dict[str, Any]:
        """
        Get the workflow status and history of an adjustment.

        Args:
            adjustment_id: ID of the adjustment

        Returns:
            Workflow status with key dates and responsible parties
        """
        adjustment = self.get(adjustment_id)
        if not adjustment:
            return {
                "adjustment_id": adjustment_id,
                "error": "Adjustment not found",
            }

        workflow_stages = [
            {
                "stage": "Created",
                "date": adjustment.get("createdDate"),
                "resource_id": adjustment.get("createdByResourceID"),
                "notes": adjustment.get("adjustmentReason"),
                "completed": True,
            },
            {
                "stage": "Approved",
                "date": adjustment.get("approvalDate"),
                "resource_id": adjustment.get("approvedByResourceID"),
                "notes": adjustment.get("approvalNotes"),
                "completed": adjustment.get("status") in ["Approved", "Implemented"],
            },
            {
                "stage": "Implemented",
                "date": adjustment.get("implementationDate"),
                "resource_id": adjustment.get("implementedByResourceID"),
                "notes": adjustment.get("implementationNotes"),
                "completed": adjustment.get("status") == "Implemented",
            },
        ]

        # Check for rejection
        if adjustment.get("status") == "Rejected":
            workflow_stages.append(
                {
                    "stage": "Rejected",
                    "date": adjustment.get("rejectionDate"),
                    "resource_id": adjustment.get("rejectedByResourceID"),
                    "notes": adjustment.get("rejectionReason"),
                    "completed": True,
                }
            )

        # Calculate progress percentage
        completed_stages = sum(1 for stage in workflow_stages if stage["completed"])
        total_stages = len(workflow_stages) - (
            1 if adjustment.get("status") == "Rejected" else 0
        )
        progress_percentage = (completed_stages / max(total_stages, 1)) * 100

        return {
            "adjustment_id": adjustment_id,
            "current_status": adjustment.get("status"),
            "progress_percentage": progress_percentage,
            "effective_date": adjustment.get("effectiveDate"),
            "workflow_stages": workflow_stages,
            "next_action": self._determine_next_action(adjustment),
        }

    def _determine_next_action(self, adjustment: Dict[str, Any]) -> str:
        """
        Determine the next action required for an adjustment.

        Args:
            adjustment: The adjustment data

        Returns:
            Description of the next required action
        """
        status = adjustment.get("status")

        if status == "Pending":
            return "Awaiting approval"
        elif status == "Approved":
            return "Ready for implementation"
        elif status == "Implemented":
            return "Complete - no further action required"
        elif status == "Rejected":
            return "Rejected - no further action unless resubmitted"
        else:
            return "Unknown status - review required"
