"""
BillingItems Entity for py-autotask

This module provides the BillingItemsEntity class for managing individual billing line items
in Autotask. BillingItems represent individual charges that can be associated with contracts,
projects, tickets, and time entries for billing purposes.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class BillingItemsEntity(BaseEntity):
    """
    Manages Autotask BillingItems - individual billing line items.

    BillingItems represent individual charges that can be associated with various
    entities for billing purposes. They support complex billing scenarios including
    time and materials, fixed price, and recurring billing.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "BillingItems"

    # Core CRUD Operations

    def create_billing_item(
        self,
        entity_id: int,
        entity_type: str,
        billing_code_id: int,
        description: str,
        quantity: Union[float, Decimal] = 1.0,
        unit_price: Optional[Union[float, Decimal]] = None,
        unit_cost: Optional[Union[float, Decimal]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new billing item.

        Args:
            entity_id: ID of the associated entity (contract, project, ticket, etc.)
            entity_type: Type of associated entity
            billing_code_id: ID of the billing code to use
            description: Description of the billing item
            quantity: Quantity of items (default: 1.0)
            unit_price: Price per unit
            unit_cost: Cost per unit
            **kwargs: Additional fields for the billing item

        Returns:
            Create response with new billing item ID

        Example:
            billing_item = client.billing_items.create_billing_item(
                entity_id=12345,
                entity_type="Ticket",
                billing_code_id=678,
                description="Emergency support services",
                quantity=2.5,
                unit_price=150.00
            )
        """
        billing_data = {
            "entityID": entity_id,
            "entityType": entity_type,
            "billingCodeID": billing_code_id,
            "description": description,
            "quantity": float(quantity),
            **kwargs,
        }

        if unit_price is not None:
            billing_data["unitPrice"] = float(unit_price)
        if unit_cost is not None:
            billing_data["unitCost"] = float(unit_cost)

        return self.create(billing_data)

    def get_billing_items_by_entity(
        self,
        entity_id: int,
        entity_type: Optional[str] = None,
        include_billed: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all billing items for a specific entity.

        Args:
            entity_id: ID of the entity
            entity_type: Type of entity (optional filter)
            include_billed: Whether to include already billed items

        Returns:
            List of billing items for the entity
        """
        filters = [f"entityID eq {entity_id}"]

        if entity_type:
            filters.append(f"entityType eq '{entity_type}'")

        if not include_billed:
            filters.append("billedDate eq null")

        return self.query(filter=" and ".join(filters))

    def get_billing_items_by_billing_code(
        self,
        billing_code_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing items by billing code with optional date range.

        Args:
            billing_code_id: ID of the billing code
            date_from: Start date for filtering
            date_to: End date for filtering

        Returns:
            List of billing items using the specified billing code
        """
        filters = [f"billingCodeID eq {billing_code_id}"]

        if date_from:
            filters.append(f"createDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"createDate le {date_to.isoformat()}")

        return self.query(filter=" and ".join(filters))

    # Business Logic Methods

    def calculate_item_total(
        self,
        quantity: Union[float, Decimal],
        unit_price: Union[float, Decimal],
        tax_rate: Optional[Union[float, Decimal]] = None,
    ) -> Dict[str, Decimal]:
        """
        Calculate billing item totals including tax.

        Args:
            quantity: Quantity of items
            unit_price: Price per unit
            tax_rate: Tax rate as decimal (e.g., 0.075 for 7.5%)

        Returns:
            Dictionary with calculated totals
        """
        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price))

        subtotal = quantity * unit_price

        result = {
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "tax_amount": Decimal("0"),
            "total": subtotal,
        }

        if tax_rate is not None:
            tax_rate = Decimal(str(tax_rate))
            tax_amount = subtotal * tax_rate
            result["tax_amount"] = tax_amount
            result["total"] = subtotal + tax_amount

        return result

    def get_unbilled_items_summary(
        self, entity_id: Optional[int] = None, entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary of unbilled items.

        Args:
            entity_id: Filter by specific entity ID
            entity_type: Filter by entity type

        Returns:
            Summary of unbilled billing items
        """
        filters = ["billedDate eq null"]

        if entity_id:
            filters.append(f"entityID eq {entity_id}")
        if entity_type:
            filters.append(f"entityType eq '{entity_type}'")

        items = self.query(filter=" and ".join(filters))

        total_amount = Decimal("0")
        total_cost = Decimal("0")
        item_count = len(items)

        for item in items:
            if item.get("unitPrice") and item.get("quantity"):
                total_amount += Decimal(str(item["unitPrice"])) * Decimal(
                    str(item["quantity"])
                )
            if item.get("unitCost") and item.get("quantity"):
                total_cost += Decimal(str(item["unitCost"])) * Decimal(
                    str(item["quantity"])
                )

        return {
            "item_count": item_count,
            "total_amount": total_amount,
            "total_cost": total_cost,
            "profit_margin": total_amount - total_cost,
            "profit_percentage": (
                float((total_amount - total_cost) / total_amount * 100)
                if total_amount > 0
                else 0
            ),
        }

    def mark_items_as_billed(
        self, billing_item_ids: List[int], billed_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Mark billing items as billed.

        Args:
            billing_item_ids: List of billing item IDs to mark as billed
            billed_date: Date when items were billed (defaults to today)

        Returns:
            Summary of update operation
        """
        if billed_date is None:
            billed_date = date.today()

        update_data = {"billedDate": billed_date.isoformat()}

        results = []
        for item_id in billing_item_ids:
            try:
                result = self.update(item_id, update_data)
                results.append({"id": item_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": item_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_items": len(billing_item_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_billing_items_by_contract(
        self,
        contract_id: int,
        include_billed: bool = True,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get billing items associated with a specific contract.

        Args:
            contract_id: ID of the contract
            include_billed: Whether to include already billed items
            date_from: Start date for filtering
            date_to: End date for filtering

        Returns:
            List of billing items for the contract
        """
        filters = [f"contractID eq {contract_id}"]

        if not include_billed:
            filters.append("billedDate eq null")

        if date_from:
            filters.append(f"createDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"createDate le {date_to.isoformat()}")

        return self.query(filter=" and ".join(filters))

    def get_billing_items_by_project(
        self, project_id: int, include_billed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get billing items associated with a specific project.

        Args:
            project_id: ID of the project
            include_billed: Whether to include already billed items

        Returns:
            List of billing items for the project
        """
        filters = [f"entityID eq {project_id}", "entityType eq 'Project'"]

        if not include_billed:
            filters.append("billedDate eq null")

        return self.query(filter=" and ".join(filters))

    def bulk_create_billing_items(
        self, billing_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple billing items in batch.

        Args:
            billing_items: List of billing item data dictionaries

        Returns:
            Summary of batch creation operation
        """
        results = []

        for item_data in billing_items:
            try:
                result = self.create(item_data)
                results.append({"success": True, "result": result, "data": item_data})
            except Exception as e:
                results.append({"success": False, "error": str(e), "data": item_data})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_items": len(billing_items),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_revenue_by_billing_code(
        self,
        date_from: date,
        date_to: date,
        billing_code_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Get revenue breakdown by billing code for a date range.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            billing_code_ids: Optional list of specific billing codes to analyze

        Returns:
            Revenue breakdown by billing code
        """
        filters = [
            f"createDate ge {date_from.isoformat()}",
            f"createDate le {date_to.isoformat()}",
            "billedDate ne null",  # Only billed items
        ]

        if billing_code_ids:
            code_filter = " or ".join(
                [f"billingCodeID eq {code_id}" for code_id in billing_code_ids]
            )
            filters.append(f"({code_filter})")

        items = self.query(filter=" and ".join(filters))

        # Group by billing code
        revenue_by_code = {}
        for item in items:
            billing_code_id = item.get("billingCodeID")
            if billing_code_id:
                if billing_code_id not in revenue_by_code:
                    revenue_by_code[billing_code_id] = {
                        "billing_code_id": billing_code_id,
                        "item_count": 0,
                        "total_revenue": Decimal("0"),
                        "total_cost": Decimal("0"),
                    }

                code_data = revenue_by_code[billing_code_id]
                code_data["item_count"] += 1

                if item.get("unitPrice") and item.get("quantity"):
                    revenue = Decimal(str(item["unitPrice"])) * Decimal(
                        str(item["quantity"])
                    )
                    code_data["total_revenue"] += revenue

                if item.get("unitCost") and item.get("quantity"):
                    cost = Decimal(str(item["unitCost"])) * Decimal(
                        str(item["quantity"])
                    )
                    code_data["total_cost"] += cost

        # Calculate profit margins
        for code_data in revenue_by_code.values():
            profit = code_data["total_revenue"] - code_data["total_cost"]
            code_data["profit_margin"] = profit
            code_data["profit_percentage"] = (
                float(profit / code_data["total_revenue"] * 100)
                if code_data["total_revenue"] > 0
                else 0
            )

        total_revenue = sum(data["total_revenue"] for data in revenue_by_code.values())
        total_cost = sum(data["total_cost"] for data in revenue_by_code.values())

        return {
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "summary": {
                "total_billing_codes": len(revenue_by_code),
                "total_items": sum(
                    data["item_count"] for data in revenue_by_code.values()
                ),
                "total_revenue": total_revenue,
                "total_cost": total_cost,
                "total_profit": total_revenue - total_cost,
                "overall_margin_percentage": (
                    float((total_revenue - total_cost) / total_revenue * 100)
                    if total_revenue > 0
                    else 0
                ),
            },
            "by_billing_code": list(revenue_by_code.values()),
        }

    def approve_billing_items(
        self,
        billing_item_ids: List[int],
        approver_resource_id: int,
        approval_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve billing items for billing.

        Args:
            billing_item_ids: List of billing item IDs to approve
            approver_resource_id: ID of the approving resource
            approval_notes: Optional notes about the approval

        Returns:
            Summary of approval operation
        """
        approval_date = datetime.now().isoformat()

        update_data = {
            "approvedByResourceID": approver_resource_id,
            "approvalDate": approval_date,
        }

        if approval_notes:
            update_data["approvalNotes"] = approval_notes

        results = []
        for item_id in billing_item_ids:
            try:
                result = self.update(item_id, update_data)
                results.append({"id": item_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": item_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_items": len(billing_item_ids),
            "successful": len(successful),
            "failed": len(failed),
            "approver_resource_id": approver_resource_id,
            "approval_date": approval_date,
            "results": results,
        }
