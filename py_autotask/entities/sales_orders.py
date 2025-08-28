"""
Sales Orders entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class SalesOrdersEntity(BaseEntity):
    """
    Handles Sales Order operations for the Autotask API.

    Manages the complete sales order lifecycle from creation to fulfillment,
    including order processing, status tracking, and financial management.
    """

    def __init__(self, client, entity_name: str = "SalesOrders"):
        super().__init__(client, entity_name)

    def create_sales_order(
        self,
        account_id: int,
        title: str,
        order_date: str,
        opportunity_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        owner_resource_id: Optional[int] = None,
        status: int = 1,  # Default to "New"
        **kwargs,
    ) -> EntityDict:
        """
        Create a new sales order.

        Args:
            account_id: ID of the account/company
            title: Sales order title/description
            order_date: Order date (ISO format)
            opportunity_id: Optional related opportunity ID
            contact_id: Optional primary contact ID
            owner_resource_id: Optional owner resource ID
            status: Order status (default: 1 = New)
            **kwargs: Additional order fields

        Returns:
            Created sales order data
        """
        order_data = {
            "AccountID": account_id,
            "Title": title,
            "OrderDate": order_date,
            "Status": status,
            **kwargs,
        }

        if opportunity_id is not None:
            order_data["OpportunityID"] = opportunity_id

        if contact_id is not None:
            order_data["ContactID"] = contact_id

        if owner_resource_id is not None:
            order_data["OwnerResourceID"] = owner_resource_id

        return self.create(order_data)

    def get_orders_by_account(
        self,
        account_id: int,
        status_filter: Optional[List[int]] = None,
        include_closed: bool = False,
    ) -> EntityList:
        """
        Get all sales orders for a specific account.

        Args:
            account_id: Account ID to filter by
            status_filter: Optional list of status IDs to include
            include_closed: Whether to include closed orders

        Returns:
            List of sales orders for the account
        """
        filters = [{"field": "AccountID", "op": "eq", "value": str(account_id)}]

        if status_filter:
            if len(status_filter) == 1:
                filters.append(
                    {"field": "Status", "op": "eq", "value": str(status_filter[0])}
                )
            else:
                filters.append(
                    {
                        "field": "Status",
                        "op": "in",
                        "value": [str(s) for s in status_filter],
                    }
                )

        if not include_closed:
            # Exclude typically closed status (assuming 5+ are closed statuses)
            filters.append({"field": "Status", "op": "lt", "value": "5"})

        return self.query_all(filters=filters)

    def get_orders_by_status(
        self,
        status: int,
        account_id: Optional[int] = None,
        owner_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get sales orders filtered by status.

        Args:
            status: Status ID to filter by
            account_id: Optional account filter
            owner_id: Optional owner filter

        Returns:
            List of sales orders with specified status
        """
        filters = [{"field": "Status", "op": "eq", "value": str(status)}]

        if account_id is not None:
            filters.append({"field": "AccountID", "op": "eq", "value": str(account_id)})

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        return self.query_all(filters=filters)

    def get_orders_by_opportunity(self, opportunity_id: int) -> EntityList:
        """
        Get sales orders related to a specific opportunity.

        Args:
            opportunity_id: Opportunity ID

        Returns:
            List of sales orders for the opportunity
        """
        filters = [{"field": "OpportunityID", "op": "eq", "value": str(opportunity_id)}]
        return self.query_all(filters=filters)

    def get_recent_orders(
        self,
        days: int = 30,
        owner_id: Optional[int] = None,
        account_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get recent sales orders within specified timeframe.

        Args:
            days: Number of days to look back
            owner_id: Optional owner filter
            account_id: Optional account filter

        Returns:
            List of recent sales orders
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        filters = [{"field": "OrderDate", "op": "gte", "value": cutoff_date}]

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        if account_id is not None:
            filters.append({"field": "AccountID", "op": "eq", "value": str(account_id)})

        return self.query_all(filters=filters)

    def update_order_status(
        self,
        order_id: int,
        new_status: int,
        status_note: Optional[str] = None,
        notify_stakeholders: bool = False,
    ) -> Optional[EntityDict]:
        """
        Update a sales order status.

        Args:
            order_id: Sales order ID
            new_status: New status ID
            status_note: Optional note about status change
            notify_stakeholders: Whether to notify stakeholders

        Returns:
            Updated sales order data
        """
        update_data = {"Status": new_status}

        if status_note:
            # Add status change note to description or notes field
            current_order = self.get(order_id)
            if current_order:
                existing_desc = current_order.get("Description", "")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                status_change_note = (
                    f"\n\n[{timestamp}] Status changed to {new_status}: {status_note}"
                )
                update_data["Description"] = existing_desc + status_change_note

        # Note: notify_stakeholders would trigger notification logic
        if notify_stakeholders:
            self.logger.info(
                f"Sales order {order_id} status updated - stakeholders should be notified"
            )

        return self.update_by_id(order_id, update_data)

    def approve_sales_order(
        self,
        order_id: int,
        approved_by: int,
        approval_note: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Approve a sales order.

        Args:
            order_id: Sales order ID
            approved_by: ID of approving resource
            approval_note: Optional approval note

        Returns:
            Updated sales order data
        """
        update_data = {
            "Status": 2,  # Assuming 2 = Approved
            "ApprovedBy": approved_by,
            "ApprovedDate": datetime.now().isoformat(),
        }

        if approval_note:
            current_order = self.get(order_id)
            if current_order:
                existing_desc = current_order.get("Description", "")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                approval_text = f"\n\n[{timestamp}] Approved by Resource {approved_by}: {approval_note}"
                update_data["Description"] = existing_desc + approval_text

        return self.update_by_id(order_id, update_data)

    def reject_sales_order(
        self,
        order_id: int,
        rejected_by: int,
        rejection_reason: str,
    ) -> Optional[EntityDict]:
        """
        Reject a sales order.

        Args:
            order_id: Sales order ID
            rejected_by: ID of rejecting resource
            rejection_reason: Reason for rejection

        Returns:
            Updated sales order data
        """
        update_data = {
            "Status": 6,  # Assuming 6 = Rejected
            "RejectedBy": rejected_by,
            "RejectedDate": datetime.now().isoformat(),
            "RejectionReason": rejection_reason,
        }

        # Add rejection note to description
        current_order = self.get(order_id)
        if current_order:
            existing_desc = current_order.get("Description", "")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            rejection_text = f"\n\n[{timestamp}] REJECTED by Resource {rejected_by}: {rejection_reason}"
            update_data["Description"] = existing_desc + rejection_text

        return self.update_by_id(order_id, update_data)

    def get_order_total_value(self, order_id: int) -> Dict[str, Any]:
        """
        Calculate the total value of a sales order including all line items.

        Args:
            order_id: Sales order ID

        Returns:
            Dictionary with order value information
        """
        # This would typically query SalesOrderItems
        try:
            filters = [{"field": "SalesOrderID", "op": "eq", "value": str(order_id)}]
            order_items = self.client.query(
                "SalesOrderItems", {"filter": filters}
            ).items
        except Exception:
            order_items = []

        totals = {
            "order_id": order_id,
            "total_items": len(order_items),
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "shipping_amount": 0.0,
            "discount_amount": 0.0,
            "total_amount": 0.0,
            "currency": "USD",  # Default, would come from order
        }

        for item in order_items:
            quantity = float(item.get("Quantity", 0))
            unit_price = float(item.get("UnitPrice", 0))
            line_total = quantity * unit_price
            totals["subtotal"] += line_total

        # Get order-level adjustments
        order = self.get(order_id)
        if order:
            totals["tax_amount"] = float(order.get("TaxAmount", 0))
            totals["shipping_amount"] = float(order.get("ShippingAmount", 0))
            totals["discount_amount"] = float(order.get("DiscountAmount", 0))
            totals["currency"] = order.get("Currency", "USD")

        # Calculate final total
        totals["total_amount"] = (
            totals["subtotal"]
            + totals["tax_amount"]
            + totals["shipping_amount"]
            - totals["discount_amount"]
        )

        return totals

    def get_fulfillment_status(self, order_id: int) -> Dict[str, Any]:
        """
        Get fulfillment status for a sales order.

        Args:
            order_id: Sales order ID

        Returns:
            Dictionary with fulfillment information
        """
        # This would typically query order items and shipments
        try:
            filters = [{"field": "SalesOrderID", "op": "eq", "value": str(order_id)}]
            order_items = self.client.query(
                "SalesOrderItems", {"filter": filters}
            ).items
        except Exception:
            order_items = []

        fulfillment = {
            "order_id": order_id,
            "total_items": len(order_items),
            "items_shipped": 0,
            "items_pending": 0,
            "items_cancelled": 0,
            "fulfillment_percentage": 0.0,
            "estimated_ship_date": None,
            "tracking_numbers": [],
        }

        for item in order_items:
            status = item.get("Status", "pending")
            if status.lower() in ["shipped", "delivered"]:
                fulfillment["items_shipped"] += 1
            elif status.lower() == "cancelled":
                fulfillment["items_cancelled"] += 1
            else:
                fulfillment["items_pending"] += 1

        # Calculate fulfillment percentage
        if fulfillment["total_items"] > 0:
            fulfillment["fulfillment_percentage"] = (
                fulfillment["items_shipped"] / fulfillment["total_items"]
            ) * 100

        return fulfillment

    def get_orders_requiring_approval(
        self, owner_id: Optional[int] = None
    ) -> EntityList:
        """
        Get sales orders that require approval.

        Args:
            owner_id: Optional owner filter

        Returns:
            List of orders requiring approval
        """
        filters = [
            {"field": "Status", "op": "eq", "value": "1"}
        ]  # Assuming 1 = Pending Approval

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        return self.query_all(filters=filters)

    def get_overdue_orders(self, owner_id: Optional[int] = None) -> EntityList:
        """
        Get sales orders that are overdue (past expected delivery date).

        Args:
            owner_id: Optional owner filter

        Returns:
            List of overdue orders
        """
        today = datetime.now().date().isoformat()
        filters = [
            {"field": "ExpectedDeliveryDate", "op": "lt", "value": today},
            {
                "field": "Status",
                "op": "not_in",
                "value": ["5", "6", "7"],
            },  # Not closed/cancelled
        ]

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        return self.query_all(filters=filters)

    def get_sales_order_pipeline(
        self, owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get sales order pipeline analysis.

        Args:
            owner_id: Optional owner filter

        Returns:
            Dictionary with pipeline statistics
        """
        filters = []
        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        orders = self.query_all(filters=filters)

        pipeline = {
            "total_orders": len(orders),
            "orders_by_status": {},
            "total_pipeline_value": 0.0,
            "average_order_value": 0.0,
            "orders_by_month": {},
            "top_accounts": {},
        }

        total_value = 0.0
        order_values = []

        for order in orders:
            # Count by status
            status = order.get("Status", "unknown")
            if status not in pipeline["orders_by_status"]:
                pipeline["orders_by_status"][status] = 0
            pipeline["orders_by_status"][status] += 1

            # Get order value
            order_value = self.get_order_total_value(int(order["id"]))
            total_value += order_value["total_amount"]
            order_values.append(order_value["total_amount"])

            # Count by month
            order_date = order.get("OrderDate", "")
            if order_date:
                month_key = order_date[:7]  # YYYY-MM
                if month_key not in pipeline["orders_by_month"]:
                    pipeline["orders_by_month"][month_key] = 0
                pipeline["orders_by_month"][month_key] += 1

            # Count by account
            account_id = order.get("AccountID")
            if account_id:
                if account_id not in pipeline["top_accounts"]:
                    pipeline["top_accounts"][account_id] = 0
                pipeline["top_accounts"][account_id] += 1

        pipeline["total_pipeline_value"] = total_value
        if order_values:
            pipeline["average_order_value"] = total_value / len(order_values)

        # Sort top accounts
        pipeline["top_accounts"] = dict(
            sorted(pipeline["top_accounts"].items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
        )

        return pipeline

    def bulk_update_order_status(
        self,
        order_ids: List[int],
        new_status: int,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update status for multiple sales orders.

        Args:
            order_ids: List of order IDs to update
            new_status: New status for all orders
            reason: Optional reason for status change

        Returns:
            Dictionary with bulk update results
        """
        results = {
            "total_requested": len(order_ids),
            "successful_updates": [],
            "failed_updates": [],
            "new_status": new_status,
        }

        for order_id in order_ids:
            try:
                updated_order = self.update_order_status(order_id, new_status, reason)
                if updated_order:
                    results["successful_updates"].append(order_id)
                else:
                    results["failed_updates"].append(
                        {"order_id": order_id, "error": "Update returned no data"}
                    )
            except Exception as e:
                results["failed_updates"].append(
                    {"order_id": order_id, "error": str(e)}
                )

        return results

    def search_orders_by_reference(self, reference: str) -> EntityList:
        """
        Search sales orders by reference number or external identifier.

        Args:
            reference: Reference to search for

        Returns:
            List of matching sales orders
        """
        # Search in multiple fields
        filters = [
            [
                {"field": "ReferenceNumber", "op": "contains", "value": reference},
                {"field": "ExternalID", "op": "contains", "value": reference},
                {"field": "PurchaseOrderNumber", "op": "contains", "value": reference},
            ]
        ]
        return self.query_all(filters=filters)

    def generate_order_summary_report(
        self,
        start_date: str,
        end_date: str,
        owner_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive order summary report.

        Args:
            start_date: Report start date (ISO format)
            end_date: Report end date (ISO format)
            owner_id: Optional owner filter

        Returns:
            Dictionary with comprehensive order statistics
        """
        filters = [
            {"field": "OrderDate", "op": "gte", "value": start_date},
            {"field": "OrderDate", "op": "lte", "value": end_date},
        ]

        if owner_id is not None:
            filters.append(
                {"field": "OwnerResourceID", "op": "eq", "value": str(owner_id)}
            )

        orders = self.query_all(filters=filters)

        report = {
            "report_period": {"start": start_date, "end": end_date},
            "total_orders": len(orders),
            "orders_by_status": {},
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "conversion_metrics": {
                "approved_orders": 0,
                "rejected_orders": 0,
                "pending_orders": 0,
                "approval_rate": 0.0,
            },
            "top_performing_accounts": {},
            "monthly_trends": {},
        }

        total_value = 0.0
        order_values = []

        for order in orders:
            status = int(order.get("Status", 0))

            # Count by status
            if status not in report["orders_by_status"]:
                report["orders_by_status"][status] = 0
            report["orders_by_status"][status] += 1

            # Track conversion metrics
            if status >= 2 and status <= 4:  # Approved statuses
                report["conversion_metrics"]["approved_orders"] += 1
            elif status >= 6:  # Rejected/cancelled statuses
                report["conversion_metrics"]["rejected_orders"] += 1
            else:  # Pending statuses
                report["conversion_metrics"]["pending_orders"] += 1

            # Calculate revenue
            order_value = self.get_order_total_value(int(order["id"]))
            value = order_value["total_amount"]
            total_value += value
            order_values.append(value)

            # Track by account
            account_id = order.get("AccountID")
            if account_id:
                if account_id not in report["top_performing_accounts"]:
                    report["top_performing_accounts"][account_id] = {
                        "orders": 0,
                        "revenue": 0.0,
                    }
                report["top_performing_accounts"][account_id]["orders"] += 1
                report["top_performing_accounts"][account_id]["revenue"] += value

            # Monthly trends
            order_date = order.get("OrderDate", "")
            if order_date:
                month_key = order_date[:7]  # YYYY-MM
                if month_key not in report["monthly_trends"]:
                    report["monthly_trends"][month_key] = {"orders": 0, "revenue": 0.0}
                report["monthly_trends"][month_key]["orders"] += 1
                report["monthly_trends"][month_key]["revenue"] += value

        # Calculate totals and averages
        report["total_revenue"] = total_value
        if order_values:
            report["average_order_value"] = total_value / len(order_values)

        # Calculate approval rate
        total_decided = (
            report["conversion_metrics"]["approved_orders"]
            + report["conversion_metrics"]["rejected_orders"]
        )
        if total_decided > 0:
            report["conversion_metrics"]["approval_rate"] = (
                report["conversion_metrics"]["approved_orders"] / total_decided
            ) * 100

        # Sort top accounts by revenue
        report["top_performing_accounts"] = dict(
            sorted(
                report["top_performing_accounts"].items(),
                key=lambda x: x[1]["revenue"],
                reverse=True,
            )[:10]
        )

        return report
