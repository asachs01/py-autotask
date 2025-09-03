"""
ProjectCosts Entity for py-autotask

This module provides the ProjectCostsEntity class for managing project cost
tracking and expense management in Autotask. Project Costs handle budgeting,
expense tracking, and financial analysis for project profitability.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ProjectCostsEntity(BaseEntity):
    """
    Manages Autotask ProjectCosts - project expense and cost tracking.

    Project Costs handle expense tracking, budget management, and cost analysis
    for projects. They support detailed cost categorization, budget vs. actual
    analysis, profitability calculations, and financial reporting for projects.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ProjectCosts"

    def create_project_cost(
        self,
        project_id: int,
        cost_type: str,
        cost_amount: float,
        cost_date: date,
        cost_category: Optional[str] = None,
        description: Optional[str] = None,
        is_billable: bool = True,
        vendor_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new project cost entry.

        Args:
            project_id: ID of the project
            cost_type: Type of cost (labor, material, expense, etc.)
            cost_amount: Amount of the cost
            cost_date: Date when the cost was incurred
            cost_category: Optional cost category
            description: Optional description of the cost
            is_billable: Whether the cost is billable to client
            vendor_id: Optional vendor ID for the cost
            **kwargs: Additional fields for the project cost

        Returns:
            Create response with new project cost ID
        """
        cost_data = {
            "projectID": project_id,
            "costType": cost_type,
            "costAmount": cost_amount,
            "costDate": cost_date.isoformat(),
            "isBillable": is_billable,
            "createDate": datetime.now().isoformat(),
            **kwargs,
        }

        if cost_category:
            cost_data["costCategory"] = cost_category
        if description:
            cost_data["description"] = description
        if vendor_id:
            cost_data["vendorID"] = vendor_id

        return self.create(cost_data)

    def get_project_costs(
        self,
        project_id: int,
        cost_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        billable_only: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get costs for a specific project.

        Args:
            project_id: ID of the project
            cost_type: Optional cost type filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            billable_only: Optional filter for billable costs only

        Returns:
            List of costs for the project
        """
        filters = [{"field": "projectID", "op": "eq", "value": str(project_id)}]

        if cost_type:
            filters.append({"field": "costType", "op": "eq", "value": cost_type})
        if date_from:
            filters.append(
                {"field": "costDate", "op": "gte", "value": date_from.isoformat()}
            )
        if date_to:
            filters.append(
                {"field": "costDate", "op": "lte", "value": date_to.isoformat()}
            )
        if billable_only is not None:
            filters.append(
                {
                    "field": "isBillable",
                    "op": "eq",
                    "value": "true" if billable_only else "false",
                }
            )

        return self.query(filters=filters).items

    def calculate_project_cost_summary(
        self,
        project_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive cost summary for a project.

        Args:
            project_id: ID of the project
            date_from: Optional start date for analysis
            date_to: Optional end date for analysis

        Returns:
            Project cost summary and analysis
        """
        project_costs = self.get_project_costs(
            project_id, date_from=date_from, date_to=date_to
        )

        # Initialize summary data
        total_costs = 0.0
        billable_costs = 0.0
        non_billable_costs = 0.0
        cost_by_type = {}
        cost_by_category = {}
        cost_timeline = {}

        for cost in project_costs:
            cost_amount = float(cost["costAmount"])
            cost_type = cost.get("costType", "unknown")
            cost_category = cost.get("costCategory", "uncategorized")
            cost_date = cost.get("costDate", "")
            is_billable = cost.get("isBillable", False)

            # Total costs
            total_costs += cost_amount

            # Billable vs non-billable
            if is_billable:
                billable_costs += cost_amount
            else:
                non_billable_costs += cost_amount

            # By type
            if cost_type not in cost_by_type:
                cost_by_type[cost_type] = {
                    "total": 0.0,
                    "count": 0,
                    "billable": 0.0,
                    "non_billable": 0.0,
                }
            cost_by_type[cost_type]["total"] += cost_amount
            cost_by_type[cost_type]["count"] += 1
            if is_billable:
                cost_by_type[cost_type]["billable"] += cost_amount
            else:
                cost_by_type[cost_type]["non_billable"] += cost_amount

            # By category
            if cost_category not in cost_by_category:
                cost_by_category[cost_category] = {"total": 0.0, "count": 0}
            cost_by_category[cost_category]["total"] += cost_amount
            cost_by_category[cost_category]["count"] += 1

            # Timeline (by month)
            if cost_date:
                month_key = cost_date[:7]  # YYYY-MM
                if month_key not in cost_timeline:
                    cost_timeline[month_key] = 0.0
                cost_timeline[month_key] += cost_amount

        return {
            "project_id": project_id,
            "analysis_period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "cost_summary": {
                "total_costs": round(total_costs, 2),
                "billable_costs": round(billable_costs, 2),
                "non_billable_costs": round(non_billable_costs, 2),
                "billable_percentage": (
                    round((billable_costs / total_costs * 100), 1)
                    if total_costs > 0
                    else 0.0
                ),
                "total_cost_entries": len(project_costs),
            },
            "cost_by_type": {
                cost_type: {
                    "total": round(data["total"], 2),
                    "count": data["count"],
                    "billable": round(data["billable"], 2),
                    "non_billable": round(data["non_billable"], 2),
                    "percentage": (
                        round((data["total"] / total_costs * 100), 1)
                        if total_costs > 0
                        else 0.0
                    ),
                }
                for cost_type, data in cost_by_type.items()
            },
            "cost_by_category": {
                category: {
                    "total": round(data["total"], 2),
                    "count": data["count"],
                    "percentage": (
                        round((data["total"] / total_costs * 100), 1)
                        if total_costs > 0
                        else 0.0
                    ),
                }
                for category, data in cost_by_category.items()
            },
            "cost_timeline": {
                month: round(amount, 2)
                for month, amount in sorted(cost_timeline.items())
            },
        }

    def compare_budget_vs_actual(
        self, project_id: int, project_budget: float
    ) -> Dict[str, Any]:
        """
        Compare actual project costs against budget.

        Args:
            project_id: ID of the project
            project_budget: Total project budget

        Returns:
            Budget vs actual analysis
        """
        cost_summary = self.calculate_project_cost_summary(project_id)
        actual_costs = cost_summary["cost_summary"]["total_costs"]

        budget_variance = actual_costs - project_budget
        budget_variance_percentage = (
            (budget_variance / project_budget * 100) if project_budget > 0 else 0.0
        )

        # Determine budget status
        if budget_variance <= 0:
            budget_status = "under_budget"
        elif budget_variance_percentage <= 10:
            budget_status = "on_budget"
        elif budget_variance_percentage <= 25:
            budget_status = "over_budget"
        else:
            budget_status = "significantly_over_budget"

        return {
            "project_id": project_id,
            "budget_analysis": {
                "project_budget": project_budget,
                "actual_costs": actual_costs,
                "remaining_budget": project_budget - actual_costs,
                "budget_variance": round(budget_variance, 2),
                "budget_variance_percentage": round(budget_variance_percentage, 1),
                "budget_status": budget_status,
                "budget_utilization_percentage": (
                    round((actual_costs / project_budget * 100), 1)
                    if project_budget > 0
                    else 0.0
                ),
            },
            "cost_breakdown": cost_summary["cost_by_type"],
            "analysis_date": datetime.now().isoformat(),
        }

    def track_cost_trends(
        self, project_id: int, months_back: int = 12
    ) -> Dict[str, Any]:
        """
        Track cost trends for a project over time.

        Args:
            project_id: ID of the project
            months_back: Number of months to analyze

        Returns:
            Cost trend analysis
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        project_costs = self.get_project_costs(
            project_id, date_from=start_date, date_to=end_date
        )

        # Group costs by month
        monthly_costs = {}
        monthly_billable = {}
        for cost in project_costs:
            cost_date = cost.get("costDate", "")
            if cost_date:
                month_key = cost_date[:7]  # YYYY-MM
                cost_amount = float(cost["costAmount"])

                if month_key not in monthly_costs:
                    monthly_costs[month_key] = 0.0
                    monthly_billable[month_key] = 0.0

                monthly_costs[month_key] += cost_amount
                if cost.get("isBillable"):
                    monthly_billable[month_key] += cost_amount

        # Calculate trend direction
        months = sorted(monthly_costs.keys())
        if len(months) >= 2:
            recent_months = months[-3:]  # Last 3 months
            earlier_months = months[:-3] if len(months) > 3 else months[:-1]

            recent_avg = sum(monthly_costs[month] for month in recent_months) / len(
                recent_months
            )
            earlier_avg = (
                sum(monthly_costs[month] for month in earlier_months)
                / len(earlier_months)
                if earlier_months
                else 0
            )

            trend_direction = (
                "increasing"
                if recent_avg > earlier_avg * 1.1
                else "decreasing" if recent_avg < earlier_avg * 0.9 else "stable"
            )
        else:
            trend_direction = "insufficient_data"

        return {
            "project_id": project_id,
            "trend_analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months_analyzed": months_back,
            },
            "monthly_costs": {
                month: round(cost, 2) for month, cost in monthly_costs.items()
            },
            "monthly_billable_costs": {
                month: round(cost, 2) for month, cost in monthly_billable.items()
            },
            "trend_summary": {
                "trend_direction": trend_direction,
                "total_months_with_costs": len(months),
                "highest_cost_month": (
                    max(monthly_costs.items(), key=lambda x: x[1])
                    if monthly_costs
                    else None
                ),
                "lowest_cost_month": (
                    min(monthly_costs.items(), key=lambda x: x[1])
                    if monthly_costs
                    else None
                ),
                "average_monthly_cost": (
                    round(sum(monthly_costs.values()) / len(monthly_costs), 2)
                    if monthly_costs
                    else 0.0
                ),
            },
        }

    def bulk_import_project_costs(
        self, project_id: int, cost_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Import multiple project costs in bulk.

        Args:
            project_id: ID of the project
            cost_entries: List of cost entry data
                Each should contain: cost_type, cost_amount, cost_date, description

        Returns:
            Summary of bulk import operation
        """
        results = []

        for cost_entry in cost_entries:
            try:
                entry_data = {"project_id": project_id, **cost_entry}

                # Convert string dates to date objects if needed
                if isinstance(entry_data.get("cost_date"), str):
                    entry_data["cost_date"] = datetime.fromisoformat(
                        entry_data["cost_date"]
                    ).date()

                create_result = self.create_project_cost(**entry_data)

                results.append(
                    {
                        "description": cost_entry.get("description", ""),
                        "cost_amount": cost_entry["cost_amount"],
                        "cost_type": cost_entry["cost_type"],
                        "success": True,
                        "cost_id": create_result["item_id"],
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "description": cost_entry.get("description", ""),
                        "cost_amount": cost_entry.get("cost_amount", 0),
                        "cost_type": cost_entry.get("cost_type", "unknown"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        total_amount_imported = sum(float(r["cost_amount"]) for r in successful)

        return {
            "project_id": project_id,
            "import_summary": {
                "total_entries": len(cost_entries),
                "successful_imports": len(successful),
                "failed_imports": len(failed),
                "total_amount_imported": round(total_amount_imported, 2),
            },
            "import_date": datetime.now().isoformat(),
            "results": results,
        }

    def calculate_project_profitability(
        self, project_id: int, project_revenue: float
    ) -> Dict[str, Any]:
        """
        Calculate project profitability based on costs and revenue.

        Args:
            project_id: ID of the project
            project_revenue: Total project revenue

        Returns:
            Profitability analysis
        """
        cost_summary = self.calculate_project_cost_summary(project_id)
        total_costs = cost_summary["cost_summary"]["total_costs"]

        gross_profit = project_revenue - total_costs
        gross_margin = (
            (gross_profit / project_revenue * 100) if project_revenue > 0 else 0.0
        )

        # Profitability assessment
        if gross_margin >= 30:
            profitability_rating = "excellent"
        elif gross_margin >= 15:
            profitability_rating = "good"
        elif gross_margin >= 5:
            profitability_rating = "acceptable"
        elif gross_margin >= 0:
            profitability_rating = "marginal"
        else:
            profitability_rating = "unprofitable"

        return {
            "project_id": project_id,
            "profitability_analysis": {
                "project_revenue": project_revenue,
                "total_costs": total_costs,
                "gross_profit": round(gross_profit, 2),
                "gross_margin_percentage": round(gross_margin, 1),
                "profitability_rating": profitability_rating,
                "roi_percentage": (
                    round((gross_profit / total_costs * 100), 1)
                    if total_costs > 0
                    else 0.0
                ),
            },
            "cost_breakdown": {
                "billable_costs": cost_summary["cost_summary"]["billable_costs"],
                "non_billable_costs": cost_summary["cost_summary"][
                    "non_billable_costs"
                ],
                "cost_recovery_rate": (
                    round(
                        (
                            cost_summary["cost_summary"]["billable_costs"]
                            / total_costs
                            * 100
                        ),
                        1,
                    )
                    if total_costs > 0
                    else 0.0
                ),
            },
            "analysis_date": datetime.now().isoformat(),
        }

    def approve_project_cost(
        self, cost_id: int, approved_by: int, approval_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a project cost entry.

        Args:
            cost_id: ID of the cost entry
            approved_by: ID of the approving resource
            approval_notes: Optional approval notes

        Returns:
            Updated cost entry data
        """
        update_data = {
            "id": cost_id,
            "isApproved": True,
            "approvedBy": approved_by,
            "approvalDate": datetime.now().isoformat(),
        }

        if approval_notes:
            update_data["approvalNotes"] = approval_notes

        return self.update(update_data)

    def reject_project_cost(
        self, cost_id: int, rejected_by: int, rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject a project cost entry.

        Args:
            cost_id: ID of the cost entry
            rejected_by: ID of the rejecting resource
            rejection_reason: Reason for rejection

        Returns:
            Updated cost entry data
        """
        return self.update(
            {
                "id": cost_id,
                "isRejected": True,
                "rejectedBy": rejected_by,
                "rejectionDate": datetime.now().isoformat(),
                "rejectionReason": rejection_reason,
            }
        )

    def get_pending_cost_approvals(
        self,
        project_ids: Optional[List[int]] = None,
        amount_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get project costs pending approval.

        Args:
            project_ids: Optional list of project IDs to filter by
            amount_threshold: Optional minimum amount threshold

        Returns:
            List of costs pending approval
        """
        filters = [
            {"field": "isApproved", "op": "eq", "value": "false"},
            {"field": "isRejected", "op": "eq", "value": "false"},
        ]

        if project_ids:
            project_filter = {
                "field": "projectID",
                "op": "in",
                "value": [str(pid) for pid in project_ids],
            }
            filters.append(project_filter)

        if amount_threshold is not None:
            filters.append(
                {"field": "costAmount", "op": "gte", "value": str(amount_threshold)}
            )

        return self.query(filters=filters).items

    def generate_cost_variance_report(
        self, project_id: int, budget_breakdown: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate cost variance report comparing actual costs to budget by category.

        Args:
            project_id: ID of the project
            budget_breakdown: Budget amounts by cost type/category

        Returns:
            Cost variance report
        """
        cost_summary = self.calculate_project_cost_summary(project_id)
        actual_by_type = cost_summary["cost_by_type"]

        variance_analysis = {}
        total_budget = sum(budget_breakdown.values())
        total_actual = cost_summary["cost_summary"]["total_costs"]

        for cost_type, budgeted_amount in budget_breakdown.items():
            actual_amount = actual_by_type.get(cost_type, {}).get("total", 0.0)
            variance = actual_amount - budgeted_amount
            variance_percentage = (
                (variance / budgeted_amount * 100) if budgeted_amount > 0 else 0.0
            )

            variance_analysis[cost_type] = {
                "budgeted_amount": budgeted_amount,
                "actual_amount": actual_amount,
                "variance": round(variance, 2),
                "variance_percentage": round(variance_percentage, 1),
                "status": (
                    "over_budget"
                    if variance > 0
                    else (
                        "under_budget"
                        if variance < -budgeted_amount * 0.05
                        else "on_budget"
                    )
                ),
            }

        return {
            "project_id": project_id,
            "variance_report": {
                "total_budget": total_budget,
                "total_actual": total_actual,
                "overall_variance": round(total_actual - total_budget, 2),
                "overall_variance_percentage": (
                    round(((total_actual - total_budget) / total_budget * 100), 1)
                    if total_budget > 0
                    else 0.0
                ),
            },
            "variance_by_type": variance_analysis,
            "report_date": datetime.now().isoformat(),
        }

    def transfer_costs_between_projects(
        self, cost_ids: List[int], target_project_id: int, transfer_reason: str
    ) -> Dict[str, Any]:
        """
        Transfer cost entries from one project to another.

        Args:
            cost_ids: List of cost entry IDs to transfer
            target_project_id: ID of the target project
            transfer_reason: Reason for the transfer

        Returns:
            Transfer operation results
        """
        transfer_results = []

        for cost_id in cost_ids:
            try:
                cost_entry = self.get(cost_id)
                if not cost_entry:
                    transfer_results.append(
                        {
                            "cost_id": cost_id,
                            "success": False,
                            "error": "Cost entry not found",
                        }
                    )
                    continue

                original_project_id = cost_entry["projectID"]

                # Update project ID and add transfer info
                updated_cost = self.update(
                    {
                        "id": cost_id,
                        "projectID": target_project_id,
                        "transferDate": datetime.now().isoformat(),
                        "transferReason": transfer_reason,
                        "originalProjectID": original_project_id,
                    }
                )

                transfer_results.append(
                    {
                        "cost_id": cost_id,
                        "original_project_id": original_project_id,
                        "cost_amount": cost_entry["costAmount"],
                        "success": True,
                    }
                )

            except Exception as e:
                transfer_results.append(
                    {"cost_id": cost_id, "success": False, "error": str(e)}
                )

        successful = [r for r in transfer_results if r["success"]]
        failed = [r for r in transfer_results if not r["success"]]
        total_amount_transferred = sum(
            float(r.get("cost_amount", 0)) for r in successful
        )

        return {
            "target_project_id": target_project_id,
            "transfer_reason": transfer_reason,
            "transfer_summary": {
                "total_cost_entries": len(cost_ids),
                "successful_transfers": len(successful),
                "failed_transfers": len(failed),
                "total_amount_transferred": round(total_amount_transferred, 2),
            },
            "transfer_date": datetime.now().isoformat(),
            "results": transfer_results,
        }
