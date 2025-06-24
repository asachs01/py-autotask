"""
ProjectCharges Entity for py-autotask

This module provides the ProjectChargesEntity class for managing project charges
in Autotask. Project charges represent charges that are applied to projects for
billing and cost tracking purposes.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ProjectChargesEntity(BaseEntity):
    """
    Manages Autotask ProjectCharges - charges applied to projects.

    Project charges represent billing and cost items associated with specific
    projects, including time charges, material costs, expenses, and other
    project-related costs.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ProjectCharges"

    def create_project_charge(
        self,
        project_id: int,
        billing_code_id: int,
        description: str,
        unit_quantity: Union[float, Decimal],
        unit_price: Union[float, Decimal],
        charge_date: Optional[date] = None,
        task_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new project charge.

        Args:
            project_id: ID of the project
            billing_code_id: ID of the billing code
            description: Description of the charge
            unit_quantity: Quantity of units
            unit_price: Price per unit
            charge_date: Date of the charge (defaults to today)
            task_id: Optional associated task ID
            **kwargs: Additional fields for the project charge

        Returns:
            Create response with new project charge ID
        """
        if charge_date is None:
            charge_date = date.today()

        charge_data = {
            "projectID": project_id,
            "billingCodeID": billing_code_id,
            "description": description,
            "unitQuantity": float(unit_quantity),
            "unitPrice": float(unit_price),
            "chargeDate": charge_date.isoformat(),
            **kwargs,
        }

        if task_id:
            charge_data["taskID"] = task_id

        return self.create(charge_data)

    def get_project_charges_by_project(
        self,
        project_id: int,
        include_billed: bool = True,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get project charges for a specific project.

        Args:
            project_id: ID of the project
            include_billed: Whether to include already billed charges
            date_from: Start date for filtering
            date_to: End date for filtering

        Returns:
            List of project charges
        """
        filters = [f"projectID eq {project_id}"]

        if not include_billed:
            filters.append("billedDate eq null")

        if date_from:
            filters.append(f"chargeDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"chargeDate le {date_to.isoformat()}")

        return self.query(filter=" and ".join(filters))

    def get_project_budget_analysis(
        self, project_id: int, include_pending: bool = True
    ) -> Dict[str, Any]:
        """
        Get budget analysis for a project including charges.

        Args:
            project_id: ID of the project
            include_pending: Whether to include pending/unbilled charges

        Returns:
            Project budget analysis with charges
        """
        filters = [f"projectID eq {project_id}"]

        if not include_pending:
            filters.append("billedDate ne null")

        charges = self.query(filter=" and ".join(filters))

        total_charges = len(charges)
        total_amount = Decimal("0")
        total_cost = Decimal("0")
        billed_amount = Decimal("0")
        pending_amount = Decimal("0")

        charges_by_billing_code = {}

        for charge in charges:
            quantity = Decimal(str(charge.get("unitQuantity", 0)))
            price = Decimal(str(charge.get("unitPrice", 0)))
            cost = Decimal(str(charge.get("unitCost", 0)))
            billing_code_id = charge.get("billingCodeID")

            charge_amount = quantity * price
            charge_cost = quantity * cost

            total_amount += charge_amount
            total_cost += charge_cost

            if charge.get("billedDate"):
                billed_amount += charge_amount
            else:
                pending_amount += charge_amount

            # Group by billing code
            if billing_code_id:
                if billing_code_id not in charges_by_billing_code:
                    charges_by_billing_code[billing_code_id] = {
                        "billing_code_id": billing_code_id,
                        "charge_count": 0,
                        "total_amount": Decimal("0"),
                        "total_cost": Decimal("0"),
                    }

                code_data = charges_by_billing_code[billing_code_id]
                code_data["charge_count"] += 1
                code_data["total_amount"] += charge_amount
                code_data["total_cost"] += charge_cost

        return {
            "project_id": project_id,
            "summary": {
                "total_charges": total_charges,
                "total_amount": total_amount,
                "total_cost": total_cost,
                "profit_margin": total_amount - total_cost,
                "billed_amount": billed_amount,
                "pending_amount": pending_amount,
                "profit_percentage": (
                    float((total_amount - total_cost) / total_amount * 100)
                    if total_amount > 0
                    else 0
                ),
            },
            "by_billing_code": list(charges_by_billing_code.values()),
        }

    def approve_project_charges(
        self,
        charge_ids: List[int],
        approver_resource_id: int,
        approval_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve project charges for billing.

        Args:
            charge_ids: List of project charge IDs to approve
            approver_resource_id: ID of the approving resource
            approval_notes: Optional approval notes

        Returns:
            Summary of approval operation
        """
        approval_date = datetime.now().isoformat()

        update_data = {
            "approvedByResourceID": approver_resource_id,
            "approvalDate": approval_date,
        }

        if approval_notes:
            update_data["approvalNotes"] = approval_notes

        results = []
        for charge_id in charge_ids:
            try:
                result = self.update(charge_id, update_data)
                results.append({"id": charge_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": charge_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_charges": len(charge_ids),
            "successful": len(successful),
            "failed": len(failed),
            "approver_resource_id": approver_resource_id,
            "approval_date": approval_date,
            "results": results,
        }

    def get_charges_by_task(
        self, task_id: int, include_billed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get project charges associated with a specific task.

        Args:
            task_id: ID of the task
            include_billed: Whether to include already billed charges

        Returns:
            List of project charges for the task
        """
        filters = [f"taskID eq {task_id}"]

        if not include_billed:
            filters.append("billedDate eq null")

        return self.query(filter=" and ".join(filters))

    def bulk_create_project_charges(
        self, charges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple project charges in batch.

        Args:
            charges: List of charge data dictionaries

        Returns:
            Summary of batch creation operation
        """
        results = []

        for charge_data in charges:
            try:
                result = self.create(charge_data)
                results.append({"success": True, "result": result, "data": charge_data})
            except Exception as e:
                results.append({"success": False, "error": str(e), "data": charge_data})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_charges": len(charges),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_project_revenue_summary(
        self,
        project_ids: List[int],
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get revenue summary for multiple projects.

        Args:
            project_ids: List of project IDs
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Revenue summary by project
        """
        if not project_ids:
            return {"projects": [], "summary": {}}

        project_filter = " or ".join([f"projectID eq {pid}" for pid in project_ids])
        filters = [f"({project_filter})"]

        if date_from:
            filters.append(f"chargeDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"chargeDate le {date_to.isoformat()}")

        charges = self.query(filter=" and ".join(filters))

        # Group by project
        projects_data = {}
        for project_id in project_ids:
            projects_data[project_id] = {
                "project_id": project_id,
                "charge_count": 0,
                "total_revenue": Decimal("0"),
                "total_cost": Decimal("0"),
                "billed_revenue": Decimal("0"),
                "pending_revenue": Decimal("0"),
            }

        for charge in charges:
            project_id = charge.get("projectID")
            if project_id in projects_data:
                quantity = Decimal(str(charge.get("unitQuantity", 0)))
                price = Decimal(str(charge.get("unitPrice", 0)))
                cost = Decimal(str(charge.get("unitCost", 0)))

                revenue = quantity * price
                charge_cost = quantity * cost

                project_data = projects_data[project_id]
                project_data["charge_count"] += 1
                project_data["total_revenue"] += revenue
                project_data["total_cost"] += charge_cost

                if charge.get("billedDate"):
                    project_data["billed_revenue"] += revenue
                else:
                    project_data["pending_revenue"] += revenue

        # Calculate totals and margins
        total_revenue = Decimal("0")
        total_cost = Decimal("0")

        for project_data in projects_data.values():
            profit = project_data["total_revenue"] - project_data["total_cost"]
            project_data["profit_margin"] = profit
            project_data["profit_percentage"] = (
                float(profit / project_data["total_revenue"] * 100)
                if project_data["total_revenue"] > 0
                else 0
            )

            total_revenue += project_data["total_revenue"]
            total_cost += project_data["total_cost"]

        return {
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "summary": {
                "total_projects": len(project_ids),
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "total_profit": total_revenue - total_cost,
                "overall_margin_percentage": (
                    float((total_revenue - total_cost) / total_revenue * 100)
                    if total_revenue > 0
                    else 0
                ),
            },
            "projects": list(projects_data.values()),
        }
