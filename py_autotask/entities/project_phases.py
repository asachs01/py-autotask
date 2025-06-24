"""
Project Phases entity for Autotask API operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ProjectPhasesEntity(BaseEntity):
    """
    Handles all Project Phase-related operations for the Autotask API.

    Project phases represent distinct stages or phases within a project,
    allowing for better organization and milestone tracking.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_project_phase(
        self,
        phase_name: str,
        project_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new project phase.

        Args:
            phase_name: Name of the project phase
            project_id: ID of the associated project
            start_date: Phase start date (ISO format)
            end_date: Phase end date (ISO format)
            description: Phase description
            estimated_hours: Estimated hours for the phase
            **kwargs: Additional phase fields

        Returns:
            Created project phase data

        Example:
            phase = client.project_phases.create_project_phase(
                "Development Phase",
                12345,
                start_date="2024-01-01",
                end_date="2024-03-31",
                estimated_hours=320.0
            )
        """
        phase_data = {"Name": phase_name, "ProjectID": project_id, **kwargs}

        if start_date:
            phase_data["StartDate"] = start_date
        if end_date:
            phase_data["EndDate"] = end_date
        if description:
            phase_data["Description"] = description
        if estimated_hours is not None:
            phase_data["EstimatedHours"] = estimated_hours

        return self.create(phase_data)

    def get_project_phases(
        self, project_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all phases for a specific project.

        Args:
            project_id: Project ID to filter by
            active_only: Whether to return only active phases
            limit: Maximum number of phases to return

        Returns:
            List of project phases

        Example:
            phases = client.project_phases.get_project_phases(12345)
        """
        filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_phases_by_status(
        self, status: str, project_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get phases by their status.

        Args:
            status: Phase status ('not_started', 'in_progress', 'completed', 'on_hold')
            project_id: Optional project filter
            limit: Maximum number of phases to return

        Returns:
            List of phases with the specified status

        Example:
            active_phases = client.project_phases.get_phases_by_status('in_progress')
        """
        status_map = {"not_started": 1, "in_progress": 2, "completed": 3, "on_hold": 4}

        status_id = status_map.get(status.lower())
        if not status_id:
            raise ValueError(f"Invalid status: {status}")

        filters = [{"field": "Status", "op": "eq", "value": status_id}]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_overdue_phases(
        self, project_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get phases that are past their end date.

        Args:
            project_id: Optional project filter
            limit: Maximum number of phases to return

        Returns:
            List of overdue phases

        Example:
            overdue = client.project_phases.get_overdue_phases()
        """
        filters = [
            {"field": "EndDate", "op": "lt", "value": datetime.now().isoformat()},
            {"field": "Status", "op": "ne", "value": 3},  # Not completed
        ]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def update_phase_status(
        self, phase_id: int, status: str, status_note: Optional[str] = None
    ) -> EntityDict:
        """
        Update a phase's status.

        Args:
            phase_id: ID of phase to update
            status: New status ('not_started', 'in_progress', 'completed', 'on_hold')
            status_note: Optional status change note

        Returns:
            Updated phase data

        Example:
            updated_phase = client.project_phases.update_phase_status(
                12345, 'completed', 'All deliverables completed'
            )
        """
        status_map = {"not_started": 1, "in_progress": 2, "completed": 3, "on_hold": 4}

        status_id = status_map.get(status.lower())
        if not status_id:
            raise ValueError(f"Invalid status: {status}")

        update_data = {"Status": status_id}

        if status_note:
            update_data["StatusNote"] = status_note

        if status.lower() == "completed":
            update_data["CompletedDate"] = datetime.now().isoformat()

        return self.update_by_id(phase_id, update_data)

    def get_phase_milestones(self, phase_id: int) -> List[EntityDict]:
        """
        Get all milestones for a specific phase.

        Args:
            phase_id: ID of the phase

        Returns:
            List of phase milestones

        Example:
            milestones = client.project_phases.get_phase_milestones(12345)
        """
        filters = [{"field": "PhaseID", "op": "eq", "value": phase_id}]

        # Query milestones entity
        response = self.client.query("ProjectMilestones", filters)
        return response.items if hasattr(response, "items") else response

    def get_phase_summary(self, phase_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a phase including progress metrics.

        Args:
            phase_id: ID of the phase

        Returns:
            Phase summary with metrics

        Example:
            summary = client.project_phases.get_phase_summary(12345)
        """
        phase = self.get(phase_id)
        if not phase:
            return {}

        # Get associated tasks
        tasks_filters = [{"field": "PhaseID", "op": "eq", "value": phase_id}]
        tasks_response = self.client.query("Tasks", tasks_filters)
        tasks = (
            tasks_response.items if hasattr(tasks_response, "items") else tasks_response
        )

        # Calculate progress metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("Status") == 5])  # Completed
        progress_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Get time entries for the phase
        time_filters = [{"field": "PhaseID", "op": "eq", "value": phase_id}]
        time_response = self.client.query("TimeEntries", time_filters)
        time_entries = (
            time_response.items if hasattr(time_response, "items") else time_response
        )

        total_hours = sum(float(entry.get("HoursWorked", 0)) for entry in time_entries)

        return {
            "phase_id": phase_id,
            "phase_name": phase.get("Name"),
            "project_id": phase.get("ProjectID"),
            "status": phase.get("Status"),
            "start_date": phase.get("StartDate"),
            "end_date": phase.get("EndDate"),
            "estimated_hours": phase.get("EstimatedHours", 0),
            "total_hours_worked": total_hours,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percentage": round(progress_percentage, 2),
            "is_overdue": self._is_phase_overdue(phase),
            "milestones_count": len(self.get_phase_milestones(phase_id)),
        }

    def activate_phase(self, phase_id: int) -> EntityDict:
        """
        Activate a project phase.

        Args:
            phase_id: ID of phase to activate

        Returns:
            Updated phase data

        Example:
            activated_phase = client.project_phases.activate_phase(12345)
        """
        return self.update_by_id(phase_id, {"IsActive": True})

    def deactivate_phase(self, phase_id: int) -> EntityDict:
        """
        Deactivate a project phase.

        Args:
            phase_id: ID of phase to deactivate

        Returns:
            Updated phase data

        Example:
            deactivated_phase = client.project_phases.deactivate_phase(12345)
        """
        return self.update_by_id(phase_id, {"IsActive": False})

    def clone_phase(
        self,
        phase_id: int,
        new_project_id: int,
        new_name: Optional[str] = None,
        adjust_dates: bool = True,
    ) -> EntityDict:
        """
        Clone a phase to another project.

        Args:
            phase_id: ID of phase to clone
            new_project_id: Target project ID
            new_name: Optional new name for cloned phase
            adjust_dates: Whether to adjust dates to current date

        Returns:
            Created cloned phase data

        Example:
            cloned_phase = client.project_phases.clone_phase(
                12345, 67890, "Cloned Development Phase"
            )
        """
        original_phase = self.get(phase_id)
        if not original_phase:
            raise ValueError(f"Phase {phase_id} not found")

        # Prepare cloned phase data
        clone_data = {
            "Name": new_name or f"Copy of {original_phase.get('Name')}",
            "ProjectID": new_project_id,
            "Description": original_phase.get("Description"),
            "EstimatedHours": original_phase.get("EstimatedHours"),
            "IsActive": True,
        }

        # Adjust dates if requested
        if adjust_dates and original_phase.get("StartDate"):
            today = datetime.now().date()
            clone_data["StartDate"] = today.isoformat()

            if original_phase.get("EndDate"):
                original_start = datetime.fromisoformat(
                    original_phase["StartDate"]
                ).date()
                original_end = datetime.fromisoformat(original_phase["EndDate"]).date()
                duration = (original_end - original_start).days
                clone_data["EndDate"] = (today + timedelta(days=duration)).isoformat()

        return self.create(clone_data)

    def bulk_update_phases(
        self, phase_updates: List[Dict[str, Any]], batch_size: int = 50
    ) -> List[EntityDict]:
        """
        Update multiple phases in batches.

        Args:
            phase_updates: List of phase update data (must include 'id' field)
            batch_size: Number of phases to update per batch

        Returns:
            List of updated phase data

        Example:
            updates = [
                {'id': 12345, 'Status': 2},
                {'id': 12346, 'Status': 3}
            ]
            results = client.project_phases.bulk_update_phases(updates)
        """
        results = []

        for i in range(0, len(phase_updates), batch_size):
            batch = phase_updates[i : i + batch_size]

            for update in batch:
                try:
                    phase_id = update.pop("id")
                    result = self.update_by_id(phase_id, update)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to update phase {update.get('id')}: {e}")
                    continue

        return results

    def get_phases_by_date_range(
        self,
        start_date: str,
        end_date: str,
        project_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get phases within a specific date range.

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            project_id: Optional project filter
            limit: Maximum number of phases to return

        Returns:
            List of phases within the date range

        Example:
            phases = client.project_phases.get_phases_by_date_range(
                "2024-01-01", "2024-12-31"
            )
        """
        filters = [
            {"field": "StartDate", "op": "gte", "value": start_date},
            {"field": "EndDate", "op": "lte", "value": end_date},
        ]

        if project_id:
            filters.append({"field": "ProjectID", "op": "eq", "value": project_id})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_phase_resource_allocation(self, phase_id: int) -> Dict[str, Any]:
        """
        Get resource allocation information for a phase.

        Args:
            phase_id: ID of the phase

        Returns:
            Resource allocation data

        Example:
            allocation = client.project_phases.get_phase_resource_allocation(12345)
        """
        # Get tasks for the phase
        tasks_filters = [{"field": "PhaseID", "op": "eq", "value": phase_id}]
        tasks_response = self.client.query("Tasks", tasks_filters)
        tasks = (
            tasks_response.items if hasattr(tasks_response, "items") else tasks_response
        )

        # Get time entries for the phase
        time_filters = [{"field": "PhaseID", "op": "eq", "value": phase_id}]
        time_response = self.client.query("TimeEntries", time_filters)
        time_entries = (
            time_response.items if hasattr(time_response, "items") else time_response
        )

        # Calculate resource allocation
        resource_hours = {}
        for entry in time_entries:
            resource_id = entry.get("ResourceID")
            hours = float(entry.get("HoursWorked", 0))
            resource_hours[resource_id] = resource_hours.get(resource_id, 0) + hours

        return {
            "phase_id": phase_id,
            "total_tasks": len(tasks),
            "total_hours_logged": sum(resource_hours.values()),
            "resource_hours": resource_hours,
            "unique_resources": len(resource_hours),
        }

    def complete_phase(
        self, phase_id: int, completion_note: Optional[str] = None
    ) -> EntityDict:
        """
        Mark a phase as completed.

        Args:
            phase_id: ID of phase to complete
            completion_note: Optional completion note

        Returns:
            Updated phase data

        Example:
            completed_phase = client.project_phases.complete_phase(
                12345, "All phase objectives met"
            )
        """
        update_data = {
            "Status": 3,  # Completed
            "CompletedDate": datetime.now().isoformat(),
        }

        if completion_note:
            update_data["CompletionNote"] = completion_note

        return self.update_by_id(phase_id, update_data)

    def _is_phase_overdue(self, phase: EntityDict) -> bool:
        """
        Check if a phase is overdue.

        Args:
            phase: Phase data

        Returns:
            True if phase is overdue
        """
        if not phase.get("EndDate") or phase.get("Status") == 3:  # Completed
            return False

        try:
            end_date = datetime.fromisoformat(phase["EndDate"])
            return datetime.now() > end_date
        except (ValueError, TypeError):
            return False
