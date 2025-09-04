"""
ContactBillingProductAssociations entity for Autotask API operations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ContactBillingProductAssociationsEntity(BaseEntity):
    """
    Handles all ContactBillingProductAssociations-related operations for the Autotask API.

    ContactBillingProductAssociations represent relationships between contacts and
    billing products, defining which products a contact has access to or is responsible for.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_contact_product_association(
        self,
        contact_id: int,
        billing_product_id: int,
        association_type: int = 1,
        is_active: bool = True,
        start_date: Optional[date] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new contact billing product association.

        Args:
            contact_id: ID of the contact
            billing_product_id: ID of the billing product
            association_type: Type of association (1=Primary, 2=Secondary, 3=Billing, etc.)
            is_active: Whether the association is active
            start_date: Date when the association starts
            **kwargs: Additional association properties

        Returns:
            Created contact billing product association data
        """
        association_data = {
            "ContactID": contact_id,
            "BillingProductID": billing_product_id,
            "AssociationType": association_type,
            "IsActive": is_active,
            **kwargs,
        }

        if start_date:
            association_data["StartDate"] = start_date.isoformat()

        return self.create(association_data)

    def get_associations_by_contact(
        self, contact_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all product associations for a specific contact.

        Args:
            contact_id: ID of the contact
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of product associations for the contact
        """
        filters = [QueryFilter(field="ContactID", op="eq", value=contact_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_associations_by_product(
        self,
        billing_product_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all contact associations for a specific billing product.

        Args:
            billing_product_id: ID of the billing product
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of contact associations for the product
        """
        filters = [
            QueryFilter(field="BillingProductID", op="eq", value=billing_product_id)
        ]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_associations_by_type(
        self,
        association_type: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get associations by association type.

        Args:
            association_type: Type of association to filter by
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of associations of the specified type
        """
        filters = [
            QueryFilter(field="AssociationType", op="eq", value=association_type)
        ]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def activate_association(self, association_id: int) -> EntityDict:
        """
        Activate a contact billing product association.

        Args:
            association_id: ID of the association to activate

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"IsActive": True})

    def deactivate_association(
        self, association_id: int, end_date: Optional[date] = None
    ) -> EntityDict:
        """
        Deactivate a contact billing product association.

        Args:
            association_id: ID of the association to deactivate
            end_date: Date when the association ends

        Returns:
            Updated association data
        """
        update_data = {"IsActive": False}

        if end_date:
            update_data["EndDate"] = end_date.isoformat()

        return self.update_by_id(association_id, update_data)

    def transfer_product_association(
        self, association_id: int, new_contact_id: int, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Transfer a product association to a different contact.

        Args:
            association_id: ID of the association to transfer
            new_contact_id: ID of the new contact
            reason: Reason for the transfer

        Returns:
            Updated association data
        """
        update_data = {
            "ContactID": new_contact_id,
            "TransferDate": datetime.now().isoformat(),
        }

        if reason:
            update_data["TransferReason"] = reason

        return self.update_by_id(association_id, update_data)

    def bulk_create_associations(
        self, associations_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple contact billing product associations in batch.

        Args:
            associations_data: List of association data dictionaries

        Returns:
            List of created association responses
        """
        return self.batch_create(associations_data)

    def get_contact_product_portfolio(self, contact_id: int) -> Dict[str, Any]:
        """
        Get a complete product portfolio for a contact.

        Args:
            contact_id: ID of the contact

        Returns:
            Dictionary containing contact's product portfolio
        """
        associations = self.get_associations_by_contact(contact_id, active_only=False)
        active_associations = [a for a in associations if a.get("IsActive", False)]

        portfolio = {
            "contact_id": contact_id,
            "total_products": len(associations),
            "active_products": len(active_associations),
            "inactive_products": len(associations) - len(active_associations),
            "products_by_type": {},
            "recent_changes": [],
        }

        # Group by association type
        for association in associations:
            assoc_type = association.get("AssociationType", 0)
            if assoc_type not in portfolio["products_by_type"]:
                portfolio["products_by_type"][assoc_type] = {
                    "total": 0,
                    "active": 0,
                    "products": [],
                }

            portfolio["products_by_type"][assoc_type]["total"] += 1
            if association.get("IsActive", False):
                portfolio["products_by_type"][assoc_type]["active"] += 1

            portfolio["products_by_type"][assoc_type]["products"].append(
                {
                    "association_id": association.get("id"),
                    "product_id": association.get("BillingProductID"),
                    "is_active": association.get("IsActive", False),
                    "start_date": association.get("StartDate"),
                    "end_date": association.get("EndDate"),
                }
            )

        return portfolio

    def find_duplicate_associations(
        self, contact_id: int, billing_product_id: int
    ) -> List[EntityDict]:
        """
        Find duplicate associations for a contact-product pair.

        Args:
            contact_id: ID of the contact
            billing_product_id: ID of the billing product

        Returns:
            List of duplicate associations
        """
        filters = [
            QueryFilter(field="ContactID", op="eq", value=contact_id),
            QueryFilter(field="BillingProductID", op="eq", value=billing_product_id),
        ]

        response = self.query(filters=filters)
        duplicates = response.items if hasattr(response, "items") else response

        return duplicates if len(duplicates) > 1 else []

    def get_product_contact_summary(self, billing_product_id: int) -> Dict[str, Any]:
        """
        Get a summary of contacts associated with a billing product.

        Args:
            billing_product_id: ID of the billing product

        Returns:
            Dictionary containing product contact summary
        """
        associations = self.get_associations_by_product(
            billing_product_id, active_only=False
        )
        active_associations = [a for a in associations if a.get("IsActive", False)]

        summary = {
            "product_id": billing_product_id,
            "total_contacts": len(associations),
            "active_contacts": len(active_associations),
            "inactive_contacts": len(associations) - len(active_associations),
            "contacts_by_type": {},
            "primary_contacts": [],
            "billing_contacts": [],
        }

        # Analyze association types
        for association in associations:
            assoc_type = association.get("AssociationType", 0)
            contact_id = association.get("ContactID")

            if assoc_type not in summary["contacts_by_type"]:
                summary["contacts_by_type"][assoc_type] = 0
            summary["contacts_by_type"][assoc_type] += 1

            # Identify specific contact types
            if assoc_type == 1 and association.get("IsActive", False):  # Primary
                summary["primary_contacts"].append(contact_id)
            elif assoc_type == 3 and association.get("IsActive", False):  # Billing
                summary["billing_contacts"].append(contact_id)

        return summary

    def validate_association_rules(
        self, contact_id: int, billing_product_id: int, association_type: int
    ) -> Dict[str, Any]:
        """
        Validate business rules for creating an association.

        Args:
            contact_id: ID of the contact
            billing_product_id: ID of the billing product
            association_type: Type of association

        Returns:
            Dictionary containing validation results
        """
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Check for existing associations
        existing_associations = self.find_duplicate_associations(
            contact_id, billing_product_id
        )
        active_duplicates = [
            a for a in existing_associations if a.get("IsActive", False)
        ]

        if active_duplicates:
            validation_results["errors"].append(
                "Active association already exists for this contact-product pair"
            )
            validation_results["is_valid"] = False

        # Check for multiple primary associations (business rule example)
        if association_type == 1:  # Primary
            primary_associations = self.get_associations_by_contact(contact_id)
            primary_count = len(
                [a for a in primary_associations if a.get("AssociationType") == 1]
            )

            if primary_count >= 5:  # Example business rule
                validation_results["warnings"].append(
                    f"Contact already has {primary_count} primary product associations"
                )

        return validation_results

    def bulk_transfer_associations(
        self,
        old_contact_id: int,
        new_contact_id: int,
        product_ids: Optional[List[int]] = None,
    ) -> List[EntityDict]:
        """
        Transfer multiple product associations from one contact to another.

        Args:
            old_contact_id: ID of the old contact
            new_contact_id: ID of the new contact
            product_ids: Optional list of specific product IDs to transfer

        Returns:
            List of updated association data
        """
        associations = self.get_associations_by_contact(old_contact_id)

        if product_ids:
            associations = [
                a for a in associations if a.get("BillingProductID") in product_ids
            ]

        transferred = []
        for association in associations:
            if association.get("id"):
                updated = self.transfer_product_association(
                    association["id"],
                    new_contact_id,
                    f"Bulk transfer from contact {old_contact_id}",
                )
                transferred.append(updated)

        return transferred

    def cleanup_expired_associations(
        self, cutoff_date: Optional[date] = None, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up associations that have expired.

        Args:
            cutoff_date: Date to use as expiration cutoff (defaults to today)
            dry_run: If True, only identify expired associations

        Returns:
            Dictionary containing cleanup results
        """
        if not cutoff_date:
            cutoff_date = date.today()

        filters = [
            QueryFilter(field="EndDate", op="lt", value=cutoff_date.isoformat()),
            QueryFilter(field="IsActive", op="eq", value=True),
        ]

        response = self.query(filters=filters)
        expired_associations = (
            response.items if hasattr(response, "items") else response
        )

        cleanup_results = {
            "cutoff_date": cutoff_date.isoformat(),
            "expired_associations_found": len(expired_associations),
            "dry_run": dry_run,
            "associations_to_deactivate": [
                {
                    "association_id": assoc.get("id"),
                    "contact_id": assoc.get("ContactID"),
                    "product_id": assoc.get("BillingProductID"),
                    "end_date": assoc.get("EndDate"),
                }
                for assoc in expired_associations
            ],
            "cleanup_count": 0,
        }

        if not dry_run and expired_associations:
            for association in expired_associations:
                if association.get("id"):
                    self.deactivate_association(association["id"])
            cleanup_results["cleanup_count"] = len(expired_associations)

        return cleanup_results
