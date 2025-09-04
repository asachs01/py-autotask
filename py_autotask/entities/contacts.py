"""
Contacts entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import ContactData, QueryFilter
from .base import BaseEntity


class ContactsEntity(BaseEntity):
    """
    Handles all Contact-related operations for the Autotask API.

    Contacts in Autotask represent individuals associated with companies
    who can submit tickets, receive notifications, etc.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_contact(
        self,
        first_name: str,
        last_name: str,
        company_id: int,
        email_address: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
        active: bool = True,
        **kwargs,
    ) -> ContactData:
        """
        Create a new contact with required and optional fields.

        Args:
            first_name: Contact's first name
            last_name: Contact's last name
            company_id: ID of the associated company
            email_address: Contact's email address
            phone: Contact's phone number
            title: Contact's job title
            active: Whether the contact is active
            **kwargs: Additional contact fields

        Returns:
            Created contact data
        """
        contact_data = {
            "FirstName": first_name,
            "LastName": last_name,
            "CompanyID": company_id,
            "Active": active,
            **kwargs,
        }

        # Add optional fields if provided
        if email_address:
            contact_data["EMailAddress"] = email_address
        if phone:
            contact_data["Phone"] = phone
        if title:
            contact_data["Title"] = title

        return self.create(contact_data)

    def search_contacts_by_name(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        exact_match: bool = False,
        limit: Optional[int] = None,
    ) -> List[ContactData]:
        """
        Search for contacts by name.

        Args:
            first_name: First name to search for
            last_name: Last name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of contacts to return

        Returns:
            List of matching contacts
        """
        filters = []

        if first_name:
            op = "eq" if exact_match else "contains"
            filters.append(QueryFilter(field="FirstName", op=op, value=first_name))

        if last_name:
            op = "eq" if exact_match else "contains"
            filters.append(QueryFilter(field="LastName", op=op, value=last_name))

        if not filters:
            raise ValueError("At least one name field must be provided")

        return self.query(filters=filters, max_records=limit)

    def search_contacts_by_email(
        self, email: str, exact_match: bool = True, limit: Optional[int] = None
    ) -> List[ContactData]:
        """
        Search for contacts by email address.

        Args:
            email: Email address to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of contacts to return

        Returns:
            List of matching contacts
        """
        op = "eq" if exact_match else "contains"
        filters = [QueryFilter(field="EMailAddress", op=op, value=email)]

        return self.query(filters=filters, max_records=limit)

    def get_contacts_by_company(
        self, company_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[ContactData]:
        """
        Get all contacts for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active contacts
            limit: Maximum number of contacts to return

        Returns:
            List of contacts for the company
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_primary_contacts(
        self, company_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[ContactData]:
        """
        Get contacts marked as primary contacts.

        Args:
            company_id: Optional company ID filter
            limit: Maximum number of contacts to return

        Returns:
            List of primary contacts
        """
        filters = [QueryFilter(field="PrimaryContact", op="eq", value=True)]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        return self.query(filters=filters, max_records=limit)

    def get_contact_tickets(
        self,
        contact_id: int,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all tickets created by or assigned to a contact.

        Args:
            contact_id: ID of the contact
            status_filter: Optional status filter ('open', 'closed', etc.)
            limit: Maximum number of tickets to return

        Returns:
            List of tickets associated with the contact
        """
        # Search both ContactID and AssignedResourceID fields
        filters = [QueryFilter(field="ContactID", op="eq", value=contact_id)]

        if status_filter:
            status_map = {
                "open": [1, 8, 9, 10, 11],
                "closed": [5],
                "new": [1],
                "in_progress": [8, 9, 10, 11],
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        return self._client.query("Tickets", filters=filters, max_records=limit)

    def update_contact_info(
        self,
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email_address: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
        mobile_phone: Optional[str] = None,
    ) -> ContactData:
        """
        Update contact information.

        Args:
            contact_id: ID of contact to update
            first_name: New first name
            last_name: New last name
            email_address: New email address
            phone: New phone number
            title: New job title
            mobile_phone: New mobile phone number

        Returns:
            Updated contact data
        """
        update_data = {}

        if first_name is not None:
            update_data["FirstName"] = first_name
        if last_name is not None:
            update_data["LastName"] = last_name
        if email_address is not None:
            update_data["EMailAddress"] = email_address
        if phone is not None:
            update_data["Phone"] = phone
        if title is not None:
            update_data["Title"] = title
        if mobile_phone is not None:
            update_data["MobilePhone"] = mobile_phone

        if not update_data:
            raise ValueError("At least one field must be provided for update")

        return self.update_by_id(contact_id, update_data)

    def activate_contact(self, contact_id: int) -> ContactData:
        """
        Activate a contact.

        Args:
            contact_id: ID of contact to activate

        Returns:
            Updated contact data
        """
        return self.update_by_id(contact_id, {"Active": True})

    def deactivate_contact(self, contact_id: int) -> ContactData:
        """
        Deactivate a contact.

        Args:
            contact_id: ID of contact to deactivate

        Returns:
            Updated contact data
        """
        return self.update_by_id(contact_id, {"Active": False})

    def set_primary_contact(
        self, contact_id: int, is_primary: bool = True
    ) -> ContactData:
        """
        Set or unset a contact as primary contact for their company.

        Args:
            contact_id: ID of contact to update
            is_primary: Whether to set as primary contact

        Returns:
            Updated contact data
        """
        return self.update_by_id(contact_id, {"PrimaryContact": is_primary})

    def get_contacts_by_role(
        self,
        company_id: Optional[int] = None,
        role_filter: str = "all",
        limit: Optional[int] = None,
    ) -> List[ContactData]:
        """
        Get contacts by their role/type.

        Args:
            company_id: Optional company ID filter
            role_filter: Role filter ('primary', 'billing', 'technical', 'all')
            limit: Maximum number of contacts to return

        Returns:
            List of contacts matching role criteria
        """
        filters = []

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        if role_filter == "primary":
            filters.append(QueryFilter(field="PrimaryContact", op="eq", value=True))
        elif role_filter == "billing":
            filters.append(QueryFilter(field="BillingContact", op="eq", value=True))
        elif role_filter == "technical":
            filters.append(QueryFilter(field="TechnicalContact", op="eq", value=True))
        # 'all' means no additional filter

        return self.query(filters=filters, max_records=limit)

    def bulk_update_company(
        self, contact_ids: List[int], new_company_id: int
    ) -> List[ContactData]:
        """
        Move multiple contacts to a different company.

        Args:
            contact_ids: List of contact IDs to move
            new_company_id: ID of the new company

        Returns:
            List of updated contact data
        """
        results = []
        for contact_id in contact_ids:
            try:
                result = self.update_by_id(contact_id, {"CompanyID": new_company_id})
                results.append(result)
            except Exception as e:
                # Log error but continue with other contacts
                self._client.logger.error(f"Failed to update contact {contact_id}: {e}")

        return results

    def find_duplicate_contacts(
        self,
        company_id: Optional[int] = None,
        by_email: bool = True,
        by_name: bool = False,
    ) -> Dict[str, List[ContactData]]:
        """
        Find potential duplicate contacts.

        Args:
            company_id: Optional company ID filter
            by_email: Check for duplicates by email address
            by_name: Check for duplicates by name

        Returns:
            Dictionary mapping duplicate keys to lists of contacts
        """
        filters = []
        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        all_contacts = self.query(filters=filters)
        duplicates = {}

        if by_email:
            email_groups = {}
            for contact in all_contacts:
                email = contact.get("EMailAddress", "").lower().strip()
                if email:
                    if email not in email_groups:
                        email_groups[email] = []
                    email_groups[email].append(contact)

            # Add groups with more than one contact
            for email, contacts in email_groups.items():
                if len(contacts) > 1:
                    duplicates[f"email:{email}"] = contacts

        if by_name:
            name_groups = {}
            for contact in all_contacts:
                first_name = contact.get("FirstName", "").lower().strip()
                last_name = contact.get("LastName", "").lower().strip()
                full_name = f"{first_name} {last_name}".strip()
                if full_name:
                    if full_name not in name_groups:
                        name_groups[full_name] = []
                    name_groups[full_name].append(contact)

            # Add groups with more than one contact
            for name, contacts in name_groups.items():
                if len(contacts) > 1:
                    duplicates[f"name:{name}"] = contacts

        return duplicates
