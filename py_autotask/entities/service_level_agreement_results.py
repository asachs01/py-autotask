"""
ServiceLevelAgreementResults Entity for py-autotask

This module provides the ServiceLevelAgreementResultsEntity class for managing SLA
performance results in Autotask. SLA Results track actual performance against
defined SLA targets and provide breach notifications.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ServiceLevelAgreementResultsEntity(BaseEntity):
    """
    Manages Autotask ServiceLevelAgreementResults - SLA performance tracking and results.

    Service Level Agreement Results track actual performance measurements against
    defined SLA targets, including response times, resolution times, and breach
    notifications. They provide detailed performance analytics and compliance reporting.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ServiceLevelAgreementResults"

    def get_sla_results_by_ticket(
        self, ticket_id: int, include_historical: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get SLA results for a specific ticket.

        Args:
            ticket_id: ID of the ticket
            include_historical: Whether to include historical results

        Returns:
            List of SLA results for the ticket
        """
        filters = [{"field": "ticketID", "op": "eq", "value": str(ticket_id)}]

        if not include_historical:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_breach_notifications(
        self, date_from: date, date_to: date, sla_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get SLA breach notifications for a date range.

        Args:
            date_from: Start date for breach analysis
            date_to: End date for breach analysis
            sla_id: Optional specific SLA ID to filter by

        Returns:
            List of breach notifications
        """
        filters = [
            {"field": "breachDateTime", "op": "gte", "value": date_from.isoformat()},
            {"field": "breachDateTime", "op": "lte", "value": date_to.isoformat()},
            {"field": "isBreach", "op": "eq", "value": "true"},
        ]

        if sla_id:
            filters.append({"field": "slaID", "op": "eq", "value": str(sla_id)})

        return self.query(filters=filters).items

    def calculate_compliance_percentage(
        self, sla_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Calculate SLA compliance percentage for a period.

        Args:
            sla_id: ID of the SLA
            date_from: Start date for calculation
            date_to: End date for calculation

        Returns:
            Dictionary with compliance statistics
        """
        # Get all results for the SLA in the period
        all_results = self.query(
            filters=[
                {"field": "slaID", "op": "eq", "value": str(sla_id)},
                {
                    "field": "createDateTime",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "createDateTime", "op": "lte", "value": date_to.isoformat()},
            ]
        ).items

        # Get breach results
        breach_results = self.query(
            filters=[
                {"field": "slaID", "op": "eq", "value": str(sla_id)},
                {
                    "field": "createDateTime",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "createDateTime", "op": "lte", "value": date_to.isoformat()},
                {"field": "isBreach", "op": "eq", "value": "true"},
            ]
        ).items

        total_count = len(all_results)
        breach_count = len(breach_results)
        compliance_count = total_count - breach_count

        return {
            "sla_id": sla_id,
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "statistics": {
                "total_results": total_count,
                "compliant_results": compliance_count,
                "breach_results": breach_count,
                "compliance_percentage": (
                    (compliance_count / total_count * 100) if total_count > 0 else 0.0
                ),
            },
        }

    def get_response_time_analysis(
        self, sla_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Analyze response time performance for an SLA.

        Args:
            sla_id: ID of the SLA
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Response time analysis results
        """
        results = self.query(
            filters=[
                {"field": "slaID", "op": "eq", "value": str(sla_id)},
                {
                    "field": "createDateTime",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "createDateTime", "op": "lte", "value": date_to.isoformat()},
            ]
        ).items

        if not results:
            return {
                "sla_id": sla_id,
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "analysis": {
                    "total_tickets": 0,
                    "average_response_time": 0.0,
                    "median_response_time": 0.0,
                    "response_breaches": 0,
                    "response_compliance_rate": 0.0,
                },
            }

        response_times = [float(r.get("responseTimeMinutes", 0)) for r in results]
        response_breaches = len(
            [r for r in results if r.get("responseTimeBreach", False)]
        )

        return {
            "sla_id": sla_id,
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "analysis": {
                "total_tickets": len(results),
                "average_response_time": sum(response_times) / len(response_times),
                "median_response_time": sorted(response_times)[
                    len(response_times) // 2
                ],
                "response_breaches": response_breaches,
                "response_compliance_rate": (
                    (len(results) - response_breaches) / len(results) * 100
                ),
            },
        }

    def get_resolution_time_analysis(
        self, sla_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Analyze resolution time performance for an SLA.

        Args:
            sla_id: ID of the SLA
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Resolution time analysis results
        """
        results = self.query(
            filters=[
                {"field": "slaID", "op": "eq", "value": str(sla_id)},
                {
                    "field": "createDateTime",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "createDateTime", "op": "lte", "value": date_to.isoformat()},
                {"field": "isResolved", "op": "eq", "value": "true"},
            ]
        ).items

        if not results:
            return {
                "sla_id": sla_id,
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "analysis": {
                    "resolved_tickets": 0,
                    "average_resolution_time": 0.0,
                    "median_resolution_time": 0.0,
                    "resolution_breaches": 0,
                    "resolution_compliance_rate": 0.0,
                },
            }

        resolution_times = [float(r.get("resolutionTimeMinutes", 0)) for r in results]
        resolution_breaches = len(
            [r for r in results if r.get("resolutionTimeBreach", False)]
        )

        return {
            "sla_id": sla_id,
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "analysis": {
                "resolved_tickets": len(results),
                "average_resolution_time": sum(resolution_times)
                / len(resolution_times),
                "median_resolution_time": sorted(resolution_times)[
                    len(resolution_times) // 2
                ],
                "resolution_breaches": resolution_breaches,
                "resolution_compliance_rate": (
                    (len(results) - resolution_breaches) / len(results) * 100
                ),
            },
        }

    def get_trending_breach_analysis(
        self, sla_id: int, months_back: int = 6
    ) -> Dict[str, Any]:
        """
        Get trending analysis of SLA breaches over time.

        Args:
            sla_id: ID of the SLA
            months_back: Number of months to analyze

        Returns:
            Trending breach analysis
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        breaches = self.query(
            filters=[
                {"field": "slaID", "op": "eq", "value": str(sla_id)},
                {
                    "field": "breachDateTime",
                    "op": "gte",
                    "value": start_date.isoformat(),
                },
                {"field": "breachDateTime", "op": "lte", "value": end_date.isoformat()},
                {"field": "isBreach", "op": "eq", "value": "true"},
            ]
        ).items

        # Group breaches by month
        monthly_breaches = {}
        for breach in breaches:
            breach_date = datetime.fromisoformat(breach.get("breachDateTime", ""))
            month_key = breach_date.strftime("%Y-%m")

            if month_key not in monthly_breaches:
                monthly_breaches[month_key] = {
                    "response_breaches": 0,
                    "resolution_breaches": 0,
                    "total_breaches": 0,
                }

            monthly_breaches[month_key]["total_breaches"] += 1
            if breach.get("responseTimeBreach"):
                monthly_breaches[month_key]["response_breaches"] += 1
            if breach.get("resolutionTimeBreach"):
                monthly_breaches[month_key]["resolution_breaches"] += 1

        return {
            "sla_id": sla_id,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months": months_back,
            },
            "trending_data": monthly_breaches,
            "summary": {
                "total_months_analyzed": len(monthly_breaches),
                "total_breaches": sum(
                    data["total_breaches"] for data in monthly_breaches.values()
                ),
                "average_monthly_breaches": sum(
                    data["total_breaches"] for data in monthly_breaches.values()
                )
                / max(len(monthly_breaches), 1),
            },
        }

    def generate_sla_performance_report(
        self, sla_ids: List[int], date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Generate comprehensive SLA performance report for multiple SLAs.

        Args:
            sla_ids: List of SLA IDs to include in report
            date_from: Start date for report
            date_to: End date for report

        Returns:
            Comprehensive SLA performance report
        """
        report_data = {
            "report_period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "slas_analyzed": len(sla_ids),
            "sla_performance": [],
        }

        for sla_id in sla_ids:
            compliance_data = self.calculate_compliance_percentage(
                sla_id, date_from, date_to
            )
            response_analysis = self.get_response_time_analysis(
                sla_id, date_from, date_to
            )
            resolution_analysis = self.get_resolution_time_analysis(
                sla_id, date_from, date_to
            )

            sla_performance = {
                "sla_id": sla_id,
                "compliance": compliance_data["statistics"],
                "response_performance": response_analysis["analysis"],
                "resolution_performance": resolution_analysis["analysis"],
            }

            report_data["sla_performance"].append(sla_performance)

        # Calculate overall statistics
        all_compliance = [
            sla["compliance"]["compliance_percentage"]
            for sla in report_data["sla_performance"]
        ]
        report_data["overall_summary"] = {
            "average_compliance": (
                sum(all_compliance) / len(all_compliance) if all_compliance else 0.0
            ),
            "best_performing_sla": (
                max(
                    report_data["sla_performance"],
                    key=lambda x: x["compliance"]["compliance_percentage"],
                )["sla_id"]
                if report_data["sla_performance"]
                else None
            ),
            "worst_performing_sla": (
                min(
                    report_data["sla_performance"],
                    key=lambda x: x["compliance"]["compliance_percentage"],
                )["sla_id"]
                if report_data["sla_performance"]
                else None
            ),
        }

        return report_data

    def get_breach_escalation_candidates(
        self, hours_threshold: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get SLA results that are approaching or have exceeded breach thresholds.

        Args:
            hours_threshold: Hours threshold for escalation consideration

        Returns:
            List of results requiring escalation
        """
        threshold_time = datetime.now() - timedelta(hours=hours_threshold)

        return self.query(
            filters=[
                {"field": "isActive", "op": "eq", "value": "true"},
                {
                    "field": "breachDateTime",
                    "op": "lte",
                    "value": threshold_time.isoformat(),
                },
                {"field": "isEscalated", "op": "eq", "value": "false"},
            ]
        ).items

    def mark_result_escalated(
        self, result_id: int, escalation_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark an SLA result as escalated.

        Args:
            result_id: ID of the SLA result
            escalation_notes: Optional notes about the escalation

        Returns:
            Updated SLA result data
        """
        update_data = {
            "id": result_id,
            "isEscalated": True,
            "escalationDateTime": datetime.now().isoformat(),
        }

        if escalation_notes:
            update_data["escalationNotes"] = escalation_notes

        return self.update(update_data)
