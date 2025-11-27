"""
Projects entity for Autotask API operations.

This module provides comprehensive PSA functionality for project management
including budgeting, cost tracking, resource allocation, milestone tracking,
profitability analysis, templates, and Gantt/dependency management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from ..constants import ProjectStatus, ProjectType
from ..exceptions import AutotaskValidationError
from ..types import ProjectData, QueryFilter
from .base import BaseEntity


class ProjectConstants:
    """Constants for project management."""

    # Project Types (using centralized constants)
    PROJECT_TYPE_FIXED_PRICE = ProjectType.FIXED_PRICE
    PROJECT_TYPE_TIME_MATERIALS = ProjectType.TIME_AND_MATERIALS
    PROJECT_TYPE_MILESTONE = ProjectType.MILESTONE
    PROJECT_TYPE_RETAINER = ProjectType.RETAINER
    PROJECT_TYPE_RECURRING_SERVICE = ProjectType.RECURRING_SERVICE

    # Project Status (using centralized constants)
    STATUS_NEW = ProjectStatus.NEW
    STATUS_IN_PROGRESS = ProjectStatus.IN_PROGRESS
    STATUS_ON_HOLD = ProjectStatus.ON_HOLD
    STATUS_COMPLETE = ProjectStatus.COMPLETE
    STATUS_CANCELLED = ProjectStatus.CANCELLED

    # Priority Levels
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_CRITICAL = 4

    # Billing Methods
    BILLING_BILLABLE = 1
    BILLING_NON_BILLABLE = 2
    BILLING_NO_CHARGE = 3

    # Phase Status
    PHASE_STATUS_NEW = 1
    PHASE_STATUS_IN_PROGRESS = 2
    PHASE_STATUS_COMPLETE = 3
    PHASE_STATUS_ON_HOLD = 4

    @classmethod
    def get_project_types(cls) -> Dict[int, str]:
        """Get mapping of project type IDs to names."""
        return {
            cls.PROJECT_TYPE_FIXED_PRICE: "Fixed Price",
            cls.PROJECT_TYPE_TIME_MATERIALS: "Time & Materials",
            cls.PROJECT_TYPE_MILESTONE: "Milestone",
            cls.PROJECT_TYPE_RETAINER: "Retainer",
            cls.PROJECT_TYPE_RECURRING_SERVICE: "Recurring Service",
        }

    @classmethod
    def get_status_names(cls) -> Dict[int, str]:
        """Get mapping of status IDs to names."""
        return {
            cls.STATUS_NEW: "New",
            cls.STATUS_IN_PROGRESS: "In Progress",
            cls.STATUS_ON_HOLD: "On Hold",
            cls.STATUS_COMPLETE: "Complete",
            cls.STATUS_CANCELLED: "Cancelled",
        }

    @classmethod
    def get_priority_names(cls) -> Dict[int, str]:
        """Get mapping of priority IDs to names."""
        return {
            cls.PRIORITY_LOW: "Low",
            cls.PRIORITY_MEDIUM: "Medium",
            cls.PRIORITY_HIGH: "High",
            cls.PRIORITY_CRITICAL: "Critical",
        }


class ProjectsEntity(BaseEntity):
    """
    Handles comprehensive project management operations for the Autotask API.

    Provides PSA functionality including:
    - Budget and cost tracking
    - Resource allocation and optimization
    - Milestone and phase management
    - Profitability analysis
    - Project templates
    - Gantt chart data and dependency management
    - Progress tracking and reporting
    """

    def __init__(self, client, entity_name="Projects"):
        """
        Initialize the Projects entity.

        Args:
            client: AutotaskClient instance
            entity_name: Name of the entity (default: "Projects")
        """
        super().__init__(client, entity_name)
        self.constants = ProjectConstants

    def create_project(
        self,
        project_name: str,
        account_id: int,
        project_type: int = ProjectType.FIXED_PRICE,
        status: int = ProjectStatus.NEW,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> ProjectData:
        """
        Create a new project with required and optional fields.

        Args:
            project_name: Name of the project
            account_id: ID of the associated account/company
            project_type: Type of project (use ProjectType enum)
            status: Project status (use ProjectStatus enum)
            start_date: Project start date (ISO format)
            end_date: Project end date (ISO format)
            description: Project description
            **kwargs: Additional project fields

        Returns:
            Created project data
        """
        project_data = {
            "ProjectName": project_name,
            "AccountID": account_id,
            "Type": project_type,
            "Status": status,
            **kwargs,
        }

        if start_date:
            project_data["StartDate"] = start_date
        if end_date:
            project_data["EndDate"] = end_date
        if description:
            project_data["Description"] = description

        return self.create(project_data)

    def get_projects_by_account(
        self,
        account_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get all projects for a specific account.

        Args:
            account_id: Account ID to filter by
            status_filter: Optional status filter ('active', 'completed', etc.)
            limit: Maximum number of projects to return

        Returns:
            List of projects for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        if status_filter:
            status_map = {
                "active": [1, 2, 3, 4],  # New, In Progress, On Hold, Waiting
                "completed": [5],  # Complete
                "new": [1],  # New
                "in_progress": [2],  # In Progress
                "on_hold": [3],  # On Hold
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        return self.query(filters=filters, max_records=limit)

    def get_projects_by_manager(
        self,
        manager_id: int,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get projects managed by a specific resource.

        Args:
            manager_id: Project manager resource ID
            include_completed: Whether to include completed projects
            limit: Maximum number of projects to return

        Returns:
            List of projects managed by the resource
        """
        filters = [
            QueryFilter(field="ProjectManagerResourceID", op="eq", value=manager_id)
        ]

        if not include_completed:
            filters.append(
                QueryFilter(field="Status", op="ne", value=5)
            )  # Not Complete

        return self.query(filters=filters, max_records=limit)

    def update_project_status(self, project_id: int, status: int) -> ProjectData:
        """
        Update a project's status.

        Args:
            project_id: ID of project to update
            status: New status ID

        Returns:
            Updated project data
        """
        return self.update_by_id(project_id, {"Status": status})

    def get_project_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of tasks for the project
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]
        return self.client.query("Tasks", filters=filters)

    def get_project_time_entries(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all time entries for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of time entries for the project
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]
        return self.client.query("TimeEntries", filters=filters)

    def get_projects_by_status(
        self, status: int, account_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[ProjectData]:
        """
        Get projects by status.

        Args:
            status: Project status ID
            account_id: Optional account filter
            limit: Maximum number of projects to return

        Returns:
            List of projects with the specified status
        """
        filters = [QueryFilter(field="Status", op="eq", value=status)]

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        return self.query(filters=filters, max_records=limit)

    def get_active_projects(
        self, account_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[ProjectData]:
        """
        Get active projects (not complete, cancelled, or on hold).

        Args:
            account_id: Optional account filter
            limit: Maximum number of projects to return

        Returns:
            List of active projects
        """
        # Exclude common inactive statuses: Complete(5), Cancelled(7), On Hold(3)
        filters = [QueryFilter(field="Status", op="not_in", value=[3, 5, 7])]

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        return self.query(filters=filters, max_records=limit)

    def get_overdue_projects(
        self, account_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[ProjectData]:
        """
        Get projects that are past their end date.

        Args:
            account_id: Optional account filter
            limit: Maximum number of projects to return

        Returns:
            List of overdue projects
        """
        from datetime import datetime

        filters = [
            QueryFilter(field="EndDate", op="lt", value=datetime.now().isoformat()),
            QueryFilter(field="Status", op="ne", value=5),  # Not complete
        ]

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        return self.query(filters=filters, max_records=limit)

    def get_project_tickets(
        self,
        project_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all tickets associated with a project.

        Args:
            project_id: ID of the project
            status_filter: Optional status filter ('open', 'closed', etc.)
            limit: Maximum number of tickets to return

        Returns:
            List of project tickets
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if status_filter:
            status_map = {"open": [1, 8, 9, 10, 11], "closed": [5], "new": [1]}

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        return self.client.query("Tickets", filters=filters, max_records=limit)

    def complete_project(
        self, project_id: int, completion_note: Optional[str] = None
    ) -> ProjectData:
        """
        Mark a project as complete.

        Args:
            project_id: ID of project to complete
            completion_note: Optional completion note

        Returns:
            Updated project data
        """
        from datetime import datetime

        update_data = {
            "Status": 5,  # Complete status
            "EndDate": datetime.now().isoformat(),
        }

        if completion_note:
            update_data["StatusDetail"] = completion_note

        return self.update_by_id(project_id, update_data)

    def assign_project_manager(self, project_id: int, manager_id: int) -> ProjectData:
        """
        Assign a project manager to a project.

        Args:
            project_id: ID of project to update
            manager_id: Resource ID of the project manager

        Returns:
            Updated project data
        """
        update_data = {"ProjectManagerResourceID": manager_id}
        return self.update_by_id(project_id, update_data)

    # ==================== BUDGETING AND COST TRACKING ====================

    def set_project_budget(
        self, project_id: int, budget_data: Dict[str, Union[float, int]]
    ) -> ProjectData:
        """
        Set or update project budget information.

        Args:
            project_id: ID of the project
            budget_data: Budget information containing:
                - labor_budget: Labor budget amount
                - expense_budget: Expense budget amount
                - material_budget: Material budget amount
                - total_budget: Total project budget
                - budget_hours: Budgeted hours

        Returns:
            Updated project data

        Raises:
            AutotaskValidationError: If budget data is invalid
        """
        required_fields = ["total_budget"]
        for field in required_fields:
            if field not in budget_data:
                raise AutotaskValidationError(f"Missing required budget field: {field}")

        # Validate positive budget values
        for key, value in budget_data.items():
            if isinstance(value, (int, float)) and value < 0:
                raise AutotaskValidationError(
                    f"Budget value for {key} cannot be negative"
                )

        update_data = {}
        field_mapping = {
            "labor_budget": "LaborCost",
            "expense_budget": "ExpenseCost",
            "material_budget": "MaterialCost",
            "total_budget": "ProjectCost",
            "budget_hours": "EstimatedTime",
        }

        for key, field_name in field_mapping.items():
            if key in budget_data:
                update_data[field_name] = budget_data[key]

        return self.update_by_id(project_id, update_data)

    def track_project_costs(
        self, project_id: int, cost_data: Dict[str, Union[float, int]]
    ) -> Dict[str, Any]:
        """
        Track actual project costs against budget.

        Args:
            project_id: ID of the project
            cost_data: Cost information to track:
                - actual_labor: Actual labor costs incurred
                - actual_expenses: Actual expense costs
                - actual_materials: Actual material costs
                - actual_hours: Actual hours worked

        Returns:
            Dictionary with cost tracking information

        Raises:
            AutotaskValidationError: If cost data is invalid
        """
        # Get current project data for budget comparison
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        # Calculate cost variances
        cost_summary = {
            "project_id": project_id,
            "tracking_date": datetime.now().isoformat(),
            "actual_costs": cost_data,
            "budget_comparison": {},
            "variances": {},
            "cost_performance": {},
        }

        # Compare against budgets
        budget_fields = {
            "actual_labor": ("LaborCost", "labor_budget"),
            "actual_expenses": ("ExpenseCost", "expense_budget"),
            "actual_materials": ("MaterialCost", "material_budget"),
            "actual_hours": ("EstimatedTime", "budget_hours"),
        }

        for cost_type, (budget_field, friendly_name) in budget_fields.items():
            if cost_type in cost_data:
                actual_value = cost_data[cost_type]
                budget_value = project.get(budget_field, 0)

                variance = actual_value - budget_value if budget_value else 0
                variance_percent = (
                    (variance / budget_value * 100) if budget_value else 0
                )

                cost_summary["budget_comparison"][friendly_name] = budget_value
                cost_summary["variances"][friendly_name] = {
                    "amount": variance,
                    "percentage": round(variance_percent, 2),
                }

                # Performance indicators
                if budget_value > 0:
                    performance = (
                        "over_budget"
                        if variance > 0
                        else "under_budget" if variance < 0 else "on_budget"
                    )
                    cost_summary["cost_performance"][friendly_name] = performance

        return cost_summary

    def get_budget_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get comprehensive budget status for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with budget status information

        Raises:
            AutotaskValidationError: If project not found
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        # Get actual costs from time entries and expenses
        time_entries = self.get_project_time_entries(project_id)

        actual_hours = sum(float(entry.get("HoursWorked", 0)) for entry in time_entries)
        actual_labor_cost = sum(
            float(entry.get("BillableAmount", 0)) for entry in time_entries
        )

        # Get expense data (would need separate API call in real implementation)
        # For now, we'll use project tracking data if available

        budget_status = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "status_date": datetime.now().isoformat(),
            "budgets": {
                "labor_budget": project.get("LaborCost", 0),
                "expense_budget": project.get("ExpenseCost", 0),
                "material_budget": project.get("MaterialCost", 0),
                "total_budget": project.get("ProjectCost", 0),
                "budget_hours": project.get("EstimatedTime", 0),
            },
            "actuals": {
                "actual_hours": actual_hours,
                "actual_labor_cost": actual_labor_cost,
                "actual_expenses": 0,  # Would be populated from expense API
                "actual_materials": 0,  # Would be populated from material API
            },
            "remaining": {},
            "utilization": {},
            "alerts": [],
        }

        # Calculate remaining budget and utilization
        for budget_type, budget_amount in budget_status["budgets"].items():
            if budget_type == "budget_hours":
                actual_key = "actual_hours"
            elif budget_type == "labor_budget":
                actual_key = "actual_labor_cost"
            else:
                continue  # Skip others for now

            actual_amount = budget_status["actuals"].get(actual_key, 0)
            remaining = budget_amount - actual_amount
            utilization = (
                (actual_amount / budget_amount * 100) if budget_amount > 0 else 0
            )

            budget_status["remaining"][budget_type] = remaining
            budget_status["utilization"][budget_type] = round(utilization, 2)

            # Add budget alerts
            if utilization > 90:
                budget_status["alerts"].append(
                    {
                        "type": "warning",
                        "category": budget_type,
                        "message": f"{budget_type} is {utilization:.1f}% utilized",
                    }
                )
            elif utilization > 100:
                budget_status["alerts"].append(
                    {
                        "type": "critical",
                        "category": budget_type,
                        "message": f"{budget_type} is over budget by {utilization - 100:.1f}%",
                    }
                )

        return budget_status

    def calculate_project_profitability(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate project profitability metrics.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with profitability analysis

        Raises:
            AutotaskValidationError: If project not found
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        budget_status = self.get_budget_status(project_id)

        # Get revenue information
        total_budget = budget_status["budgets"]["total_budget"]
        actual_labor_cost = budget_status["actuals"]["actual_labor_cost"]
        actual_expenses = budget_status["actuals"]["actual_expenses"]
        actual_materials = budget_status["actuals"]["actual_materials"]

        total_costs = actual_labor_cost + actual_expenses + actual_materials

        profitability = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "analysis_date": datetime.now().isoformat(),
            "financial_summary": {
                "revenue": total_budget,
                "total_costs": total_costs,
                "gross_profit": total_budget - total_costs,
                "gross_margin": 0,
                "gross_margin_percent": 0,
            },
            "cost_breakdown": {
                "labor_costs": actual_labor_cost,
                "expense_costs": actual_expenses,
                "material_costs": actual_materials,
            },
            "profitability_metrics": {
                "roi": 0,
                "profit_per_hour": 0,
                "cost_efficiency": 0,
            },
            "status": "unknown",
        }

        # Calculate margins and metrics
        if total_budget > 0:
            gross_margin = total_budget - total_costs
            gross_margin_percent = (gross_margin / total_budget) * 100

            profitability["financial_summary"]["gross_margin"] = gross_margin
            profitability["financial_summary"]["gross_margin_percent"] = round(
                gross_margin_percent, 2
            )

            # ROI calculation
            roi = (gross_margin / total_costs) * 100 if total_costs > 0 else 0
            profitability["profitability_metrics"]["roi"] = round(roi, 2)

            # Profit per hour
            actual_hours = budget_status["actuals"]["actual_hours"]
            profit_per_hour = gross_margin / actual_hours if actual_hours > 0 else 0
            profitability["profitability_metrics"]["profit_per_hour"] = round(
                profit_per_hour, 2
            )

            # Cost efficiency (budget vs actual)
            budget_total = budget_status["budgets"]["total_budget"]
            cost_efficiency = (
                (budget_total - total_costs) / budget_total * 100
                if budget_total > 0
                else 0
            )
            profitability["profitability_metrics"]["cost_efficiency"] = round(
                cost_efficiency, 2
            )

            # Determine profitability status
            if gross_margin_percent > 20:
                profitability["status"] = "highly_profitable"
            elif gross_margin_percent > 10:
                profitability["status"] = "profitable"
            elif gross_margin_percent > 0:
                profitability["status"] = "marginally_profitable"
            else:
                profitability["status"] = "unprofitable"

        return profitability

    # ==================== RESOURCE ALLOCATION ====================

    def allocate_resource(
        self, project_id: int, resource_id: int, allocation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Allocate a resource to a project with specific parameters.

        Args:
            project_id: ID of the project
            resource_id: ID of the resource to allocate
            allocation_data: Allocation parameters:
                - allocation_percentage: Percentage of resource time (0-100)
                - start_date: Allocation start date
                - end_date: Allocation end date
                - role: Resource role in project
                - hourly_rate: Billable hourly rate
                - estimated_hours: Estimated hours for this resource

        Returns:
            Dictionary with allocation information

        Raises:
            AutotaskValidationError: If allocation data is invalid
        """
        required_fields = ["allocation_percentage", "start_date", "end_date"]
        for field in required_fields:
            if field not in allocation_data:
                raise AutotaskValidationError(
                    f"Missing required allocation field: {field}"
                )

        # Validate allocation percentage
        allocation_percent = allocation_data["allocation_percentage"]
        if not 0 <= allocation_percent <= 100:
            raise AutotaskValidationError(
                "Allocation percentage must be between 0 and 100"
            )

        # Validate dates
        start_date = allocation_data["start_date"]
        end_date = allocation_data["end_date"]

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        if end_date <= start_date:
            raise AutotaskValidationError("End date must be after start date")

        allocation_record = {
            "project_id": project_id,
            "resource_id": resource_id,
            "allocation_percentage": allocation_percent,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "role": allocation_data.get("role", "Team Member"),
            "hourly_rate": allocation_data.get("hourly_rate", 0),
            "estimated_hours": allocation_data.get("estimated_hours", 0),
            "status": "active",
            "created_date": datetime.now().isoformat(),
        }

        # In a real implementation, this would be stored in a project allocations table
        # For now, we'll return the allocation data structure
        return allocation_record

    def get_resource_allocation(self, project_id: int) -> Dict[str, Any]:
        """
        Get current resource allocation for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with resource allocation information
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        # Get project tasks to understand resource allocation
        tasks = self.get_project_tasks(project_id)

        # Analyze resource allocation from tasks
        resource_summary = {}
        total_estimated_hours = 0

        for task in tasks:
            resource_id = task.get("assignedResourceID")
            estimated_hours = float(task.get("estimatedHours", 0))

            if resource_id:
                if resource_id not in resource_summary:
                    resource_summary[resource_id] = {
                        "resource_id": resource_id,
                        "total_hours": 0,
                        "tasks_assigned": 0,
                        "completion_percentage": 0,
                        "utilization": 0,
                    }

                resource_summary[resource_id]["total_hours"] += estimated_hours
                resource_summary[resource_id]["tasks_assigned"] += 1

                # Calculate completion percentage from task progress
                percent_complete = float(task.get("percentComplete", 0))
                resource_summary[resource_id][
                    "completion_percentage"
                ] += percent_complete

            total_estimated_hours += estimated_hours

        # Calculate utilization and average completion
        for resource_id, data in resource_summary.items():
            task_count = data["tasks_assigned"]
            data["completion_percentage"] = (
                data["completion_percentage"] / task_count if task_count > 0 else 0
            )
            data["utilization"] = (
                (data["total_hours"] / total_estimated_hours * 100)
                if total_estimated_hours > 0
                else 0
            )
            data["utilization"] = round(data["utilization"], 2)

        allocation_report = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "total_estimated_hours": total_estimated_hours,
            "resources_allocated": len(resource_summary),
            "resource_breakdown": list(resource_summary.values()),
            "allocation_date": datetime.now().isoformat(),
        }

        return allocation_report

    def optimize_resource_allocation(self, project_id: int) -> Dict[str, Any]:
        """
        Analyze and provide recommendations for optimizing resource allocation.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with optimization recommendations
        """
        allocation_data = self.get_resource_allocation(project_id)
        project = self.get_by_id(project_id)

        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        recommendations = {
            "project_id": project_id,
            "analysis_date": datetime.now().isoformat(),
            "current_allocation": allocation_data,
            "optimization_opportunities": [],
            "recommendations": [],
            "risk_factors": [],
            "efficiency_score": 0,
        }

        resources = allocation_data["resource_breakdown"]

        # Analyze resource utilization
        over_allocated = []
        under_allocated = []
        balanced_allocation = []

        for resource in resources:
            utilization = resource["utilization"]
            completion = resource["completion_percentage"]

            if utilization > 80:
                over_allocated.append(resource)
                recommendations["risk_factors"].append(
                    {
                        "type": "over_allocation",
                        "resource_id": resource["resource_id"],
                        "message": f"Resource {resource['resource_id']} is {utilization}% utilized (high risk)",
                    }
                )
            elif utilization < 20:
                under_allocated.append(resource)
                recommendations["optimization_opportunities"].append(
                    {
                        "type": "under_utilization",
                        "resource_id": resource["resource_id"],
                        "message": f"Resource {resource['resource_id']} is only {utilization}% utilized",
                    }
                )
            else:
                balanced_allocation.append(resource)

        # Generate recommendations
        if over_allocated:
            recommendations["recommendations"].append(
                {
                    "priority": "high",
                    "action": "redistribute_workload",
                    "description": "Consider redistributing tasks from over-allocated resources",
                    "affected_resources": [r["resource_id"] for r in over_allocated],
                }
            )

        if under_allocated:
            recommendations["recommendations"].append(
                {
                    "priority": "medium",
                    "action": "increase_utilization",
                    "description": "Consider assigning additional tasks to under-utilized resources",
                    "affected_resources": [r["resource_id"] for r in under_allocated],
                }
            )

        # Calculate efficiency score
        total_resources = len(resources)
        balanced_count = len(balanced_allocation)
        efficiency_score = (
            (balanced_count / total_resources * 100) if total_resources > 0 else 0
        )
        recommendations["efficiency_score"] = round(efficiency_score, 2)

        # Add performance insights
        avg_completion = (
            sum(r["completion_percentage"] for r in resources) / len(resources)
            if resources
            else 0
        )

        if avg_completion < 30:
            recommendations["recommendations"].append(
                {
                    "priority": "high",
                    "action": "review_project_progress",
                    "description": f"Project completion average is {avg_completion:.1f}% - review blocking factors",
                }
            )

        return recommendations

    # ==================== MILESTONE AND PHASE MANAGEMENT ====================

    def add_project_phase(
        self, project_id: int, phase_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a phase to a project.

        Args:
            project_id: ID of the project
            phase_data: Phase information:
                - title: Phase title
                - description: Phase description
                - start_date: Phase start date
                - end_date: Phase end date
                - estimated_hours: Estimated hours for phase
                - budget: Phase budget
                - status: Phase status (default: New)

        Returns:
            Dictionary with created phase information

        Raises:
            AutotaskValidationError: If phase data is invalid
        """
        required_fields = ["title", "description", "start_date", "end_date"]
        for field in required_fields:
            if field not in phase_data:
                raise AutotaskValidationError(f"Missing required phase field: {field}")

        # Validate dates
        start_date = phase_data["start_date"]
        end_date = phase_data["end_date"]

        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        if end_date <= start_date:
            raise AutotaskValidationError("Phase end date must be after start date")

        # Create phase record structure
        phase_record = {
            "id": f"phase_{datetime.now().timestamp()}",  # Generate temporary ID
            "project_id": project_id,
            "title": phase_data["title"],
            "description": phase_data["description"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "estimated_hours": phase_data.get("estimated_hours", 0),
            "actual_hours": 0,
            "budget": phase_data.get("budget", 0),
            "actual_cost": 0,
            "status": phase_data.get("status", self.constants.PHASE_STATUS_NEW),
            "progress_percentage": 0,
            "created_date": datetime.now().isoformat(),
            "tasks": [],
            "milestones": [],
        }

        # In a real implementation, this would be stored in a project phases table
        # For now, we return the phase structure
        return phase_record

    def update_phase_progress(
        self, phase_id: str, progress: Union[int, float]
    ) -> Dict[str, Any]:
        """
        Update the progress percentage of a project phase.

        Args:
            phase_id: ID of the phase to update
            progress: Progress percentage (0-100)

        Returns:
            Updated phase information

        Raises:
            AutotaskValidationError: If progress value is invalid
        """
        if not 0 <= progress <= 100:
            raise AutotaskValidationError(
                "Progress percentage must be between 0 and 100"
            )

        # In a real implementation, this would update the phase record
        # For now, we'll return a mock updated phase
        updated_phase = {
            "phase_id": phase_id,
            "progress_percentage": progress,
            "updated_date": datetime.now().isoformat(),
            "status": (
                self.constants.PHASE_STATUS_COMPLETE
                if progress == 100
                else (
                    self.constants.PHASE_STATUS_IN_PROGRESS
                    if progress > 0
                    else self.constants.PHASE_STATUS_NEW
                )
            ),
        }

        return updated_phase

    def get_project_milestones(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all milestones for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of project milestones
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        # Get tasks that are marked as milestones or have milestone characteristics
        tasks = self.get_project_tasks(project_id)

        milestones = []
        for task in tasks:
            # Consider a task a milestone if it has zero duration or is marked as such
            estimated_hours = float(task.get("estimatedHours", 0))
            task_type = task.get("taskType", "")

            # Identify milestone tasks (typically have 0 hours or specific type)
            is_milestone = (
                estimated_hours == 0
                or "milestone" in task.get("title", "").lower()
                or task_type == "milestone"
            )

            if is_milestone:
                milestone = {
                    "milestone_id": task.get("id"),
                    "project_id": project_id,
                    "title": task.get("title"),
                    "description": task.get("description"),
                    "due_date": task.get("endDate"),
                    "completion_date": task.get("completedDateTime"),
                    "status": task.get("status"),
                    "is_completed": task.get("status") == 5,  # Complete status
                    "progress_percentage": float(task.get("percentComplete", 0)),
                    "dependencies": task.get("predecessors", []),
                    "priority": task.get("priority", 2),
                }
                milestones.append(milestone)

        # Sort by due date
        milestones.sort(key=lambda x: x.get("due_date", "9999-12-31"))

        return milestones

    def track_milestone_completion(self, milestone_id: int) -> Dict[str, Any]:
        """
        Track completion status of a specific milestone.

        Args:
            milestone_id: ID of the milestone (task ID)

        Returns:
            Dictionary with milestone completion information
        """
        # Get milestone task details
        milestone_task = self.client.query(
            "Tasks", filters=[QueryFilter(field="id", op="eq", value=milestone_id)]
        )

        if not milestone_task:
            raise AutotaskValidationError(f"Milestone {milestone_id} not found")

        task = milestone_task[0]
        project_id = task.get("projectID")

        # Get related tasks (successors)
        all_tasks = self.get_project_tasks(project_id) if project_id else []
        dependent_tasks = [
            t
            for t in all_tasks
            if str(milestone_id) in str(t.get("predecessors", "")).split(",")
        ]

        milestone_info = {
            "milestone_id": milestone_id,
            "project_id": project_id,
            "title": task.get("title"),
            "status": task.get("status"),
            "is_completed": task.get("status") == 5,
            "due_date": task.get("endDate"),
            "completion_date": task.get("completedDateTime"),
            "progress_percentage": float(task.get("percentComplete", 0)),
            "dependent_tasks": len(dependent_tasks),
            "blocked_tasks": [
                {"task_id": t.get("id"), "title": t.get("title")}
                for t in dependent_tasks
                if t.get("status") not in [2, 5]  # Not in progress or complete
            ],
            "impact_analysis": {
                "critical_path": False,  # Would be calculated from dependency analysis
                "delay_risk": "low",  # Based on current progress and due date
                "completion_probability": 0,
            },
            "tracking_date": datetime.now().isoformat(),
        }

        # Calculate completion probability based on progress and time remaining
        due_date = task.get("endDate")
        if due_date:
            try:
                due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                now = datetime.now()

                if due < now:
                    milestone_info["impact_analysis"]["delay_risk"] = "high"
                    milestone_info["impact_analysis"]["completion_probability"] = 0
                else:
                    days_remaining = (due - now).days
                    progress = milestone_info["progress_percentage"]

                    if days_remaining > 0 and progress > 0:
                        completion_rate = progress / max(
                            1, (now - due + timedelta(days=30)).days
                        )
                        probability = min(100, completion_rate * days_remaining)
                        milestone_info["impact_analysis"]["completion_probability"] = (
                            round(probability, 2)
                        )

            except (ValueError, TypeError):
                pass  # Invalid date format

        return milestone_info

    # ==================== PROFITABILITY ANALYSIS HELPERS ====================

    def calculate_gross_margin(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate gross margin for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with gross margin calculation
        """
        profitability = self.calculate_project_profitability(project_id)

        return {
            "project_id": project_id,
            "gross_margin": profitability["financial_summary"]["gross_margin"],
            "gross_margin_percent": profitability["financial_summary"][
                "gross_margin_percent"
            ],
            "revenue": profitability["financial_summary"]["revenue"],
            "total_costs": profitability["financial_summary"]["total_costs"],
            "calculation_date": datetime.now().isoformat(),
        }

    def get_profitability_report(self, project_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive profitability report for a project.

        Args:
            project_id: ID of the project

        Returns:
            Comprehensive profitability report
        """
        profitability = self.calculate_project_profitability(project_id)
        budget_status = self.get_budget_status(project_id)

        # Add additional analysis
        report = {
            **profitability,
            "budget_analysis": budget_status,
            "performance_indicators": {
                "budget_variance": 0,
                "schedule_variance": 0,
                "cost_performance_index": 0,
                "schedule_performance_index": 0,
            },
            "recommendations": [],
        }

        # Calculate performance indicators
        budgeted_cost = budget_status["budgets"]["total_budget"]
        actual_cost = profitability["financial_summary"]["total_costs"]

        if budgeted_cost > 0:
            budget_variance = budgeted_cost - actual_cost
            cost_performance_index = (
                budgeted_cost / actual_cost if actual_cost > 0 else 0
            )

            report["performance_indicators"]["budget_variance"] = budget_variance
            report["performance_indicators"]["cost_performance_index"] = round(
                cost_performance_index, 3
            )

        # Add recommendations based on analysis
        if profitability["status"] == "unprofitable":
            report["recommendations"].append(
                {
                    "priority": "high",
                    "category": "cost_control",
                    "message": "Project is unprofitable - review cost structure and pricing",
                }
            )
        elif profitability["status"] == "marginally_profitable":
            report["recommendations"].append(
                {
                    "priority": "medium",
                    "category": "optimization",
                    "message": "Low margins detected - consider optimizing resource allocation",
                }
            )

        return report

    def compare_actual_vs_estimated(self, project_id: int) -> Dict[str, Any]:
        """
        Compare actual project performance against original estimates.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with actual vs estimated comparison
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        budget_status = self.get_budget_status(project_id)

        comparison = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "comparison_date": datetime.now().isoformat(),
            "cost_comparison": {
                "estimated_total": budget_status["budgets"]["total_budget"],
                "actual_total": (
                    budget_status["actuals"]["actual_labor_cost"]
                    + budget_status["actuals"]["actual_expenses"]
                    + budget_status["actuals"]["actual_materials"]
                ),
                "variance_amount": 0,
                "variance_percent": 0,
            },
            "time_comparison": {
                "estimated_hours": budget_status["budgets"]["budget_hours"],
                "actual_hours": budget_status["actuals"]["actual_hours"],
                "variance_hours": 0,
                "variance_percent": 0,
            },
            "schedule_comparison": {
                "estimated_start": project.get("StartDate"),
                "actual_start": project.get("ActualStartDate"),
                "estimated_end": project.get("EndDate"),
                "projected_end": None,  # Would be calculated from current progress
                "schedule_variance_days": 0,
            },
            "accuracy_metrics": {
                "cost_estimation_accuracy": 0,
                "time_estimation_accuracy": 0,
                "overall_accuracy_score": 0,
            },
        }

        # Calculate cost variance
        estimated_cost = comparison["cost_comparison"]["estimated_total"]
        actual_cost = comparison["cost_comparison"]["actual_total"]

        if estimated_cost > 0:
            cost_variance = estimated_cost - actual_cost
            cost_variance_percent = (cost_variance / estimated_cost) * 100

            comparison["cost_comparison"]["variance_amount"] = cost_variance
            comparison["cost_comparison"]["variance_percent"] = round(
                cost_variance_percent, 2
            )

            # Accuracy score (100% = perfect estimate)
            accuracy = max(0, 100 - abs(cost_variance_percent))
            comparison["accuracy_metrics"]["cost_estimation_accuracy"] = round(
                accuracy, 2
            )

        # Calculate time variance
        estimated_hours = comparison["time_comparison"]["estimated_hours"]
        actual_hours = comparison["time_comparison"]["actual_hours"]

        if estimated_hours > 0:
            time_variance = estimated_hours - actual_hours
            time_variance_percent = (time_variance / estimated_hours) * 100

            comparison["time_comparison"]["variance_hours"] = time_variance
            comparison["time_comparison"]["variance_percent"] = round(
                time_variance_percent, 2
            )

            # Time accuracy score
            time_accuracy = max(0, 100 - abs(time_variance_percent))
            comparison["accuracy_metrics"]["time_estimation_accuracy"] = round(
                time_accuracy, 2
            )

        # Overall accuracy score
        cost_acc = comparison["accuracy_metrics"]["cost_estimation_accuracy"]
        time_acc = comparison["accuracy_metrics"]["time_estimation_accuracy"]
        overall_accuracy = (
            (cost_acc + time_acc) / 2 if (cost_acc > 0 or time_acc > 0) else 0
        )
        comparison["accuracy_metrics"]["overall_accuracy_score"] = round(
            overall_accuracy, 2
        )

        return comparison

    # ==================== PROJECT TEMPLATES ====================

    def create_from_template(
        self, template_id: str, project_data: Dict[str, Any]
    ) -> ProjectData:
        """
        Create a new project from a template.

        Args:
            template_id: ID of the template to use
            project_data: Project-specific data to override template defaults:
                - project_name: Name of the new project
                - account_id: Account ID for the project
                - start_date: Project start date
                - end_date: Project end date
                - project_manager_id: Project manager resource ID

        Returns:
            Created project data

        Raises:
            AutotaskValidationError: If template not found or data is invalid
        """
        # In a real implementation, this would load template from database
        # For now, we'll use a mock template structure
        template = self._get_project_template(template_id)

        if not template:
            raise AutotaskValidationError(f"Project template {template_id} not found")

        # Merge template with project-specific data
        new_project_data = {**template["project_defaults"], **project_data}

        # Create the project
        project = self.create_project(**new_project_data)

        # Create phases from template
        if template.get("phases"):
            for i, phase_name in enumerate(template["phases"]):
                phase_data = {
                    "title": phase_name,
                    "description": f"Phase {i + 1}: {phase_name}",
                    "start_date": project_data.get(
                        "start_date", datetime.now().isoformat()
                    ),
                    "end_date": project_data.get(
                        "end_date", (datetime.now() + timedelta(days=30)).isoformat()
                    ),
                }
                self.add_project_phase(project["id"], phase_data)

        return project

    def save_as_template(
        self,
        project_id: int,
        template_name: str,
        template_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save an existing project as a template.

        Args:
            project_id: ID of the project to save as template
            template_name: Name for the template
            template_description: Optional template description

        Returns:
            Created template information

        Raises:
            AutotaskValidationError: If project not found
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        # Get project structure
        tasks = self.get_project_tasks(project_id)
        milestones = self.get_project_milestones(project_id)

        template = {
            "template_id": f"template_{datetime.now().timestamp()}",
            "name": template_name,
            "description": template_description
            or f"Template created from project {project.get('ProjectName')}",
            "created_from_project": project_id,
            "created_date": datetime.now().isoformat(),
            "project_defaults": {
                "project_type": project.get("Type"),
                "status": self.constants.STATUS_NEW,
                "priority": project.get("Priority"),
                "estimated_time": project.get("EstimatedTime"),
                "project_cost": project.get("ProjectCost"),
                "labor_cost": project.get("LaborCost"),
                "expense_cost": project.get("ExpenseCost"),
                "material_cost": project.get("MaterialCost"),
            },
            "phases": [],  # Would be populated from project phases
            "task_templates": [
                {
                    "title": task.get("title"),
                    "description": task.get("description"),
                    "estimated_hours": task.get("estimatedHours"),
                    "priority": task.get("priority"),
                    "dependencies": task.get("predecessors", []),
                }
                for task in tasks
            ],
            "milestone_templates": [
                {
                    "title": milestone.get("title"),
                    "description": milestone.get("description"),
                    "dependencies": milestone.get("dependencies", []),
                }
                for milestone in milestones
            ],
        }

        # In a real implementation, this would be stored in a templates table
        return template

    def get_project_templates(self) -> List[Dict[str, Any]]:
        """
        Get all available project templates.

        Returns:
            List of project templates
        """
        # In a real implementation, this would query the templates table
        # For now, return mock templates
        mock_templates = [
            {
                "template_id": "web_development",
                "name": "Web Development Project",
                "description": "Standard template for web development projects",
                "phases": [
                    "Planning",
                    "Design",
                    "Development",
                    "Testing",
                    "Deployment",
                ],
                "estimated_duration_days": 90,
                "typical_team_size": 5,
            },
            {
                "template_id": "infrastructure_upgrade",
                "name": "Infrastructure Upgrade",
                "description": "Template for IT infrastructure upgrade projects",
                "phases": [
                    "Assessment",
                    "Planning",
                    "Procurement",
                    "Implementation",
                    "Testing",
                ],
                "estimated_duration_days": 120,
                "typical_team_size": 3,
            },
            {
                "template_id": "software_implementation",
                "name": "Software Implementation",
                "description": "Template for software implementation projects",
                "phases": [
                    "Requirements",
                    "Configuration",
                    "Data Migration",
                    "Training",
                    "Go-Live",
                ],
                "estimated_duration_days": 180,
                "typical_team_size": 4,
            },
        ]

        return mock_templates

    def _get_project_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Internal method to get a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Template data or None if not found
        """
        templates = self.get_project_templates()
        for template in templates:
            if template["template_id"] == template_id:
                # Add detailed template data
                template["project_defaults"] = {
                    "project_type": self.constants.PROJECT_TYPE_TIME_MATERIALS,
                    "status": self.constants.STATUS_NEW,
                    "priority": self.constants.PRIORITY_MEDIUM,
                }
                return template
        return None

    # ==================== GANTT CHART AND DEPENDENCY MANAGEMENT ====================

    def get_gantt_data(self, project_id: int) -> Dict[str, Any]:
        """
        Get Gantt chart data for a project including tasks, dependencies, and timeline.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with Gantt chart data structure
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        tasks = self.get_project_tasks(project_id)
        milestones = self.get_project_milestones(project_id)

        # Process tasks for Gantt display
        gantt_tasks = []
        for task in tasks:
            gantt_task = {
                "id": task.get("id"),
                "name": task.get("title"),
                "start_date": task.get("startDate"),
                "end_date": task.get("endDate"),
                "duration_days": self._calculate_task_duration(
                    task.get("startDate"), task.get("endDate")
                ),
                "progress": float(task.get("percentComplete", 0)) / 100,
                "assigned_resource": task.get("assignedResourceID"),
                "estimated_hours": float(task.get("estimatedHours", 0)),
                "dependencies": self._parse_dependencies(task.get("predecessors", "")),
                "is_milestone": False,
                "priority": task.get("priority", 2),
                "status": task.get("status"),
                "parent_id": task.get("phaseID"),
            }
            gantt_tasks.append(gantt_task)

        # Process milestones for Gantt display
        for milestone in milestones:
            gantt_milestone = {
                "id": f"milestone_{milestone.get('milestone_id')}",
                "name": milestone.get("title"),
                "start_date": milestone.get("due_date"),
                "end_date": milestone.get("due_date"),
                "duration_days": 0,
                "progress": milestone.get("progress_percentage", 0) / 100,
                "assigned_resource": None,
                "estimated_hours": 0,
                "dependencies": milestone.get("dependencies", []),
                "is_milestone": True,
                "priority": milestone.get("priority", 2),
                "status": milestone.get("status"),
                "parent_id": None,
            }
            gantt_tasks.append(gantt_milestone)

        # Calculate project timeline
        project_start = project.get("StartDate")
        project_end = project.get("EndDate")

        # If no dates set, calculate from tasks
        if not project_start or not project_end:
            task_dates = [
                task.get("start_date")
                for task in gantt_tasks
                if task.get("start_date") and not task["is_milestone"]
            ]
            end_dates = [
                task.get("end_date")
                for task in gantt_tasks
                if task.get("end_date") and not task["is_milestone"]
            ]

            if task_dates:
                project_start = min(task_dates)
            if end_dates:
                project_end = max(end_dates)

        gantt_data = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "project_start": project_start,
            "project_end": project_end,
            "project_duration_days": self._calculate_task_duration(
                project_start, project_end
            ),
            "tasks": gantt_tasks,
            "critical_path": [],  # Will be calculated
            "resource_assignments": self._get_resource_assignments(gantt_tasks),
            "timeline_metadata": {
                "total_tasks": len([t for t in gantt_tasks if not t["is_milestone"]]),
                "total_milestones": len([t for t in gantt_tasks if t["is_milestone"]]),
                "completed_tasks": len(
                    [t for t in gantt_tasks if t["progress"] >= 1.0]
                ),
                "overdue_tasks": len(
                    [t for t in gantt_tasks if self._is_task_overdue(t)]
                ),
                "generated_date": datetime.now().isoformat(),
            },
        }

        # Calculate critical path
        gantt_data["critical_path"] = self.calculate_critical_path(project_id)

        return gantt_data

    def add_task_dependency(
        self, task_id: int, depends_on_id: int, dependency_type: str = "finish_to_start"
    ) -> Dict[str, Any]:
        """
        Add a dependency relationship between two tasks.

        Args:
            task_id: ID of the dependent task
            depends_on_id: ID of the task that must be completed first
            dependency_type: Type of dependency:
                - finish_to_start: Dependent task starts when predecessor finishes
                - start_to_start: Both tasks start together
                - finish_to_finish: Both tasks finish together
                - start_to_finish: Dependent task finishes when predecessor starts

        Returns:
            Dictionary with dependency information

        Raises:
            AutotaskValidationError: If tasks not found or circular dependency detected
        """
        # Validate dependency type
        valid_types = [
            "finish_to_start",
            "start_to_start",
            "finish_to_finish",
            "start_to_finish",
        ]
        if dependency_type not in valid_types:
            raise AutotaskValidationError(f"Invalid dependency type: {dependency_type}")

        # Check if tasks exist
        task = self.client.query(
            "Tasks", filters=[QueryFilter(field="id", op="eq", value=task_id)]
        )
        predecessor = self.client.query(
            "Tasks", filters=[QueryFilter(field="id", op="eq", value=depends_on_id)]
        )

        if not task:
            raise AutotaskValidationError(f"Task {task_id} not found")
        if not predecessor:
            raise AutotaskValidationError(f"Predecessor task {depends_on_id} not found")

        # Check for circular dependencies
        if self._has_circular_dependency(task_id, depends_on_id):
            raise AutotaskValidationError(
                f"Adding dependency would create circular reference between tasks {task_id} and {depends_on_id}"
            )

        # Update task with new dependency
        current_predecessors = task[0].get("predecessors", "")
        predecessor_list = [
            p.strip() for p in current_predecessors.split(",") if p.strip()
        ]

        if str(depends_on_id) not in predecessor_list:
            predecessor_list.append(str(depends_on_id))
            new_predecessors = ",".join(predecessor_list)

            # Update the task
            self.client.update("Tasks", task_id, {"predecessors": new_predecessors})

        dependency_info = {
            "task_id": task_id,
            "depends_on_id": depends_on_id,
            "dependency_type": dependency_type,
            "created_date": datetime.now().isoformat(),
            "status": "active",
        }

        return dependency_info

    def calculate_critical_path(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Calculate the critical path for a project using CPM (Critical Path Method).

        Args:
            project_id: ID of the project

        Returns:
            List of tasks on the critical path with timing information
        """
        tasks = self.get_project_tasks(project_id)

        if not tasks:
            return []

        # Build task network
        task_network = {}
        for task in tasks:
            task_id = task.get("id")
            predecessors = self._parse_dependencies(task.get("predecessors", ""))
            duration = (
                float(task.get("estimatedHours", 0)) / 8
            )  # Convert to days (8 hours/day)

            task_network[task_id] = {
                "id": task_id,
                "name": task.get("title"),
                "duration": max(1, duration),  # Minimum 1 day
                "predecessors": predecessors,
                "successors": [],
                "early_start": 0,
                "early_finish": 0,
                "late_start": 0,
                "late_finish": 0,
                "total_float": 0,
                "is_critical": False,
            }

        # Build successor relationships
        for task_id, task_data in task_network.items():
            for pred_id in task_data["predecessors"]:
                if pred_id in task_network:
                    task_network[pred_id]["successors"].append(task_id)

        # Forward pass - calculate early start and early finish
        def forward_pass():
            # Need to process in topological order
            processed = set()

            def process_task(task_id):
                if task_id in processed or task_id not in task_network:
                    return

                task_data = task_network[task_id]

                # Process all predecessors first
                for pred_id in task_data["predecessors"]:
                    if pred_id in task_network:
                        process_task(pred_id)

                # Calculate early start
                if not task_data["predecessors"]:
                    # Start task
                    task_data["early_start"] = 0
                else:
                    # Calculate based on predecessors
                    predecessor_finishes = []
                    for pred_id in task_data["predecessors"]:
                        if pred_id in task_network:
                            predecessor_finishes.append(
                                task_network[pred_id]["early_finish"]
                            )

                    task_data["early_start"] = (
                        max(predecessor_finishes) if predecessor_finishes else 0
                    )

                task_data["early_finish"] = (
                    task_data["early_start"] + task_data["duration"]
                )
                processed.add(task_id)

            # Process all tasks
            for task_id in task_network.keys():
                process_task(task_id)

        # Backward pass - calculate late start and late finish
        def backward_pass():
            # Find project end time
            project_end_time = max(
                task_data["early_finish"] for task_data in task_network.values()
            )

            processed = set()

            def process_task_backward(task_id):
                if task_id in processed or task_id not in task_network:
                    return

                task_data = task_network[task_id]

                # Process all successors first
                for succ_id in task_data["successors"]:
                    if succ_id in task_network:
                        process_task_backward(succ_id)

                # Calculate late finish
                if not task_data["successors"]:
                    # End task
                    task_data["late_finish"] = project_end_time
                else:
                    # Calculate based on successors
                    successor_starts = []
                    for succ_id in task_data["successors"]:
                        if succ_id in task_network:
                            successor_starts.append(task_network[succ_id]["late_start"])

                    task_data["late_finish"] = (
                        min(successor_starts) if successor_starts else project_end_time
                    )

                task_data["late_start"] = (
                    task_data["late_finish"] - task_data["duration"]
                )
                processed.add(task_id)

            # Process all tasks
            for task_id in task_network.keys():
                process_task_backward(task_id)

        # Perform forward and backward passes
        forward_pass()
        backward_pass()

        # Calculate float and identify critical path
        critical_tasks = []
        for task_id, task_data in task_network.items():
            task_data["total_float"] = (
                task_data["late_start"] - task_data["early_start"]
            )
            task_data["is_critical"] = (
                abs(task_data["total_float"]) < 0.1
            )  # Consider floating point precision

            if task_data["is_critical"]:
                critical_tasks.append(
                    {
                        "task_id": task_id,
                        "name": task_data["name"],
                        "duration": task_data["duration"],
                        "early_start": task_data["early_start"],
                        "early_finish": task_data["early_finish"],
                        "late_start": task_data["late_start"],
                        "late_finish": task_data["late_finish"],
                        "total_float": task_data["total_float"],
                    }
                )

        # Sort by early start time
        critical_tasks.sort(key=lambda x: x["early_start"])

        return critical_tasks

    def _calculate_task_duration(self, start_date: str, end_date: str) -> int:
        """Calculate duration in days between two dates."""
        if not start_date or not end_date:
            return 0

        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            return max(1, (end - start).days)
        except (ValueError, TypeError):
            return 0

    def _parse_dependencies(self, predecessors_str: str) -> List[int]:
        """Parse predecessor string into list of task IDs."""
        if not predecessors_str:
            return []

        dependencies = []
        for pred in predecessors_str.split(","):
            pred = pred.strip()
            if pred.isdigit():
                dependencies.append(int(pred))

        return dependencies

    def _get_resource_assignments(
        self, gantt_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get resource assignment summary from Gantt tasks."""
        assignments = {}

        for task in gantt_tasks:
            resource_id = task.get("assigned_resource")
            if resource_id and not task["is_milestone"]:
                if resource_id not in assignments:
                    assignments[resource_id] = {
                        "resource_id": resource_id,
                        "tasks": [],
                        "total_hours": 0,
                        "workload_days": [],
                    }

                assignments[resource_id]["tasks"].append(task["id"])
                assignments[resource_id]["total_hours"] += task.get(
                    "estimated_hours", 0
                )

                # Calculate workload timeline (simplified)
                if task.get("start_date") and task.get("end_date"):
                    assignments[resource_id]["workload_days"].append(
                        {
                            "start": task["start_date"],
                            "end": task["end_date"],
                            "task_name": task["name"],
                        }
                    )

        return assignments

    def _is_task_overdue(self, task: Dict[str, Any]) -> bool:
        """Check if a task is overdue."""
        if task["is_milestone"]:
            return False

        end_date = task.get("end_date")
        progress = task.get("progress", 0)

        if not end_date or progress >= 1.0:
            return False

        try:
            due = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            return due < datetime.now()
        except (ValueError, TypeError):
            return False

    def _has_circular_dependency(self, task_id: int, depends_on_id: int) -> bool:
        """Check if adding a dependency would create a circular reference."""
        # Simple circular dependency check - in a real implementation this would be more thorough
        # Check if depends_on_id already depends on task_id (direct circular reference)
        depends_on_task = self.client.query(
            "Tasks", filters=[QueryFilter(field="id", op="eq", value=depends_on_id)]
        )

        if depends_on_task:
            predecessors = depends_on_task[0].get("predecessors", "")
            predecessor_ids = [
                int(p.strip()) for p in predecessors.split(",") if p.strip().isdigit()
            ]
            return task_id in predecessor_ids

        return False

    # ==================== VALIDATION AND HELPER METHODS ====================

    def validate_project_data(self, project_data: Dict[str, Any]) -> List[str]:
        """
        Validate project data for common issues.

        Args:
            project_data: Project data to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Required fields
        required_fields = ["ProjectName", "AccountID"]
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                errors.append(f"Missing required field: {field}")

        # Validate dates
        start_date = project_data.get("StartDate")
        end_date = project_data.get("EndDate")

        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

                if end <= start:
                    errors.append("End date must be after start date")
            except (ValueError, TypeError):
                errors.append("Invalid date format")

        # Validate budget values
        budget_fields = [
            "ProjectCost",
            "LaborCost",
            "ExpenseCost",
            "MaterialCost",
            "EstimatedTime",
        ]
        for field in budget_fields:
            if field in project_data:
                value = project_data[field]
                if value is not None and (
                    not isinstance(value, (int, float)) or value < 0
                ):
                    errors.append(f"Invalid {field}: must be a non-negative number")

        # Validate project type
        project_type = project_data.get("Type")
        if project_type and project_type not in [1, 2, 3, 4, 5]:
            errors.append("Invalid project type")

        # Validate status
        status = project_data.get("Status")
        if status and status not in [1, 2, 3, 4, 5, 7, 8]:
            errors.append("Invalid project status")

        return errors

    def get_project_health_score(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate overall project health score based on multiple factors.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with health score and contributing factors
        """
        project = self.get_by_id(project_id)
        if not project:
            raise AutotaskValidationError(f"Project {project_id} not found")

        budget_status = self.get_budget_status(project_id)
        allocation_data = self.get_resource_allocation(project_id)
        profitability = self.calculate_project_profitability(project_id)

        # Health factors (each scored 0-100)
        factors = {
            "budget_health": 0,
            "schedule_health": 0,
            "resource_health": 0,
            "profitability_health": 0,
            "progress_health": 0,
        }

        # Budget health (based on budget utilization)
        budget_utilization = budget_status["utilization"].get("total_budget", 0)
        if budget_utilization <= 80:
            factors["budget_health"] = 100
        elif budget_utilization <= 100:
            factors["budget_health"] = 80
        elif budget_utilization <= 120:
            factors["budget_health"] = 50
        else:
            factors["budget_health"] = 20

        # Schedule health (based on current date vs planned dates)
        start_date = project.get("StartDate")
        end_date = project.get("EndDate")

        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                now = datetime.now()

                if now < start:
                    factors["schedule_health"] = 100  # Not started yet
                elif now > end:
                    factors["schedule_health"] = 20  # Overdue
                else:
                    # Calculate based on timeline position
                    total_days = (end - start).days
                    elapsed_days = (now - start).days

                    if total_days > 0:
                        timeline_progress = elapsed_days / total_days
                        # Good health if we're on track
                        factors["schedule_health"] = max(
                            20, 100 - abs(timeline_progress - 0.5) * 100
                        )
            except (ValueError, TypeError):
                factors["schedule_health"] = 50  # Unknown

        # Resource health (based on allocation efficiency)
        if allocation_data["resources_allocated"] > 0:
            avg_utilization = (
                sum(r["utilization"] for r in allocation_data["resource_breakdown"])
                / allocation_data["resources_allocated"]
            )

            # Optimal utilization is around 70-80%
            if 70 <= avg_utilization <= 80:
                factors["resource_health"] = 100
            elif 50 <= avg_utilization <= 90:
                factors["resource_health"] = 80
            else:
                factors["resource_health"] = 50
        else:
            factors["resource_health"] = 30  # No resources allocated

        # Profitability health
        profit_status = profitability["status"]
        profit_margin = profitability["financial_summary"]["gross_margin_percent"]

        if profit_status == "highly_profitable":
            factors["profitability_health"] = 100
        elif profit_status == "profitable":
            factors["profitability_health"] = 80
        elif profit_status == "marginally_profitable":
            factors["profitability_health"] = 60
        else:
            factors["profitability_health"] = 20

        # Progress health (based on task completion)
        tasks = self.get_project_tasks(project_id)
        if tasks:
            avg_progress = sum(
                float(task.get("percentComplete", 0)) for task in tasks
            ) / len(tasks)
            factors["progress_health"] = min(
                100, avg_progress + 20
            )  # Bonus for any progress
        else:
            factors["progress_health"] = 50

        # Calculate overall health score (weighted average)
        weights = {
            "budget_health": 0.25,
            "schedule_health": 0.25,
            "resource_health": 0.20,
            "profitability_health": 0.20,
            "progress_health": 0.10,
        }

        overall_score = sum(factors[factor] * weights[factor] for factor in factors)

        # Determine health status
        if overall_score >= 80:
            health_status = "excellent"
        elif overall_score >= 60:
            health_status = "good"
        elif overall_score >= 40:
            health_status = "fair"
        else:
            health_status = "poor"

        return {
            "project_id": project_id,
            "overall_score": round(overall_score, 2),
            "health_status": health_status,
            "factor_scores": factors,
            "recommendations": self._generate_health_recommendations(factors),
            "assessment_date": datetime.now().isoformat(),
        }

    def _generate_health_recommendations(
        self, factors: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on health factor scores."""
        recommendations = []

        for factor, score in factors.items():
            if score < 50:
                if factor == "budget_health":
                    recommendations.append(
                        {
                            "category": "budget",
                            "priority": "high",
                            "message": "Budget is over-utilized. Review costs and consider scope adjustments.",
                        }
                    )
                elif factor == "schedule_health":
                    recommendations.append(
                        {
                            "category": "schedule",
                            "priority": "high",
                            "message": "Project is behind schedule. Consider resource reallocation or scope reduction.",
                        }
                    )
                elif factor == "resource_health":
                    recommendations.append(
                        {
                            "category": "resources",
                            "priority": "medium",
                            "message": "Resource allocation needs optimization. Review workload distribution.",
                        }
                    )
                elif factor == "profitability_health":
                    recommendations.append(
                        {
                            "category": "profitability",
                            "priority": "high",
                            "message": "Project profitability is at risk. Review pricing and cost structure.",
                        }
                    )
                elif factor == "progress_health":
                    recommendations.append(
                        {
                            "category": "progress",
                            "priority": "medium",
                            "message": "Project progress is slow. Identify and address blocking factors.",
                        }
                    )

        return recommendations
