"""
ContactGroupContacts entity for Autotask API operations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ContactGroupContactsEntity(BaseEntity):
    """
    Handles all ContactGroupContacts-related operations for the Autotask API.

    ContactGroupContacts represent the many-to-many relationships between
    contact groups and individual contacts, managing group memberships.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def add_contact_to_group(
        self,
        contact_group_id: int,
        contact_id: int,
        is_active: bool = True,
        date_added: Optional[date] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Add a contact to a contact group.

        Args:
            contact_group_id: ID of the contact group
            contact_id: ID of the contact to add
            is_active: Whether the membership is active
            date_added: Date when contact was added to group
            **kwargs: Additional membership properties

        Returns:
            Created contact group membership data
        """
        membership_data = {
            "ContactGroupID": contact_group_id,
            "ContactID": contact_id,
            "IsActive": is_active,
            **kwargs,
        }

        if date_added:
            membership_data["DateAdded"] = date_added.isoformat()

        return self.create(membership_data)

    def get_contacts_by_group(
        self,
        contact_group_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all contacts in a specific contact group.

        Args:
            contact_group_id: ID of the contact group
            active_only: Whether to return only active memberships
            limit: Maximum number of contacts to return

        Returns:
            List of contacts in the group
        """
        filters = [QueryFilter(field="ContactGroupID", op="eq", value=contact_group_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_groups_by_contact(
        self, contact_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all contact groups that a contact belongs to.

        Args:
            contact_id: ID of the contact
            active_only: Whether to return only active memberships
            limit: Maximum number of groups to return

        Returns:
            List of contact groups the contact belongs to
        """
        filters = [QueryFilter(field="ContactID", op="eq", value=contact_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def remove_contact_from_group(
        self, contact_group_id: int, contact_id: int, soft_delete: bool = True
    ) -> bool:
        """
        Remove a contact from a contact group.

        Args:
            contact_group_id: ID of the contact group
            contact_id: ID of the contact to remove
            soft_delete: Whether to deactivate (True) or hard delete (False)

        Returns:
            True if successful
        """
        # Find the membership record
        filters = [
            QueryFilter(field="ContactGroupID", op="eq", value=contact_group_id),
            QueryFilter(field="ContactID", op="eq", value=contact_id),
        ]

        response = self.query(filters=filters, max_records=1)
        memberships = response.items if hasattr(response, "items") else response

        if memberships:
            membership = memberships[0]
            membership_id = membership.get("id")

            if soft_delete:
                # Deactivate the membership
                self.update_by_id(membership_id, {"IsActive": False})
            else:
                # Hard delete the membership
                self.delete(membership_id)

            return True

        return False

    def activate_membership(
        self, contact_group_id: int, contact_id: int
    ) -> Optional[EntityDict]:
        """
        Activate a contact's membership in a group.

        Args:
            contact_group_id: ID of the contact group
            contact_id: ID of the contact

        Returns:
            Updated membership data or None if not found
        """
        filters = [
            QueryFilter(field="ContactGroupID", op="eq", value=contact_group_id),
            QueryFilter(field="ContactID", op="eq", value=contact_id),
        ]

        response = self.query(filters=filters, max_records=1)
        memberships = response.items if hasattr(response, "items") else response

        if memberships:
            membership = memberships[0]
            membership_id = membership.get("id")
            return self.update_by_id(membership_id, {"IsActive": True})

        return None

    def bulk_add_contacts_to_group(
        self, contact_group_id: int, contact_ids: List[int]
    ) -> List[EntityDict]:
        """
        Add multiple contacts to a group in batch.

        Args:
            contact_group_id: ID of the contact group
            contact_ids: List of contact IDs to add

        Returns:
            List of created membership responses
        """
        memberships_data = []
        for contact_id in contact_ids:
            membership = {
                "ContactGroupID": contact_group_id,
                "ContactID": contact_id,
                "IsActive": True,
                "DateAdded": date.today().isoformat(),
            }
            memberships_data.append(membership)

        return self.batch_create(memberships_data)

    def bulk_remove_contacts_from_group(
        self, contact_group_id: int, contact_ids: List[int], soft_delete: bool = True
    ) -> List[bool]:
        """
        Remove multiple contacts from a group in batch.

        Args:
            contact_group_id: ID of the contact group
            contact_ids: List of contact IDs to remove
            soft_delete: Whether to deactivate or hard delete

        Returns:
            List of success indicators
        """
        results = []
        for contact_id in contact_ids:
            success = self.remove_contact_from_group(
                contact_group_id, contact_id, soft_delete
            )
            results.append(success)

        return results

    def get_group_membership_statistics(self, contact_group_id: int) -> Dict[str, Any]:
        """
        Get membership statistics for a contact group.

        Args:
            contact_group_id: ID of the contact group

        Returns:
            Dictionary containing membership statistics
        """
        all_memberships = self.get_contacts_by_group(
            contact_group_id, active_only=False
        )
        active_memberships = [m for m in all_memberships if m.get("IsActive", False)]

        return {
            "group_id": contact_group_id,
            "total_memberships": len(all_memberships),
            "active_memberships": len(active_memberships),
            "inactive_memberships": len(all_memberships) - len(active_memberships),
            "activation_rate": (len(active_memberships) / max(1, len(all_memberships)))
            * 100,
            "recent_additions": (
                len(
                    [
                        m
                        for m in all_memberships
                        if m.get("DateAdded")
                        and datetime.fromisoformat(m["DateAdded"]).date()
                        >= (date.today() - datetime.timedelta(days=30))
                    ]
                )
                if all_memberships
                else 0
            ),
        }

    def get_contact_membership_summary(self, contact_id: int) -> Dict[str, Any]:
        """
        Get a summary of group memberships for a contact.

        Args:
            contact_id: ID of the contact

        Returns:
            Dictionary containing contact's group membership summary
        """
        all_memberships = self.get_groups_by_contact(contact_id, active_only=False)
        active_memberships = [m for m in all_memberships if m.get("IsActive", False)]

        return {
            "contact_id": contact_id,
            "total_groups": len(all_memberships),
            "active_groups": len(active_memberships),
            "inactive_groups": len(all_memberships) - len(active_memberships),
            "group_details": [
                {
                    "group_id": membership.get("ContactGroupID"),
                    "is_active": membership.get("IsActive", False),
                    "date_added": membership.get("DateAdded"),
                }
                for membership in all_memberships
            ],
        }

    def find_duplicate_memberships(self) -> List[Dict[str, Any]]:
        """
        Find duplicate memberships (same contact in same group multiple times).

        Returns:
            List of duplicate membership information
        """
        all_memberships = self.query_all()

        # Group by contact_id and contact_group_id
        membership_groups = {}
        for membership in all_memberships:
            key = (membership.get("ContactID"), membership.get("ContactGroupID"))
            if key not in membership_groups:
                membership_groups[key] = []
            membership_groups[key].append(membership)

        duplicates = []
        for (contact_id, group_id), memberships in membership_groups.items():
            if len(memberships) > 1:
                duplicates.append(
                    {
                        "contact_id": contact_id,
                        "contact_group_id": group_id,
                        "duplicate_count": len(memberships),
                        "membership_ids": [m.get("id") for m in memberships],
                        "active_duplicates": [
                            m for m in memberships if m.get("IsActive", False)
                        ],
                    }
                )

        return duplicates

    def transfer_contact_memberships(
        self,
        old_contact_id: int,
        new_contact_id: int,
        group_ids: Optional[List[int]] = None,
    ) -> List[EntityDict]:
        """
        Transfer group memberships from one contact to another.

        Args:
            old_contact_id: ID of the old contact
            new_contact_id: ID of the new contact
            group_ids: Optional list of specific group IDs to transfer

        Returns:
            List of updated/created membership data
        """
        old_memberships = self.get_groups_by_contact(old_contact_id)

        if group_ids:
            old_memberships = [
                m for m in old_memberships if m.get("ContactGroupID") in group_ids
            ]

        transferred = []
        for membership in old_memberships:
            group_id = membership.get("ContactGroupID")

            # Deactivate old membership
            if membership.get("id"):
                self.update_by_id(membership["id"], {"IsActive": False})

            # Create new membership
            new_membership = self.add_contact_to_group(
                contact_group_id=group_id, contact_id=new_contact_id, is_active=True
            )
            transferred.append(new_membership)

        return transferred

    def sync_group_memberships(
        self, contact_group_id: int, target_contact_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Synchronize group memberships to match a target list of contacts.

        Args:
            contact_group_id: ID of the contact group
            target_contact_ids: List of contact IDs that should be in the group

        Returns:
            Dictionary containing sync results
        """
        current_memberships = self.get_contacts_by_group(
            contact_group_id, active_only=True
        )
        current_contact_ids = [m.get("ContactID") for m in current_memberships]

        # Contacts to add
        contacts_to_add = set(target_contact_ids) - set(current_contact_ids)

        # Contacts to remove
        contacts_to_remove = set(current_contact_ids) - set(target_contact_ids)

        sync_results = {
            "group_id": contact_group_id,
            "contacts_added": 0,
            "contacts_removed": 0,
            "contacts_unchanged": len(
                set(target_contact_ids) & set(current_contact_ids)
            ),
            "add_results": [],
            "remove_results": [],
        }

        # Add new contacts
        if contacts_to_add:
            add_results = self.bulk_add_contacts_to_group(
                contact_group_id, list(contacts_to_add)
            )
            sync_results["add_results"] = add_results
            sync_results["contacts_added"] = len(add_results)

        # Remove contacts
        if contacts_to_remove:
            remove_results = self.bulk_remove_contacts_from_group(
                contact_group_id, list(contacts_to_remove)
            )
            sync_results["remove_results"] = remove_results
            sync_results["contacts_removed"] = sum(remove_results)

        return sync_results

    def get_group_overlap_analysis(self, group_ids: List[int]) -> Dict[str, Any]:
        """
        Analyze membership overlap between multiple contact groups.

        Args:
            group_ids: List of contact group IDs to analyze

        Returns:
            Dictionary containing overlap analysis
        """
        group_memberships = {}
        all_contacts = set()

        # Get memberships for each group
        for group_id in group_ids:
            memberships = self.get_contacts_by_group(group_id, active_only=True)
            contact_ids = [m.get("ContactID") for m in memberships]
            group_memberships[group_id] = set(contact_ids)
            all_contacts.update(contact_ids)

        # Calculate overlaps
        overlap_analysis = {
            "total_groups": len(group_ids),
            "total_unique_contacts": len(all_contacts),
            "group_sizes": {
                group_id: len(contacts)
                for group_id, contacts in group_memberships.items()
            },
            "pairwise_overlaps": {},
            "contacts_in_multiple_groups": [],
            "exclusive_contacts": {},
        }

        # Pairwise overlaps
        for i, group_id1 in enumerate(group_ids):
            for group_id2 in group_ids[i + 1 :]:
                overlap = group_memberships[group_id1] & group_memberships[group_id2]
                overlap_analysis["pairwise_overlaps"][f"{group_id1}-{group_id2}"] = {
                    "overlap_size": len(overlap),
                    "overlap_contacts": list(overlap),
                }

        # Contacts in multiple groups
        for contact_id in all_contacts:
            group_count = sum(
                1 for contacts in group_memberships.values() if contact_id in contacts
            )
            if group_count > 1:
                overlap_analysis["contacts_in_multiple_groups"].append(
                    {
                        "contact_id": contact_id,
                        "group_count": group_count,
                        "groups": [
                            group_id
                            for group_id, contacts in group_memberships.items()
                            if contact_id in contacts
                        ],
                    }
                )

        # Exclusive contacts per group
        for group_id, contacts in group_memberships.items():
            other_contacts = set()
            for other_id, other_contacts_set in group_memberships.items():
                if other_id != group_id:
                    other_contacts.update(other_contacts_set)

            exclusive = contacts - other_contacts
            overlap_analysis["exclusive_contacts"][group_id] = list(exclusive)

        return overlap_analysis
