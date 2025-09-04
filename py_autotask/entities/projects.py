"""
Projects entity for Autotask API operations.

This module provides comprehensive project management functionality for Professional
Services Automation (PSA), including project lifecycle management, resource allocation,
budget tracking, timeline management, and integration with other Autotask entities.
"""

from datetime import datetime, timedelta
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union

from ..types import EntityDict, ProjectData, QueryFilter
from .base import BaseEntity


class ProjectStatus(IntEnum):
    """Project status constants."""

    NEW = 1
    IN_PROGRESS = 2
    ON_HOLD = 3
    WAITING = 4
    COMPLETE = 5
    CANCELLED = 7


class ProjectType(IntEnum):
    """Project type constants."""

    FIXED_PRICE = 1
    TIME_AND_MATERIALS = 2
    RETAINER = 3
    RECURRING_SERVICE = 4
    BLOCK_HOURS = 5


class ProjectLineItemType(IntEnum):
    """Project line item type constants."""

    LABOR = 1
    EXPENSE = 2
    MATERIAL = 3
    MILESTONE = 4


class ProjectResourceRole(IntEnum):
    """Project resource role constants."""

    PROJECT_MANAGER = 1
    TEAM_MEMBER = 2
    STAKEHOLDER = 3
    OBSERVER = 4


class BillingCodeType(IntEnum):
    """Billing code type constants."""

    LABOR = 1
    EXPENSE = 2
    MATERIAL = 3


class ProjectsEntity(BaseEntity):
    """
    Handles all Project-related operations for the Autotask API.

    This entity provides comprehensive Professional Services Automation (PSA) functionality
    including project lifecycle management, resource allocation, budget tracking, timeline
    management, analytics, and integration with other Autotask entities.

    Key features:
    - Project creation with templates and hierarchy support
    - Resource allocation and capacity planning
    - Budget and cost tracking
    - Timeline and milestone management
    - Analytics and reporting
    - Integration with tasks, tickets, time entries, and expenses
    """

    def __init__(self, client, entity_name: str = "Projects"):
        super().__init__(client, entity_name)

    # =====================================================================================
    # PROJECT LIFECYCLE MANAGEMENT
    # =====================================================================================

    def create_project(
        self,
        project_name: str,
        account_id: int,
        project_type: Union[int, ProjectType] = ProjectType.FIXED_PRICE,
        status: Union[int, ProjectStatus] = ProjectStatus.NEW,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
        project_manager_id: Optional[int] = None,
        parent_project_id: Optional[int] = None,
        budget_hours: Optional[float] = None,
        budget_cost: Optional[float] = None,
        estimated_hours: Optional[float] = None,
        contract_id: Optional[int] = None,
        business_division_subdivision_id: Optional[int] = None,
        **kwargs,
    ) -> ProjectData:
        """
        Create a new project with comprehensive configuration options.

        Args:
            project_name: Name of the project
            account_id: ID of the associated account/company
            project_type: Type of project (ProjectType enum or int)
            status: Project status (ProjectStatus enum or int)
            start_date: Project start date (ISO format)
            end_date: Project end date (ISO format)
            description: Project description
            project_manager_id: ID of the project manager resource
            parent_project_id: ID of parent project (for sub-projects)
            budget_hours: Budgeted hours for the project
            budget_cost: Budgeted cost for the project
            estimated_hours: Estimated hours for completion
            contract_id: Associated contract ID
            business_division_subdivision_id: Business division/subdivision ID
            **kwargs: Additional project fields

        Returns:
            Created project data

        Raises:
            ValueError: If required fields are invalid
        """
        # Convert enums to int values
        if isinstance(project_type, ProjectType):
            project_type = project_type.value
        if isinstance(status, ProjectStatus):
            status = status.value

        # Validate required fields
        if not project_name.strip():
            raise ValueError("Project name cannot be empty")
        if account_id <= 0:
            raise ValueError("Account ID must be positive")

        project_data = {
            "ProjectName": project_name,
            "AccountID": account_id,
            "Type": project_type,
            "Status": status,
            **kwargs,
        }

        # Add optional fields if provided
        optional_fields = {
            "StartDate": start_date,
            "EndDate": end_date,
            "Description": description,
            "ProjectManagerResourceID": project_manager_id,
            "ParentProjectID": parent_project_id,
            "BudgetHours": budget_hours,
            "BudgetCost": budget_cost,
            "EstimatedHours": estimated_hours,
            "ContractID": contract_id,
            "BusinessDivisionSubdivisionID": business_division_subdivision_id,
        }

        for field_name, field_value in optional_fields.items():
            if field_value is not None:
                project_data[field_name] = field_value

        return self.create(project_data)

    def create_project_from_template(
        self,
        template_project_id: int,
        project_name: str,
        account_id: int,
        start_date: Optional[str] = None,
        project_manager_id: Optional[int] = None,
        copy_tasks: bool = True,
        copy_phases: bool = True,
        copy_resources: bool = False,
        **kwargs,
    ) -> ProjectData:
        """
        Create a new project based on an existing project template.

        Args:
            template_project_id: ID of the template project to copy
            project_name: Name for the new project
            account_id: ID of the associated account/company
            start_date: Start date for the new project
            project_manager_id: Project manager for the new project
            copy_tasks: Whether to copy tasks from template
            copy_phases: Whether to copy phases from template
            copy_resources: Whether to copy resource assignments from template
            **kwargs: Additional project fields

        Returns:
            Created project data
        """
        # Get template project data
        template_project = self.get_by_id(template_project_id)
        if not template_project:
            raise ValueError(f"Template project {template_project_id} not found")

        # Create project data based on template
        project_data = {
            "ProjectName": project_name,
            "AccountID": account_id,
            "Type": template_project.get("Type"),
            "Status": ProjectStatus.NEW.value,
            "Description": template_project.get("Description"),
            "EstimatedHours": template_project.get("EstimatedHours"),
            "BudgetHours": template_project.get("BudgetHours"),
            "BudgetCost": template_project.get("BudgetCost"),
            **kwargs,
        }

        # Override with provided values
        if start_date:
            project_data["StartDate"] = start_date
        if project_manager_id:
            project_data["ProjectManagerResourceID"] = project_manager_id

        # Create the project
        new_project = self.create(project_data)

        # TODO: Implement task, phase, and resource copying
        # This would require additional API calls to copy related entities

        return new_project

    def duplicate_project(
        self,
        project_id: int,
        new_project_name: str,
        new_account_id: Optional[int] = None,
        include_tasks: bool = True,
        include_resources: bool = False,
        include_time_entries: bool = False,
        **kwargs,
    ) -> ProjectData:
        """
        Duplicate an existing project with all its components.

        Args:
            project_id: ID of project to duplicate
            new_project_name: Name for the duplicated project
            new_account_id: Account ID for new project (defaults to original)
            include_tasks: Whether to duplicate tasks
            include_resources: Whether to duplicate resource assignments
            include_time_entries: Whether to duplicate time entries
            **kwargs: Additional fields to override

        Returns:
            Duplicated project data
        """
        original_project = self.get_by_id(project_id)
        if not original_project:
            raise ValueError(f"Project {project_id} not found")

        # Prepare project data for duplication
        project_data = {
            key: value
            for key, value in original_project.items()
            if key
            not in ["id", "ID", "CreateDate", "CreatedDateTime", "LastModifiedDateTime"]
        }

        # Override with new values
        project_data.update(
            {
                "ProjectName": new_project_name,
                "Status": ProjectStatus.NEW.value,
                **kwargs,
            }
        )

        if new_account_id:
            project_data["AccountID"] = new_account_id

        # Remove timestamps and IDs that shouldn't be duplicated
        fields_to_remove = [
            "StartDate",
            "EndDate",
            "ActualHours",
            "ActualCost",
            "CompletedDateTime",
            "CompletedPercentage",
        ]
        for field in fields_to_remove:
            project_data.pop(field, None)

        return self.create(project_data)

    def update_project_status(
        self,
        project_id: int,
        status: Union[int, ProjectStatus],
        status_notes: Optional[str] = None,
        completion_date: Optional[str] = None,
    ) -> ProjectData:
        """
        Update a project's status with optional notes and completion tracking.

        Args:
            project_id: ID of project to update
            status: New status (ProjectStatus enum or int)
            status_notes: Optional notes about the status change
            completion_date: Completion date for completed projects

        Returns:
            Updated project data
        """
        if isinstance(status, ProjectStatus):
            status = status.value

        update_data = {"Status": status}

        if status_notes:
            update_data["StatusDetail"] = status_notes

        # Auto-set completion date for completed projects
        if status == ProjectStatus.COMPLETE.value:
            if completion_date:
                update_data["EndDate"] = completion_date
            else:
                update_data["EndDate"] = datetime.now().isoformat()

        return self.update_by_id(project_id, update_data)

    def start_project(
        self,
        project_id: int,
        actual_start_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ProjectData:
        """
        Start a project (change status to In Progress).

        Args:
            project_id: ID of project to start
            actual_start_date: Actual start date (defaults to now)
            notes: Optional notes about project start

        Returns:
            Updated project data
        """
        update_data = {
            "Status": ProjectStatus.IN_PROGRESS.value,
            "ActualStartDate": actual_start_date or datetime.now().isoformat(),
        }

        if notes:
            update_data["StatusDetail"] = notes

        return self.update_by_id(project_id, update_data)

    def pause_project(
        self,
        project_id: int,
        reason: Optional[str] = None,
    ) -> ProjectData:
        """
        Pause a project (change status to On Hold).

        Args:
            project_id: ID of project to pause
            reason: Optional reason for pausing

        Returns:
            Updated project data
        """
        update_data = {"Status": ProjectStatus.ON_HOLD.value}

        if reason:
            update_data["StatusDetail"] = reason

        return self.update_by_id(project_id, update_data)

    def complete_project(
        self,
        project_id: int,
        completion_date: Optional[str] = None,
        completion_notes: Optional[str] = None,
        actual_hours: Optional[float] = None,
        actual_cost: Optional[float] = None,
    ) -> ProjectData:
        """
        Complete a project with comprehensive completion tracking.

        Args:
            project_id: ID of project to complete
            completion_date: Project completion date (defaults to now)
            completion_notes: Optional completion notes
            actual_hours: Actual hours worked on project
            actual_cost: Actual cost of project

        Returns:
            Updated project data
        """
        update_data = {
            "Status": ProjectStatus.COMPLETE.value,
            "EndDate": completion_date or datetime.now().isoformat(),
            "CompletedPercentage": 100,
        }

        if completion_notes:
            update_data["StatusDetail"] = completion_notes
        if actual_hours is not None:
            update_data["ActualHours"] = actual_hours
        if actual_cost is not None:
            update_data["ActualCost"] = actual_cost

        return self.update_by_id(project_id, update_data)

    def cancel_project(
        self,
        project_id: int,
        cancellation_reason: Optional[str] = None,
    ) -> ProjectData:
        """
        Cancel a project.

        Args:
            project_id: ID of project to cancel
            cancellation_reason: Optional reason for cancellation

        Returns:
            Updated project data
        """
        update_data = {"Status": ProjectStatus.CANCELLED.value}

        if cancellation_reason:
            update_data["StatusDetail"] = cancellation_reason

        return self.update_by_id(project_id, update_data)

    # =====================================================================================
    # PROJECT QUERYING AND FILTERING
    # =====================================================================================

    def get_projects_by_account(
        self,
        account_id: int,
        status_filter: Optional[Union[str, List[Union[int, ProjectStatus]]]] = None,
        include_sub_projects: bool = True,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get all projects for a specific account with advanced filtering.

        Args:
            account_id: Account ID to filter by
            status_filter: Status filter (string shortcut or list of statuses)
            include_sub_projects: Whether to include sub-projects
            limit: Maximum number of projects to return

        Returns:
            List of projects for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        if status_filter:
            if isinstance(status_filter, str):
                status_map = {
                    "active": [
                        ProjectStatus.NEW,
                        ProjectStatus.IN_PROGRESS,
                        ProjectStatus.WAITING,
                    ],
                    "completed": [ProjectStatus.COMPLETE],
                    "new": [ProjectStatus.NEW],
                    "in_progress": [ProjectStatus.IN_PROGRESS],
                    "on_hold": [ProjectStatus.ON_HOLD],
                    "cancelled": [ProjectStatus.CANCELLED],
                }

                if status_filter.lower() in status_map:
                    status_list = [s.value for s in status_map[status_filter.lower()]]
                else:
                    raise ValueError(f"Invalid status filter: {status_filter}")
            else:
                # Convert ProjectStatus enums to int values
                status_list = [
                    s.value if isinstance(s, ProjectStatus) else s
                    for s in status_filter
                ]

            if len(status_list) == 1:
                filters.append(
                    QueryFilter(field="Status", op="eq", value=status_list[0])
                )
            else:
                filters.append(QueryFilter(field="Status", op="in", value=status_list))

        # Optionally exclude sub-projects
        if not include_sub_projects:
            filters.append(QueryFilter(field="ParentProjectID", op="isNull"))

        return self.query(filters=filters, max_records=limit)

    def get_projects_by_manager(
        self,
        manager_id: int,
        status_filter: Optional[Union[str, List[Union[int, ProjectStatus]]]] = None,
        include_sub_projects: bool = True,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get projects managed by a specific resource with advanced filtering.

        Args:
            manager_id: Project manager resource ID
            status_filter: Status filter (string shortcut or list of statuses)
            include_sub_projects: Whether to include sub-projects
            limit: Maximum number of projects to return

        Returns:
            List of projects managed by the resource
        """
        filters = [
            QueryFilter(field="ProjectManagerResourceID", op="eq", value=manager_id)
        ]

        # Apply status filter
        if status_filter:
            if isinstance(status_filter, str):
                if status_filter.lower() == "active":
                    active_statuses = [
                        ProjectStatus.NEW.value,
                        ProjectStatus.IN_PROGRESS.value,
                        ProjectStatus.WAITING.value,
                    ]
                    filters.append(
                        QueryFilter(field="Status", op="in", value=active_statuses)
                    )
                elif status_filter.lower() == "completed":
                    filters.append(
                        QueryFilter(
                            field="Status", op="eq", value=ProjectStatus.COMPLETE.value
                        )
                    )
            else:
                status_list = [
                    s.value if isinstance(s, ProjectStatus) else s
                    for s in status_filter
                ]
                filters.append(QueryFilter(field="Status", op="in", value=status_list))

        # Optionally exclude sub-projects
        if not include_sub_projects:
            filters.append(QueryFilter(field="ParentProjectID", op="isNull"))

        return self.query(filters=filters, max_records=limit)

    def get_projects_by_status(
        self,
        status: Union[int, ProjectStatus, List[Union[int, ProjectStatus]]],
        account_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        date_range: Optional[Tuple[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get projects by status with comprehensive filtering options.

        Args:
            status: Project status(es) to filter by
            account_id: Optional account filter
            manager_id: Optional project manager filter
            date_range: Optional date range tuple (start_date, end_date)
            limit: Maximum number of projects to return

        Returns:
            List of projects matching the criteria
        """
        filters = []

        # Handle status filter
        if isinstance(status, (list, tuple)):
            status_list = [
                s.value if isinstance(s, ProjectStatus) else s for s in status
            ]
            filters.append(QueryFilter(field="Status", op="in", value=status_list))
        else:
            status_value = status.value if isinstance(status, ProjectStatus) else status
            filters.append(QueryFilter(field="Status", op="eq", value=status_value))

        # Apply optional filters
        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))
        if manager_id:
            filters.append(
                QueryFilter(field="ProjectManagerResourceID", op="eq", value=manager_id)
            )

        # Apply date range filter
        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="StartDate", op="gte", value=start_date)
                )
            if end_date:
                filters.append(QueryFilter(field="EndDate", op="lte", value=end_date))

        return self.query(filters=filters, max_records=limit)

    def get_active_projects(
        self,
        account_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        exclude_on_hold: bool = False,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get active projects with comprehensive filtering options.

        Args:
            account_id: Optional account filter
            manager_id: Optional project manager filter
            exclude_on_hold: Whether to exclude projects on hold
            limit: Maximum number of projects to return

        Returns:
            List of active projects
        """
        active_statuses = [
            ProjectStatus.NEW,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.WAITING,
        ]
        if not exclude_on_hold:
            active_statuses.append(ProjectStatus.ON_HOLD)

        return self.get_projects_by_status(
            status=active_statuses,
            account_id=account_id,
            manager_id=manager_id,
            limit=limit,
        )

    def get_overdue_projects(
        self,
        account_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        overdue_days: int = 0,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get projects that are past their end date with enhanced filtering.

        Args:
            account_id: Optional account filter
            manager_id: Optional project manager filter
            overdue_days: Minimum number of days overdue (0 = any overdue)
            limit: Maximum number of projects to return

        Returns:
            List of overdue projects
        """
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=overdue_days)

        filters = [
            QueryFilter(field="EndDate", op="lt", value=cutoff_date.isoformat()),
            QueryFilter(field="Status", op="ne", value=ProjectStatus.COMPLETE.value),
            QueryFilter(field="Status", op="ne", value=ProjectStatus.CANCELLED.value),
        ]

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))
        if manager_id:
            filters.append(
                QueryFilter(field="ProjectManagerResourceID", op="eq", value=manager_id)
            )

        return self.query(filters=filters, max_records=limit)

    def get_projects_by_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = "StartDate",
        account_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Get projects within a specific date range.

        Args:
            start_date: Range start date (ISO format)
            end_date: Range end date (ISO format)
            date_field: Field to filter on ('StartDate', 'EndDate', 'ActualStartDate')
            account_id: Optional account filter
            status_filter: Optional status filter
            limit: Maximum number of projects to return

        Returns:
            List of projects within the date range
        """
        filters = []

        if start_date:
            filters.append(QueryFilter(field=date_field, op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field=date_field, op="lte", value=end_date))
        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        if status_filter:
            status_map = {
                "active": [
                    ProjectStatus.NEW.value,
                    ProjectStatus.IN_PROGRESS.value,
                    ProjectStatus.WAITING.value,
                ],
                "completed": [ProjectStatus.COMPLETE.value],
                "cancelled": [ProjectStatus.CANCELLED.value],
            }
            if status_filter.lower() in status_map:
                status_values = status_map[status_filter.lower()]
                filters.append(
                    QueryFilter(field="Status", op="in", value=status_values)
                )

        return self.query(filters=filters, max_records=limit)

    def search_projects(
        self,
        search_term: str,
        search_fields: Optional[List[str]] = None,
        account_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProjectData]:
        """
        Search projects by name, description, or other text fields.

        Args:
            search_term: Text to search for
            search_fields: Fields to search in (defaults to ProjectName and Description)
            account_id: Optional account filter
            status_filter: Optional status filter
            limit: Maximum number of projects to return

        Returns:
            List of matching projects
        """
        if not search_fields:
            search_fields = ["ProjectName", "Description"]

        filters = []

        # Create OR filters for each search field
        # search_filters = [  # TODO: Implement OR operations when API supports it
        #             QueryFilter(field=field, op="contains", value=search_term)
        #             for field in search_fields
        #         ]

        # Note: Autotask API doesn't support OR operations directly
        # This implementation searches each field separately and combines results
        # In a real implementation, you might need to make multiple API calls

        # For now, search in the primary field (ProjectName)
        filters.append(
            QueryFilter(field="ProjectName", op="contains", value=search_term)
        )

        if account_id:
            filters.append(QueryFilter(field="AccountID", op="eq", value=account_id))

        if status_filter and status_filter.lower() == "active":
            active_statuses = [
                ProjectStatus.NEW.value,
                ProjectStatus.IN_PROGRESS.value,
                ProjectStatus.WAITING.value,
            ]
            filters.append(QueryFilter(field="Status", op="in", value=active_statuses))

        return self.query(filters=filters, max_records=limit)

    # =====================================================================================
    # RESOURCE ALLOCATION AND SCHEDULING
    # =====================================================================================

    def assign_project_manager(
        self,
        project_id: int,
        manager_id: int,
        effective_date: Optional[str] = None,
        notify_manager: bool = True,
    ) -> ProjectData:
        """
        Assign a project manager to a project with enhanced options.

        Args:
            project_id: ID of project to update
            manager_id: Resource ID of the project manager
            effective_date: Date the assignment becomes effective
            notify_manager: Whether to notify the new manager

        Returns:
            Updated project data
        """
        update_data = {"ProjectManagerResourceID": manager_id}

        if effective_date:
            update_data["ManagerAssignmentDate"] = effective_date

        return self.update_by_id(project_id, update_data)

    def get_project_resources(
        self,
        project_id: int,
        role_filter: Optional[Union[int, ProjectResourceRole]] = None,
        active_only: bool = True,
        include_hours: bool = True,
    ) -> List[EntityDict]:
        """
        Get all resources assigned to a project.

        Args:
            project_id: ID of the project
            role_filter: Optional role filter
            active_only: Whether to return only active resource assignments
            include_hours: Whether to include hours information

        Returns:
            List of project resources
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if role_filter:
            role_value = (
                role_filter.value
                if isinstance(role_filter, ProjectResourceRole)
                else role_filter
            )
            filters.append(QueryFilter(field="Role", op="eq", value=role_value))

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        # Note: This assumes a ProjectResources entity exists in Autotask
        # In reality, this might need to query Tasks or TimeEntries to find resources
        try:
            return self.client.query("ProjectResources", filters=filters)
        except Exception:
            # Fallback: Get resources from tasks
            return self._get_resources_from_tasks(project_id)

    def assign_resource_to_project(
        self,
        project_id: int,
        resource_id: int,
        role: Union[int, ProjectResourceRole] = ProjectResourceRole.TEAM_MEMBER,
        allocation_percentage: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        hourly_rate: Optional[float] = None,
    ) -> EntityDict:
        """
        Assign a resource to a project with detailed configuration.

        Args:
            project_id: ID of the project
            resource_id: ID of the resource to assign
            role: Role of the resource on the project
            allocation_percentage: Percentage of resource's time allocated
            start_date: Assignment start date
            end_date: Assignment end date
            hourly_rate: Hourly rate for this assignment

        Returns:
            Created project resource assignment
        """
        role_value = role.value if isinstance(role, ProjectResourceRole) else role

        assignment_data = {
            "ProjectID": project_id,
            "ResourceID": resource_id,
            "Role": role_value,
        }

        # Add optional fields
        optional_fields = {
            "AllocationPercentage": allocation_percentage,
            "StartDate": start_date,
            "EndDate": end_date,
            "HourlyRate": hourly_rate,
        }

        for field, value in optional_fields.items():
            if value is not None:
                assignment_data[field] = value

        # Note: This assumes a ProjectResources entity exists
        # In practice, this might need to be handled differently
        try:
            return self.client.create("ProjectResources", assignment_data)
        except Exception as e:
            raise ValueError(f"Could not assign resource to project: {e}")

    def unassign_resource_from_project(
        self,
        project_id: int,
        resource_id: int,
        end_date: Optional[str] = None,
    ) -> bool:
        """
        Remove a resource assignment from a project.

        Args:
            project_id: ID of the project
            resource_id: ID of the resource to unassign
            end_date: Optional end date for the assignment

        Returns:
            True if successful
        """
        filters = [
            QueryFilter(field="ProjectID", op="eq", value=project_id),
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
        ]

        try:
            assignments = self.client.query("ProjectResources", filters=filters)
            for assignment in assignments:
                if end_date:
                    # Update with end date instead of deleting
                    self.client.update(
                        "ProjectResources", assignment["id"], {"EndDate": end_date}
                    )
                else:
                    # Delete the assignment
                    self.client.delete("ProjectResources", assignment["id"])
            return True
        except Exception:
            return False

    def get_resource_capacity(
        self,
        resource_id: int,
        date_range: Optional[Tuple[str, str]] = None,
        include_projects: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Get resource capacity information for project planning.

        Args:
            resource_id: ID of the resource
            date_range: Date range to analyze (start_date, end_date)
            include_projects: Specific project IDs to include in analysis

        Returns:
            Resource capacity information
        """
        capacity_info = {
            "resource_id": resource_id,
            "total_capacity_hours": 0,
            "allocated_hours": 0,
            "available_hours": 0,
            "allocation_percentage": 0,
            "projects": [],
        }

        # Get resource's standard work hours (assuming 40 hours/week)
        capacity_info["total_capacity_hours"] = 40.0

        # Get project assignments for the resource
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="StartDate", op="gte", value=start_date)
                )
            if end_date:
                filters.append(QueryFilter(field="EndDate", op="lte", value=end_date))

        try:
            assignments = self.client.query("ProjectResources", filters=filters)
            allocated_hours = sum(
                assignment.get("AllocationPercentage", 0) / 100 * 40
                for assignment in assignments
            )
            capacity_info["allocated_hours"] = allocated_hours
            capacity_info["available_hours"] = 40.0 - allocated_hours
            capacity_info["allocation_percentage"] = (allocated_hours / 40.0) * 100
            capacity_info["projects"] = assignments
        except Exception:
            # Fallback: estimate from time entries
            time_entries = self.get_resource_time_entries_for_projects(
                resource_id, date_range, include_projects
            )
            allocated_hours = sum(entry.get("HoursWorked", 0) for entry in time_entries)
            capacity_info["allocated_hours"] = allocated_hours
            capacity_info["available_hours"] = max(0, 40.0 - allocated_hours)
            capacity_info["allocation_percentage"] = min(
                100, (allocated_hours / 40.0) * 100
            )

        return capacity_info

    def detect_resource_conflicts(
        self,
        project_id: int,
        resource_id: Optional[int] = None,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect resource allocation conflicts for a project.

        Args:
            project_id: ID of the project to analyze
            resource_id: Specific resource to check (optional)
            date_range: Date range to analyze

        Returns:
            List of conflicts found
        """
        conflicts = []

        # Get project resources
        project_resources = self.get_project_resources(project_id)

        for resource in project_resources:
            if resource_id and resource.get("ResourceID") != resource_id:
                continue

            resource_capacity = self.get_resource_capacity(
                resource.get("ResourceID"), date_range
            )

            # Check for over-allocation
            if resource_capacity["allocation_percentage"] > 100:
                conflicts.append(
                    {
                        "type": "over_allocation",
                        "resource_id": resource.get("ResourceID"),
                        "allocation_percentage": resource_capacity[
                            "allocation_percentage"
                        ],
                        "over_allocation": resource_capacity["allocation_percentage"]
                        - 100,
                        "conflicting_projects": resource_capacity["projects"],
                    }
                )

        return conflicts

    def get_project_timeline(
        self,
        project_id: int,
        include_tasks: bool = True,
        include_milestones: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive project timeline information.

        Args:
            project_id: ID of the project
            include_tasks: Whether to include task timeline
            include_milestones: Whether to include milestones

        Returns:
            Project timeline information
        """
        project = self.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        timeline = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "start_date": project.get("StartDate"),
            "end_date": project.get("EndDate"),
            "actual_start_date": project.get("ActualStartDate"),
            "status": project.get("Status"),
            "completion_percentage": project.get("CompletedPercentage", 0),
            "tasks": [],
            "milestones": [],
            "critical_path": [],
        }

        if include_tasks:
            tasks = self.get_project_tasks(project_id)
            timeline["tasks"] = sorted(tasks, key=lambda x: x.get("StartDate", ""))

        if include_milestones:
            milestones = self.get_project_milestones(project_id)
            timeline["milestones"] = sorted(
                milestones, key=lambda x: x.get("DueDate", "")
            )

        return timeline

    def calculate_critical_path(
        self,
        project_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Calculate the critical path for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of tasks in the critical path
        """
        tasks = self.get_project_tasks(project_id)

        # This is a simplified critical path calculation
        # In a real implementation, you would use network analysis algorithms

        critical_tasks = []
        for task in tasks:
            # Identify tasks with no slack/float time
            start_date = task.get("StartDate")
            end_date = task.get("EndDate")

            if start_date and end_date:
                # Tasks that are critical to the project timeline
                if task.get("IsCritical") or task.get("Priority") == "High":
                    critical_tasks.append(task)

        return sorted(critical_tasks, key=lambda x: x.get("StartDate", ""))

    def get_project_tasks(
        self,
        project_id: int,
        status_filter: Optional[str] = None,
        assigned_resource_id: Optional[int] = None,
        include_completed: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all tasks for a specific project with comprehensive filtering.

        Args:
            project_id: ID of the project
            status_filter: Optional status filter ('open', 'completed', etc.)
            assigned_resource_id: Optional resource assignment filter
            include_completed: Whether to include completed tasks
            limit: Maximum number of tasks to return

        Returns:
            List of tasks for the project
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if status_filter:
            status_map = {
                "open": [1, 2, 3, 4],  # New, In Progress, Waiting, On Hold
                "completed": [5],  # Complete
                "active": [1, 2, 3],  # New, In Progress, Waiting
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                filters.append(QueryFilter(field="Status", op="in", value=status_ids))

        if assigned_resource_id:
            filters.append(
                QueryFilter(
                    field="AssignedResourceID", op="eq", value=assigned_resource_id
                )
            )

        if not include_completed:
            filters.append(
                QueryFilter(field="Status", op="ne", value=5)
            )  # Not Complete

        return self.client.query("Tasks", filters=filters, max_records=limit)

    def get_project_milestones(
        self,
        project_id: int,
        completed_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get milestones for a project.

        Args:
            project_id: ID of the project
            completed_only: Whether to return only completed milestones
            limit: Maximum number of milestones to return

        Returns:
            List of project milestones
        """
        filters = [
            QueryFilter(field="ProjectID", op="eq", value=project_id),
            QueryFilter(
                field="Type", op="eq", value=ProjectLineItemType.MILESTONE.value
            ),
        ]

        if completed_only:
            filters.append(QueryFilter(field="Status", op="eq", value=5))  # Complete

        # Note: Might need to query ProjectLineItems or similar entity
        try:
            return self.client.query(
                "ProjectLineItems", filters=filters, max_records=limit
            )
        except Exception:
            # Fallback: Get milestones from tasks with milestone flag
            task_filters = [
                QueryFilter(field="ProjectID", op="eq", value=project_id),
                QueryFilter(field="IsMilestone", op="eq", value=True),
            ]
            return self.client.query("Tasks", filters=task_filters, max_records=limit)

    def _get_resources_from_tasks(self, project_id: int) -> List[EntityDict]:
        """
        Helper method to get resources from project tasks.

        Args:
            project_id: ID of the project

        Returns:
            List of resources working on project tasks
        """
        tasks = self.get_project_tasks(project_id)
        resource_ids = set()
        resources = []

        for task in tasks:
            resource_id = task.get("AssignedResourceID")
            if resource_id and resource_id not in resource_ids:
                resource_ids.add(resource_id)
                resources.append(
                    {
                        "ResourceID": resource_id,
                        "ProjectID": project_id,
                        "Role": ProjectResourceRole.TEAM_MEMBER.value,
                    }
                )

        return resources

    def get_resource_time_entries_for_projects(
        self,
        resource_id: int,
        date_range: Optional[Tuple[str, str]] = None,
        project_ids: Optional[List[int]] = None,
    ) -> List[EntityDict]:
        """
        Get time entries for a resource across projects.

        Args:
            resource_id: ID of the resource
            date_range: Optional date range
            project_ids: Specific project IDs to include

        Returns:
            List of time entries
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="DateWorked", op="gte", value=start_date)
                )
            if end_date:
                filters.append(
                    QueryFilter(field="DateWorked", op="lte", value=end_date)
                )

        if project_ids:
            filters.append(QueryFilter(field="ProjectID", op="in", value=project_ids))

        return self.client.query("TimeEntries", filters=filters)

    # =====================================================================================
    # FINANCIAL MANAGEMENT AND BUDGET TRACKING
    # =====================================================================================

    def update_project_budget(
        self,
        project_id: int,
        budget_hours: Optional[float] = None,
        budget_cost: Optional[float] = None,
        estimated_hours: Optional[float] = None,
        estimated_cost: Optional[float] = None,
    ) -> ProjectData:
        """
        Update project budget information.

        Args:
            project_id: ID of project to update
            budget_hours: New budgeted hours
            budget_cost: New budgeted cost
            estimated_hours: New estimated hours
            estimated_cost: New estimated cost

        Returns:
            Updated project data
        """
        update_data = {}

        if budget_hours is not None:
            update_data["BudgetHours"] = budget_hours
        if budget_cost is not None:
            update_data["BudgetCost"] = budget_cost
        if estimated_hours is not None:
            update_data["EstimatedHours"] = estimated_hours
        if estimated_cost is not None:
            update_data["EstimatedCost"] = estimated_cost

        if not update_data:
            raise ValueError("At least one budget field must be provided")

        return self.update_by_id(project_id, update_data)

    def get_project_financial_summary(
        self,
        project_id: int,
        include_time_entries: bool = True,
        include_expenses: bool = True,
        include_line_items: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive financial summary for a project.

        Args:
            project_id: ID of the project
            include_time_entries: Whether to include time entry costs
            include_expenses: Whether to include expense costs
            include_line_items: Whether to include line item costs

        Returns:
            Financial summary with budget vs actual analysis
        """
        project = self.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        summary = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "project_type": project.get("Type"),
            "budget": {
                "hours": project.get("BudgetHours", 0),
                "cost": project.get("BudgetCost", 0),
            },
            "estimated": {
                "hours": project.get("EstimatedHours", 0),
                "cost": project.get("EstimatedCost", 0),
            },
            "actual": {
                "hours": 0,
                "cost": 0,
                "billable_hours": 0,
                "billable_cost": 0,
                "non_billable_hours": 0,
                "non_billable_cost": 0,
            },
            "expenses": {
                "total": 0,
                "billable": 0,
                "non_billable": 0,
            },
            "variance": {
                "hours": 0,
                "cost": 0,
                "percentage": 0,
            },
            "profitability": {
                "gross_profit": 0,
                "gross_margin": 0,
                "markup": 0,
            },
        }

        # Get actual hours and costs from time entries
        if include_time_entries:
            time_entries = self.get_project_time_entries(project_id)
            for entry in time_entries:
                hours = entry.get("HoursWorked", 0)
                summary["actual"]["hours"] += hours

                if entry.get("BillableToAccount"):
                    summary["actual"]["billable_hours"] += hours
                else:
                    summary["actual"]["non_billable_hours"] += hours

        # Get expenses
        if include_expenses:
            expenses = self.get_project_expenses(project_id)
            for expense in expenses:
                amount = expense.get("Amount", 0)
                summary["expenses"]["total"] += amount

                if expense.get("BillableToAccount"):
                    summary["expenses"]["billable"] += amount
                else:
                    summary["expenses"]["non_billable"] += amount

        # Calculate variances
        budget_cost = summary["budget"]["cost"]
        actual_cost = summary["actual"]["cost"] + summary["expenses"]["total"]

        summary["variance"]["hours"] = (
            summary["actual"]["hours"] - summary["budget"]["hours"]
        )
        summary["variance"]["cost"] = actual_cost - budget_cost

        if budget_cost > 0:
            summary["variance"]["percentage"] = (
                summary["variance"]["cost"] / budget_cost
            ) * 100

        # Calculate profitability (simplified)
        revenue = summary["actual"]["billable_cost"] + summary["expenses"]["billable"]
        costs = actual_cost
        summary["profitability"]["gross_profit"] = revenue - costs

        if revenue > 0:
            summary["profitability"]["gross_margin"] = (
                summary["profitability"]["gross_profit"] / revenue
            ) * 100
        if costs > 0:
            summary["profitability"]["markup"] = (
                summary["profitability"]["gross_profit"] / costs
            ) * 100

        return summary

    def get_budget_utilization(
        self,
        project_id: int,
        as_of_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get budget utilization metrics for a project.

        Args:
            project_id: ID of the project
            as_of_date: Date to calculate utilization as of (defaults to now)

        Returns:
            Budget utilization metrics
        """
        financial_summary = self.get_project_financial_summary(project_id)

        utilization = {
            "project_id": project_id,
            "as_of_date": as_of_date or datetime.now().isoformat(),
            "hours_utilization": {
                "budgeted": financial_summary["budget"]["hours"],
                "actual": financial_summary["actual"]["hours"],
                "remaining": 0,
                "utilization_percentage": 0,
            },
            "cost_utilization": {
                "budgeted": financial_summary["budget"]["cost"],
                "actual": financial_summary["actual"]["cost"]
                + financial_summary["expenses"]["total"],
                "remaining": 0,
                "utilization_percentage": 0,
            },
            "status": "on_budget",
            "alerts": [],
        }

        # Calculate remaining budget
        utilization["hours_utilization"]["remaining"] = max(
            0,
            utilization["hours_utilization"]["budgeted"]
            - utilization["hours_utilization"]["actual"],
        )
        utilization["cost_utilization"]["remaining"] = max(
            0,
            utilization["cost_utilization"]["budgeted"]
            - utilization["cost_utilization"]["actual"],
        )

        # Calculate utilization percentages
        if utilization["hours_utilization"]["budgeted"] > 0:
            utilization["hours_utilization"]["utilization_percentage"] = (
                utilization["hours_utilization"]["actual"]
                / utilization["hours_utilization"]["budgeted"]
            ) * 100

        if utilization["cost_utilization"]["budgeted"] > 0:
            utilization["cost_utilization"]["utilization_percentage"] = (
                utilization["cost_utilization"]["actual"]
                / utilization["cost_utilization"]["budgeted"]
            ) * 100

        # Determine status and generate alerts
        cost_util = utilization["cost_utilization"]["utilization_percentage"]
        hours_util = utilization["hours_utilization"]["utilization_percentage"]

        if cost_util > 100 or hours_util > 100:
            utilization["status"] = "over_budget"
            utilization["alerts"].append("Project is over budget")
        elif cost_util > 90 or hours_util > 90:
            utilization["status"] = "near_budget_limit"
            utilization["alerts"].append("Project is approaching budget limit")
        elif cost_util > 75 or hours_util > 75:
            utilization["status"] = "on_track"
            utilization["alerts"].append("Project is on track with budget consumption")

        return utilization

    def track_project_costs(
        self,
        project_id: int,
        cost_type: str = "all",  # "labor", "expense", "material", "all"
        date_range: Optional[Tuple[str, str]] = None,
        group_by: str = "month",  # "day", "week", "month"
    ) -> Dict[str, Any]:
        """
        Track project costs over time with detailed breakdown.

        Args:
            project_id: ID of the project
            cost_type: Type of costs to track
            date_range: Date range for cost tracking
            group_by: How to group the cost data

        Returns:
            Cost tracking data with time series analysis
        """
        cost_tracking = {
            "project_id": project_id,
            "cost_type": cost_type,
            "date_range": date_range,
            "group_by": group_by,
            "total_costs": 0,
            "cost_breakdown": {
                "labor": 0,
                "expenses": 0,
                "materials": 0,
            },
            "time_series": [],
            "trends": {
                "average_monthly_cost": 0,
                "cost_acceleration": 0,
                "projected_total": 0,
            },
        }

        # Get time entries for labor costs
        if cost_type in ["labor", "all"]:
            time_entries = self.get_project_time_entries(project_id)
            labor_cost = sum(
                entry.get("HoursWorked", 0) * entry.get("HourlyRate", 0)
                for entry in time_entries
                if date_range is None or self._entry_in_date_range(entry, date_range)
            )
            cost_tracking["cost_breakdown"]["labor"] = labor_cost

        # Get expenses
        if cost_type in ["expense", "all"]:
            expenses = self.get_project_expenses(project_id)
            expense_cost = sum(
                expense.get("Amount", 0)
                for expense in expenses
                if date_range is None or self._entry_in_date_range(expense, date_range)
            )
            cost_tracking["cost_breakdown"]["expenses"] = expense_cost

        # Calculate totals
        cost_tracking["total_costs"] = sum(cost_tracking["cost_breakdown"].values())

        return cost_tracking

    def _entry_in_date_range(
        self, entry: Dict[str, Any], date_range: Tuple[str, str]
    ) -> bool:
        """
        Helper to check if an entry falls within a date range.

        Args:
            entry: Entry with date field
            date_range: Tuple of (start_date, end_date)

        Returns:
            True if entry is in range
        """
        start_date, end_date = date_range
        entry_date = (
            entry.get("DateWorked") or entry.get("ExpenseDate") or entry.get("Date")
        )

        if not entry_date:
            return True

        return start_date <= entry_date <= end_date

    # =====================================================================================
    # INTEGRATION METHODS (TASKS, TICKETS, TIME ENTRIES, EXPENSES)
    # =====================================================================================

    def get_project_time_entries(
        self,
        project_id: int,
        resource_id: Optional[int] = None,
        date_range: Optional[Tuple[str, str]] = None,
        billable_only: bool = False,
        include_summary: bool = False,
        limit: Optional[int] = None,
    ) -> Union[List[EntityDict], Dict[str, Any]]:
        """
        Get all time entries for a specific project with comprehensive filtering.

        Args:
            project_id: ID of the project
            resource_id: Optional resource filter
            date_range: Optional date range (start_date, end_date)
            billable_only: Whether to return only billable entries
            include_summary: Whether to include summary statistics
            limit: Maximum number of entries to return

        Returns:
            List of time entries or dict with summary if include_summary=True
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="DateWorked", op="gte", value=start_date)
                )
            if end_date:
                filters.append(
                    QueryFilter(field="DateWorked", op="lte", value=end_date)
                )

        if billable_only:
            filters.append(QueryFilter(field="BillableToAccount", op="eq", value=True))

        time_entries = self.client.query(
            "TimeEntries", filters=filters, max_records=limit
        )

        if include_summary:
            total_hours = sum(entry.get("HoursWorked", 0) for entry in time_entries)
            billable_hours = sum(
                entry.get("HoursWorked", 0)
                for entry in time_entries
                if entry.get("BillableToAccount")
            )

            return {
                "entries": time_entries,
                "summary": {
                    "total_entries": len(time_entries),
                    "total_hours": total_hours,
                    "billable_hours": billable_hours,
                    "non_billable_hours": total_hours - billable_hours,
                    "unique_resources": len(
                        set(
                            entry.get("ResourceID")
                            for entry in time_entries
                            if entry.get("ResourceID")
                        )
                    ),
                },
            }

        return time_entries

    def get_project_expenses(
        self,
        project_id: int,
        resource_id: Optional[int] = None,
        expense_category: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
        billable_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all expenses for a specific project.

        Args:
            project_id: ID of the project
            resource_id: Optional resource filter
            expense_category: Optional expense category filter
            date_range: Optional date range (start_date, end_date)
            billable_only: Whether to return only billable expenses
            limit: Maximum number of expenses to return

        Returns:
            List of expenses for the project
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        if expense_category:
            filters.append(
                QueryFilter(field="ExpenseCategory", op="eq", value=expense_category)
            )

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="ExpenseDate", op="gte", value=start_date)
                )
            if end_date:
                filters.append(
                    QueryFilter(field="ExpenseDate", op="lte", value=end_date)
                )

        if billable_only:
            filters.append(QueryFilter(field="BillableToAccount", op="eq", value=True))

        return self.client.query("Expenses", filters=filters, max_records=limit)

    def get_project_tickets(
        self,
        project_id: int,
        status_filter: Optional[str] = None,
        assigned_resource_id: Optional[int] = None,
        priority_filter: Optional[str] = None,
        include_completed: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all tickets associated with a project with comprehensive filtering.

        Args:
            project_id: ID of the project
            status_filter: Optional status filter ('open', 'closed', etc.)
            assigned_resource_id: Optional resource assignment filter
            priority_filter: Optional priority filter ('high', 'medium', 'low')
            include_completed: Whether to include completed tickets
            limit: Maximum number of tickets to return

        Returns:
            List of project tickets
        """
        filters = [QueryFilter(field="ProjectID", op="eq", value=project_id)]

        if status_filter:
            status_map = {
                "open": [1, 8, 9, 10, 11],
                "closed": [5],
                "new": [1],
                "in_progress": [8, 9, 10, 11],
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

        if assigned_resource_id:
            filters.append(
                QueryFilter(
                    field="AssignedResourceID", op="eq", value=assigned_resource_id
                )
            )

        if priority_filter:
            priority_map = {"low": [4], "medium": [3], "high": [2], "critical": [1]}
            if priority_filter.lower() in priority_map:
                priority_ids = priority_map[priority_filter.lower()]
                filters.append(
                    QueryFilter(field="Priority", op="in", value=priority_ids)
                )

        if not include_completed:
            filters.append(
                QueryFilter(field="Status", op="ne", value=5)
            )  # Not Complete

        return self.client.query("Tickets", filters=filters, max_records=limit)

    def create_project_task(
        self,
        project_id: int,
        title: str,
        description: Optional[str] = None,
        assigned_resource_id: Optional[int] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        priority: int = 3,  # Medium priority
        **kwargs,
    ) -> EntityDict:
        """
        Create a new task for a project.

        Args:
            project_id: ID of the project
            title: Task title
            description: Task description
            assigned_resource_id: Resource to assign the task to
            start_date: Task start date
            due_date: Task due date
            estimated_hours: Estimated hours for completion
            priority: Task priority (1=High, 2=Medium, 3=Low)
            **kwargs: Additional task fields

        Returns:
            Created task data
        """
        task_data = {
            "ProjectID": project_id,
            "Title": title,
            "Priority": priority,
            **kwargs,
        }

        optional_fields = {
            "Description": description,
            "AssignedResourceID": assigned_resource_id,
            "StartDate": start_date,
            "DueDate": due_date,
            "EstimatedHours": estimated_hours,
        }

        for field, value in optional_fields.items():
            if value is not None:
                task_data[field] = value

        return self.client.create("Tasks", task_data)

    def link_project_to_contract(
        self,
        project_id: int,
        contract_id: int,
    ) -> ProjectData:
        """
        Link a project to a contract.

        Args:
            project_id: ID of the project
            contract_id: ID of the contract

        Returns:
            Updated project data
        """
        return self.update_by_id(project_id, {"ContractID": contract_id})

    def get_project_documents(
        self,
        project_id: int,
        document_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get documents associated with a project.

        Args:
            project_id: ID of the project
            document_type: Optional document type filter
            limit: Maximum number of documents to return

        Returns:
            List of project documents
        """
        filters = [
            QueryFilter(field="ParentType", op="eq", value="Project"),
            QueryFilter(field="ParentID", op="eq", value=project_id),
        ]

        if document_type:
            filters.append(QueryFilter(field="Type", op="eq", value=document_type))

        return self.client.query("Attachments", filters=filters, max_records=limit)

    # =====================================================================================
    # PROJECT ANALYTICS AND REPORTING
    # =====================================================================================

    def generate_project_report(
        self,
        project_id: int,
        report_type: str = "comprehensive",
        include_financials: bool = True,
        include_resources: bool = True,
        include_timeline: bool = True,
        include_tasks: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive project report.

        Args:
            project_id: ID of the project
            report_type: Type of report ('comprehensive', 'financial', 'resource', 'timeline')
            include_financials: Whether to include financial analysis
            include_resources: Whether to include resource analysis
            include_timeline: Whether to include timeline analysis
            include_tasks: Whether to include task analysis

        Returns:
            Comprehensive project report
        """
        project = self.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        report = {
            "project_id": project_id,
            "project_name": project.get("ProjectName"),
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "project_overview": {
                "status": project.get("Status"),
                "type": project.get("Type"),
                "start_date": project.get("StartDate"),
                "end_date": project.get("EndDate"),
                "completion_percentage": project.get("CompletedPercentage", 0),
                "project_manager": project.get("ProjectManagerResourceID"),
                "account_id": project.get("AccountID"),
            },
        }

        if include_financials or report_type in ["comprehensive", "financial"]:
            report["financial_summary"] = self.get_project_financial_summary(project_id)
            report["budget_utilization"] = self.get_budget_utilization(project_id)

        if include_resources or report_type in ["comprehensive", "resource"]:
            report["resource_analysis"] = {
                "assigned_resources": self.get_project_resources(project_id),
                "resource_utilization": {},  # Could be expanded
                "conflicts": self.detect_resource_conflicts(project_id),
            }

        if include_timeline or report_type in ["comprehensive", "timeline"]:
            report["timeline_analysis"] = self.get_project_timeline(project_id)
            report["critical_path"] = self.calculate_critical_path(project_id)

        if include_tasks or report_type in ["comprehensive"]:
            report["task_analysis"] = {
                "total_tasks": len(self.get_project_tasks(project_id)),
                "completed_tasks": len(
                    self.get_project_tasks(project_id, status_filter="completed")
                ),
                "active_tasks": len(
                    self.get_project_tasks(project_id, status_filter="active")
                ),
                "overdue_tasks": [],  # Could be expanded
            }

        return report

    def get_project_performance_metrics(
        self,
        project_id: int,
        comparison_projects: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a project with optional comparison.

        Args:
            project_id: ID of the project to analyze
            comparison_projects: Optional list of project IDs for comparison

        Returns:
            Performance metrics and comparisons
        """
        project = self.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        financial_summary = self.get_project_financial_summary(project_id)

        metrics = {
            "project_id": project_id,
            "performance_indicators": {
                "budget_variance_percentage": financial_summary["variance"][
                    "percentage"
                ],
                "schedule_performance": self._calculate_schedule_performance(project),
                "cost_performance": self._calculate_cost_performance(financial_summary),
                "resource_efficiency": self._calculate_resource_efficiency(project_id),
                "quality_metrics": self._calculate_quality_metrics(project_id),
            },
            "health_score": 0,
            "risk_factors": [],
            "recommendations": [],
        }

        # Calculate overall health score (0-100)
        health_factors = [
            max(
                0,
                100
                - abs(metrics["performance_indicators"]["budget_variance_percentage"]),
            ),
            metrics["performance_indicators"]["schedule_performance"],
            metrics["performance_indicators"]["cost_performance"],
            metrics["performance_indicators"]["resource_efficiency"],
            metrics["performance_indicators"]["quality_metrics"],
        ]
        metrics["health_score"] = sum(health_factors) / len(health_factors)

        # Generate risk factors and recommendations
        if metrics["performance_indicators"]["budget_variance_percentage"] > 10:
            metrics["risk_factors"].append("Project is significantly over budget")
            metrics["recommendations"].append(
                "Review budget allocation and cost controls"
            )

        if metrics["performance_indicators"]["schedule_performance"] < 80:
            metrics["risk_factors"].append("Project is behind schedule")
            metrics["recommendations"].append("Review timeline and resource allocation")

        return metrics

    def _calculate_schedule_performance(self, project: Dict[str, Any]) -> float:
        """Calculate schedule performance index (0-100)."""
        # Simplified calculation - in reality would use earned value management
        completion_pct = project.get("CompletedPercentage", 0)

        # Calculate expected completion based on dates
        start_date = project.get("StartDate")
        end_date = project.get("EndDate")

        if not start_date or not end_date:
            return completion_pct

        # This is a simplified calculation
        return min(100, completion_pct * 1.2)  # Placeholder logic

    def _calculate_cost_performance(self, financial_summary: Dict[str, Any]) -> float:
        """Calculate cost performance index (0-100)."""
        budgeted = financial_summary["budget"]["cost"]
        actual = (
            financial_summary["actual"]["cost"] + financial_summary["expenses"]["total"]
        )

        if budgeted == 0:
            return 100

        performance = (budgeted / actual) * 100 if actual > 0 else 100
        return min(100, performance)

    def _calculate_resource_efficiency(self, project_id: int) -> float:
        """Calculate resource efficiency score (0-100)."""
        # Simplified calculation based on resource utilization
        conflicts = self.detect_resource_conflicts(project_id)
        if conflicts:
            return max(0, 100 - len(conflicts) * 20)
        return 100

    def _calculate_quality_metrics(self, project_id: int) -> float:
        """Calculate quality metrics score (0-100)."""
        # Simplified calculation based on tickets and issues
        tickets = self.get_project_tickets(project_id)
        if not tickets:
            return 100

        # Fewer tickets might indicate higher quality
        open_tickets = len(self.get_project_tickets(project_id, status_filter="open"))
        total_tickets = len(tickets)

        if total_tickets == 0:
            return 100

        quality_score = max(0, 100 - (open_tickets / total_tickets) * 100)
        return quality_score

    # =====================================================================================
    # BULK OPERATIONS AND UTILITIES
    # =====================================================================================

    def bulk_update_projects(
        self,
        project_ids: List[int],
        update_data: Dict[str, Any],
        validate_before_update: bool = True,
    ) -> List[ProjectData]:
        """
        Bulk update multiple projects with the same data.

        Args:
            project_ids: List of project IDs to update
            update_data: Data to update for all projects
            validate_before_update: Whether to validate projects exist first

        Returns:
            List of updated project data
        """
        if validate_before_update:
            # Verify all projects exist
            existing_projects = []
            for project_id in project_ids:
                project = self.get_by_id(project_id)
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                existing_projects.append(project)

        updated_projects = []
        for project_id in project_ids:
            try:
                updated_project = self.update_by_id(project_id, update_data)
                updated_projects.append(updated_project)
            except Exception as e:
                # Log error but continue with other projects
                print(f"Error updating project {project_id}: {e}")

        return updated_projects

    def export_projects_data(
        self,
        project_ids: Optional[List[int]] = None,
        account_id: Optional[int] = None,
        include_tasks: bool = False,
        include_time_entries: bool = False,
        include_expenses: bool = False,
        format_type: str = "dict",
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Export project data in various formats.

        Args:
            project_ids: Specific project IDs to export
            account_id: Export all projects for an account
            include_tasks: Whether to include task data
            include_time_entries: Whether to include time entry data
            include_expenses: Whether to include expense data
            format_type: Export format ('dict', 'json', 'csv')

        Returns:
            Exported data in requested format
        """
        if project_ids:
            projects = [
                self.get_by_id(pid) for pid in project_ids if self.get_by_id(pid)
            ]
        elif account_id:
            projects = self.get_projects_by_account(account_id)
        else:
            projects = self.get_active_projects()

        export_data = []
        for project in projects:
            project_data = dict(project)
            project_id = project.get("id") or project.get("ID")

            if include_tasks:
                project_data["tasks"] = self.get_project_tasks(project_id)
            if include_time_entries:
                project_data["time_entries"] = self.get_project_time_entries(project_id)
            if include_expenses:
                project_data["expenses"] = self.get_project_expenses(project_id)

            export_data.append(project_data)

        if format_type == "json":
            import json

            return json.dumps(export_data, indent=2)
        elif format_type == "csv":
            # Basic CSV export (would need more sophisticated implementation)
            import csv
            import io

            output = io.StringIO()
            if export_data:
                fieldnames = export_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(export_data)
            return output.getvalue()

        return export_data
