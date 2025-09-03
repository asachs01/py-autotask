"""
Project Budgets entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ProjectBudgetsEntity(BaseEntity):
    """
    Handles all Project Budget-related operations for the Autotask API.

    Project budgets manage budget tracking and variance analysis for projects,
    providing financial oversight and cost control capabilities.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_project_budget(
        self,
        project_id: int,
        budget_amount: Decimal,
        budget_type: str = "total",  # total, labor, materials, expenses
        budget_period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new project budget.

        Args:
            project_id: ID of the associated project
            budget_amount: Budget amount
            budget_type: Type of budget (total, labor, materials, expenses)
            budget_period: Budget period (monthly, quarterly, annual, project)
            start_date: Budget start date (ISO format)
            end_date: Budget end date (ISO format)
            **kwargs: Additional budget fields

        Returns:
            Created project budget data

        Example:
            budget = client.project_budgets.create_project_budget(
                12345,
                Decimal('50000.00'),
                budget_type="total",
                budget_period="project",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
        """
        budget_data = {
            "ProjectID": project_id,
            "BudgetAmount": str(budget_amount),
            "BudgetType": budget_type,
            **kwargs,
        }

        if budget_period:
            budget_data["BudgetPeriod"] = budget_period
        if start_date:
            budget_data["StartDate"] = start_date
        if end_date:
            budget_data["EndDate"] = end_date

        return self.create(budget_data)

    def get_project_budgets(
        self,
        project_id: int,
        budget_type: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all budgets for a specific project.

        Args:
            project_id: Project ID to filter by
            budget_type: Optional budget type filter
            active_only: Whether to return only active budgets
            limit: Maximum number of budgets to return

        Returns:
            List of project budgets

        Example:
            budgets = client.project_budgets.get_project_budgets(12345)
        """
        filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        if budget_type:
            filters.append({"field": "BudgetType", "op": "eq", "value": budget_type})

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_budget_variance_analysis(
        self, budget_id: int, as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get budget variance analysis for a specific budget.

        Args:
            budget_id: ID of the budget to analyze
            as_of_date: Date for analysis (ISO format, defaults to today)

        Returns:
            Budget variance analysis

        Example:
            analysis = client.project_budgets.get_budget_variance_analysis(12345)
        """
        budget = self.get(budget_id)
        if not budget:
            return {}

        project_id = budget.get("ProjectID")
        budget_amount = Decimal(str(budget.get("BudgetAmount", 0)))
        budget_type = budget.get("BudgetType", "total")

        if not as_of_date:
            as_of_date = datetime.now().isoformat()

        # Get actual costs based on budget type
        actual_costs = self._get_actual_costs(
            project_id, budget_type, as_of_date, budget
        )

        # Calculate variance
        variance_amount = budget_amount - actual_costs
        variance_percentage = (
            (variance_amount / budget_amount * 100) if budget_amount != 0 else 0
        )

        # Determine status
        if variance_amount > 0:
            status = "under_budget"
        elif variance_amount < 0:
            status = "over_budget"
        else:
            status = "on_budget"

        # Calculate burn rate if dates available
        burn_rate_info = self._calculate_burn_rate(budget, actual_costs, as_of_date)

        return {
            "budget_id": budget_id,
            "project_id": project_id,
            "budget_type": budget_type,
            "analysis_date": as_of_date,
            "budget_amount": float(budget_amount),
            "actual_costs": float(actual_costs),
            "variance_amount": float(variance_amount),
            "variance_percentage": round(float(variance_percentage), 2),
            "status": status,
            "utilization_percentage": (
                round(float(actual_costs / budget_amount * 100), 2)
                if budget_amount != 0
                else 0
            ),
            "burn_rate": burn_rate_info,
        }

    def get_project_budget_summary(
        self, project_id: int, as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive budget summary for a project.

        Args:
            project_id: ID of the project
            as_of_date: Date for analysis (ISO format, defaults to today)

        Returns:
            Project budget summary

        Example:
            summary = client.project_budgets.get_project_budget_summary(12345)
        """
        if not as_of_date:
            as_of_date = datetime.now().isoformat()

        budgets = self.get_project_budgets(project_id)

        summary = {
            "project_id": project_id,
            "analysis_date": as_of_date,
            "budget_count": len(budgets),
            "budgets": [],
            "totals": {
                "total_budget": Decimal("0"),
                "total_actual": Decimal("0"),
                "total_variance": Decimal("0"),
                "overall_status": "on_budget",
            },
        }

        for budget in budgets:
            budget_id = budget.get("id")
            if budget_id:
                analysis = self.get_budget_variance_analysis(budget_id, as_of_date)
                summary["budgets"].append(analysis)

                # Add to totals
                summary["totals"]["total_budget"] += Decimal(
                    str(analysis["budget_amount"])
                )
                summary["totals"]["total_actual"] += Decimal(
                    str(analysis["actual_costs"])
                )
                summary["totals"]["total_variance"] += Decimal(
                    str(analysis["variance_amount"])
                )

        # Calculate overall status
        total_variance = summary["totals"]["total_variance"]
        if total_variance > 0:
            summary["totals"]["overall_status"] = "under_budget"
        elif total_variance < 0:
            summary["totals"]["overall_status"] = "over_budget"

        # Convert decimals to floats for JSON serialization
        summary["totals"]["total_budget"] = float(summary["totals"]["total_budget"])
        summary["totals"]["total_actual"] = float(summary["totals"]["total_actual"])
        summary["totals"]["total_variance"] = float(summary["totals"]["total_variance"])

        if summary["totals"]["total_budget"] != 0:
            summary["totals"]["overall_variance_percentage"] = round(
                summary["totals"]["total_variance"]
                / summary["totals"]["total_budget"]
                * 100,
                2,
            )
        else:
            summary["totals"]["overall_variance_percentage"] = 0

        return summary

    def update_budget_amount(
        self, budget_id: int, new_amount: Decimal, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Update budget amount with optional reason.

        Args:
            budget_id: ID of budget to update
            new_amount: New budget amount
            reason: Optional reason for the change

        Returns:
            Updated budget data

        Example:
            updated = client.project_budgets.update_budget_amount(
                12345, Decimal('60000.00'), "Scope increase approved"
            )
        """
        update_data = {
            "BudgetAmount": str(new_amount),
            "LastModifiedDate": datetime.now().isoformat(),
        }

        if reason:
            update_data["ChangeReason"] = reason

        return self.update_by_id(budget_id, update_data)

    def forecast_budget_completion(
        self, budget_id: int, forecast_method: str = "linear"
    ) -> Dict[str, Any]:
        """
        Forecast budget completion based on current spending patterns.

        Args:
            budget_id: ID of the budget to forecast
            forecast_method: Forecasting method (linear, weighted, exponential)

        Returns:
            Budget completion forecast

        Example:
            forecast = client.project_budgets.forecast_budget_completion(12345)
        """
        budget = self.get(budget_id)
        if not budget:
            return {}

        variance_analysis = self.get_budget_variance_analysis(budget_id)
        budget_amount = Decimal(str(variance_analysis["budget_amount"]))
        actual_costs = Decimal(str(variance_analysis["actual_costs"]))

        # Get project timeline
        project_id = budget.get("ProjectID")
        project_filters = [{"field": "id", "op": "eq", "value": project_id}]

        try:
            project_response = self.client.query("Projects", project_filters)
            projects = (
                project_response.items
                if hasattr(project_response, "items")
                else project_response
            )
            project = projects[0] if projects else {}
        except Exception:
            project = {}

        # Calculate forecast based on method
        if forecast_method == "linear":
            forecast_data = self._linear_forecast(
                budget, actual_costs, budget_amount, project
            )
        elif forecast_method == "weighted":
            forecast_data = self._weighted_forecast(
                budget, actual_costs, budget_amount, project
            )
        else:
            forecast_data = self._linear_forecast(
                budget, actual_costs, budget_amount, project
            )

        return {
            "budget_id": budget_id,
            "forecast_method": forecast_method,
            "current_analysis": variance_analysis,
            "forecast": forecast_data,
        }

    def get_budget_alerts(
        self, project_id: Optional[int] = None, threshold_percentage: float = 80.0
    ) -> List[Dict[str, Any]]:
        """
        Get budget alerts for budgets approaching or exceeding thresholds.

        Args:
            project_id: Optional project filter
            threshold_percentage: Threshold for alerts (default 80%)

        Returns:
            List of budget alerts

        Example:
            alerts = client.project_budgets.get_budget_alerts(threshold_percentage=75.0)
        """
        filters = []
        if project_id:
            filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        # Get all budgets (or for specific project)
        response = self.query(filters=filters)
        budgets = response.items if hasattr(response, "items") else response

        alerts = []

        for budget in budgets:
            budget_id = budget.get("id")
            if not budget_id:
                continue

            analysis = self.get_budget_variance_analysis(budget_id)
            utilization = analysis.get("utilization_percentage", 0)

            alert_level = None
            if utilization >= 100:
                alert_level = "critical"  # Over budget
            elif utilization >= 90:
                alert_level = "high"  # 90%+ utilized
            elif utilization >= threshold_percentage:
                alert_level = "medium"  # Above threshold

            if alert_level:
                alerts.append(
                    {
                        "budget_id": budget_id,
                        "project_id": budget.get("ProjectID"),
                        "budget_type": budget.get("BudgetType"),
                        "alert_level": alert_level,
                        "utilization_percentage": utilization,
                        "budget_amount": analysis.get("budget_amount"),
                        "actual_costs": analysis.get("actual_costs"),
                        "variance_amount": analysis.get("variance_amount"),
                        "message": self._generate_alert_message(
                            alert_level, utilization, analysis
                        ),
                    }
                )

        # Sort by alert level priority
        priority_order = {"critical": 0, "high": 1, "medium": 2}
        alerts.sort(key=lambda x: priority_order.get(x["alert_level"], 3))

        return alerts

    def bulk_update_budgets(
        self, budget_updates: List[Dict[str, Any]], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Update multiple budgets in batches.

        Args:
            budget_updates: List of budget update data (must include 'id' field)
            batch_size: Number of budgets to update per batch

        Returns:
            List of updated budget data

        Example:
            updates = [
                {'id': 12345, 'BudgetAmount': '55000.00'},
                {'id': 12346, 'BudgetAmount': '75000.00'}
            ]
            results = client.project_budgets.bulk_update_budgets(updates)
        """
        results = []

        for i in range(0, len(budget_updates), batch_size):
            batch = budget_updates[i : i + batch_size]

            for update in batch:
                try:
                    budget_id = update.pop("id")
                    result = self.update_by_id(budget_id, update)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update budget {update.get('id')}: {e}"
                    )
                    continue

        return results

    def clone_project_budget(
        self,
        budget_id: int,
        new_project_id: int,
        adjust_amount: Optional[Decimal] = None,
    ) -> EntityDict:
        """
        Clone a budget to another project.

        Args:
            budget_id: ID of budget to clone
            new_project_id: Target project ID
            adjust_amount: Optional new budget amount

        Returns:
            Created cloned budget data

        Example:
            cloned = client.project_budgets.clone_project_budget(
                12345, 67890, adjust_amount=Decimal('45000.00')
            )
        """
        original = self.get(budget_id)
        if not original:
            raise ValueError(f"Budget {budget_id} not found")

        clone_data = {
            "ProjectID": new_project_id,
            "BudgetAmount": (
                str(adjust_amount) if adjust_amount else original.get("BudgetAmount")
            ),
            "BudgetType": original.get("BudgetType"),
            "BudgetPeriod": original.get("BudgetPeriod"),
            "StartDate": original.get("StartDate"),
            "EndDate": original.get("EndDate"),
        }

        return self.create(clone_data)

    def _get_actual_costs(
        self, project_id: int, budget_type: str, as_of_date: str, budget: EntityDict
    ) -> Decimal:
        """
        Calculate actual costs for a project based on budget type.

        Args:
            project_id: Project ID
            budget_type: Type of budget (total, labor, materials, expenses)
            as_of_date: Date for cost calculation
            budget: Budget entity data

        Returns:
            Actual costs as Decimal
        """
        total_costs = Decimal("0")

        try:
            if budget_type in ["total", "labor"]:
                # Get time entries
                time_filters = [
                    {"field": "ProjectID", "op": "eq", "value": project_id},
                    {"field": "DateWorked", "op": "lte", "value": as_of_date},
                ]

                if budget.get("StartDate"):
                    time_filters.append(
                        {
                            "field": "DateWorked",
                            "op": "gte",
                            "value": budget["StartDate"],
                        }
                    )

                time_response = self.client.query("TimeEntries", time_filters)
                time_entries = (
                    time_response.items
                    if hasattr(time_response, "items")
                    else time_response
                )

                for entry in time_entries:
                    hours = float(entry.get("HoursWorked", 0))
                    rate = float(entry.get("HourlyRate", 0))
                    total_costs += Decimal(str(hours * rate))

            if budget_type in ["total", "expenses"]:
                # Get expense entries
                expense_filters = [
                    {"field": "ProjectID", "op": "eq", "value": project_id},
                    {"field": "ExpenseDate", "op": "lte", "value": as_of_date},
                ]

                if budget.get("StartDate"):
                    expense_filters.append(
                        {
                            "field": "ExpenseDate",
                            "op": "gte",
                            "value": budget["StartDate"],
                        }
                    )

                expense_response = self.client.query("Expenses", expense_filters)
                expenses = (
                    expense_response.items
                    if hasattr(expense_response, "items")
                    else expense_response
                )

                for expense in expenses:
                    amount = float(expense.get("Amount", 0))
                    total_costs += Decimal(str(amount))

            # Could add materials/inventory costs here if needed

        except Exception as e:
            self.logger.error(f"Error calculating actual costs: {e}")

        return total_costs

    def _calculate_burn_rate(
        self, budget: EntityDict, actual_costs: Decimal, as_of_date: str
    ) -> Dict[str, Any]:
        """
        Calculate budget burn rate information.
        """
        try:
            start_date_str = budget.get("StartDate")
            if not start_date_str:
                return {}

            start_date = datetime.fromisoformat(start_date_str).date()
            current_date = datetime.fromisoformat(as_of_date).date()

            days_elapsed = (current_date - start_date).days + 1
            if days_elapsed <= 0:
                return {}

            daily_burn_rate = actual_costs / days_elapsed

            # Calculate projected completion
            budget_amount = Decimal(str(budget.get("BudgetAmount", 0)))
            if daily_burn_rate > 0:
                days_to_completion = budget_amount / daily_burn_rate
                projected_completion_date = start_date + timedelta(
                    days=int(days_to_completion)
                )
            else:
                projected_completion_date = None

            return {
                "daily_burn_rate": float(daily_burn_rate),
                "days_elapsed": days_elapsed,
                "projected_completion_date": (
                    projected_completion_date.isoformat()
                    if projected_completion_date
                    else None
                ),
            }

        except (ValueError, TypeError):
            return {}

    def _linear_forecast(
        self,
        budget: EntityDict,
        actual_costs: Decimal,
        budget_amount: Decimal,
        project: EntityDict,
    ) -> Dict[str, Any]:
        """
        Perform linear forecast calculation.
        """
        try:
            start_date = datetime.fromisoformat(
                budget.get("StartDate", datetime.now().isoformat())
            ).date()
            end_date = datetime.fromisoformat(
                budget.get(
                    "EndDate", project.get("EndDate", datetime.now().isoformat())
                )
            ).date()
            current_date = datetime.now().date()

            total_days = (end_date - start_date).days + 1
            elapsed_days = (current_date - start_date).days + 1
            remaining_days = (end_date - current_date).days

            if elapsed_days <= 0:
                return {"error": "Project not started"}

            daily_spend_rate = actual_costs / elapsed_days
            projected_total_cost = daily_spend_rate * total_days
            projected_remaining_cost = daily_spend_rate * remaining_days

            return {
                "projected_total_cost": float(projected_total_cost),
                "projected_remaining_cost": float(projected_remaining_cost),
                "projected_variance": float(budget_amount - projected_total_cost),
                "completion_percentage": min(100, elapsed_days / total_days * 100),
                "days_remaining": max(0, remaining_days),
            }

        except (ValueError, TypeError):
            return {"error": "Invalid date format in forecast calculation"}

    def _weighted_forecast(
        self,
        budget: EntityDict,
        actual_costs: Decimal,
        budget_amount: Decimal,
        project: EntityDict,
    ) -> Dict[str, Any]:
        """
        Perform weighted forecast calculation (more recent data weighted higher).
        """
        # For now, use linear forecast
        # In a real implementation, this would analyze spending patterns over time
        # and weight recent spending more heavily
        return self._linear_forecast(budget, actual_costs, budget_amount, project)

    def _generate_alert_message(
        self, alert_level: str, utilization: float, analysis: Dict[str, Any]
    ) -> str:
        """
        Generate alert message based on budget status.
        """
        if alert_level == "critical":
            return f"Budget exceeded! Current spending: {utilization:.1f}% of budget"
        elif alert_level == "high":
            return f"Budget nearly exhausted: {utilization:.1f}% utilized"
        else:
            return f"Budget threshold reached: {utilization:.1f}% utilized"
