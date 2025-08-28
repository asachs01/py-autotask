"""
PaymentTerms entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class PaymentTermsEntity(BaseEntity):
    """
    Handles all Payment Terms-related operations for the Autotask API.

    Payment Terms define the conditions under which payments are to be made.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_payment_term(
        self,
        name: str,
        due_days: int,
        discount_percentage: Optional[float] = None,
        discount_days: Optional[int] = None,
        is_active: bool = True,
        description: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new payment term.

        Args:
            name: Name of the payment term
            due_days: Number of days until payment is due
            discount_percentage: Early payment discount percentage
            discount_days: Number of days to qualify for discount
            is_active: Whether the payment term is active
            description: Description of the payment term
            **kwargs: Additional payment term fields

        Returns:
            Created payment term data
        """
        payment_term_data = {
            "Name": name,
            "DueDays": due_days,
            "IsActive": is_active,
            **kwargs,
        }

        if discount_percentage is not None:
            payment_term_data["DiscountPercentage"] = discount_percentage
        if discount_days is not None:
            payment_term_data["DiscountDays"] = discount_days
        if description:
            payment_term_data["Description"] = description

        return self.create(payment_term_data)

    def get_active_payment_terms(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all active payment terms.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of active payment terms
        """
        filters = [QueryFilter(field="IsActive", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def search_payment_terms_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for payment terms by name.

        Args:
            name: Name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching payment terms
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_payment_terms_by_due_days(
        self, due_days: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get payment terms with specific due days.

        Args:
            due_days: Number of due days to filter by
            limit: Maximum number of records to return

        Returns:
            List of payment terms with the specified due days
        """
        filters = [QueryFilter(field="DueDays", op="eq", value=due_days)]

        return self.query(filters=filters, max_records=limit)

    def get_payment_terms_with_discount(
        self, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get payment terms that offer early payment discounts.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of payment terms with discounts
        """
        filters = [QueryFilter(field="DiscountPercentage", op="gt", value=0)]

        return self.query(filters=filters, max_records=limit)

    def get_net_payment_terms(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get "Net" payment terms (typically 30, 60, or 90 days).

        Args:
            limit: Maximum number of records to return

        Returns:
            List of net payment terms
        """
        filters = [QueryFilter(field="Name", op="contains", value="Net")]

        return self.query(filters=filters, max_records=limit)

    def update_payment_term_status(
        self, payment_term_id: int, is_active: bool
    ) -> EntityDict:
        """
        Activate or deactivate a payment term.

        Args:
            payment_term_id: ID of the payment term
            is_active: Whether to activate or deactivate

        Returns:
            Updated payment term data
        """
        return self.update_by_id(payment_term_id, {"IsActive": is_active})

    def update_discount_terms(
        self,
        payment_term_id: int,
        discount_percentage: Optional[float] = None,
        discount_days: Optional[int] = None,
    ) -> EntityDict:
        """
        Update the discount terms for a payment term.

        Args:
            payment_term_id: ID of the payment term
            discount_percentage: New discount percentage
            discount_days: New discount days

        Returns:
            Updated payment term data
        """
        update_data = {}
        if discount_percentage is not None:
            update_data["DiscountPercentage"] = discount_percentage
        if discount_days is not None:
            update_data["DiscountDays"] = discount_days

        return self.update_by_id(payment_term_id, update_data)

    def get_payment_terms_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about payment terms.

        Returns:
            Dictionary containing payment terms statistics
        """
        all_terms = self.query()

        # Group by due days
        due_days_distribution = {}
        for term in all_terms:
            due_days = term.get("DueDays", 0)
            due_days_distribution[due_days] = due_days_distribution.get(due_days, 0) + 1

        # Calculate discount statistics
        terms_with_discount = [
            term for term in all_terms if term.get("DiscountPercentage", 0) > 0
        ]

        discount_percentages = [
            term.get("DiscountPercentage", 0) for term in terms_with_discount
        ]

        stats = {
            "total_payment_terms": len(all_terms),
            "active_terms": len(
                [term for term in all_terms if term.get("IsActive", False)]
            ),
            "inactive_terms": len(
                [term for term in all_terms if not term.get("IsActive", False)]
            ),
            "terms_with_discount": len(terms_with_discount),
            "due_days_distribution": due_days_distribution,
        }

        if discount_percentages:
            stats["discount_stats"] = {
                "average_discount": round(
                    sum(discount_percentages) / len(discount_percentages), 2
                ),
                "min_discount": min(discount_percentages),
                "max_discount": max(discount_percentages),
            }

        return stats

    def get_commonly_used_terms(self, limit: int = 10) -> List[EntityDict]:
        """
        Get the most commonly used payment terms.

        Note: This would require additional data about usage frequency,
        which may come from invoice/quote data.

        Args:
            limit: Maximum number of terms to return

        Returns:
            List of commonly used payment terms
        """
        # For now, return active terms sorted by name
        # In practice, this would need to join with invoice/quote data
        # to determine actual usage frequency
        active_terms = self.get_active_payment_terms()

        # Sort by name as a proxy for common usage
        sorted_terms = sorted(active_terms, key=lambda x: x.get("Name", ""))

        return sorted_terms[:limit]

    def create_standard_payment_terms(self) -> List[EntityDict]:
        """
        Create a set of standard payment terms.

        Returns:
            List of created standard payment terms
        """
        standard_terms = [
            {"name": "Net 30", "due_days": 30, "description": "Payment due in 30 days"},
            {"name": "Net 15", "due_days": 15, "description": "Payment due in 15 days"},
            {"name": "Net 60", "due_days": 60, "description": "Payment due in 60 days"},
            {
                "name": "2/10 Net 30",
                "due_days": 30,
                "discount_percentage": 2.0,
                "discount_days": 10,
                "description": "2% discount if paid within 10 days, otherwise due in 30 days",
            },
            {
                "name": "Due on Receipt",
                "due_days": 0,
                "description": "Payment due immediately",
            },
            {"name": "COD", "due_days": 0, "description": "Cash on Delivery"},
        ]

        created_terms = []
        for term_data in standard_terms:
            try:
                created_term = self.create_payment_term(**term_data)
                created_terms.append(created_term)
            except Exception as e:
                # Log the error but continue with other terms
                print(f"Error creating payment term {term_data['name']}: {e}")

        return created_terms
