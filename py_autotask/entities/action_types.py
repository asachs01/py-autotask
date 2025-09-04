"""
Action Types entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class ActionTypesEntity(BaseEntity):
    """
    Handles Action Type operations for the Autotask API.

    Manages the different types of actions that can be performed
    in Autotask workflows and automation processes.
    """

    def __init__(self, client, entity_name: str = "ActionTypes"):
        super().__init__(client, entity_name)

    def get_all_action_types(self, active_only: bool = True) -> EntityList:
        """
        Get all action types available in the system.

        Args:
            active_only: Whether to include only active action types

        Returns:
            List of action types
        """
        filters = []
        if active_only:
            filters = [{"field": "IsActive", "op": "eq", "value": "true"}]

        return self.query_all(filters=filters)

    def get_action_types_by_category(
        self, category: str, active_only: bool = True
    ) -> EntityList:
        """
        Get action types filtered by category.

        Args:
            category: Action type category
            active_only: Whether to include only active types

        Returns:
            List of action types in the category
        """
        filters = [{"field": "Category", "op": "eq", "value": category}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def search_action_types_by_name(self, name_pattern: str) -> EntityList:
        """
        Search action types by name pattern.

        Args:
            name_pattern: Name pattern to search for

        Returns:
            List of matching action types
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]
        return self.query_all(filters=filters)

    def get_action_type_details(self, action_type_id: int) -> Optional[EntityDict]:
        """
        Get detailed information about a specific action type.

        Args:
            action_type_id: Action type ID

        Returns:
            Action type details or None if not found
        """
        return self.get(action_type_id)

    def get_workflow_compatible_types(
        self, workflow_type: str = "ticket"
    ) -> EntityList:
        """
        Get action types compatible with specific workflow types.

        Args:
            workflow_type: Type of workflow (ticket, project, etc.)

        Returns:
            List of compatible action types
        """
        # This would typically filter based on compatibility fields
        # For now, we'll return all active types and let caller filter
        filters = [
            {"field": "IsActive", "op": "eq", "value": "true"},
            {"field": "WorkflowType", "op": "contains", "value": workflow_type},
        ]

        return self.query_all(filters=filters)

    def validate_action_type_configuration(
        self, action_type_id: int, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate configuration parameters for an action type.

        Args:
            action_type_id: Action type ID
            configuration: Configuration parameters to validate

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "required_fields": [],
        }

        action_type = self.get_action_type_details(action_type_id)
        if not action_type:
            result["valid"] = False
            result["errors"].append("Action type not found")
            return result

        # Basic validation logic
        # In a real implementation, this would check against action type schema
        action_name = action_type.get("Name", "").lower()

        if "email" in action_name:
            # Email action validation
            if "recipient" not in configuration:
                result["required_fields"].append("recipient")
            if "subject" not in configuration:
                result["required_fields"].append("subject")

        elif "webhook" in action_name:
            # Webhook action validation
            if "url" not in configuration:
                result["required_fields"].append("url")
            if "method" not in configuration:
                result["required_fields"].append("method")

        elif "assignment" in action_name:
            # Assignment action validation
            if "resource_id" not in configuration and "queue_id" not in configuration:
                result["warnings"].append(
                    "Either resource_id or queue_id should be specified"
                )

        # Check for missing required fields
        if result["required_fields"]:
            result["valid"] = False
            result["errors"].append(
                f"Missing required fields: {', '.join(result['required_fields'])}"
            )

        return result

    def get_action_type_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about action types in the system.

        Returns:
            Dictionary with action type statistics
        """
        all_types = self.query_all()
        active_types = self.get_all_action_types(active_only=True)

        stats = {
            "total_action_types": len(all_types),
            "active_action_types": len(active_types),
            "inactive_action_types": len(all_types) - len(active_types),
            "by_category": {},
            "by_workflow_type": {},
        }

        for action_type in all_types:
            # Count by category
            category = action_type.get("Category", "unknown")
            if category not in stats["by_category"]:
                stats["by_category"][category] = {"total": 0, "active": 0}
            stats["by_category"][category]["total"] += 1

            if action_type.get("IsActive", True):
                stats["by_category"][category]["active"] += 1

            # Count by workflow type
            workflow_type = action_type.get("WorkflowType", "unknown")
            if workflow_type not in stats["by_workflow_type"]:
                stats["by_workflow_type"][workflow_type] = 0
            stats["by_workflow_type"][workflow_type] += 1

        return stats

    def get_commonly_used_action_types(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most commonly used action types.

        Note: This would typically require usage statistics from workflows/automations.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of commonly used action types with usage info
        """
        # This is a placeholder implementation
        # In practice, this would query usage statistics
        active_types = self.get_all_action_types(active_only=True)

        # Sort by name for consistent results (placeholder for usage count)
        sorted_types = sorted(active_types, key=lambda x: x.get("Name", ""))

        result = []
        for action_type in sorted_types[:limit]:
            result.append(
                {
                    "action_type": action_type,
                    "usage_count": 0,  # Placeholder - would be actual usage
                    "last_used": None,  # Placeholder - would be actual date
                }
            )

        return result

    def get_deprecated_action_types(self) -> EntityList:
        """
        Get action types that are marked as deprecated.

        Returns:
            List of deprecated action types
        """
        filters = [{"field": "IsDeprecated", "op": "eq", "value": "true"}]
        return self.query_all(filters=filters)

    def create_custom_action_type(
        self,
        name: str,
        description: str,
        category: str,
        workflow_type: str,
        configuration_schema: Dict[str, Any],
        **kwargs,
    ) -> EntityDict:
        """
        Create a custom action type (if supported by API).

        Args:
            name: Action type name
            description: Description of the action
            category: Action category
            workflow_type: Compatible workflow type
            configuration_schema: Schema for configuration parameters
            **kwargs: Additional fields

        Returns:
            Created action type data
        """
        action_data = {
            "Name": name,
            "Description": description,
            "Category": category,
            "WorkflowType": workflow_type,
            "ConfigurationSchema": configuration_schema,
            "IsActive": True,
            "IsCustom": True,
            **kwargs,
        }

        return self.create(action_data)
