"""
Contract Services entity for Autotask API.

This module provides the ContractServicesEntity class for managing
contract services within the Autotask system.
"""

from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ContractServicesEntity(BaseEntity):
    """
    Entity for managing Autotask Contract Services.

    Contract Services represent billable services associated with contracts,
    including service definitions, pricing, and billing configurations.
    """

    def __init__(self, client, entity_name="ContractServices"):
        """Initialize the Contract Services entity."""
        super().__init__(client, entity_name)

    def create(self, contract_service_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new contract service.

        Args:
            contract_service_data: Dictionary containing contract service information
                Required fields:
                - contractID: ID of the associated contract
                - serviceID: ID of the service
                - unitPrice: Price per unit
                Optional fields:
                - unitCost: Cost per unit
                - adjustedPrice: Adjusted price if different from unit price
                - businessDivisionSubdivisionID: Business division subdivision
                - internalCurrencyAdjustedPrice: Adjusted price in internal currency
                - internalCurrencyUnitPrice: Unit price in internal currency
                - invoiceDescription: Description for invoicing
                - periodCost: Period cost
                - quoteItemID: Associated quote item ID
                - vendorAccountID: Vendor account ID

        Returns:
            CreateResponse: Response containing created contract service data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["contractID", "serviceID", "unitPrice"]
        self._validate_required_fields(contract_service_data, required_fields)

        return self._create(contract_service_data)

    def get(self, contract_service_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a contract service by ID.

        Args:
            contract_service_id: The contract service ID

        Returns:
            Dictionary containing contract service data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(contract_service_id)

    def update(
        self, contract_service_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing contract service.

        Args:
            contract_service_id: The contract service ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated contract service data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(contract_service_id, update_data)

    def delete(self, contract_service_id: int) -> bool:
        """
        Delete a contract service.

        Args:
            contract_service_id: The contract service ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(contract_service_id)

    def query(
        self, filters: Optional[List[QueryFilter]] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Query contract services with optional filters.

        Args:
            filters: List of QueryFilter objects for filtering results
            **kwargs: Additional query parameters (max_records, fields, etc.)

        Returns:
            List of dictionaries containing contract service data

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._query(filters, **kwargs)

    def get_by_contract(self, contract_id: int) -> List[Dict[str, Any]]:
        """
        Get all contract services for a specific contract.

        Args:
            contract_id: The contract ID

        Returns:
            List of contract services for the specified contract

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="contractID", op="eq", value=contract_id)]
        return self.query(filters)

    def get_by_service(self, service_id: int) -> List[Dict[str, Any]]:
        """
        Get all contract services for a specific service.

        Args:
            service_id: The service ID

        Returns:
            List of contract services for the specified service

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = [QueryFilter(field="serviceID", op="eq", value=service_id)]
        return self.query(filters)

    def get_active_services(
        self, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active contract services, optionally filtered by contract.

        Args:
            contract_id: Optional contract ID to filter by

        Returns:
            List of active contract services

        Raises:
            AutotaskAPIError: If the API request fails
        """
        filters = []

        if contract_id:
            filters.append(QueryFilter(field="contractID", op="eq", value=contract_id))

        # Add filter for active services (assuming isActive field exists)
        # Note: Adjust field name based on actual Autotask API schema
        filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters)

    def calculate_service_total(
        self, contract_service_data: Dict[str, Any], quantity: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate total cost and price for a contract service.

        Args:
            contract_service_data: Contract service data
            quantity: Quantity to calculate for (default: 1.0)

        Returns:
            Dictionary with calculated totals:
            - total_price: Total price (unitPrice * quantity)
            - total_cost: Total cost (unitCost * quantity) if available
            - profit_margin: Profit margin if both price and cost available

        Raises:
            ValueError: If required pricing data is missing
        """
        if "unitPrice" not in contract_service_data:
            raise ValueError("Unit price is required for calculation")

        unit_price = float(contract_service_data["unitPrice"])
        total_price = unit_price * quantity

        result = {
            "total_price": total_price,
            "quantity": quantity,
            "unit_price": unit_price,
        }

        # Calculate cost totals if available
        if (
            "unitCost" in contract_service_data
            and contract_service_data["unitCost"] is not None
        ):
            unit_cost = float(contract_service_data["unitCost"])
            total_cost = unit_cost * quantity
            profit = total_price - total_cost
            profit_margin = (profit / total_price * 100) if total_price > 0 else 0

            result.update(
                {
                    "total_cost": total_cost,
                    "unit_cost": unit_cost,
                    "profit": profit,
                    "profit_margin": profit_margin,
                }
            )

        return result

    def bulk_update_pricing(
        self, contract_id: int, price_adjustments: Dict[int, Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Bulk update pricing for multiple contract services.

        Args:
            contract_id: The contract ID
            price_adjustments: Dictionary mapping service IDs to pricing updates
                Example: {service_id: {'unitPrice': 100.0, 'adjustedPrice': 95.0}}

        Returns:
            List of UpdateResponse objects for each updated service

        Raises:
            AutotaskAPIError: If any API request fails
        """
        # Get current contract services
        contract_services = self.get_by_contract(contract_id)

        results = []
        for service in contract_services:
            service_id = service.get("serviceID")
            if service_id in price_adjustments:
                contract_service_id = service["id"]
                update_data = price_adjustments[service_id]

                try:
                    result = self.update(contract_service_id, update_data)
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other updates
                    self.logger.error(f"Failed to update service {service_id}: {e}")
                    results.append(
                        {
                            "error": str(e),
                            "service_id": service_id,
                            "contract_service_id": contract_service_id,
                        }
                    )

        return results

    def validate_service_pricing(
        self, contract_service_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate contract service pricing data.

        Args:
            contract_service_data: Contract service data to validate

        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if data is valid
            - errors: List of validation errors
            - warnings: List of validation warnings

        Raises:
            None (returns validation results instead)
        """
        errors = []
        warnings = []

        # Check required pricing fields
        if (
            "unitPrice" not in contract_service_data
            or contract_service_data["unitPrice"] is None
        ):
            errors.append("Unit price is required")
        elif float(contract_service_data["unitPrice"]) < 0:
            errors.append("Unit price cannot be negative")

        # Check cost vs price relationship
        if (
            "unitCost" in contract_service_data
            and "unitPrice" in contract_service_data
            and contract_service_data["unitCost"] is not None
            and contract_service_data["unitPrice"] is not None
        ):

            unit_cost = float(contract_service_data["unitCost"])
            unit_price = float(contract_service_data["unitPrice"])

            if unit_cost > unit_price:
                warnings.append("Unit cost is higher than unit price (negative margin)")
            elif unit_cost == unit_price:
                warnings.append("Unit cost equals unit price (zero margin)")

        # Check adjusted price
        if (
            "adjustedPrice" in contract_service_data
            and "unitPrice" in contract_service_data
            and contract_service_data["adjustedPrice"] is not None
            and contract_service_data["unitPrice"] is not None
        ):

            adjusted_price = float(contract_service_data["adjustedPrice"])
            unit_price = float(contract_service_data["unitPrice"])

            if adjusted_price != unit_price:
                warnings.append(
                    f"Adjusted price ({adjusted_price}) differs from unit price ({unit_price})"
                )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
