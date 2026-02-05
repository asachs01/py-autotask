"""
Configuration Item Billing Product Associations entity for Autotask API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemBillingProductAssociationsEntity(BaseEntity):
    """
    Handles all Configuration Item Billing Product Association-related operations for the Autotask API.

    Configuration Item Billing Product Associations link configuration items to billing products
    for recurring billing and service management purposes.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ci_billing_association(
        self,
        configuration_item_id: int,
        billing_product_id: int,
        quantity: float = 1.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item billing product association.

        Args:
            configuration_item_id: ID of the configuration item
            billing_product_id: ID of the billing product
            quantity: Quantity of the product (default 1.0)
            start_date: Association start date (ISO format)
            end_date: Optional association end date (ISO format)
            **kwargs: Additional association fields

        Returns:
            Created billing product association data
        """
        association_data = {
            "ConfigurationItemID": configuration_item_id,
            "BillingProductID": billing_product_id,
            "Quantity": quantity,
            **kwargs,
        }

        if start_date:
            association_data["StartDate"] = start_date
        else:
            association_data["StartDate"] = datetime.now().isoformat()

        if end_date:
            association_data["EndDate"] = end_date

        return self.create(association_data)

    def get_ci_billing_associations(
        self,
        configuration_item_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all billing product associations for a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of billing product associations
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            )
        ]

        if active_only:
            # Filter out associations that have ended
            current_date = datetime.now().isoformat()
            filters.append(QueryFilter(field="EndDate", op="gt", value=current_date))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_associations_by_product(
        self,
        billing_product_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all configuration item associations for a specific billing product.

        Args:
            billing_product_id: ID of the billing product
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of configuration item associations
        """
        filters = [
            QueryFilter(field="BillingProductID", op="eq", value=billing_product_id)
        ]

        if active_only:
            current_date = datetime.now().isoformat()
            filters.append(QueryFilter(field="EndDate", op="gt", value=current_date))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_expiring_associations(
        self,
        days_ahead: int = 30,
        configuration_item_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing associations that are expiring within a specified timeframe.

        Args:
            days_ahead: Number of days ahead to check for expiration
            configuration_item_id: Optional filter by configuration item

        Returns:
            List of associations expiring soon
        """
        from datetime import datetime, timedelta

        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        current_date = datetime.now().isoformat()

        filters = [
            QueryFilter(field="EndDate", op="lte", value=future_date),
            QueryFilter(field="EndDate", op="gte", value=current_date),
        ]

        if configuration_item_id:
            filters.append(
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            )

        response = self.query(filters=filters)
        return response.items

    def update_association_quantity(
        self, association_id: int, new_quantity: float
    ) -> Dict[str, Any]:
        """
        Update the quantity for a billing product association.

        Args:
            association_id: ID of association to update
            new_quantity: New quantity value

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"Quantity": new_quantity})

    def extend_association(
        self, association_id: int, new_end_date: str
    ) -> Dict[str, Any]:
        """
        Extend the end date of a billing product association.

        Args:
            association_id: ID of association to extend
            new_end_date: New end date (ISO format)

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"EndDate": new_end_date})

    def terminate_association(
        self, association_id: int, termination_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Terminate a billing product association.

        Args:
            association_id: ID of association to terminate
            termination_date: Optional termination date (defaults to now)

        Returns:
            Updated association data
        """
        end_date = termination_date or datetime.now().isoformat()
        return self.update_by_id(association_id, {"EndDate": end_date})

    def get_ci_billing_summary(self, configuration_item_id: int) -> Dict[str, Any]:
        """
        Get a billing summary for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item

        Returns:
            Dictionary with billing statistics
        """
        associations = self.get_ci_billing_associations(
            configuration_item_id, active_only=False
        )

        summary = {
            "configuration_item_id": configuration_item_id,
            "total_associations": len(associations),
            "active_associations": 0,
            "expired_associations": 0,
            "total_monthly_cost": 0.0,
            "products": [],
        }

        current_date = datetime.now()

        for association in associations:
            product_id = association.get("BillingProductID")
            quantity = float(association.get("Quantity", 0))
            end_date_str = association.get("EndDate")

            # Determine if association is active
            is_active = True
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(
                        end_date_str.replace("Z", "+00:00")
                    )
                    is_active = end_date > current_date
                except ValueError:
                    pass

            if is_active:
                summary["active_associations"] += 1
            else:
                summary["expired_associations"] += 1

            # Get product details (simplified - actual implementation may vary)
            product_info = {
                "product_id": product_id,
                "quantity": quantity,
                "active": is_active,
            }

            # Add to monthly cost if product has pricing info
            # This would typically involve querying the product to get pricing

            summary["products"].append(product_info)

        return summary

    def bulk_update_quantities(
        self, association_updates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Update quantities for multiple billing product associations in bulk.

        Args:
            association_updates: List of dicts with 'association_id' and 'quantity'

        Returns:
            List of updated association data
        """
        update_data = [
            {"id": update["association_id"], "Quantity": update["quantity"]}
            for update in association_updates
        ]
        return self.batch_update(update_data)

    def get_associations_by_date_range(
        self,
        start_date: str,
        end_date: str,
        configuration_item_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing associations created within a specific date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            configuration_item_id: Optional filter by configuration item

        Returns:
            List of associations within the date range
        """
        filters = [
            QueryFilter(field="StartDate", op="gte", value=start_date),
            QueryFilter(field="StartDate", op="lte", value=end_date),
        ]

        if configuration_item_id:
            filters.append(
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            )

        response = self.query(filters=filters)
        return response.items
