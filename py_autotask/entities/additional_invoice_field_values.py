"""
AdditionalInvoiceFieldValues entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class AdditionalInvoiceFieldValuesEntity(BaseEntity):
    """
    Handles all AdditionalInvoiceFieldValues-related operations for the Autotask API.

    AdditionalInvoiceFieldValues represent custom field values that can be
    associated with invoices for extended invoice data capture.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_field_value(
        self,
        invoice_id: int,
        user_defined_field_id: int,
        value: str,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new additional invoice field value.

        Args:
            invoice_id: ID of the invoice
            user_defined_field_id: ID of the user defined field
            value: Field value
            **kwargs: Additional field properties

        Returns:
            Created additional invoice field value data
        """
        field_data = {
            "InvoiceID": invoice_id,
            "UserDefinedFieldID": user_defined_field_id,
            "Value": value,
            **kwargs,
        }

        return self.create(field_data)

    def get_field_values_by_invoice(
        self, invoice_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all additional field values for a specific invoice.

        Args:
            invoice_id: ID of the invoice
            limit: Maximum number of field values to return

        Returns:
            List of additional field values for the invoice
        """
        filters = [QueryFilter(field="InvoiceID", op="eq", value=invoice_id)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_field_values_by_field_type(
        self, user_defined_field_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all field values for a specific user defined field.

        Args:
            user_defined_field_id: ID of the user defined field
            limit: Maximum number of field values to return

        Returns:
            List of field values for the specified field type
        """
        filters = [
            QueryFilter(
                field="UserDefinedFieldID", op="eq", value=user_defined_field_id
            )
        ]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def update_field_value(
        self, field_value_id: int, value: str, **kwargs
    ) -> EntityDict:
        """
        Update an additional invoice field value.

        Args:
            field_value_id: ID of the field value to update
            value: New field value
            **kwargs: Additional properties to update

        Returns:
            Updated field value data
        """
        update_data = {"Value": value, **kwargs}
        return self.update_by_id(field_value_id, update_data)

    def bulk_create_field_values(
        self, invoice_field_values: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple additional invoice field values in batch.

        Args:
            invoice_field_values: List of field value data dictionaries

        Returns:
            List of created field value responses
        """
        return self.batch_create(invoice_field_values)

    def delete_field_values_by_invoice(self, invoice_id: int) -> List[bool]:
        """
        Delete all additional field values for a specific invoice.

        Args:
            invoice_id: ID of the invoice

        Returns:
            List of deletion success indicators
        """
        field_values = self.get_field_values_by_invoice(invoice_id)
        field_value_ids = [fv["id"] for fv in field_values if "id" in fv]

        if field_value_ids:
            return self.batch_delete(field_value_ids)
        return []

    def get_field_value_statistics(self, user_defined_field_id: int) -> Dict[str, Any]:
        """
        Get statistics about field values for a specific field type.

        Args:
            user_defined_field_id: ID of the user defined field

        Returns:
            Dictionary containing field value statistics
        """
        field_values = self.get_field_values_by_field_type(user_defined_field_id)

        total_count = len(field_values)
        unique_values = set(fv.get("Value", "") for fv in field_values)

        return {
            "total_count": total_count,
            "unique_value_count": len(unique_values),
            "most_common_values": list(unique_values)[:10],  # Top 10 unique values
            "field_usage_rate": total_count / max(1, total_count) * 100,
        }

    def search_field_values_by_content(
        self, search_term: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search field values by content.

        Args:
            search_term: Term to search for in field values
            limit: Maximum number of results to return

        Returns:
            List of field values matching the search term
        """
        filters = [QueryFilter(field="Value", op="contains", value=search_term)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_field_value_format(
        self, user_defined_field_id: int, value: str
    ) -> bool:
        """
        Validate if a field value conforms to expected format for the field type.

        Args:
            user_defined_field_id: ID of the user defined field
            value: Value to validate

        Returns:
            True if value format is valid, False otherwise
        """
        # Basic validation - could be enhanced with field type specific checks
        if not value or not isinstance(value, str):
            return False

        # Check if value is within reasonable length limits
        if len(value) > 8000:  # Autotask typical field limit
            return False

        return True

    def copy_field_values_between_invoices(
        self, source_invoice_id: int, target_invoice_id: int
    ) -> List[EntityDict]:
        """
        Copy all additional field values from one invoice to another.

        Args:
            source_invoice_id: ID of the source invoice
            target_invoice_id: ID of the target invoice

        Returns:
            List of created field value responses
        """
        source_field_values = self.get_field_values_by_invoice(source_invoice_id)

        target_field_values = []
        for field_value in source_field_values:
            target_data = {
                "InvoiceID": target_invoice_id,
                "UserDefinedFieldID": field_value.get("UserDefinedFieldID"),
                "Value": field_value.get("Value"),
            }
            target_field_values.append(target_data)

        if target_field_values:
            return self.bulk_create_field_values(target_field_values)
        return []
