"""
Organizational Level Associations entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class OrganizationalLevelAssociationsEntity(BaseEntity):
    """
    Handles all Organizational Level Association-related operations for the Autotask API.

    Organizational Level Associations link various entities (like accounts, projects,
    resources) to specific organizational levels, enabling hierarchical organization
    and reporting within the Autotask system.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_organizational_association(
        self,
        organizational_level_id: int,
        associated_entity_type: str,
        associated_entity_id: int,
        association_type: Optional[str] = None,
        is_active: bool = True,
        effective_date: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new organizational level association.

        Args:
            organizational_level_id: ID of the organizational level
            associated_entity_type: Type of entity being associated (e.g., 'Account', 'Resource')
            associated_entity_id: ID of the entity being associated
            association_type: Type of association (e.g., 'primary', 'secondary')
            is_active: Whether the association is active
            effective_date: Date when association becomes effective
            **kwargs: Additional association fields

        Returns:
            Created organizational level association data
        """
        association_data = {
            "OrganizationalLevelID": organizational_level_id,
            "AssociatedEntityType": associated_entity_type,
            "AssociatedEntityID": associated_entity_id,
            "IsActive": is_active,
            **kwargs,
        }

        if association_type:
            association_data["AssociationType"] = association_type
        if effective_date:
            association_data["EffectiveDate"] = effective_date

        return self.create(association_data)

    def get_associations_for_level(
        self,
        organizational_level_id: int,
        entity_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[EntityDict]:
        """
        Get all associations for a specific organizational level.

        Args:
            organizational_level_id: Organizational level ID to get associations for
            entity_type: Optional entity type filter
            active_only: Whether to return only active associations

        Returns:
            List of associations for the organizational level
        """
        filters = [
            {
                "field": "OrganizationalLevelID",
                "op": "eq",
                "value": organizational_level_id,
            }
        ]

        if entity_type:
            filters.append(
                {"field": "AssociatedEntityType", "op": "eq", "value": entity_type}
            )

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_associations_for_entity(
        self,
        entity_type: str,
        entity_id: int,
        active_only: bool = True,
    ) -> List[EntityDict]:
        """
        Get organizational level associations for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            active_only: Whether to return only active associations

        Returns:
            List of organizational level associations for the entity
        """
        filters = [
            {"field": "AssociatedEntityType", "op": "eq", "value": entity_type},
            {"field": "AssociatedEntityID", "op": "eq", "value": entity_id},
        ]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_associations_by_type(
        self,
        association_type: str,
        organizational_level_id: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get associations by association type.

        Args:
            association_type: Type of association to filter by
            organizational_level_id: Optional organizational level filter

        Returns:
            List of associations matching the type
        """
        filters = [{"field": "AssociationType", "op": "eq", "value": association_type}]

        if organizational_level_id:
            filters.append(
                {
                    "field": "OrganizationalLevelID",
                    "op": "eq",
                    "value": organizational_level_id,
                }
            )

        return self.query_all(filters=filters)

    def deactivate_association(self, association_id: int) -> EntityDict:
        """
        Deactivate an organizational level association.

        Args:
            association_id: ID of the association to deactivate

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"IsActive": False})

    def update_association_effective_date(
        self, association_id: int, effective_date: str
    ) -> EntityDict:
        """
        Update the effective date of an association.

        Args:
            association_id: ID of the association to update
            effective_date: New effective date

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"EffectiveDate": effective_date})

    def bulk_associate_entities(
        self,
        organizational_level_id: int,
        entities: List[Dict[str, Any]],
        association_type: Optional[str] = None,
    ) -> List[EntityDict]:
        """
        Associate multiple entities with an organizational level in bulk.

        Args:
            organizational_level_id: Organizational level ID
            entities: List of dicts with 'entity_type' and 'entity_id' keys
            association_type: Optional association type

        Returns:
            List of created associations
        """
        results = []

        for entity in entities:
            try:
                association = self.create_organizational_association(
                    organizational_level_id=organizational_level_id,
                    associated_entity_type=entity["entity_type"],
                    associated_entity_id=entity["entity_id"],
                    association_type=association_type,
                )
                results.append(association)
            except Exception as e:
                self.logger.error(
                    f"Failed to associate {entity['entity_type']} {entity['entity_id']} "
                    f"with organizational level {organizational_level_id}: {e}"
                )
                continue

        return results

    def transfer_entity_association(
        self,
        entity_type: str,
        entity_id: int,
        from_level_id: int,
        to_level_id: int,
        preserve_history: bool = True,
    ) -> Dict[str, Any]:
        """
        Transfer an entity from one organizational level to another.

        Args:
            entity_type: Type of entity to transfer
            entity_id: ID of entity to transfer
            from_level_id: Current organizational level ID
            to_level_id: New organizational level ID
            preserve_history: Whether to deactivate old association instead of deleting

        Returns:
            Dictionary with transfer results
        """
        # Find existing association
        existing_associations = self.query_all(
            filters=[
                {"field": "OrganizationalLevelID", "op": "eq", "value": from_level_id},
                {"field": "AssociatedEntityType", "op": "eq", "value": entity_type},
                {"field": "AssociatedEntityID", "op": "eq", "value": entity_id},
                {"field": "IsActive", "op": "eq", "value": "true"},
            ]
        )

        if not existing_associations:
            return {"error": "No active association found to transfer"}

        old_association = existing_associations[0]

        try:
            # Create new association
            new_association = self.create_organizational_association(
                organizational_level_id=to_level_id,
                associated_entity_type=entity_type,
                associated_entity_id=entity_id,
                association_type=old_association.get("AssociationType"),
            )

            # Handle old association
            if preserve_history:
                self.deactivate_association(old_association["id"])
                old_status = "deactivated"
            else:
                self.delete(old_association["id"])
                old_status = "deleted"

            return {
                "success": True,
                "old_association": old_association["id"],
                "old_association_status": old_status,
                "new_association": new_association,
                "transferred_entity": f"{entity_type} {entity_id}",
                "from_level": from_level_id,
                "to_level": to_level_id,
            }

        except Exception as e:
            return {
                "error": f"Transfer failed: {e}",
                "entity": f"{entity_type} {entity_id}",
                "from_level": from_level_id,
                "to_level": to_level_id,
            }

    def get_level_hierarchy_for_entity(
        self, entity_type: str, entity_id: int
    ) -> Dict[str, Any]:
        """
        Get the complete organizational level hierarchy for an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity

        Returns:
            Dictionary containing hierarchy information
        """
        associations = self.get_associations_for_entity(entity_type, entity_id)

        hierarchy_info = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_associations": len(associations),
            "active_associations": len([a for a in associations if a.get("IsActive")]),
            "levels": [],
        }

        for association in associations:
            level_info = {
                "association_id": association["id"],
                "organizational_level_id": association.get("OrganizationalLevelID"),
                "association_type": association.get("AssociationType"),
                "is_active": association.get("IsActive"),
                "effective_date": association.get("EffectiveDate"),
            }
            hierarchy_info["levels"].append(level_info)

        return hierarchy_info

    def get_association_summary_by_entity_type(self) -> Dict[str, Any]:
        """
        Get summary of associations grouped by entity type.

        Returns:
            Dictionary containing association summary by entity type
        """
        all_associations = self.query_all()

        summary = {}
        for association in all_associations:
            entity_type = association.get("AssociatedEntityType", "unknown")

            if entity_type not in summary:
                summary[entity_type] = {
                    "total_associations": 0,
                    "active_associations": 0,
                    "unique_entities": set(),
                    "unique_levels": set(),
                }

            summary[entity_type]["total_associations"] += 1
            if association.get("IsActive"):
                summary[entity_type]["active_associations"] += 1

            summary[entity_type]["unique_entities"].add(
                association.get("AssociatedEntityID")
            )
            summary[entity_type]["unique_levels"].add(
                association.get("OrganizationalLevelID")
            )

        # Convert sets to counts for JSON serialization
        for entity_type in summary:
            summary[entity_type]["unique_entity_count"] = len(
                summary[entity_type]["unique_entities"]
            )
            summary[entity_type]["unique_level_count"] = len(
                summary[entity_type]["unique_levels"]
            )
            del summary[entity_type]["unique_entities"]
            del summary[entity_type]["unique_levels"]

        return summary
