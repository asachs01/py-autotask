"""
InstalledProducts entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class InstalledProductsEntity(BaseEntity):
    """
    Handles all Installed Product-related operations for the Autotask API.

    Installed Products represent products or software installed at customer sites.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_installed_product(
        self,
        company_id: int,
        product_id: int,
        installation_date: str,
        serial_number: Optional[str] = None,
        warranty_expiration_date: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new installed product record.

        Args:
            company_id: ID of the company where product is installed
            product_id: ID of the product
            installation_date: Date when product was installed
            serial_number: Serial number of the installed product
            warranty_expiration_date: When warranty expires
            location: Installation location
            **kwargs: Additional installed product fields

        Returns:
            Created installed product data
        """
        installed_product_data = {
            "AccountID": company_id,
            "ProductID": product_id,
            "InstallDate": installation_date,
            **kwargs,
        }

        if serial_number:
            installed_product_data["SerialNumber"] = serial_number
        if warranty_expiration_date:
            installed_product_data["WarrantyExpirationDate"] = warranty_expiration_date
        if location:
            installed_product_data["Location"] = location

        return self.create(installed_product_data)

    def get_installed_products_by_company(
        self, company_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all installed products for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active installed products
            limit: Maximum number of records to return

        Returns:
            List of installed products for the company
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_installed_products_by_product(
        self, product_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all installations of a specific product.

        Args:
            product_id: ID of the product
            limit: Maximum number of records to return

        Returns:
            List of installations for the product
        """
        filters = [QueryFilter(field="ProductID", op="eq", value=product_id)]

        return self.query(filters=filters, max_records=limit)

    def get_expiring_warranties(
        self, days_ahead: int = 30, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get installed products with warranties expiring soon.

        Args:
            days_ahead: Number of days ahead to check for expiring warranties
            limit: Maximum number of records to return

        Returns:
            List of installed products with expiring warranties
        """
        from datetime import date, timedelta

        expiration_date = (date.today() + timedelta(days=days_ahead)).strftime(
            "%Y-%m-%d"
        )
        filters = [
            QueryFilter(field="WarrantyExpirationDate", op="le", value=expiration_date)
        ]

        return self.query(filters=filters, max_records=limit)

    def search_by_serial_number(
        self, serial_number: str, exact_match: bool = True
    ) -> List[EntityDict]:
        """
        Search for installed products by serial number.

        Args:
            serial_number: Serial number to search for
            exact_match: Whether to do exact match or partial match

        Returns:
            List of matching installed products
        """
        if exact_match:
            filters = [QueryFilter(field="SerialNumber", op="eq", value=serial_number)]
        else:
            filters = [
                QueryFilter(field="SerialNumber", op="contains", value=serial_number)
            ]

        return self.query(filters=filters)

    def update_installation_location(
        self, installed_product_id: int, new_location: str
    ) -> EntityDict:
        """
        Update the installation location of an installed product.

        Args:
            installed_product_id: ID of the installed product
            new_location: New installation location

        Returns:
            Updated installed product data
        """
        return self.update_by_id(installed_product_id, {"Location": new_location})

    def extend_warranty(
        self, installed_product_id: int, new_expiration_date: str
    ) -> EntityDict:
        """
        Extend the warranty expiration date.

        Args:
            installed_product_id: ID of the installed product
            new_expiration_date: New warranty expiration date

        Returns:
            Updated installed product data
        """
        return self.update_by_id(
            installed_product_id, {"WarrantyExpirationDate": new_expiration_date}
        )

    def deactivate_installation(self, installed_product_id: int) -> EntityDict:
        """
        Deactivate an installed product (mark as no longer in use).

        Args:
            installed_product_id: ID of the installed product

        Returns:
            Updated installed product data
        """
        return self.update_by_id(installed_product_id, {"Active": False})

    def get_installations_by_date_range(
        self, start_date: str, end_date: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get installed products installed within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            limit: Maximum number of records to return

        Returns:
            List of installed products within the date range
        """
        filters = [
            QueryFilter(field="InstallDate", op="ge", value=start_date),
            QueryFilter(field="InstallDate", op="le", value=end_date),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_installation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about installed products.

        Returns:
            Dictionary containing installation statistics
        """
        all_installations = self.query()

        stats = {
            "total_installations": len(all_installations),
            "active_installations": len(
                [ip for ip in all_installations if ip.get("Active", False)]
            ),
            "installations_with_warranty": len(
                [ip for ip in all_installations if ip.get("WarrantyExpirationDate")]
            ),
            "installations_with_serial": len(
                [ip for ip in all_installations if ip.get("SerialNumber")]
            ),
        }

        return stats
