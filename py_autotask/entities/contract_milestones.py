"""
ContractMilestones Entity for py-autotask

This module provides the ContractMilestonesEntity class for managing contract
milestones in Autotask. Contract milestones represent key deliverables or
achievements within a contract that can be tracked for progress monitoring
and billing purposes.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractMilestonesEntity(BaseEntity):
    """
    Manages Autotask ContractMilestones - key deliverables and achievements in contracts.

    Contract milestones represent significant points in a contract's lifecycle,
    such as project phases, deliverables, or billing milestones. These can be
    used to track progress, trigger billing, and manage contract completion.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractMilestones"

    # Core CRUD Operations

    def create_milestone(
        self,
        contract_id: int,
        milestone_name: str,
        target_date: date,
        milestone_value: Optional[Union[float, Decimal]] = None,
        description: Optional[str] = None,
        milestone_type: str = "Deliverable",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract milestone.

        Args:
            contract_id: ID of the contract
            milestone_name: Name of the milestone
            target_date: Target completion date
            milestone_value: Financial value of the milestone
            description: Detailed description of the milestone
            milestone_type: Type of milestone (Deliverable, Billing, Phase, etc.)
            **kwargs: Additional fields for the milestone

        Returns:
            Create response with new milestone ID

        Example:
            milestone = client.contract_milestones.create_milestone(
                contract_id=12345,
                milestone_name="Phase 1 Completion",
                target_date=date(2024, 3, 31),
                milestone_value=25000.00,
                description="Complete initial setup and configuration"
            )
        """
        milestone_data = {
            "contractID": contract_id,
            "milestoneName": milestone_name,
            "targetDate": target_date.isoformat(),
            "milestoneType": milestone_type,
            "status": "Planned",
            **kwargs,
        }

        if milestone_value is not None:
            milestone_data["milestoneValue"] = float(milestone_value)

        if description:
            milestone_data["description"] = description

        return self.create(milestone_data)

    def get_milestones_by_contract(
        self,
        contract_id: int,
        status_filter: Optional[str] = None,
        milestone_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get milestones for a specific contract.

        Args:
            contract_id: ID of the contract
            status_filter: Filter by milestone status
            milestone_type: Filter by milestone type

        Returns:
            List of contract milestones
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if status_filter:
            filters.append({"field": "status", "op": "eq", "value": status_filter})

        if milestone_type:
            filters.append(
                {"field": "milestoneType", "op": "eq", "value": milestone_type}
            )

        return self.query(filters=filters).items

    def get_upcoming_milestones(
        self,
        days_ahead: int = 30,
        contract_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get milestones that are due within a specified number of days.

        Args:
            days_ahead: Number of days to look ahead
            contract_id: Optional filter by specific contract

        Returns:
            List of upcoming milestones
        """
        from datetime import timedelta

        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        filters = [
            {"field": "targetDate", "op": "gte", "value": today.isoformat()},
            {"field": "targetDate", "op": "lte", "value": future_date.isoformat()},
            {"field": "status", "op": "ne", "value": "Completed"},
        ]

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        return self.query(filters=filters).items

    # Business Logic Methods

    def complete_milestone(
        self,
        milestone_id: int,
        completion_date: Optional[date] = None,
        completion_notes: Optional[str] = None,
        actual_value: Optional[Union[float, Decimal]] = None,
    ) -> Dict[str, Any]:
        """
        Mark a milestone as completed.

        Args:
            milestone_id: ID of the milestone
            completion_date: Date of completion (defaults to today)
            completion_notes: Notes about the completion
            actual_value: Actual value achieved (if different from planned)

        Returns:
            Update response with completion details
        """
        if completion_date is None:
            completion_date = date.today()

        update_data = {
            "status": "Completed",
            "completionDate": completion_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if completion_notes:
            update_data["completionNotes"] = completion_notes

        if actual_value is not None:
            update_data["actualValue"] = float(actual_value)

        return self.update_by_id(milestone_id, update_data)

    def update_milestone_status(
        self,
        milestone_id: int,
        new_status: str,
        status_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the status of a milestone.

        Args:
            milestone_id: ID of the milestone
            new_status: New status (Planned, In Progress, On Hold, Completed, Cancelled)
            status_notes: Notes about the status change

        Returns:
            Update response
        """
        update_data = {
            "status": new_status,
            "statusDate": date.today().isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if status_notes:
            update_data["statusNotes"] = status_notes

        return self.update_by_id(milestone_id, update_data)

    def reschedule_milestone(
        self,
        milestone_id: int,
        new_target_date: date,
        reschedule_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reschedule a milestone to a new target date.

        Args:
            milestone_id: ID of the milestone
            new_target_date: New target completion date
            reschedule_reason: Reason for rescheduling

        Returns:
            Update response
        """
        # Store the original target date for audit purposes
        milestone = self.get(milestone_id)
        original_date = milestone.get("targetDate") if milestone else None

        update_data = {
            "targetDate": new_target_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
            "rescheduledDate": datetime.now().isoformat(),
        }

        if original_date:
            update_data["originalTargetDate"] = original_date

        if reschedule_reason:
            update_data["rescheduleReason"] = reschedule_reason

        return self.update_by_id(milestone_id, update_data)

    def get_milestone_progress_report(
        self,
        contract_id: int,
        include_completed: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a progress report for contract milestones.

        Args:
            contract_id: ID of the contract
            include_completed: Whether to include completed milestones

        Returns:
            Progress report with milestone statistics
        """
        if include_completed:
            milestones = self.get_milestones_by_contract(contract_id)
        else:
            milestones = self.get_milestones_by_contract(
                contract_id, status_filter="Planned"
            )
            milestones.extend(
                self.get_milestones_by_contract(
                    contract_id, status_filter="In Progress"
                )
            )

        today = date.today()

        # Categorize milestones
        status_counts = {}
        overdue_milestones = []
        upcoming_milestones = []
        total_value = Decimal("0")
        completed_value = Decimal("0")

        for milestone in milestones:
            status = milestone.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            # Check if overdue
            target_date_str = milestone.get("targetDate")
            if target_date_str and status not in ["Completed", "Cancelled"]:
                target_date = datetime.fromisoformat(
                    target_date_str.replace("Z", "+00:00")
                ).date()
                if target_date < today:
                    overdue_milestones.append(milestone)
                elif (target_date - today).days <= 30:
                    upcoming_milestones.append(milestone)

            # Calculate values
            milestone_value = milestone.get("milestoneValue")
            if milestone_value:
                value = Decimal(str(milestone_value))
                total_value += value
                if status == "Completed":
                    actual_value = milestone.get("actualValue")
                    completed_value += (
                        Decimal(str(actual_value)) if actual_value else value
                    )

        completion_percentage = (
            float(completed_value / total_value * 100) if total_value > 0 else 0
        )

        return {
            "contract_id": contract_id,
            "report_date": today.isoformat(),
            "summary": {
                "total_milestones": len(milestones),
                "completed_milestones": status_counts.get("Completed", 0),
                "in_progress_milestones": status_counts.get("In Progress", 0),
                "planned_milestones": status_counts.get("Planned", 0),
                "overdue_milestones": len(overdue_milestones),
                "upcoming_milestones": len(upcoming_milestones),
                "total_value": total_value,
                "completed_value": completed_value,
                "completion_percentage": completion_percentage,
            },
            "status_breakdown": status_counts,
            "overdue_milestones": overdue_milestones,
            "upcoming_milestones": upcoming_milestones,
        }

    def create_billing_milestone(
        self,
        contract_id: int,
        milestone_name: str,
        billing_amount: Union[float, Decimal],
        target_date: date,
        billing_code_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a billing-specific milestone.

        Args:
            contract_id: ID of the contract
            milestone_name: Name of the billing milestone
            billing_amount: Amount to bill when milestone is completed
            target_date: Target billing date
            billing_code_id: Associated billing code
            **kwargs: Additional fields

        Returns:
            Create response
        """
        milestone_data = {
            "milestoneType": "Billing",
            "milestoneValue": float(billing_amount),
            "isBillable": True,
        }

        if billing_code_id:
            milestone_data["billingCodeID"] = billing_code_id

        milestone_data.update(kwargs)

        return self.create_milestone(
            contract_id=contract_id,
            milestone_name=milestone_name,
            target_date=target_date,
            milestone_value=billing_amount,
            milestone_type="Billing",
            **milestone_data,
        )

    def get_billing_milestones(
        self,
        contract_id: Optional[int] = None,
        ready_to_bill: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get billing milestones, optionally filtered by readiness to bill.

        Args:
            contract_id: Optional filter by specific contract
            ready_to_bill: Filter for milestones ready to bill

        Returns:
            List of billing milestones
        """
        filters = [
            {"field": "milestoneType", "op": "eq", "value": "Billing"},
            {"field": "isBillable", "op": "eq", "value": True},
        ]

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        if ready_to_bill:
            filters.extend(
                [
                    {"field": "status", "op": "eq", "value": "Completed"},
                    {"field": "billedDate", "op": "eq", "value": None},
                ]
            )

        return self.query(filters=filters).items

    def mark_milestone_as_billed(
        self,
        milestone_id: int,
        billed_date: Optional[date] = None,
        invoice_id: Optional[int] = None,
        billed_amount: Optional[Union[float, Decimal]] = None,
    ) -> Dict[str, Any]:
        """
        Mark a billing milestone as billed.

        Args:
            milestone_id: ID of the milestone
            billed_date: Date when milestone was billed
            invoice_id: Associated invoice ID
            billed_amount: Amount actually billed

        Returns:
            Update response
        """
        if billed_date is None:
            billed_date = date.today()

        update_data = {
            "billedDate": billed_date.isoformat(),
            "isBilled": True,
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if invoice_id:
            update_data["invoiceID"] = invoice_id

        if billed_amount is not None:
            update_data["billedAmount"] = float(billed_amount)

        return self.update_by_id(milestone_id, update_data)

    def bulk_update_milestones(
        self,
        milestone_updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update multiple milestones in batch.

        Args:
            milestone_updates: List of updates, each containing milestone_id and update data

        Returns:
            Summary of the bulk update operation
        """
        results = []

        for update in milestone_updates:
            milestone_id = update.get("milestone_id")
            update_data = update.get("update_data", {})

            try:
                result = self.update_by_id(milestone_id, update_data)
                results.append(
                    {
                        "milestone_id": milestone_id,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "milestone_id": milestone_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(milestone_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_milestone_timeline(
        self,
        contract_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get a timeline view of contract milestones.

        Args:
            contract_id: ID of the contract
            start_date: Start date for timeline
            end_date: End date for timeline

        Returns:
            Timeline data with milestones ordered by date
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if start_date:
            filters.append(
                {"field": "targetDate", "op": "gte", "value": start_date.isoformat()}
            )
        if end_date:
            filters.append(
                {"field": "targetDate", "op": "lte", "value": end_date.isoformat()}
            )

        milestones = self.query(filters=filters).items

        # Sort by target date
        milestones.sort(key=lambda x: x.get("targetDate", ""))

        # Group by month for timeline view
        timeline = {}
        for milestone in milestones:
            target_date_str = milestone.get("targetDate")
            if target_date_str:
                target_date = datetime.fromisoformat(
                    target_date_str.replace("Z", "+00:00")
                ).date()
                month_key = f"{target_date.year}-{target_date.month:02d}"

                if month_key not in timeline:
                    timeline[month_key] = []

                timeline[month_key].append(milestone)

        return {
            "contract_id": contract_id,
            "timeline_period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "total_milestones": len(milestones),
            "timeline": timeline,
        }
