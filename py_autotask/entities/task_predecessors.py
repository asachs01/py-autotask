"""
TaskPredecessors Entity for py-autotask

This module provides the TaskPredecessorsEntity class for managing task
dependencies and predecessor relationships in Autotask. Task Predecessors
define the sequential order and dependencies between project tasks.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class TaskPredecessorsEntity(BaseEntity):
    """
    Manages Autotask TaskPredecessors - task dependencies and predecessor relationships.

    Task Predecessors define the sequential order and dependencies between tasks,
    enabling proper project scheduling, critical path analysis, and automated
    task flow management. They support various dependency types and constraints.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "TaskPredecessors"

    def create_task_predecessor(
        self,
        successor_task_id: int,
        predecessor_task_id: int,
        dependency_type: str = "finish_to_start",
        lag_time_days: Optional[int] = 0,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new task predecessor relationship.

        Args:
            successor_task_id: ID of the task that depends on another task
            predecessor_task_id: ID of the task that must complete first
            dependency_type: Type of dependency (finish_to_start, start_to_start, etc.)
            lag_time_days: Number of days lag between tasks
            is_active: Whether the dependency is active
            **kwargs: Additional fields for the task predecessor

        Returns:
            Create response with new task predecessor ID
        """
        predecessor_data = {
            "successorTaskID": successor_task_id,
            "predecessorTaskID": predecessor_task_id,
            "dependencyType": dependency_type,
            "lagTimeDays": lag_time_days or 0,
            "isActive": is_active,
            **kwargs,
        }

        return self.create(predecessor_data)

    def get_task_predecessors(
        self, task_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get predecessor tasks for a specific task.

        Args:
            task_id: ID of the task
            include_inactive: Whether to include inactive dependencies

        Returns:
            List of predecessor relationships for the task
        """
        filters = [{"field": "successorTaskID", "op": "eq", "value": str(task_id)}]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_task_successors(
        self, task_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get successor tasks for a specific task.

        Args:
            task_id: ID of the task
            include_inactive: Whether to include inactive dependencies

        Returns:
            List of successor relationships for the task
        """
        filters = [{"field": "predecessorTaskID", "op": "eq", "value": str(task_id)}]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_project_dependency_chain(self, project_id: int) -> Dict[str, Any]:
        """
        Get the complete dependency chain for a project.

        Args:
            project_id: ID of the project

        Returns:
            Complete dependency chain analysis
        """
        # This would typically require joining with Tasks to filter by project
        # For now, return dependency chain structure
        all_dependencies = self.query(
            filters=[{"field": "isActive", "op": "eq", "value": "true"}]
        ).items

        # Group dependencies by project (would need task data)
        project_dependencies = [
            dep
            for dep in all_dependencies
            # Would filter by project_id from task data
        ]

        return {
            "project_id": project_id,
            "total_dependencies": len(project_dependencies),
            "dependency_relationships": project_dependencies,
            "critical_path": [],  # Would calculate critical path
            "circular_dependencies": [],  # Would detect circular refs
            "orphaned_tasks": [],  # Would find tasks with no dependencies
        }

    def validate_dependency(
        self, successor_task_id: int, predecessor_task_id: int
    ) -> Dict[str, Any]:
        """
        Validate a potential task dependency for circular references and conflicts.

        Args:
            successor_task_id: ID of the successor task
            predecessor_task_id: ID of the predecessor task

        Returns:
            Validation results
        """
        validation_result = {
            "successor_task_id": successor_task_id,
            "predecessor_task_id": predecessor_task_id,
            "is_valid": True,
            "validation_issues": [],
        }

        # Check for self-dependency
        if successor_task_id == predecessor_task_id:
            validation_result["is_valid"] = False
            validation_result["validation_issues"].append(
                {
                    "type": "self_dependency",
                    "description": "A task cannot depend on itself",
                    "severity": "error",
                }
            )
            return validation_result

        # Check for circular dependencies
        if self._would_create_circular_dependency(
            successor_task_id, predecessor_task_id
        ):
            validation_result["is_valid"] = False
            validation_result["validation_issues"].append(
                {
                    "type": "circular_dependency",
                    "description": "This dependency would create a circular reference",
                    "severity": "error",
                }
            )

        # Check if dependency already exists
        existing_deps = self.get_task_predecessors(successor_task_id)
        for dep in existing_deps:
            if dep["predecessorTaskID"] == predecessor_task_id:
                validation_result["validation_issues"].append(
                    {
                        "type": "duplicate_dependency",
                        "description": "This dependency already exists",
                        "severity": "warning",
                    }
                )
                break

        return validation_result

    def _would_create_circular_dependency(
        self,
        successor_task_id: int,
        predecessor_task_id: int,
        visited: Optional[set] = None,
    ) -> bool:
        """
        Check if adding a dependency would create a circular reference.

        Args:
            successor_task_id: ID of the successor task
            predecessor_task_id: ID of the predecessor task
            visited: Set of visited task IDs (for recursion)

        Returns:
            True if circular dependency would be created
        """
        if visited is None:
            visited = set()

        if predecessor_task_id in visited:
            return True

        visited.add(predecessor_task_id)

        # Get predecessors of the predecessor task
        predecessor_deps = self.get_task_predecessors(predecessor_task_id)

        for dep in predecessor_deps:
            dep_predecessor_id = dep["predecessorTaskID"]

            # If any predecessor of the predecessor is the successor, we have a cycle
            if dep_predecessor_id == successor_task_id:
                return True

            # Recursively check for circular dependencies
            if self._would_create_circular_dependency(
                successor_task_id, dep_predecessor_id, visited.copy()
            ):
                return True

        return False

    def calculate_critical_path(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate the critical path for a project based on task dependencies.

        Args:
            project_id: ID of the project

        Returns:
            Critical path analysis results
        """
        # This would require complex scheduling calculations with task durations
        # For now, return critical path structure
        return {
            "project_id": project_id,
            "critical_path": {
                "total_duration_days": 0,
                "tasks_in_critical_path": [],
                "critical_dependencies": [],
                "project_start_date": None,
                "project_end_date": None,
            },
            "float_analysis": {"tasks_with_float": [], "tasks_without_float": []},
            "scheduling_conflicts": [],
            "recommendations": [],
        }

    def get_dependency_conflicts(
        self, project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify dependency conflicts and circular references.

        Args:
            project_id: Optional project ID to limit analysis to

        Returns:
            List of dependency conflicts
        """
        conflicts = []

        # Get all active dependencies
        all_deps = self.query(
            filters=[{"field": "isActive", "op": "eq", "value": "true"}]
        ).items

        # Check for circular dependencies
        checked_pairs = set()

        for dep in all_deps:
            successor_id = dep["successorTaskID"]
            predecessor_id = dep["predecessorTaskID"]

            pair_key = f"{successor_id}-{predecessor_id}"
            if pair_key in checked_pairs:
                continue

            checked_pairs.add(pair_key)

            if self._would_create_circular_dependency(successor_id, predecessor_id):
                conflicts.append(
                    {
                        "conflict_type": "circular_dependency",
                        "dependency_id": dep["id"],
                        "successor_task_id": successor_id,
                        "predecessor_task_id": predecessor_id,
                        "description": f"Circular dependency detected between tasks {successor_id} and {predecessor_id}",
                        "severity": "high",
                    }
                )

        return conflicts

    def remove_dependency(
        self, successor_task_id: int, predecessor_task_id: int
    ) -> Dict[str, Any]:
        """
        Remove a task dependency relationship.

        Args:
            successor_task_id: ID of the successor task
            predecessor_task_id: ID of the predecessor task

        Returns:
            Removal operation results
        """
        # Find the dependency relationship
        dependencies = self.query(
            filters=[
                {
                    "field": "successorTaskID",
                    "op": "eq",
                    "value": str(successor_task_id),
                },
                {
                    "field": "predecessorTaskID",
                    "op": "eq",
                    "value": str(predecessor_task_id),
                },
            ]
        ).items

        if not dependencies:
            return {
                "success": False,
                "error": "Dependency relationship not found",
                "successor_task_id": successor_task_id,
                "predecessor_task_id": predecessor_task_id,
            }

        dependency = dependencies[0]
        self.delete(dependency["id"])

        return {
            "success": True,
            "removed_dependency_id": dependency["id"],
            "successor_task_id": successor_task_id,
            "predecessor_task_id": predecessor_task_id,
            "removal_date": datetime.now().isoformat(),
        }

    def bulk_create_dependencies(
        self, dependency_relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple task dependencies in bulk.

        Args:
            dependency_relationships: List of dependency definitions
                Each should contain: successor_task_id, predecessor_task_id, dependency_type, lag_time_days

        Returns:
            Summary of bulk creation operation
        """
        results = []

        for relationship in dependency_relationships:
            try:
                # Validate the dependency first
                validation = self.validate_dependency(
                    relationship["successor_task_id"],
                    relationship["predecessor_task_id"],
                )

                if not validation["is_valid"]:
                    results.append(
                        {
                            "successor_task_id": relationship["successor_task_id"],
                            "predecessor_task_id": relationship["predecessor_task_id"],
                            "success": False,
                            "error": "Validation failed",
                            "validation_issues": validation["validation_issues"],
                        }
                    )
                    continue

                # Create the dependency
                create_result = self.create_task_predecessor(**relationship)

                results.append(
                    {
                        "successor_task_id": relationship["successor_task_id"],
                        "predecessor_task_id": relationship["predecessor_task_id"],
                        "success": True,
                        "dependency_id": create_result["item_id"],
                        "dependency_type": relationship.get(
                            "dependency_type", "finish_to_start"
                        ),
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "successor_task_id": relationship.get("successor_task_id"),
                        "predecessor_task_id": relationship.get("predecessor_task_id"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_relationships": len(dependency_relationships),
            "successful_creations": len(successful),
            "failed_creations": len(failed),
            "results": results,
        }

    def get_dependency_impact_analysis(self, task_id: int) -> Dict[str, Any]:
        """
        Analyze the impact of changes to a task on its dependencies.

        Args:
            task_id: ID of the task to analyze

        Returns:
            Dependency impact analysis
        """
        predecessors = self.get_task_predecessors(task_id)
        successors = self.get_task_successors(task_id)

        return {
            "analyzed_task_id": task_id,
            "dependency_summary": {
                "predecessor_count": len(predecessors),
                "successor_count": len(successors),
                "total_dependencies": len(predecessors) + len(successors),
            },
            "impact_analysis": {
                "tasks_blocking_this_task": [
                    {
                        "task_id": dep["predecessorTaskID"],
                        "dependency_type": dep["dependencyType"],
                        "lag_time_days": dep.get("lagTimeDays", 0),
                    }
                    for dep in predecessors
                ],
                "tasks_blocked_by_this_task": [
                    {
                        "task_id": dep["successorTaskID"],
                        "dependency_type": dep["dependencyType"],
                        "lag_time_days": dep.get("lagTimeDays", 0),
                    }
                    for dep in successors
                ],
                "is_critical_path_task": False,  # Would calculate based on scheduling
                "scheduling_flexibility": "unknown",  # Would calculate float time
            },
            "recommendations": [
                # Would provide scheduling recommendations
            ],
        }

    def update_dependency_lag_time(
        self, dependency_id: int, new_lag_time_days: int
    ) -> Dict[str, Any]:
        """
        Update the lag time for a task dependency.

        Args:
            dependency_id: ID of the dependency relationship
            new_lag_time_days: New lag time in days

        Returns:
            Updated dependency data
        """
        return self.update(
            {
                "id": dependency_id,
                "lagTimeDays": new_lag_time_days,
                "lastModifiedDate": datetime.now().isoformat(),
            }
        )

    def clone_project_dependencies(
        self,
        source_project_id: int,
        target_project_id: int,
        task_id_mapping: Dict[int, int],
    ) -> Dict[str, Any]:
        """
        Clone task dependencies from one project to another.

        Args:
            source_project_id: ID of the source project
            target_project_id: ID of the target project
            task_id_mapping: Mapping of source task IDs to target task IDs

        Returns:
            Cloning operation results
        """
        # This would typically require joining with tasks to filter by project
        # For now, return cloning structure
        return {
            "source_project_id": source_project_id,
            "target_project_id": target_project_id,
            "cloning_summary": {
                "dependencies_cloned": 0,
                "dependencies_skipped": 0,
                "cloning_errors": 0,
            },
            "task_mapping_used": task_id_mapping,
            "cloned_dependencies": [],
            "skipped_dependencies": [],
            "cloning_errors": [],
        }

    def deactivate_dependency(
        self, dependency_id: int, deactivation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate a task dependency without deleting it.

        Args:
            dependency_id: ID of the dependency to deactivate
            deactivation_reason: Optional reason for deactivation

        Returns:
            Updated dependency data
        """
        update_data = {
            "id": dependency_id,
            "isActive": False,
            "deactivationDate": datetime.now().isoformat(),
        }

        if deactivation_reason:
            update_data["deactivationReason"] = deactivation_reason

        return self.update(update_data)
