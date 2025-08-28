"""
Invoices entity for Autotask API.

This module provides the InvoicesEntity class for managing
invoices within the Autotask system.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class InvoicesEntity(BaseEntity):
    """
    Entity for managing Autotask Invoices.

    Invoices represent billing documents generated from contracts,
    time entries, expenses, and other billable items.
    """

    def __init__(self, client, entity_name="Invoices"):
        """Initialize the Invoices entity."""
        super().__init__(client, entity_name)

    def create(self, invoice_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new invoice.

        Args:
            invoice_data: Dictionary containing invoice information
                Required fields:
                - accountID: ID of the account being invoiced
                - invoiceDate: Date of the invoice
                - paymentTerms: Payment terms
                Optional fields:
                - invoiceNumber: Invoice number (auto-generated if not provided)
                - description: Invoice description
                - dueDate: Due date for payment
                - purchaseOrderNumber: Purchase order number
                - taxRegionID: Tax region ID
                - currencyID: Currency ID
                - webServiceDate: Web service date
                - comments: Additional comments

        Returns:
            CreateResponse: Response containing created invoice data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["accountID", "invoiceDate", "paymentTerms"]
        self._validate_required_fields(invoice_data, required_fields)

        return self._create(invoice_data)

    def get(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an invoice by ID.

        Args:
            invoice_id: The invoice ID

        Returns:
            Dictionary containing invoice data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(invoice_id)

    def update(self, invoice_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing invoice.

        Args:
            invoice_id: The invoice ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated invoice data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(invoice_id, update_data)

    def delete(self, invoice_id: int) -> bool:
        """
        Delete an invoice.

        Args:
            invoice_id: The invoice ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(invoice_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query invoices with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing invoice data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_account(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get all invoices for a specific account.

        Args:
            account_id: The account ID

        Returns:
            List of invoices for the specified account

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="accountID", op="eq", value=account_id)]
        return self.query(filters)

    def get_by_date_range(
        self, start_date: date, end_date: date, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get invoices within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            account_id: Optional account ID to filter by

        Returns:
            List of invoices within the date range

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="invoiceDate", op="gte", value=start_date.isoformat()),
            QueryFilter(field="invoiceDate", op="lte", value=end_date.isoformat()),
        ]

        if account_id:
            filters.append(QueryFilter(field="accountID", op="eq", value=account_id))

        return self.query(filters)

    def get_by_status(
        self, status: str, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get invoices by status.

        Args:
            status: Invoice status to filter by
            account_id: Optional account ID to filter by

        Returns:
            List of invoices with the specified status

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="eq", value=status)]

        if account_id:
            filters.append(QueryFilter(field="accountID", op="eq", value=account_id))

        return self.query(filters)

    def get_overdue_invoices(
        self, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get overdue invoices.

        Args:
            as_of_date: Date to check overdue status against (default: today)

        Returns:
            List of overdue invoices

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if as_of_date is None:
            as_of_date = date.today()

        filters = [
            QueryFilter(field="dueDate", op="lt", value=as_of_date.isoformat()),
            QueryFilter(field="status", op="ne", value="Paid"),
        ]

        return self.query(filters)

    def get_unpaid_invoices(
        self, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get unpaid invoices.

        Args:
            account_id: Optional account ID to filter by

        Returns:
            List of unpaid invoices

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="ne", value="Paid")]

        if account_id:
            filters.append(QueryFilter(field="accountID", op="eq", value=account_id))

        return self.query(filters)

    def calculate_invoice_totals(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate totals for an invoice.

        Args:
            invoice_data: Invoice data containing line items

        Returns:
            Dictionary with calculated totals:
            - subtotal: Sum of all line item amounts
            - tax_amount: Total tax amount
            - total_amount: Final invoice total
            - line_item_count: Number of line items

        Raises:
            ValueError: If required data is missing
        """
        # Note: This assumes invoice line items are included in the invoice data
        # The actual structure may vary based on Autotask API implementation

        line_items = invoice_data.get("lineItems", [])
        if not isinstance(line_items, list):
            line_items = []

        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item in line_items:
            item_amount = Decimal(str(item.get("amount", 0)))
            item_tax = Decimal(str(item.get("taxAmount", 0)))

            subtotal += item_amount
            tax_amount += item_tax

        total_amount = subtotal + tax_amount

        return {
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),
            "line_item_count": len(line_items),
            "currency": invoice_data.get("currency", "USD"),
        }

    def mark_as_paid(
        self,
        invoice_id: int,
        payment_date: Optional[date] = None,
        payment_method: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Mark an invoice as paid.

        Args:
            invoice_id: The invoice ID to mark as paid
            payment_date: Date of payment (default: today)
            payment_method: Method of payment

        Returns:
            UpdateResponse: Response containing updated invoice data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if payment_date is None:
            payment_date = date.today()

        update_data = {"status": "Paid", "paymentDate": payment_date.isoformat()}

        if payment_method:
            update_data["paymentMethod"] = payment_method

        return self.update(invoice_id, update_data)

    def void_invoice(
        self, invoice_id: int, void_reason: Optional[str] = None
    ) -> UpdateResponse:
        """
        Void an invoice.

        Args:
            invoice_id: The invoice ID to void
            void_reason: Reason for voiding the invoice

        Returns:
            UpdateResponse: Response containing updated invoice data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {"status": "Void", "voidDate": date.today().isoformat()}

        if void_reason:
            update_data["voidReason"] = void_reason

        return self.update(invoice_id, update_data)

    def get_invoice_aging_report(
        self, account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate an aging report for invoices.

        Args:
            account_id: Optional account ID to filter by

        Returns:
            Dictionary with aging report data:
            - current: Invoices not yet due
            - days_30: Invoices 1-30 days overdue
            - days_60: Invoices 31-60 days overdue
            - days_90: Invoices 61-90 days overdue
            - days_90_plus: Invoices over 90 days overdue
            - totals: Summary totals for each category

        Raises:
            AutotaskAPIError: If the API request fails
        """
        today = date.today()

        # Get all unpaid invoices
        unpaid_invoices = self.get_unpaid_invoices(account_id)

        aging_buckets = {
            "current": [],
            "days_30": [],
            "days_60": [],
            "days_90": [],
            "days_90_plus": [],
        }

        totals = {
            "current": 0.0,
            "days_30": 0.0,
            "days_60": 0.0,
            "days_90": 0.0,
            "days_90_plus": 0.0,
        }

        for invoice in unpaid_invoices:
            due_date_str = invoice.get("dueDate")
            if not due_date_str:
                continue

            due_date = datetime.fromisoformat(
                due_date_str.replace("Z", "+00:00")
            ).date()
            days_overdue = (today - due_date).days

            invoice_amount = float(invoice.get("totalAmount", 0))

            if days_overdue <= 0:
                aging_buckets["current"].append(invoice)
                totals["current"] += invoice_amount
            elif days_overdue <= 30:
                aging_buckets["days_30"].append(invoice)
                totals["days_30"] += invoice_amount
            elif days_overdue <= 60:
                aging_buckets["days_60"].append(invoice)
                totals["days_60"] += invoice_amount
            elif days_overdue <= 90:
                aging_buckets["days_90"].append(invoice)
                totals["days_90"] += invoice_amount
            else:
                aging_buckets["days_90_plus"].append(invoice)
                totals["days_90_plus"] += invoice_amount

        return {
            "account_id": account_id,
            "report_date": today.isoformat(),
            "aging_buckets": aging_buckets,
            "totals": totals,
            "grand_total": sum(totals.values()),
            "invoice_count": len(unpaid_invoices),
        }

    def get_invoice_summary(
        self, account_id: Optional[int] = None, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of invoices.

        Args:
            account_id: Optional account ID to filter by
            date_range: Optional tuple of (start_date, end_date) to filter by

        Returns:
            Dictionary with invoice summary:
            - total_invoices: Total number of invoices
            - total_amount: Total invoice amount
            - paid_invoices: Number of paid invoices
            - paid_amount: Total amount of paid invoices
            - unpaid_invoices: Number of unpaid invoices
            - unpaid_amount: Total amount of unpaid invoices
            - overdue_invoices: Number of overdue invoices
            - overdue_amount: Total amount of overdue invoices

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get invoices based on filters
        if date_range:
            start_date, end_date = date_range
            invoices = self.get_by_date_range(start_date, end_date, account_id)
        elif account_id:
            invoices = self.get_by_account(account_id)
        else:
            invoices = self.query()

        # Get overdue invoices
        overdue_invoices = self.get_overdue_invoices()
        if account_id:
            overdue_invoices = [
                inv for inv in overdue_invoices if inv.get("accountID") == account_id
            ]

        summary = {
            "account_id": account_id,
            "date_range": date_range,
            "total_invoices": len(invoices),
            "total_amount": 0.0,
            "paid_invoices": 0,
            "paid_amount": 0.0,
            "unpaid_invoices": 0,
            "unpaid_amount": 0.0,
            "overdue_invoices": len(overdue_invoices),
            "overdue_amount": 0.0,
        }

        for invoice in invoices:
            amount = float(invoice.get("totalAmount", 0))
            status = invoice.get("status", "").lower()

            summary["total_amount"] += amount

            if status == "paid":
                summary["paid_invoices"] += 1
                summary["paid_amount"] += amount
            else:
                summary["unpaid_invoices"] += 1
                summary["unpaid_amount"] += amount

        # Calculate overdue amount
        for invoice in overdue_invoices:
            summary["overdue_amount"] += float(invoice.get("totalAmount", 0))

        return summary

    def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice data.

        Args:
            invoice_data: Invoice data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["accountID", "invoiceDate", "paymentTerms"]
        for field in required_fields:
            if field not in invoice_data or invoice_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate dates
        invoice_date = invoice_data.get("invoiceDate")
        if invoice_date:
            try:
                if isinstance(invoice_date, str):
                    datetime.fromisoformat(invoice_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Invoice date must be a valid date")

        due_date = invoice_data.get("dueDate")
        if due_date:
            try:
                if isinstance(due_date, str):
                    due_date_obj = datetime.fromisoformat(
                        due_date.replace("Z", "+00:00")
                    ).date()
                    if invoice_date:
                        invoice_date_obj = datetime.fromisoformat(
                            invoice_date.replace("Z", "+00:00")
                        ).date()
                        if due_date_obj < invoice_date_obj:
                            warnings.append("Due date is before invoice date")
            except ValueError:
                errors.append("Due date must be a valid date")

        # Validate amounts
        total_amount = invoice_data.get("totalAmount")
        if total_amount is not None:
            try:
                amount_float = float(total_amount)
                if amount_float < 0:
                    warnings.append("Invoice amount is negative")
            except (ValueError, TypeError):
                errors.append("Total amount must be a valid number")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
