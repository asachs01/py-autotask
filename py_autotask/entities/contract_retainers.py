"""
ContractRetainers Entity for py-autotask

This module provides the ContractRetainersEntity class for managing contract
retainers in Autotask. Contract retainers represent prepaid amounts or reserved
funds that are held against a contract for future services or work.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractRetainersEntity(BaseEntity):
    """
    Manages Autotask ContractRetainers - prepaid amounts and reserved funds for contracts.

    Contract retainers represent financial arrangements where clients prepay for
    services or where funds are held in reserve. These can be drawn down against
    as work is performed or services are delivered.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractRetainers"

    # Core CRUD Operations

    def create_retainer(
        self,
        contract_id: int,
        retainer_amount: Union[float, Decimal],
        retainer_type: str = "Prepaid",
        effective_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract retainer.

        Args:
            contract_id: ID of the contract
            retainer_amount: Amount of the retainer
            retainer_type: Type of retainer (Prepaid, Reserved, Security, etc.)
            effective_date: When the retainer becomes effective
            expiration_date: When the retainer expires
            description: Description of the retainer
            **kwargs: Additional fields for the retainer

        Returns:
            Create response with new retainer ID

        Example:
            retainer = client.contract_retainers.create_retainer(
                contract_id=12345,
                retainer_amount=10000.00,
                retainer_type="Prepaid",
                description="Prepaid hours for ongoing support"
            )
        """
        if effective_date is None:
            effective_date = date.today()

        retainer_data = {
            "contractID": contract_id,
            "retainerAmount": float(retainer_amount),
            "remainingBalance": float(retainer_amount),  # Initially full amount
            "retainerType": retainer_type,
            "effectiveDate": effective_date.isoformat(),
            "status": "Active",
            **kwargs,
        }

        if expiration_date:
            retainer_data["expirationDate"] = expiration_date.isoformat()

        if description:
            retainer_data["description"] = description

        return self.create(retainer_data)

    def get_retainers_by_contract(
        self,
        contract_id: int,
        active_only: bool = True,
        retainer_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get retainers for a specific contract.

        Args:
            contract_id: ID of the contract
            active_only: Whether to return only active retainers
            retainer_type: Filter by retainer type

        Returns:
            List of contract retainers
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if active_only:
            filters.append({"field": "status", "op": "eq", "value": "Active"})

        if retainer_type:
            filters.append(
                {"field": "retainerType", "op": "eq", "value": retainer_type}
            )

        return self.query(filters=filters).items

    def get_expiring_retainers(
        self,
        days_ahead: int = 30,
        contract_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get retainers that are expiring within a specified number of days.

        Args:
            days_ahead: Number of days to look ahead for expiring retainers
            contract_id: Optional filter by specific contract

        Returns:
            List of expiring retainers
        """
        from datetime import timedelta

        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        filters = [
            {"field": "expirationDate", "op": "gte", "value": today.isoformat()},
            {"field": "expirationDate", "op": "lte", "value": future_date.isoformat()},
            {"field": "status", "op": "eq", "value": "Active"},
        ]

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        return self.query(filters=filters).items

    # Business Logic Methods

    def draw_from_retainer(
        self,
        retainer_id: int,
        draw_amount: Union[float, Decimal],
        description: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Draw funds from a retainer.

        Args:
            retainer_id: ID of the retainer
            draw_amount: Amount to draw from the retainer
            description: Description of the draw
            reference_id: Reference to associated transaction/invoice

        Returns:
            Update response with new balance information
        """
        retainer = self.get(retainer_id)
        if not retainer:
            raise ValueError(f"Retainer {retainer_id} not found")

        current_balance = Decimal(str(retainer.get("remainingBalance", 0)))
        draw_amount_decimal = Decimal(str(draw_amount))

        if draw_amount_decimal > current_balance:
            raise ValueError(
                f"Draw amount {draw_amount} exceeds remaining balance {current_balance}"
            )

        new_balance = current_balance - draw_amount_decimal

        update_data = {
            "remainingBalance": float(new_balance),
            "lastDrawDate": date.today().isoformat(),
            "lastDrawAmount": float(draw_amount_decimal),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if description:
            update_data["lastDrawDescription"] = description

        if reference_id:
            update_data["lastDrawReferenceID"] = reference_id

        # Check if retainer is now depleted
        if new_balance <= 0:
            update_data["status"] = "Depleted"
            update_data["depletedDate"] = date.today().isoformat()

        result = self.update_by_id(retainer_id, update_data)

        return {
            "retainer_id": retainer_id,
            "draw_amount": draw_amount_decimal,
            "previous_balance": current_balance,
            "new_balance": new_balance,
            "status": update_data.get("status", "Active"),
            "update_result": result,
        }

    def add_to_retainer(
        self,
        retainer_id: int,
        addition_amount: Union[float, Decimal],
        description: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add funds to an existing retainer.

        Args:
            retainer_id: ID of the retainer
            addition_amount: Amount to add to the retainer
            description: Description of the addition
            reference_id: Reference to associated transaction/payment

        Returns:
            Update response with new balance information
        """
        retainer = self.get(retainer_id)
        if not retainer:
            raise ValueError(f"Retainer {retainer_id} not found")

        current_balance = Decimal(str(retainer.get("remainingBalance", 0)))
        addition_amount_decimal = Decimal(str(addition_amount))
        new_balance = current_balance + addition_amount_decimal

        # Update the total retainer amount as well
        current_total = Decimal(str(retainer.get("retainerAmount", 0)))
        new_total = current_total + addition_amount_decimal

        update_data = {
            "retainerAmount": float(new_total),
            "remainingBalance": float(new_balance),
            "lastAdditionDate": date.today().isoformat(),
            "lastAdditionAmount": float(addition_amount_decimal),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if description:
            update_data["lastAdditionDescription"] = description

        if reference_id:
            update_data["lastAdditionReferenceID"] = reference_id

        # Reactivate if it was depleted
        if retainer.get("status") == "Depleted" and new_balance > 0:
            update_data["status"] = "Active"
            update_data["reactivatedDate"] = date.today().isoformat()

        result = self.update_by_id(retainer_id, update_data)

        return {
            "retainer_id": retainer_id,
            "addition_amount": addition_amount_decimal,
            "previous_balance": current_balance,
            "new_balance": new_balance,
            "previous_total": current_total,
            "new_total": new_total,
            "status": update_data.get("status", retainer.get("status")),
            "update_result": result,
        }

    def get_retainer_balance(
        self,
        retainer_id: int,
    ) -> Dict[str, Any]:
        """
        Get current balance information for a retainer.

        Args:
            retainer_id: ID of the retainer

        Returns:
            Balance information and utilization statistics
        """
        retainer = self.get(retainer_id)
        if not retainer:
            raise ValueError(f"Retainer {retainer_id} not found")

        original_amount = Decimal(str(retainer.get("retainerAmount", 0)))
        remaining_balance = Decimal(str(retainer.get("remainingBalance", 0)))
        utilized_amount = original_amount - remaining_balance

        utilization_percentage = (
            float(utilized_amount / original_amount * 100) if original_amount > 0 else 0
        )

        return {
            "retainer_id": retainer_id,
            "contract_id": retainer.get("contractID"),
            "status": retainer.get("status"),
            "original_amount": original_amount,
            "remaining_balance": remaining_balance,
            "utilized_amount": utilized_amount,
            "utilization_percentage": utilization_percentage,
            "effective_date": retainer.get("effectiveDate"),
            "expiration_date": retainer.get("expirationDate"),
            "last_draw_date": retainer.get("lastDrawDate"),
            "last_draw_amount": retainer.get("lastDrawAmount"),
        }

    def get_contract_retainer_summary(
        self,
        contract_id: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of all retainers for a contract.

        Args:
            contract_id: ID of the contract

        Returns:
            Summary of all retainers for the contract
        """
        retainers = self.get_retainers_by_contract(contract_id, active_only=False)

        total_amount = Decimal("0")
        total_remaining = Decimal("0")
        total_utilized = Decimal("0")
        status_counts = {}
        type_breakdown = {}

        for retainer in retainers:
            amount = Decimal(str(retainer.get("retainerAmount", 0)))
            remaining = Decimal(str(retainer.get("remainingBalance", 0)))
            status = retainer.get("status", "Unknown")
            retainer_type = retainer.get("retainerType", "Unknown")

            total_amount += amount
            total_remaining += remaining
            total_utilized += amount - remaining

            status_counts[status] = status_counts.get(status, 0) + 1

            if retainer_type not in type_breakdown:
                type_breakdown[retainer_type] = {
                    "count": 0,
                    "total_amount": Decimal("0"),
                    "remaining_balance": Decimal("0"),
                }

            type_breakdown[retainer_type]["count"] += 1
            type_breakdown[retainer_type]["total_amount"] += amount
            type_breakdown[retainer_type]["remaining_balance"] += remaining

        overall_utilization = (
            float(total_utilized / total_amount * 100) if total_amount > 0 else 0
        )

        return {
            "contract_id": contract_id,
            "summary": {
                "total_retainers": len(retainers),
                "total_amount": total_amount,
                "total_remaining": total_remaining,
                "total_utilized": total_utilized,
                "overall_utilization_percentage": overall_utilization,
            },
            "status_breakdown": status_counts,
            "type_breakdown": {
                rtype: {
                    "count": data["count"],
                    "total_amount": data["total_amount"],
                    "remaining_balance": data["remaining_balance"],
                    "utilized_amount": data["total_amount"] - data["remaining_balance"],
                }
                for rtype, data in type_breakdown.items()
            },
            "retainers": retainers,
        }

    def create_prepaid_hours_retainer(
        self,
        contract_id: int,
        total_hours: Union[float, Decimal],
        hourly_rate: Union[float, Decimal],
        effective_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a prepaid hours retainer.

        Args:
            contract_id: ID of the contract
            total_hours: Number of prepaid hours
            hourly_rate: Rate per hour
            effective_date: When the retainer becomes effective
            expiration_date: When the hours expire

        Returns:
            Create response for the hours-based retainer
        """
        total_amount = Decimal(str(total_hours)) * Decimal(str(hourly_rate))

        return self.create_retainer(
            contract_id=contract_id,
            retainer_amount=float(total_amount),
            retainer_type="Prepaid Hours",
            effective_date=effective_date,
            expiration_date=expiration_date,
            description=f"{total_hours} prepaid hours at ${hourly_rate}/hour",
            prepaidHours=float(total_hours),
            hourlyRate=float(hourly_rate),
            remainingHours=float(total_hours),
        )

    def draw_prepaid_hours(
        self,
        retainer_id: int,
        hours_used: Union[float, Decimal],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Draw prepaid hours from a hours-based retainer.

        Args:
            retainer_id: ID of the retainer
            hours_used: Number of hours to draw
            description: Description of the hour usage

        Returns:
            Update response with hour and dollar amounts
        """
        retainer = self.get(retainer_id)
        if not retainer:
            raise ValueError(f"Retainer {retainer_id} not found")

        hourly_rate = Decimal(str(retainer.get("hourlyRate", 0)))
        if hourly_rate <= 0:
            raise ValueError("This retainer is not configured for hourly draws")

        hours_used_decimal = Decimal(str(hours_used))
        dollar_amount = hours_used_decimal * hourly_rate

        # Update remaining hours
        remaining_hours = Decimal(str(retainer.get("remainingHours", 0)))
        new_hours_remaining = remaining_hours - hours_used_decimal

        if new_hours_remaining < 0:
            raise ValueError(
                f"Hours used {hours_used} exceeds remaining hours {remaining_hours}"
            )

        # Update the monetary balance as well
        result = self.draw_from_retainer(
            retainer_id=retainer_id,
            draw_amount=float(dollar_amount),
            description=description,
        )

        # Update hours tracking
        self.update_by_id(
            retainer_id,
            {
                "remainingHours": float(new_hours_remaining),
                "lastHoursUsed": float(hours_used_decimal),
            },
        )

        result.update(
            {
                "hours_used": hours_used_decimal,
                "hourly_rate": hourly_rate,
                "previous_hours": remaining_hours,
                "new_hours_remaining": new_hours_remaining,
            }
        )

        return result

    def extend_retainer_expiration(
        self,
        retainer_id: int,
        new_expiration_date: date,
        extension_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extend the expiration date of a retainer.

        Args:
            retainer_id: ID of the retainer
            new_expiration_date: New expiration date
            extension_reason: Reason for the extension

        Returns:
            Update response
        """
        retainer = self.get(retainer_id)
        original_expiration = retainer.get("expirationDate") if retainer else None

        update_data = {
            "expirationDate": new_expiration_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
            "extensionDate": datetime.now().isoformat(),
        }

        if original_expiration:
            update_data["originalExpirationDate"] = original_expiration

        if extension_reason:
            update_data["extensionReason"] = extension_reason

        return self.update_by_id(retainer_id, update_data)

    def get_retainer_utilization_report(
        self,
        contract_ids: Optional[List[int]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Generate a utilization report for retainers.

        Args:
            contract_ids: Optional filter by specific contracts
            date_from: Start date for the report period
            date_to: End date for the report period

        Returns:
            Utilization report with statistics by contract and retainer type
        """
        filters = []

        if contract_ids:
            # This would need to be implemented as multiple queries or an IN filter
            pass

        if date_from:
            filters.append(
                {"field": "effectiveDate", "op": "gte", "value": date_from.isoformat()}
            )
        if date_to:
            filters.append(
                {"field": "effectiveDate", "op": "lte", "value": date_to.isoformat()}
            )

        all_retainers = (
            self.query(filters=filters).items if filters else self.query().items
        )

        contract_summary = {}
        type_summary = {}
        overall_stats = {
            "total_retainers": len(all_retainers),
            "total_amount": Decimal("0"),
            "total_remaining": Decimal("0"),
            "total_utilized": Decimal("0"),
        }

        for retainer in all_retainers:
            contract_id = retainer.get("contractID")
            retainer_type = retainer.get("retainerType", "Unknown")
            amount = Decimal(str(retainer.get("retainerAmount", 0)))
            remaining = Decimal(str(retainer.get("remainingBalance", 0)))
            utilized = amount - remaining

            # Overall statistics
            overall_stats["total_amount"] += amount
            overall_stats["total_remaining"] += remaining
            overall_stats["total_utilized"] += utilized

            # Contract summary
            if contract_id not in contract_summary:
                contract_summary[contract_id] = {
                    "contract_id": contract_id,
                    "retainer_count": 0,
                    "total_amount": Decimal("0"),
                    "remaining_balance": Decimal("0"),
                    "utilized_amount": Decimal("0"),
                }

            contract_summary[contract_id]["retainer_count"] += 1
            contract_summary[contract_id]["total_amount"] += amount
            contract_summary[contract_id]["remaining_balance"] += remaining
            contract_summary[contract_id]["utilized_amount"] += utilized

            # Type summary
            if retainer_type not in type_summary:
                type_summary[retainer_type] = {
                    "retainer_type": retainer_type,
                    "count": 0,
                    "total_amount": Decimal("0"),
                    "remaining_balance": Decimal("0"),
                    "utilized_amount": Decimal("0"),
                }

            type_summary[retainer_type]["count"] += 1
            type_summary[retainer_type]["total_amount"] += amount
            type_summary[retainer_type]["remaining_balance"] += remaining
            type_summary[retainer_type]["utilized_amount"] += utilized

        # Calculate utilization percentages
        if overall_stats["total_amount"] > 0:
            overall_stats["utilization_percentage"] = float(
                overall_stats["total_utilized"] / overall_stats["total_amount"] * 100
            )
        else:
            overall_stats["utilization_percentage"] = 0

        for contract_data in contract_summary.values():
            if contract_data["total_amount"] > 0:
                contract_data["utilization_percentage"] = float(
                    contract_data["utilized_amount"]
                    / contract_data["total_amount"]
                    * 100
                )
            else:
                contract_data["utilization_percentage"] = 0

        for type_data in type_summary.values():
            if type_data["total_amount"] > 0:
                type_data["utilization_percentage"] = float(
                    type_data["utilized_amount"] / type_data["total_amount"] * 100
                )
            else:
                type_data["utilization_percentage"] = 0

        return {
            "report_period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "overall_statistics": overall_stats,
            "by_contract": list(contract_summary.values()),
            "by_retainer_type": list(type_summary.values()),
        }
