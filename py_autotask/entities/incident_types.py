"""
IncidentTypes Entity for py-autotask

This module provides the IncidentTypesEntity class for managing incident types
in Autotask. Incident types help categorize and classify incidents for proper
handling, escalation, and reporting.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class IncidentTypesEntity(BaseEntity):
    """
    Manages Autotask IncidentTypes - incident classification and categorization.

    Incident types help categorize incidents for proper handling, escalation,
    priority determination, and reporting within Autotask service desk operations.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "IncidentTypes"

    def create_incident_type(
        self,
        name: str,
        description: str,
        severity_level: str,
        default_priority: str,
        escalation_minutes: int = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new incident type.

        Args:
            name: Name of the incident type
            description: Description of the incident type
            severity_level: Severity level (Critical, High, Medium, Low)
            default_priority: Default priority for this incident type
            escalation_minutes: Minutes before escalation
            **kwargs: Additional fields for the incident type

        Returns:
            Create response with new incident type ID
        """
        incident_type_data = {
            "name": name,
            "description": description,
            "severityLevel": severity_level,
            "defaultPriority": default_priority,
            "escalationMinutes": escalation_minutes,
            "isActive": True,
            **kwargs,
        }

        return self.create(incident_type_data)

    def get_active_incident_types(
        self, severity_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active incident types.

        Args:
            severity_level: Optional severity level to filter by

        Returns:
            List of active incident types
        """
        filters = ["isActive eq true"]

        if severity_level:
            filters.append(f"severityLevel eq '{severity_level}'")

        return self.query(filter=" and ".join(filters))

    def get_incident_types_by_severity(
        self, severity_level: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get incident types by severity level.

        Args:
            severity_level: Severity level to filter by
            active_only: Whether to only return active incident types

        Returns:
            List of incident types with the specified severity
        """
        filters = [f"severityLevel eq '{severity_level}'"]

        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def get_critical_incident_types(self) -> List[Dict[str, Any]]:
        """
        Get all critical incident types.

        Returns:
            List of critical incident types
        """
        return self.get_incident_types_by_severity("Critical")

    def get_incident_type_statistics(
        self,
        incident_type_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics for an incident type.

        Args:
            incident_type_id: ID of the incident type
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            Incident type statistics
        """
        # This would typically query related incidents
        # For now, return statistics structure

        incident_type = self.get(incident_type_id)

        return {
            "incident_type_id": incident_type_id,
            "name": incident_type.get("name"),
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "statistics": {
                "total_incidents": 0,  # Would count related incidents
                "open_incidents": 0,  # Would count open incidents
                "resolved_incidents": 0,  # Would count resolved incidents
                "average_resolution_time": 0.0,  # Would calculate avg resolution time
                "escalation_rate": 0.0,  # Would calculate escalation percentage
                "customer_satisfaction": 0.0,  # Would calculate satisfaction scores
            },
        }

    def get_incident_type_escalation_rules(
        self, incident_type_id: int
    ) -> Dict[str, Any]:
        """
        Get escalation rules for an incident type.

        Args:
            incident_type_id: ID of the incident type

        Returns:
            Escalation rules for the incident type
        """
        incident_type = self.get(incident_type_id)

        return {
            "incident_type_id": incident_type_id,
            "name": incident_type.get("name"),
            "escalation_rules": {
                "escalation_minutes": incident_type.get("escalationMinutes", 0),
                "automatic_escalation": incident_type.get("automaticEscalation", False),
                "escalation_path": [],  # Would contain escalation hierarchy
                "notification_rules": [],  # Would contain notification settings
            },
        }

    def activate_incident_type(self, incident_type_id: int) -> Dict[str, Any]:
        """
        Activate an incident type.

        Args:
            incident_type_id: ID of the incident type to activate

        Returns:
            Update response
        """
        return self.update(incident_type_id, {"isActive": True})

    def deactivate_incident_type(self, incident_type_id: int) -> Dict[str, Any]:
        """
        Deactivate an incident type.

        Args:
            incident_type_id: ID of the incident type to deactivate

        Returns:
            Update response
        """
        return self.update(incident_type_id, {"isActive": False})

    def clone_incident_type(
        self,
        source_incident_type_id: int,
        new_name: str,
        new_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a copy of an existing incident type.

        Args:
            source_incident_type_id: ID of the incident type to clone
            new_name: Name for the new incident type
            new_description: Description for the new incident type

        Returns:
            Create response for the new incident type
        """
        source_incident_type = self.get(source_incident_type_id)

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_incident_type.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        clone_data["isActive"] = True
        if new_description:
            clone_data["description"] = new_description

        return self.create(clone_data)

    def update_escalation_time(
        self, incident_type_id: int, escalation_minutes: int
    ) -> Dict[str, Any]:
        """
        Update escalation time for an incident type.

        Args:
            incident_type_id: ID of the incident type
            escalation_minutes: New escalation time in minutes

        Returns:
            Update response
        """
        return self.update(incident_type_id, {"escalationMinutes": escalation_minutes})

    def get_incident_types_summary(self) -> Dict[str, Any]:
        """
        Get summary of all incident types.

        Returns:
            Summary of incident types by various categories
        """
        incident_types = self.query()

        # Group by severity level
        severity_groups = {}
        priority_groups = {}

        for incident_type in incident_types:
            severity = incident_type.get("severityLevel", "Unknown")
            priority = incident_type.get("defaultPriority", "Unknown")

            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(incident_type)

            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(incident_type)

        active_count = len([it for it in incident_types if it.get("isActive")])
        inactive_count = len(incident_types) - active_count

        return {
            "total_incident_types": len(incident_types),
            "active_incident_types": active_count,
            "inactive_incident_types": inactive_count,
            "by_severity": {
                severity: len(types) for severity, types in severity_groups.items()
            },
            "by_priority": {
                priority: len(types) for priority, types in priority_groups.items()
            },
            "severity_distribution": severity_groups,
            "priority_distribution": priority_groups,
        }

    def bulk_update_escalation_times(
        self, escalation_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update escalation times for multiple incident types.

        Args:
            escalation_updates: List of updates
                Each should contain: incident_type_id, escalation_minutes

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in escalation_updates:
            incident_type_id = update["incident_type_id"]
            escalation_minutes = update["escalation_minutes"]

            try:
                result = self.update_escalation_time(
                    incident_type_id, escalation_minutes
                )
                results.append(
                    {"id": incident_type_id, "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"id": incident_type_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(escalation_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }
