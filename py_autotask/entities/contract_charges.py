"""
ContractCharges Entity for py-autotask

This module provides the ContractChargesEntity class for managing contract charges
in Autotask. Contract charges represent charges that are applied to contracts for
billing purposes, including recurring charges, one-time fees, and adjustments.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractChargesEntity(BaseEntity):
    """
    Manages Autotask ContractCharges - charges applied to contracts.

    Contract charges represent various types of charges that can be applied
    to contracts, including recurring fees, one-time charges, adjustments,
    and other billing items associated with service contracts.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractCharges"

    # Core CRUD Operations

    def create_contract_charge(
        self,
        contract_id: int,
        billing_code_id: int,
        description: str,
        unit_quantity: Union[float, Decimal],
        unit_price: Union[float, Decimal],
        charge_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract charge.

        Args:
            contract_id: ID of the contract
            billing_code_id: ID of the billing code
            description: Description of the charge
            unit_quantity: Quantity of units
            unit_price: Price per unit
            charge_date: Date of the charge (defaults to today)
            **kwargs: Additional fields for the contract charge

        Returns:
            Create response with new contract charge ID

        Example:
            charge = client.contract_charges.create_contract_charge(
                contract_id=12345,
                billing_code_id=678,
                description="Monthly monitoring fee",
                unit_quantity=1.0,
                unit_price=299.00
            )
        """
        if charge_date is None:
            charge_date = date.today()

        charge_data = {
            "contractID": contract_id,
            "billingCodeID": billing_code_id,
            "description": description,
            "unitQuantity": float(unit_quantity),
            "unitPrice": float(unit_price),
            "chargeDate": charge_date.isoformat(),
            **kwargs,
        }

        return self.create(charge_data)

    def get_contract_charges_by_contract(
        self,
        contract_id: int,
        include_billed: bool = True,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get contract charges for a specific contract.

        Args:
            contract_id: ID of the contract
            include_billed: Whether to include already billed charges
            date_from: Start date for filtering
            date_to: End date for filtering

        Returns:
            List of contract charges
        """
        filters = [f"contractID eq {contract_id}"]

        if not include_billed:
            filters.append("billedDate eq null")

        if date_from:
            filters.append(f"chargeDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"chargeDate le {date_to.isoformat()}")

        return self.query(filter=" and ".join(filters))

    def get_unbilled_contract_charges(
        self, contract_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get unbilled contract charges.

        Args:
            contract_id: Optional filter by contract ID

        Returns:
            List of unbilled contract charges
        """
        filters = ["billedDate eq null"]

        if contract_id:
            filters.append(f"contractID eq {contract_id}")

        return self.query(filter=" and ".join(filters))

    # Business Logic Methods

    def calculate_charge_total(
        self,
        unit_quantity: Union[float, Decimal],
        unit_price: Union[float, Decimal],
        unit_cost: Optional[Union[float, Decimal]] = None,
    ) -> Dict[str, Decimal]:
        """
        Calculate contract charge totals.

        Args:
            unit_quantity: Quantity of units
            unit_price: Price per unit
            unit_cost: Cost per unit (optional)

        Returns:
            Dictionary with calculated totals
        """
        quantity = Decimal(str(unit_quantity))
        price = Decimal(str(unit_price))

        total_price = quantity * price

        result = {
            "unit_quantity": quantity,
            "unit_price": price,
            "total_price": total_price,
            "unit_cost": Decimal("0"),
            "total_cost": Decimal("0"),
            "profit_margin": total_price,
        }

        if unit_cost is not None:
            cost = Decimal(str(unit_cost))
            total_cost = quantity * cost
            result.update(
                {
                    "unit_cost": cost,
                    "total_cost": total_cost,
                    "profit_margin": total_price - total_cost,
                }
            )

        return result

    def approve_contract_charges(
        self,
        charge_ids: List[int],
        approver_resource_id: int,
        approval_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve contract charges for billing.

        Args:
            charge_ids: List of contract charge IDs to approve
            approver_resource_id: ID of the approving resource
            approval_notes: Optional approval notes

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
        for charge_id in charge_ids:
            try:
                result = self.update(charge_id, update_data)
                results.append({"id": charge_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": charge_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_charges": len(charge_ids),
            "successful": len(successful),
            "failed": len(failed),
            "approver_resource_id": approver_resource_id,
            "approval_date": approval_date,
            "results": results,
        }

    def mark_charges_as_billed(
        self,
        charge_ids: List[int],
        billed_date: Optional[date] = None,
        invoice_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Mark contract charges as billed.

        Args:
            charge_ids: List of contract charge IDs
            billed_date: Date when charges were billed
            invoice_id: Optional invoice ID

        Returns:
            Summary of billing operation
        """
        if billed_date is None:
            billed_date = date.today()

        update_data = {"billedDate": billed_date.isoformat()}

        if invoice_id:
            update_data["invoiceID"] = invoice_id

        results = []
        for charge_id in charge_ids:
            try:
                result = self.update(charge_id, update_data)
                results.append({"id": charge_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": charge_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_charges": len(charge_ids),
            "successful": len(successful),
            "failed": len(failed),
            "billed_date": billed_date.isoformat(),
            "invoice_id": invoice_id,
            "results": results,
        }

    def get_contract_charges_summary(
        self,
        contract_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get summary of contract charges.

        Args:
            contract_id: ID of the contract
            date_from: Start date for summary
            date_to: End date for summary

        Returns:
            Summary of contract charges
        """
        filters = [f"contractID eq {contract_id}"]

        if date_from:
            filters.append(f"chargeDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"chargeDate le {date_to.isoformat()}")

        charges = self.query(filter=" and ".join(filters))

        total_charges = len(charges)
        total_amount = Decimal("0")
        total_cost = Decimal("0")
        billed_amount = Decimal("0")
        unbilled_amount = Decimal("0")
        billed_count = 0
        unbilled_count = 0

        for charge in charges:
            quantity = Decimal(str(charge.get("unitQuantity", 0)))
            price = Decimal(str(charge.get("unitPrice", 0)))
            cost = Decimal(str(charge.get("unitCost", 0)))

            charge_amount = quantity * price
            charge_cost = quantity * cost

            total_amount += charge_amount
            total_cost += charge_cost

            if charge.get("billedDate"):
                billed_amount += charge_amount
                billed_count += 1
            else:
                unbilled_amount += charge_amount
                unbilled_count += 1

        return {
            "contract_id": contract_id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "summary": {
                "total_charges": total_charges,
                "total_amount": total_amount,
                "total_cost": total_cost,
                "profit_margin": total_amount - total_cost,
                "billed_charges": billed_count,
                "billed_amount": billed_amount,
                "unbilled_charges": unbilled_count,
                "unbilled_amount": unbilled_amount,
            },
        }

    def create_recurring_charge(
        self,
        contract_id: int,
        billing_code_id: int,
        description: str,
        unit_quantity: Union[float, Decimal],
        unit_price: Union[float, Decimal],
        recurrence_frequency: str,
        start_date: date,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a recurring contract charge.

        Args:
            contract_id: ID of the contract
            billing_code_id: ID of the billing code
            description: Description of the charge
            unit_quantity: Quantity per occurrence
            unit_price: Price per unit
            recurrence_frequency: Frequency (Monthly, Quarterly, etc.)
            start_date: Start date for recurring charges
            end_date: Optional end date

        Returns:
            Create response for recurring charge
        """
        charge_data = {
            "contractID": contract_id,
            "billingCodeID": billing_code_id,
            "description": description,
            "unitQuantity": float(unit_quantity),
            "unitPrice": float(unit_price),
            "recurrenceFrequency": recurrence_frequency,
            "startDate": start_date.isoformat(),
            "isRecurring": True,
        }

        if end_date:
            charge_data["endDate"] = end_date.isoformat()

        return self.create(charge_data)

    def get_recurring_charges(
        self, contract_id: Optional[int] = None, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get recurring contract charges.

        Args:
            contract_id: Optional filter by contract ID
            active_only: Whether to only return active recurring charges

        Returns:
            List of recurring charges
        """
        filters = ["isRecurring eq true"]

        if contract_id:
            filters.append(f"contractID eq {contract_id}")

        if active_only:
            today = date.today().isoformat()
            filters.append(f"(endDate eq null or endDate ge {today})")

        return self.query(filter=" and ".join(filters))

    def bulk_create_charges(self, charges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple contract charges in batch.

        Args:
            charges: List of charge data dictionaries

        Returns:
            Summary of batch creation operation
        """
        results = []

        for charge_data in charges:
            try:
                result = self.create(charge_data)
                results.append({"success": True, "result": result, "data": charge_data})
            except Exception as e:
                results.append({"success": False, "error": str(e), "data": charge_data})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_charges": len(charges),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_charges_by_billing_code(
        self,
        billing_code_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get contract charges by billing code.

        Args:
            billing_code_id: ID of the billing code
            date_from: Start date for filtering
            date_to: End date for filtering

        Returns:
            List of contract charges using the billing code
        """
        filters = [f"billingCodeID eq {billing_code_id}"]

        if date_from:
            filters.append(f"chargeDate ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"chargeDate le {date_to.isoformat()}")

        return self.query(filter=" and ".join(filters))

    def update_charge_amounts(
        self,
        charge_id: int,
        unit_quantity: Optional[Union[float, Decimal]] = None,
        unit_price: Optional[Union[float, Decimal]] = None,
        unit_cost: Optional[Union[float, Decimal]] = None,
    ) -> Dict[str, Any]:
        """
        Update charge amounts.

        Args:
            charge_id: ID of the contract charge
            unit_quantity: New unit quantity
            unit_price: New unit price
            unit_cost: New unit cost

        Returns:
            Update response
        """
        update_data = {}

        if unit_quantity is not None:
            update_data["unitQuantity"] = float(unit_quantity)
        if unit_price is not None:
            update_data["unitPrice"] = float(unit_price)
        if unit_cost is not None:
            update_data["unitCost"] = float(unit_cost)

        return self.update(charge_id, update_data)

    def get_revenue_by_contract(
        self, date_from: date, date_to: date, contract_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get revenue breakdown by contract for contract charges.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis
            contract_ids: Optional list of specific contracts

        Returns:
            Revenue breakdown by contract
        """
        filters = [
            f"chargeDate ge {date_from.isoformat()}",
            f"chargeDate le {date_to.isoformat()}",
            "billedDate ne null",  # Only billed charges
        ]

        if contract_ids:
            contract_filter = " or ".join(
                [f"contractID eq {cid}" for cid in contract_ids]
            )
            filters.append(f"({contract_filter})")

        charges = self.query(filter=" and ".join(filters))

        # Group by contract
        revenue_by_contract = {}
        for charge in charges:
            contract_id = charge.get("contractID")
            if contract_id:
                if contract_id not in revenue_by_contract:
                    revenue_by_contract[contract_id] = {
                        "contract_id": contract_id,
                        "charge_count": 0,
                        "total_revenue": Decimal("0"),
                        "total_cost": Decimal("0"),
                    }

                contract_data = revenue_by_contract[contract_id]
                contract_data["charge_count"] += 1

                quantity = Decimal(str(charge.get("unitQuantity", 0)))
                price = Decimal(str(charge.get("unitPrice", 0)))
                cost = Decimal(str(charge.get("unitCost", 0)))

                contract_data["total_revenue"] += quantity * price
                contract_data["total_cost"] += quantity * cost

        # Calculate profit margins
        for contract_data in revenue_by_contract.values():
            profit = contract_data["total_revenue"] - contract_data["total_cost"]
            contract_data["profit_margin"] = profit
            contract_data["profit_percentage"] = (
                float(profit / contract_data["total_revenue"] * 100)
                if contract_data["total_revenue"] > 0
                else 0
            )

        total_revenue = sum(
            data["total_revenue"] for data in revenue_by_contract.values()
        )
        total_cost = sum(data["total_cost"] for data in revenue_by_contract.values())

        return {
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "summary": {
                "total_contracts": len(revenue_by_contract),
                "total_charges": sum(
                    data["charge_count"] for data in revenue_by_contract.values()
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
            "by_contract": list(revenue_by_contract.values()),
        }
