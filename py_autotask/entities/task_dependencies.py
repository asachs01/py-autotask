"""
Task Dependencies entity for Autotask API.

This module provides the TaskDependenciesEntity class for managing
task relationships, dependency chains, critical path analysis, and scheduling constraints.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, EntityDict, UpdateResponse
from .base import BaseEntity

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of task dependencies supported."""

    FINISH_TO_START = "FS"  # Default: successor starts after predecessor finishes
    START_TO_START = "SS"  # Successor starts when predecessor starts
    FINISH_TO_FINISH = "FF"  # Successor finishes when predecessor finishes
    START_TO_FINISH = "SF"  # Successor finishes when predecessor starts (rare)


class DependencyStatus(Enum):
    """Status of dependency constraints."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    VIOLATED = "violated"
    PENDING = "pending"


class TaskDependenciesEntity(BaseEntity):
    """
    Handles all Task Dependency-related operations for the Autotask API.

    Task dependencies manage relationships between tasks to ensure proper
    sequencing and dependency tracking in project execution.
    """

    def __init__(self, client, entity_name="TaskDependencies"):
        """Initialize the Task Dependencies entity."""
        super().__init__(client, entity_name)

    def create_task_dependency(
        self,
        predecessor_task_id: int,
        successor_task_id: int,
        dependency_type: str = "finish_to_start",
        lag_time: int = 0,
        is_critical: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new task dependency.

        Args:
            predecessor_task_id: ID of the predecessor task
            successor_task_id: ID of the successor task
            dependency_type: Type of dependency (finish_to_start, start_to_start, etc.)
            lag_time: Lag time in days between tasks
            is_critical: Whether this is a critical path dependency
            **kwargs: Additional dependency fields

        Returns:
            Created task dependency data

        Example:
            dependency = client.task_dependencies.create_task_dependency(
                12345,
                12346,
                dependency_type="finish_to_start",
                lag_time=2,
                is_critical=True
            )
        """
        dependency_data = {
            "PredecessorTaskID": predecessor_task_id,
            "SuccessorTaskID": successor_task_id,
            "DependencyType": dependency_type,
            "LagTime": lag_time,
            "IsCritical": is_critical,
            **kwargs,
        }

        return self.create(dependency_data)

    def get_task_dependencies(
        self, task_id: int, direction: str = "both"  # predecessors, successors, both
    ) -> Dict[str, List[EntityDict]]:
        """
        Get dependencies for a specific task.

        Args:
            task_id: Task ID to get dependencies for
            direction: Direction of dependencies (predecessors, successors, both)

        Returns:
            Dictionary with predecessor and successor dependencies

        Example:
            deps = client.task_dependencies.get_task_dependencies(12345)
        """
        result = {"predecessors": [], "successors": []}

        if direction in ["predecessors", "both"]:
            # Get tasks that this task depends on
            pred_filters = [{"field": "SuccessorTaskID", "op": "eq", "value": task_id}]
            pred_response = self.query(filters=pred_filters)
            result["predecessors"] = (
                pred_response.items
                if hasattr(pred_response, "items")
                else pred_response
            )

        if direction in ["successors", "both"]:
            # Get tasks that depend on this task
            succ_filters = [
                {"field": "PredecessorTaskID", "op": "eq", "value": task_id}
            ]
            succ_response = self.query(filters=succ_filters)
            result["successors"] = (
                succ_response.items
                if hasattr(succ_response, "items")
                else succ_response
            )

        return result

    def get_project_dependency_graph(self, project_id: int) -> Dict[str, Any]:
        """
        Get complete dependency graph for a project.

        Args:
            project_id: Project ID to analyze

        Returns:
            Project dependency graph

        Example:
            graph = client.task_dependencies.get_project_dependency_graph(12345)
        """
        # Get all tasks for the project
        task_filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]

        try:
            tasks_response = self.client.query("Tasks", task_filters)
            tasks = (
                tasks_response.items
                if hasattr(tasks_response, "items")
                else tasks_response
            )
        except Exception:
            tasks = []

        task_ids = [task.get("id") for task in tasks if task.get("id")]

        # Get all dependencies for project tasks
        project_dependencies = []

        if task_ids:
            # Get dependencies where either predecessor or successor is in this project
            pred_filters = [
                {
                    "field": "PredecessorTaskID",
                    "op": "in",
                    "value": [str(tid) for tid in task_ids],
                }
            ]
            pred_response = self.query(filters=pred_filters)
            project_dependencies.extend(
                pred_response.items
                if hasattr(pred_response, "items")
                else pred_response
            )

            succ_filters = [
                {
                    "field": "SuccessorTaskID",
                    "op": "in",
                    "value": [str(tid) for tid in task_ids],
                }
            ]
            succ_response = self.query(filters=succ_filters)
            project_dependencies.extend(
                succ_response.items
                if hasattr(succ_response, "items")
                else succ_response
            )

        # Remove duplicates
        seen_deps = set()
        unique_dependencies = []
        for dep in project_dependencies:
            dep_key = (dep.get("PredecessorTaskID"), dep.get("SuccessorTaskID"))
            if dep_key not in seen_deps:
                seen_deps.add(dep_key)
                unique_dependencies.append(dep)

        # Build adjacency lists
        dependency_map = {}
        reverse_dependency_map = {}

        for task in tasks:
            task_id = task.get("id")
            dependency_map[task_id] = []
            reverse_dependency_map[task_id] = []

        for dep in unique_dependencies:
            pred_id = dep.get("PredecessorTaskID")
            succ_id = dep.get("SuccessorTaskID")

            if pred_id in dependency_map:
                dependency_map[pred_id].append(
                    {
                        "successor_task_id": succ_id,
                        "dependency_type": dep.get("DependencyType"),
                        "lag_time": dep.get("LagTime", 0),
                        "is_critical": dep.get("IsCritical", False),
                    }
                )

            if succ_id in reverse_dependency_map:
                reverse_dependency_map[succ_id].append(
                    {
                        "predecessor_task_id": pred_id,
                        "dependency_type": dep.get("DependencyType"),
                        "lag_time": dep.get("LagTime", 0),
                        "is_critical": dep.get("IsCritical", False),
                    }
                )

        # Find root tasks (no predecessors)
        root_tasks = [
            task_id
            for task_id in reverse_dependency_map
            if not reverse_dependency_map[task_id]
        ]

        # Find leaf tasks (no successors)
        leaf_tasks = [
            task_id for task_id in dependency_map if not dependency_map[task_id]
        ]

        return {
            "project_id": project_id,
            "total_tasks": len(tasks),
            "total_dependencies": len(unique_dependencies),
            "root_tasks": root_tasks,
            "leaf_tasks": leaf_tasks,
            "dependency_map": dependency_map,
            "reverse_dependency_map": reverse_dependency_map,
            "critical_path": self._find_critical_path(tasks, unique_dependencies),
        }

    def validate_dependency(
        self, predecessor_task_id: int, successor_task_id: int
    ) -> Dict[str, Any]:
        """
        Validate if a dependency can be created without creating cycles.

        Args:
            predecessor_task_id: ID of the predecessor task
            successor_task_id: ID of the successor task

        Returns:
            Validation result

        Example:
            validation = client.task_dependencies.validate_dependency(12345, 12346)
        """
        # Check if tasks exist
        try:
            pred_task = self.client.get("Tasks", predecessor_task_id)
            succ_task = self.client.get("Tasks", successor_task_id)
        except Exception:
            return {"is_valid": False, "error": "One or both tasks not found"}

        if not pred_task or not succ_task:
            return {"is_valid": False, "error": "One or both tasks not found"}

        # Check if tasks are in the same project
        if pred_task.get("ProjectID") != succ_task.get("ProjectID"):
            return {"is_valid": False, "error": "Tasks must be in the same project"}

        # Check if dependency already exists
        existing_deps = self.get_task_dependencies(predecessor_task_id, "successors")
        for dep in existing_deps["successors"]:
            if dep.get("SuccessorTaskID") == successor_task_id:
                return {"is_valid": False, "error": "Dependency already exists"}

        # Check for circular dependencies using DFS
        would_create_cycle = self._would_create_cycle(
            predecessor_task_id, successor_task_id, pred_task.get("ProjectID")
        )

        if would_create_cycle:
            return {"is_valid": False, "error": "Would create circular dependency"}

        return {
            "is_valid": True,
            "predecessor_task": pred_task,
            "successor_task": succ_task,
        }

    def remove_task_dependency(
        self, predecessor_task_id: int, successor_task_id: int
    ) -> bool:
        """
        Remove a dependency between two tasks.

        Args:
            predecessor_task_id: ID of the predecessor task
            successor_task_id: ID of the successor task

        Returns:
            True if dependency was removed

        Example:
            removed = client.task_dependencies.remove_task_dependency(12345, 12346)
        """
        # Find the dependency
        filters = [
            {"field": "PredecessorTaskID", "op": "eq", "value": predecessor_task_id},
            {"field": "SuccessorTaskID", "op": "eq", "value": successor_task_id},
        ]

        response = self.query(filters=filters)
        dependencies = response.items if hasattr(response, "items") else response

        if dependencies:
            dependency_id = dependencies[0].get("id")
            if dependency_id:
                return self.delete(dependency_id)

        return False

    def get_critical_path(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate the critical path for a project.

        Args:
            project_id: Project ID to analyze

        Returns:
            Critical path analysis

        Example:
            critical_path = client.task_dependencies.get_critical_path(12345)
        """
        dependency_graph = self.get_project_dependency_graph(project_id)
        critical_path = dependency_graph.get("critical_path", {})

        return {
            "project_id": project_id,
            "critical_path_length": critical_path.get("length", 0),
            "critical_tasks": critical_path.get("tasks", []),
            "total_duration": critical_path.get("duration", 0),
            "analysis_date": datetime.now().isoformat(),
        }

    def bulk_create_dependencies(
        self,
        dependencies: List[Dict[str, Any]],
        validate: bool = True,
        batch_size: int = 20,
    ) -> List[EntityDict]:
        """
        Create multiple task dependencies in batches.

        Args:
            dependencies: List of dependency data
            validate: Whether to validate each dependency
            batch_size: Number of dependencies to process per batch

        Returns:
            List of created dependency data

        Example:
            deps = [
                {
                    'predecessor_task_id': 12345,
                    'successor_task_id': 12346,
                    'dependency_type': 'finish_to_start'
                }
            ]
            results = client.task_dependencies.bulk_create_dependencies(deps)
        """
        results = []

        for i in range(0, len(dependencies), batch_size):
            batch = dependencies[i : i + batch_size]

            for dep_data in batch:
                try:
                    if validate:
                        validation = self.validate_dependency(
                            dep_data["predecessor_task_id"],
                            dep_data["successor_task_id"],
                        )

                        if not validation["is_valid"]:
                            self.logger.warning(
                                f"Skipping invalid dependency: {validation['error']}"
                            )
                            continue

                    result = self.create_task_dependency(**dep_data)
                    results.append(result)

                except Exception as e:
                    self.logger.error(f"Failed to create dependency: {e}")
                    continue

        return results

    def get_dependency_violations(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Find dependency violations in a project (tasks that started before predecessors finished).

        Args:
            project_id: Project ID to analyze

        Returns:
            List of dependency violations

        Example:
            violations = client.task_dependencies.get_dependency_violations(12345)
        """
        dependency_graph = self.get_project_dependency_graph(project_id)
        violations = []

        # Get task details
        task_filters = [{"field": "ProjectID", "op": "eq", "value": project_id}]
        try:
            tasks_response = self.client.query("Tasks", task_filters)
            tasks = (
                tasks_response.items
                if hasattr(tasks_response, "items")
                else tasks_response
            )
        except Exception:
            return violations

        # Create task lookup
        task_lookup = {task.get("id"): task for task in tasks}

        # Check each dependency
        for task_id, successors in dependency_graph["dependency_map"].items():
            predecessor_task = task_lookup.get(task_id)
            if not predecessor_task:
                continue

            pred_end_date = predecessor_task.get("EndDate")
            pred_actual_end = predecessor_task.get("CompletedDate")

            for successor_info in successors:
                successor_task_id = successor_info["successor_task_id"]
                successor_task = task_lookup.get(successor_task_id)

                if not successor_task:
                    continue

                succ_start_date = successor_task.get("StartDate")
                lag_time = successor_info.get("lag_time", 0)

                # Check for violations
                violation_type = None
                violation_details = {}

                # Check if successor started before predecessor finished
                if pred_actual_end and succ_start_date:
                    try:
                        pred_end = datetime.fromisoformat(pred_actual_end).date()
                        succ_start = datetime.fromisoformat(succ_start_date).date()

                        expected_start = pred_end + timedelta(days=lag_time)

                        if succ_start < expected_start:
                            violation_type = "early_start"
                            violation_details = {
                                "expected_start": expected_start.isoformat(),
                                "actual_start": succ_start.isoformat(),
                                "days_early": (expected_start - succ_start).days,
                            }
                    except (ValueError, TypeError):
                        pass

                # Check if tasks are scheduled to overlap inappropriately
                elif pred_end_date and succ_start_date:
                    try:
                        pred_end = datetime.fromisoformat(pred_end_date).date()
                        succ_start = datetime.fromisoformat(succ_start_date).date()

                        expected_start = pred_end + timedelta(days=lag_time)

                        if succ_start < expected_start:
                            violation_type = "schedule_conflict"
                            violation_details = {
                                "expected_start": expected_start.isoformat(),
                                "scheduled_start": succ_start.isoformat(),
                                "schedule_gap": (expected_start - succ_start).days,
                            }
                    except (ValueError, TypeError):
                        pass

                if violation_type:
                    violations.append(
                        {
                            "predecessor_task_id": task_id,
                            "successor_task_id": successor_task_id,
                            "dependency_type": successor_info["dependency_type"],
                            "violation_type": violation_type,
                            "is_critical": successor_info.get("is_critical", False),
                            "details": violation_details,
                        }
                    )

        return violations

    def update_dependency_type(
        self,
        predecessor_task_id: int,
        successor_task_id: int,
        new_dependency_type: str,
        new_lag_time: Optional[int] = None,
    ) -> Optional[EntityDict]:
        """
        Update the type of an existing dependency.

        Args:
            predecessor_task_id: ID of the predecessor task
            successor_task_id: ID of the successor task
            new_dependency_type: New dependency type
            new_lag_time: Optional new lag time

        Returns:
            Updated dependency data or None if not found

        Example:
            updated = client.task_dependencies.update_dependency_type(
                12345, 12346, "start_to_start", 1
            )
        """
        # Find the dependency
        filters = [
            {"field": "PredecessorTaskID", "op": "eq", "value": predecessor_task_id},
            {"field": "SuccessorTaskID", "op": "eq", "value": successor_task_id},
        ]

        response = self.query(filters=filters)
        dependencies = response.items if hasattr(response, "items") else response

        if dependencies:
            dependency_id = dependencies[0].get("id")
            if dependency_id:
                update_data = {"DependencyType": new_dependency_type}
                if new_lag_time is not None:
                    update_data["LagTime"] = new_lag_time

                return self.update_by_id(dependency_id, update_data)

        return None

    def _would_create_cycle(
        self, predecessor_id: int, successor_id: int, project_id: int
    ) -> bool:
        """
        Check if adding a dependency would create a circular dependency.
        """
        # Get current dependency graph
        dependency_graph = self.get_project_dependency_graph(project_id)
        dependency_map = dependency_graph["dependency_map"]

        # Temporarily add the new dependency
        if predecessor_id not in dependency_map:
            dependency_map[predecessor_id] = []

        dependency_map[predecessor_id].append(
            {"successor_task_id": successor_id, "dependency_type": "finish_to_start"}
        )

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            if node in rec_stack:
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for successor_info in dependency_map.get(node, []):
                successor = successor_info["successor_task_id"]
                if has_cycle(successor):
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for node in dependency_map:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False

    def _find_critical_path(
        self, tasks: List[EntityDict], dependencies: List[EntityDict]
    ) -> Dict[str, Any]:
        """
        Find the critical path using longest path algorithm.
        """
        if not tasks:
            return {"length": 0, "tasks": [], "duration": 0}

        # Create task lookup with durations
        task_lookup = {}
        for task in tasks:
            task_id = task.get("id")
            start_date = task.get("StartDate")
            end_date = task.get("EndDate")

            # Calculate duration in days
            duration = 0
            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date).date()
                    end = datetime.fromisoformat(end_date).date()
                    duration = (end - start).days + 1
                except (ValueError, TypeError):
                    duration = 1  # Default duration
            else:
                duration = task.get("EstimatedHours", 8) / 8  # Convert hours to days

            task_lookup[task_id] = {
                "task": task,
                "duration": max(1, duration),
                "earliest_start": 0,
                "earliest_finish": 0,
                "latest_start": float("inf"),
                "latest_finish": float("inf"),
            }

        # Build dependency graph
        dependency_map = {}
        reverse_deps = {}

        for task_id in task_lookup:
            dependency_map[task_id] = []
            reverse_deps[task_id] = []

        for dep in dependencies:
            pred_id = dep.get("PredecessorTaskID")
            succ_id = dep.get("SuccessorTaskID")
            lag = dep.get("LagTime", 0)

            if pred_id in dependency_map and succ_id in task_lookup:
                dependency_map[pred_id].append({"successor": succ_id, "lag": lag})
                reverse_deps[succ_id].append({"predecessor": pred_id, "lag": lag})

        # Forward pass (calculate earliest times)
        def calculate_earliest_times(task_id, visited):
            if task_id in visited:
                return task_lookup[task_id]["earliest_finish"]

            visited.add(task_id)
            task_info = task_lookup[task_id]

            max_pred_finish = 0
            for pred_info in reverse_deps[task_id]:
                pred_id = pred_info["predecessor"]
                lag = pred_info["lag"]
                pred_finish = calculate_earliest_times(pred_id, visited)
                max_pred_finish = max(max_pred_finish, pred_finish + lag)

            task_info["earliest_start"] = max_pred_finish
            task_info["earliest_finish"] = max_pred_finish + task_info["duration"]

            return task_info["earliest_finish"]

        # Calculate earliest times for all tasks
        visited = set()
        for task_id in task_lookup:
            calculate_earliest_times(task_id, visited)

        # Find project duration
        project_duration = max(
            task_lookup[task_id]["earliest_finish"] for task_id in task_lookup
        )

        # Backward pass (calculate latest times)
        for task_id in task_lookup:
            task_info = task_lookup[task_id]
            if not dependency_map[task_id]:  # Leaf node
                task_info["latest_finish"] = project_duration
                task_info["latest_start"] = project_duration - task_info["duration"]

        def calculate_latest_times(task_id, visited):
            if task_id in visited:
                return task_lookup[task_id]["latest_start"]

            visited.add(task_id)
            task_info = task_lookup[task_id]

            if task_info["latest_start"] == float("inf"):
                min_succ_start = float("inf")
                for succ_info in dependency_map[task_id]:
                    succ_id = succ_info["successor"]
                    lag = succ_info["lag"]
                    succ_start = calculate_latest_times(succ_id, visited)
                    min_succ_start = min(min_succ_start, succ_start - lag)

                if min_succ_start != float("inf"):
                    task_info["latest_finish"] = min_succ_start
                    task_info["latest_start"] = min_succ_start - task_info["duration"]

            return task_info["latest_start"]

        visited = set()
        for task_id in task_lookup:
            calculate_latest_times(task_id, visited)

        # Find critical tasks (where earliest = latest)
        critical_tasks = []
        for task_id, task_info in task_lookup.items():
            slack = task_info["latest_start"] - task_info["earliest_start"]
            if abs(slack) < 0.01:  # Account for floating point precision
                critical_tasks.append(
                    {
                        "task_id": task_id,
                        "task_name": task_info["task"].get("Title"),
                        "duration": task_info["duration"],
                        "earliest_start": task_info["earliest_start"],
                        "earliest_finish": task_info["earliest_finish"],
                    }
                )

        return {
            "length": len(critical_tasks),
            "tasks": critical_tasks,
            "duration": project_duration,
        }

    def create_dependency_template(
        self,
        template_name: str,
        dependencies: List[Dict[str, Any]],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a reusable dependency template.

        Args:
            template_name: Name for the template
            dependencies: List of dependency definitions
            description: Optional template description

        Returns:
            Template configuration
        """
        template = {
            "template_name": template_name,
            "description": description or "",
            "dependencies": dependencies,
            "created_date": datetime.now().isoformat(),
            "usage_count": 0,
        }

        # In a real implementation, this would be stored in database
        self.logger.info(f"Created dependency template: {template_name}")
        return template

    def apply_dependency_template(
        self, template: Dict[str, Any], task_mapping: Dict[str, int]
    ) -> List[CreateResponse]:
        """
        Apply a dependency template to mapped tasks.

        Args:
            template: Template configuration
            task_mapping: Mapping of template task names to actual task IDs

        Returns:
            List of created dependencies
        """
        created = []

        for dep_def in template.get("dependencies", []):
            pred_name = dep_def.get("predecessor")
            succ_name = dep_def.get("successor")

            if pred_name in task_mapping and succ_name in task_mapping:
                try:
                    result = self.create_task_dependency(
                        predecessor_task_id=task_mapping[pred_name],
                        successor_task_id=task_mapping[succ_name],
                        dependency_type=dep_def.get(
                            "dependency_type", "finish_to_start"
                        ),
                        lag_time=dep_def.get("lag_time", 0),
                    )
                    created.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to apply template dependency: {e}")

        return created

    def activate_dependencies_bulk(
        self, dependency_ids: List[int]
    ) -> List[UpdateResponse]:
        """
        Activate multiple dependencies in bulk.

        Args:
            dependency_ids: List of dependency IDs to activate

        Returns:
            List of update responses
        """
        results = []
        for dep_id in dependency_ids:
            try:
                result = self.update_by_id(dep_id, {"is_active": True})
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to activate dependency {dep_id}: {e}")

        return results

    def deactivate_dependencies_bulk(
        self, dependency_ids: List[int]
    ) -> List[UpdateResponse]:
        """
        Deactivate multiple dependencies in bulk.

        Args:
            dependency_ids: List of dependency IDs to deactivate

        Returns:
            List of update responses
        """
        results = []
        for dep_id in dependency_ids:
            try:
                result = self.update_by_id(dep_id, {"is_active": False})
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to deactivate dependency {dep_id}: {e}")

        return results

    def clone_project_dependencies(
        self,
        source_project_id: int,
        target_project_id: int,
        task_mapping: Optional[Dict[int, int]] = None,
    ) -> List[CreateResponse]:
        """
        Clone dependencies from one project to another.

        Args:
            source_project_id: Source project ID
            target_project_id: Target project ID
            task_mapping: Optional mapping of source to target task IDs

        Returns:
            List of created dependencies
        """
        # Get source project dependency graph
        source_graph = self.get_project_dependency_graph(source_project_id)

        if not task_mapping:
            # Auto-generate mapping based on task order/position
            task_mapping = self._generate_task_mapping(
                source_project_id, target_project_id
            )

        created = []
        dependency_map = source_graph.get("dependency_map", {})

        for pred_task_id, successors in dependency_map.items():
            if pred_task_id not in task_mapping:
                continue

            for succ_info in successors:
                succ_task_id = succ_info["successor_task_id"]
                if succ_task_id not in task_mapping:
                    continue

                try:
                    result = self.create_task_dependency(
                        predecessor_task_id=task_mapping[pred_task_id],
                        successor_task_id=task_mapping[succ_task_id],
                        dependency_type=succ_info.get(
                            "dependency_type", "finish_to_start"
                        ),
                        lag_time=succ_info.get("lag_time", 0),
                        is_critical=succ_info.get("is_critical", False),
                    )
                    created.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to clone dependency: {e}")

        return created

    def get_dependency_impact_analysis(
        self, task_id: int, change_duration: float
    ) -> Dict[str, Any]:
        """
        Analyze impact of changing a task's duration on dependent tasks.

        Args:
            task_id: Task ID to analyze
            change_duration: Duration change in hours (positive or negative)

        Returns:
            Impact analysis results
        """
        # Get task details
        task = self.client.entities.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        project_id = task.get("projectID")
        if not project_id:
            return {"error": "Project ID not found for task"}

        # Get dependency chain
        forward_chain = self.get_dependency_chain(task_id, "forward", max_depth=20)
        _ = self.get_dependency_chain(task_id, "backward", max_depth=20)

        impact = {
            "task_id": task_id,
            "duration_change": change_duration,
            "analysis_date": datetime.now().isoformat(),
            "directly_impacted": len(forward_chain),
            "indirectly_impacted": 0,
            "critical_path_affected": False,
            "schedule_slip_days": 0,
            "affected_tasks": [],
            "mitigation_suggestions": [],
        }

        # Check if task is on critical path
        critical_path = self.get_critical_path(project_id)
        critical_task_ids = {
            t["task_id"] for t in critical_path.get("critical_tasks", [])
        }

        if task_id in critical_task_ids:
            impact["critical_path_affected"] = True
            impact["schedule_slip_days"] = (
                abs(change_duration) / 8
            )  # Convert hours to days

        # Analyze affected tasks
        all_affected = set()
        for chain_task in forward_chain:
            affected_id = chain_task["task_id"]
            all_affected.add(affected_id)

            impact["affected_tasks"].append(
                {
                    "task_id": affected_id,
                    "task_title": chain_task["task_title"],
                    "dependency_depth": chain_task["depth"],
                    "is_critical": affected_id in critical_task_ids,
                }
            )

        impact["indirectly_impacted"] = len(all_affected)

        # Generate mitigation suggestions
        if impact["critical_path_affected"]:
            impact["mitigation_suggestions"].extend(
                [
                    "Consider fast-tracking parallel activities",
                    "Review resource allocation for critical tasks",
                    "Assess scope reduction opportunities",
                ]
            )

        if impact["schedule_slip_days"] > 5:
            impact["mitigation_suggestions"].append(
                "Major schedule impact - consider project timeline revision"
            )

        return impact

    def get_dependency_health_score(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate a health score for project dependencies.

        Args:
            project_id: Project ID to analyze

        Returns:
            Dependency health score and metrics
        """
        dependency_graph = self.get_project_dependency_graph(project_id)
        violations = self.get_dependency_violations(project_id)

        total_deps = dependency_graph.get("total_dependencies", 0)
        violation_count = len(violations)

        # Calculate base health score
        if total_deps == 0:
            health_score = 100
        else:
            violation_rate = violation_count / total_deps
            health_score = max(0, 100 - (violation_rate * 100))

        # Adjust for complexity factors
        complexity_penalty = 0
        max_depth = 0

        for task_id in dependency_graph.get("dependency_map", {}):
            chain = self.get_dependency_chain(task_id, "forward", max_depth=10)
            if chain:
                depth = max(item["depth"] for item in chain)
                max_depth = max(max_depth, depth)

        if max_depth > 10:
            complexity_penalty = min(20, (max_depth - 10) * 2)

        # Adjust for circular dependencies
        circular_penalty = 0
        # Check for potential circular dependencies

        final_score = max(0, health_score - complexity_penalty - circular_penalty)

        return {
            "project_id": project_id,
            "health_score": round(final_score, 2),
            "total_dependencies": total_deps,
            "violations": violation_count,
            "max_dependency_depth": max_depth,
            "complexity_penalty": complexity_penalty,
            "circular_penalty": circular_penalty,
            "assessment_date": datetime.now().isoformat(),
            "health_category": self._categorize_health_score(final_score),
            "recommendations": self._generate_health_recommendations(
                final_score, violations
            ),
        }

    def update_dependency_lag_bulk(
        self, updates: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Update lag times for multiple dependencies in bulk.

        Args:
            updates: List of update dictionaries with dependency_id and new_lag_time

        Returns:
            List of update responses
        """
        results = []

        for update in updates:
            dependency_id = update.get("dependency_id")
            new_lag_time = update.get("new_lag_time")

            if dependency_id is not None and new_lag_time is not None:
                try:
                    result = self.update_by_id(
                        dependency_id, {"lag_time": new_lag_time}
                    )
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update lag for dependency {dependency_id}: {e}"
                    )

        return results

    def get_dependency_bottlenecks(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Identify dependency bottlenecks in a project.

        Args:
            project_id: Project ID to analyze

        Returns:
            List of potential bottlenecks
        """
        dependency_graph = self.get_project_dependency_graph(project_id)
        bottlenecks = []

        # Analyze each task's dependency count
        dependency_map = dependency_graph.get("dependency_map", {})
        reverse_map = dependency_graph.get("reverse_dependency_map", {})

        for task_id in dependency_map:
            successor_count = len(dependency_map.get(task_id, []))
            predecessor_count = len(reverse_map.get(task_id, []))

            # Identify bottlenecks based on high fan-out or fan-in
            if successor_count > 3 or predecessor_count > 3:
                try:
                    task = self.client.entities.tasks.get(task_id)
                    bottlenecks.append(
                        {
                            "task_id": task_id,
                            "task_title": task.get("title", "") if task else "",
                            "successor_count": successor_count,
                            "predecessor_count": predecessor_count,
                            "bottleneck_type": (
                                "fan_out" if successor_count > 3 else "fan_in"
                            ),
                            "risk_level": (
                                "high"
                                if max(successor_count, predecessor_count) > 5
                                else "medium"
                            ),
                        }
                    )
                except Exception:
                    pass

        # Sort by risk level and dependency count
        bottlenecks.sort(
            key=lambda x: (
                0 if x["risk_level"] == "high" else 1,
                -(x["successor_count"] + x["predecessor_count"]),
            )
        )

        return bottlenecks

    def generate_dependency_matrix(self, project_id: int) -> Dict[str, Any]:
        """
        Generate a dependency structure matrix (DSM).

        Args:
            project_id: Project ID to analyze

        Returns:
            Dependency structure matrix data
        """
        # Get all project tasks
        task_filters = [{"field": "projectID", "op": "eq", "value": project_id}]
        tasks_response = self.client.entities.tasks.query(filters=task_filters)
        tasks = tasks_response.items if hasattr(tasks_response, "items") else []

        if not tasks:
            return {"error": "No tasks found for project"}

        # Sort tasks by ID for consistent ordering
        tasks.sort(key=lambda t: t.get("id", 0))
        task_ids = [t["id"] for t in tasks]
        task_names = {t["id"]: t.get("title", f"Task {t['id']}") for t in tasks}

        # Build dependency matrix
        matrix_size = len(task_ids)
        matrix = [[0 for _ in range(matrix_size)] for _ in range(matrix_size)]

        # Get dependency graph
        dependency_graph = self.get_project_dependency_graph(project_id)
        dependency_map = dependency_graph.get("dependency_map", {})

        # Populate matrix
        for i, pred_id in enumerate(task_ids):
            for successor in dependency_map.get(pred_id, []):
                succ_id = successor["successor_task_id"]
                if succ_id in task_ids:
                    j = task_ids.index(succ_id)
                    matrix[i][j] = 1

        return {
            "project_id": project_id,
            "matrix_size": matrix_size,
            "task_ids": task_ids,
            "task_names": task_names,
            "dependency_matrix": matrix,
            "matrix_density": self._calculate_matrix_density(matrix),
            "generated_date": datetime.now().isoformat(),
        }

    def get_dependency_summary_advanced(self, project_id: int) -> Dict[str, Any]:
        """
        Get advanced dependency summary with additional metrics.

        Args:
            project_id: Project to analyze

        Returns:
            Advanced dependency statistics
        """
        basic_summary = self.get_dependency_summary(project_id)
        health_score = self.get_dependency_health_score(project_id)
        bottlenecks = self.get_dependency_bottlenecks(project_id)

        # Additional advanced metrics
        dependency_graph = self.get_project_dependency_graph(project_id)

        # Calculate network metrics
        total_tasks = basic_summary.get("total_tasks", 0)
        total_deps = basic_summary.get("total_dependencies", 0)

        network_density = (
            (total_deps / (total_tasks * (total_tasks - 1))) * 100
            if total_tasks > 1
            else 0
        )

        advanced_summary = {
            **basic_summary,
            "health_score": health_score.get("health_score", 0),
            "health_category": health_score.get("health_category", "unknown"),
            "network_density_percentage": round(network_density, 2),
            "bottleneck_count": len(bottlenecks),
            "high_risk_bottlenecks": len(
                [b for b in bottlenecks if b["risk_level"] == "high"]
            ),
            "complexity_index": self._calculate_complexity_index(dependency_graph),
            "parallel_work_potential": self._calculate_parallel_potential(
                dependency_graph
            ),
            "critical_path_flexibility": self._calculate_cp_flexibility(project_id),
        }

        return advanced_summary

    def _generate_task_mapping(
        self, source_project_id: int, target_project_id: int
    ) -> Dict[int, int]:
        """Generate automatic task mapping between projects."""
        # Simple implementation - match by position/order
        # In practice, this would be more sophisticated
        mapping = {}

        try:
            source_tasks = self.client.entities.tasks.query(
                filters=[{"field": "projectID", "op": "eq", "value": source_project_id}]
            )
            target_tasks = self.client.entities.tasks.query(
                filters=[{"field": "projectID", "op": "eq", "value": target_project_id}]
            )

            source_list = sorted(source_tasks.items, key=lambda t: t.get("id", 0))
            target_list = sorted(target_tasks.items, key=lambda t: t.get("id", 0))

            for i, (source_task, target_task) in enumerate(
                zip(source_list, target_list)
            ):
                mapping[source_task["id"]] = target_task["id"]

        except Exception as e:
            self.logger.error(f"Failed to generate task mapping: {e}")

        return mapping

    def _categorize_health_score(self, score: float) -> str:
        """Categorize health score into descriptive categories."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"

    def _generate_health_recommendations(
        self, score: float, violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on health score."""
        recommendations = []

        if score < 60:
            recommendations.append("Review and resolve dependency violations")
            recommendations.append("Consider simplifying dependency structure")

        if len(violations) > 0:
            recommendations.append("Address constraint violations immediately")

        if score < 40:
            recommendations.append(
                "Critical dependency issues require immediate attention"
            )
            recommendations.append("Consider project schedule revision")

        return recommendations

    def _calculate_matrix_density(self, matrix: List[List[int]]) -> float:
        """Calculate density of dependency matrix."""
        if not matrix:
            return 0.0

        size = len(matrix)
        total_cells = size * size
        filled_cells = sum(sum(row) for row in matrix)

        return round((filled_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0

    def _calculate_complexity_index(self, dependency_graph: Dict[str, Any]) -> float:
        """Calculate complexity index based on dependency structure."""
        total_deps = dependency_graph.get("total_dependencies", 0)
        total_tasks = dependency_graph.get("total_tasks", 0)

        if total_tasks == 0:
            return 0.0

        # Simple complexity calculation
        base_complexity = total_deps / total_tasks

        # Adjust for depth
        max_depth = dependency_graph.get("max_dependency_depth", 0)
        depth_factor = min(2.0, max_depth / 10)

        return round(base_complexity * (1 + depth_factor), 2)

    def _calculate_parallel_potential(self, dependency_graph: Dict[str, Any]) -> float:
        """Calculate potential for parallel work execution."""
        dependency_map = dependency_graph.get("dependency_map", {})
        reverse_map = dependency_graph.get("reverse_dependency_map", {})

        # Count tasks that can potentially run in parallel
        independent_tasks = 0
        for task_id in dependency_map:
            if not reverse_map.get(task_id, []):  # No predecessors
                independent_tasks += 1

        total_tasks = dependency_graph.get("total_tasks", 0)
        if total_tasks == 0:
            return 0.0

        return round((independent_tasks / total_tasks) * 100, 2)

    def _calculate_cp_flexibility(self, project_id: int) -> float:
        """Calculate critical path flexibility."""
        critical_path = self.get_critical_path(project_id)
        critical_tasks = critical_path.get("critical_tasks", [])

        dependency_graph = self.get_project_dependency_graph(project_id)
        total_tasks = dependency_graph.get("total_tasks", 0)

        if total_tasks == 0:
            return 0.0

        non_critical_ratio = (total_tasks - len(critical_tasks)) / total_tasks
        return round(non_critical_ratio * 100, 2)
