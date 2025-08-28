"""
ChecklistLibraryChecklistItems entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ChecklistLibraryChecklistItemsEntity(BaseEntity):
    """
    Handles all ChecklistLibraryChecklistItems-related operations for the Autotask API.

    ChecklistLibraryChecklistItems represent individual items within checklist libraries,
    defining the specific tasks or checks that should be completed.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_checklist_item(
        self,
        checklist_library_id: int,
        name: str,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        is_required: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new checklist item in a library.

        Args:
            checklist_library_id: ID of the checklist library
            name: Name of the checklist item
            description: Detailed description of the item
            sort_order: Order position within the checklist
            is_required: Whether this item is required for completion
            **kwargs: Additional checklist item properties

        Returns:
            Created checklist item data
        """
        item_data = {
            "ChecklistLibraryID": checklist_library_id,
            "Name": name,
            "IsRequired": is_required,
            **kwargs,
        }

        if description:
            item_data["Description"] = description
        if sort_order is not None:
            item_data["SortOrder"] = sort_order

        return self.create(item_data)

    def get_items_by_library(
        self, checklist_library_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all checklist items for a specific library.

        Args:
            checklist_library_id: ID of the checklist library
            limit: Maximum number of items to return

        Returns:
            List of checklist items, ordered by sort order
        """
        filters = [
            QueryFilter(field="ChecklistLibraryID", op="eq", value=checklist_library_id)
        ]
        response = self.query(filters=filters, max_records=limit)

        items = response.items if hasattr(response, "items") else response
        # Sort by sort order if available
        return sorted(items, key=lambda x: x.get("SortOrder", 999))

    def get_required_items_by_library(
        self, checklist_library_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all required checklist items for a specific library.

        Args:
            checklist_library_id: ID of the checklist library
            limit: Maximum number of items to return

        Returns:
            List of required checklist items
        """
        filters = [
            QueryFilter(
                field="ChecklistLibraryID", op="eq", value=checklist_library_id
            ),
            QueryFilter(field="IsRequired", op="eq", value=True),
        ]
        response = self.query(filters=filters, max_records=limit)

        items = response.items if hasattr(response, "items") else response
        return sorted(items, key=lambda x: x.get("SortOrder", 999))

    def update_item_order(self, item_id: int, new_sort_order: int) -> EntityDict:
        """
        Update the sort order of a checklist item.

        Args:
            item_id: ID of the checklist item
            new_sort_order: New sort order position

        Returns:
            Updated checklist item data
        """
        return self.update_by_id(item_id, {"SortOrder": new_sort_order})

    def bulk_update_sort_orders(
        self, item_order_updates: List[Dict[str, int]]
    ) -> List[EntityDict]:
        """
        Update sort orders for multiple checklist items.

        Args:
            item_order_updates: List of dicts with 'item_id' and 'sort_order' keys

        Returns:
            List of updated checklist item data
        """
        updates = []
        for update in item_order_updates:
            item_data = {"id": update["item_id"], "SortOrder": update["sort_order"]}
            updates.append(item_data)

        return self.batch_update(updates)

    def toggle_required_status(
        self, item_id: int, is_required: Optional[bool] = None
    ) -> EntityDict:
        """
        Toggle or set the required status of a checklist item.

        Args:
            item_id: ID of the checklist item
            is_required: New required status (if None, toggles current status)

        Returns:
            Updated checklist item data
        """
        if is_required is None:
            # Need to get current status to toggle
            current_item = self.get(item_id)
            if current_item:
                is_required = not current_item.get("IsRequired", False)
            else:
                is_required = True

        return self.update_by_id(item_id, {"IsRequired": is_required})

    def duplicate_items_to_library(
        self, source_library_id: int, target_library_id: int
    ) -> List[EntityDict]:
        """
        Duplicate all checklist items from one library to another.

        Args:
            source_library_id: ID of the source checklist library
            target_library_id: ID of the target checklist library

        Returns:
            List of created checklist item responses
        """
        source_items = self.get_items_by_library(source_library_id)

        target_items = []
        for item in source_items:
            target_data = {
                "ChecklistLibraryID": target_library_id,
                "Name": item.get("Name"),
                "Description": item.get("Description"),
                "SortOrder": item.get("SortOrder"),
                "IsRequired": item.get("IsRequired", False),
            }
            target_items.append(target_data)

        if target_items:
            return self.batch_create(target_items)
        return []

    def reorder_library_items(
        self, checklist_library_id: int, new_order: List[int]
    ) -> List[EntityDict]:
        """
        Reorder all items in a checklist library.

        Args:
            checklist_library_id: ID of the checklist library
            new_order: List of item IDs in the desired order

        Returns:
            List of updated checklist item data
        """
        order_updates = []
        for index, item_id in enumerate(new_order, start=1):
            order_updates.append(
                {
                    "item_id": item_id,
                    "sort_order": index * 10,  # Leave gaps for future insertions
                }
            )

        return self.bulk_update_sort_orders(order_updates)

    def get_library_item_statistics(self, checklist_library_id: int) -> Dict[str, Any]:
        """
        Get statistics about checklist items in a library.

        Args:
            checklist_library_id: ID of the checklist library

        Returns:
            Dictionary containing item statistics
        """
        items = self.get_items_by_library(checklist_library_id)

        required_items = [item for item in items if item.get("IsRequired", False)]
        optional_items = [item for item in items if not item.get("IsRequired", False)]

        return {
            "library_id": checklist_library_id,
            "total_items": len(items),
            "required_items": len(required_items),
            "optional_items": len(optional_items),
            "required_percentage": (len(required_items) / max(1, len(items))) * 100,
            "avg_name_length": sum(len(item.get("Name", "")) for item in items)
            / max(1, len(items)),
            "items_with_descriptions": len(
                [item for item in items if item.get("Description")]
            ),
            "max_sort_order": max(
                [item.get("SortOrder", 0) for item in items], default=0
            ),
        }

    def search_items_by_name(
        self,
        search_term: str,
        checklist_library_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Search checklist items by name.

        Args:
            search_term: Term to search for in item names
            checklist_library_id: Optional library ID to limit search scope
            limit: Maximum number of items to return

        Returns:
            List of matching checklist items
        """
        filters = [QueryFilter(field="Name", op="contains", value=search_term)]

        if checklist_library_id:
            filters.append(
                QueryFilter(
                    field="ChecklistLibraryID", op="eq", value=checklist_library_id
                )
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def bulk_create_library_items(
        self, checklist_library_id: int, items_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple checklist items for a library in batch.

        Args:
            checklist_library_id: ID of the checklist library
            items_data: List of item data dictionaries

        Returns:
            List of created checklist item responses
        """
        # Ensure all items have the correct library ID
        for item_data in items_data:
            item_data["ChecklistLibraryID"] = checklist_library_id

            # Auto-assign sort order if not provided
            if "SortOrder" not in item_data:
                item_data["SortOrder"] = (items_data.index(item_data) + 1) * 10

        return self.batch_create(items_data)

    def export_library_checklist(
        self, checklist_library_id: int, include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Export a complete checklist library with all its items.

        Args:
            checklist_library_id: ID of the checklist library
            include_metadata: Whether to include metadata like IDs and timestamps

        Returns:
            Dictionary containing complete checklist export
        """
        items = self.get_items_by_library(checklist_library_id)

        export_data = {
            "library_id": checklist_library_id if include_metadata else None,
            "total_items": len(items),
            "required_items_count": len(
                [item for item in items if item.get("IsRequired", False)]
            ),
            "items": [],
        }

        for item in items:
            item_export = {
                "name": item.get("Name"),
                "description": item.get("Description"),
                "sort_order": item.get("SortOrder"),
                "is_required": item.get("IsRequired", False),
            }

            if include_metadata:
                item_export.update(
                    {
                        "item_id": item.get("id"),
                        "created_date": item.get("CreateDateTime"),
                        "last_modified": item.get("LastModifiedDateTime"),
                    }
                )

            export_data["items"].append(item_export)

        return export_data
