"""
Projects entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import ProjectData, QueryFilter
from .base import BaseEntity


class ProjectsEntity(BaseEntity):
    """
    Handles all Project-related operations for the Autotask API.

    Projects in Autotask represent work initiatives with defined scopes,
    timelines, and deliverables.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_project(
        self,
        project_name: str,
        account_id: int,
        project_type: int = 1,  # 1 = Fixed Price
        status: int = 1,  # 1 = New
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
            project_type: Type of project (1=Fixed Price, 2=Time & Materials, etc.)
            status: Project status (1=New, 2=In Progress, etc.)
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
