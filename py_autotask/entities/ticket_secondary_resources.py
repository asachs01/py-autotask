"""
Ticket Secondary Resources entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketSecondaryResourcesEntity(BaseEntity):
    """
    Handles Ticket Secondary Resources operations for the Autotask API.

    Manages additional resources assigned to tickets beyond the primary assignee,
    enabling collaborative work, specialized support, and resource coordination
    for complex ticket resolution.
    """

    def __init__(self, client, entity_name: str = "TicketSecondaryResources"):
        super().__init__(client, entity_name)

    def assign_secondary_resource(
        self,
        ticket_id: int,
        resource_id: int,
        role_description: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Assign a secondary resource to a ticket.

        Args:
            ticket_id: ID of the ticket
            resource_id: ID of the resource to assign
            role_description: Optional description of resource's role
            estimated_hours: Estimated hours for this resource
            **kwargs: Additional fields

        Returns:
            Created secondary resource assignment data
        """
        assignment_data = {
            "TicketID": ticket_id,
            "ResourceID": resource_id,
            "IsActive": True,
            **kwargs,
        }

        if role_description:
            assignment_data["RoleDescription"] = role_description
        if estimated_hours is not None:
            assignment_data["EstimatedHours"] = estimated_hours

        return self.create(assignment_data)

    def get_secondary_resources_by_ticket(
        self,
        ticket_id: int,
        active_only: bool = True,
    ) -> EntityList:
        """
        Get all secondary resources assigned to a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            active_only: Return only active assignments

        Returns:
            List of secondary resource assignments for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        return self.query_all(filters=filters)

    def get_tickets_by_secondary_resource(
        self,
        resource_id: int,
        active_only: bool = True,
        include_completed: bool = False,
    ) -> EntityList:
        """
        Get all tickets where a resource is assigned as secondary.

        Args:
            resource_id: Resource ID to filter by
            active_only: Return only active assignments
            include_completed: Whether to include completed tickets

        Returns:
            List of secondary resource assignments for the resource
        """
        filters = [{"field": "ResourceID", "op": "eq", "value": str(resource_id)}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        results = self.query_all(filters=filters)

        if not include_completed:
            # Note: Filtering by ticket status would require joining with tickets
            # For now, return all and let caller filter by ticket status if needed
            pass

        return results

    def remove_secondary_resource(
        self,
        ticket_id: int,
        resource_id: int,
        removal_reason: Optional[str] = None,
    ) -> bool:
        """
        Remove a secondary resource assignment from a ticket.

        Args:
            ticket_id: Ticket ID
            resource_id: Resource ID to remove
            removal_reason: Optional reason for removal

        Returns:
            True if removal was successful
        """
        # Find the specific assignment record
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {"field": "ResourceID", "op": "eq", "value": str(resource_id)},
        ]

        assignments = self.query(filters=filters)

        if assignments.items:
            assignment_id = assignments.items[0]["id"]

            # Instead of deleting, mark as inactive
            update_data = {
                "id": assignment_id,
                "IsActive": False,
            }

            if removal_reason:
                update_data["RemovalReason"] = removal_reason

            updated = self.update(update_data)
            return updated is not None

        return False

    def update_resource_assignment(
        self,
        assignment_id: int,
        updates: Dict[str, Any],
    ) -> Optional[EntityDict]:
        """
        Update a secondary resource assignment.

        Args:
            assignment_id: Assignment ID
            updates: Dictionary of field updates

        Returns:
            Updated assignment record or None if failed
        """
        update_data = {"id": assignment_id, **updates}
        return self.update(update_data)

    def bulk_assign_secondary_resources(
        self,
        ticket_id: int,
        resource_assignments: List[Dict[str, Any]],
    ) -> List[EntityDict]:
        """
        Assign multiple secondary resources to a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            resource_assignments: List of resource assignment dictionaries
                Each dict should contain:
                - resource_id: ID of resource to assign
                - role_description: Optional role description
                - estimated_hours: Optional estimated hours
                - other optional fields

        Returns:
            List of created assignment records
        """
        results = []

        for assignment in resource_assignments:
            try:
                resource_assignment = self.assign_secondary_resource(
                    ticket_id=ticket_id,
                    resource_id=assignment["resource_id"],
                    role_description=assignment.get("role_description"),
                    estimated_hours=assignment.get("estimated_hours"),
                    **{
                        k: v
                        for k, v in assignment.items()
                        if k
                        not in ["resource_id", "role_description", "estimated_hours"]
                    },
                )
                results.append(resource_assignment)
            except Exception as e:
                self.logger.error(
                    f"Failed to assign secondary resource {assignment.get('resource_id')} "
                    f"to ticket {ticket_id}: {e}"
                )

        return results

    def get_resource_workload_summary(
        self,
        resource_id: int,
        include_time_entries: bool = False,
    ) -> Dict[str, Any]:
        """
        Get workload summary for a resource across all secondary assignments.

        Args:
            resource_id: Resource ID
            include_time_entries: Whether to include actual time tracking data

        Returns:
            Dictionary with resource workload information
        """
        assignments = self.get_tickets_by_secondary_resource(
            resource_id, active_only=True, include_completed=False
        )

        workload = {
            "resource_id": resource_id,
            "total_active_assignments": len(assignments),
            "total_estimated_hours": 0.0,
            "actual_hours_logged": 0.0 if include_time_entries else None,
            "assignments_by_role": {},
            "tickets": [],
        }

        for assignment in assignments:
            ticket_id = assignment.get("TicketID")
            estimated_hours = float(assignment.get("EstimatedHours", 0))
            role = assignment.get("RoleDescription", "Unspecified")

            workload["total_estimated_hours"] += estimated_hours

            # Group by role
            if role not in workload["assignments_by_role"]:
                workload["assignments_by_role"][role] = {
                    "count": 0,
                    "estimated_hours": 0.0,
                }
            workload["assignments_by_role"][role]["count"] += 1
            workload["assignments_by_role"][role]["estimated_hours"] += estimated_hours

            # Add ticket details
            ticket_info = {
                "ticket_id": ticket_id,
                "assignment_id": assignment.get("id"),
                "role_description": role,
                "estimated_hours": estimated_hours,
                "assignment_date": assignment.get("CreateDateTime"),
            }
            workload["tickets"].append(ticket_info)

        # TODO: If include_time_entries, would need to query TimeEntries
        # to get actual hours logged by this resource on these tickets

        return workload

    def get_ticket_resource_collaboration(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get collaboration overview for all resources working on a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with resource collaboration information
        """
        secondary_resources = self.get_secondary_resources_by_ticket(ticket_id)

        collaboration = {
            "ticket_id": ticket_id,
            "secondary_resource_count": len(secondary_resources),
            "total_estimated_hours": 0.0,
            "resources": [],
            "roles_represented": set(),
            "collaboration_complexity": "Low",
        }

        for assignment in secondary_resources:
            resource_info = {
                "resource_id": assignment.get("ResourceID"),
                "role_description": assignment.get("RoleDescription", "Unspecified"),
                "estimated_hours": float(assignment.get("EstimatedHours", 0)),
                "assignment_date": assignment.get("CreateDateTime"),
                "is_active": assignment.get("IsActive", False),
            }

            collaboration["resources"].append(resource_info)
            collaboration["total_estimated_hours"] += resource_info["estimated_hours"]
            collaboration["roles_represented"].add(resource_info["role_description"])

        # Determine collaboration complexity
        resource_count = len(secondary_resources)
        role_count = len(collaboration["roles_represented"])

        if resource_count == 0:
            collaboration["collaboration_complexity"] = "None"
        elif resource_count <= 2 and role_count <= 2:
            collaboration["collaboration_complexity"] = "Low"
        elif resource_count <= 4 and role_count <= 3:
            collaboration["collaboration_complexity"] = "Medium"
        else:
            collaboration["collaboration_complexity"] = "High"

        # Convert set to list for JSON serialization
        collaboration["roles_represented"] = list(collaboration["roles_represented"])

        return collaboration

    def transfer_secondary_assignment(
        self,
        assignment_id: int,
        new_resource_id: int,
        transfer_reason: str,
        preserve_role: bool = True,
    ) -> Optional[EntityDict]:
        """
        Transfer a secondary resource assignment to a different resource.

        Args:
            assignment_id: Current assignment ID
            new_resource_id: ID of new resource
            transfer_reason: Reason for transfer
            preserve_role: Whether to preserve the role description

        Returns:
            Updated assignment record or None if failed
        """
        current_assignment = self.get(assignment_id)
        if not current_assignment:
            return None

        updates = {
            "ResourceID": new_resource_id,
            "TransferReason": transfer_reason,
            "TransferDateTime": datetime.now().isoformat(),
        }

        if not preserve_role:
            updates["RoleDescription"] = "Transferred Assignment"

        return self.update_resource_assignment(assignment_id, updates)

    def get_resource_assignment_history(
        self,
        resource_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get assignment history for a resource.

        Args:
            resource_id: Resource ID
            days: Number of days to analyze

        Returns:
            Dictionary with assignment history
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get all assignments (active and inactive) for the resource
        filters = [{"field": "ResourceID", "op": "eq", "value": str(resource_id)}]
        all_assignments = self.query_all(filters=filters)

        # Filter by date range
        recent_assignments = []
        for assignment in all_assignments:
            if "CreateDateTime" in assignment:
                try:
                    create_date = datetime.fromisoformat(
                        assignment["CreateDateTime"].replace("Z", "+00:00")
                    )
                    if create_date >= start_date:
                        recent_assignments.append(assignment)
                except ValueError:
                    continue

        history = {
            "resource_id": resource_id,
            "analysis_period_days": days,
            "total_assignments": len(recent_assignments),
            "active_assignments": len(
                [a for a in recent_assignments if a.get("IsActive")]
            ),
            "completed_assignments": len(
                [a for a in recent_assignments if not a.get("IsActive")]
            ),
            "unique_tickets": len(set(a.get("TicketID") for a in recent_assignments)),
            "roles_performed": list(
                set(a.get("RoleDescription", "Unspecified") for a in recent_assignments)
            ),
            "assignments": recent_assignments,
        }

        return history

    def optimize_resource_assignments(
        self,
        ticket_id: int,
        resource_skills: Optional[Dict[int, List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze and provide optimization suggestions for resource assignments.

        Args:
            ticket_id: Ticket ID
            resource_skills: Optional mapping of resource_id to skills list

        Returns:
            Dictionary with optimization suggestions
        """
        current_assignments = self.get_secondary_resources_by_ticket(ticket_id)

        analysis = {
            "ticket_id": ticket_id,
            "current_assignments": len(current_assignments),
            "suggestions": [],
            "warnings": [],
            "efficiency_score": 100,
        }

        # Check for duplicate roles
        roles = [a.get("RoleDescription") for a in current_assignments]
        duplicate_roles = [role for role in set(roles) if roles.count(role) > 1]

        if duplicate_roles:
            analysis["warnings"].append(
                f"Duplicate roles detected: {', '.join(duplicate_roles)}"
            )
            analysis["efficiency_score"] -= 15

        # Check for over-assignment
        if len(current_assignments) > 5:
            analysis["warnings"].append(
                f"High number of secondary resources ({len(current_assignments)}) may cause coordination issues"
            )
            analysis["efficiency_score"] -= 10

        # Check estimated hours distribution
        total_hours = sum(
            float(a.get("EstimatedHours", 0)) for a in current_assignments
        )
        if total_hours > 40:
            analysis["suggestions"].append(
                "Consider breaking ticket into subtasks due to high total estimated hours"
            )

        # Skill-based suggestions (if skill data provided)
        if resource_skills:
            # This would contain logic to match resource skills with ticket requirements
            analysis["suggestions"].append(
                "Skill-based optimization requires ticket category/type analysis"
            )

        return analysis

    def get_assignment_performance_metrics(
        self,
        assignment_id: int,
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a specific assignment.

        Args:
            assignment_id: Assignment ID

        Returns:
            Dictionary with performance metrics
        """
        assignment = self.get(assignment_id)
        if not assignment:
            return {"error": f"Assignment {assignment_id} not found"}

        metrics = {
            "assignment_id": assignment_id,
            "resource_id": assignment.get("ResourceID"),
            "ticket_id": assignment.get("TicketID"),
            "estimated_hours": float(assignment.get("EstimatedHours", 0)),
            "actual_hours": 0.0,  # Would need to query TimeEntries
            "hours_variance": 0.0,
            "completion_percentage": 0.0,
            "assignment_duration_days": 0,
            "is_active": assignment.get("IsActive", False),
        }

        # Calculate assignment duration
        if "CreateDateTime" in assignment:
            try:
                create_date = datetime.fromisoformat(
                    assignment["CreateDateTime"].replace("Z", "+00:00")
                )

                end_date = datetime.now()
                if (
                    not assignment.get("IsActive")
                    and "LastModifiedDateTime" in assignment
                ):
                    end_date = datetime.fromisoformat(
                        assignment["LastModifiedDateTime"].replace("Z", "+00:00")
                    )

                duration = (end_date - create_date).days
                metrics["assignment_duration_days"] = duration
            except ValueError:
                pass

        # TODO: Query actual time entries to calculate real performance metrics

        return metrics

    def reassign_all_secondary_resources(
        self,
        from_resource_id: int,
        to_resource_id: int,
        reason: str,
        ticket_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Reassign all secondary resource assignments from one resource to another.

        Args:
            from_resource_id: Current resource ID
            to_resource_id: New resource ID
            reason: Reason for reassignment
            ticket_ids: Optional list to limit reassignment to specific tickets

        Returns:
            Dictionary with reassignment results
        """
        # Get current assignments
        current_assignments = self.get_tickets_by_secondary_resource(
            from_resource_id, active_only=True
        )

        if ticket_ids:
            current_assignments = [
                a
                for a in current_assignments
                if int(a.get("TicketID", 0)) in ticket_ids
            ]

        results = {
            "from_resource_id": from_resource_id,
            "to_resource_id": to_resource_id,
            "reason": reason,
            "total_assignments": len(current_assignments),
            "successful_reassignments": 0,
            "failed_reassignments": 0,
            "reassigned_tickets": [],
            "errors": [],
        }

        for assignment in current_assignments:
            assignment_id = int(assignment["id"])
            ticket_id = assignment.get("TicketID")

            try:
                updated = self.transfer_secondary_assignment(
                    assignment_id, to_resource_id, reason
                )

                if updated:
                    results["successful_reassignments"] += 1
                    results["reassigned_tickets"].append(ticket_id)
                else:
                    results["failed_reassignments"] += 1
                    results["errors"].append(
                        {
                            "ticket_id": ticket_id,
                            "assignment_id": assignment_id,
                            "error": "Update failed",
                        }
                    )
            except Exception as e:
                results["failed_reassignments"] += 1
                results["errors"].append(
                    {
                        "ticket_id": ticket_id,
                        "assignment_id": assignment_id,
                        "error": str(e),
                    }
                )
                self.logger.error(
                    f"Failed to reassign assignment {assignment_id} "
                    f"from resource {from_resource_id} to {to_resource_id}: {e}"
                )

        return results
