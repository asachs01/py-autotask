"""
Ticket Checklist Libraries entity for Autotask API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TicketChecklistLibrariesEntity(BaseEntity):
    """
    Handles Ticket Checklist Libraries operations for the Autotask API.

    Manages reusable checklist templates that can be applied to tickets,
    providing standardized workflows and procedures for common ticket types.
    """

    def __init__(self, client, entity_name: str = "TicketChecklistLibraries"):
        super().__init__(client, entity_name)

    def create_checklist_library(
        self,
        name: str,
        description: Optional[str] = None,
        ticket_category_id: Optional[int] = None,
        is_active: bool = True,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new checklist library template.

        Args:
            name: Name of the checklist library
            description: Optional description
            ticket_category_id: Optional associated ticket category
            is_active: Whether the library is active for use
            **kwargs: Additional fields

        Returns:
            Created checklist library data
        """
        library_data = {
            "Name": name,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            library_data["Description"] = description
        if ticket_category_id:
            library_data["TicketCategoryID"] = ticket_category_id

        return self.create(library_data)

    def get_active_libraries(
        self, ticket_category_id: Optional[int] = None
    ) -> EntityList:
        """
        Get all active checklist libraries.

        Args:
            ticket_category_id: Optional filter by ticket category

        Returns:
            List of active checklist libraries
        """
        filters = [{"field": "IsActive", "op": "eq", "value": True}]

        if ticket_category_id:
            filters.append(
                {
                    "field": "TicketCategoryID",
                    "op": "eq",
                    "value": str(ticket_category_id),
                }
            )

        return self.query_all(filters=filters)

    def get_library_by_name(self, name: str, exact_match: bool = True) -> EntityList:
        """
        Search for checklist libraries by name.

        Args:
            name: Library name to search for
            exact_match: Whether to use exact match or partial match

        Returns:
            List of matching libraries
        """
        if exact_match:
            filters = [{"field": "Name", "op": "eq", "value": name}]
        else:
            filters = [{"field": "Name", "op": "contains", "value": name}]

        return self.query_all(filters=filters)

    def apply_library_to_ticket(
        self,
        library_id: int,
        ticket_id: int,
        override_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Apply a checklist library template to a ticket.

        Note: This method would typically integrate with TicketChecklistItems
        to create the actual checklist items from the library template.

        Args:
            library_id: ID of the checklist library to apply
            ticket_id: ID of the target ticket
            override_existing: Whether to replace existing checklist items

        Returns:
            Dictionary with application results
        """
        library = self.get(library_id)
        if not library:
            return {
                "success": False,
                "error": f"Library with ID {library_id} not found",
            }

        # Get library template items (would need TicketChecklistLibraryItems entity)
        # For now, return a placeholder response
        result = {
            "success": True,
            "library_id": library_id,
            "library_name": library.get("Name"),
            "ticket_id": ticket_id,
            "items_created": 0,
            "override_existing": override_existing,
            "applied_datetime": datetime.now().isoformat(),
        }

        self.logger.info(
            f"Applied checklist library '{library.get('Name')}' to ticket {ticket_id}"
        )

        return result

    def clone_library(
        self,
        source_library_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Clone an existing checklist library.

        Args:
            source_library_id: ID of library to clone
            new_name: Name for the new library
            new_description: Optional description for new library

        Returns:
            Created library record or None if failed
        """
        source_library = self.get(source_library_id)
        if not source_library:
            self.logger.error(f"Source library {source_library_id} not found")
            return None

        # Create new library with source data
        new_library_data = {
            "name": new_name,
            "description": new_description or source_library.get("Description"),
            "ticket_category_id": source_library.get("TicketCategoryID"),
            "is_active": True,  # New cloned libraries are active by default
        }

        try:
            new_library = self.create_checklist_library(**new_library_data)

            # TODO: Clone library items (would need TicketChecklistLibraryItems entity)

            self.logger.info(
                f"Cloned library '{source_library.get('Name')}' to '{new_name}'"
            )

            return new_library
        except Exception as e:
            self.logger.error(f"Failed to clone library: {e}")
            return None

    def deactivate_library(
        self, library_id: int, reason: Optional[str] = None
    ) -> Optional[EntityDict]:
        """
        Deactivate a checklist library.

        Args:
            library_id: Library ID to deactivate
            reason: Optional reason for deactivation

        Returns:
            Updated library record or None if failed
        """
        update_data = {
            "id": library_id,
            "IsActive": False,
        }

        if reason:
            # Assuming there's a notes or reason field
            update_data["DeactivationReason"] = reason

        return self.update(update_data)

    def activate_library(self, library_id: int) -> Optional[EntityDict]:
        """
        Activate a checklist library.

        Args:
            library_id: Library ID to activate

        Returns:
            Updated library record or None if failed
        """
        update_data = {
            "id": library_id,
            "IsActive": True,
        }

        return self.update(update_data)

    def get_library_usage_statistics(
        self, library_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a checklist library.

        Note: This would require integration with ticket data to track actual usage.

        Args:
            library_id: Library ID
            days: Number of days to analyze

        Returns:
            Dictionary with usage statistics
        """
        library = self.get(library_id)
        if not library:
            return {"error": f"Library with ID {library_id} not found"}

        # Placeholder statistics - would need actual usage tracking
        stats = {
            "library_id": library_id,
            "library_name": library.get("Name"),
            "analysis_period_days": days,
            "times_applied": 0,  # Would query actual usage
            "associated_tickets": [],
            "success_rate": 0.0,
            "avg_completion_time": None,
            "last_used": None,
            "created_date": library.get("CreateDateTime"),
        }

        return stats

    def search_libraries_by_criteria(
        self,
        search_criteria: Dict[str, Any],
    ) -> EntityList:
        """
        Search libraries by multiple criteria.

        Args:
            search_criteria: Dictionary with search parameters:
                - name: Partial name match
                - category_id: Ticket category filter
                - is_active: Active status filter
                - created_after: Created after date (ISO format)
                - created_before: Created before date (ISO format)

        Returns:
            List of matching libraries
        """
        filters = []

        if search_criteria.get("name"):
            filters.append(
                {"field": "Name", "op": "contains", "value": search_criteria["name"]}
            )

        if search_criteria.get("category_id"):
            filters.append(
                {
                    "field": "TicketCategoryID",
                    "op": "eq",
                    "value": str(search_criteria["category_id"]),
                }
            )

        if "is_active" in search_criteria:
            filters.append(
                {"field": "IsActive", "op": "eq", "value": search_criteria["is_active"]}
            )

        if search_criteria.get("created_after"):
            filters.append(
                {
                    "field": "CreateDateTime",
                    "op": "gte",
                    "value": search_criteria["created_after"],
                }
            )

        if search_criteria.get("created_before"):
            filters.append(
                {
                    "field": "CreateDateTime",
                    "op": "lte",
                    "value": search_criteria["created_before"],
                }
            )

        return self.query_all(filters=filters)

    def get_libraries_by_category(self, category_id: int) -> EntityList:
        """
        Get all libraries associated with a specific ticket category.

        Args:
            category_id: Ticket category ID

        Returns:
            List of libraries for the category
        """
        filters = [{"field": "TicketCategoryID", "op": "eq", "value": str(category_id)}]
        return self.query_all(filters=filters)

    def update_library_metadata(
        self,
        library_id: int,
        updates: Dict[str, Any],
    ) -> Optional[EntityDict]:
        """
        Update library metadata (name, description, category, etc.).

        Args:
            library_id: Library ID
            updates: Dictionary of field updates

        Returns:
            Updated library record or None if failed
        """
        update_data = {"id": library_id, **updates}
        return self.update(update_data)

    def get_library_recommendations(
        self,
        ticket_category_id: int,
        ticket_type_id: Optional[int] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get recommended checklist libraries based on ticket attributes.

        Args:
            ticket_category_id: Ticket category ID
            ticket_type_id: Optional ticket type ID
            limit: Maximum number of recommendations

        Returns:
            List of recommended libraries with relevance scores
        """
        # Get libraries for the category
        category_libraries = self.get_libraries_by_category(ticket_category_id)

        recommendations = []

        for library in category_libraries[:limit]:
            if library.get("IsActive"):
                recommendation = {
                    "library_id": library.get("id"),
                    "library_name": library.get("Name"),
                    "description": library.get("Description"),
                    "relevance_score": 100,  # Placeholder - would calculate based on usage patterns
                    "category_match": True,
                    "type_match": ticket_type_id is not None,  # Placeholder logic
                    "usage_count": 0,  # Would get from usage statistics
                    "success_rate": 0.0,  # Would calculate from historical data
                }
                recommendations.append(recommendation)

        # Sort by relevance score (highest first)
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

        return recommendations

    def export_library_template(self, library_id: int) -> Dict[str, Any]:
        """
        Export a library template for backup or sharing.

        Args:
            library_id: Library ID to export

        Returns:
            Dictionary with complete library template data
        """
        library = self.get(library_id)
        if not library:
            return {"error": f"Library with ID {library_id} not found"}

        export_data = {
            "library_metadata": library,
            "export_timestamp": datetime.now().isoformat(),
            "library_items": [],  # Would get from TicketChecklistLibraryItems
            "version": "1.0",
        }

        return export_data

    def import_library_template(
        self,
        template_data: Dict[str, Any],
        new_name: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Import a library template from exported data.

        Args:
            template_data: Exported library template data
            new_name: Optional new name for imported library

        Returns:
            Created library record or None if failed
        """
        if "library_metadata" not in template_data:
            self.logger.error("Invalid template data: missing library_metadata")
            return None

        metadata = template_data["library_metadata"]

        # Create new library from template
        library_data = {
            "name": new_name or f"{metadata.get('Name')} (Imported)",
            "description": metadata.get("Description"),
            "ticket_category_id": metadata.get("TicketCategoryID"),
            "is_active": True,
        }

        try:
            new_library = self.create_checklist_library(**library_data)

            # TODO: Import library items from template_data["library_items"]

            self.logger.info(f"Imported library template as '{library_data['name']}'")

            return new_library
        except Exception as e:
            self.logger.error(f"Failed to import library template: {e}")
            return None
