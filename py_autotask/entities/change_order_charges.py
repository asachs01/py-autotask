"""
ChangeOrderCharges entity for Autotask API operations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ChangeOrderChargesEntity(BaseEntity):
    """
    Handles all ChangeOrderCharges-related operations for the Autotask API.

    ChangeOrderCharges represent financial charges associated with change orders
    in projects, tracking additional costs and billing modifications.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_change_order_charge(
        self,
        change_order_id: int,
        charge_type: int,
        amount: float,
        description: str,
        billing_date: Optional[date] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new change order charge.

        Args:
            change_order_id: ID of the change order
            charge_type: Type of charge (1=Labor, 2=Material, 3=Other, etc.)
            amount: Charge amount
            description: Charge description
            billing_date: Date when charge should be billed
            **kwargs: Additional charge properties

        Returns:
            Created change order charge data
        """
        charge_data = {
            "ChangeOrderID": change_order_id,
            "ChargeType": charge_type,
            "Amount": amount,
            "Description": description,
            **kwargs,
        }

        if billing_date:
            charge_data["BillingDate"] = billing_date.isoformat()

        return self.create(charge_data)

    def get_charges_by_change_order(
        self, change_order_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all charges for a specific change order.

        Args:
            change_order_id: ID of the change order
            limit: Maximum number of charges to return

        Returns:
            List of charges for the change order
        """
        filters = [QueryFilter(field="ChangeOrderID", op="eq", value=change_order_id)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_charges_by_type(
        self, charge_type: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get charges by charge type across all change orders.

        Args:
            charge_type: Type of charge to filter by
            limit: Maximum number of charges to return

        Returns:
            List of charges of the specified type
        """
        filters = [QueryFilter(field="ChargeType", op="eq", value=charge_type)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_charges_by_date_range(
        self,
        start_date: date,
        end_date: date,
        billing_date_field: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get charges within a specific date range.

        Args:
            start_date: Start date for range
            end_date: End date for range
            billing_date_field: Whether to use billing date (True) or creation date (False)
            limit: Maximum number of charges to return

        Returns:
            List of charges within the date range
        """
        field_name = "BillingDate" if billing_date_field else "CreateDateTime"

        filters = [
            QueryFilter(field=field_name, op="gte", value=start_date.isoformat()),
            QueryFilter(field=field_name, op="lte", value=end_date.isoformat()),
        ]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def calculate_change_order_total(self, change_order_id: int) -> Dict[str, Any]:
        """
        Calculate total charges for a change order by type.

        Args:
            change_order_id: ID of the change order

        Returns:
            Dictionary containing charge totals by type
        """
        charges = self.get_charges_by_change_order(change_order_id)

        totals = {
            "labor_total": 0.0,
            "material_total": 0.0,
            "other_total": 0.0,
            "grand_total": 0.0,
            "charge_count": len(charges),
        }

        for charge in charges:
            amount = float(charge.get("Amount", 0))
            charge_type = charge.get("ChargeType", 0)

            totals["grand_total"] += amount

            if charge_type == 1:  # Labor
                totals["labor_total"] += amount
            elif charge_type == 2:  # Material
                totals["material_total"] += amount
            else:  # Other
                totals["other_total"] += amount

        return totals

    def update_charge_amount(
        self, charge_id: int, new_amount: float, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Update the amount of a change order charge.

        Args:
            charge_id: ID of the charge to update
            new_amount: New charge amount
            reason: Optional reason for the change

        Returns:
            Updated charge data
        """
        update_data = {"Amount": new_amount}

        if reason:
            update_data["ModificationReason"] = reason

        return self.update_by_id(charge_id, update_data)

    def approve_change_order_charges(
        self, change_order_id: int, approver_resource_id: int
    ) -> List[EntityDict]:
        """
        Approve all charges for a change order.

        Args:
            change_order_id: ID of the change order
            approver_resource_id: ID of the approver resource

        Returns:
            List of updated charge data
        """
        charges = self.get_charges_by_change_order(change_order_id)

        approved_charges = []
        for charge in charges:
            if charge.get("id"):
                update_data = {
                    "Status": 2,  # Approved status
                    "ApproverResourceID": approver_resource_id,
                    "ApprovalDate": datetime.now().isoformat(),
                }
                updated = self.update_by_id(charge["id"], update_data)
                approved_charges.append(updated)

        return approved_charges

    def get_pending_approval_charges(
        self, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all charges pending approval.

        Args:
            limit: Maximum number of charges to return

        Returns:
            List of charges pending approval
        """
        filters = [QueryFilter(field="Status", op="eq", value=1)]  # Pending status
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def bulk_create_charges(
        self, change_order_charges: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple change order charges in batch.

        Args:
            change_order_charges: List of charge data dictionaries

        Returns:
            List of created charge responses
        """
        return self.batch_create(change_order_charges)

    def get_charges_summary_by_project(self, project_id: int) -> Dict[str, Any]:
        """
        Get change order charges summary for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary containing charges summary for the project
        """
        # This would typically require joining with change orders table
        # For now, we'll implement a basic version

        all_charges = []
        # We would need to get change orders for the project first
        # then get charges for each change order

        return {
            "project_id": project_id,
            "total_change_orders": 0,
            "total_charges": len(all_charges),
            "total_amount": sum(
                float(charge.get("Amount", 0)) for charge in all_charges
            ),
            "avg_charge_amount": 0.0,
            "charges_by_type": {},
        }

    def export_charges_for_billing(
        self, change_order_id: int, approved_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Export change order charges formatted for billing integration.

        Args:
            change_order_id: ID of the change order
            approved_only: Whether to include only approved charges

        Returns:
            List of charges formatted for billing export
        """
        charges = self.get_charges_by_change_order(change_order_id)

        if approved_only:
            charges = [c for c in charges if c.get("Status") == 2]

        billing_export = []
        for charge in charges:
            billing_item = {
                "change_order_id": change_order_id,
                "charge_id": charge.get("id"),
                "description": charge.get("Description"),
                "charge_type": charge.get("ChargeType"),
                "amount": float(charge.get("Amount", 0)),
                "billing_date": charge.get("BillingDate"),
                "approval_status": (
                    "Approved" if charge.get("Status") == 2 else "Pending"
                ),
            }
            billing_export.append(billing_item)

        return billing_export
