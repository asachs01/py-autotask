"""
Tasks entity for Autotask API.

This module provides the TasksEntity class for managing
task creation, assignment, and progress tracking.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class TasksEntity(BaseEntity):
    """
    Entity for managing Autotask Tasks.

    Tasks represent work items that can be assigned to resources
    with scheduling, progress tracking, and dependency management.
    """

    def __init__(self, client, entity_name="Tasks"):
        """Initialize the Tasks entity."""
        super().__init__(client, entity_name)

    def create(self, task_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new task.

        Args:
            task_data: Dictionary containing task information
                Required fields:
                - title: Task title/summary
                - description: Task description
                - projectID: ID of the associated project
                - phaseID: ID of the project phase
                - assignedResourceID: ID of the assigned resource
                - estimatedHours: Estimated hours to complete
                Optional fields:
                - startDate: Planned start date
                - endDate: Planned end date
                - status: Task status
                - priorityLevel: Priority level (1-4)
                - percentComplete: Completion percentage
                - taskCategoryID: Category ID
                - dependencies: Task dependencies
                - notes: Additional notes

        Returns:
            CreateResponse: Response containing created task data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = [
            "title",
            "description",
            "projectID",
            "phaseID",
            "assignedResourceID",
            "estimatedHours",
        ]
        self._validate_required_fields(task_data, required_fields)

        # Validate estimated hours is positive
        estimated_hours = task_data.get("estimatedHours", 0)
        if float(estimated_hours) <= 0:
            raise ValueError("Estimated hours must be positive")

        return self._create(task_data)

    def get(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task by ID.

        Args:
            task_id: The task ID

        Returns:
            Dictionary containing task data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(task_id)

    def update(self, task_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing task.

        Args:
            task_id: The task ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated task data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(task_id, update_data)

    def delete(self, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            task_id: The task ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(task_id)

    def get_by_project(
        self,
        project_id: int,
        phase_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tasks for a specific project.

        Args:
            project_id: ID of the project
            phase_id: Optional filter by project phase
            status_filter: Optional status filter ('open', 'completed', 'in_progress')
            limit: Maximum number of tasks to return

        Returns:
            List of project tasks
        """
        filters = [QueryFilter(field="projectID", op="eq", value=project_id)]

        if phase_id:
            filters.append(QueryFilter(field="phaseID", op="eq", value=phase_id))

        if status_filter:
            status_map = {
                "open": [1, 2, 3],  # New, In Progress, Waiting
                "completed": [5],  # Complete
                "in_progress": [2],  # In Progress
                "waiting": [3],  # Waiting
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="status", op="in", value=status_ids)
                    )

        return self.query(filters=filters, max_records=limit)

    def get_by_resource(
        self,
        resource_id: int,
        date_range: Optional[tuple] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tasks assigned to a specific resource.

        Args:
            resource_id: ID of the assigned resource
            date_range: Optional tuple of (start_date, end_date)
            status_filter: Optional status filter
            limit: Maximum number of tasks to return

        Returns:
            List of assigned tasks
        """
        filters = [QueryFilter(field="assignedResourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="startDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="startDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if status_filter:
            status_map = {
                "open": [1, 2, 3],
                "completed": [5],
                "in_progress": [2],
                "overdue": [1, 2, 3],  # Will filter by date separately
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="status", op="in", value=status_ids)
                    )

        tasks = self.query(filters=filters, max_records=limit)

        # Post-filter for overdue tasks
        if status_filter and status_filter.lower() == "overdue":
            now = datetime.now()
            overdue_tasks = []
            for task in tasks:
                end_date = task.get("endDate")
                if end_date:
                    try:
                        task_end = datetime.fromisoformat(
                            end_date.replace("Z", "+00:00")
                        )
                        if task_end < now:
                            overdue_tasks.append(task)
                    except ValueError:
                        pass
            return overdue_tasks

        return tasks

    def get_overdue_tasks(
        self, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all overdue tasks.

        Args:
            project_id: Optional filter by project

        Returns:
            List of overdue tasks
        """
        filters = [
            QueryFilter(field="status", op="in", value=[1, 2, 3]),  # Open statuses
            QueryFilter(field="endDate", op="lt", value=datetime.now().isoformat()),
        ]

        if project_id:
            filters.append(QueryFilter(field="projectID", op="eq", value=project_id))

        return self.query(filters=filters)

    def start_task(
        self, task_id: int, start_note: Optional[str] = None
    ) -> UpdateResponse:
        """
        Start a task (mark as in progress).

        Args:
            task_id: Task ID to start
            start_note: Optional note about starting the task

        Returns:
            Updated task data
        """
        update_data = {
            "status": 2,  # In Progress
            "actualStartDate": datetime.now().isoformat(),
            "lastActivityDate": datetime.now().isoformat(),
        }

        if start_note:
            update_data["startNote"] = start_note

        return self.update(task_id, update_data)

    def complete_task(
        self,
        task_id: int,
        completion_note: Optional[str] = None,
        actual_hours: Optional[float] = None,
    ) -> UpdateResponse:
        """
        Complete a task.

        Args:
            task_id: Task ID to complete
            completion_note: Optional completion note
            actual_hours: Actual hours worked

        Returns:
            Updated task data
        """
        update_data = {
            "status": 5,  # Complete
            "percentComplete": 100,
            "completionDate": datetime.now().isoformat(),
            "lastActivityDate": datetime.now().isoformat(),
        }

        if completion_note:
            update_data["completionNote"] = completion_note

        if actual_hours is not None:
            update_data["actualHours"] = actual_hours

        return self.update(task_id, update_data)

    def update_progress(
        self, task_id: int, percent_complete: int, progress_note: Optional[str] = None
    ) -> UpdateResponse:
        """
        Update task progress.

        Args:
            task_id: Task ID to update
            percent_complete: Completion percentage (0-100)
            progress_note: Optional progress note

        Returns:
            Updated task data
        """
        if not 0 <= percent_complete <= 100:
            raise ValueError("Percent complete must be between 0 and 100")

        update_data = {
            "percentComplete": percent_complete,
            "lastActivityDate": datetime.now().isoformat(),
        }

        # Auto-complete if 100%
        if percent_complete == 100:
            update_data["status"] = 5  # Complete
            update_data["completionDate"] = datetime.now().isoformat()
        elif percent_complete > 0:
            # Mark as in progress if not already
            task = self.get(task_id)
            if task and task.get("status", 1) == 1:  # New status
                update_data["status"] = 2  # In Progress
                update_data["actualStartDate"] = datetime.now().isoformat()

        if progress_note:
            update_data["progressNote"] = progress_note

        return self.update(task_id, update_data)

    def assign_task(
        self, task_id: int, new_resource_id: int, assignment_note: Optional[str] = None
    ) -> UpdateResponse:
        """
        Reassign a task to a different resource.

        Args:
            task_id: Task ID to reassign
            new_resource_id: ID of the new resource
            assignment_note: Optional assignment note

        Returns:
            Updated task data
        """
        update_data = {
            "assignedResourceID": new_resource_id,
            "lastAssignmentDate": datetime.now().isoformat(),
            "lastActivityDate": datetime.now().isoformat(),
        }

        if assignment_note:
            update_data["assignmentNote"] = assignment_note

        return self.update(task_id, update_data)

    def set_task_priority(self, task_id: int, priority_level: int) -> UpdateResponse:
        """
        Set task priority level.

        Args:
            task_id: Task ID to update
            priority_level: Priority level (1=Critical, 2=High, 3=Medium, 4=Low)

        Returns:
            Updated task data
        """
        if priority_level not in [1, 2, 3, 4]:
            raise ValueError(
                "Priority level must be 1 (Critical), 2 (High), 3 (Medium), or 4 (Low)"
            )

        update_data = {
            "priorityLevel": priority_level,
            "lastActivityDate": datetime.now().isoformat(),
        }

        return self.update(task_id, update_data)

    def add_task_dependency(
        self,
        task_id: int,
        predecessor_task_id: int,
        dependency_type: str = "finish_to_start",
    ) -> UpdateResponse:
        """
        Add a dependency to a task.

        Args:
            task_id: Task ID to add dependency to
            predecessor_task_id: ID of the predecessor task
            dependency_type: Type of dependency ('finish_to_start', 'start_to_start', etc.)

        Returns:
            Updated task data
        """
        task = self.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Get existing dependencies
        existing_deps = task.get("dependencies", [])
        if not isinstance(existing_deps, list):
            existing_deps = []

        # Add new dependency
        new_dependency = {
            "predecessor_id": predecessor_task_id,
            "dependency_type": dependency_type,
            "created_date": datetime.now().isoformat(),
        }

        existing_deps.append(new_dependency)

        update_data = {
            "dependencies": existing_deps,
            "lastActivityDate": datetime.now().isoformat(),
        }

        return self.update(task_id, update_data)

    def get_task_time_entries(self, task_id: int) -> List[Dict[str, Any]]:
        """
        Get time entries for a specific task.

        Args:
            task_id: Task ID to get time entries for

        Returns:
            List of time entries
        """
        filters = [QueryFilter(field="taskID", op="eq", value=task_id)]
        return self.client.query("TimeEntries", filters=filters)

    def get_task_analytics(
        self, project_id: Optional[int] = None, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get task analytics and metrics.

        Args:
            project_id: Optional filter by project
            date_range: Optional date range for analysis

        Returns:
            Dictionary with task analytics
        """
        filters = []

        if project_id:
            filters.append(QueryFilter(field="projectID", op="eq", value=project_id))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        tasks = self.query(filters=filters)

        analytics = {
            "total_tasks": len(tasks),
            "by_status": {
                "new": 0,
                "in_progress": 0,
                "waiting": 0,
                "complete": 0,
                "cancelled": 0,
            },
            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
            "completion_rate": 0,
            "avg_estimated_hours": 0,
            "avg_actual_hours": 0,
            "avg_completion_time": 0,
            "overdue_count": 0,
            "on_time_completion_rate": 0,
        }

        estimated_hours = []
        actual_hours = []
        completion_times = []
        on_time_completions = 0
        completed_tasks = 0

        status_map = {
            1: "new",
            2: "in_progress",
            3: "waiting",
            5: "complete",
            4: "cancelled",
        }

        for task in tasks:
            status_id = task.get("status", 1)
            status_name = status_map.get(status_id, "new")
            analytics["by_status"][status_name] += 1

            priority = task.get("priorityLevel", 4)
            if priority in analytics["by_priority"]:
                analytics["by_priority"][priority] += 1

            # Hours analysis
            est_hours = task.get("estimatedHours", 0)
            act_hours = task.get("actualHours", 0)

            if est_hours > 0:
                estimated_hours.append(float(est_hours))
            if act_hours > 0:
                actual_hours.append(float(act_hours))

            # Completion time analysis
            if status_id == 5:  # Complete
                completed_tasks += 1
                start_date = task.get("actualStartDate") or task.get("startDate")
                completion_date = task.get("completionDate")
                planned_end = task.get("endDate")

                if start_date and completion_date:
                    try:
                        start = datetime.fromisoformat(
                            start_date.replace("Z", "+00:00")
                        )
                        completed = datetime.fromisoformat(
                            completion_date.replace("Z", "+00:00")
                        )
                        completion_time = (
                            completed - start
                        ).total_seconds() / 3600  # Hours
                        completion_times.append(completion_time)

                        # Check if completed on time
                        if planned_end:
                            planned = datetime.fromisoformat(
                                planned_end.replace("Z", "+00:00")
                            )
                            if completed <= planned:
                                on_time_completions += 1
                    except ValueError:
                        pass

            # Overdue analysis
            end_date = task.get("endDate")
            if end_date and status_id in [1, 2, 3]:  # Open statuses
                try:
                    planned_end = datetime.fromisoformat(
                        end_date.replace("Z", "+00:00")
                    )
                    if datetime.now() > planned_end:
                        analytics["overdue_count"] += 1
                except ValueError:
                    pass

        # Calculate averages and rates
        if analytics["total_tasks"] > 0:
            analytics["completion_rate"] = (
                completed_tasks / analytics["total_tasks"]
            ) * 100

        if estimated_hours:
            analytics["avg_estimated_hours"] = sum(estimated_hours) / len(
                estimated_hours
            )

        if actual_hours:
            analytics["avg_actual_hours"] = sum(actual_hours) / len(actual_hours)

        if completion_times:
            analytics["avg_completion_time"] = sum(completion_times) / len(
                completion_times
            )

        if completed_tasks > 0:
            analytics["on_time_completion_rate"] = (
                on_time_completions / completed_tasks
            ) * 100

        return analytics

    def get_resource_workload(
        self, resource_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get workload analysis for a resource.

        Args:
            resource_id: Resource ID to analyze
            date_range: Optional date range for analysis

        Returns:
            Dictionary with workload analysis
        """
        tasks = self.get_by_resource(resource_id, date_range, status_filter="open")

        workload = {
            "resource_id": resource_id,
            "total_open_tasks": len(tasks),
            "total_estimated_hours": 0,
            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
            "by_project": {},
            "overdue_tasks": 0,
            "upcoming_deadlines": [],
            "capacity_analysis": {
                "hours_per_week": 40,  # Assuming standard work week
                "weeks_of_work": 0,
                "capacity_utilization": 0,
            },
        }

        now = datetime.now()
        one_week = now + timedelta(weeks=1)

        for task in tasks:
            estimated = task.get("estimatedHours", 0)
            priority = task.get("priorityLevel", 4)
            project_id = task.get("projectID", "Unknown")
            end_date = task.get("endDate")

            workload["total_estimated_hours"] += float(estimated)

            if priority in workload["by_priority"]:
                workload["by_priority"][priority] += 1

            # Project breakdown
            if project_id not in workload["by_project"]:
                workload["by_project"][project_id] = {
                    "task_count": 0,
                    "estimated_hours": 0,
                }
            workload["by_project"][project_id]["task_count"] += 1
            workload["by_project"][project_id]["estimated_hours"] += float(estimated)

            # Deadline analysis
            if end_date:
                try:
                    deadline = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    if deadline < now:
                        workload["overdue_tasks"] += 1
                    elif deadline <= one_week:
                        workload["upcoming_deadlines"].append(
                            {
                                "task_id": task["id"],
                                "title": task.get("title", ""),
                                "deadline": end_date,
                                "days_remaining": (deadline - now).days,
                            }
                        )
                except ValueError:
                    pass

        # Capacity analysis
        if workload["total_estimated_hours"] > 0:
            weeks_of_work = (
                workload["total_estimated_hours"]
                / workload["capacity_analysis"]["hours_per_week"]
            )
            workload["capacity_analysis"]["weeks_of_work"] = weeks_of_work

            # Simple utilization calculation (assumes all work to be done in coming weeks)
            if weeks_of_work <= 4:  # Next 4 weeks
                workload["capacity_analysis"]["capacity_utilization"] = (
                    weeks_of_work / 4
                ) * 100
            else:
                workload["capacity_analysis"][
                    "capacity_utilization"
                ] = 100  # Over capacity

        return workload

    def validate_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task data.

        Args:
            task_data: Task data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = [
            "title",
            "description",
            "projectID",
            "phaseID",
            "assignedResourceID",
            "estimatedHours",
        ]
        for field in required_fields:
            if field not in task_data or task_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate title
        title = task_data.get("title", "")
        if title:
            if len(title) < 3:
                errors.append("Task title must be at least 3 characters")
            elif len(title) > 255:
                errors.append("Task title must not exceed 255 characters")

        # Validate estimated hours
        estimated_hours = task_data.get("estimatedHours")
        if estimated_hours is not None:
            try:
                est_val = float(estimated_hours)
                if est_val <= 0:
                    errors.append("Estimated hours must be positive")
                elif est_val > 1000:
                    warnings.append(
                        "Estimated hours seems unusually high (over 1000 hours)"
                    )
            except (ValueError, TypeError):
                errors.append("Estimated hours must be a valid number")

        # Validate dates
        start_date = task_data.get("startDate")
        end_date = task_data.get("endDate")

        if start_date:
            try:
                if isinstance(start_date, str):
                    start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Start date must be a valid date")

        if end_date:
            try:
                if isinstance(end_date, str):
                    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    if start_date:
                        start_dt = datetime.fromisoformat(
                            start_date.replace("Z", "+00:00")
                        )
                        if end_dt <= start_dt:
                            errors.append("End date must be after start date")
            except ValueError:
                errors.append("End date must be a valid date")

        # Validate percent complete
        percent_complete = task_data.get("percentComplete")
        if percent_complete is not None:
            try:
                percent_val = int(percent_complete)
                if not 0 <= percent_val <= 100:
                    errors.append("Percent complete must be between 0 and 100")
            except (ValueError, TypeError):
                errors.append("Percent complete must be a valid integer")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
