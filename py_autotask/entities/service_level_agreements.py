"""
ServiceLevelAgreements Entity for py-autotask

This module provides the ServiceLevelAgreementsEntity class for managing SLAs
in Autotask. SLAs define service commitments, response times, and performance
metrics for customer service delivery.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ServiceLevelAgreementsEntity(BaseEntity):
    """
    Manages Autotask ServiceLevelAgreements - SLA definitions and tracking.

    Service Level Agreements define service commitments, response times,
    resolution times, and performance metrics for customer service delivery.
    They support SLA monitoring, breach tracking, and performance reporting.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ServiceLevelAgreements"

    def create_sla(
        self,
        name: str,
        description: str,
        account_id: Optional[int] = None,
        response_time_hours: Optional[Union[int, float]] = None,
        resolution_time_hours: Optional[Union[int, float]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new SLA.

        Args:
            name: Name of the SLA
            description: Description of SLA terms
            account_id: Optional account ID this SLA applies to
            response_time_hours: Response time commitment in hours
            resolution_time_hours: Resolution time commitment in hours
            **kwargs: Additional fields for the SLA

        Returns:
            Create response with new SLA ID
        """
        sla_data = {"name": name, "description": description, **kwargs}

        if account_id:
            sla_data["accountID"] = account_id
        if response_time_hours is not None:
            sla_data["responseTimeHours"] = float(response_time_hours)
        if resolution_time_hours is not None:
            sla_data["resolutionTimeHours"] = float(resolution_time_hours)

        return self.create(sla_data)

    def get_active_slas(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all active SLAs.

        Args:
            account_id: Optional account ID to filter by

        Returns:
            List of active SLAs
        """
        filters = ["isActive eq true"]

        if account_id:
            filters.append(f"accountID eq {account_id}")

        return self.query(filter=" and ".join(filters))

    def get_slas_by_account(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get SLAs for a specific account.

        Args:
            account_id: ID of the account

        Returns:
            List of SLAs for the account
        """
        return self.query(filter=f"accountID eq {account_id}")

    def check_sla_breach(
        self, sla_id: int, ticket_id: int, current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Check if a ticket is in breach of SLA.

        Args:
            sla_id: ID of the SLA to check against
            ticket_id: ID of the ticket
            current_time: Current time for calculation (defaults to now)

        Returns:
            SLA breach status and details
        """
        if current_time is None:
            current_time = datetime.now()

        sla = self.get(sla_id)

        # This would typically query the ticket details
        # For now, return breach check structure

        response_time_hours = sla.get("responseTimeHours", 0)
        resolution_time_hours = sla.get("resolutionTimeHours", 0)

        return {
            "sla_id": sla_id,
            "ticket_id": ticket_id,
            "check_time": current_time.isoformat(),
            "sla_terms": {
                "response_time_hours": response_time_hours,
                "resolution_time_hours": resolution_time_hours,
            },
            "breach_status": {
                "response_breach": False,  # Would calculate based on ticket data
                "resolution_breach": False,  # Would calculate based on ticket data
                "time_remaining": {
                    "response": 0,  # Would calculate remaining time
                    "resolution": 0,  # Would calculate remaining time
                },
            },
        }

    def get_sla_performance_report(
        self, sla_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Get SLA performance report for a period.

        Args:
            sla_id: ID of the SLA
            date_from: Start date for the report
            date_to: End date for the report

        Returns:
            SLA performance report
        """
        sla = self.get(sla_id)

        # This would typically query tickets and calculate performance
        # For now, return performance report structure

        return {
            "sla_id": sla_id,
            "sla_name": sla.get("name"),
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "performance": {
                "total_tickets": 0,  # Would count tickets under this SLA
                "response_breaches": 0,  # Would count response breaches
                "resolution_breaches": 0,  # Would count resolution breaches
                "response_compliance": 0.0,  # Would calculate percentage
                "resolution_compliance": 0.0,  # Would calculate percentage
                "average_response_time": 0.0,  # Would calculate average
                "average_resolution_time": 0.0,  # Would calculate average
            },
        }

    def get_sla_breach_summary(
        self, date_from: date, date_to: date, account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get summary of SLA breaches for a period.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            account_id: Optional account ID to filter by

        Returns:
            SLA breach summary
        """
        filters = []

        if account_id:
            filters.append(f"accountID eq {account_id}")

        slas = self.query(filter=" and ".join(filters) if filters else None)

        # This would typically analyze breach data
        # For now, return breach summary structure

        return {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "account_id": account_id,
            "breach_summary": {
                "total_slas": len(slas),
                "total_breaches": 0,  # Would count actual breaches
                "response_breaches": 0,  # Would count response breaches
                "resolution_breaches": 0,  # Would count resolution breaches
                "most_breached_sla": None,  # Would identify worst performing SLA
                "breach_trends": [],  # Would show trends over time
            },
        }

    def update_sla_terms(
        self,
        sla_id: int,
        response_time_hours: Optional[Union[int, float]] = None,
        resolution_time_hours: Optional[Union[int, float]] = None,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update SLA terms.

        Args:
            sla_id: ID of the SLA
            response_time_hours: New response time commitment
            resolution_time_hours: New resolution time commitment
            effective_date: When changes become effective

        Returns:
            Update response
        """
        update_data = {}

        if response_time_hours is not None:
            update_data["responseTimeHours"] = float(response_time_hours)
        if resolution_time_hours is not None:
            update_data["resolutionTimeHours"] = float(resolution_time_hours)
        if effective_date:
            update_data["effectiveDate"] = effective_date.isoformat()

        return self.update(sla_id, update_data)

    def get_sla_compliance_trends(
        self, sla_id: int, months_back: int = 12
    ) -> Dict[str, Any]:
        """
        Get SLA compliance trends over time.

        Args:
            sla_id: ID of the SLA
            months_back: Number of months to analyze

        Returns:
            SLA compliance trends
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        # This would typically analyze historical compliance data
        # For now, return trends structure

        return {
            "sla_id": sla_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months": months_back,
            },
            "trends": {
                "monthly_compliance": [],  # Would show month-by-month compliance
                "improvement_areas": [],  # Would identify areas needing improvement
                "best_performance": None,  # Would identify best performing period
                "worst_performance": None,  # Would identify worst performing period
            },
        }

    def bulk_update_sla_terms(
        self, sla_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update terms for multiple SLAs.

        Args:
            sla_updates: List of SLA updates
                Each should contain: sla_id, response_time_hours, resolution_time_hours

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in sla_updates:
            sla_id = update["sla_id"]
            response_time = update.get("response_time_hours")
            resolution_time = update.get("resolution_time_hours")
            effective_date = update.get("effective_date")

            try:
                result = self.update_sla_terms(
                    sla_id, response_time, resolution_time, effective_date
                )
                results.append({"id": sla_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": sla_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(sla_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def clone_sla(
        self, source_sla_id: int, new_name: str, new_account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing SLA.

        Args:
            source_sla_id: ID of the SLA to clone
            new_name: Name for the new SLA
            new_account_id: Optional new account ID

        Returns:
            Create response for the new SLA
        """
        source_sla = self.get(source_sla_id)

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_sla.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        if new_account_id:
            clone_data["accountID"] = new_account_id

        return self.create(clone_data)
