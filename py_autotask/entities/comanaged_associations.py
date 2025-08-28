"""
ComanagedAssociations entity for Autotask API operations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ComanagedAssociationsEntity(BaseEntity):
    """
    Handles all ComanagedAssociations-related operations for the Autotask API.

    ComanagedAssociations represent relationships between multiple service providers
    or teams that share responsibility for managing client accounts or services.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_comanaged_association(
        self,
        account_id: int,
        partner_account_id: int,
        association_type: int,
        is_active: bool = True,
        start_date: Optional[date] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new comanaged association.

        Args:
            account_id: ID of the primary account
            partner_account_id: ID of the partner account
            association_type: Type of association (1=Primary, 2=Secondary, 3=Referral, etc.)
            is_active: Whether the association is active
            start_date: Date when the association starts
            **kwargs: Additional association properties

        Returns:
            Created comanaged association data
        """
        association_data = {
            "AccountID": account_id,
            "PartnerAccountID": partner_account_id,
            "AssociationType": association_type,
            "IsActive": is_active,
            **kwargs,
        }

        if start_date:
            association_data["StartDate"] = start_date.isoformat()

        return self.create(association_data)

    def get_associations_by_account(
        self, account_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all comanaged associations for a specific account.

        Args:
            account_id: ID of the account
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of comanaged associations for the account
        """
        filters = [QueryFilter(field="AccountID", op="eq", value=account_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_partner_associations(
        self,
        partner_account_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get all associations where the specified account is a partner.

        Args:
            partner_account_id: ID of the partner account
            active_only: Whether to return only active associations
            limit: Maximum number of associations to return

        Returns:
            List of associations where the account is a partner
        """
        filters = [
            QueryFilter(field="PartnerAccountID", op="eq", value=partner_account_id)
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
        Get comanaged associations by type.

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
        Activate a comanaged association.

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
        Deactivate a comanaged association.

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

    def get_bidirectional_associations(
        self, account_id: int
    ) -> Dict[str, List[EntityDict]]:
        """
        Get both primary and partner associations for an account.

        Args:
            account_id: ID of the account

        Returns:
            Dictionary with 'primary' and 'partner' association lists
        """
        primary_associations = self.get_associations_by_account(account_id)
        partner_associations = self.get_partner_associations(account_id)

        return {
            "primary_associations": primary_associations,
            "partner_associations": partner_associations,
            "total_associations": len(primary_associations) + len(partner_associations),
        }

    def transfer_association(
        self,
        association_id: int,
        new_partner_account_id: int,
        reason: Optional[str] = None,
    ) -> EntityDict:
        """
        Transfer a comanaged association to a different partner.

        Args:
            association_id: ID of the association to transfer
            new_partner_account_id: ID of the new partner account
            reason: Reason for the transfer

        Returns:
            Updated association data
        """
        update_data = {
            "PartnerAccountID": new_partner_account_id,
            "TransferDate": datetime.now().isoformat(),
        }

        if reason:
            update_data["TransferReason"] = reason

        return self.update_by_id(association_id, update_data)

    def bulk_create_associations(
        self, associations_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple comanaged associations in batch.

        Args:
            associations_data: List of association data dictionaries

        Returns:
            List of created association responses
        """
        return self.batch_create(associations_data)

    def validate_association_conflicts(
        self, account_id: int, partner_account_id: int, association_type: int
    ) -> Dict[str, Any]:
        """
        Validate if creating an association would cause conflicts.

        Args:
            account_id: ID of the primary account
            partner_account_id: ID of the partner account
            association_type: Type of association

        Returns:
            Dictionary containing validation results
        """
        validation_results = {"is_valid": True, "conflicts": [], "warnings": []}

        # Check for existing associations
        existing_associations = self.get_associations_by_account(account_id)

        # Check for duplicate associations
        duplicate = any(
            assoc.get("PartnerAccountID") == partner_account_id
            and assoc.get("AssociationType") == association_type
            for assoc in existing_associations
        )

        if duplicate:
            validation_results["is_valid"] = False
            validation_results["conflicts"].append(
                "Duplicate association already exists for this account and partner"
            )

        # Check for circular associations (account A -> B and B -> A)
        reverse_associations = self.get_associations_by_account(partner_account_id)
        circular = any(
            assoc.get("PartnerAccountID") == account_id
            for assoc in reverse_associations
        )

        if circular:
            validation_results["warnings"].append(
                "Circular association detected - both accounts are partners to each other"
            )

        # Check for self-association
        if account_id == partner_account_id:
            validation_results["is_valid"] = False
            validation_results["conflicts"].append(
                "Account cannot be associated with itself"
            )

        return validation_results

    def get_association_network(
        self, account_id: int, max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get the complete association network for an account.

        Args:
            account_id: ID of the root account
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary containing the association network
        """
        network = {
            "root_account": account_id,
            "max_depth": max_depth,
            "associations": {},
            "total_accounts": 0,
            "network_size": 0,
        }

        visited = set()

        def traverse_associations(current_account_id: int, depth: int):
            if depth > max_depth or current_account_id in visited:
                return

            visited.add(current_account_id)

            # Get associations for current account
            associations = self.get_associations_by_account(current_account_id)
            partner_associations = self.get_partner_associations(current_account_id)

            all_associations = associations + partner_associations
            network["associations"][current_account_id] = all_associations

            # Traverse partners
            for assoc in all_associations:
                partner_id = assoc.get("PartnerAccountID") or assoc.get("AccountID")
                if partner_id and partner_id != current_account_id:
                    traverse_associations(partner_id, depth + 1)

        traverse_associations(account_id, 0)

        network["total_accounts"] = len(visited)
        network["network_size"] = sum(
            len(assocs) for assocs in network["associations"].values()
        )

        return network

    def get_association_summary_by_type(self) -> Dict[str, Any]:
        """
        Get a summary of all comanaged associations grouped by type.

        Returns:
            Dictionary containing association statistics by type
        """
        all_associations = self.query_all()

        summary = {
            "total_associations": len(all_associations),
            "active_associations": len(
                [a for a in all_associations if a.get("IsActive", False)]
            ),
            "types": {},
            "partner_distribution": {},
        }

        for association in all_associations:
            assoc_type = association.get("AssociationType", 0)
            partner_id = association.get("PartnerAccountID")

            # Count by type
            if assoc_type not in summary["types"]:
                summary["types"][assoc_type] = {"total": 0, "active": 0}

            summary["types"][assoc_type]["total"] += 1
            if association.get("IsActive", False):
                summary["types"][assoc_type]["active"] += 1

            # Count partner distribution
            if partner_id:
                if partner_id not in summary["partner_distribution"]:
                    summary["partner_distribution"][partner_id] = 0
                summary["partner_distribution"][partner_id] += 1

        return summary

    def find_orphaned_associations(self) -> List[EntityDict]:
        """
        Find associations that may be orphaned or have invalid references.

        Returns:
            List of potentially orphaned associations
        """
        all_associations = self.query_all()
        orphaned = []

        for association in all_associations:
            # Check for associations without proper account references
            if not association.get("AccountID") or not association.get(
                "PartnerAccountID"
            ):
                orphaned.append(association)

            # Check for self-referential associations
            if association.get("AccountID") == association.get("PartnerAccountID"):
                orphaned.append(association)

        return orphaned
