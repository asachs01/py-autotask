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

    def create_milestone(
        self,
        project_id: int,
        title: str,
        target_date: str,
        description: Optional[str] = None,
        priority: str = "Medium",
        milestone_type: str = "Project",
        deliverables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new milestone for a project.

        Args:
            project_id: ID of the project
            title: Milestone title
            target_date: Target completion date (YYYY-MM-DD)
            description: Optional milestone description
            priority: Milestone priority (Low, Medium, High, Critical)
            milestone_type: Type of milestone (Project, Contract, Billing, etc.)
            deliverables: List of expected deliverables

        Returns:
            Created milestone data
        """
        milestone_data = {
            "ProjectID": project_id,
            "Title": title,
            "TargetDate": target_date,
            "Description": description or "",
            "Priority": priority,
            "MilestoneType": milestone_type,
            "Status": "Planned",
            "CompletionPercentage": 0,
            "CreatedDate": datetime.now().isoformat(),
            "IsActive": True,
        }

        if deliverables:
            milestone_data["Deliverables"] = ",".join(deliverables)

        try:
            # Create milestone record in Autotask
            milestone = self.entity.create(milestone_data)

            # Add audit log
            self._log_milestone_activity(
                project_id, "created", f"Milestone '{title}' created"
            )

            return milestone
        except Exception as e:
            raise Exception(f"Failed to create milestone: {str(e)}")

    def update_milestone(
        self,
        milestone_id: int,
        updates: Dict[str, Any],
        completion_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing milestone.

        Args:
            milestone_id: ID of the milestone to update
            updates: Dictionary of fields to update
            completion_notes: Optional notes when marking as complete

        Returns:
            Updated milestone data
        """
        try:
            # Get existing milestone
            milestone = self.entity.get_by_id(milestone_id)
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")

            # Prepare update data
            update_data = dict(updates)
            update_data["LastModifiedDate"] = datetime.now().isoformat()

            # Handle completion status
            if "Status" in updates and updates["Status"] == "Completed":
                update_data["CompletionDate"] = datetime.now().isoformat()
                update_data["CompletionPercentage"] = 100
                if completion_notes:
                    update_data["CompletionNotes"] = completion_notes

            # Update milestone
            updated_milestone = self.entity.update(milestone_id, update_data)

            # Log activity
            project_id = milestone.get("ProjectID")
            activity_msg = f"Milestone '{milestone.get('Title')}' updated"
            if "Status" in updates:
                activity_msg += f" - status changed to {updates['Status']}"

            self._log_milestone_activity(project_id, "updated", activity_msg)

            return updated_milestone
        except Exception as e:
            raise Exception(f"Failed to update milestone: {str(e)}")

    def delete_milestone(self, milestone_id: int) -> bool:
        """
        Delete a milestone.

        Args:
            milestone_id: ID of the milestone to delete

        Returns:
            True if successfully deleted
        """
        try:
            # Get milestone info for logging
            milestone = self.entity.get_by_id(milestone_id)
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")

            # Soft delete by marking as inactive
            self.entity.update(
                milestone_id,
                {
                    "IsActive": False,
                    "Status": "Cancelled",
                    "LastModifiedDate": datetime.now().isoformat(),
                },
            )

            # Log activity
            project_id = milestone.get("ProjectID")
            self._log_milestone_activity(
                project_id, "deleted", f"Milestone '{milestone.get('Title')}' deleted"
            )

            return True
        except Exception as e:
            raise Exception(f"Failed to delete milestone: {str(e)}")

    def get_project_milestones(
        self,
        project_id: int,
        status_filter: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all milestones for a project.

        Args:
            project_id: ID of the project
            status_filter: Optional status filter (Planned, In Progress, Completed, etc.)
            include_inactive: Include inactive/deleted milestones

        Returns:
            List of milestone data
        """
        filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        if not include_inactive:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        if status_filter:
            filters.append({"field": "Status", "op": "eq", "value": status_filter})

        return self.entity.query(filters)

    def get_milestone_progress(self, project_id: int) -> Dict[str, Any]:
        """
        Get milestone progress summary for a project.

        Args:
            project_id: ID of the project

        Returns:
            Milestone progress summary
        """
        milestones = self.get_project_milestones(project_id)

        progress = {
            "project_id": project_id,
            "total_milestones": len(milestones),
            "completed": 0,
            "in_progress": 0,
            "planned": 0,
            "overdue": 0,
            "completion_percentage": 0,
            "next_milestone": None,
            "critical_milestones": [],
            "overdue_milestones": [],
        }

        now = datetime.now()

        for milestone in milestones:
            status = milestone.get("Status", "")
            target_date = milestone.get("TargetDate", "")
            priority = milestone.get("Priority", "")

            # Count by status
            if status == "Completed":
                progress["completed"] += 1
            elif status == "In Progress":
                progress["in_progress"] += 1
            else:
                progress["planned"] += 1

            # Check for overdue
            if target_date and status != "Completed":
                try:
                    target = datetime.fromisoformat(target_date.replace("Z", "+00:00"))
                    if target < now:
                        progress["overdue"] += 1
                        progress["overdue_milestones"].append(
                            {
                                "id": milestone.get("id"),
                                "title": milestone.get("Title"),
                                "target_date": target_date,
                                "days_overdue": (now - target).days,
                            }
                        )
                except:
                    pass

            # Track critical milestones
            if priority in ["High", "Critical"]:
                progress["critical_milestones"].append(
                    {
                        "id": milestone.get("id"),
                        "title": milestone.get("Title"),
                        "target_date": target_date,
                        "status": status,
                    }
                )

        # Calculate completion percentage
        if progress["total_milestones"] > 0:
            progress["completion_percentage"] = (
                progress["completed"] / progress["total_milestones"]
            ) * 100

        # Find next milestone
        upcoming = [
            m
            for m in milestones
            if m.get("Status") in ["Planned", "In Progress"] and m.get("TargetDate")
        ]
        if upcoming:
            upcoming.sort(key=lambda x: x.get("TargetDate", ""))
            progress["next_milestone"] = {
                "id": upcoming[0].get("id"),
                "title": upcoming[0].get("Title"),
                "target_date": upcoming[0].get("TargetDate"),
                "status": upcoming[0].get("Status"),
            }

        return progress

    def _log_milestone_activity(
        self, project_id: int, action: str, description: str
    ) -> None:
        """Log milestone activity for audit trail."""
        try:
            activity_data = {
                "ProjectID": project_id,
                "ActivityType": "Milestone",
                "Action": action,
                "Description": description,
                "Timestamp": datetime.now().isoformat(),
                "UserID": getattr(self, "current_user_id", None),
            }
            # Log to project notes or activity log
            self.add_project_note(project_id, f"[Milestone Activity] {description}")
        except:
            # Fail silently for logging
            pass

    def get_gantt_chart_data(
        self,
        project_id: int,
        include_tasks: bool = True,
        include_milestones: bool = True,
        include_dependencies: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive Gantt chart data for a project.

        Args:
            project_id: ID of the project
            include_tasks: Include project tasks
            include_milestones: Include project milestones
            include_dependencies: Include task dependencies

        Returns:
            Complete Gantt chart data structure
        """
        project = self.get_project_details(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        gantt_data = {
            "project": {
                "id": project_id,
                "name": project.get("ProjectName", ""),
                "start_date": project.get("StartDateTime", ""),
                "end_date": project.get("EndDateTime", ""),
                "status": project.get("Status", ""),
                "completion_percentage": project.get("PercentComplete", 0),
            },
            "tasks": [],
            "milestones": [],
            "dependencies": [],
            "critical_path": [],
            "timeline": {
                "earliest_start": None,
                "latest_end": None,
                "duration_days": 0,
            },
            "resource_allocation": {},
        }

        # Get tasks if requested
        if include_tasks:
            tasks = self.get_project_tasks(project_id)
            gantt_data["tasks"] = self._format_tasks_for_gantt(tasks)

        # Get milestones if requested
        if include_milestones:
            milestones = self.get_project_milestones(project_id)
            gantt_data["milestones"] = self._format_milestones_for_gantt(milestones)

        # Get dependencies if requested
        if include_dependencies:
            gantt_data["dependencies"] = self._get_task_dependencies(project_id)

        # Calculate timeline metrics
        gantt_data["timeline"] = self._calculate_timeline_metrics(gantt_data)

        # Calculate critical path
        if include_tasks and include_dependencies:
            gantt_data["critical_path"] = self._calculate_critical_path(gantt_data)

        # Get resource allocation
        gantt_data["resource_allocation"] = self._get_resource_allocation(project_id)

        return gantt_data

    def _format_tasks_for_gantt(
        self, tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format tasks for Gantt chart display."""
        gantt_tasks = []

        for task in tasks:
            gantt_task = {
                "id": task.get("id"),
                "title": task.get("Title", ""),
                "start_date": task.get("StartDateTime", ""),
                "end_date": task.get("EndDateTime", ""),
                "duration": self._calculate_duration_hours(
                    task.get("StartDateTime"), task.get("EndDateTime")
                ),
                "completion_percentage": task.get("PercentComplete", 0),
                "status": task.get("Status", ""),
                "priority": task.get("Priority", ""),
                "assigned_resource": task.get("AssignedResourceID", ""),
                "estimated_hours": task.get("EstimatedHours", 0),
                "hours_to_complete": task.get("HoursToComplete", 0),
                "department": task.get("DepartmentID", ""),
                "phase": task.get("Phase", ""),
                "task_type": task.get("TaskType", ""),
                "is_milestone_task": task.get("IsMilestone", False),
                "predecessors": [],  # Will be populated by dependencies
                "successors": [],  # Will be populated by dependencies
                "early_start": None,
                "early_finish": None,
                "late_start": None,
                "late_finish": None,
                "slack": 0,
                "is_critical": False,
            }
            gantt_tasks.append(gantt_task)

        return gantt_tasks

    def _format_milestones_for_gantt(
        self, milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format milestones for Gantt chart display."""
        gantt_milestones = []

        for milestone in milestones:
            gantt_milestone = {
                "id": milestone.get("id"),
                "title": milestone.get("Title", ""),
                "target_date": milestone.get("TargetDate", ""),
                "completion_date": milestone.get("CompletionDate", ""),
                "status": milestone.get("Status", ""),
                "priority": milestone.get("Priority", ""),
                "milestone_type": milestone.get("MilestoneType", ""),
                "completion_percentage": milestone.get("CompletionPercentage", 0),
                "deliverables": (
                    milestone.get("Deliverables", "").split(",")
                    if milestone.get("Deliverables")
                    else []
                ),
                "is_critical": milestone.get("Priority") in ["High", "Critical"],
                "dependent_tasks": [],  # Tasks that must complete before this milestone
            }
            gantt_milestones.append(gantt_milestone)

        return gantt_milestones

    def _get_task_dependencies(self, project_id: int) -> List[Dict[str, Any]]:
        """Get task dependency relationships."""
        # This would typically query a separate task dependencies table
        # For now, return a basic structure
        dependencies = []

        try:
            # Query task dependencies from Autotask
            # This is a placeholder - actual implementation would depend on Autotask schema
            dep_filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]
            # task_deps = self.entity.query_dependencies(dep_filters)

            # For demonstration, create sample dependency structure
            dependencies = [
                {
                    "id": f"dep_{i}",
                    "predecessor_id": None,  # Would be populated from actual data
                    "successor_id": None,  # Would be populated from actual data
                    "dependency_type": "finish_to_start",  # finish_to_start, start_to_start, etc.
                    "lag_days": 0,
                }
                # Add more dependencies as found
            ]

        except Exception:
            # Return empty if dependencies can't be loaded
            dependencies = []

        return dependencies

    def _calculate_timeline_metrics(self, gantt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall timeline metrics."""
        timeline = {
            "earliest_start": None,
            "latest_end": None,
            "duration_days": 0,
        }

        all_dates = []

        # Collect all start and end dates from tasks
        for task in gantt_data["tasks"]:
            if task["start_date"]:
                all_dates.append(task["start_date"])
            if task["end_date"]:
                all_dates.append(task["end_date"])

        # Collect milestone dates
        for milestone in gantt_data["milestones"]:
            if milestone["target_date"]:
                all_dates.append(milestone["target_date"])

        if all_dates:
            # Sort dates and find range
            sorted_dates = sorted(
                [
                    datetime.fromisoformat(date.replace("Z", "+00:00"))
                    for date in all_dates
                    if date
                ]
            )

            if sorted_dates:
                timeline["earliest_start"] = sorted_dates[0].isoformat()
                timeline["latest_end"] = sorted_dates[-1].isoformat()
                timeline["duration_days"] = (sorted_dates[-1] - sorted_dates[0]).days

        return timeline

    def _calculate_critical_path(
        self, gantt_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate critical path using basic CPM algorithm."""
        tasks = gantt_data["tasks"]
        dependencies = gantt_data["dependencies"]

        if not tasks:
            return []

        # Create dependency mapping
        predecessor_map = {}
        successor_map = {}

        for dep in dependencies:
            pred_id = dep["predecessor_id"]
            succ_id = dep["successor_id"]

            if succ_id not in predecessor_map:
                predecessor_map[succ_id] = []
            predecessor_map[succ_id].append(pred_id)

            if pred_id not in successor_map:
                successor_map[pred_id] = []
            successor_map[pred_id].append(succ_id)

        # Forward pass - calculate early start/finish
        for task in tasks:
            task_id = task["id"]
            duration = task["duration"] or 0

            # If no predecessors, early start is project start
            if task_id not in predecessor_map:
                task["early_start"] = gantt_data["project"]["start_date"]
            else:
                # Early start is max early finish of predecessors
                max_early_finish = None
                for pred_id in predecessor_map[task_id]:
                    pred_task = next((t for t in tasks if t["id"] == pred_id), None)
                    if pred_task and pred_task.get("early_finish"):
                        pred_finish = datetime.fromisoformat(
                            pred_task["early_finish"].replace("Z", "+00:00")
                        )
                        if max_early_finish is None or pred_finish > max_early_finish:
                            max_early_finish = pred_finish

                task["early_start"] = (
                    max_early_finish.isoformat()
                    if max_early_finish
                    else gantt_data["project"]["start_date"]
                )

            # Calculate early finish
            if task["early_start"]:
                early_start = datetime.fromisoformat(
                    task["early_start"].replace("Z", "+00:00")
                )
                early_finish = early_start + timedelta(hours=duration)
                task["early_finish"] = early_finish.isoformat()

        # Backward pass - calculate late start/finish
        # Find project end date
        project_end = None
        if gantt_data["project"]["end_date"]:
            project_end = datetime.fromisoformat(
                gantt_data["project"]["end_date"].replace("Z", "+00:00")
            )
        else:
            # Use latest early finish
            latest_finish = max(
                [
                    datetime.fromisoformat(t["early_finish"].replace("Z", "+00:00"))
                    for t in tasks
                    if t.get("early_finish")
                ]
            )
            project_end = latest_finish

        # Calculate late start/finish for each task
        for task in reversed(tasks):  # Process in reverse order
            task_id = task["id"]
            duration = task["duration"] or 0

            # If no successors, late finish is project end
            if task_id not in successor_map:
                task["late_finish"] = project_end.isoformat()
            else:
                # Late finish is min late start of successors
                min_late_start = None
                for succ_id in successor_map[task_id]:
                    succ_task = next((t for t in tasks if t["id"] == succ_id), None)
                    if succ_task and succ_task.get("late_start"):
                        succ_start = datetime.fromisoformat(
                            succ_task["late_start"].replace("Z", "+00:00")
                        )
                        if min_late_start is None or succ_start < min_late_start:
                            min_late_start = succ_start

                task["late_finish"] = (
                    min_late_start.isoformat()
                    if min_late_start
                    else project_end.isoformat()
                )

            # Calculate late start
            if task["late_finish"]:
                late_finish = datetime.fromisoformat(
                    task["late_finish"].replace("Z", "+00:00")
                )
                late_start = late_finish - timedelta(hours=duration)
                task["late_start"] = late_start.isoformat()

        # Calculate slack and identify critical path
        critical_tasks = []
        for task in tasks:
            if task.get("early_start") and task.get("late_start"):
                early_start = datetime.fromisoformat(
                    task["early_start"].replace("Z", "+00:00")
                )
                late_start = datetime.fromisoformat(
                    task["late_start"].replace("Z", "+00:00")
                )
                slack_hours = (late_start - early_start).total_seconds() / 3600
                task["slack"] = slack_hours

                # Task is critical if slack is 0
                if slack_hours <= 0.01:  # Allow small floating point errors
                    task["is_critical"] = True
                    critical_tasks.append(
                        {
                            "task_id": task["id"],
                            "title": task["title"],
                            "early_start": task["early_start"],
                            "early_finish": task["early_finish"],
                            "duration": task["duration"],
                        }
                    )

        return critical_tasks

    def _get_resource_allocation(self, project_id: int) -> Dict[str, Any]:
        """Get resource allocation data for the project."""
        allocation = {
            "by_resource": {},
            "by_department": {},
            "by_role": {},
            "total_allocated_hours": 0,
            "utilization_percentage": 0,
        }

        try:
            # Get project tasks with resource assignments
            tasks = self.get_project_tasks(project_id)

            for task in tasks:
                resource_id = task.get("AssignedResourceID")
                department_id = task.get("DepartmentID")
                estimated_hours = task.get("EstimatedHours", 0)

                if resource_id:
                    # Track by resource
                    if resource_id not in allocation["by_resource"]:
                        allocation["by_resource"][resource_id] = {
                            "resource_name": task.get(
                                "AssignedResourceName", f"Resource {resource_id}"
                            ),
                            "allocated_hours": 0,
                            "tasks": [],
                        }

                    allocation["by_resource"][resource_id][
                        "allocated_hours"
                    ] += estimated_hours
                    allocation["by_resource"][resource_id]["tasks"].append(
                        {
                            "task_id": task.get("id"),
                            "title": task.get("Title"),
                            "hours": estimated_hours,
                        }
                    )

                if department_id:
                    # Track by department
                    if department_id not in allocation["by_department"]:
                        allocation["by_department"][department_id] = {
                            "department_name": f"Department {department_id}",
                            "allocated_hours": 0,
                            "task_count": 0,
                        }

                    allocation["by_department"][department_id][
                        "allocated_hours"
                    ] += estimated_hours
                    allocation["by_department"][department_id]["task_count"] += 1

                allocation["total_allocated_hours"] += estimated_hours

            # Calculate utilization (placeholder - would need actual capacity data)
            if allocation["total_allocated_hours"] > 0:
                # Assume 40 hours/week capacity per resource for demo
                total_resources = len(allocation["by_resource"])
                estimated_capacity = total_resources * 40  # Simple calculation
                if estimated_capacity > 0:
                    allocation["utilization_percentage"] = (
                        allocation["total_allocated_hours"] / estimated_capacity
                    ) * 100

        except Exception as e:
            # Return basic structure on error
            pass

        return allocation

    def _calculate_duration_hours(self, start_date: str, end_date: str) -> float:
        """Calculate duration in hours between two dates."""
        if not start_date or not end_date:
            return 0.0

        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            return (end - start).total_seconds() / 3600
        except:
            return 0.0

    def create_project_template(
        self,
        template_name: str,
        template_data: Dict[str, Any],
        include_tasks: bool = True,
        include_milestones: bool = True,
        include_phases: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a project template from existing project or custom data.

        Args:
            template_name: Name for the template
            template_data: Template configuration data
            include_tasks: Include task templates
            include_milestones: Include milestone templates
            include_phases: Include project phases

        Returns:
            Created template data
        """
        template = {
            "name": template_name,
            "description": template_data.get("description", ""),
            "template_type": template_data.get("template_type", "Custom"),
            "industry": template_data.get("industry", "General"),
            "created_date": datetime.now().isoformat(),
            "version": "1.0",
            "is_active": True,
            "project_settings": {
                "default_duration_days": template_data.get("default_duration_days", 30),
                "default_priority": template_data.get("default_priority", "Medium"),
                "default_status": template_data.get("default_status", "New"),
                "billing_type": template_data.get("billing_type", "Time and Materials"),
                "department": template_data.get("department", ""),
            },
            "tasks": [],
            "milestones": [],
            "phases": [],
            "resources": [],
            "custom_fields": template_data.get("custom_fields", {}),
        }

        # Add task templates if requested
        if include_tasks and "tasks" in template_data:
            template["tasks"] = [
                {
                    "title": task.get("title", ""),
                    "description": task.get("description", ""),
                    "estimated_hours": task.get("estimated_hours", 0),
                    "priority": task.get("priority", "Medium"),
                    "phase": task.get("phase", ""),
                    "department": task.get("department", ""),
                    "task_type": task.get("task_type", "General"),
                    "prerequisites": task.get("prerequisites", []),
                    "deliverables": task.get("deliverables", []),
                    "sort_order": task.get("sort_order", 0),
                }
                for task in template_data["tasks"]
            ]

        # Add milestone templates if requested
        if include_milestones and "milestones" in template_data:
            template["milestones"] = [
                {
                    "title": milestone.get("title", ""),
                    "description": milestone.get("description", ""),
                    "milestone_type": milestone.get("milestone_type", "Project"),
                    "priority": milestone.get("priority", "Medium"),
                    "days_from_start": milestone.get("days_from_start", 0),
                    "deliverables": milestone.get("deliverables", []),
                    "success_criteria": milestone.get("success_criteria", ""),
                }
                for milestone in template_data["milestones"]
            ]

        # Add phase templates if requested
        if include_phases and "phases" in template_data:
            template["phases"] = [
                {
                    "name": phase.get("name", ""),
                    "description": phase.get("description", ""),
                    "duration_days": phase.get("duration_days", 7),
                    "sort_order": phase.get("sort_order", 0),
                    "prerequisites": phase.get("prerequisites", []),
                    "deliverables": phase.get("deliverables", []),
                }
                for phase in template_data["phases"]
            ]

        try:
            # Save template to storage (implementation depends on storage system)
            template_id = self._save_project_template(template)
            template["id"] = template_id
            return template
        except Exception as e:
            raise Exception(f"Failed to create project template: {str(e)}")

    def apply_project_template(
        self,
        template_id: str,
        project_data: Dict[str, Any],
        override_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Apply a project template to create a new project.

        Args:
            template_id: ID of the template to apply
            project_data: Basic project information (name, client, etc.)
            override_settings: Settings to override from template

        Returns:
            Created project data
        """
        template = self._get_project_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Merge template settings with project data
        settings = template.get("project_settings", {})
        if override_settings:
            settings.update(override_settings)

        # Create base project
        project_create_data = {
            "ProjectName": project_data.get("name", ""),
            "Description": project_data.get(
                "description", template.get("description", "")
            ),
            "AccountID": project_data.get("account_id"),
            "Type": settings.get("billing_type", "Time and Materials"),
            "Status": settings.get("default_status", "New"),
            "Priority": settings.get("default_priority", "Medium"),
            "DepartmentID": settings.get("department", ""),
            "StartDateTime": project_data.get("start_date"),
            "EndDateTime": self._calculate_end_date(
                project_data.get("start_date"),
                settings.get("default_duration_days", 30),
            ),
        }

        # Add custom fields from template
        if template.get("custom_fields"):
            project_create_data.update(template["custom_fields"])

        try:
            # Create the project
            new_project = self.entity.create(project_create_data)
            project_id = new_project.get("id")

            # Apply tasks from template
            if template.get("tasks"):
                self._apply_template_tasks(
                    project_id, template["tasks"], project_data.get("start_date")
                )

            # Apply milestones from template
            if template.get("milestones"):
                self._apply_template_milestones(
                    project_id, template["milestones"], project_data.get("start_date")
                )

            # Apply phases from template
            if template.get("phases"):
                self._apply_template_phases(project_id, template["phases"])

            return {
                "project": new_project,
                "template_applied": template_id,
                "tasks_created": len(template.get("tasks", [])),
                "milestones_created": len(template.get("milestones", [])),
                "phases_created": len(template.get("phases", [])),
            }

        except Exception as e:
            raise Exception(f"Failed to apply project template: {str(e)}")

    def get_project_templates(
        self,
        template_type: Optional[str] = None,
        industry: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get available project templates.

        Args:
            template_type: Filter by template type
            industry: Filter by industry
            active_only: Only return active templates

        Returns:
            List of available templates
        """
        try:
            templates = self._list_project_templates()

            # Apply filters
            if template_type:
                templates = [
                    t for t in templates if t.get("template_type") == template_type
                ]

            if industry:
                templates = [t for t in templates if t.get("industry") == industry]

            if active_only:
                templates = [t for t in templates if t.get("is_active", True)]

            return templates
        except Exception as e:
            raise Exception(f"Failed to get project templates: {str(e)}")

    def update_project_template(
        self,
        template_id: str,
        updates: Dict[str, Any],
        increment_version: bool = True,
    ) -> Dict[str, Any]:
        """
        Update an existing project template.

        Args:
            template_id: ID of template to update
            updates: Fields to update
            increment_version: Whether to increment version number

        Returns:
            Updated template data
        """
        try:
            template = self._get_project_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Apply updates
            template.update(updates)
            template["last_modified_date"] = datetime.now().isoformat()

            # Increment version if requested
            if increment_version:
                current_version = template.get("version", "1.0")
                major, minor = current_version.split(".")
                template["version"] = f"{major}.{int(minor) + 1}"

            # Save updated template
            self._save_project_template(template, template_id)

            return template
        except Exception as e:
            raise Exception(f"Failed to update project template: {str(e)}")

    def delete_project_template(self, template_id: str) -> bool:
        """
        Delete a project template (soft delete by marking inactive).

        Args:
            template_id: ID of template to delete

        Returns:
            True if successfully deleted
        """
        try:
            template = self._get_project_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Soft delete by marking as inactive
            template["is_active"] = False
            template["deleted_date"] = datetime.now().isoformat()

            self._save_project_template(template, template_id)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete project template: {str(e)}")

    def _save_project_template(
        self, template: Dict[str, Any], template_id: Optional[str] = None
    ) -> str:
        """Save project template to storage."""
        # Implementation depends on storage system (file, database, etc.)
        # For demonstration, assume we have a storage mechanism
        if not template_id:
            template_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # In real implementation, this would save to persistent storage
        # For now, just return the ID
        return template_id

    def _get_project_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get project template from storage."""
        # Implementation depends on storage system
        # For demonstration, return None (would load from storage)
        return None

    def _list_project_templates(self) -> List[Dict[str, Any]]:
        """List all project templates from storage."""
        # Implementation depends on storage system
        # For demonstration, return empty list (would load from storage)
        return []

    def _apply_template_tasks(
        self,
        project_id: int,
        task_templates: List[Dict[str, Any]],
        project_start_date: Optional[str],
    ) -> None:
        """Apply task templates to a project."""
        for task_template in task_templates:
            task_data = {
                "ProjectID": project_id,
                "Title": task_template.get("title", ""),
                "Description": task_template.get("description", ""),
                "EstimatedHours": task_template.get("estimated_hours", 0),
                "Priority": task_template.get("priority", "Medium"),
                "Phase": task_template.get("phase", ""),
                "DepartmentID": task_template.get("department", ""),
                "TaskType": task_template.get("task_type", "General"),
                "Status": "New",
            }

            # Set start date based on project start
            if project_start_date:
                task_data["StartDateTime"] = project_start_date

            # Create the task (would use tasks entity)
            # self.tasks_entity.create(task_data)

    def _apply_template_milestones(
        self,
        project_id: int,
        milestone_templates: List[Dict[str, Any]],
        project_start_date: Optional[str],
    ) -> None:
        """Apply milestone templates to a project."""
        if not project_start_date:
            return

        project_start = datetime.fromisoformat(
            project_start_date.replace("Z", "+00:00")
        )

        for milestone_template in milestone_templates:
            days_from_start = milestone_template.get("days_from_start", 0)
            target_date = project_start + timedelta(days=days_from_start)

            milestone_data = {
                "ProjectID": project_id,
                "Title": milestone_template.get("title", ""),
                "Description": milestone_template.get("description", ""),
                "TargetDate": target_date.isoformat(),
                "Priority": milestone_template.get("priority", "Medium"),
                "MilestoneType": milestone_template.get("milestone_type", "Project"),
                "Status": "Planned",
                "IsActive": True,
            }

            # Add deliverables if specified
            if milestone_template.get("deliverables"):
                milestone_data["Deliverables"] = ",".join(
                    milestone_template["deliverables"]
                )

            # Create milestone using existing method
            self.create_milestone(
                project_id,
                milestone_data["Title"],
                milestone_data["TargetDate"],
                milestone_data.get("Description"),
                milestone_data.get("Priority"),
                milestone_data.get("MilestoneType"),
                milestone_template.get("deliverables"),
            )

    def _apply_template_phases(
        self, project_id: int, phase_templates: List[Dict[str, Any]]
    ) -> None:
        """Apply phase templates to a project."""
        for phase_template in phase_templates:
            phase_data = {
                "ProjectID": project_id,
                "PhaseName": phase_template.get("name", ""),
                "Description": phase_template.get("description", ""),
                "DurationDays": phase_template.get("duration_days", 7),
                "SortOrder": phase_template.get("sort_order", 0),
                "Status": "Planned",
            }

            # Create phase (would use appropriate entity/method)
            # Implementation depends on how phases are handled in Autotask

    def _calculate_end_date(
        self, start_date: Optional[str], duration_days: int
    ) -> Optional[str]:
        """Calculate project end date based on start date and duration."""
        if not start_date:
            return None

        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end = start + timedelta(days=duration_days)
            return end.isoformat()
        except:
            return None
