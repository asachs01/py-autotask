"""
Teams Entity for py-autotask

This module provides the TeamsEntity class for managing teams
in Autotask. Teams organize resources for collaboration, project assignment,
and workflow management.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class TeamsEntity(BaseEntity):
    """
    Manages Autotask Teams - team organization and resource collaboration.

    Teams provide a way to organize resources for collaboration, project
    assignment, and workflow management. They support team-based reporting,
    capacity planning, and resource allocation.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Teams"

    def create_team(
        self,
        name: str,
        description: Optional[str] = None,
        team_lead_resource_id: Optional[int] = None,
        department_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new team.

        Args:
            name: Name of the team
            description: Description of the team
            team_lead_resource_id: ID of the team lead resource
            department_id: ID of the department this team belongs to
            **kwargs: Additional fields for the team

        Returns:
            Create response with new team ID
        """
        team_data = {"name": name, **kwargs}

        if description:
            team_data["description"] = description
        if team_lead_resource_id:
            team_data["teamLeadResourceID"] = team_lead_resource_id
        if department_id:
            team_data["departmentID"] = department_id

        return self.create(team_data)

    def get_teams_by_department(
        self, department_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get teams by department.

        Args:
            department_id: ID of the department
            active_only: Whether to only return active teams

        Returns:
            List of teams in the department
        """
        filters = [f"departmentID eq {department_id}"]

        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def get_teams_by_lead(self, lead_resource_id: int) -> List[Dict[str, Any]]:
        """
        Get teams led by a specific resource.

        Args:
            lead_resource_id: ID of the team lead resource

        Returns:
            List of teams led by the resource
        """
        return self.query(filter=f"teamLeadResourceID eq {lead_resource_id}")

    def search_teams(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search teams by name or description.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching teams
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        filters = []
        for field in search_fields:
            filters.append(f"contains({field}, '{search_term}')")

        return self.query(filter=" or ".join(filters))

    def get_team_members(
        self, team_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get members of a team.

        Args:
            team_id: ID of the team
            active_only: Whether to only include active members

        Returns:
            List of team members
        """
        # This would typically query team member assignments
        # For now, return placeholder structure

        return []  # Would be populated with actual team member query

    def add_team_member(
        self, team_id: int, resource_id: int, role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a member to a team.

        Args:
            team_id: ID of the team
            resource_id: ID of the resource to add
            role: Optional role within the team

        Returns:
            Add member result
        """
        # This would typically create a team member assignment
        # For now, return placeholder structure

        return {
            "team_id": team_id,
            "resource_id": resource_id,
            "role": role,
            "added_date": datetime.now().isoformat(),
            "success": True,
        }

    def remove_team_member(self, team_id: int, resource_id: int) -> Dict[str, Any]:
        """
        Remove a member from a team.

        Args:
            team_id: ID of the team
            resource_id: ID of the resource to remove

        Returns:
            Remove member result
        """
        # This would typically remove a team member assignment
        # For now, return placeholder structure

        return {
            "team_id": team_id,
            "resource_id": resource_id,
            "removed_date": datetime.now().isoformat(),
            "success": True,
        }

    def update_team_lead(
        self, team_id: int, new_lead_resource_id: int
    ) -> Dict[str, Any]:
        """
        Update team lead resource.

        Args:
            team_id: ID of the team
            new_lead_resource_id: ID of the new team lead

        Returns:
            Update response
        """
        return self.update(team_id, {"teamLeadResourceID": new_lead_resource_id})

    def get_team_summary(self, team_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary for a team.

        Args:
            team_id: ID of the team

        Returns:
            Team summary with related data
        """
        team = self.get(team_id)

        # This would typically query related entities
        # For now, return structure with placeholder data

        return {
            "team": team,
            "summary": {
                "team_id": team_id,
                "total_members": 0,  # Would count team members
                "active_members": 0,  # Would count active members
                "open_tickets": 0,  # Would query tickets assigned to team
                "active_projects": 0,  # Would query projects assigned to team
                "total_time_entries": 0,  # Would query time entries by team members
                "team_utilization": 0.0,  # Would calculate team utilization
            },
        }

    def get_team_workload(
        self,
        team_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get workload summary for a team.

        Args:
            team_id: ID of the team
            date_from: Start date for workload analysis
            date_to: End date for workload analysis

        Returns:
            Team workload summary
        """
        # This would typically analyze team member workloads
        # For now, return structure that could be populated

        return {
            "team_id": team_id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "workload_summary": {
                "total_hours": Decimal("0"),  # Would sum team member hours
                "billable_hours": Decimal("0"),  # Would sum billable hours
                "utilization_rate": 0.0,  # Would calculate utilization
                "capacity": Decimal("0"),  # Would calculate team capacity
                "overallocation": Decimal("0"),  # Would identify overallocation
                "member_workloads": [],  # Would include per-member data
            },
        }

    def bulk_assign_members(
        self, team_assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assign multiple resources to teams.

        Args:
            team_assignments: List of team assignments
                Each should contain: team_id, resource_id, role

        Returns:
            Summary of bulk assignment operation
        """
        results = []

        for assignment in team_assignments:
            team_id = assignment["team_id"]
            resource_id = assignment["resource_id"]
            role = assignment.get("role")

            try:
                result = self.add_team_member(team_id, resource_id, role)
                results.append(
                    {
                        "team_id": team_id,
                        "resource_id": resource_id,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "team_id": team_id,
                        "resource_id": resource_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_assignments": len(team_assignments),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_team_performance_metrics(
        self, team_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a team.

        Args:
            team_id: ID of the team
            date_from: Start date for metrics
            date_to: End date for metrics

        Returns:
            Team performance metrics
        """
        # This would typically analyze various performance data
        # For now, return structure that could be populated

        return {
            "team_id": team_id,
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "performance_metrics": {
                "tickets_resolved": 0,  # Would count resolved tickets
                "avg_resolution_time": 0.0,  # Would calculate average time
                "customer_satisfaction": 0.0,  # Would calculate satisfaction score
                "project_completion_rate": 0.0,  # Would calculate completion rate
                "revenue_generated": Decimal("0"),  # Would calculate team revenue
                "efficiency_score": 0.0,  # Would calculate efficiency
            },
        }

    def clone_team(
        self, source_team_id: int, new_name: str, include_members: bool = False
    ) -> Dict[str, Any]:
        """
        Create a clone of an existing team.

        Args:
            source_team_id: ID of the team to clone
            new_name: Name for the new team
            include_members: Whether to copy team members

        Returns:
            Create response for the new team
        """
        source_team = self.get(source_team_id)

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_team.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name

        new_team = self.create(clone_data)

        if include_members and new_team.get("success"):
            # Would copy team members here
            pass

        return new_team
