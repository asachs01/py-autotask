"""
ResourceRoleQueues entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ResourceRoleQueuesEntity(BaseEntity):
    """
    Handles all Resource Role Queue-related operations for the Autotask API.

    ResourceRoleQueues in Autotask represent the association between resources,
    roles, and queues, defining which resources can work on tickets or tasks
    in specific queues based on their assigned roles.
    """

    def __init__(self, client, entity_name="ResourceRoleQueues"):
        super().__init__(client, entity_name)

    def get_resource_queue_roles(
        self, resource_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all queue role assignments for a specific resource.

        Args:
            resource_id: ID of the resource
            limit: Maximum number of records to return

        Returns:
            List of resource queue role assignments

        Example:
            queues = client.resource_role_queues.get_resource_queue_roles(123)
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]
        return self.query(filters=filters, max_records=limit)

    def get_queue_resources(
        self, queue_id: int, role_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all resources assigned to work in a specific queue.

        Args:
            queue_id: ID of the queue
            role_id: Optional role ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of resource assignments for the queue
        """
        filters = [QueryFilter(field="QueueID", op="eq", value=queue_id)]

        if role_id:
            filters.append(QueryFilter(field="RoleID", op="eq", value=role_id))

        return self.query(filters=filters, max_records=limit)

    def get_role_queue_assignments(
        self, role_id: int, queue_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all queue assignments for resources with a specific role.

        Args:
            role_id: ID of the role
            queue_id: Optional queue ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of role-based queue assignments
        """
        filters = [QueryFilter(field="RoleID", op="eq", value=role_id)]

        if queue_id:
            filters.append(QueryFilter(field="QueueID", op="eq", value=queue_id))

        return self.query(filters=filters, max_records=limit)

    def get_active_queue_assignments(
        self,
        resource_id: Optional[int] = None,
        queue_id: Optional[int] = None,
        role_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all active resource role queue assignments.

        Args:
            resource_id: Optional resource ID to filter by
            queue_id: Optional queue ID to filter by
            role_id: Optional role ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of active queue assignments
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        if queue_id:
            filters.append(QueryFilter(field="QueueID", op="eq", value=queue_id))

        if role_id:
            filters.append(QueryFilter(field="RoleID", op="eq", value=role_id))

        return self.query(filters=filters, max_records=limit)

    def create_queue_assignment(
        self,
        resource_id: int,
        queue_id: int,
        role_id: int,
        is_default: bool = False,
        active: bool = True,
        priority_level: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new resource role queue assignment.

        Args:
            resource_id: ID of the resource
            queue_id: ID of the queue
            role_id: ID of the role
            is_default: Whether this is the default queue for the resource/role combination
            active: Whether the assignment is active
            priority_level: Optional priority level for queue processing

        Returns:
            Created assignment record

        Example:
            assignment = client.resource_role_queues.create_queue_assignment(
                resource_id=123,
                queue_id=456,
                role_id=789,
                is_default=True,
                priority_level=1
            )
        """
        data = {
            "ResourceID": resource_id,
            "QueueID": queue_id,
            "RoleID": role_id,
            "IsDefault": is_default,
            "Active": active,
        }

        if priority_level is not None:
            data["PriorityLevel"] = priority_level

        return self.create(data)

    def get_default_queue_assignments(
        self,
        resource_id: Optional[int] = None,
        role_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get default queue assignments for resources and roles.

        Args:
            resource_id: Optional resource ID to filter by
            role_id: Optional role ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of default queue assignments
        """
        filters = [QueryFilter(field="IsDefault", op="eq", value=True)]

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        if role_id:
            filters.append(QueryFilter(field="RoleID", op="eq", value=role_id))

        return self.query(filters=filters, max_records=limit)

    def bulk_assign_resources_to_queue(
        self,
        resource_ids: List[int],
        queue_id: int,
        role_id: int,
        priority_level: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Assign multiple resources to a queue with specific role.

        Args:
            resource_ids: List of resource IDs to assign
            queue_id: ID of the queue
            role_id: ID of the role
            priority_level: Optional priority level for all assignments

        Returns:
            List of created assignment records
        """
        created_records = []

        for resource_id in resource_ids:
            try:
                assignment = self.create_queue_assignment(
                    resource_id=resource_id,
                    queue_id=queue_id,
                    role_id=role_id,
                    priority_level=priority_level,
                )
                created_records.append(assignment)
            except Exception as e:
                self.logger.warning(
                    f"Failed to create queue assignment for resource {resource_id}: {e}"
                )

        return created_records

    def get_queue_capacity_analysis(
        self, queue_id: int, include_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze the capacity and resource distribution for a queue.

        Args:
            queue_id: ID of the queue to analyze
            include_inactive: Whether to include inactive assignments

        Returns:
            Dictionary with capacity analysis
        """
        filters = [QueryFilter(field="QueueID", op="eq", value=queue_id)]

        if not include_inactive:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        assignments = self.query(filters=filters)

        if not assignments:
            return {
                "queue_id": queue_id,
                "total_resources": 0,
                "by_role": {},
                "by_priority": {},
                "default_assignments": 0,
                "coverage_score": 0,
            }

        by_role = {}
        by_priority = {}
        default_count = 0

        for assignment in assignments:
            role_id = assignment.get("RoleID")
            priority = assignment.get("PriorityLevel", 0)
            is_default = assignment.get("IsDefault", False)

            # Count by role
            by_role[role_id] = by_role.get(role_id, 0) + 1

            # Count by priority
            by_priority[priority] = by_priority.get(priority, 0) + 1

            if is_default:
                default_count += 1

        # Simple coverage score based on role diversity and default assignments
        coverage_score = min(100, (len(by_role) * 20) + (default_count * 10))

        return {
            "queue_id": queue_id,
            "total_resources": len(assignments),
            "by_role": by_role,
            "by_priority": by_priority,
            "default_assignments": default_count,
            "coverage_score": coverage_score,
            "recommendations": self._generate_queue_recommendations(
                by_role, default_count
            ),
        }

    def _generate_queue_recommendations(
        self, by_role: Dict[int, int], default_count: int
    ) -> List[str]:
        """Generate recommendations for queue capacity optimization."""
        recommendations = []

        if len(by_role) < 2:
            recommendations.append(
                "Consider adding resources with different roles for better coverage"
            )

        if default_count == 0:
            recommendations.append(
                "Set default assignments for reliable queue processing"
            )

        total_resources = sum(by_role.values())
        if total_resources < 3:
            recommendations.append(
                "Queue may be understaffed - consider adding more resources"
            )
        elif total_resources > 20:
            recommendations.append(
                "Queue may be overstaffed - consider redistributing resources"
            )

        return recommendations

    def reassign_queue_priority(
        self, assignment_ids: List[int], new_priority: int
    ) -> List[Dict[str, Any]]:
        """
        Update priority levels for multiple queue assignments.

        Args:
            assignment_ids: List of assignment IDs to update
            new_priority: New priority level to set

        Returns:
            List of updated assignment records
        """
        updated_records = []

        for assignment_id in assignment_ids:
            try:
                data = {"PriorityLevel": new_priority}
                updated = self.update(assignment_id, data)
                updated_records.append(updated)
            except Exception as e:
                self.logger.warning(f"Failed to update assignment {assignment_id}: {e}")

        return updated_records

    def get_resource_workload_distribution(self, resource_id: int) -> Dict[str, Any]:
        """
        Get workload distribution analysis for a resource across queues.

        Args:
            resource_id: ID of the resource to analyze

        Returns:
            Dictionary with workload distribution data
        """
        assignments = self.get_resource_queue_roles(resource_id)

        if not assignments:
            return {
                "resource_id": resource_id,
                "total_queues": 0,
                "queue_roles": {},
                "default_queues": [],
                "priority_distribution": {},
                "workload_score": 0,
            }

        queue_roles = {}
        default_queues = []
        priority_dist = {}

        for assignment in assignments:
            queue_id = assignment.get("QueueID")
            role_id = assignment.get("RoleID")
            priority = assignment.get("PriorityLevel", 0)
            is_default = assignment.get("IsDefault", False)

            queue_roles[queue_id] = role_id

            if is_default:
                default_queues.append(queue_id)

            priority_dist[priority] = priority_dist.get(priority, 0) + 1

        # Calculate workload score based on queue count and priority distribution
        queue_count = len(assignments)
        workload_score = min(100, queue_count * 10)

        return {
            "resource_id": resource_id,
            "total_queues": queue_count,
            "queue_roles": queue_roles,
            "default_queues": default_queues,
            "priority_distribution": priority_dist,
            "workload_score": workload_score,
            "recommendations": self._generate_workload_recommendations(
                queue_count, len(default_queues)
            ),
        }

    def _generate_workload_recommendations(
        self, queue_count: int, default_count: int
    ) -> List[str]:
        """Generate recommendations for resource workload optimization."""
        recommendations = []

        if queue_count > 10:
            recommendations.append(
                "Resource may be overcommitted - consider reducing queue assignments"
            )
        elif queue_count < 2:
            recommendations.append(
                "Resource may be underutilized - consider additional queue assignments"
            )

        if default_count > queue_count / 2:
            recommendations.append(
                "Too many default assignments - consider redistributing defaults"
            )
        elif default_count == 0:
            recommendations.append(
                "No default queues - assign at least one default for reliability"
            )

        return recommendations
