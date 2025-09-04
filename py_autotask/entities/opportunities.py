"""
Opportunities entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class OpportunitiesEntity(BaseEntity):
    """
    Handles Opportunity operations for the Autotask API.

    Manages sales opportunities including pipeline tracking,
    forecasting, and opportunity lifecycle management.
    """

    def __init__(self, client, entity_name: str = "Opportunities"):
        super().__init__(client, entity_name)

    def create_opportunity(
        self,
        title: str,
        account_id: int,
        amount: float,
        stage: int,
        close_date: str,
        probability: Optional[int] = None,
        owner_resource_id: Optional[int] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new sales opportunity.

        Args:
            title: Opportunity title/name
            account_id: ID of the account/company
            amount: Estimated opportunity value
            stage: Opportunity stage ID
            close_date: Expected close date (ISO format)
            probability: Win probability percentage (0-100)
            owner_resource_id: ID of opportunity owner
            description: Opportunity description
            **kwargs: Additional opportunity fields

        Returns:
            Created opportunity data
        """
        opp_data = {
            "Title": title,
            "AccountID": account_id,
            "Amount": amount,
            "Stage": stage,
            "ProjectedCloseDate": close_date,
            **kwargs,
        }

        if probability is not None:
            opp_data["Probability"] = probability

        if owner_resource_id is not None:
            opp_data["OwnerResourceID"] = owner_resource_id

        if description:
            opp_data["Description"] = description

        return self.create(opp_data)

    def get_opportunities_by_account(
        self,
        account_id: int,
        include_closed: bool = False,
        stage_filter: Optional[List[int]] = None,
    ) -> EntityList:
        """
        Get all opportunities for a specific account.

        Args:
            account_id: Account ID to filter by
            include_closed: Whether to include closed opportunities
            stage_filter: Optional list of stage IDs to filter by

        Returns:
            List of opportunities for the account
        """
        filters = [{"field": "AccountID", "op": "eq", "value": str(account_id)}]

        if not include_closed:
            # Exclude closed/lost stages (typically stage 5-7)
            filters.append({"field": "Stage", "op": "lt", "value": "5"})

        if stage_filter:
            if len(stage_filter) == 1:
                filters.append(
                    {"field": "Stage", "op": "eq", "value": str(stage_filter[0])}
                )
            else:
                filters.append(
                    {
                        "field": "Stage",
                        "op": "in",
                        "value": [str(s) for s in stage_filter],
                    }
                )

        return self.query_all(filters=filters)

    def get_opportunities_by_owner(
        self,
        owner_resource_id: int,
        include_closed: bool = False,
        days_filter: Optional[int] = None,
    ) -> EntityList:
        """
        Get opportunities assigned to a specific resource.

        Args:
            owner_resource_id: Resource ID of the opportunity owner
            include_closed: Whether to include closed opportunities
            days_filter: Optional filter for opportunities created/modified in last N days

        Returns:
            List of opportunities owned by the resource
        """
        filters = [
            {"field": "OwnerResourceID", "op": "eq", "value": str(owner_resource_id)}
        ]

        if not include_closed:
            filters.append({"field": "Stage", "op": "lt", "value": "5"})

        if days_filter:
            cutoff_date = datetime.now() - timedelta(days=days_filter)
            filters.append(
                {
                    "field": "LastModifiedDateTime",
                    "op": "gte",
                    "value": cutoff_date.isoformat(),
                }
            )

        return self.query_all(filters=filters)

    def get_opportunities_by_stage(
        self,
        stage: int,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> EntityList:
        """
        Get opportunities in a specific stage.

        Args:
            stage: Stage ID to filter by
            min_amount: Minimum opportunity amount
            max_amount: Maximum opportunity amount

        Returns:
            List of opportunities in the specified stage
        """
        filters = [{"field": "Stage", "op": "eq", "value": str(stage)}]

        if min_amount is not None:
            filters.append({"field": "Amount", "op": "gte", "value": str(min_amount)})

        if max_amount is not None:
            filters.append({"field": "Amount", "op": "lte", "value": str(max_amount)})

        return self.query_all(filters=filters)

    def get_closing_soon_opportunities(
        self,
        days: int = 30,
        min_probability: Optional[int] = None,
        owner_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get opportunities that are closing soon.

        Args:
            days: Number of days to look ahead
            min_probability: Minimum probability threshold
            owner_id: Optional owner filter

        Returns:
            List of opportunities closing soon
        """
        future_date = datetime.now() + timedelta(days=days)
        filters = [
            {
                "field": "ProjectedCloseDate",
                "op": "lte",
                "value": future_date.isoformat(),
            },
            {"field": "Stage", "op": "lt", "value": "5"},  # Not closed
        ]

        if min_probability is not None:
            filters.append(
                {"field": "Probability", "op": "gte", "value": str(min_probability)}
            )

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        return self.query_all(filters=filters)

    def get_overdue_opportunities(self, owner_id: Optional[int] = None) -> EntityList:
        """
        Get opportunities that are past their projected close date.

        Args:
            owner_id: Optional owner filter

        Returns:
            List of overdue opportunities
        """
        today = datetime.now().date().isoformat()
        filters = [
            {"field": "ProjectedCloseDate", "op": "lt", "value": today},
            {"field": "Stage", "op": "lt", "value": "5"},  # Not closed
        ]

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        return self.query_all(filters=filters)

    def advance_opportunity_stage(
        self,
        opportunity_id: int,
        new_stage: int,
        update_probability: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Advance an opportunity to the next stage.

        Args:
            opportunity_id: Opportunity ID
            new_stage: New stage ID
            update_probability: Optional updated probability
            notes: Optional notes about the stage change

        Returns:
            Updated opportunity data
        """
        update_data = {"Stage": new_stage}

        if update_probability is not None:
            update_data["Probability"] = update_probability

        if notes:
            # Add notes to description or a notes field if available
            current_opp = self.get(opportunity_id)
            if current_opp:
                existing_desc = current_opp.get("Description", "")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_desc = f"{existing_desc}\n\n[{timestamp}] Stage Advanced to {new_stage}: {notes}".strip()
                update_data["Description"] = new_desc

        return self.update_by_id(opportunity_id, update_data)

    def close_opportunity_won(
        self,
        opportunity_id: int,
        actual_close_date: Optional[str] = None,
        actual_amount: Optional[float] = None,
        win_reason: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Close an opportunity as won.

        Args:
            opportunity_id: Opportunity ID
            actual_close_date: Actual close date (ISO format)
            actual_amount: Actual amount won
            win_reason: Optional reason for winning

        Returns:
            Updated opportunity data
        """
        update_data = {
            "Stage": 4,  # Typically "Closed Won" stage
            "Probability": 100,
        }

        if actual_close_date:
            update_data["ActualCloseDate"] = actual_close_date
        else:
            update_data["ActualCloseDate"] = datetime.now().date().isoformat()

        if actual_amount is not None:
            update_data["Amount"] = actual_amount

        if win_reason:
            current_opp = self.get(opportunity_id)
            if current_opp:
                existing_desc = current_opp.get("Description", "")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_desc = f"{existing_desc}\n\n[{timestamp}] Won - Reason: {win_reason}".strip()
                update_data["Description"] = new_desc

        return self.update_by_id(opportunity_id, update_data)

    def close_opportunity_lost(
        self,
        opportunity_id: int,
        loss_reason: str,
        competitor: Optional[str] = None,
        actual_close_date: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Close an opportunity as lost.

        Args:
            opportunity_id: Opportunity ID
            loss_reason: Reason for losing the opportunity
            competitor: Optional competitor who won
            actual_close_date: Actual close date (ISO format)

        Returns:
            Updated opportunity data
        """
        update_data = {
            "Stage": 5,  # Typically "Closed Lost" stage
            "Probability": 0,
            "LossReason": loss_reason,
        }

        if actual_close_date:
            update_data["ActualCloseDate"] = actual_close_date
        else:
            update_data["ActualCloseDate"] = datetime.now().date().isoformat()

        if competitor:
            update_data["Competitor"] = competitor

        # Add to description
        current_opp = self.get(opportunity_id)
        if current_opp:
            existing_desc = current_opp.get("Description", "")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            competitor_text = f" to {competitor}" if competitor else ""
            new_desc = f"{existing_desc}\n\n[{timestamp}] Lost{competitor_text} - Reason: {loss_reason}".strip()
            update_data["Description"] = new_desc

        return self.update_by_id(opportunity_id, update_data)

    def get_sales_pipeline_report(
        self,
        owner_id: Optional[int] = None,
        include_amounts: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a sales pipeline report.

        Args:
            owner_id: Optional owner filter
            include_amounts: Whether to include amount calculations

        Returns:
            Dictionary with pipeline analysis
        """
        filters = [{"field": "Stage", "op": "lt", "value": "5"}]  # Open opportunities

        if owner_id:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        opportunities = self.query_all(filters=filters)

        # Initialize report structure
        report = {
            "total_opportunities": len(opportunities),
            "stages": {},
            "total_pipeline_value": 0.0,
            "weighted_pipeline_value": 0.0,
            "average_deal_size": 0.0,
            "largest_deal": 0.0,
            "smallest_deal": float("inf"),
            "opportunities_by_probability": {
                "high": 0,  # 80-100%
                "medium": 0,  # 50-79%
                "low": 0,  # 0-49%
            },
        }

        amounts = []

        for opp in opportunities:
            stage = opp.get("Stage", 0)
            amount = float(opp.get("Amount", 0))
            probability = int(opp.get("Probability", 0))

            # Track by stage
            if stage not in report["stages"]:
                report["stages"][stage] = {"count": 0, "value": 0.0}

            report["stages"][stage]["count"] += 1
            report["stages"][stage]["value"] += amount

            if include_amounts:
                # Calculate totals
                report["total_pipeline_value"] += amount
                report["weighted_pipeline_value"] += amount * (probability / 100)
                amounts.append(amount)

                # Track largest/smallest
                report["largest_deal"] = max(report["largest_deal"], amount)
                if amount > 0:
                    report["smallest_deal"] = min(report["smallest_deal"], amount)

            # Categorize by probability
            if probability >= 80:
                report["opportunities_by_probability"]["high"] += 1
            elif probability >= 50:
                report["opportunities_by_probability"]["medium"] += 1
            else:
                report["opportunities_by_probability"]["low"] += 1

        # Calculate averages
        if amounts:
            report["average_deal_size"] = sum(amounts) / len(amounts)

        if report["smallest_deal"] == float("inf"):
            report["smallest_deal"] = 0.0

        return report

    def get_win_loss_analysis(
        self,
        days: int = 90,
        owner_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze win/loss rates over a period.

        Args:
            days: Number of days to analyze
            owner_id: Optional owner filter

        Returns:
            Dictionary with win/loss analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        filters = [
            {
                "field": "ActualCloseDate",
                "op": "gte",
                "value": cutoff_date.date().isoformat(),
            },
            {"field": "Stage", "op": "gte", "value": "4"},  # Closed opportunities
        ]

        if owner_id:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        closed_opps = self.query_all(filters=filters)

        analysis = {
            "total_closed": len(closed_opps),
            "won_count": 0,
            "lost_count": 0,
            "win_rate": 0.0,
            "total_won_value": 0.0,
            "total_lost_value": 0.0,
            "average_won_deal_size": 0.0,
            "average_lost_deal_size": 0.0,
            "period_days": days,
        }

        won_amounts = []
        lost_amounts = []

        for opp in closed_opps:
            stage = int(opp.get("Stage", 0))
            amount = float(opp.get("Amount", 0))

            if stage == 4:  # Won
                analysis["won_count"] += 1
                analysis["total_won_value"] += amount
                won_amounts.append(amount)
            else:  # Lost
                analysis["lost_count"] += 1
                analysis["total_lost_value"] += amount
                lost_amounts.append(amount)

        # Calculate rates and averages
        if analysis["total_closed"] > 0:
            analysis["win_rate"] = (
                analysis["won_count"] / analysis["total_closed"]
            ) * 100

        if won_amounts:
            analysis["average_won_deal_size"] = sum(won_amounts) / len(won_amounts)

        if lost_amounts:
            analysis["average_lost_deal_size"] = sum(lost_amounts) / len(lost_amounts)

        return analysis

    def forecast_opportunities(
        self,
        owner_id: Optional[int] = None,
        quarters: int = 2,
        min_probability: int = 50,
    ) -> Dict[str, Any]:
        """
        Generate revenue forecast based on opportunity pipeline.

        Args:
            owner_id: Optional owner filter
            quarters: Number of quarters to forecast
            min_probability: Minimum probability to include in forecast

        Returns:
            Dictionary with forecast data
        """
        # Calculate date ranges for quarters
        today = datetime.now()
        forecast_periods = []

        for q in range(quarters):
            quarter_start = today + timedelta(days=90 * q)
            quarter_end = today + timedelta(days=90 * (q + 1))
            forecast_periods.append(
                {
                    "name": f"Q{q+1}",
                    "start": quarter_start.date().isoformat(),
                    "end": quarter_end.date().isoformat(),
                    "opportunities": 0,
                    "total_value": 0.0,
                    "weighted_value": 0.0,
                }
            )

        # Get opportunities within forecast period
        end_date = today + timedelta(days=90 * quarters)
        filters = [
            {
                "field": "ProjectedCloseDate",
                "op": "lte",
                "value": end_date.date().isoformat(),
            },
            {
                "field": "ProjectedCloseDate",
                "op": "gte",
                "value": today.date().isoformat(),
            },
            {"field": "Stage", "op": "lt", "value": "5"},  # Open
            {"field": "Probability", "op": "gte", "value": str(min_probability)},
        ]

        if owner_id:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        opportunities = self.query_all(filters=filters)

        # Assign opportunities to quarters
        for opp in opportunities:
            close_date = opp.get("ProjectedCloseDate", "")
            amount = float(opp.get("Amount", 0))
            probability = int(opp.get("Probability", 0))

            if close_date:
                opp_date = datetime.fromisoformat(close_date).date()

                for period in forecast_periods:
                    period_start = datetime.fromisoformat(period["start"]).date()
                    period_end = datetime.fromisoformat(period["end"]).date()

                    if period_start <= opp_date < period_end:
                        period["opportunities"] += 1
                        period["total_value"] += amount
                        period["weighted_value"] += amount * (probability / 100)
                        break

        forecast = {
            "forecast_date": today.date().isoformat(),
            "min_probability_threshold": min_probability,
            "periods": forecast_periods,
            "total_forecast_value": sum(p["weighted_value"] for p in forecast_periods),
            "total_pipeline_value": sum(p["total_value"] for p in forecast_periods),
            "total_opportunities": sum(p["opportunities"] for p in forecast_periods),
        }

        return forecast
