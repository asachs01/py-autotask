"""
Ticket Checklist Items entity for Autotask API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketChecklistItemsEntity(BaseEntity):
    """
    Handles Ticket Checklist Items operations for the Autotask API.

    Manages individual checklist items within tickets, including task completion
    tracking, item assignments, and progress monitoring for structured workflows.
    """

    def __init__(self, client, entity_name: str = "TicketChecklistItems"):
        super().__init__(client, entity_name)

    def create_checklist_item(
        self,
        ticket_id: int,
        item_name: str,
        description: Optional[str] = None,
        position: Optional[int] = None,
        required: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new checklist item for a ticket.

        Args:
            ticket_id: ID of the ticket
            item_name: Name/title of the checklist item
            description: Optional detailed description
            position: Display position/order (lower numbers appear first)
            required: Whether this item must be completed
            **kwargs: Additional fields

        Returns:
            Created checklist item data
        """
        item_data = {
            "TicketID": ticket_id,
            "Name": item_name,
            "IsCompleted": False,
            "IsRequired": required,
            **kwargs,
        }

        if description:
            item_data["Description"] = description
        if position is not None:
            item_data["Position"] = position

        return self.create(item_data)

    def get_checklist_items_by_ticket(
        self,
        ticket_id: int,
        completed_only: bool = False,
        pending_only: bool = False,
    ) -> EntityList:
        """
        Get all checklist items for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            completed_only: Return only completed items
            pending_only: Return only incomplete items

        Returns:
            List of checklist items for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]

        if completed_only:
            filters.append({"field": "IsCompleted", "op": "eq", "value": True})
        elif pending_only:
            filters.append({"field": "IsCompleted", "op": "eq", "value": False})

        return self.query_all(filters=filters)

    def complete_checklist_item(
        self,
        item_id: int,
        completed_by_resource_id: Optional[int] = None,
        completion_notes: Optional[str] = None,
        **kwargs,
    ) -> Optional[EntityDict]:
        """
        Mark a checklist item as completed.

        Args:
            item_id: Checklist item ID
            completed_by_resource_id: ID of resource who completed the item
            completion_notes: Optional completion notes
            **kwargs: Additional fields

        Returns:
            Updated checklist item record or None if failed
        """
        update_data = {
            "id": item_id,
            "IsCompleted": True,
            "CompletedDateTime": datetime.now().isoformat(),
            **kwargs,
        }

        if completed_by_resource_id:
            update_data["CompletedByResourceID"] = completed_by_resource_id
        if completion_notes:
            update_data["CompletionNotes"] = completion_notes

        return self.update(update_data)

    def uncomplete_checklist_item(
        self, item_id: int, reason: Optional[str] = None
    ) -> Optional[EntityDict]:
        """
        Mark a checklist item as incomplete.

        Args:
            item_id: Checklist item ID
            reason: Optional reason for uncompleting

        Returns:
            Updated checklist item record or None if failed
        """
        update_data = {
            "id": item_id,
            "IsCompleted": False,
            "CompletedDateTime": None,
            "CompletedByResourceID": None,
        }

        if reason:
            update_data["CompletionNotes"] = f"Uncompleted: {reason}"

        return self.update(update_data)

    def assign_checklist_item(
        self,
        item_id: int,
        assigned_resource_id: int,
        due_date: Optional[str] = None,
        **kwargs,
    ) -> Optional[EntityDict]:
        """
        Assign a checklist item to a resource.

        Args:
            item_id: Checklist item ID
            assigned_resource_id: ID of resource to assign to
            due_date: Optional due date (ISO format)
            **kwargs: Additional fields

        Returns:
            Updated checklist item record or None if failed
        """
        update_data = {
            "id": item_id,
            "AssignedResourceID": assigned_resource_id,
            **kwargs,
        }

        if due_date:
            update_data["DueDate"] = due_date

        return self.update(update_data)

    def get_checklist_progress(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get completion progress for a ticket's checklist.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with checklist progress information
        """
        items = self.get_checklist_items_by_ticket(ticket_id)

        total_items = len(items)
        completed_items = len([item for item in items if item.get("IsCompleted")])
        required_items = len([item for item in items if item.get("IsRequired")])
        completed_required = len(
            [
                item
                for item in items
                if item.get("IsCompleted") and item.get("IsRequired")
            ]
        )

        progress_percentage = (
            (completed_items / total_items * 100) if total_items > 0 else 100
        )
        required_percentage = (
            (completed_required / required_items * 100) if required_items > 0 else 100
        )

        return {
            "ticket_id": ticket_id,
            "total_items": total_items,
            "completed_items": completed_items,
            "pending_items": total_items - completed_items,
            "required_items": required_items,
            "completed_required": completed_required,
            "progress_percentage": round(progress_percentage, 1),
            "required_percentage": round(required_percentage, 1),
            "all_required_complete": completed_required == required_items,
            "checklist_complete": completed_items == total_items,
        }

    def bulk_create_checklist_items(
        self,
        ticket_id: int,
        items: List[Dict[str, Any]],
    ) -> List[EntityDict]:
        """
        Create multiple checklist items for a ticket in bulk.

        Args:
            ticket_id: Ticket ID
            items: List of item dictionaries, each containing:
                - name: Item name (required)
                - description: Item description (optional)
                - position: Display position (optional)
                - required: Whether required (optional, defaults to False)
                - other optional fields

        Returns:
            List of created checklist item records
        """
        results = []

        for i, item in enumerate(items):
            try:
                checklist_item = self.create_checklist_item(
                    ticket_id=ticket_id,
                    item_name=item["name"],
                    description=item.get("description"),
                    position=item.get("position", i + 1),
                    required=item.get("required", False),
                    **{
                        k: v
                        for k, v in item.items()
                        if k not in ["name", "description", "position", "required"]
                    },
                )
                results.append(checklist_item)
            except Exception as e:
                self.logger.error(
                    f"Failed to create checklist item '{item.get('name')}' "
                    f"for ticket {ticket_id}: {e}"
                )

        return results

    def reorder_checklist_items(
        self,
        ticket_id: int,
        item_position_map: Dict[int, int],
    ) -> List[EntityDict]:
        """
        Reorder checklist items by updating their positions.

        Args:
            ticket_id: Ticket ID
            item_position_map: Dictionary mapping item_id to new position

        Returns:
            List of updated checklist item records
        """
        results = []

        for item_id, new_position in item_position_map.items():
            try:
                updated_item = self.update(
                    {
                        "id": item_id,
                        "Position": new_position,
                    }
                )
                if updated_item:
                    results.append(updated_item)
            except Exception as e:
                self.logger.error(
                    f"Failed to reorder checklist item {item_id} "
                    f"to position {new_position}: {e}"
                )

        return results

    def get_overdue_checklist_items(
        self,
        ticket_id: Optional[int] = None,
        assigned_resource_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get checklist items that are past their due date.

        Args:
            ticket_id: Optional ticket ID filter
            assigned_resource_id: Optional assigned resource filter

        Returns:
            List of overdue checklist items
        """
        filters = [{"field": "IsCompleted", "op": "eq", "value": False}]

        if ticket_id:
            filters.append({"field": "TicketID", "op": "eq", "value": str(ticket_id)})
        if assigned_resource_id:
            filters.append(
                {
                    "field": "AssignedResourceID",
                    "op": "eq",
                    "value": str(assigned_resource_id),
                }
            )

        items = self.query_all(filters=filters)
        current_date = datetime.now().date()

        overdue_items = []
        for item in items:
            if "DueDate" in item and item["DueDate"]:
                try:
                    due_date = datetime.fromisoformat(
                        item["DueDate"].replace("Z", "+00:00")
                    ).date()
                    if due_date < current_date:
                        overdue_items.append(item)
                except (ValueError, TypeError):
                    # Skip if date parsing fails
                    continue

        return overdue_items

    def get_assigned_items_by_resource(
        self,
        resource_id: int,
        include_completed: bool = False,
    ) -> EntityList:
        """
        Get checklist items assigned to a specific resource.

        Args:
            resource_id: Resource ID
            include_completed: Whether to include completed items

        Returns:
            List of assigned checklist items
        """
        filters = [
            {"field": "AssignedResourceID", "op": "eq", "value": str(resource_id)}
        ]

        if not include_completed:
            filters.append({"field": "IsCompleted", "op": "eq", "value": False})

        return self.query_all(filters=filters)

    def copy_checklist_to_ticket(
        self,
        source_ticket_id: int,
        target_ticket_id: int,
        copy_completion_status: bool = False,
    ) -> List[EntityDict]:
        """
        Copy checklist items from one ticket to another.

        Args:
            source_ticket_id: Source ticket ID
            target_ticket_id: Target ticket ID
            copy_completion_status: Whether to copy completion status

        Returns:
            List of created checklist items in target ticket
        """
        source_items = self.get_checklist_items_by_ticket(source_ticket_id)
        new_items = []

        for item in source_items:
            new_item_data = {
                "name": item.get("Name"),
                "description": item.get("Description"),
                "position": item.get("Position"),
                "required": item.get("IsRequired", False),
            }

            # Copy completion status if requested
            if copy_completion_status:
                new_item_data.update(
                    {
                        "IsCompleted": item.get("IsCompleted", False),
                        "CompletedDateTime": item.get("CompletedDateTime"),
                        "CompletedByResourceID": item.get("CompletedByResourceID"),
                        "CompletionNotes": item.get("CompletionNotes"),
                    }
                )

            try:
                new_item = self.create_checklist_item(target_ticket_id, **new_item_data)
                new_items.append(new_item)
            except Exception as e:
                self.logger.error(
                    f"Failed to copy checklist item '{item.get('Name')}' "
                    f"from ticket {source_ticket_id} to {target_ticket_id}: {e}"
                )

        return new_items

    def get_checklist_completion_statistics(
        self,
        ticket_id: int,
        include_resource_stats: bool = True,
    ) -> Dict[str, Any]:
        """
        Get detailed completion statistics for a ticket's checklist.

        Args:
            ticket_id: Ticket ID
            include_resource_stats: Include per-resource completion stats

        Returns:
            Dictionary with detailed completion statistics
        """
        items = self.get_checklist_items_by_ticket(ticket_id)

        stats = {
            "ticket_id": ticket_id,
            "total_items": len(items),
            "completed_count": 0,
            "pending_count": 0,
            "required_count": 0,
            "completed_required_count": 0,
            "overdue_count": 0,
            "assigned_count": 0,
            "unassigned_count": 0,
            "completion_times": [],
        }

        resource_stats = {}
        current_date = datetime.now().date()

        for item in items:
            is_completed = item.get("IsCompleted", False)
            is_required = item.get("IsRequired", False)
            assigned_resource = item.get("AssignedResourceID")

            # Basic counts
            if is_completed:
                stats["completed_count"] += 1
            else:
                stats["pending_count"] += 1

            if is_required:
                stats["required_count"] += 1
                if is_completed:
                    stats["completed_required_count"] += 1

            if assigned_resource:
                stats["assigned_count"] += 1
            else:
                stats["unassigned_count"] += 1

            # Check if overdue
            if not is_completed and "DueDate" in item and item["DueDate"]:
                try:
                    due_date = datetime.fromisoformat(
                        item["DueDate"].replace("Z", "+00:00")
                    ).date()
                    if due_date < current_date:
                        stats["overdue_count"] += 1
                except (ValueError, TypeError):
                    pass

            # Calculate completion time
            if (
                is_completed
                and "CompletedDateTime" in item
                and "CreateDateTime" in item
            ):
                try:
                    completed_date = datetime.fromisoformat(
                        item["CompletedDateTime"].replace("Z", "+00:00")
                    )
                    created_date = datetime.fromisoformat(
                        item["CreateDateTime"].replace("Z", "+00:00")
                    )
                    completion_time = (
                        completed_date - created_date
                    ).total_seconds() / 3600
                    stats["completion_times"].append(completion_time)
                except (ValueError, TypeError):
                    pass

            # Resource statistics
            if include_resource_stats and assigned_resource:
                if assigned_resource not in resource_stats:
                    resource_stats[assigned_resource] = {
                        "assigned": 0,
                        "completed": 0,
                        "pending": 0,
                        "overdue": 0,
                    }

                resource_stats[assigned_resource]["assigned"] += 1
                if is_completed:
                    resource_stats[assigned_resource]["completed"] += 1
                else:
                    resource_stats[assigned_resource]["pending"] += 1

        # Calculate averages and percentages
        if stats["completion_times"]:
            stats["avg_completion_time_hours"] = sum(stats["completion_times"]) / len(
                stats["completion_times"]
            )
        else:
            stats["avg_completion_time_hours"] = None

        stats["completion_percentage"] = (
            stats["completed_count"] / stats["total_items"] * 100
            if stats["total_items"] > 0
            else 100
        )

        stats["required_completion_percentage"] = (
            stats["completed_required_count"] / stats["required_count"] * 100
            if stats["required_count"] > 0
            else 100
        )

        if include_resource_stats:
            stats["resource_statistics"] = resource_stats

        return stats
