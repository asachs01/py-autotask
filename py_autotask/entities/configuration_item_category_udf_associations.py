"""
Configuration Item Category UDF Associations entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemCategoryUdfAssociationsEntity(BaseEntity):
    """
    Handles all Configuration Item Category UDF Association-related operations for the Autotask API.

    Configuration Item Category UDF Associations link user-defined fields (UDFs) to
    configuration item categories, enabling custom field availability based on CI category.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_category_udf_association(
        self,
        configuration_item_category_id: int,
        udf_id: int,
        is_required: bool = False,
        display_order: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item category UDF association.

        Args:
            configuration_item_category_id: ID of the configuration item category
            udf_id: ID of the user-defined field
            is_required: Whether the UDF is required for this category
            display_order: Optional display order for the UDF
            **kwargs: Additional association fields

        Returns:
            Created UDF association data
        """
        association_data = {
            "ConfigurationItemCategoryID": configuration_item_category_id,
            "UserDefinedFieldID": udf_id,
            "IsRequired": is_required,
            **kwargs,
        }

        if display_order is not None:
            association_data["DisplayOrder"] = display_order

        return self.create(association_data)

    def get_category_udf_associations(
        self,
        configuration_item_category_id: int,
        required_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all UDF associations for a specific configuration item category.

        Args:
            configuration_item_category_id: ID of the configuration item category
            required_only: Whether to return only required UDF associations
            limit: Maximum number of associations to return

        Returns:
            List of UDF associations
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemCategoryID",
                op="eq",
                value=configuration_item_category_id,
            )
        ]

        if required_only:
            filters.append(QueryFilter(field="IsRequired", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_udf_category_associations(
        self,
        udf_id: int,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all category associations for a specific user-defined field.

        Args:
            udf_id: ID of the user-defined field
            limit: Maximum number of associations to return

        Returns:
            List of category associations
        """
        filters = [QueryFilter(field="UserDefinedFieldID", op="eq", value=udf_id)]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_required_udfs_for_category(
        self, configuration_item_category_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all required UDFs for a specific configuration item category.

        Args:
            configuration_item_category_id: ID of the configuration item category

        Returns:
            List of required UDF associations with UDF details
        """
        associations = self.get_category_udf_associations(
            configuration_item_category_id, required_only=True
        )

        # Enrich with UDF details
        for association in associations:
            udf_id = association.get("UserDefinedFieldID")
            if udf_id:
                udf_details = self.client.get("UserDefinedFields", udf_id)
                association["udf_details"] = udf_details

        return associations

    def update_association_requirement(
        self, association_id: int, is_required: bool
    ) -> Dict[str, Any]:
        """
        Update the requirement status of a UDF association.

        Args:
            association_id: ID of association to update
            is_required: Whether the UDF should be required

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"IsRequired": is_required})

    def update_display_order(
        self, association_id: int, display_order: int
    ) -> Dict[str, Any]:
        """
        Update the display order of a UDF association.

        Args:
            association_id: ID of association to update
            display_order: New display order value

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"DisplayOrder": display_order})

    def remove_udf_from_category(
        self, configuration_item_category_id: int, udf_id: int
    ) -> bool:
        """
        Remove a UDF association from a configuration item category.

        Args:
            configuration_item_category_id: ID of the configuration item category
            udf_id: ID of the user-defined field to remove

        Returns:
            True if successfully removed
        """
        # Find the association
        associations = self.get_category_udf_associations(
            configuration_item_category_id
        )

        for association in associations:
            if association.get("UserDefinedFieldID") == udf_id:
                association_id = association.get("id")
                if association_id:
                    return self.delete(association_id)

        return False

    def get_category_udf_summary(
        self, configuration_item_category_id: int
    ) -> Dict[str, Any]:
        """
        Get a summary of UDF associations for a configuration item category.

        Args:
            configuration_item_category_id: ID of the configuration item category

        Returns:
            Dictionary with UDF association statistics
        """
        associations = self.get_category_udf_associations(
            configuration_item_category_id
        )

        summary = {
            "category_id": configuration_item_category_id,
            "total_udfs": len(associations),
            "required_udfs": 0,
            "optional_udfs": 0,
            "udf_types": {},
            "display_ordered": 0,
        }

        for association in associations:
            if association.get("IsRequired"):
                summary["required_udfs"] += 1
            else:
                summary["optional_udfs"] += 1

            if association.get("DisplayOrder") is not None:
                summary["display_ordered"] += 1

            # Get UDF details for type information
            udf_id = association.get("UserDefinedFieldID")
            if udf_id:
                udf_details = self.client.get("UserDefinedFields", udf_id)
                if udf_details:
                    udf_type = udf_details.get("DataType", "Unknown")
                    summary["udf_types"][udf_type] = (
                        summary["udf_types"].get(udf_type, 0) + 1
                    )

        return summary

    def copy_udfs_between_categories(
        self,
        source_category_id: int,
        target_category_id: int,
        preserve_requirements: bool = True,
        preserve_display_order: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Copy UDF associations from one category to another.

        Args:
            source_category_id: ID of the source configuration item category
            target_category_id: ID of the target configuration item category
            preserve_requirements: Whether to preserve requirement settings
            preserve_display_order: Whether to preserve display order

        Returns:
            List of newly created associations
        """
        source_associations = self.get_category_udf_associations(source_category_id)
        new_associations = []

        for association in source_associations:
            udf_id = association.get("UserDefinedFieldID")
            if not udf_id:
                continue

            # Check if association already exists for target category
            existing = self.get_category_udf_associations(target_category_id)
            if any(assoc.get("UserDefinedFieldID") == udf_id for assoc in existing):
                continue  # Skip if already exists

            new_association_data = {
                "configuration_item_category_id": target_category_id,
                "udf_id": udf_id,
            }

            if preserve_requirements:
                new_association_data["is_required"] = association.get(
                    "IsRequired", False
                )

            if preserve_display_order and association.get("DisplayOrder") is not None:
                new_association_data["display_order"] = association.get("DisplayOrder")

            try:
                new_association = self.create_category_udf_association(
                    **new_association_data
                )
                new_associations.append(new_association)
            except Exception as e:
                # Log error but continue with other associations
                self.client.logger.error(
                    f"Failed to copy UDF {udf_id} to category {target_category_id}: {e}"
                )

        return new_associations

    def bulk_update_requirements(
        self, association_updates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Update requirement status for multiple UDF associations in bulk.

        Args:
            association_updates: List of dicts with 'association_id' and 'is_required'

        Returns:
            List of updated association data
        """
        update_data = [
            {"id": update["association_id"], "IsRequired": update["is_required"]}
            for update in association_updates
        ]
        return self.batch_update(update_data)

    def get_associations_by_udf_type(
        self, udf_type: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all category associations for UDFs of a specific data type.

        Args:
            udf_type: Type of UDF to filter by (e.g., 'Text', 'Date', 'Number')
            limit: Maximum number of associations to return

        Returns:
            List of associations for UDFs of the specified type
        """
        # First get all UDFs of the specified type
        udf_filters = [QueryFilter(field="DataType", op="eq", value=udf_type)]
        udf_response = self.client.query("UserDefinedFields", filters=udf_filters)
        udfs = udf_response.get("items", [])

        if not udfs:
            return []

        # Get associations for these UDFs
        udf_ids = [udf.get("id") for udf in udfs if udf.get("id")]

        associations = []
        for udf_id in udf_ids:
            udf_associations = self.get_udf_category_associations(udf_id)
            associations.extend(udf_associations)

        if limit and len(associations) > limit:
            associations = associations[:limit]

        return associations
