"""
Notification Templates entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class NotificationTemplatesEntity(BaseEntity):
    """
    Handles all Notification Template-related operations for the Autotask API.

    Notification templates define standardized email templates used for various
    automated notifications throughout the Autotask system, including ticket
    updates, project notifications, and system alerts.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_notification_template(
        self,
        template_name: str,
        subject: str,
        body_template: str,
        template_type: str,
        is_active: bool = True,
        is_system_template: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new notification template.

        Args:
            template_name: Name of the notification template
            subject: Email subject template
            body_template: Email body template (can include merge fields)
            template_type: Type of template (e.g., 'ticket', 'project', 'general')
            is_active: Whether the template is active
            is_system_template: Whether this is a system-level template
            **kwargs: Additional template fields

        Returns:
            Created notification template data
        """
        template_data = {
            "TemplateName": template_name,
            "Subject": subject,
            "BodyTemplate": body_template,
            "TemplateType": template_type,
            "IsActive": is_active,
            "IsSystemTemplate": is_system_template,
            **kwargs,
        }

        return self.create(template_data)

    def get_active_templates(
        self, template_type: Optional[str] = None
    ) -> List[EntityDict]:
        """
        Get all active notification templates, optionally filtered by type.

        Args:
            template_type: Optional template type filter

        Returns:
            List of active notification templates
        """
        filters = [{"field": "IsActive", "op": "eq", "value": "true"}]

        if template_type:
            filters.append(
                {"field": "TemplateType", "op": "eq", "value": template_type}
            )

        return self.query_all(filters=filters)

    def get_templates_by_type(self, template_type: str) -> List[EntityDict]:
        """
        Get notification templates by type.

        Args:
            template_type: Template type to filter by

        Returns:
            List of templates of the specified type
        """
        return self.query_all(
            filters={"field": "TemplateType", "op": "eq", "value": template_type}
        )

    def get_system_templates(self) -> List[EntityDict]:
        """
        Get system-level notification templates.

        Returns:
            List of system notification templates
        """
        return self.query_all(
            filters={"field": "IsSystemTemplate", "op": "eq", "value": "true"}
        )

    def get_user_templates(self) -> List[EntityDict]:
        """
        Get user-created notification templates (non-system).

        Returns:
            List of user-created notification templates
        """
        return self.query_all(
            filters={"field": "IsSystemTemplate", "op": "eq", "value": "false"}
        )

    def search_templates_by_name(self, search_term: str) -> List[EntityDict]:
        """
        Search notification templates by name.

        Args:
            search_term: Term to search for in template names

        Returns:
            List of matching notification templates
        """
        return self.query_all(
            filters={"field": "TemplateName", "op": "contains", "value": search_term}
        )

    def update_template_content(
        self,
        template_id: int,
        subject: Optional[str] = None,
        body_template: Optional[str] = None,
    ) -> EntityDict:
        """
        Update the content of a notification template.

        Args:
            template_id: ID of the template to update
            subject: New email subject template
            body_template: New email body template

        Returns:
            Updated template data
        """
        update_data = {}

        if subject is not None:
            update_data["Subject"] = subject
        if body_template is not None:
            update_data["BodyTemplate"] = body_template

        return self.update_by_id(template_id, update_data)

    def deactivate_template(self, template_id: int) -> EntityDict:
        """
        Deactivate a notification template.

        Args:
            template_id: ID of the template to deactivate

        Returns:
            Updated template data
        """
        return self.update_by_id(template_id, {"IsActive": False})

    def clone_template(
        self,
        source_template_id: int,
        new_name: str,
        new_type: Optional[str] = None,
    ) -> EntityDict:
        """
        Clone an existing notification template.

        Args:
            source_template_id: ID of template to clone
            new_name: Name for the new template
            new_type: Optional new type for the cloned template

        Returns:
            Created cloned template data
        """
        source_template = self.get(source_template_id)
        if not source_template:
            raise ValueError(f"Source template {source_template_id} not found")

        # Create new template with source data
        new_template_data = {
            "TemplateName": new_name,
            "Subject": source_template.get("Subject", ""),
            "BodyTemplate": source_template.get("BodyTemplate", ""),
            "TemplateType": new_type or source_template.get("TemplateType", ""),
            "IsActive": True,
            "IsSystemTemplate": False,  # Cloned templates are always user templates
        }

        return self.create(new_template_data)

    def get_template_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for notification templates.

        Returns:
            Dictionary containing template usage statistics
        """
        all_templates = self.query_all()
        active_templates = [t for t in all_templates if t.get("IsActive")]
        system_templates = [t for t in all_templates if t.get("IsSystemTemplate")]

        # Group by type
        by_type = {}
        for template in active_templates:
            template_type = template.get("TemplateType", "unspecified")
            if template_type not in by_type:
                by_type[template_type] = []
            by_type[template_type].append(template)

        return {
            "total_templates": len(all_templates),
            "active_templates": len(active_templates),
            "inactive_templates": len(all_templates) - len(active_templates),
            "system_templates": len(system_templates),
            "user_templates": len(all_templates) - len(system_templates),
            "templates_by_type": {
                type_name: len(templates) for type_name, templates in by_type.items()
            },
            "available_types": list(by_type.keys()),
        }

    def validate_template_merge_fields(
        self, template_id: int, available_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Validate merge fields used in a template against available fields.

        Args:
            template_id: Template ID to validate
            available_fields: List of available merge field names

        Returns:
            Dictionary containing validation results
        """
        template = self.get(template_id)
        if not template:
            return {"error": "Template not found"}

        import re

        subject = template.get("Subject", "")
        body = template.get("BodyTemplate", "")

        # Find merge fields in template (assuming format like {FieldName} or [FieldName])
        merge_field_pattern = r"[{\[]([^}\]]+)[}\]]"

        subject_fields = set(re.findall(merge_field_pattern, subject))
        body_fields = set(re.findall(merge_field_pattern, body))

        used_fields = subject_fields.union(body_fields)
        available_set = set(available_fields)

        valid_fields = used_fields.intersection(available_set)
        invalid_fields = used_fields - available_set

        return {
            "template_id": template_id,
            "template_name": template.get("TemplateName", ""),
            "validation_results": {
                "total_merge_fields": len(used_fields),
                "valid_fields": sorted(list(valid_fields)),
                "invalid_fields": sorted(list(invalid_fields)),
                "is_valid": len(invalid_fields) == 0,
            },
            "field_usage": {
                "subject_fields": sorted(list(subject_fields)),
                "body_fields": sorted(list(body_fields)),
            },
        }
