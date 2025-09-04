"""
Ticket Costs entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketCostsEntity(BaseEntity):
    """
    Handles Ticket Costs operations for the Autotask API.

    Manages costs associated with tickets including materials, labor,
    travel expenses, and other billable/non-billable costs for accurate
    project tracking and client billing.
    """

    def __init__(self, client, entity_name: str = "TicketCosts"):
        super().__init__(client, entity_name)

    def create_ticket_cost(
        self,
        ticket_id: int,
        name: str,
        cost_type: str,
        unit_cost: float,
        unit_quantity: float = 1.0,
        billable: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new cost entry for a ticket.

        Args:
            ticket_id: ID of the ticket
            name: Description/name of the cost
            cost_type: Type of cost (Material, Labor, Travel, etc.)
            unit_cost: Cost per unit
            unit_quantity: Quantity of units
            billable: Whether this cost is billable to client
            **kwargs: Additional fields

        Returns:
            Created ticket cost data
        """
        cost_data = {
            "TicketID": ticket_id,
            "Name": name,
            "CostType": cost_type,
            "UnitCost": unit_cost,
            "UnitQuantity": unit_quantity,
            "ExtendedCost": unit_cost * unit_quantity,
            "Billable": billable,
            **kwargs,
        }

        return self.create(cost_data)

    def get_costs_by_ticket(
        self,
        ticket_id: int,
        billable_only: bool = False,
        cost_type: Optional[str] = None,
    ) -> EntityList:
        """
        Get all costs for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            billable_only: Return only billable costs
            cost_type: Optional filter by cost type

        Returns:
            List of costs for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]

        if billable_only:
            filters.append({"field": "Billable", "op": "eq", "value": True})

        if cost_type:
            filters.append({"field": "CostType", "op": "eq", "value": cost_type})

        return self.query_all(filters=filters)

    def update_cost_entry(
        self,
        cost_id: int,
        updates: Dict[str, Any],
        recalculate_extended: bool = True,
    ) -> Optional[EntityDict]:
        """
        Update a cost entry.

        Args:
            cost_id: Cost entry ID
            updates: Dictionary of field updates
            recalculate_extended: Whether to recalculate extended cost

        Returns:
            Updated cost record or None if failed
        """
        update_data = {"id": cost_id, **updates}

        # Recalculate extended cost if unit cost or quantity changed
        if recalculate_extended:
            if "UnitCost" in updates or "UnitQuantity" in updates:
                # Get current record to calculate extended cost
                current_record = self.get(cost_id)
                if current_record:
                    unit_cost = updates.get(
                        "UnitCost", current_record.get("UnitCost", 0)
                    )
                    unit_quantity = updates.get(
                        "UnitQuantity", current_record.get("UnitQuantity", 0)
                    )
                    update_data["ExtendedCost"] = float(unit_cost) * float(
                        unit_quantity
                    )

        return self.update(update_data)

    def delete_cost_entry(self, cost_id: int) -> bool:
        """
        Delete a cost entry.

        Args:
            cost_id: Cost entry ID

        Returns:
            True if deletion was successful
        """
        return self.delete(cost_id)

    def get_ticket_cost_summary(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get comprehensive cost summary for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with cost summary statistics
        """
        costs = self.get_costs_by_ticket(ticket_id)

        summary = {
            "ticket_id": ticket_id,
            "total_entries": len(costs),
            "total_cost": 0.0,
            "billable_cost": 0.0,
            "non_billable_cost": 0.0,
            "cost_by_type": {},
            "cost_entries": costs,
        }

        for cost in costs:
            extended_cost = float(cost.get("ExtendedCost", 0))
            is_billable = cost.get("Billable", False)
            cost_type = cost.get("CostType", "Unknown")

            summary["total_cost"] += extended_cost

            if is_billable:
                summary["billable_cost"] += extended_cost
            else:
                summary["non_billable_cost"] += extended_cost

            # Group by cost type
            if cost_type not in summary["cost_by_type"]:
                summary["cost_by_type"][cost_type] = {
                    "total": 0.0,
                    "billable": 0.0,
                    "non_billable": 0.0,
                    "count": 0,
                }

            summary["cost_by_type"][cost_type]["total"] += extended_cost
            summary["cost_by_type"][cost_type]["count"] += 1

            if is_billable:
                summary["cost_by_type"][cost_type]["billable"] += extended_cost
            else:
                summary["cost_by_type"][cost_type]["non_billable"] += extended_cost

        # Calculate profit margin
        if summary["total_cost"] > 0:
            summary["profit_margin_percentage"] = round(
                (summary["billable_cost"] - summary["total_cost"])
                / summary["total_cost"]
                * 100,
                2,
            )
        else:
            summary["profit_margin_percentage"] = 0.0

        return summary

    def bulk_create_costs(
        self,
        ticket_id: int,
        cost_entries: List[Dict[str, Any]],
    ) -> List[EntityDict]:
        """
        Create multiple cost entries for a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            cost_entries: List of cost entry dictionaries

        Returns:
            List of created cost records
        """
        results = []

        for cost_entry in cost_entries:
            try:
                cost = self.create_ticket_cost(
                    ticket_id=ticket_id,
                    name=cost_entry["name"],
                    cost_type=cost_entry["cost_type"],
                    unit_cost=cost_entry["unit_cost"],
                    unit_quantity=cost_entry.get("unit_quantity", 1.0),
                    billable=cost_entry.get("billable", True),
                    **{
                        k: v
                        for k, v in cost_entry.items()
                        if k
                        not in [
                            "name",
                            "cost_type",
                            "unit_cost",
                            "unit_quantity",
                            "billable",
                        ]
                    },
                )
                results.append(cost)
            except Exception as e:
                self.logger.error(
                    f"Failed to create cost entry '{cost_entry.get('name')}' "
                    f"for ticket {ticket_id}: {e}"
                )

        return results

    def apply_discount_to_costs(
        self,
        ticket_id: int,
        discount_percentage: float,
        cost_types: Optional[List[str]] = None,
        billable_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Apply a discount percentage to ticket costs.

        Args:
            ticket_id: Ticket ID
            discount_percentage: Discount percentage (0-100)
            cost_types: Optional list of cost types to apply discount to
            billable_only: Only apply discount to billable costs

        Returns:
            Dictionary with discount application results
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]

        if billable_only:
            filters.append({"field": "Billable", "op": "eq", "value": True})

        costs = self.query_all(filters=filters)

        if cost_types:
            costs = [cost for cost in costs if cost.get("CostType") in cost_types]

        discount_multiplier = 1.0 - (discount_percentage / 100.0)
        updated_costs = []
        total_discount_amount = 0.0

        for cost in costs:
            original_cost = float(cost.get("UnitCost", 0))
            discounted_cost = original_cost * discount_multiplier
            discount_amount = original_cost - discounted_cost

            try:
                updated_cost = self.update_cost_entry(
                    int(cost["id"]),
                    {"UnitCost": discounted_cost},
                )
                if updated_cost:
                    updated_costs.append(updated_cost)
                    total_discount_amount += discount_amount * float(
                        cost.get("UnitQuantity", 1)
                    )
            except Exception as e:
                self.logger.error(f"Failed to apply discount to cost {cost['id']}: {e}")

        return {
            "ticket_id": ticket_id,
            "discount_percentage": discount_percentage,
            "costs_updated": len(updated_costs),
            "total_discount_amount": round(total_discount_amount, 2),
            "updated_cost_ids": [int(cost["id"]) for cost in updated_costs],
        }

    def get_costs_by_date_range(
        self,
        start_date: str,
        end_date: str,
        account_id: Optional[int] = None,
        billable_only: bool = False,
    ) -> EntityList:
        """
        Get costs within a specific date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            account_id: Optional account ID filter
            billable_only: Only return billable costs

        Returns:
            List of costs within the date range
        """
        filters = [
            {"field": "CreateDateTime", "op": "gte", "value": start_date},
            {"field": "CreateDateTime", "op": "lte", "value": end_date},
        ]

        if billable_only:
            filters.append({"field": "Billable", "op": "eq", "value": True})

        # Note: account_id filter would require joining with tickets table
        # For now, we'll get all costs and filter later if needed

        return self.query_all(filters=filters)

    def convert_cost_to_billable(
        self,
        cost_id: int,
        markup_percentage: float = 0.0,
        billing_notes: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Convert a non-billable cost to billable with optional markup.

        Args:
            cost_id: Cost entry ID
            markup_percentage: Markup percentage to apply (0-100)
            billing_notes: Optional notes for billing

        Returns:
            Updated cost record or None if failed
        """
        cost = self.get(cost_id)
        if not cost:
            return None

        if cost.get("Billable"):
            self.logger.warning(f"Cost {cost_id} is already billable")
            return cost

        updates = {"Billable": True}

        if markup_percentage > 0:
            original_unit_cost = float(cost.get("UnitCost", 0))
            marked_up_cost = original_unit_cost * (1 + markup_percentage / 100.0)
            updates["UnitCost"] = marked_up_cost

        if billing_notes:
            updates["BillingNotes"] = billing_notes

        return self.update_cost_entry(cost_id, updates)

    def get_cost_analysis_by_resource(
        self,
        resource_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get cost analysis for tickets handled by a specific resource.

        Args:
            resource_id: Resource ID
            days: Number of days to analyze

        Returns:
            Dictionary with cost analysis by resource
        """
        # Note: This would require joining with tickets to filter by resource
        # For now, we'll return a placeholder structure

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        analysis = {
            "resource_id": resource_id,
            "analysis_period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_tickets_with_costs": 0,
            "total_cost_entries": 0,
            "total_cost_amount": 0.0,
            "billable_cost_amount": 0.0,
            "non_billable_cost_amount": 0.0,
            "cost_by_type": {},
            "avg_cost_per_ticket": 0.0,
        }

        # This would need actual implementation to query tickets by resource
        # and then get associated costs

        return analysis

    def estimate_ticket_profitability(
        self,
        ticket_id: int,
        estimated_billable_hours: float,
        hourly_rate: float,
    ) -> Dict[str, Any]:
        """
        Estimate ticket profitability based on costs and billing.

        Args:
            ticket_id: Ticket ID
            estimated_billable_hours: Estimated billable hours
            hourly_rate: Hourly billing rate

        Returns:
            Dictionary with profitability analysis
        """
        cost_summary = self.get_ticket_cost_summary(ticket_id)

        estimated_labor_revenue = estimated_billable_hours * hourly_rate
        total_estimated_revenue = (
            estimated_labor_revenue + cost_summary["billable_cost"]
        )
        total_costs = cost_summary["total_cost"]

        estimated_profit = total_estimated_revenue - total_costs
        profit_margin = (
            (estimated_profit / total_estimated_revenue * 100)
            if total_estimated_revenue > 0
            else 0
        )

        return {
            "ticket_id": ticket_id,
            "estimated_labor_revenue": round(estimated_labor_revenue, 2),
            "billable_costs": round(cost_summary["billable_cost"], 2),
            "total_estimated_revenue": round(total_estimated_revenue, 2),
            "total_costs": round(total_costs, 2),
            "non_billable_costs": round(cost_summary["non_billable_cost"], 2),
            "estimated_profit": round(estimated_profit, 2),
            "profit_margin_percentage": round(profit_margin, 2),
            "cost_breakdown": cost_summary["cost_by_type"],
            "profitability_rating": (
                "High"
                if profit_margin > 25
                else (
                    "Medium"
                    if profit_margin > 10
                    else "Low" if profit_margin > 0 else "Loss"
                )
            ),
        }

    def copy_costs_to_ticket(
        self,
        source_ticket_id: int,
        target_ticket_id: int,
        cost_types: Optional[List[str]] = None,
        apply_multiplier: float = 1.0,
    ) -> List[EntityDict]:
        """
        Copy costs from one ticket to another.

        Args:
            source_ticket_id: Source ticket ID
            target_ticket_id: Target ticket ID
            cost_types: Optional list of cost types to copy
            apply_multiplier: Multiplier to apply to costs (default 1.0)

        Returns:
            List of created cost entries in target ticket
        """
        source_costs = self.get_costs_by_ticket(source_ticket_id)

        if cost_types:
            source_costs = [
                cost for cost in source_costs if cost.get("CostType") in cost_types
            ]

        new_costs = []

        for cost in source_costs:
            new_cost_data = {
                "name": cost.get("Name"),
                "cost_type": cost.get("CostType"),
                "unit_cost": float(cost.get("UnitCost", 0)) * apply_multiplier,
                "unit_quantity": float(cost.get("UnitQuantity", 1)),
                "billable": cost.get("Billable", True),
            }

            # Copy additional fields
            for field in ["Description", "InternalNotes", "BillingNotes"]:
                if field in cost:
                    new_cost_data[field.lower()] = cost[field]

            try:
                new_cost = self.create_ticket_cost(target_ticket_id, **new_cost_data)
                new_costs.append(new_cost)
            except Exception as e:
                self.logger.error(
                    f"Failed to copy cost '{cost.get('Name')}' "
                    f"from ticket {source_ticket_id} to {target_ticket_id}: {e}"
                )

        return new_costs
