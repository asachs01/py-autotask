"""
Purchase Orders entity for Autotask API.

This module provides the PurchaseOrdersEntity class for managing
purchase orders within the Autotask system.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class PurchaseOrdersEntity(BaseEntity):
    """
    Entity for managing Autotask Purchase Orders.

    Purchase Orders represent procurement documents for purchasing
    goods and services from vendors.
    """

    def __init__(self, client, entity_name="PurchaseOrders"):
        """Initialize the Purchase Orders entity."""
        super().__init__(client, entity_name)

    def create(self, purchase_order_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new purchase order.

        Args:
            purchase_order_data: Dictionary containing purchase order information
                Required fields:
                - vendorAccountID: ID of the vendor account
                - purchaseOrderDate: Date of the purchase order
                - requestedBy: ID of the person requesting the order
                Optional fields:
                - purchaseOrderNumber: PO number (auto-generated if not provided)
                - description: Description of the purchase order
                - expectedDeliveryDate: Expected delivery date
                - shippingType: Shipping method
                - paymentTerms: Payment terms
                - vendorInvoiceNumber: Vendor's invoice number
                - totalCost: Total cost of the order
                - status: Order status
                - comments: Additional comments

        Returns:
            CreateResponse: Response containing created purchase order data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["vendorAccountID", "purchaseOrderDate", "requestedBy"]
        self._validate_required_fields(purchase_order_data, required_fields)

        return self._create(purchase_order_data)

    def get(self, purchase_order_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a purchase order by ID.

        Args:
            purchase_order_id: The purchase order ID

        Returns:
            Dictionary containing purchase order data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(purchase_order_id)

    def update(
        self, purchase_order_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing purchase order.

        Args:
            purchase_order_id: The purchase order ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated purchase order data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(purchase_order_id, update_data)

    def delete(self, purchase_order_id: int) -> bool:
        """
        Delete a purchase order.

        Args:
            purchase_order_id: The purchase order ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(purchase_order_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query purchase orders with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing purchase order data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_vendor(self, vendor_account_id: int) -> List[Dict[str, Any]]:
        """
        Get all purchase orders for a specific vendor.

        Args:
            vendor_account_id: The vendor account ID

        Returns:
            List of purchase orders for the specified vendor

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="vendorAccountID", op="eq", value=vendor_account_id)
        ]
        return self.query(filters)

    def get_by_status(
        self, status: str, vendor_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get purchase orders by status.

        Args:
            status: Purchase order status to filter by
            vendor_id: Optional vendor ID to filter by

        Returns:
            List of purchase orders with the specified status

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="eq", value=status)]

        if vendor_id:
            filters.append(
                QueryFilter(field="vendorAccountID", op="eq", value=vendor_id)
            )

        return self.query(filters)

    def get_by_date_range(
        self, start_date: date, end_date: date, vendor_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get purchase orders within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            vendor_id: Optional vendor ID to filter by

        Returns:
            List of purchase orders within the date range

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(
                field="purchaseOrderDate", op="gte", value=start_date.isoformat()
            ),
            QueryFilter(
                field="purchaseOrderDate", op="lte", value=end_date.isoformat()
            ),
        ]

        if vendor_id:
            filters.append(
                QueryFilter(field="vendorAccountID", op="eq", value=vendor_id)
            )

        return self.query(filters)

    def get_pending_orders(
        self, vendor_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending purchase orders.

        Args:
            vendor_id: Optional vendor ID to filter by

        Returns:
            List of pending purchase orders

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="eq", value="Pending")]

        if vendor_id:
            filters.append(
                QueryFilter(field="vendorAccountID", op="eq", value=vendor_id)
            )

        return self.query(filters)

    def get_overdue_orders(
        self, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get overdue purchase orders (past expected delivery date).

        Args:
            as_of_date: Date to check overdue status against (default: today)

        Returns:
            List of overdue purchase orders

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if as_of_date is None:
            as_of_date = date.today()

        filters = [
            QueryFilter(
                field="expectedDeliveryDate", op="lt", value=as_of_date.isoformat()
            ),
            QueryFilter(field="status", op="ne", value="Delivered"),
            QueryFilter(field="status", op="ne", value="Cancelled"),
        ]

        return self.query(filters)

    def get_by_requester(self, requester_id: int) -> List[Dict[str, Any]]:
        """
        Get purchase orders by requester.

        Args:
            requester_id: The requester's resource ID

        Returns:
            List of purchase orders requested by the specified person

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="requestedBy", op="eq", value=requester_id)]
        return self.query(filters)

    def calculate_order_totals(
        self, purchase_order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate totals for a purchase order.

        Args:
            purchase_order_data: Purchase order data containing line items

        Returns:
            Dictionary with calculated totals:
            - subtotal: Sum of all line item amounts
            - tax_amount: Total tax amount
            - shipping_cost: Shipping cost
            - total_cost: Final order total
            - line_item_count: Number of line items

        Raises:
            ValueError: If required data is missing
        """
        # Note: This assumes PO line items are included in the order data
        # The actual structure may vary based on Autotask API implementation

        line_items = purchase_order_data.get("lineItems", [])
        if not isinstance(line_items, list):
            line_items = []

        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item in line_items:
            item_amount = Decimal(str(item.get("totalCost", 0)))
            item_tax = Decimal(str(item.get("taxAmount", 0)))

            subtotal += item_amount
            tax_amount += item_tax

        shipping_cost = Decimal(str(purchase_order_data.get("shippingCost", 0)))
        total_cost = subtotal + tax_amount + shipping_cost

        return {
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "shipping_cost": float(shipping_cost),
            "total_cost": float(total_cost),
            "line_item_count": len(line_items),
            "currency": purchase_order_data.get("currency", "USD"),
        }

    def approve_order(
        self,
        purchase_order_id: int,
        approved_by: int,
        approval_notes: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Approve a purchase order.

        Args:
            purchase_order_id: The purchase order ID to approve
            approved_by: Resource ID of the approver
            approval_notes: Optional approval notes

        Returns:
            UpdateResponse: Response containing updated purchase order data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {
            "status": "Approved",
            "approvedBy": approved_by,
            "approvalDate": datetime.now().isoformat(),
        }

        if approval_notes:
            update_data["approvalNotes"] = approval_notes

        return self.update(purchase_order_id, update_data)

    def reject_order(
        self,
        purchase_order_id: int,
        rejected_by: int,
        rejection_reason: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Reject a purchase order.

        Args:
            purchase_order_id: The purchase order ID to reject
            rejected_by: Resource ID of the rejector
            rejection_reason: Optional rejection reason

        Returns:
            UpdateResponse: Response containing updated purchase order data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {
            "status": "Rejected",
            "rejectedBy": rejected_by,
            "rejectionDate": datetime.now().isoformat(),
        }

        if rejection_reason:
            update_data["rejectionReason"] = rejection_reason

        return self.update(purchase_order_id, update_data)

    def mark_as_delivered(
        self,
        purchase_order_id: int,
        delivery_date: Optional[date] = None,
        received_by: Optional[int] = None,
    ) -> UpdateResponse:
        """
        Mark a purchase order as delivered.

        Args:
            purchase_order_id: The purchase order ID to mark as delivered
            delivery_date: Date of delivery (default: today)
            received_by: Resource ID of the person who received the order

        Returns:
            UpdateResponse: Response containing updated purchase order data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if delivery_date is None:
            delivery_date = date.today()

        update_data = {"status": "Delivered", "deliveryDate": delivery_date.isoformat()}

        if received_by:
            update_data["receivedBy"] = received_by

        return self.update(purchase_order_id, update_data)

    def cancel_order(
        self,
        purchase_order_id: int,
        cancelled_by: int,
        cancellation_reason: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Cancel a purchase order.

        Args:
            purchase_order_id: The purchase order ID to cancel
            cancelled_by: Resource ID of the person cancelling the order
            cancellation_reason: Optional cancellation reason

        Returns:
            UpdateResponse: Response containing updated purchase order data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {
            "status": "Cancelled",
            "cancelledBy": cancelled_by,
            "cancellationDate": datetime.now().isoformat(),
        }

        if cancellation_reason:
            update_data["cancellationReason"] = cancellation_reason

        return self.update(purchase_order_id, update_data)

    def get_vendor_spending_summary(
        self, vendor_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get spending summary for a specific vendor.

        Args:
            vendor_id: The vendor account ID
            date_range: Optional tuple of (start_date, end_date) to filter by

        Returns:
            Dictionary with vendor spending summary:
            - vendor_id: Vendor account ID
            - total_orders: Total number of orders
            - total_amount: Total amount spent
            - approved_orders: Number of approved orders
            - approved_amount: Total amount of approved orders
            - pending_orders: Number of pending orders
            - pending_amount: Total amount of pending orders
            - average_order_value: Average value per order

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get orders based on date range if provided
        if date_range:
            start_date, end_date = date_range
            orders = self.get_by_date_range(start_date, end_date, vendor_id)
        else:
            orders = self.get_by_vendor(vendor_id)

        summary = {
            "vendor_id": vendor_id,
            "date_range": date_range,
            "total_orders": len(orders),
            "total_amount": 0.0,
            "approved_orders": 0,
            "approved_amount": 0.0,
            "pending_orders": 0,
            "pending_amount": 0.0,
            "delivered_orders": 0,
            "delivered_amount": 0.0,
            "cancelled_orders": 0,
            "cancelled_amount": 0.0,
        }

        for order in orders:
            amount = float(order.get("totalCost", 0))
            status = order.get("status", "").lower()

            summary["total_amount"] += amount

            if status == "approved":
                summary["approved_orders"] += 1
                summary["approved_amount"] += amount
            elif status == "pending":
                summary["pending_orders"] += 1
                summary["pending_amount"] += amount
            elif status == "delivered":
                summary["delivered_orders"] += 1
                summary["delivered_amount"] += amount
            elif status == "cancelled":
                summary["cancelled_orders"] += 1
                summary["cancelled_amount"] += amount

        # Calculate average
        if summary["total_orders"] > 0:
            summary["average_order_value"] = (
                summary["total_amount"] / summary["total_orders"]
            )
        else:
            summary["average_order_value"] = 0.0

        return summary

    def get_procurement_summary(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get overall procurement summary.

        Args:
            date_range: Optional tuple of (start_date, end_date) to filter by

        Returns:
            Dictionary with procurement summary:
            - total_orders: Total number of orders
            - total_amount: Total procurement amount
            - orders_by_status: Breakdown by status
            - top_vendors: Top vendors by spending
            - average_order_value: Average value per order
            - overdue_orders: Number of overdue orders

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get orders based on date range if provided
        if date_range:
            start_date, end_date = date_range
            orders = self.get_by_date_range(start_date, end_date)
        else:
            orders = self.query()

        summary = {
            "date_range": date_range,
            "total_orders": len(orders),
            "total_amount": 0.0,
            "orders_by_status": {},
            "vendor_spending": {},
            "overdue_orders": 0,
        }

        # Get overdue orders
        overdue_orders = self.get_overdue_orders()
        summary["overdue_orders"] = len(overdue_orders)

        for order in orders:
            amount = float(order.get("totalCost", 0))
            status = order.get("status", "Unknown")
            vendor_id = order.get("vendorAccountID")

            summary["total_amount"] += amount

            # Count by status
            if status not in summary["orders_by_status"]:
                summary["orders_by_status"][status] = {"count": 0, "amount": 0.0}
            summary["orders_by_status"][status]["count"] += 1
            summary["orders_by_status"][status]["amount"] += amount

            # Count by vendor
            if vendor_id:
                if vendor_id not in summary["vendor_spending"]:
                    summary["vendor_spending"][vendor_id] = {"count": 0, "amount": 0.0}
                summary["vendor_spending"][vendor_id]["count"] += 1
                summary["vendor_spending"][vendor_id]["amount"] += amount

        # Calculate average
        if summary["total_orders"] > 0:
            summary["average_order_value"] = (
                summary["total_amount"] / summary["total_orders"]
            )
        else:
            summary["average_order_value"] = 0.0

        # Sort top vendors by spending
        top_vendors = sorted(
            summary["vendor_spending"].items(),
            key=lambda x: x[1]["amount"],
            reverse=True,
        )[
            :10
        ]  # Top 10 vendors

        summary["top_vendors"] = [
            {"vendor_id": vendor_id, **data} for vendor_id, data in top_vendors
        ]

        return summary

    def validate_purchase_order_data(
        self, purchase_order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate purchase order data.

        Args:
            purchase_order_data: Purchase order data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["vendorAccountID", "purchaseOrderDate", "requestedBy"]
        for field in required_fields:
            if field not in purchase_order_data or purchase_order_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate dates
        po_date = purchase_order_data.get("purchaseOrderDate")
        if po_date:
            try:
                if isinstance(po_date, str):
                    datetime.fromisoformat(po_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Purchase order date must be a valid date")

        expected_delivery_date = purchase_order_data.get("expectedDeliveryDate")
        if expected_delivery_date:
            try:
                if isinstance(expected_delivery_date, str):
                    delivery_date_obj = datetime.fromisoformat(
                        expected_delivery_date.replace("Z", "+00:00")
                    ).date()
                    if po_date:
                        po_date_obj = datetime.fromisoformat(
                            po_date.replace("Z", "+00:00")
                        ).date()
                        if delivery_date_obj < po_date_obj:
                            errors.append(
                                "Expected delivery date cannot be before purchase order date"
                            )
                        elif delivery_date_obj < date.today():
                            warnings.append("Expected delivery date is in the past")
            except ValueError:
                errors.append("Expected delivery date must be a valid date")

        # Validate amounts
        total_cost = purchase_order_data.get("totalCost")
        if total_cost is not None:
            try:
                cost_float = float(total_cost)
                if cost_float < 0:
                    errors.append("Total cost cannot be negative")
                elif cost_float == 0:
                    warnings.append("Total cost is zero")
            except (ValueError, TypeError):
                errors.append("Total cost must be a valid number")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
