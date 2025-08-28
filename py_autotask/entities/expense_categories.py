"""
Expense Categories entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class ExpenseCategoriesEntity(BaseEntity):
    """
    Handles all Expense Category-related operations for the Autotask API.

    Expense categories are used to classify and organize different types of
    expenses in the system, providing standardized categorization for expense
    reporting, tracking, and analysis.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_expense_category(
        self,
        category_name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        requires_receipt: bool = False,
        is_billable_by_default: bool = True,
        gl_account_number: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new expense category.

        Args:
            category_name: Name of the expense category
            description: Optional description of the category
            is_active: Whether the category is active
            requires_receipt: Whether receipts are required for this category
            is_billable_by_default: Default billability status for expenses in this category
            gl_account_number: General ledger account number
            **kwargs: Additional category fields

        Returns:
            Created expense category data
        """
        category_data = {
            "CategoryName": category_name,
            "IsActive": is_active,
            "RequiresReceipt": requires_receipt,
            "IsBillableByDefault": is_billable_by_default,
            **kwargs,
        }

        if description:
            category_data["Description"] = description
        if gl_account_number:
            category_data["GLAccountNumber"] = gl_account_number

        return self.create(category_data)

    def get_active_categories(self) -> List[EntityDict]:
        """
        Get all active expense categories.

        Returns:
            List of active expense categories
        """
        return self.query_all(
            filters={"field": "IsActive", "op": "eq", "value": "true"}
        )

    def get_billable_categories(self) -> List[EntityDict]:
        """
        Get expense categories that are billable by default.

        Returns:
            List of billable expense categories
        """
        return self.query_all(
            filters=[
                {"field": "IsActive", "op": "eq", "value": "true"},
                {"field": "IsBillableByDefault", "op": "eq", "value": "true"},
            ]
        )

    def get_receipt_required_categories(self) -> List[EntityDict]:
        """
        Get expense categories that require receipts.

        Returns:
            List of expense categories requiring receipts
        """
        return self.query_all(
            filters=[
                {"field": "IsActive", "op": "eq", "value": "true"},
                {"field": "RequiresReceipt", "op": "eq", "value": "true"},
            ]
        )

    def search_categories_by_name(self, search_term: str) -> List[EntityDict]:
        """
        Search expense categories by name.

        Args:
            search_term: Term to search for in category names

        Returns:
            List of matching expense categories
        """
        return self.query_all(
            filters={"field": "CategoryName", "op": "contains", "value": search_term}
        )

    def get_categories_by_gl_account(self, gl_account: str) -> List[EntityDict]:
        """
        Get expense categories by GL account number.

        Args:
            gl_account: General ledger account number

        Returns:
            List of expense categories for the GL account
        """
        return self.query_all(
            filters={"field": "GLAccountNumber", "op": "eq", "value": gl_account}
        )

    def deactivate_category(self, category_id: int) -> EntityDict:
        """
        Deactivate an expense category.

        Args:
            category_id: ID of the category to deactivate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": False})

    def update_category_settings(
        self,
        category_id: int,
        requires_receipt: Optional[bool] = None,
        is_billable_by_default: Optional[bool] = None,
        gl_account_number: Optional[str] = None,
    ) -> EntityDict:
        """
        Update expense category settings.

        Args:
            category_id: ID of the category to update
            requires_receipt: Whether receipts are required
            is_billable_by_default: Default billability status
            gl_account_number: General ledger account number

        Returns:
            Updated category data
        """
        update_data = {}

        if requires_receipt is not None:
            update_data["RequiresReceipt"] = requires_receipt
        if is_billable_by_default is not None:
            update_data["IsBillableByDefault"] = is_billable_by_default
        if gl_account_number is not None:
            update_data["GLAccountNumber"] = gl_account_number

        return self.update_by_id(category_id, update_data)

    def get_category_usage_summary(self) -> Dict[str, Any]:
        """
        Get summary of expense category usage and configuration.

        Returns:
            Dictionary containing category usage summary
        """
        all_categories = self.query_all()
        active_categories = [cat for cat in all_categories if cat.get("IsActive")]

        billable_count = sum(
            1 for cat in active_categories if cat.get("IsBillableByDefault")
        )

        receipt_required_count = sum(
            1 for cat in active_categories if cat.get("RequiresReceipt")
        )

        gl_mapped_count = sum(
            1 for cat in active_categories if cat.get("GLAccountNumber")
        )

        return {
            "total_categories": len(all_categories),
            "active_categories": len(active_categories),
            "inactive_categories": len(all_categories) - len(active_categories),
            "billable_by_default": billable_count,
            "require_receipts": receipt_required_count,
            "have_gl_mapping": gl_mapped_count,
            "summary_metrics": {
                "billable_percentage": (
                    (billable_count / len(active_categories) * 100)
                    if active_categories
                    else 0
                ),
                "receipt_required_percentage": (
                    (receipt_required_count / len(active_categories) * 100)
                    if active_categories
                    else 0
                ),
                "gl_mapped_percentage": (
                    (gl_mapped_count / len(active_categories) * 100)
                    if active_categories
                    else 0
                ),
            },
        }

    def get_categories_for_expense_reporting(
        self, include_gl_info: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get expense categories formatted for expense reporting.

        Args:
            include_gl_info: Whether to include GL account information

        Returns:
            List of categories with reporting-friendly format
        """
        active_categories = self.get_active_categories()

        formatted_categories = []
        for category in active_categories:
            formatted_cat = {
                "id": category["id"],
                "name": category.get("CategoryName", ""),
                "description": category.get("Description", ""),
                "requires_receipt": category.get("RequiresReceipt", False),
                "billable_by_default": category.get("IsBillableByDefault", True),
            }

            if include_gl_info:
                formatted_cat["gl_account"] = category.get("GLAccountNumber", "")

            formatted_categories.append(formatted_cat)

        # Sort by name for consistency
        formatted_categories.sort(key=lambda x: x["name"].lower())

        return formatted_categories
