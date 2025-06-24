"""
Subscriptions Entity for py-autotask

This module provides the SubscriptionsEntity class for managing subscriptions
in Autotask. Subscriptions handle recurring services, licensing, and ongoing
service agreements with automated billing capabilities.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class SubscriptionsEntity(BaseEntity):
    """
    Manages Autotask Subscriptions - recurring service and licensing management.

    Subscriptions represent ongoing service agreements, software licenses,
    and recurring billing arrangements. They support automated billing,
    usage tracking, and subscription lifecycle management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Subscriptions"

    def create_subscription(
        self,
        account_id: int,
        subscription_name: str,
        billing_period: str,
        unit_price: Union[float, Decimal],
        quantity: Union[int, Decimal] = 1,
        start_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new subscription.

        Args:
            account_id: ID of the account for this subscription
            subscription_name: Name/description of the subscription
            billing_period: Billing period (Monthly, Quarterly, Annually)
            unit_price: Price per unit for the subscription
            quantity: Quantity of units subscribed
            start_date: Start date for the subscription
            **kwargs: Additional fields for the subscription

        Returns:
            Create response with new subscription ID
        """
        subscription_data = {
            "accountID": account_id,
            "subscriptionName": subscription_name,
            "billingPeriod": billing_period,
            "unitPrice": float(unit_price),
            "quantity": float(quantity),
            **kwargs,
        }

        if start_date:
            subscription_data["startDate"] = start_date.isoformat()

        return self.create(subscription_data)

    def get_active_subscriptions(
        self, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active subscriptions.

        Args:
            account_id: Optional account ID to filter by

        Returns:
            List of active subscriptions
        """
        filters = ["status eq 'Active'"]

        if account_id:
            filters.append(f"accountID eq {account_id}")

        return self.query(filter=" and ".join(filters))

    def get_subscriptions_by_account(
        self, account_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get subscriptions for a specific account.

        Args:
            account_id: ID of the account
            include_inactive: Whether to include inactive subscriptions

        Returns:
            List of subscriptions for the account
        """
        filters = [f"accountID eq {account_id}"]

        if not include_inactive:
            filters.append("status eq 'Active'")

        return self.query(filter=" and ".join(filters))

    def get_expiring_subscriptions(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Get subscriptions expiring within specified days.

        Args:
            days_ahead: Number of days to look ahead for expiring subscriptions

        Returns:
            List of expiring subscriptions
        """
        from datetime import timedelta

        cutoff_date = date.today() + timedelta(days=days_ahead)

        return self.query(
            filter=f"endDate le {cutoff_date.isoformat()} and status eq 'Active'"
        )

    def renew_subscription(
        self,
        subscription_id: int,
        new_end_date: date,
        new_unit_price: Optional[Union[float, Decimal]] = None,
        new_quantity: Optional[Union[int, Decimal]] = None,
    ) -> Dict[str, Any]:
        """
        Renew a subscription with new terms.

        Args:
            subscription_id: ID of the subscription to renew
            new_end_date: New end date for the subscription
            new_unit_price: Optional new unit price
            new_quantity: Optional new quantity

        Returns:
            Update response
        """
        update_data = {"endDate": new_end_date.isoformat(), "status": "Active"}

        if new_unit_price is not None:
            update_data["unitPrice"] = float(new_unit_price)
        if new_quantity is not None:
            update_data["quantity"] = float(new_quantity)

        return self.update(subscription_id, update_data)

    def cancel_subscription(
        self,
        subscription_id: int,
        cancellation_date: Optional[date] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: ID of the subscription to cancel
            cancellation_date: Date of cancellation (defaults to today)
            reason: Optional reason for cancellation

        Returns:
            Update response
        """
        if cancellation_date is None:
            cancellation_date = date.today()

        update_data = {"status": "Cancelled", "endDate": cancellation_date.isoformat()}

        if reason:
            update_data["cancellationReason"] = reason

        return self.update(subscription_id, update_data)

    def calculate_subscription_revenue(
        self,
        subscription_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Calculate revenue for a subscription over a period.

        Args:
            subscription_id: ID of the subscription
            date_from: Start date for calculation
            date_to: End date for calculation

        Returns:
            Revenue calculation details
        """
        subscription = self.get(subscription_id)

        unit_price = Decimal(str(subscription.get("unitPrice", 0)))
        quantity = Decimal(str(subscription.get("quantity", 1)))

        # This would typically calculate based on billing period and dates
        # For now, return basic calculation structure

        return {
            "subscription_id": subscription_id,
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "calculation": {
                "unit_price": unit_price,
                "quantity": quantity,
                "total_revenue": unit_price * quantity,  # Simplified calculation
                "billing_periods": 1,  # Would calculate actual periods
            },
        }

    def get_subscription_analytics(
        self,
        account_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get subscription analytics for account or overall.

        Args:
            account_id: Optional account ID to filter by
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Subscription analytics summary
        """
        filters = []

        if account_id:
            filters.append(f"accountID eq {account_id}")
        if date_from:
            filters.append(f"startDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"startDate le {date_to.isoformat()}")

        subscriptions = self.query(filter=" and ".join(filters) if filters else None)

        # Analyze subscriptions
        total_revenue = Decimal("0")
        active_count = 0
        cancelled_count = 0

        for sub in subscriptions:
            if sub.get("status") == "Active":
                active_count += 1
            elif sub.get("status") == "Cancelled":
                cancelled_count += 1

            unit_price = Decimal(str(sub.get("unitPrice", 0)))
            quantity = Decimal(str(sub.get("quantity", 1)))
            total_revenue += unit_price * quantity

        return {
            "account_id": account_id,
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "summary": {
                "total_subscriptions": len(subscriptions),
                "active_subscriptions": active_count,
                "cancelled_subscriptions": cancelled_count,
                "total_revenue": total_revenue,
                "average_subscription_value": (
                    total_revenue / len(subscriptions)
                    if subscriptions
                    else Decimal("0")
                ),
            },
        }

    def bulk_renew_subscriptions(
        self, subscription_renewals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Renew multiple subscriptions in bulk.

        Args:
            subscription_renewals: List of renewal instructions
                Each should contain: subscription_id, new_end_date, optional pricing

        Returns:
            Summary of bulk renewal operation
        """
        results = []

        for renewal in subscription_renewals:
            subscription_id = renewal["subscription_id"]
            new_end_date = renewal["new_end_date"]
            new_unit_price = renewal.get("new_unit_price")
            new_quantity = renewal.get("new_quantity")

            try:
                result = self.renew_subscription(
                    subscription_id, new_end_date, new_unit_price, new_quantity
                )
                results.append(
                    {"id": subscription_id, "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"id": subscription_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_renewals": len(subscription_renewals),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_subscription_usage_tracking(
        self,
        subscription_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get usage tracking data for a subscription.

        Args:
            subscription_id: ID of the subscription
            date_from: Start date for usage tracking
            date_to: End date for usage tracking

        Returns:
            Usage tracking summary
        """
        # This would typically query usage data from related entities
        # For now, return structure that could be populated

        return {
            "subscription_id": subscription_id,
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "usage_data": {
                "total_usage": 0,  # Would track actual usage
                "billable_usage": 0,  # Would track billable usage
                "overage_charges": Decimal("0"),  # Would calculate overages
                "utilization_rate": 0.0,  # Would calculate utilization
            },
        }
