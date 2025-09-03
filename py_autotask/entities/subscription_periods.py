"""
SubscriptionPeriods Entity for py-autotask

This module provides the SubscriptionPeriodsEntity class for managing subscription
billing periods in Autotask. Subscription Periods define billing cycles, renewal
dates, and period-specific configurations for recurring services.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class SubscriptionPeriodsEntity(BaseEntity):
    """
    Manages Autotask SubscriptionPeriods - subscription billing cycles and periods.

    Subscription Periods define the billing cycles, renewal dates, and period-specific
    configurations for recurring services and subscriptions. They support automated
    billing calculations, proration handling, and subscription lifecycle management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "SubscriptionPeriods"

    def create_subscription_period(
        self,
        subscription_id: int,
        period_type: str,
        start_date: date,
        end_date: date,
        billing_amount: float,
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new subscription period.

        Args:
            subscription_id: ID of the subscription
            period_type: Type of period (monthly, quarterly, annual, etc.)
            start_date: Start date of the period
            end_date: End date of the period
            billing_amount: Amount to bill for this period
            is_active: Whether the period is active
            **kwargs: Additional fields for the subscription period

        Returns:
            Create response with new subscription period ID
        """
        period_data = {
            "subscriptionID": subscription_id,
            "periodType": period_type,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "billingAmount": billing_amount,
            "isActive": is_active,
            **kwargs,
        }

        return self.create(period_data)

    def get_periods_by_subscription(
        self, subscription_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get periods for a specific subscription.

        Args:
            subscription_id: ID of the subscription
            include_inactive: Whether to include inactive periods

        Returns:
            List of periods for the subscription
        """
        filters = [
            {"field": "subscriptionID", "op": "eq", "value": str(subscription_id)}
        ]

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": "true"})

        return self.query(filters=filters).items

    def get_current_periods(
        self, subscription_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get currently active subscription periods.

        Args:
            subscription_ids: Optional list of subscription IDs to filter by

        Returns:
            List of current active periods
        """
        today = date.today().isoformat()

        filters = [
            {"field": "isActive", "op": "eq", "value": "true"},
            {"field": "startDate", "op": "lte", "value": today},
            {"field": "endDate", "op": "gte", "value": today},
        ]

        if subscription_ids:
            subscription_filter = {
                "field": "subscriptionID",
                "op": "in",
                "value": [str(sid) for sid in subscription_ids],
            }
            filters.append(subscription_filter)

        return self.query(filters=filters).items

    def get_periods_for_billing(
        self, billing_date: date, period_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get periods that should be billed on a specific date.

        Args:
            billing_date: Date to check for billing
            period_types: Optional list of period types to include

        Returns:
            List of periods to be billed
        """
        filters = [
            {"field": "isActive", "op": "eq", "value": "true"},
            {"field": "billingDate", "op": "eq", "value": billing_date.isoformat()},
        ]

        if period_types:
            period_filter = {"field": "periodType", "op": "in", "value": period_types}
            filters.append(period_filter)

        return self.query(filters=filters).items

    def calculate_proration(
        self,
        subscription_id: int,
        change_date: date,
        new_amount: float,
        proration_method: str = "daily",
    ) -> Dict[str, Any]:
        """
        Calculate prorated amount for subscription changes.

        Args:
            subscription_id: ID of the subscription
            change_date: Date when the change occurs
            new_amount: New billing amount
            proration_method: Method for calculating proration (daily, none)

        Returns:
            Proration calculation results
        """
        current_periods = self.get_periods_by_subscription(subscription_id)
        current_period = None

        # Find the current active period
        for period in current_periods:
            period_start = datetime.fromisoformat(period["startDate"]).date()
            period_end = datetime.fromisoformat(period["endDate"]).date()

            if period_start <= change_date <= period_end:
                current_period = period
                break

        if not current_period:
            return {
                "subscription_id": subscription_id,
                "change_date": change_date.isoformat(),
                "error": "No active period found for change date",
            }

        period_start = datetime.fromisoformat(current_period["startDate"]).date()
        period_end = datetime.fromisoformat(current_period["endDate"]).date()
        current_amount = float(current_period["billingAmount"])

        total_days = (period_end - period_start).days + 1
        remaining_days = (period_end - change_date).days + 1
        used_days = total_days - remaining_days

        if proration_method == "daily":
            daily_rate_old = current_amount / total_days
            daily_rate_new = new_amount / total_days

            used_amount = daily_rate_old * used_days
            remaining_amount_old = daily_rate_old * remaining_days
            remaining_amount_new = daily_rate_new * remaining_days

            proration_adjustment = remaining_amount_new - remaining_amount_old
        else:
            # No proration
            proration_adjustment = 0.0
            used_amount = 0.0
            remaining_amount_old = 0.0
            remaining_amount_new = 0.0

        return {
            "subscription_id": subscription_id,
            "current_period_id": current_period["id"],
            "change_date": change_date.isoformat(),
            "period_details": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
                "total_days": total_days,
                "used_days": used_days,
                "remaining_days": remaining_days,
            },
            "amounts": {
                "current_period_amount": current_amount,
                "new_period_amount": new_amount,
                "used_amount": round(used_amount, 2),
                "remaining_old_amount": round(remaining_amount_old, 2),
                "remaining_new_amount": round(remaining_amount_new, 2),
                "proration_adjustment": round(proration_adjustment, 2),
            },
            "proration_method": proration_method,
        }

    def generate_next_period(
        self, current_period_id: int, auto_renew: bool = True
    ) -> Dict[str, Any]:
        """
        Generate the next period for a subscription.

        Args:
            current_period_id: ID of the current period
            auto_renew: Whether to automatically create the next period

        Returns:
            Next period details or creation result
        """
        current_period = self.get(current_period_id)

        if not current_period:
            raise ValueError(f"Period {current_period_id} not found")

        period_end = datetime.fromisoformat(current_period["endDate"]).date()
        period_type = current_period["periodType"]

        # Calculate next period dates based on type
        if period_type == "monthly":
            next_start = period_end + timedelta(days=1)
            next_end = next_start + timedelta(days=30)  # Approximation
        elif period_type == "quarterly":
            next_start = period_end + timedelta(days=1)
            next_end = next_start + timedelta(days=90)  # Approximation
        elif period_type == "annually":
            next_start = period_end + timedelta(days=1)
            next_end = next_start + timedelta(days=365)  # Approximation
        else:
            # Use current period length
            period_length = (
                period_end - datetime.fromisoformat(current_period["startDate"]).date()
            ).days
            next_start = period_end + timedelta(days=1)
            next_end = next_start + timedelta(days=period_length)

        next_period_data = {
            "subscription_id": current_period["subscriptionID"],
            "period_type": period_type,
            "start_date": next_start,
            "end_date": next_end,
            "billing_amount": float(current_period["billingAmount"]),
            "auto_generated": True,
            "previous_period_id": current_period_id,
        }

        if auto_renew:
            # Create the next period
            result = self.create_subscription_period(**next_period_data)
            return {
                "action": "created",
                "next_period": result,
                "period_details": next_period_data,
            }
        else:
            # Return details without creating
            return {
                "action": "preview",
                "next_period": None,
                "period_details": next_period_data,
            }

    def get_expiring_periods(
        self, days_ahead: int = 30, period_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get periods expiring within a specified number of days.

        Args:
            days_ahead: Number of days to look ahead
            period_types: Optional list of period types to include

        Returns:
            List of expiring periods
        """
        today = date.today()
        expiry_date = today + timedelta(days=days_ahead)

        filters = [
            {"field": "isActive", "op": "eq", "value": "true"},
            {"field": "endDate", "op": "gte", "value": today.isoformat()},
            {"field": "endDate", "op": "lte", "value": expiry_date.isoformat()},
        ]

        if period_types:
            period_filter = {"field": "periodType", "op": "in", "value": period_types}
            filters.append(period_filter)

        expiring_periods = self.query(filters=filters).items

        # Add days until expiry to each period
        for period in expiring_periods:
            period_end = datetime.fromisoformat(period["endDate"]).date()
            days_until_expiry = (period_end - today).days
            period["days_until_expiry"] = days_until_expiry

        # Sort by days until expiry
        expiring_periods.sort(key=lambda x: x["days_until_expiry"])
        return expiring_periods

    def bulk_renew_periods(
        self,
        period_ids: List[int],
        renewal_adjustments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Bulk renew multiple subscription periods.

        Args:
            period_ids: List of period IDs to renew
            renewal_adjustments: Optional adjustments for renewal (amount_multiplier, etc.)

        Returns:
            Summary of bulk renewal operation
        """
        results = []
        amount_multiplier = (
            renewal_adjustments.get("amount_multiplier", 1.0)
            if renewal_adjustments
            else 1.0
        )

        for period_id in period_ids:
            try:
                current_period = self.get(period_id)
                if not current_period:
                    results.append(
                        {
                            "period_id": period_id,
                            "success": False,
                            "error": "Period not found",
                        }
                    )
                    continue

                # Apply amount adjustment if specified
                if amount_multiplier != 1.0:
                    new_amount = (
                        float(current_period["billingAmount"]) * amount_multiplier
                    )
                    self.update({"id": period_id, "billingAmount": new_amount})

                # Generate next period
                renewal_result = self.generate_next_period(period_id, auto_renew=True)

                results.append(
                    {
                        "period_id": period_id,
                        "subscription_id": current_period["subscriptionID"],
                        "success": True,
                        "next_period_id": renewal_result["next_period"]["item_id"],
                        "next_period_dates": {
                            "start_date": renewal_result["period_details"][
                                "start_date"
                            ].isoformat(),
                            "end_date": renewal_result["period_details"][
                                "end_date"
                            ].isoformat(),
                        },
                    }
                )

            except Exception as e:
                results.append(
                    {"period_id": period_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_periods": len(period_ids),
            "successful_renewals": len(successful),
            "failed_renewals": len(failed),
            "renewal_adjustments": renewal_adjustments,
            "results": results,
        }

    def get_revenue_forecast(
        self, months_ahead: int = 12, subscription_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Generate revenue forecast based on subscription periods.

        Args:
            months_ahead: Number of months to forecast
            subscription_ids: Optional list of subscription IDs to include

        Returns:
            Revenue forecast analysis
        """
        end_forecast_date = date.today() + timedelta(days=months_ahead * 30)

        filters = [
            {"field": "isActive", "op": "eq", "value": "true"},
            {"field": "endDate", "op": "lte", "value": end_forecast_date.isoformat()},
        ]

        if subscription_ids:
            subscription_filter = {
                "field": "subscriptionID",
                "op": "in",
                "value": [str(sid) for sid in subscription_ids],
            }
            filters.append(subscription_filter)

        periods = self.query(filters=filters).items

        # Group revenue by month
        monthly_revenue = {}
        total_forecast = 0.0

        for period in periods:
            billing_amount = float(period["billingAmount"])
            period_start = datetime.fromisoformat(period["startDate"]).date()
            period_end = datetime.fromisoformat(period["endDate"]).date()

            # Allocate revenue to months within the period
            current_date = period_start
            while current_date <= period_end and current_date <= end_forecast_date:
                month_key = current_date.strftime("%Y-%m")

                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = 0.0

                # For simplicity, allocate full amount to first month of period
                if current_date == period_start:
                    monthly_revenue[month_key] += billing_amount
                    total_forecast += billing_amount

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        return {
            "forecast_period": {
                "start_date": date.today().isoformat(),
                "end_date": end_forecast_date.isoformat(),
                "months_ahead": months_ahead,
            },
            "total_forecasted_revenue": round(total_forecast, 2),
            "monthly_breakdown": {
                month: round(amount, 2)
                for month, amount in sorted(monthly_revenue.items())
            },
            "average_monthly_revenue": (
                round(total_forecast / months_ahead, 2) if months_ahead > 0 else 0.0
            ),
            "periods_included": len(periods),
            "subscription_filter": subscription_ids,
        }

    def suspend_period(
        self, period_id: int, suspension_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suspend a subscription period.

        Args:
            period_id: ID of the period to suspend
            suspension_reason: Optional reason for suspension

        Returns:
            Updated period data
        """
        update_data = {
            "id": period_id,
            "isSuspended": True,
            "suspensionDate": datetime.now().isoformat(),
        }

        if suspension_reason:
            update_data["suspensionReason"] = suspension_reason

        return self.update(update_data)

    def reactivate_period(
        self, period_id: int, reactivation_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reactivate a suspended subscription period.

        Args:
            period_id: ID of the period to reactivate
            reactivation_notes: Optional notes about reactivation

        Returns:
            Updated period data
        """
        update_data = {
            "id": period_id,
            "isSuspended": False,
            "reactivationDate": datetime.now().isoformat(),
        }

        if reactivation_notes:
            update_data["reactivationNotes"] = reactivation_notes

        return self.update(update_data)
