"""
TaskSecondaryResources Entity for py-autotask

This module provides the TaskSecondaryResourcesEntity class for managing
additional resource assignments on tasks in Autotask. Task Secondary Resources
allow multiple team members to be assigned to tasks beyond the primary resource.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class TaskSecondaryResourcesEntity(BaseEntity):
    """
    Manages Autotask TaskSecondaryResources - additional resource assignments for tasks.

    Task Secondary Resources enable assignment of multiple team members to tasks,
    supporting collaborative work, resource sharing, and flexible task staffing.
    They complement the primary resource assignment with additional skilled resources.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "TaskSecondaryResources"

    def assign_secondary_resource(
        self,
        task_id: int,
        resource_id: int,
        role_type: Optional[str] = None,
        assignment_date: Optional[date] = None,
        estimated_hours: Optional[float] = None,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Assign a secondary resource to a task.

        Args:
            task_id: ID of the task
            resource_id: ID of the resource to assign
            role_type: Optional role type for the assignment
            assignment_date: Date of assignment (defaults to today)
            estimated_hours: Estimated hours for this resource
            is_active: Whether the assignment is active
            **kwargs: Additional fields for the assignment

        Returns:
            Create response with new assignment ID
        """
        assignment_data = {
            "taskID": task_id,
            "resourceID": resource_id,
            "assignmentDate": (assignment_date or date.today()).isoformat(),
            "isActive": is_active,
            **kwargs,
        }

        if role_type:
            assignment_data["roleType"] = role_type
        if estimated_hours is not None:
            assignment_data["estimatedHours"] = estimated_hours

        return self.create(assignment_data)

    def get_task_secondary_resources(
        self, task_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get secondary resources assigned to a task.

        Args:
            task_id: ID of the task
            include_inactive: Whether to include inactive assignments

        Returns:
            List of secondary resource assignments
        """
        filters = [{"field": "taskID", "op": "eq", "value": str(task_id)}]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_resource_task_assignments(
        self, resource_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get task assignments for a specific resource.

        Args:
            resource_id: ID of the resource
            include_inactive: Whether to include inactive assignments

        Returns:
            List of task assignments for the resource
        """
        filters = [{"field": "resourceID", "op": "eq", "value": str(resource_id)}]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_resource_workload_analysis(
        self, resource_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Analyze workload for a resource across their task assignments.

        Args:
            resource_id: ID of the resource
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Resource workload analysis
        """
        assignments = self.get_resource_task_assignments(resource_id)

        # This would typically require joining with task data to get dates and hours
        # For now, return workload analysis structure
        total_estimated_hours = sum(
            float(assignment.get("estimatedHours", 0)) for assignment in assignments
        )

        return {
            "resource_id": resource_id,
            "analysis_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "workload_summary": {
                "total_task_assignments": len(assignments),
                "total_estimated_hours": total_estimated_hours,
                "average_hours_per_task": (
                    total_estimated_hours / len(assignments) if assignments else 0.0
                ),
                "active_assignments": len(
                    [a for a in assignments if a.get("isActive")]
                ),
            },
            "task_distribution": {
                "by_role_type": {},  # Would group by role type
                "by_priority": {},  # Would group by task priority
                "by_status": {},  # Would group by task status
            },
        }

    def bulk_assign_resources_to_task(
        self, task_id: int, resource_assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assign multiple secondary resources to a task in bulk.

        Args:
            task_id: ID of the task
            resource_assignments: List of resource assignment data
                Each should contain: resource_id, role_type, estimated_hours

        Returns:
            Summary of bulk assignment operation
        """
        results = []

        for assignment in resource_assignments:
            try:
                assignment_data = {
                    "task_id": task_id,
                    "resource_id": assignment["resource_id"],
                    **assignment,
                }

                create_result = self.assign_secondary_resource(**assignment_data)

                results.append(
                    {
                        "resource_id": assignment["resource_id"],
                        "success": True,
                        "assignment_id": create_result["item_id"],
                        "role_type": assignment.get("role_type"),
                        "estimated_hours": assignment.get("estimated_hours"),
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "resource_id": assignment.get("resource_id"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "task_id": task_id,
            "total_assignments": len(resource_assignments),
            "successful_assignments": len(successful),
            "failed_assignments": len(failed),
            "results": results,
        }

    def transfer_resource_assignments(
        self,
        from_resource_id: int,
        to_resource_id: int,
        task_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Transfer task assignments from one resource to another.

        Args:
            from_resource_id: ID of the source resource
            to_resource_id: ID of the target resource
            task_ids: Optional list of specific task IDs to transfer

        Returns:
            Transfer operation results
        """
        # Get assignments to transfer
        if task_ids:
            assignments_to_transfer = []
            for task_id in task_ids:
                task_assignments = self.query(
                    filters=[
                        {"field": "taskID", "op": "eq", "value": str(task_id)},
                        {
                            "field": "resourceID",
                            "op": "eq",
                            "value": str(from_resource_id),
                        },
                        {"field": "isActive", "op": "eq", "value": "true"},
                    ]
                ).items
                assignments_to_transfer.extend(task_assignments)
        else:
            assignments_to_transfer = self.get_resource_task_assignments(
                from_resource_id
            )

        transfer_results = []

        for assignment in assignments_to_transfer:
            try:
                # Update assignment to new resource
                updated_assignment = self.update(
                    {
                        "id": assignment["id"],
                        "resourceID": to_resource_id,
                        "transferDate": datetime.now().isoformat(),
                        "previousResourceID": from_resource_id,
                    }
                )

                transfer_results.append(
                    {
                        "assignment_id": assignment["id"],
                        "task_id": assignment["taskID"],
                        "success": True,
                        "transferred_hours": assignment.get("estimatedHours", 0),
                    }
                )

            except Exception as e:
                transfer_results.append(
                    {
                        "assignment_id": assignment["id"],
                        "task_id": assignment.get("taskID"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in transfer_results if r["success"]]
        failed = [r for r in transfer_results if not r["success"]]
        total_hours_transferred = sum(
            float(r.get("transferred_hours", 0)) for r in successful
        )

        return {
            "from_resource_id": from_resource_id,
            "to_resource_id": to_resource_id,
            "transfer_summary": {
                "total_assignments": len(assignments_to_transfer),
                "successful_transfers": len(successful),
                "failed_transfers": len(failed),
                "total_hours_transferred": total_hours_transferred,
            },
            "transfer_date": datetime.now().isoformat(),
            "results": transfer_results,
        }

    def get_team_collaboration_analysis(
        self,
        project_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Analyze team collaboration patterns across task assignments.

        Args:
            project_id: Optional project ID to limit analysis to
            date_from: Optional start date for analysis
            date_to: Optional end date for analysis

        Returns:
            Team collaboration analysis
        """
        filters = [{"field": "isActive", "op": "eq", "value": "true"}]

        if date_from:
            filters.append(
                {"field": "assignmentDate", "op": "gte", "value": date_from.isoformat()}
            )
        if date_to:
            filters.append(
                {"field": "assignmentDate", "op": "lte", "value": date_to.isoformat()}
            )

        assignments = self.query(filters=filters).items

        # Group assignments by task to find collaboration patterns
        task_teams = {}
        for assignment in assignments:
            task_id = assignment["taskID"]
            resource_id = assignment["resourceID"]

            if task_id not in task_teams:
                task_teams[task_id] = []
            task_teams[task_id].append(resource_id)

        # Analyze collaboration patterns
        multi_resource_tasks = {
            task_id: resources
            for task_id, resources in task_teams.items()
            if len(resources) > 1
        }

        resource_collaboration_count = {}
        for task_id, resources in multi_resource_tasks.items():
            for i, resource1 in enumerate(resources):
                for resource2 in resources[i + 1 :]:
                    pair = tuple(sorted([resource1, resource2]))
                    resource_collaboration_count[pair] = (
                        resource_collaboration_count.get(pair, 0) + 1
                    )

        return {
            "analysis_period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "project_id": project_id,
            "collaboration_metrics": {
                "total_tasks_analyzed": len(task_teams),
                "multi_resource_tasks": len(multi_resource_tasks),
                "single_resource_tasks": len(task_teams) - len(multi_resource_tasks),
                "collaboration_percentage": (
                    round(len(multi_resource_tasks) / len(task_teams) * 100, 1)
                    if task_teams
                    else 0.0
                ),
            },
            "resource_collaboration_pairs": [
                {
                    "resource_1_id": pair[0],
                    "resource_2_id": pair[1],
                    "shared_tasks_count": count,
                }
                for pair, count in sorted(
                    resource_collaboration_count.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ],
            "most_collaborative_task": (
                max(multi_resource_tasks.items(), key=lambda x: len(x[1]))[0]
                if multi_resource_tasks
                else None
            ),
        }

    def update_resource_role(
        self,
        assignment_id: int,
        new_role_type: str,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update the role type for a resource assignment.

        Args:
            assignment_id: ID of the assignment
            new_role_type: New role type
            effective_date: When the role change is effective

        Returns:
            Updated assignment data
        """
        update_data = {
            "id": assignment_id,
            "roleType": new_role_type,
            "roleChangeDate": (effective_date or date.today()).isoformat(),
        }

        return self.update(update_data)

    def get_resource_skills_coverage(self, task_id: int) -> Dict[str, Any]:
        """
        Analyze skills coverage across secondary resources assigned to a task.

        Args:
            task_id: ID of the task

        Returns:
            Skills coverage analysis
        """
        secondary_resources = self.get_task_secondary_resources(task_id)

        # This would typically require joining with resource skills data
        # For now, return skills coverage structure
        return {
            "task_id": task_id,
            "assigned_resources": [
                {
                    "resource_id": assignment["resourceID"],
                    "role_type": assignment.get("roleType"),
                    "estimated_hours": assignment.get("estimatedHours", 0),
                }
                for assignment in secondary_resources
            ],
            "skills_analysis": {
                "total_resources": len(secondary_resources),
                "unique_skills_covered": [],  # Would populate from resource skills
                "skill_gaps": [],  # Would identify missing skills
                "skill_redundancy": [],  # Would identify overlapping skills
                "recommended_skills": [],  # Would suggest additional skills needed
            },
        }

    def deactivate_assignment(
        self, assignment_id: int, deactivation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate a secondary resource assignment.

        Args:
            assignment_id: ID of the assignment
            deactivation_reason: Optional reason for deactivation

        Returns:
            Updated assignment data
        """
        update_data = {
            "id": assignment_id,
            "isActive": False,
            "deactivationDate": datetime.now().isoformat(),
        }

        if deactivation_reason:
            update_data["deactivationReason"] = deactivation_reason

        return self.update(update_data)

    def reactivate_assignment(
        self, assignment_id: int, reactivation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reactivate a deactivated secondary resource assignment.

        Args:
            assignment_id: ID of the assignment
            reactivation_reason: Optional reason for reactivation

        Returns:
            Updated assignment data
        """
        update_data = {
            "id": assignment_id,
            "isActive": True,
            "reactivationDate": datetime.now().isoformat(),
        }

        if reactivation_reason:
            update_data["reactivationReason"] = reactivation_reason

        return self.update(update_data)

    def clone_task_resource_assignments(
        self,
        source_task_id: int,
        target_task_id: int,
        resource_mapping: Optional[Dict[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Clone secondary resource assignments from one task to another.

        Args:
            source_task_id: ID of the source task
            target_task_id: ID of the target task
            resource_mapping: Optional mapping of source to target resource IDs

        Returns:
            Cloning operation results
        """
        source_assignments = self.get_task_secondary_resources(source_task_id)
        cloning_results = []

        for assignment in source_assignments:
            try:
                source_resource_id = assignment["resourceID"]
                target_resource_id = (
                    resource_mapping.get(source_resource_id, source_resource_id)
                    if resource_mapping
                    else source_resource_id
                )

                # Create new assignment for target task
                new_assignment_data = {
                    "task_id": target_task_id,
                    "resource_id": target_resource_id,
                    "role_type": assignment.get("roleType"),
                    "estimated_hours": assignment.get("estimatedHours"),
                    "assignment_date": date.today(),
                }

                create_result = self.assign_secondary_resource(**new_assignment_data)

                cloning_results.append(
                    {
                        "source_assignment_id": assignment["id"],
                        "target_assignment_id": create_result["item_id"],
                        "resource_id": target_resource_id,
                        "success": True,
                    }
                )

            except Exception as e:
                cloning_results.append(
                    {
                        "source_assignment_id": assignment["id"],
                        "resource_id": assignment["resourceID"],
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in cloning_results if r["success"]]
        failed = [r for r in cloning_results if not r["success"]]

        return {
            "source_task_id": source_task_id,
            "target_task_id": target_task_id,
            "cloning_summary": {
                "total_assignments": len(source_assignments),
                "successful_clones": len(successful),
                "failed_clones": len(failed),
            },
            "resource_mapping_used": resource_mapping,
            "results": cloning_results,
        }
