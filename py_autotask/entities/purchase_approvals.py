"""
Purchase Approvals entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class PurchaseApprovalsEntity(BaseEntity):
    """
    Handles all Purchase Approval-related operations for the Autotask API.

    Purchase approvals manage the approval workflow for purchase orders,
    tracking approval status, approver assignments, and approval history.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_purchase_approval(
        self,
        purchase_order_id: int,
        approver_resource_id: int,
        approval_level: int = 1,
        required_approval: bool = True,
        approval_status: str = "pending",
        **kwargs,
    ) -> EntityDict:
        """Create a new purchase approval entry."""
        approval_data = {
            "PurchaseOrderID": purchase_order_id,
            "ApproverResourceID": approver_resource_id,
            "ApprovalLevel": approval_level,
            "RequiredApproval": required_approval,
            "ApprovalStatus": approval_status,
            **kwargs,
        }

        return self.create(approval_data)

    def get_approvals_for_purchase_order(
        self, purchase_order_id: int, status_filter: Optional[str] = None
    ) -> List[EntityDict]:
        """Get all approvals for a specific purchase order."""
        filters = [{"field": "PurchaseOrderID", "op": "eq", "value": purchase_order_id}]

        if status_filter:
            filters.append(
                {"field": "ApprovalStatus", "op": "eq", "value": status_filter}
            )

        return self.query_all(filters=filters)

    def get_pending_approvals_for_user(self, resource_id: int) -> List[EntityDict]:
        """Get pending approvals for a specific user."""
        return self.query_all(
            filters=[
                {"field": "ApproverResourceID", "op": "eq", "value": resource_id},
                {"field": "ApprovalStatus", "op": "eq", "value": "pending"},
            ]
        )

    def approve_purchase_order(
        self,
        approval_id: int,
        approver_resource_id: int,
        approval_comments: Optional[str] = None,
    ) -> EntityDict:
        """Approve a purchase order."""
        from datetime import datetime

        update_data = {
            "ApprovalStatus": "approved",
            "ApprovalDate": datetime.now().isoformat(),
            "ApproverResourceID": approver_resource_id,
        }

        if approval_comments:
            update_data["ApprovalComments"] = approval_comments

        return self.update_by_id(approval_id, update_data)

    def reject_purchase_order(
        self,
        approval_id: int,
        approver_resource_id: int,
        rejection_reason: str,
    ) -> EntityDict:
        """Reject a purchase order."""
        from datetime import datetime

        update_data = {
            "ApprovalStatus": "rejected",
            "ApprovalDate": datetime.now().isoformat(),
            "ApproverResourceID": approver_resource_id,
            "ApprovalComments": rejection_reason,
        }

        return self.update_by_id(approval_id, update_data)

    def get_approval_status_summary(self, purchase_order_id: int) -> Dict[str, Any]:
        """Get approval status summary for a purchase order."""
        approvals = self.get_approvals_for_purchase_order(purchase_order_id)

        status_counts = {}
        for approval in approvals:
            status = approval.get("ApprovalStatus", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        required_approvals = [a for a in approvals if a.get("RequiredApproval")]
        approved_required = [
            a for a in required_approvals if a.get("ApprovalStatus") == "approved"
        ]
        rejected_any = any(
            a.get("ApprovalStatus") == "rejected" for a in required_approvals
        )

        overall_status = "pending"
        if rejected_any:
            overall_status = "rejected"
        elif len(approved_required) == len(required_approvals) and required_approvals:
            overall_status = "approved"

        return {
            "purchase_order_id": purchase_order_id,
            "total_approvals": len(approvals),
            "required_approvals": len(required_approvals),
            "status_breakdown": status_counts,
            "overall_status": overall_status,
            "approval_progress": (
                f"{len(approved_required)}/{len(required_approvals)}"
                if required_approvals
                else "0/0"
            ),
        }

    def bulk_approve_orders(
        self,
        approval_ids: List[int],
        approver_resource_id: int,
        approval_comments: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Approve multiple purchase orders in bulk."""
        results = []

        for approval_id in approval_ids:
            try:
                approved = self.approve_purchase_order(
                    approval_id, approver_resource_id, approval_comments
                )
                results.append(
                    {
                        "approval_id": approval_id,
                        "status": "success",
                        "approval_data": approved,
                    }
                )
            except Exception as e:
                results.append(
                    {"approval_id": approval_id, "status": "failed", "error": str(e)}
                )

        return results

    def reassign_approval(
        self,
        approval_id: int,
        new_approver_resource_id: int,
        reassignment_reason: Optional[str] = None,
    ) -> EntityDict:
        """Reassign an approval to a different approver."""
        update_data = {
            "ApproverResourceID": new_approver_resource_id,
            "ApprovalStatus": "pending",  # Reset to pending for new approver
        }

        if reassignment_reason:
            update_data["ReassignmentReason"] = reassignment_reason

        return self.update_by_id(approval_id, update_data)

    def get_approval_workload(self, resource_id: int) -> Dict[str, Any]:
        """Get approval workload summary for a resource."""
        all_approvals = self.query_all(
            filters={"field": "ApproverResourceID", "op": "eq", "value": resource_id}
        )

        pending_approvals = [
            a for a in all_approvals if a.get("ApprovalStatus") == "pending"
        ]

        # Group by approval level
        by_level = {}
        for approval in pending_approvals:
            level = approval.get("ApprovalLevel", 1)
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(approval)

        return {
            "resource_id": resource_id,
            "total_approvals": len(all_approvals),
            "pending_approvals": len(pending_approvals),
            "completed_approvals": len(all_approvals) - len(pending_approvals),
            "pending_by_level": {
                level: len(approvals) for level, approvals in by_level.items()
            },
            "completion_rate": (
                (len(all_approvals) - len(pending_approvals)) / len(all_approvals) * 100
                if all_approvals
                else 0
            ),
        }

    def get_approval_history(self, purchase_order_id: int) -> List[Dict[str, Any]]:
        """Get approval history for a purchase order."""
        approvals = self.get_approvals_for_purchase_order(purchase_order_id)

        history = []
        for approval in approvals:
            history_entry = {
                "approval_id": approval["id"],
                "approver_resource_id": approval.get("ApproverResourceID"),
                "approval_level": approval.get("ApprovalLevel"),
                "approval_status": approval.get("ApprovalStatus"),
                "approval_date": approval.get("ApprovalDate"),
                "approval_comments": approval.get("ApprovalComments"),
                "required_approval": approval.get("RequiredApproval", False),
            }
            history.append(history_entry)

        # Sort by approval level and date
        history.sort(key=lambda x: (x["approval_level"], x["approval_date"] or ""))

        return history
