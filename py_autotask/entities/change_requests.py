"""
ChangeRequests Entity for py-autotask

This module provides the ChangeRequestsEntity class for managing change requests
in Autotask. Change requests handle modifications to systems, processes, or
configurations with proper approval workflows and impact assessment.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ChangeRequestsEntity(BaseEntity):
    """
    Manages Autotask ChangeRequests - change management and approval workflows.

    Change requests handle modifications to systems, processes, or configurations
    within Autotask. They support approval workflows, impact assessment,
    and change tracking throughout the lifecycle.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ChangeRequests"

    def create_change_request(
        self,
        title: str,
        description: str,
        change_type: str,
        priority: str,
        requested_by_resource_id: int,
        business_justification: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new change request.

        Args:
            title: Title of the change request
            description: Detailed description of the change
            change_type: Type of change (Emergency, Standard, Normal)
            priority: Priority level (Critical, High, Medium, Low)
            requested_by_resource_id: ID of the resource requesting the change
            business_justification: Business justification for the change
            **kwargs: Additional fields for the change request

        Returns:
            Create response with new change request ID
        """
        change_data = {
            "title": title,
            "description": description,
            "changeType": change_type,
            "priority": priority,
            "requestedByResourceID": requested_by_resource_id,
            "businessJustification": business_justification,
            "status": "Draft",
            **kwargs,
        }

        return self.create(change_data)

    def get_pending_change_requests(
        self, assigned_to_resource_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending change requests awaiting approval.

        Args:
            assigned_to_resource_id: Optional resource ID to filter by assignee

        Returns:
            List of pending change requests
        """
        filters = ["status eq 'Pending Approval'"]

        if assigned_to_resource_id:
            filters.append(f"assignedResourceID eq {assigned_to_resource_id}")

        return self.query(filter=" and ".join(filters))

    def get_change_requests_by_type(
        self, change_type: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get change requests by type.

        Args:
            change_type: Type of change request
            status: Optional status to filter by

        Returns:
            List of change requests of the specified type
        """
        filters = [f"changeType eq '{change_type}'"]

        if status:
            filters.append(f"status eq '{status}'")

        return self.query(filter=" and ".join(filters))

    def approve_change_request(
        self,
        change_request_id: int,
        approver_resource_id: int,
        approval_comments: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a change request.

        Args:
            change_request_id: ID of the change request
            approver_resource_id: ID of the approving resource
            approval_comments: Optional approval comments

        Returns:
            Update response
        """
        update_data = {
            "status": "Approved",
            "approvedByResourceID": approver_resource_id,
            "approvalDate": datetime.now().isoformat(),
        }

        if approval_comments:
            update_data["approvalComments"] = approval_comments

        return self.update(change_request_id, update_data)

    def reject_change_request(
        self, change_request_id: int, rejector_resource_id: int, rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject a change request.

        Args:
            change_request_id: ID of the change request
            rejector_resource_id: ID of the rejecting resource
            rejection_reason: Reason for rejection

        Returns:
            Update response
        """
        update_data = {
            "status": "Rejected",
            "rejectedByResourceID": rejector_resource_id,
            "rejectionDate": datetime.now().isoformat(),
            "rejectionReason": rejection_reason,
        }

        return self.update(change_request_id, update_data)

    def implement_change_request(
        self,
        change_request_id: int,
        implementer_resource_id: int,
        implementation_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark a change request as implemented.

        Args:
            change_request_id: ID of the change request
            implementer_resource_id: ID of the implementing resource
            implementation_notes: Optional implementation notes

        Returns:
            Update response
        """
        update_data = {
            "status": "Implemented",
            "implementedByResourceID": implementer_resource_id,
            "implementationDate": datetime.now().isoformat(),
        }

        if implementation_notes:
            update_data["implementationNotes"] = implementation_notes

        return self.update(change_request_id, update_data)

    def get_change_request_impact_assessment(
        self, change_request_id: int
    ) -> Dict[str, Any]:
        """
        Get impact assessment for a change request.

        Args:
            change_request_id: ID of the change request

        Returns:
            Impact assessment details
        """
        change_request = self.get(change_request_id)

        # This would typically analyze system impacts
        # For now, return impact assessment structure

        return {
            "change_request_id": change_request_id,
            "title": change_request.get("title"),
            "impact_assessment": {
                "risk_level": "Medium",  # Would calculate based on change
                "affected_systems": [],  # Would identify affected systems
                "affected_users": 0,  # Would estimate user impact
                "downtime_estimate": "0 hours",  # Would estimate downtime
                "rollback_plan": "",  # Would outline rollback procedures
                "testing_requirements": [],  # Would define testing needs
            },
        }

    def get_change_calendar(
        self, date_from: date, date_to: date, change_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get change calendar for a date range.

        Args:
            date_from: Start date for calendar
            date_to: End date for calendar
            change_type: Optional change type to filter by

        Returns:
            Change calendar with scheduled changes
        """
        filters = [
            f"scheduledDate ge {date_from.isoformat()}",
            f"scheduledDate le {date_to.isoformat()}",
        ]

        if change_type:
            filters.append(f"changeType eq '{change_type}'")

        changes = self.query(filter=" and ".join(filters))

        # Organize changes by date
        calendar = {}
        for change in changes:
            scheduled_date = change.get("scheduledDate", "")
            if scheduled_date:
                date_key = scheduled_date.split("T")[0]  # Extract date part
                if date_key not in calendar:
                    calendar[date_key] = []
                calendar[date_key].append(change)

        return {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "change_type_filter": change_type,
            "calendar": calendar,
            "total_changes": len(changes),
        }

    def get_change_metrics(self, date_from: date, date_to: date) -> Dict[str, Any]:
        """
        Get change management metrics for a period.

        Args:
            date_from: Start date for metrics
            date_to: End date for metrics

        Returns:
            Change management metrics
        """
        filters = [
            f"createDate ge {date_from.isoformat()}",
            f"createDate le {date_to.isoformat()}",
        ]

        changes = self.query(filter=" and ".join(filters))

        # Calculate metrics
        total_changes = len(changes)
        approved_changes = len([c for c in changes if c.get("status") == "Approved"])
        rejected_changes = len([c for c in changes if c.get("status") == "Rejected"])
        implemented_changes = len(
            [c for c in changes if c.get("status") == "Implemented"]
        )

        return {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "metrics": {
                "total_changes": total_changes,
                "approved_changes": approved_changes,
                "rejected_changes": rejected_changes,
                "implemented_changes": implemented_changes,
                "approval_rate": (
                    (approved_changes / total_changes * 100) if total_changes > 0 else 0
                ),
                "implementation_rate": (
                    (implemented_changes / approved_changes * 100)
                    if approved_changes > 0
                    else 0
                ),
            },
        }

    def bulk_approve_changes(
        self, change_approvals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Approve multiple change requests in bulk.

        Args:
            change_approvals: List of change approvals
                Each should contain: change_request_id, approver_resource_id, optional comments

        Returns:
            Summary of bulk approval operation
        """
        results = []

        for approval in change_approvals:
            change_request_id = approval["change_request_id"]
            approver_resource_id = approval["approver_resource_id"]
            approval_comments = approval.get("approval_comments")

            try:
                result = self.approve_change_request(
                    change_request_id, approver_resource_id, approval_comments
                )
                results.append(
                    {"id": change_request_id, "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"id": change_request_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_approvals": len(change_approvals),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }
