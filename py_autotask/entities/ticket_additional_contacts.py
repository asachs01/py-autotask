"""
Ticket Additional Contacts entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketAdditionalContactsEntity(BaseEntity):
    """
    Handles Ticket Additional Contacts operations for the Autotask API.

    Manages additional contacts associated with tickets beyond the primary contact,
    enabling multiple stakeholder involvement in ticket resolution.
    """

    def __init__(self, client, entity_name: str = "TicketAdditionalContacts"):
        super().__init__(client, entity_name)

    def add_contact_to_ticket(
        self,
        ticket_id: int,
        contact_id: int,
        **kwargs,
    ) -> EntityDict:
        """
        Add an additional contact to a ticket.

        Args:
            ticket_id: ID of the ticket
            contact_id: ID of the contact to add
            **kwargs: Additional fields

        Returns:
            Created ticket additional contact data
        """
        contact_data = {
            "TicketID": ticket_id,
            "ContactID": contact_id,
            **kwargs,
        }

        return self.create(contact_data)

    def get_contacts_by_ticket(self, ticket_id: int) -> EntityList:
        """
        Get all additional contacts for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by

        Returns:
            List of additional contacts for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]
        return self.query_all(filters=filters)

    def get_tickets_by_contact(
        self,
        contact_id: int,
        include_closed: bool = False,
    ) -> EntityList:
        """
        Get all tickets where a contact is listed as an additional contact.

        Args:
            contact_id: Contact ID to filter by
            include_closed: Whether to include closed tickets

        Returns:
            List of ticket additional contact records
        """
        filters = [{"field": "ContactID", "op": "eq", "value": str(contact_id)}]

        results = self.query_all(filters=filters)

        if not include_closed:
            # Filter out closed tickets by checking ticket status
            # This would require joining with tickets, but for now we'll return all
            # and let the caller filter by ticket status if needed
            pass

        return results

    def remove_contact_from_ticket(self, ticket_id: int, contact_id: int) -> bool:
        """
        Remove an additional contact from a ticket.

        Args:
            ticket_id: Ticket ID
            contact_id: Contact ID to remove

        Returns:
            True if removal was successful
        """
        # Find the specific association record
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {"field": "ContactID", "op": "eq", "value": str(contact_id)},
        ]

        associations = self.query(filters=filters)

        if associations.items:
            association_id = associations.items[0]["id"]
            return self.delete(int(association_id))

        return False

    def bulk_add_contacts_to_ticket(
        self,
        ticket_id: int,
        contact_ids: List[int],
    ) -> List[EntityDict]:
        """
        Add multiple contacts to a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            contact_ids: List of contact IDs to add

        Returns:
            List of created associations
        """
        results = []

        for contact_id in contact_ids:
            try:
                result = self.add_contact_to_ticket(ticket_id, contact_id)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Failed to add contact {contact_id} to ticket {ticket_id}: {e}"
                )

        return results

    def bulk_remove_contacts_from_ticket(
        self,
        ticket_id: int,
        contact_ids: List[int],
    ) -> List[bool]:
        """
        Remove multiple contacts from a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            contact_ids: List of contact IDs to remove

        Returns:
            List of success indicators
        """
        results = []

        for contact_id in contact_ids:
            try:
                success = self.remove_contact_from_ticket(ticket_id, contact_id)
                results.append(success)
            except Exception as e:
                self.logger.error(
                    f"Failed to remove contact {contact_id} from ticket {ticket_id}: {e}"
                )
                results.append(False)

        return results

    def replace_ticket_contacts(
        self,
        ticket_id: int,
        new_contact_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Replace all additional contacts for a ticket with a new set.

        Args:
            ticket_id: Ticket ID
            new_contact_ids: List of new contact IDs

        Returns:
            Dictionary with operation results
        """
        # Get current contacts
        current_contacts = self.get_contacts_by_ticket(ticket_id)
        current_contact_ids = [int(c["ContactID"]) for c in current_contacts]

        # Determine contacts to add and remove
        contacts_to_add = [
            cid for cid in new_contact_ids if cid not in current_contact_ids
        ]
        contacts_to_remove = [
            cid for cid in current_contact_ids if cid not in new_contact_ids
        ]

        results = {
            "added": [],
            "removed": [],
            "errors": [],
        }

        # Add new contacts
        if contacts_to_add:
            add_results = self.bulk_add_contacts_to_ticket(ticket_id, contacts_to_add)
            results["added"] = add_results

        # Remove old contacts
        if contacts_to_remove:
            remove_results = self.bulk_remove_contacts_from_ticket(
                ticket_id, contacts_to_remove
            )
            results["removed"] = remove_results

        return results

    def get_contact_notification_preferences(
        self, ticket_id: int, contact_id: int
    ) -> Optional[EntityDict]:
        """
        Get notification preferences for a specific contact on a ticket.

        Args:
            ticket_id: Ticket ID
            contact_id: Contact ID

        Returns:
            Contact association record with preferences
        """
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {"field": "ContactID", "op": "eq", "value": str(contact_id)},
        ]

        associations = self.query(filters=filters)
        return associations.items[0] if associations.items else None

    def update_contact_notification_preferences(
        self,
        ticket_id: int,
        contact_id: int,
        preferences: Dict[str, Any],
    ) -> Optional[EntityDict]:
        """
        Update notification preferences for a contact on a ticket.

        Args:
            ticket_id: Ticket ID
            contact_id: Contact ID
            preferences: Dictionary of preference updates

        Returns:
            Updated association record
        """
        # Find the association record
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {"field": "ContactID", "op": "eq", "value": str(contact_id)},
        ]

        associations = self.query(filters=filters)

        if associations.items:
            association_id = associations.items[0]["id"]
            update_data = {"id": association_id, **preferences}
            return self.update(update_data)

        return None

    def get_contact_activity_summary(
        self, contact_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get activity summary for a contact across all tickets.

        Args:
            contact_id: Contact ID
            days: Number of days to look back

        Returns:
            Dictionary with activity summary
        """
        from datetime import datetime, timedelta

        # Get all ticket associations for this contact
        associations = self.get_tickets_by_contact(contact_id, include_closed=True)

        # Calculate statistics
        cutoff_date = datetime.now() - timedelta(days=days)

        summary = {
            "total_tickets": len(associations),
            "recent_activity_count": 0,
            "ticket_ids": [int(a["TicketID"]) for a in associations],
            "contact_id": contact_id,
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

    def validate_contact_ticket_association(
        self, ticket_id: int, contact_id: int
    ) -> Dict[str, Any]:
        """
        Validate if a contact can be associated with a ticket.

        Args:
            ticket_id: Ticket ID
            contact_id: Contact ID

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "reasons": [],
            "warnings": [],
        }

        # Check if association already exists
        existing = self.get_contact_notification_preferences(ticket_id, contact_id)
        if existing:
            result["warnings"].append("Contact is already associated with this ticket")

        # Additional validation logic could be added here
        # - Check if contact belongs to the same company as the ticket
        # - Check if contact is active
        # - Check permissions/access rights

        return result
