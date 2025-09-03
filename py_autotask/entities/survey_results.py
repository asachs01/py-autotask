"""
SurveyResults Entity for py-autotask

This module provides the SurveyResultsEntity class for managing customer satisfaction
surveys and feedback in Autotask. Survey Results capture customer feedback, ratings,
and responses to help track service quality and customer satisfaction.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class SurveyResultsEntity(BaseEntity):
    """
    Manages Autotask SurveyResults - customer satisfaction surveys and feedback.

    Survey Results capture customer feedback, ratings, and responses to service
    quality questionnaires. They support automated survey distribution, response
    collection, and satisfaction analytics for continuous service improvement.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "SurveyResults"

    def create_survey_result(
        self,
        ticket_id: int,
        contact_id: int,
        survey_type: str,
        overall_rating: int,
        survey_responses: Dict[str, Any],
        completion_date: Optional[datetime] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new survey result.

        Args:
            ticket_id: ID of the related ticket
            contact_id: ID of the responding contact
            survey_type: Type of survey (satisfaction, follow_up, etc.)
            overall_rating: Overall satisfaction rating (1-5 or 1-10 scale)
            survey_responses: Dictionary of survey question responses
            completion_date: When the survey was completed
            **kwargs: Additional fields for the survey result

        Returns:
            Create response with new survey result ID
        """
        result_data = {
            "ticketID": ticket_id,
            "contactID": contact_id,
            "surveyType": survey_type,
            "overallRating": overall_rating,
            "surveyResponses": survey_responses,
            "completionDate": (completion_date or datetime.now()).isoformat(),
            **kwargs,
        }

        return self.create(result_data)

    def get_results_by_ticket(
        self, ticket_id: int, survey_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get survey results for a specific ticket.

        Args:
            ticket_id: ID of the ticket
            survey_type: Optional survey type to filter by

        Returns:
            List of survey results for the ticket
        """
        filters = [{"field": "ticketID", "op": "eq", "value": str(ticket_id)}]

        if survey_type:
            filters.append({"field": "surveyType", "op": "eq", "value": survey_type})

        return self.query(filters=filters).items

    def get_results_by_contact(
        self,
        contact_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get survey results by a specific contact.

        Args:
            contact_id: ID of the contact
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            List of survey results from the contact
        """
        filters = [{"field": "contactID", "op": "eq", "value": str(contact_id)}]

        if date_from:
            filters.append(
                {"field": "completionDate", "op": "gte", "value": date_from.isoformat()}
            )
        if date_to:
            filters.append(
                {"field": "completionDate", "op": "lte", "value": date_to.isoformat()}
            )

        return self.query(filters=filters).items

    def calculate_satisfaction_metrics(
        self, date_from: date, date_to: date, survey_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate satisfaction metrics for a period.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            survey_type: Optional survey type to analyze

        Returns:
            Satisfaction metrics and statistics
        """
        filters = [
            {"field": "completionDate", "op": "gte", "value": date_from.isoformat()},
            {"field": "completionDate", "op": "lte", "value": date_to.isoformat()},
        ]

        if survey_type:
            filters.append({"field": "surveyType", "op": "eq", "value": survey_type})

        results = self.query(filters=filters).items

        if not results:
            return {
                "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
                "survey_type": survey_type,
                "metrics": {
                    "total_responses": 0,
                    "average_rating": 0.0,
                    "satisfaction_distribution": {},
                    "response_rate": 0.0,
                    "nps_score": 0.0,
                },
            }

        ratings = [
            int(result["overallRating"])
            for result in results
            if result.get("overallRating")
        ]

        # Calculate satisfaction distribution
        satisfaction_distribution = {}
        for rating in ratings:
            satisfaction_distribution[str(rating)] = (
                satisfaction_distribution.get(str(rating), 0) + 1
            )

        # Calculate NPS (Net Promoter Score) assuming 1-10 scale
        promoters = sum(1 for r in ratings if r >= 9)
        detractors = sum(1 for r in ratings if r <= 6)
        nps_score = ((promoters - detractors) / len(ratings) * 100) if ratings else 0.0

        # Calculate satisfaction levels (assuming 1-5 scale, adjust as needed)
        very_satisfied = sum(1 for r in ratings if r >= 5)
        satisfied = sum(1 for r in ratings if r == 4)
        neutral = sum(1 for r in ratings if r == 3)
        dissatisfied = sum(1 for r in ratings if r == 2)
        very_dissatisfied = sum(1 for r in ratings if r == 1)

        return {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "survey_type": survey_type,
            "metrics": {
                "total_responses": len(results),
                "average_rating": (
                    round(sum(ratings) / len(ratings), 2) if ratings else 0.0
                ),
                "median_rating": sorted(ratings)[len(ratings) // 2] if ratings else 0,
                "satisfaction_distribution": satisfaction_distribution,
                "satisfaction_levels": {
                    "very_satisfied": very_satisfied,
                    "satisfied": satisfied,
                    "neutral": neutral,
                    "dissatisfied": dissatisfied,
                    "very_dissatisfied": very_dissatisfied,
                },
                "satisfaction_percentage": (
                    round((very_satisfied + satisfied) / len(ratings) * 100, 1)
                    if ratings
                    else 0.0
                ),
                "nps_score": round(nps_score, 1),
            },
        }

    def get_low_satisfaction_results(
        self, rating_threshold: int = 3, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get survey results with low satisfaction ratings.

        Args:
            rating_threshold: Rating threshold (results below this are considered low)
            days_back: Number of days to look back

        Returns:
            List of low satisfaction survey results
        """
        date_from = date.today() - timedelta(days=days_back)

        filters = [
            {"field": "completionDate", "op": "gte", "value": date_from.isoformat()},
            {"field": "overallRating", "op": "lt", "value": str(rating_threshold)},
        ]

        return self.query(filters=filters).items

    def get_survey_response_trends(
        self, months_back: int = 12, survey_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze survey response trends over time.

        Args:
            months_back: Number of months to analyze
            survey_type: Optional survey type to analyze

        Returns:
            Survey response trend analysis
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        filters = [
            {"field": "completionDate", "op": "gte", "value": start_date.isoformat()},
            {"field": "completionDate", "op": "lte", "value": end_date.isoformat()},
        ]

        if survey_type:
            filters.append({"field": "surveyType", "op": "eq", "value": survey_type})

        results = self.query(filters=filters).items

        # Group results by month
        monthly_trends = {}
        for result in results:
            completion_date = datetime.fromisoformat(result["completionDate"])
            month_key = completion_date.strftime("%Y-%m")

            if month_key not in monthly_trends:
                monthly_trends[month_key] = {
                    "total_responses": 0,
                    "ratings_sum": 0,
                    "ratings": [],
                }

            monthly_trends[month_key]["total_responses"] += 1
            rating = int(result.get("overallRating", 0))
            monthly_trends[month_key]["ratings_sum"] += rating
            monthly_trends[month_key]["ratings"].append(rating)

        # Calculate monthly averages
        for month_data in monthly_trends.values():
            if month_data["total_responses"] > 0:
                month_data["average_rating"] = round(
                    month_data["ratings_sum"] / month_data["total_responses"], 2
                )
            else:
                month_data["average_rating"] = 0.0

        return {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months_analyzed": months_back,
            },
            "survey_type": survey_type,
            "monthly_trends": monthly_trends,
            "summary": {
                "total_responses": sum(
                    data["total_responses"] for data in monthly_trends.values()
                ),
                "overall_average_rating": round(
                    sum(data["ratings_sum"] for data in monthly_trends.values())
                    / max(
                        sum(
                            data["total_responses"] for data in monthly_trends.values()
                        ),
                        1,
                    ),
                    2,
                ),
                "trend_direction": self._calculate_trend_direction(monthly_trends),
            },
        }

    def _calculate_trend_direction(self, monthly_trends: Dict[str, Dict]) -> str:
        """Calculate the trend direction of satisfaction ratings."""
        if len(monthly_trends) < 2:
            return "insufficient_data"

        months = sorted(monthly_trends.keys())
        first_half = months[: len(months) // 2]
        second_half = months[len(months) // 2 :]

        first_half_avg = sum(
            monthly_trends[month]["average_rating"] for month in first_half
        ) / len(first_half)
        second_half_avg = sum(
            monthly_trends[month]["average_rating"] for month in second_half
        ) / len(second_half)

        difference = second_half_avg - first_half_avg

        if difference > 0.2:
            return "improving"
        elif difference < -0.2:
            return "declining"
        else:
            return "stable"

    def generate_satisfaction_report(
        self, date_from: date, date_to: date, group_by: str = "survey_type"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive satisfaction report.

        Args:
            date_from: Start date for report
            date_to: End date for report
            group_by: How to group results (survey_type, department, contact)

        Returns:
            Comprehensive satisfaction report
        """
        all_results = self.query(
            filters=[
                {
                    "field": "completionDate",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "completionDate", "op": "lte", "value": date_to.isoformat()},
            ]
        ).items

        # Group results by specified field
        grouped_results = {}
        for result in all_results:
            group_key = result.get(group_by, "unknown")
            if group_key not in grouped_results:
                grouped_results[group_key] = []
            grouped_results[group_key].append(result)

        # Calculate metrics for each group
        group_metrics = {}
        for group_key, group_results in grouped_results.items():
            ratings = [
                int(r["overallRating"]) for r in group_results if r.get("overallRating")
            ]

            if ratings:
                group_metrics[group_key] = {
                    "total_responses": len(group_results),
                    "average_rating": round(sum(ratings) / len(ratings), 2),
                    "satisfaction_rate": round(
                        sum(1 for r in ratings if r >= 4) / len(ratings) * 100, 1
                    ),
                    "response_details": {
                        "highest_rating": max(ratings),
                        "lowest_rating": min(ratings),
                        "rating_distribution": {
                            str(i): ratings.count(i) for i in range(1, 6)
                        },
                    },
                }

        return {
            "report_period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "grouping": group_by,
            "total_responses": len(all_results),
            "group_metrics": group_metrics,
            "overall_summary": {
                "average_satisfaction": round(
                    sum(
                        float(metrics["average_rating"]) * metrics["total_responses"]
                        for metrics in group_metrics.values()
                    )
                    / max(
                        sum(
                            metrics["total_responses"]
                            for metrics in group_metrics.values()
                        ),
                        1,
                    ),
                    2,
                ),
                "best_performing_group": (
                    max(group_metrics.items(), key=lambda x: x[1]["average_rating"])[0]
                    if group_metrics
                    else None
                ),
                "worst_performing_group": (
                    min(group_metrics.items(), key=lambda x: x[1]["average_rating"])[0]
                    if group_metrics
                    else None
                ),
            },
        }

    def get_survey_completion_rate(
        self, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Calculate survey completion rates.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Survey completion rate analysis
        """
        # This would typically compare sent surveys vs completed surveys
        # For now, return completion rate structure
        completed_surveys = self.query(
            filters=[
                {
                    "field": "completionDate",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "completionDate", "op": "lte", "value": date_to.isoformat()},
            ]
        ).items

        return {
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "completion_metrics": {
                "completed_surveys": len(completed_surveys),
                "sent_surveys": 0,  # Would need to query sent survey data
                "completion_rate": 0.0,  # Would calculate: completed/sent * 100
                "average_completion_time": 0.0,  # Would calculate from survey data
                "completion_by_type": {},  # Would group by survey type
            },
        }

    def flag_survey_for_followup(
        self, result_id: int, followup_reason: str, priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Flag a survey result for follow-up action.

        Args:
            result_id: ID of the survey result
            followup_reason: Reason for follow-up
            priority: Follow-up priority (low, normal, high, urgent)

        Returns:
            Updated survey result data
        """
        return self.update(
            {
                "id": result_id,
                "requiresFollowup": True,
                "followupReason": followup_reason,
                "followupPriority": priority,
                "followupFlaggedDate": datetime.now().isoformat(),
            }
        )

    def bulk_analyze_satisfaction_by_technician(
        self, date_from: date, date_to: date, min_responses: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze satisfaction ratings by technician performance.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            min_responses: Minimum responses required for inclusion

        Returns:
            Technician satisfaction analysis
        """
        results = self.query(
            filters=[
                {
                    "field": "completionDate",
                    "op": "gte",
                    "value": date_from.isoformat(),
                },
                {"field": "completionDate", "op": "lte", "value": date_to.isoformat()},
            ]
        ).items

        # Group by technician (would need to join with ticket data)
        technician_metrics = {}

        # This would typically require joining survey results with ticket data
        # to get the assigned technician. For now, return structure.
        return {
            "analysis_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "minimum_responses_threshold": min_responses,
            "technician_performance": technician_metrics,
            "summary": {
                "technicians_analyzed": len(technician_metrics),
                "highest_rated_technician": None,
                "lowest_rated_technician": None,
                "average_technician_rating": 0.0,
            },
        }
