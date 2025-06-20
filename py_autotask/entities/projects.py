"""
Projects entity for Autotask API operations.
"""

from typing import Dict, List, Optional, Any
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
        status: int = 1,        # 1 = New
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
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
            'ProjectName': project_name,
            'AccountID': account_id,
            'Type': project_type,
            'Status': status,
            **kwargs
        }
        
        if start_date:
            project_data['StartDate'] = start_date
        if end_date:
            project_data['EndDate'] = end_date
        if description:
            project_data['Description'] = description
            
        return self.create(project_data)
    
    def get_projects_by_account(
        self, 
        account_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
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
        filters = [QueryFilter(field='AccountID', op='eq', value=account_id)]
        
        if status_filter:
            status_map = {
                'active': [1, 2, 3, 4],  # New, In Progress, On Hold, Waiting
                'completed': [5],         # Complete
                'new': [1],              # New
                'in_progress': [2],      # In Progress
                'on_hold': [3],          # On Hold
            }
            
            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(QueryFilter(field='Status', op='eq', value=status_ids[0]))
                else:
                    filters.append(QueryFilter(field='Status', op='in', value=status_ids))
        
        return self.query(filters=filters, max_records=limit)
    
    def get_projects_by_manager(
        self, 
        manager_id: int,
        include_completed: bool = False,
        limit: Optional[int] = None
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
        filters = [QueryFilter(field='ProjectManagerResourceID', op='eq', value=manager_id)]
        
        if not include_completed:
            filters.append(QueryFilter(field='Status', op='ne', value=5))  # Not Complete
        
        return self.query(filters=filters, max_records=limit)
    
    def update_project_status(
        self, 
        project_id: int, 
        status: int
    ) -> ProjectData:
        """
        Update a project's status.
        
        Args:
            project_id: ID of project to update
            status: New status ID
            
        Returns:
            Updated project data
        """
        return self.update(project_id, {'Status': status})
    
    def get_project_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of tasks for the project
        """
        filters = [QueryFilter(field='ProjectID', op='eq', value=project_id)]
        return self._client.query('Tasks', filters=filters)
    
    def get_project_time_entries(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all time entries for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of time entries for the project
        """
        filters = [QueryFilter(field='ProjectID', op='eq', value=project_id)]
        return self._client.query('TimeEntries', filters=filters) 