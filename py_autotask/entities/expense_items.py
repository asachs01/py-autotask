"""
ExpenseItems entity for Autotask API operations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ExpenseItemsEntity(BaseEntity):
    """
    Handles all ExpenseItems-related operations for the Autotask API.

    ExpenseItems represent individual expense line items within expense reports,
    tracking detailed expense information including amounts, categories, and receipts.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_expense_item(
        self,
        expense_report_id: int,
        expense_category_id: int,
        amount: float,
        expense_date: date,
        description: str,
        billable: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new expense item.

        Args:
            expense_report_id: ID of the expense report
            expense_category_id: ID of the expense category
            amount: Expense amount
            expense_date: Date of the expense
            description: Description of the expense
            billable: Whether the expense is billable to client
            **kwargs: Additional expense item properties

        Returns:
            Created expense item data
        """
        item_data = {
            "ExpenseReportID": expense_report_id,
            "ExpenseCategoryID": expense_category_id,
            "Amount": amount,
            "ExpenseDate": expense_date.isoformat(),
            "Description": description,
            "Billable": billable,
            **kwargs,
        }

        return self.create(item_data)

    def get_items_by_expense_report(
        self, expense_report_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all expense items for a specific expense report.

        Args:
            expense_report_id: ID of the expense report
            limit: Maximum number of items to return

        Returns:
            List of expense items for the report
        """
        filters = [
            QueryFilter(field="ExpenseReportID", op="eq", value=expense_report_id)
        ]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_items_by_category(
        self, expense_category_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get expense items by category.

        Args:
            expense_category_id: ID of the expense category
            limit: Maximum number of items to return

        Returns:
            List of expense items in the category
        """
        filters = [
            QueryFilter(field="ExpenseCategoryID", op="eq", value=expense_category_id)
        ]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_billable_items(
        self, expense_report_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get billable expense items.

        Args:
            expense_report_id: Optional expense report ID to filter by
            limit: Maximum number of items to return

        Returns:
            List of billable expense items
        """
        filters = [QueryFilter(field="Billable", op="eq", value=True)]

        if expense_report_id:
            filters.append(
                QueryFilter(field="ExpenseReportID", op="eq", value=expense_report_id)
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_items_by_date_range(
        self,
        start_date: date,
        end_date: date,
        expense_report_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get expense items within a date range.

        Args:
            start_date: Start date of range
            end_date: End date of range
            expense_report_id: Optional expense report ID to filter by
            limit: Maximum number of items to return

        Returns:
            List of expense items within the date range
        """
        filters = [
            QueryFilter(field="ExpenseDate", op="gte", value=start_date.isoformat()),
            QueryFilter(field="ExpenseDate", op="lte", value=end_date.isoformat()),
        ]

        if expense_report_id:
            filters.append(
                QueryFilter(field="ExpenseReportID", op="eq", value=expense_report_id)
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def update_item_amount(
        self, item_id: int, new_amount: float, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Update the amount of an expense item.

        Args:
            item_id: ID of the expense item
            new_amount: New expense amount
            reason: Optional reason for the change

        Returns:
            Updated expense item data
        """
        update_data = {"Amount": new_amount}

        if reason:
            update_data["AmendmentReason"] = reason
            update_data["LastModifiedDate"] = datetime.now().isoformat()

        return self.update_by_id(item_id, update_data)

    def mark_item_billable(self, item_id: int, billable: bool = True) -> EntityDict:
        """
        Mark an expense item as billable or non-billable.

        Args:
            item_id: ID of the expense item
            billable: Whether the item should be billable

        Returns:
            Updated expense item data
        """
        return self.update_by_id(item_id, {"Billable": billable})

    def bulk_create_expense_items(
        self, items_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple expense items in batch.

        Args:
            items_data: List of expense item data dictionaries

        Returns:
            List of created expense item responses
        """
        return self.batch_create(items_data)

    def calculate_expense_report_totals(self, expense_report_id: int) -> Dict[str, Any]:
        """
        Calculate totals for an expense report.

        Args:
            expense_report_id: ID of the expense report

        Returns:
            Dictionary containing expense report totals
        """
        items = self.get_items_by_expense_report(expense_report_id)

        totals = {
            "total_items": len(items),
            "total_amount": 0.0,
            "billable_amount": 0.0,
            "non_billable_amount": 0.0,
            "category_breakdown": {},
            "currency_breakdown": {},
        }

        for item in items:
            amount = float(item.get("Amount", 0))
            category_id = item.get("ExpenseCategoryID")
            currency = item.get("Currency", "USD")
            is_billable = item.get("Billable", False)

            # Total amounts
            totals["total_amount"] += amount

            if is_billable:
                totals["billable_amount"] += amount
            else:
                totals["non_billable_amount"] += amount

            # Category breakdown
            if category_id not in totals["category_breakdown"]:
                totals["category_breakdown"][category_id] = {
                    "amount": 0.0,
                    "count": 0,
                    "billable_amount": 0.0,
                }

            totals["category_breakdown"][category_id]["amount"] += amount
            totals["category_breakdown"][category_id]["count"] += 1

            if is_billable:
                totals["category_breakdown"][category_id]["billable_amount"] += amount

            # Currency breakdown
            if currency not in totals["currency_breakdown"]:
                totals["currency_breakdown"][currency] = 0.0
            totals["currency_breakdown"][currency] += amount

        # Calculate percentages
        if totals["total_amount"] > 0:
            totals["billable_percentage"] = (
                totals["billable_amount"] / totals["total_amount"]
            ) * 100
        else:
            totals["billable_percentage"] = 0.0

        return totals

    def get_items_requiring_approval(
        self, amount_threshold: Optional[float] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get expense items that require approval.

        Args:
            amount_threshold: Optional amount threshold for approval
            limit: Maximum number of items to return

        Returns:
            List of expense items requiring approval
        """
        filters = []

        # Items with pending approval status
        filters.append(QueryFilter(field="ApprovalStatus", op="eq", value="Pending"))

        if amount_threshold:
            filters.append(
                QueryFilter(field="Amount", op="gte", value=amount_threshold)
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def approve_expense_item(
        self,
        item_id: int,
        approver_resource_id: int,
        approval_note: Optional[str] = None,
    ) -> EntityDict:
        """
        Approve an expense item.

        Args:
            item_id: ID of the expense item
            approver_resource_id: ID of the approver
            approval_note: Optional approval note

        Returns:
            Updated expense item data
        """
        update_data = {
            "ApprovalStatus": "Approved",
            "ApproverResourceID": approver_resource_id,
            "ApprovalDate": datetime.now().isoformat(),
        }

        if approval_note:
            update_data["ApprovalNote"] = approval_note

        return self.update_by_id(item_id, update_data)

    def reject_expense_item(
        self, item_id: int, rejector_resource_id: int, rejection_reason: str
    ) -> EntityDict:
        """
        Reject an expense item.

        Args:
            item_id: ID of the expense item
            rejector_resource_id: ID of the rejector
            rejection_reason: Reason for rejection

        Returns:
            Updated expense item data
        """
        update_data = {
            "ApprovalStatus": "Rejected",
            "ApproverResourceID": rejector_resource_id,
            "ApprovalDate": datetime.now().isoformat(),
            "RejectionReason": rejection_reason,
        }

        return self.update_by_id(item_id, update_data)

    def get_expense_analytics_by_category(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """
        Get expense analytics grouped by category for a date range.

        Args:
            start_date: Start date of analysis period
            end_date: End date of analysis period

        Returns:
            Dictionary containing expense analytics by category
        """
        items = self.get_items_by_date_range(start_date, end_date)

        analytics = {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_items": len(items),
            "total_amount": 0.0,
            "categories": {},
            "top_categories": [],
            "billable_summary": {
                "billable_items": 0,
                "non_billable_items": 0,
                "billable_amount": 0.0,
                "non_billable_amount": 0.0,
            },
        }

        # Process items
        for item in items:
            amount = float(item.get("Amount", 0))
            category_id = item.get("ExpenseCategoryID", "Unknown")
            is_billable = item.get("Billable", False)

            analytics["total_amount"] += amount

            # Category analytics
            if category_id not in analytics["categories"]:
                analytics["categories"][category_id] = {
                    "total_amount": 0.0,
                    "item_count": 0,
                    "avg_amount": 0.0,
                    "billable_count": 0,
                    "billable_amount": 0.0,
                }

            cat_data = analytics["categories"][category_id]
            cat_data["total_amount"] += amount
            cat_data["item_count"] += 1

            if is_billable:
                cat_data["billable_count"] += 1
                cat_data["billable_amount"] += amount
                analytics["billable_summary"]["billable_items"] += 1
                analytics["billable_summary"]["billable_amount"] += amount
            else:
                analytics["billable_summary"]["non_billable_items"] += 1
                analytics["billable_summary"]["non_billable_amount"] += amount

        # Calculate averages
        for category_id, cat_data in analytics["categories"].items():
            cat_data["avg_amount"] = cat_data["total_amount"] / max(
                1, cat_data["item_count"]
            )

        # Top categories by amount
        analytics["top_categories"] = sorted(
            analytics["categories"].items(),
            key=lambda x: x[1]["total_amount"],
            reverse=True,
        )[:5]

        return analytics

    def validate_expense_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate expense item data before creation/update.

        Args:
            item_data: Expense item data to validate

        Returns:
            Dictionary containing validation results
        """
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Required fields
        required_fields = [
            "ExpenseReportID",
            "ExpenseCategoryID",
            "Amount",
            "ExpenseDate",
            "Description",
        ]
        for field in required_fields:
            if field not in item_data or item_data[field] is None:
                validation_results["errors"].append(f"Missing required field: {field}")
                validation_results["is_valid"] = False

        # Amount validation
        amount = item_data.get("Amount", 0)
        if amount <= 0:
            validation_results["errors"].append("Amount must be greater than zero")
            validation_results["is_valid"] = False
        elif amount > 10000:  # Example business rule
            validation_results["warnings"].append(
                "Large expense amount - may require additional approval"
            )

        # Date validation
        expense_date = item_data.get("ExpenseDate")
        if expense_date:
            try:
                parsed_date = datetime.fromisoformat(expense_date).date()
                if parsed_date > date.today():
                    validation_results["errors"].append(
                        "Expense date cannot be in the future"
                    )
                    validation_results["is_valid"] = False
                elif parsed_date < (date.today() - datetime.timedelta(days=90)):
                    validation_results["warnings"].append(
                        "Expense date is more than 90 days old"
                    )
            except ValueError:
                validation_results["errors"].append("Invalid expense date format")
                validation_results["is_valid"] = False

        # Description validation
        description = item_data.get("Description", "")
        if len(description.strip()) < 5:
            validation_results["warnings"].append(
                "Description should be more descriptive"
            )

        return validation_results
