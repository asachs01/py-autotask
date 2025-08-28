"""
Ticket Additional Configuration Items entity for Autotask API operations.
"""

from typing import Any, Dict, List

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketAdditionalConfigurationItemsEntity(BaseEntity):
    """
    Handles Ticket Additional Configuration Items operations for the Autotask API.

    Manages additional configuration items (CIs) associated with tickets beyond
    the primary CI, enabling multiple asset involvement in ticket resolution.
    """

    def __init__(self, client, entity_name: str = "TicketAdditionalConfigurationItems"):
        super().__init__(client, entity_name)

    def add_configuration_item_to_ticket(
        self,
        ticket_id: int,
        configuration_item_id: int,
        **kwargs,
    ) -> EntityDict:
        """
        Add an additional configuration item to a ticket.

        Args:
            ticket_id: ID of the ticket
            configuration_item_id: ID of the configuration item to add
            **kwargs: Additional fields

        Returns:
            Created ticket additional configuration item data
        """
        ci_data = {
            "TicketID": ticket_id,
            "ConfigurationItemID": configuration_item_id,
            **kwargs,
        }

        return self.create(ci_data)

    def get_configuration_items_by_ticket(self, ticket_id: int) -> EntityList:
        """
        Get all additional configuration items for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by

        Returns:
            List of additional configuration items for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]
        return self.query_all(filters=filters)

    def get_tickets_by_configuration_item(
        self,
        configuration_item_id: int,
        include_closed: bool = False,
    ) -> EntityList:
        """
        Get all tickets where a configuration item is listed as additional CI.

        Args:
            configuration_item_id: Configuration item ID to filter by
            include_closed: Whether to include closed tickets

        Returns:
            List of ticket additional CI records
        """
        filters = [
            {
                "field": "ConfigurationItemID",
                "op": "eq",
                "value": str(configuration_item_id),
            }
        ]

        results = self.query_all(filters=filters)

        if not include_closed:
            # Note: Filtering by ticket status would require joining with tickets
            # For now, return all and let caller filter by ticket status if needed
            pass

        return results

    def remove_configuration_item_from_ticket(
        self, ticket_id: int, configuration_item_id: int
    ) -> bool:
        """
        Remove an additional configuration item from a ticket.

        Args:
            ticket_id: Ticket ID
            configuration_item_id: Configuration item ID to remove

        Returns:
            True if removal was successful
        """
        # Find the specific association record
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {
                "field": "ConfigurationItemID",
                "op": "eq",
                "value": str(configuration_item_id),
            },
        ]

        associations = self.query(filters=filters)

        if associations.items:
            association_id = associations.items[0]["id"]
            return self.delete(int(association_id))

        return False

    def bulk_add_configuration_items_to_ticket(
        self,
        ticket_id: int,
        configuration_item_ids: List[int],
    ) -> List[EntityDict]:
        """
        Add multiple configuration items to a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            configuration_item_ids: List of configuration item IDs to add

        Returns:
            List of created associations
        """
        results = []

        for ci_id in configuration_item_ids:
            try:
                result = self.add_configuration_item_to_ticket(ticket_id, ci_id)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Failed to add configuration item {ci_id} to ticket {ticket_id}: {e}"
                )

        return results

    def bulk_remove_configuration_items_from_ticket(
        self,
        ticket_id: int,
        configuration_item_ids: List[int],
    ) -> List[bool]:
        """
        Remove multiple configuration items from a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            configuration_item_ids: List of configuration item IDs to remove

        Returns:
            List of success indicators
        """
        results = []

        for ci_id in configuration_item_ids:
            try:
                success = self.remove_configuration_item_from_ticket(ticket_id, ci_id)
                results.append(success)
            except Exception as e:
                self.logger.error(
                    f"Failed to remove configuration item {ci_id} from ticket {ticket_id}: {e}"
                )
                results.append(False)

        return results

    def replace_ticket_configuration_items(
        self,
        ticket_id: int,
        new_configuration_item_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Replace all additional configuration items for a ticket with a new set.

        Args:
            ticket_id: Ticket ID
            new_configuration_item_ids: List of new configuration item IDs

        Returns:
            Dictionary with operation results
        """
        # Get current configuration items
        current_cis = self.get_configuration_items_by_ticket(ticket_id)
        current_ci_ids = [int(ci["ConfigurationItemID"]) for ci in current_cis]

        # Determine CIs to add and remove
        cis_to_add = [
            cid for cid in new_configuration_item_ids if cid not in current_ci_ids
        ]
        cis_to_remove = [
            cid for cid in current_ci_ids if cid not in new_configuration_item_ids
        ]

        results = {
            "added": [],
            "removed": [],
            "errors": [],
        }

        # Add new configuration items
        if cis_to_add:
            add_results = self.bulk_add_configuration_items_to_ticket(
                ticket_id, cis_to_add
            )
            results["added"] = add_results

        # Remove old configuration items
        if cis_to_remove:
            remove_results = self.bulk_remove_configuration_items_from_ticket(
                ticket_id, cis_to_remove
            )
            results["removed"] = remove_results

        return results

    def get_configuration_item_impact_summary(
        self, configuration_item_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get impact summary for a configuration item across all tickets.

        Args:
            configuration_item_id: Configuration item ID
            days: Number of days to look back

        Returns:
            Dictionary with impact summary
        """
        from datetime import datetime, timedelta

        # Get all ticket associations for this CI
        associations = self.get_tickets_by_configuration_item(
            configuration_item_id, include_closed=True
        )

        # Calculate statistics
        cutoff_date = datetime.now() - timedelta(days=days)

        summary = {
            "total_tickets": len(associations),
            "recent_activity_count": 0,
            "ticket_ids": [int(a["TicketID"]) for a in associations],
            "configuration_item_id": configuration_item_id,
            "summary_period_days": days,
        }

        # Count recent associations (would need CreateDateTime field)
        for assoc in associations:
            if "CreateDateTime" in assoc:
                create_date = datetime.fromisoformat(
                    assoc["CreateDateTime"].replace("Z", "+00:00")
                )
                if create_date >= cutoff_date:
                    summary["recent_activity_count"] += 1

        return summary

    def validate_configuration_item_ticket_association(
        self, ticket_id: int, configuration_item_id: int
    ) -> Dict[str, Any]:
        """
        Validate if a configuration item can be associated with a ticket.

        Args:
            ticket_id: Ticket ID
            configuration_item_id: Configuration item ID

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "reasons": [],
            "warnings": [],
        }

        # Check if association already exists
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {
                "field": "ConfigurationItemID",
                "op": "eq",
                "value": str(configuration_item_id),
            },
        ]

        existing = self.query(filters=filters)
        if existing.items:
            result["warnings"].append(
                "Configuration item is already associated with this ticket"
            )

        # Additional validation logic could be added here
        # - Check if CI belongs to the same account as the ticket
        # - Check if CI is active/installed
        # - Check CI type compatibility

        return result

    def get_ticket_asset_dependencies(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get all asset dependencies for a ticket including additional CIs.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with asset dependency information
        """
        additional_cis = self.get_configuration_items_by_ticket(ticket_id)

        dependency_info = {
            "ticket_id": ticket_id,
            "additional_configuration_items": additional_cis,
            "total_additional_cis": len(additional_cis),
            "configuration_item_ids": [
                int(ci["ConfigurationItemID"]) for ci in additional_cis
            ],
        }

        return dependency_info
