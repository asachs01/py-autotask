"""
Project Milestones entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ProjectMilestonesEntity(BaseEntity):
    """
    Handles all Project Milestone-related operations for the Autotask API.

    Project milestones represent key achievements and deadline tracking
    within projects and phases.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_milestone(
        self,
        title: str,
        project_id: int,
        due_date: str,
        phase_id: Optional[int] = None,
        description: Optional[str] = None,
        status: int = 1,  # 1 = Not Started
        **kwargs,
    ) -> EntityDict:
        """
        Create a new project milestone.

        Args:
            title: Milestone title
            project_id: ID of the associated project
            due_date: Milestone due date (ISO format)
            phase_id: Optional phase ID to associate with
            description: Milestone description
            status: Milestone status (1=Not Started, 2=In Progress, 3=Completed)
            **kwargs: Additional milestone fields

        Returns:
            Created milestone data

        Example:
            milestone = client.project_milestones.create_milestone(
                "Beta Release",
                12345,
                "2024-06-01",
                phase_id=67890,
                description="Beta version ready for testing"
            )
        """
        milestone_data = {
            "Title": title,
            "ProjectID": project_id,
            "DueDate": due_date,
            "Status": status,
            **kwargs,
        }

        if phase_id:
            milestone_data["PhaseID"] = phase_id
        if description:
            milestone_data["Description"] = description

        return self.create(milestone_data)

    def get_project_milestones(
        self,
        project_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all milestones for a specific project.

        Args:
            project_id: Project ID to filter by
            status_filter: Optional status filter ('not_started', 'in_progress', 'completed')
            limit: Maximum number of milestones to return

        Returns:
            List of project milestones

        Example:
            milestones = client.project_milestones.get_project_milestones(12345)
        """
        filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        if status_filter:
            status_map = {"not_started": 1, "in_progress": 2, "completed": 3}

            status_id = status_map.get(status_filter.lower())
            if status_id:
                filters.append({"field": "Status", "op": "eq", "value": status_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_phase_milestones(
        self, phase_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all milestones for a specific phase.

        Args:
            phase_id: Phase ID to filter by
            active_only: Whether to return only active milestones
            limit: Maximum number of milestones to return

        Returns:
            List of phase milestones

        Example:
            milestones = client.project_milestones.get_phase_milestones(67890)
        """
        filters = [{"field": "PhaseID", "op": "eq", "value": phase_id}]

        if active_only:
            filters.append({"field": "Status", "op": "ne", "value": 3})  # Not completed

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_overdue_milestones(
        self, project_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get milestones that are past their due date.

        Args:
            project_id: Optional project filter
            limit: Maximum number of milestones to return

        Returns:
            List of overdue milestones

        Example:
            overdue = client.project_milestones.get_overdue_milestones()
        """
        filters = [
            {"field": "DueDate", "op": "lt", "value": datetime.now().isoformat()},
            {"field": "Status", "op": "ne", "value": 3},  # Not completed
        ]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_upcoming_milestones(
        self,
        days_ahead: int = 7,
        project_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get milestones due within the next specified days.

        Args:
            days_ahead: Number of days to look ahead
            project_id: Optional project filter
            limit: Maximum number of milestones to return

        Returns:
            List of upcoming milestones

        Example:
            upcoming = client.project_milestones.get_upcoming_milestones(14)
        """
        end_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()

        filters = [
            {"field": "DueDate", "op": "gte", "value": datetime.now().isoformat()},
            {"field": "DueDate", "op": "lte", "value": end_date},
            {"field": "Status", "op": "ne", "value": 3},  # Not completed
        ]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def update_milestone_status(
        self, milestone_id: int, status: str, completion_note: Optional[str] = None
    ) -> EntityDict:
        """
        Update a milestone's status.

        Args:
            milestone_id: ID of milestone to update
            status: New status ('not_started', 'in_progress', 'completed')
            completion_note: Optional completion note

        Returns:
            Updated milestone data

        Example:
            updated = client.project_milestones.update_milestone_status(
                12345, 'completed', 'All objectives met'
            )
        """
        status_map = {"not_started": 1, "in_progress": 2, "completed": 3}

        status_id = status_map.get(status.lower())
        if not status_id:
            raise ValueError(f"Invalid status: {status}")

        update_data = {"Status": status_id}

        if status.lower() == "completed":
            update_data["CompletedDate"] = datetime.now().isoformat()
            if completion_note:
                update_data["CompletionNote"] = completion_note

        return self.update_by_id(milestone_id, update_data)

    def get_milestone_summary(self, milestone_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a milestone.

        Args:
            milestone_id: ID of the milestone

        Returns:
            Milestone summary with related data

        Example:
            summary = client.project_milestones.get_milestone_summary(12345)
        """
        milestone = self.get(milestone_id)
        if not milestone:
            return {}

        # Get related tasks
        tasks_filters = [{"field": "MilestoneID", "op": "eq", "value": milestone_id}]
        tasks_response = self.client.query("Tasks", tasks_filters)
        tasks = (
            tasks_response.items if hasattr(tasks_response, "items") else tasks_response
        )

        # Calculate completion metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("Status") == 5])  # Completed

        # Check if overdue
        is_overdue = self._is_milestone_overdue(milestone)

        return {
            "milestone_id": milestone_id,
            "title": milestone.get("Title"),
            "project_id": milestone.get("ProjectID"),
            "phase_id": milestone.get("PhaseID"),
            "status": milestone.get("Status"),
            "due_date": milestone.get("DueDate"),
            "completed_date": milestone.get("CompletedDate"),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_percentage": round(
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2
            ),
            "is_overdue": is_overdue,
            "days_until_due": self._calculate_days_until_due(milestone),
            "description": milestone.get("Description"),
        }

    def complete_milestone(
        self, milestone_id: int, completion_note: Optional[str] = None
    ) -> EntityDict:
        """
        Mark a milestone as completed.

        Args:
            milestone_id: ID of milestone to complete
            completion_note: Optional completion note

        Returns:
            Updated milestone data

        Example:
            completed = client.project_milestones.complete_milestone(
                12345, "Delivered ahead of schedule"
            )
        """
        return self.update_milestone_status(milestone_id, "completed", completion_note)

    def clone_milestone(
        self,
        milestone_id: int,
        new_project_id: int,
        new_phase_id: Optional[int] = None,
        new_title: Optional[str] = None,
        adjust_dates: bool = True,
    ) -> EntityDict:
        """
        Clone a milestone to another project or phase.

        Args:
            milestone_id: ID of milestone to clone
            new_project_id: Target project ID
            new_phase_id: Optional target phase ID
            new_title: Optional new title
            adjust_dates: Whether to adjust dates relative to today

        Returns:
            Created cloned milestone data

        Example:
            cloned = client.project_milestones.clone_milestone(
                12345, 67890, new_title="Cloned Beta Release"
            )
        """
        original = self.get(milestone_id)
        if not original:
            raise ValueError(f"Milestone {milestone_id} not found")

        clone_data = {
            "Title": new_title or f"Copy of {original.get('Title')}",
            "ProjectID": new_project_id,
            "Description": original.get("Description"),
            "Status": 1,  # Reset to Not Started
        }

        if new_phase_id:
            clone_data["PhaseID"] = new_phase_id

        # Adjust due date if requested
        if adjust_dates and original.get("DueDate"):
            try:
                datetime.fromisoformat(original["DueDate"])
                # Add 30 days as default offset
                new_due = datetime.now() + timedelta(days=30)
                clone_data["DueDate"] = new_due.isoformat()
            except (ValueError, TypeError):
                clone_data["DueDate"] = (
                    datetime.now() + timedelta(days=30)
                ).isoformat()
        elif original.get("DueDate"):
            clone_data["DueDate"] = original["DueDate"]

        return self.create(clone_data)

    def bulk_update_milestones(
        self, milestone_updates: List[Dict[str, Any]], batch_size: int = 50
    ) -> List[EntityDict]:
        """
        Update multiple milestones in batches.

        Args:
            milestone_updates: List of milestone update data (must include 'id' field)
            batch_size: Number of milestones to update per batch

        Returns:
            List of updated milestone data

        Example:
            updates = [
                {'id': 12345, 'Status': 2},
                {'id': 12346, 'Status': 3}
            ]
            results = client.project_milestones.bulk_update_milestones(updates)
        """
        results = []

        for i in range(0, len(milestone_updates), batch_size):
            batch = milestone_updates[i : i + batch_size]

            for update in batch:
                try:
                    milestone_id = update.pop("id")
                    result = self.update_by_id(milestone_id, update)
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update milestone {update.get('id')}: {e}"
                    )
                    continue

        return results

    def get_milestones_by_date_range(
        self,
        start_date: str,
        end_date: str,
        project_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get milestones due within a specific date range.

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            project_id: Optional project filter
            limit: Maximum number of milestones to return

        Returns:
            List of milestones within the date range

        Example:
            milestones = client.project_milestones.get_milestones_by_date_range(
                "2024-01-01", "2024-12-31"
            )
        """
        filters = [
            {"field": "DueDate", "op": "gte", "value": start_date},
            {"field": "DueDate", "op": "lte", "value": end_date},
        ]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_critical_milestones(
        self,
        project_id: Optional[int] = None,
        days_threshold: int = 3,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get critical milestones (overdue or due very soon).

        Args:
            project_id: Optional project filter
            days_threshold: Days ahead to consider critical
            limit: Maximum number of milestones to return

        Returns:
            List of critical milestones

        Example:
            critical = client.project_milestones.get_critical_milestones()
        """
        threshold_date = (datetime.now() + timedelta(days=days_threshold)).isoformat()

        filters = [
            {"field": "DueDate", "op": "lte", "value": threshold_date},
            {"field": "Status", "op": "ne", "value": 3},  # Not completed
        ]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_milestone_dependencies(self, milestone_id: int) -> Dict[str, Any]:
        """
        Get dependencies for a milestone (tasks and other milestones).

        Args:
            milestone_id: ID of the milestone

        Returns:
            Milestone dependencies data

        Example:
            deps = client.project_milestones.get_milestone_dependencies(12345)
        """
        # Get tasks associated with this milestone
        tasks_filters = [{"field": "MilestoneID", "op": "eq", "value": milestone_id}]
        tasks_response = self.client.query("Tasks", tasks_filters)
        tasks = (
            tasks_response.items if hasattr(tasks_response, "items") else tasks_response
        )

        # Get dependent milestones (those that depend on this one)
        dependent_filters = [
            {"field": "PredecessorMilestoneID", "op": "eq", "value": milestone_id}
        ]
        dependent_response = self.query(filters=dependent_filters)
        dependent_milestones = (
            dependent_response.items
            if hasattr(dependent_response, "items")
            else dependent_response
        )

        return {
            "milestone_id": milestone_id,
            "associated_tasks": len(tasks),
            "task_details": tasks,
            "dependent_milestones": len(dependent_milestones),
            "dependent_milestone_details": dependent_milestones,
        }

    def reschedule_milestone(
        self, milestone_id: int, new_due_date: str, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Reschedule a milestone to a new due date.

        Args:
            milestone_id: ID of milestone to reschedule
            new_due_date: New due date (ISO format)
            reason: Optional reason for rescheduling

        Returns:
            Updated milestone data

        Example:
            rescheduled = client.project_milestones.reschedule_milestone(
                12345, "2024-07-15", "Resource availability changed"
            )
        """
        update_data = {"DueDate": new_due_date}

        if reason:
            update_data["RescheduleReason"] = reason
            update_data["LastRescheduledDate"] = datetime.now().isoformat()

        return self.update_by_id(milestone_id, update_data)

    def _is_milestone_overdue(self, milestone: EntityDict) -> bool:
        """
        Check if a milestone is overdue.

        Args:
            milestone: Milestone data

        Returns:
            True if milestone is overdue
        """
        if not milestone.get("DueDate") or milestone.get("Status") == 3:  # Completed
            return False

        try:
            due_date = datetime.fromisoformat(milestone["DueDate"])
            return datetime.now() > due_date
        except (ValueError, TypeError):
            return False

    def _calculate_days_until_due(self, milestone: EntityDict) -> Optional[int]:
        """
        Calculate days until milestone is due.

        Args:
            milestone: Milestone data

        Returns:
            Days until due (negative if overdue, None if no due date)
        """
        if not milestone.get("DueDate"):
            return None

        try:
            due_date = datetime.fromisoformat(milestone["DueDate"])
            delta = due_date - datetime.now()
            return delta.days
        except (ValueError, TypeError):
            return None
