"""
CompanyTeams entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyTeamsEntity(BaseEntity):
    """
    Handles all Company Team-related operations for the Autotask API.

    Company Teams in Autotask represent the association between internal teams
    and client companies for service delivery and account management.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company_team_assignment(
        self,
        company_id: int,
        team_id: int,
        assignment_type: int = 1,
        is_primary: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company team assignment.

        Args:
            company_id: ID of the company
            team_id: ID of the team
            assignment_type: Type of assignment (1=Primary, 2=Support, etc.)
            is_primary: Whether this is the primary team for the company
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            **kwargs: Additional assignment fields

        Returns:
            Created company team assignment data
        """
        assignment_data = {
            "CompanyID": company_id,
            "TeamID": team_id,
            "AssignmentType": assignment_type,
            "IsPrimary": is_primary,
            **kwargs,
        }

        if start_date:
            assignment_data["StartDate"] = start_date
        if end_date:
            assignment_data["EndDate"] = end_date

        return self.create(assignment_data)

    def get_company_teams(
        self,
        company_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all team assignments for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active assignments
            limit: Maximum number of assignments to return

        Returns:
            List of company team assignments
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if active_only:
            from datetime import datetime

            datetime.now().isoformat()

            # Active assignments: no end date or end date in future
            filters.append(QueryFilter(field="EndDate", op="isNull", value=None))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_team_companies(
        self,
        team_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all company assignments for a specific team.

        Args:
            team_id: ID of the team
            active_only: Whether to return only active assignments
            limit: Maximum number of assignments to return

        Returns:
            List of team company assignments
        """
        filters = [QueryFilter(field="TeamID", op="eq", value=team_id)]

        if active_only:
            from datetime import datetime

            datetime.now().isoformat()

            filters.append(QueryFilter(field="EndDate", op="isNull", value=None))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_primary_team(self, company_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the primary team assigned to a company.

        Args:
            company_id: ID of the company

        Returns:
            Primary team assignment data or None if not found
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="IsPrimary", op="eq", value=True),
        ]

        response = self.query(filters=filters, max_records=1)
        return response.items[0] if response.items else None

    def set_primary_team(self, company_id: int, team_id: int) -> Dict[str, Any]:
        """
        Set a team as the primary team for a company.

        Args:
            company_id: ID of the company
            team_id: ID of the team to set as primary

        Returns:
            Updated team assignment data
        """
        # First, remove primary flag from any existing primary team
        existing_primary = self.get_primary_team(company_id)
        if existing_primary:
            self.update_by_id(existing_primary["id"], {"IsPrimary": False})

        # Find the assignment for the specified team
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="TeamID", op="eq", value=team_id),
        ]

        response = self.query(filters=filters, max_records=1)
        if not response.items:
            # Create new assignment if it doesn't exist
            return self.create_company_team_assignment(
                company_id=company_id,
                team_id=team_id,
                is_primary=True,
                assignment_type=1,
            )
        else:
            # Update existing assignment to be primary
            assignment = response.items[0]
            return self.update_by_id(assignment["id"], {"IsPrimary": True})

    def remove_team_assignment(self, company_id: int, team_id: int) -> bool:
        """
        Remove a team assignment from a company.

        Args:
            company_id: ID of the company
            team_id: ID of the team to remove

        Returns:
            True if successful
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="TeamID", op="eq", value=team_id),
        ]

        response = self.query(filters=filters, max_records=1)
        if response.items:
            assignment = response.items[0]
            return self.delete(assignment["id"])

        return False

    def end_team_assignment(
        self, assignment_id: int, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a team assignment by setting an end date.

        Args:
            assignment_id: ID of the assignment to end
            end_date: End date (ISO format, uses current date if not specified)

        Returns:
            Updated assignment data
        """
        if not end_date:
            from datetime import datetime

            end_date = datetime.now().isoformat()

        return self.update_by_id(assignment_id, {"EndDate": end_date})

    def get_assignments_by_type(
        self,
        assignment_type: int,
        company_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get team assignments filtered by assignment type.

        Args:
            assignment_type: Assignment type to filter by
            company_id: Optional company ID to further filter
            limit: Maximum number of assignments to return

        Returns:
            List of assignments matching the criteria
        """
        filters = [QueryFilter(field="AssignmentType", op="eq", value=assignment_type)]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_assignments_by_date_range(
        self,
        start_date: str,
        end_date: str,
        company_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get team assignments within a specific date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            company_id: Optional company ID to filter
            limit: Maximum number of assignments to return

        Returns:
            List of assignments within the date range
        """
        filters = [
            QueryFilter(field="StartDate", op="gte", value=start_date),
            QueryFilter(field="StartDate", op="lte", value=end_date),
        ]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def bulk_assign_teams(
        self,
        company_id: int,
        team_ids: List[int],
        assignment_type: int = 2,  # Support team by default
    ) -> List[Dict[str, Any]]:
        """
        Assign multiple teams to a company in bulk.

        Args:
            company_id: ID of the company
            team_ids: List of team IDs to assign
            assignment_type: Type of assignment for all teams

        Returns:
            List of created assignment data
        """
        assignments_data = [
            {
                "CompanyID": company_id,
                "TeamID": team_id,
                "AssignmentType": assignment_type,
                "IsPrimary": False,
            }
            for team_id in team_ids
        ]

        return self.batch_create(assignments_data)

    def get_team_workload(self, team_id: int) -> Dict[str, Any]:
        """
        Get workload statistics for a specific team.

        Args:
            team_id: ID of the team

        Returns:
            Dictionary with team workload statistics
        """
        # Get all active company assignments for this team
        assignments = self.get_team_companies(team_id, active_only=True)

        primary_assignments = [a for a in assignments if a.get("IsPrimary")]
        support_assignments = [a for a in assignments if not a.get("IsPrimary")]

        return {
            "team_id": team_id,
            "total_companies": len(assignments),
            "primary_companies": len(primary_assignments),
            "support_companies": len(support_assignments),
            "assignments": assignments,
        }
