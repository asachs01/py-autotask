"""
Quotes entity for Autotask API.

This module provides the QuotesEntity class for managing
quotes and estimates within the Autotask system.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class QuotesEntity(BaseEntity):
    """
    Entity for managing Autotask Quotes.

    Quotes represent estimates and proposals provided to clients
    for potential work, services, or products.
    """

    def __init__(self, client, entity_name="Quotes"):
        """Initialize the Quotes entity."""
        super().__init__(client, entity_name)

    def create(self, quote_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new quote.

        Args:
            quote_data: Dictionary containing quote information
                Required fields:
                - opportunityID: ID of the associated opportunity
                - name: Quote name/title
                - quoteDate: Date of the quote
                Optional fields:
                - description: Quote description
                - expirationDate: Quote expiration date
                - contactID: Primary contact for the quote
                - soldToAccountID: Account being quoted
                - billToAccountID: Billing account
                - shipToAccountID: Shipping account
                - taxRegionID: Tax region ID
                - currencyID: Currency ID
                - comments: Additional comments

        Returns:
            CreateResponse: Response containing created quote data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["opportunityID", "name", "quoteDate"]
        self._validate_required_fields(quote_data, required_fields)

        return self._create(quote_data)

    def get(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a quote by ID.

        Args:
            quote_id: The quote ID

        Returns:
            Dictionary containing quote data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(quote_id)

    def update(self, quote_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing quote.

        Args:
            quote_id: The quote ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated quote data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(quote_id, update_data)

    def delete(self, quote_id: int) -> bool:
        """
        Delete a quote.

        Args:
            quote_id: The quote ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(quote_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query quotes with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing quote data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_opportunity(self, opportunity_id: int) -> List[Dict[str, Any]]:
        """
        Get all quotes for a specific opportunity.

        Args:
            opportunity_id: The opportunity ID

        Returns:
            List of quotes for the specified opportunity

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="opportunityID", op="eq", value=opportunity_id)]
        return self.query(filters)

    def get_by_account(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get all quotes for a specific account.

        Args:
            account_id: The account ID

        Returns:
            List of quotes for the specified account

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="soldToAccountID", op="eq", value=account_id)]
        return self.query(filters)

    def get_by_status(
        self, status: str, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get quotes by status.

        Args:
            status: Quote status to filter by
            account_id: Optional account ID to filter by

        Returns:
            List of quotes with the specified status

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="status", op="eq", value=status)]

        if account_id:
            filters.append(
                QueryFilter(field="soldToAccountID", op="eq", value=account_id)
            )

        return self.query(filters)

    def get_by_date_range(
        self, start_date: date, end_date: date, account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get quotes within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            account_id: Optional account ID to filter by

        Returns:
            List of quotes within the date range

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [
            QueryFilter(field="quoteDate", op="gte", value=start_date.isoformat()),
            QueryFilter(field="quoteDate", op="lte", value=end_date.isoformat()),
        ]

        if account_id:
            filters.append(
                QueryFilter(field="soldToAccountID", op="eq", value=account_id)
            )

        return self.query(filters)

    def get_expired_quotes(
        self, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get expired quotes.

        Args:
            as_of_date: Date to check expiration against (default: today)

        Returns:
            List of expired quotes

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if as_of_date is None:
            as_of_date = date.today()

        filters = [
            QueryFilter(field="expirationDate", op="lt", value=as_of_date.isoformat()),
            QueryFilter(field="status", op="ne", value="Accepted"),
            QueryFilter(field="status", op="ne", value="Rejected"),
        ]

        return self.query(filters)

    def get_expiring_soon(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get quotes expiring within a specified number of days.

        Args:
            days_ahead: Number of days ahead to check (default: 7)

        Returns:
            List of quotes expiring soon

        Raises:
            AutotaskAPIError: If the API request fails
        """
        today = date.today()
        future_date = date.fromordinal(today.toordinal() + days_ahead)

        filters = [
            QueryFilter(field="expirationDate", op="gte", value=today.isoformat()),
            QueryFilter(
                field="expirationDate", op="lte", value=future_date.isoformat()
            ),
            QueryFilter(field="status", op="eq", value="Pending"),
        ]

        return self.query(filters)

    def calculate_quote_totals(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate totals for a quote.

        Args:
            quote_data: Quote data containing line items

        Returns:
            Dictionary with calculated totals:
            - subtotal: Sum of all line item amounts
            - tax_amount: Total tax amount
            - total_amount: Final quote total
            - line_item_count: Number of line items
            - discount_amount: Total discount amount

        Raises:
            ValueError: If required data is missing
        """
        # Note: This assumes quote line items are included in the quote data
        # The actual structure may vary based on Autotask API implementation

        line_items = quote_data.get("lineItems", [])
        if not isinstance(line_items, list):
            line_items = []

        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        discount_amount = Decimal("0.00")

        for item in line_items:
            item_amount = Decimal(str(item.get("amount", 0)))
            item_tax = Decimal(str(item.get("taxAmount", 0)))
            item_discount = Decimal(str(item.get("discountAmount", 0)))

            subtotal += item_amount
            tax_amount += item_tax
            discount_amount += item_discount

        total_amount = subtotal + tax_amount - discount_amount

        return {
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "discount_amount": float(discount_amount),
            "total_amount": float(total_amount),
            "line_item_count": len(line_items),
            "currency": quote_data.get("currency", "USD"),
        }

    def accept_quote(
        self,
        quote_id: int,
        accepted_by: Optional[str] = None,
        acceptance_date: Optional[date] = None,
    ) -> UpdateResponse:
        """
        Accept a quote.

        Args:
            quote_id: The quote ID to accept
            accepted_by: Name/ID of person accepting the quote
            acceptance_date: Date of acceptance (default: today)

        Returns:
            UpdateResponse: Response containing updated quote data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if acceptance_date is None:
            acceptance_date = date.today()

        update_data = {
            "status": "Accepted",
            "acceptanceDate": acceptance_date.isoformat(),
        }

        if accepted_by:
            update_data["acceptedBy"] = accepted_by

        return self.update(quote_id, update_data)

    def reject_quote(
        self,
        quote_id: int,
        rejected_by: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        rejection_date: Optional[date] = None,
    ) -> UpdateResponse:
        """
        Reject a quote.

        Args:
            quote_id: The quote ID to reject
            rejected_by: Name/ID of person rejecting the quote
            rejection_reason: Reason for rejection
            rejection_date: Date of rejection (default: today)

        Returns:
            UpdateResponse: Response containing updated quote data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        if rejection_date is None:
            rejection_date = date.today()

        update_data = {
            "status": "Rejected",
            "rejectionDate": rejection_date.isoformat(),
        }

        if rejected_by:
            update_data["rejectedBy"] = rejected_by

        if rejection_reason:
            update_data["rejectionReason"] = rejection_reason

        return self.update(quote_id, update_data)

    def extend_expiration(
        self, quote_id: int, new_expiration_date: date
    ) -> UpdateResponse:
        """
        Extend the expiration date of a quote.

        Args:
            quote_id: The quote ID to extend
            new_expiration_date: New expiration date

        Returns:
            UpdateResponse: Response containing updated quote data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        update_data = {"expirationDate": new_expiration_date.isoformat()}

        return self.update(quote_id, update_data)

    def get_quote_conversion_rate(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Calculate quote conversion rate (accepted quotes vs total quotes).

        Args:
            date_range: Optional tuple of (start_date, end_date) to filter by

        Returns:
            Dictionary with conversion rate data:
            - total_quotes: Total number of quotes
            - accepted_quotes: Number of accepted quotes
            - rejected_quotes: Number of rejected quotes
            - pending_quotes: Number of pending quotes
            - conversion_rate: Percentage of quotes accepted
            - rejection_rate: Percentage of quotes rejected

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get quotes based on date range if provided
        if date_range:
            start_date, end_date = date_range
            quotes = self.get_by_date_range(start_date, end_date)
        else:
            quotes = self.query()

        stats = {
            "total_quotes": len(quotes),
            "accepted_quotes": 0,
            "rejected_quotes": 0,
            "pending_quotes": 0,
            "expired_quotes": 0,
        }

        for quote in quotes:
            status = quote.get("status", "").lower()

            if status == "accepted":
                stats["accepted_quotes"] += 1
            elif status == "rejected":
                stats["rejected_quotes"] += 1
            elif status == "pending":
                stats["pending_quotes"] += 1
            elif status == "expired":
                stats["expired_quotes"] += 1

        # Calculate rates
        if stats["total_quotes"] > 0:
            stats["conversion_rate"] = (
                stats["accepted_quotes"] / stats["total_quotes"]
            ) * 100
            stats["rejection_rate"] = (
                stats["rejected_quotes"] / stats["total_quotes"]
            ) * 100
        else:
            stats["conversion_rate"] = 0.0
            stats["rejection_rate"] = 0.0

        stats["date_range"] = date_range

        return stats

    def get_quote_summary(
        self, account_id: Optional[int] = None, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of quotes.

        Args:
            account_id: Optional account ID to filter by
            date_range: Optional tuple of (start_date, end_date) to filter by

        Returns:
            Dictionary with quote summary:
            - total_quotes: Total number of quotes
            - total_value: Total value of all quotes
            - accepted_quotes: Number of accepted quotes
            - accepted_value: Total value of accepted quotes
            - pending_quotes: Number of pending quotes
            - pending_value: Total value of pending quotes
            - expired_quotes: Number of expired quotes
            - average_quote_value: Average value per quote

        Raises:
            AutotaskAPIError: If the API request fails
        """
        # Get quotes based on filters
        if date_range:
            start_date, end_date = date_range
            quotes = self.get_by_date_range(start_date, end_date, account_id)
        elif account_id:
            quotes = self.get_by_account(account_id)
        else:
            quotes = self.query()

        summary = {
            "account_id": account_id,
            "date_range": date_range,
            "total_quotes": len(quotes),
            "total_value": 0.0,
            "accepted_quotes": 0,
            "accepted_value": 0.0,
            "pending_quotes": 0,
            "pending_value": 0.0,
            "rejected_quotes": 0,
            "rejected_value": 0.0,
            "expired_quotes": 0,
            "expired_value": 0.0,
        }

        for quote in quotes:
            value = float(quote.get("totalAmount", 0))
            status = quote.get("status", "").lower()

            summary["total_value"] += value

            if status == "accepted":
                summary["accepted_quotes"] += 1
                summary["accepted_value"] += value
            elif status == "pending":
                summary["pending_quotes"] += 1
                summary["pending_value"] += value
            elif status == "rejected":
                summary["rejected_quotes"] += 1
                summary["rejected_value"] += value
            elif status == "expired":
                summary["expired_quotes"] += 1
                summary["expired_value"] += value

        # Calculate average
        if summary["total_quotes"] > 0:
            summary["average_quote_value"] = (
                summary["total_value"] / summary["total_quotes"]
            )
        else:
            summary["average_quote_value"] = 0.0

        return summary

    def validate_quote_data(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate quote data.

        Args:
            quote_data: Quote data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["opportunityID", "name", "quoteDate"]
        for field in required_fields:
            if field not in quote_data or quote_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate dates
        quote_date = quote_data.get("quoteDate")
        if quote_date:
            try:
                if isinstance(quote_date, str):
                    datetime.fromisoformat(quote_date.replace("Z", "+00:00"))
            except ValueError:
                errors.append("Quote date must be a valid date")

        expiration_date = quote_data.get("expirationDate")
        if expiration_date:
            try:
                if isinstance(expiration_date, str):
                    exp_date_obj = datetime.fromisoformat(
                        expiration_date.replace("Z", "+00:00")
                    ).date()
                    if quote_date:
                        quote_date_obj = datetime.fromisoformat(
                            quote_date.replace("Z", "+00:00")
                        ).date()
                        if exp_date_obj < quote_date_obj:
                            errors.append("Expiration date cannot be before quote date")
                        elif exp_date_obj < date.today():
                            warnings.append("Expiration date is in the past")
            except ValueError:
                errors.append("Expiration date must be a valid date")

        # Validate amounts
        total_amount = quote_data.get("totalAmount")
        if total_amount is not None:
            try:
                amount_float = float(total_amount)
                if amount_float < 0:
                    warnings.append("Quote amount is negative")
                elif amount_float == 0:
                    warnings.append("Quote amount is zero")
            except (ValueError, TypeError):
                errors.append("Total amount must be a valid number")

        # Validate name
        name = quote_data.get("name")
        if name and len(str(name).strip()) == 0:
            errors.append("Quote name cannot be empty")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
