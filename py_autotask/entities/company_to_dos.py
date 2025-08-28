"""
CompanyToDos entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyToDosEntity(BaseEntity):
    """
    Handles all Company To-Do-related operations for the Autotask API.

    Company To-Dos in Autotask represent action items, reminders, and tasks
    associated with company records that need to be completed.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company_todo(
        self,
        company_id: int,
        title: str,
        description: Optional[str] = None,
        assigned_resource_id: Optional[int] = None,
        due_date: Optional[str] = None,
        priority: int = 3,  # Medium priority by default
        is_completed: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company to-do item.

        Args:
            company_id: ID of the company
            title: Title of the to-do item
            description: Optional detailed description
            assigned_resource_id: ID of resource assigned to complete the to-do
            due_date: Optional due date (ISO format)
            priority: Priority level (1=High, 2=Medium, 3=Low)
            is_completed: Whether the to-do is already completed
            **kwargs: Additional to-do fields

        Returns:
            Created company to-do data
        """
        todo_data = {
            "CompanyID": company_id,
            "Title": title,
            "Priority": priority,
            "IsCompleted": is_completed,
            **kwargs,
        }

        if description:
            todo_data["Description"] = description
        if assigned_resource_id:
            todo_data["AssignedResourceID"] = assigned_resource_id
        if due_date:
            todo_data["DueDate"] = due_date

        return self.create(todo_data)

    def get_company_todos(
        self,
        company_id: int,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all to-do items for a specific company.

        Args:
            company_id: ID of the company
            include_completed: Whether to include completed to-dos
            limit: Maximum number of to-dos to return

        Returns:
            List of company to-dos
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if not include_completed:
            filters.append(QueryFilter(field="IsCompleted", op="eq", value=False))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_todos_by_assignee(
        self,
        resource_id: int,
        company_id: Optional[int] = None,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get to-do items assigned to a specific resource.

        Args:
            resource_id: ID of the assigned resource
            company_id: Optional company ID to filter by
            include_completed: Whether to include completed to-dos
            limit: Maximum number of to-dos to return

        Returns:
            List of to-dos assigned to the resource
        """
        filters = [QueryFilter(field="AssignedResourceID", op="eq", value=resource_id)]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        if not include_completed:
            filters.append(QueryFilter(field="IsCompleted", op="eq", value=False))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_todos_by_priority(
        self,
        priority: int,
        company_id: Optional[int] = None,
        include_completed: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get to-do items filtered by priority level.

        Args:
            priority: Priority level to filter by (1=High, 2=Medium, 3=Low)
            company_id: Optional company ID to filter by
            include_completed: Whether to include completed to-dos
            limit: Maximum number of to-dos to return

        Returns:
            List of to-dos matching the priority
        """
        filters = [QueryFilter(field="Priority", op="eq", value=priority)]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        if not include_completed:
            filters.append(QueryFilter(field="IsCompleted", op="eq", value=False))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_overdue_todos(
        self,
        company_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get overdue to-do items.

        Args:
            company_id: Optional company ID to filter by
            limit: Maximum number of to-dos to return

        Returns:
            List of overdue to-dos
        """
        from datetime import datetime

        current_date = datetime.now().isoformat()

        filters = [
            QueryFilter(field="IsCompleted", op="eq", value=False),
            QueryFilter(field="DueDate", op="lt", value=current_date),
            QueryFilter(field="DueDate", op="isNotNull", value=None),
        ]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_todos_due_today(
        self,
        company_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get to-do items due today.

        Args:
            company_id: Optional company ID to filter by
            limit: Maximum number of to-dos to return

        Returns:
            List of to-dos due today
        """
        from datetime import datetime, timedelta

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        filters = [
            QueryFilter(field="IsCompleted", op="eq", value=False),
            QueryFilter(field="DueDate", op="gte", value=today_start.isoformat()),
            QueryFilter(field="DueDate", op="lt", value=today_end.isoformat()),
        ]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def complete_todo(self, todo_id: int) -> Dict[str, Any]:
        """
        Mark a to-do item as completed.

        Args:
            todo_id: ID of to-do to complete

        Returns:
            Updated to-do data
        """
        from datetime import datetime

        return self.update_by_id(
            todo_id,
            {
                "IsCompleted": True,
                "CompletedDate": datetime.now().isoformat(),
            },
        )

    def reopen_todo(self, todo_id: int) -> Dict[str, Any]:
        """
        Reopen a completed to-do item.

        Args:
            todo_id: ID of to-do to reopen

        Returns:
            Updated to-do data
        """
        return self.update_by_id(
            todo_id,
            {
                "IsCompleted": False,
                "CompletedDate": None,
            },
        )

    def update_todo_due_date(self, todo_id: int, new_due_date: str) -> Dict[str, Any]:
        """
        Update the due date of a to-do item.

        Args:
            todo_id: ID of to-do to update
            new_due_date: New due date (ISO format)

        Returns:
            Updated to-do data
        """
        return self.update_by_id(todo_id, {"DueDate": new_due_date})

    def reassign_todo(self, todo_id: int, new_assignee_id: int) -> Dict[str, Any]:
        """
        Reassign a to-do item to a different resource.

        Args:
            todo_id: ID of to-do to reassign
            new_assignee_id: ID of new assigned resource

        Returns:
            Updated to-do data
        """
        return self.update_by_id(todo_id, {"AssignedResourceID": new_assignee_id})

    def update_todo_priority(self, todo_id: int, new_priority: int) -> Dict[str, Any]:
        """
        Update the priority of a to-do item.

        Args:
            todo_id: ID of to-do to update
            new_priority: New priority level (1=High, 2=Medium, 3=Low)

        Returns:
            Updated to-do data
        """
        return self.update_by_id(todo_id, {"Priority": new_priority})

    def bulk_complete_todos(self, todo_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Mark multiple to-do items as completed in bulk.

        Args:
            todo_ids: List of to-do IDs to complete

        Returns:
            List of updated to-do data
        """
        from datetime import datetime

        completed_date = datetime.now().isoformat()

        update_data = [
            {
                "id": todo_id,
                "IsCompleted": True,
                "CompletedDate": completed_date,
            }
            for todo_id in todo_ids
        ]
        return self.batch_update(update_data)

    def get_todo_summary(self, company_id: int) -> Dict[str, Any]:
        """
        Get a summary of to-do items for a company.

        Args:
            company_id: ID of the company

        Returns:
            Dictionary with to-do summary statistics
        """
        all_todos = self.get_company_todos(company_id, include_completed=True)

        completed_todos = [t for t in all_todos if t.get("IsCompleted")]
        pending_todos = [t for t in all_todos if not t.get("IsCompleted")]

        overdue_todos = self.get_overdue_todos(company_id)
        due_today_todos = self.get_todos_due_today(company_id)

        return {
            "company_id": company_id,
            "total_todos": len(all_todos),
            "completed_todos": len(completed_todos),
            "pending_todos": len(pending_todos),
            "overdue_todos": len(overdue_todos),
            "due_today_todos": len(due_today_todos),
            "completion_rate": (
                len(completed_todos) / len(all_todos) * 100 if all_todos else 0
            ),
        }
