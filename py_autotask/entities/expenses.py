"""
Expenses entity for Autotask API.

This module provides the ExpensesEntity class for managing
expense tracking and reimbursement within the Autotask system.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ExpensesEntity(BaseEntity):
    """
    Entity for managing Autotask Expenses.

    Expenses represent billable and non-billable expense entries
    for tracking costs, receipts, and reimbursements.
    """

    def __init__(self, client, entity_name="Expenses"):
        """Initialize the Expenses entity."""
        super().__init__(client, entity_name)

    def create(self, expense_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new expense entry.

        Args:
            expense_data: Dictionary containing expense information
                Required fields:
                - accountID: ID of the account/company
                - projectID: ID of the project (if project-related)
                - ticketID: ID of the ticket (if ticket-related)
                - expenseDate: Date of the expense
                - expenseAmount: Amount of the expense
                - expenseCategory: Category of expense
                - description: Description of the expense
                Optional fields:
                - expenseReportID: ID of expense report
                - haveReceipt: Whether receipt is available
                - reimbursable: Whether expense is reimbursable
                - billable: Whether expense is billable
                - paidByCompany: Whether paid by company
                - receiptAmount: Amount on receipt
                - currencyID: Currency ID
                - exchangeRate: Exchange rate if foreign currency
                - taxRate: Tax rate applied

        Returns:
            CreateResponse: Response containing created expense data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = [
            "accountID",
            "expenseDate",
            "expenseAmount",
            "expenseCategory",
            "description",
        ]
        self._validate_required_fields(expense_data, required_fields)

        # Validate amount is positive
        amount = expense_data.get("expenseAmount", 0)
        if float(amount) <= 0:
            raise ValueError("Expense amount must be positive")

        return self._create(expense_data)

    def get(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an expense by ID.

        Args:
            expense_id: The expense ID

        Returns:
            Dictionary containing expense data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(expense_id)

    def update(self, expense_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing expense.

        Args:
            expense_id: The expense ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated expense data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(expense_id, update_data)

    def delete(self, expense_id: int) -> bool:
        """
        Delete an expense.

        Args:
            expense_id: The expense ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(expense_id)

    def get_by_project(
        self,
        project_id: int,
        date_range: Optional[tuple] = None,
        include_non_billable: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all expenses for a specific project.

        Args:
            project_id: ID of the project
            date_range: Optional tuple of (start_date, end_date)
            include_non_billable: Whether to include non-billable expenses
            limit: Maximum number of expenses to return

        Returns:
            List of project expenses
        """
        filters = [QueryFilter(field="projectID", op="eq", value=project_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="expenseDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="expenseDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if not include_non_billable:
            filters.append(QueryFilter(field="billable", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_by_ticket(
        self,
        ticket_id: int,
        date_range: Optional[tuple] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all expenses for a specific ticket.

        Args:
            ticket_id: ID of the ticket
            date_range: Optional tuple of (start_date, end_date)
            limit: Maximum number of expenses to return

        Returns:
            List of ticket expenses
        """
        filters = [QueryFilter(field="ticketID", op="eq", value=ticket_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="expenseDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="expenseDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        return self.query(filters=filters, max_records=limit)

    def get_by_resource(
        self,
        resource_id: int,
        date_range: Optional[tuple] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all expenses for a specific resource.

        Args:
            resource_id: ID of the resource
            date_range: Optional tuple of (start_date, end_date)
            status_filter: Filter by status ('pending', 'approved', 'reimbursed')
            limit: Maximum number of expenses to return

        Returns:
            List of resource expenses
        """
        filters = [QueryFilter(field="resourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="expenseDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="expenseDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if status_filter:
            status_map = {"pending": 1, "approved": 2, "reimbursed": 3, "rejected": 4}
            if status_filter.lower() in status_map:
                filters.append(
                    QueryFilter(
                        field="status", op="eq", value=status_map[status_filter.lower()]
                    )
                )

        return self.query(filters=filters, max_records=limit)

    def get_pending_reimbursements(
        self, resource_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get expenses pending reimbursement.

        Args:
            resource_id: Optional filter by specific resource
            limit: Maximum number of expenses to return

        Returns:
            List of expenses pending reimbursement
        """
        filters = [
            QueryFilter(field="reimbursable", op="eq", value=True),
            QueryFilter(
                field="status", op="eq", value=2
            ),  # Approved but not reimbursed
        ]

        if resource_id:
            filters.append(QueryFilter(field="resourceID", op="eq", value=resource_id))

        return self.query(filters=filters, max_records=limit)

    def approve_expense(
        self, expense_id: int, approval_note: Optional[str] = None
    ) -> UpdateResponse:
        """
        Approve an expense for reimbursement.

        Args:
            expense_id: ID of expense to approve
            approval_note: Optional approval note

        Returns:
            Updated expense data
        """
        update_data = {
            "status": 2,  # Approved
            "approvalDate": datetime.now().isoformat(),
        }

        if approval_note:
            update_data["approvalNotes"] = approval_note

        return self.update(expense_id, update_data)

    def reject_expense(self, expense_id: int, rejection_reason: str) -> UpdateResponse:
        """
        Reject an expense.

        Args:
            expense_id: ID of expense to reject
            rejection_reason: Reason for rejection

        Returns:
            Updated expense data
        """
        update_data = {
            "status": 4,  # Rejected
            "rejectionReason": rejection_reason,
            "rejectionDate": datetime.now().isoformat(),
        }

        return self.update(expense_id, update_data)

    def mark_reimbursed(
        self,
        expense_id: int,
        reimbursement_amount: Optional[float] = None,
        reimbursement_date: Optional[Union[datetime, str]] = None,
    ) -> UpdateResponse:
        """
        Mark an expense as reimbursed.

        Args:
            expense_id: ID of expense to mark as reimbursed
            reimbursement_amount: Actual reimbursement amount
            reimbursement_date: Date of reimbursement

        Returns:
            Updated expense data
        """
        update_data = {
            "status": 3,  # Reimbursed
            "reimbursementDate": reimbursement_date or datetime.now().isoformat(),
        }

        if reimbursement_amount is not None:
            update_data["reimbursementAmount"] = reimbursement_amount

        return self.update(expense_id, update_data)

    def bulk_approve_expenses(
        self, expense_ids: List[int], approval_note: Optional[str] = None
    ) -> List[UpdateResponse]:
        """
        Approve multiple expenses in bulk.

        Args:
            expense_ids: List of expense IDs to approve
            approval_note: Optional approval note for all expenses

        Returns:
            List of update responses
        """
        results = []

        for expense_id in expense_ids:
            try:
                result = self.approve_expense(expense_id, approval_note)
                results.append(result)
            except Exception as e:
                # Log error but continue with other expenses
                self.client.logger.error(f"Failed to approve expense {expense_id}: {e}")
                results.append({"error": str(e), "expense_id": expense_id})

        return results

    def calculate_expense_totals(
        self, expense_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate totals for a list of expenses.

        Args:
            expense_list: List of expense data

        Returns:
            Dictionary with calculated totals:
            - total_amount: Sum of all expense amounts
            - billable_amount: Sum of billable expenses
            - reimbursable_amount: Sum of reimbursable expenses
            - tax_amount: Total tax amount
            - count: Number of expenses
            - by_category: Breakdown by expense category
        """
        totals = {
            "total_amount": Decimal("0.00"),
            "billable_amount": Decimal("0.00"),
            "reimbursable_amount": Decimal("0.00"),
            "tax_amount": Decimal("0.00"),
            "count": len(expense_list),
            "by_category": {},
            "currency": "USD",
        }

        for expense in expense_list:
            amount = Decimal(str(expense.get("expenseAmount", 0)))
            tax = Decimal(str(expense.get("taxAmount", 0)))
            category = expense.get("expenseCategory", "Other")

            totals["total_amount"] += amount
            totals["tax_amount"] += tax

            if expense.get("billable", False):
                totals["billable_amount"] += amount

            if expense.get("reimbursable", False):
                totals["reimbursable_amount"] += amount

            # Category breakdown
            if category not in totals["by_category"]:
                totals["by_category"][category] = {
                    "count": 0,
                    "amount": Decimal("0.00"),
                }

            totals["by_category"][category]["count"] += 1
            totals["by_category"][category]["amount"] += amount

        # Convert Decimal to float for JSON serialization
        totals["total_amount"] = float(totals["total_amount"])
        totals["billable_amount"] = float(totals["billable_amount"])
        totals["reimbursable_amount"] = float(totals["reimbursable_amount"])
        totals["tax_amount"] = float(totals["tax_amount"])

        for category in totals["by_category"]:
            totals["by_category"][category]["amount"] = float(
                totals["by_category"][category]["amount"]
            )

        return totals

    def get_expense_report_summary(
        self,
        resource_id: Optional[int] = None,
        date_range: Optional[tuple] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate expense report summary.

        Args:
            resource_id: Optional filter by resource
            date_range: Optional date range filter
            status_filter: Optional status filter

        Returns:
            Dictionary with expense report summary
        """
        filters = []

        if resource_id:
            filters.append(QueryFilter(field="resourceID", op="eq", value=resource_id))

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="expenseDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="expenseDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if status_filter:
            status_map = {"pending": 1, "approved": 2, "reimbursed": 3, "rejected": 4}
            if status_filter.lower() in status_map:
                filters.append(
                    QueryFilter(
                        field="status", op="eq", value=status_map[status_filter.lower()]
                    )
                )

        expenses = self.query(filters=filters)
        totals = self.calculate_expense_totals(expenses)

        # Add status breakdown
        status_breakdown = {
            "pending": {"count": 0, "amount": 0.0},
            "approved": {"count": 0, "amount": 0.0},
            "reimbursed": {"count": 0, "amount": 0.0},
            "rejected": {"count": 0, "amount": 0.0},
        }

        status_map = {1: "pending", 2: "approved", 3: "reimbursed", 4: "rejected"}

        for expense in expenses:
            status_id = expense.get("status", 1)
            status_name = status_map.get(status_id, "pending")
            amount = float(expense.get("expenseAmount", 0))

            status_breakdown[status_name]["count"] += 1
            status_breakdown[status_name]["amount"] += amount

        return {
            **totals,
            "status_breakdown": status_breakdown,
            "date_range": {
                "start": (
                    date_range[0].isoformat()
                    if date_range and hasattr(date_range[0], "isoformat")
                    else date_range[0] if date_range else None
                ),
                "end": (
                    date_range[1].isoformat()
                    if date_range and hasattr(date_range[1], "isoformat")
                    else date_range[1] if date_range else None
                ),
            },
        }

    def validate_expense_data(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate expense data.

        Args:
            expense_data: Expense data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = [
            "accountID",
            "expenseDate",
            "expenseAmount",
            "expenseCategory",
            "description",
        ]
        for field in required_fields:
            if field not in expense_data or expense_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate amount
        amount = expense_data.get("expenseAmount")
        if amount is not None:
            try:
                amount_val = float(amount)
                if amount_val <= 0:
                    errors.append("Expense amount must be positive")
                elif amount_val > 10000:
                    warnings.append("Expense amount is unusually high")
            except (ValueError, TypeError):
                errors.append("Expense amount must be a valid number")

        # Validate dates
        expense_date = expense_data.get("expenseDate")
        if expense_date:
            try:
                if isinstance(expense_date, str):
                    datetime.fromisoformat(expense_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Expense date must be a valid date")

        # Validate receipt amount consistency
        have_receipt = expense_data.get("haveReceipt", False)
        receipt_amount = expense_data.get("receiptAmount")
        expense_amount = expense_data.get("expenseAmount")

        if have_receipt and receipt_amount and expense_amount:
            try:
                receipt_val = float(receipt_amount)
                expense_val = float(expense_amount)
                if abs(receipt_val - expense_val) > 0.01:
                    warnings.append("Receipt amount differs from expense amount")
            except (ValueError, TypeError):
                pass  # Amount validation will catch this

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
