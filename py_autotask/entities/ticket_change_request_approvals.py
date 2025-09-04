"""
Ticket Change Request Approvals entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketChangeRequestApprovalsEntity(BaseEntity):
    """
    Handles Ticket Change Request Approvals operations for the Autotask API.

    Manages approval workflows for ticket change requests, including approval
    status tracking, approver assignments, and approval notifications.
    """

    def __init__(self, client, entity_name: str = "TicketChangeRequestApprovals"):
        super().__init__(client, entity_name)

    def create_approval_request(
        self,
        ticket_id: int,
        approver_resource_id: int,
        approval_level: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new approval request for a ticket change request.

        Args:
            ticket_id: ID of the ticket
            approver_resource_id: ID of the approver resource
            approval_level: Level of approval (1=Primary, 2=Secondary, etc.)
            **kwargs: Additional fields

        Returns:
            Created approval request data
        """
        approval_data = {
            "TicketID": ticket_id,
            "ApproverResourceID": approver_resource_id,
            "ApprovalLevel": approval_level,
            "ApprovalStatus": "Pending",  # Default status
            **kwargs,
        }

        return self.create(approval_data)

    def get_approvals_by_ticket(self, ticket_id: int) -> EntityList:
        """
        Get all approval requests for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by

        Returns:
            List of approval requests for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]
        return self.query_all(filters=filters)

    def get_pending_approvals_by_resource(self, resource_id: int) -> EntityList:
        """
        Get all pending approval requests assigned to a specific resource.

        Args:
            resource_id: Resource ID to filter by

        Returns:
            List of pending approval requests for the resource
        """
        filters = [
            {"field": "ApproverResourceID", "op": "eq", "value": str(resource_id)},
            {"field": "ApprovalStatus", "op": "eq", "value": "Pending"},
        ]
        return self.query_all(filters=filters)

    def approve_change_request(
        self,
        approval_id: int,
        approval_notes: Optional[str] = None,
        **kwargs,
    ) -> Optional[EntityDict]:
        """
        Approve a change request.

        Args:
            approval_id: Approval request ID
            approval_notes: Optional approval notes/comments
            **kwargs: Additional fields

        Returns:
            Updated approval record or None if failed
        """
        update_data = {
            "id": approval_id,
            "ApprovalStatus": "Approved",
            "ApprovalDateTime": datetime.now().isoformat(),
            **kwargs,
        }

        if approval_notes:
            update_data["ApprovalNotes"] = approval_notes

        return self.update(update_data)

    def reject_change_request(
        self,
        approval_id: int,
        rejection_reason: str,
        **kwargs,
    ) -> Optional[EntityDict]:
        """
        Reject a change request.

        Args:
            approval_id: Approval request ID
            rejection_reason: Reason for rejection
            **kwargs: Additional fields

        Returns:
            Updated approval record or None if failed
        """
        update_data = {
            "id": approval_id,
            "ApprovalStatus": "Rejected",
            "ApprovalDateTime": datetime.now().isoformat(),
            "ApprovalNotes": rejection_reason,
            **kwargs,
        }

        return self.update(update_data)

    def get_approval_status_summary(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get approval status summary for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with approval status summary
        """
        approvals = self.get_approvals_by_ticket(ticket_id)

        status_counts = {
            "Pending": 0,
            "Approved": 0,
            "Rejected": 0,
            "Cancelled": 0,
        }

        approval_levels = {}
        approvers = []

        for approval in approvals:
            status = approval.get("ApprovalStatus", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            level = approval.get("ApprovalLevel", 1)
            approval_levels[level] = approval_levels.get(level, [])
            approval_levels[level].append(approval)

            approvers.append(
                {
                    "resource_id": approval.get("ApproverResourceID"),
                    "status": status,
                    "level": level,
                    "approval_date": approval.get("ApprovalDateTime"),
                }
            )

        overall_status = "Pending"
        if status_counts["Rejected"] > 0:
            overall_status = "Rejected"
        elif status_counts["Pending"] == 0 and status_counts["Approved"] > 0:
            overall_status = "Fully Approved"
        elif status_counts["Approved"] > 0:
            overall_status = "Partially Approved"

        return {
            "ticket_id": ticket_id,
            "overall_status": overall_status,
            "status_counts": status_counts,
            "total_approvals": len(approvals),
            "approval_levels": approval_levels,
            "approvers": approvers,
        }

    def bulk_assign_approvers(
        self,
        ticket_id: int,
        approver_assignments: List[Dict[str, Any]],
    ) -> List[EntityDict]:
        """
        Assign multiple approvers to a ticket change request in bulk.

        Args:
            ticket_id: Ticket ID
            approver_assignments: List of approver assignment dictionaries
                Each dict should contain:
                - approver_resource_id: ID of approver
                - approval_level: Level of approval
                - other optional fields

        Returns:
            List of created approval request records
        """
        results = []

        for assignment in approver_assignments:
            try:
                approval = self.create_approval_request(
                    ticket_id=ticket_id,
                    approver_resource_id=assignment["approver_resource_id"],
                    approval_level=assignment.get("approval_level", 1),
                    **{
                        k: v
                        for k, v in assignment.items()
                        if k not in ["approver_resource_id", "approval_level"]
                    },
                )
                results.append(approval)
            except Exception as e:
                self.logger.error(
                    f"Failed to assign approver {assignment.get('approver_resource_id')} "
                    f"to ticket {ticket_id}: {e}"
                )

        return results

    def cancel_approval_request(
        self, approval_id: int, reason: str
    ) -> Optional[EntityDict]:
        """
        Cancel a pending approval request.

        Args:
            approval_id: Approval request ID
            reason: Reason for cancellation

        Returns:
            Updated approval record or None if failed
        """
        update_data = {
            "id": approval_id,
            "ApprovalStatus": "Cancelled",
            "ApprovalDateTime": datetime.now().isoformat(),
            "ApprovalNotes": f"Cancelled: {reason}",
        }

        return self.update(update_data)

    def get_overdue_approvals(
        self,
        days_overdue: int = 3,
        approver_resource_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get approval requests that are overdue.

        Args:
            days_overdue: Number of days past creation to consider overdue
            approver_resource_id: Optional filter by specific approver

        Returns:
            List of overdue approval requests
        """
        filters = [{"field": "ApprovalStatus", "op": "eq", "value": "Pending"}]

        if approver_resource_id:
            filters.append(
                {
                    "field": "ApproverResourceID",
                    "op": "eq",
                    "value": str(approver_resource_id),
                }
            )

        approvals = self.query_all(filters=filters)
        cutoff_date = datetime.now() - timedelta(days=days_overdue)

        overdue_approvals = []
        for approval in approvals:
            if "CreateDateTime" in approval:
                try:
                    create_date = datetime.fromisoformat(
                        approval["CreateDateTime"].replace("Z", "+00:00")
                    )
                    if create_date <= cutoff_date:
                        overdue_approvals.append(approval)
                except ValueError:
                    # Skip if date parsing fails
                    continue

        return overdue_approvals

    def get_approval_history_by_resource(
        self,
        resource_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get approval history for a specific resource.

        Args:
            resource_id: Resource ID
            days: Number of days to look back

        Returns:
            Dictionary with approval history summary
        """
        filters = [
            {"field": "ApproverResourceID", "op": "eq", "value": str(resource_id)}
        ]
        approvals = self.query_all(filters=filters)

        cutoff_date = datetime.now() - timedelta(days=days)

        stats = {
            "resource_id": resource_id,
            "period_days": days,
            "total_approvals": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "pending_count": 0,
            "response_times": [],
            "recent_approvals": [],
        }

        for approval in approvals:
            # Check if within time period
            if "CreateDateTime" in approval:
                try:
                    create_date = datetime.fromisoformat(
                        approval["CreateDateTime"].replace("Z", "+00:00")
                    )
                    if create_date >= cutoff_date:
                        stats["recent_approvals"].append(approval)
                        stats["total_approvals"] += 1

                        status = approval.get("ApprovalStatus")
                        if status == "Approved":
                            stats["approved_count"] += 1
                        elif status == "Rejected":
                            stats["rejected_count"] += 1
                        elif status == "Pending":
                            stats["pending_count"] += 1

                        # Calculate response time if approved/rejected
                        if (
                            status in ["Approved", "Rejected"]
                            and "ApprovalDateTime" in approval
                        ):
                            try:
                                approval_date = datetime.fromisoformat(
                                    approval["ApprovalDateTime"].replace("Z", "+00:00")
                                )
                                response_time = (
                                    approval_date - create_date
                                ).total_seconds() / 3600
                                stats["response_times"].append(response_time)
                            except ValueError:
                                continue
                except ValueError:
                    continue

        # Calculate average response time
        if stats["response_times"]:
            stats["avg_response_time_hours"] = sum(stats["response_times"]) / len(
                stats["response_times"]
            )
        else:
            stats["avg_response_time_hours"] = None

        return stats

    def reassign_approval(
        self,
        approval_id: int,
        new_approver_resource_id: int,
        reason: str,
    ) -> Optional[EntityDict]:
        """
        Reassign an approval request to a different approver.

        Args:
            approval_id: Current approval request ID
            new_approver_resource_id: ID of new approver
            reason: Reason for reassignment

        Returns:
            Updated approval record or None if failed
        """
        update_data = {
            "id": approval_id,
            "ApproverResourceID": new_approver_resource_id,
            "ApprovalNotes": f"Reassigned: {reason}",
        }

        return self.update(update_data)

    def get_approval_workflow_status(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get complete workflow status for multi-level approvals.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with workflow status information
        """
        approvals = self.get_approvals_by_ticket(ticket_id)

        # Group by approval level
        levels = {}
        for approval in approvals:
            level = approval.get("ApprovalLevel", 1)
            if level not in levels:
                levels[level] = []
            levels[level].append(approval)

        workflow_status = {
            "ticket_id": ticket_id,
            "current_level": 1,
            "total_levels": len(levels) if levels else 0,
            "completed_levels": 0,
            "workflow_complete": False,
            "workflow_blocked": False,
            "levels": {},
        }

        for level in sorted(levels.keys()):
            level_approvals = levels[level]
            level_status = {
                "level": level,
                "approvals": level_approvals,
                "approved_count": len(
                    [
                        a
                        for a in level_approvals
                        if a.get("ApprovalStatus") == "Approved"
                    ]
                ),
                "rejected_count": len(
                    [
                        a
                        for a in level_approvals
                        if a.get("ApprovalStatus") == "Rejected"
                    ]
                ),
                "pending_count": len(
                    [a for a in level_approvals if a.get("ApprovalStatus") == "Pending"]
                ),
                "level_complete": False,
                "level_rejected": False,
            }

            # Check if level is complete or rejected
            if level_status["rejected_count"] > 0:
                level_status["level_rejected"] = True
                workflow_status["workflow_blocked"] = True
            elif (
                level_status["pending_count"] == 0
                and level_status["approved_count"] > 0
            ):
                level_status["level_complete"] = True
                workflow_status["completed_levels"] += 1

            workflow_status["levels"][level] = level_status

        # Determine current level and overall status
        if workflow_status["completed_levels"] == workflow_status["total_levels"]:
            workflow_status["workflow_complete"] = True
        else:
            workflow_status["current_level"] = workflow_status["completed_levels"] + 1

        return workflow_status
