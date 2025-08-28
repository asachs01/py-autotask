"""
Ticket History entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityList
from .base import BaseEntity


class TicketHistoryEntity(BaseEntity):
    """
    Handles Ticket History operations for the Autotask API.

    Manages the audit trail and change history for tickets, tracking all
    modifications, status changes, assignments, and other ticket activities
    for compliance and analysis purposes.
    """

    def __init__(self, client, entity_name: str = "TicketHistory"):
        super().__init__(client, entity_name)

    def get_history_by_ticket(
        self,
        ticket_id: int,
        field_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> EntityList:
        """
        Get history entries for a specific ticket.

        Args:
            ticket_id: Ticket ID to filter by
            field_name: Optional filter by specific field changes
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            List of history entries for the ticket
        """
        filters = [{"field": "TicketID", "op": "eq", "value": str(ticket_id)}]

        if field_name:
            filters.append({"field": "FieldName", "op": "eq", "value": field_name})

        if start_date:
            filters.append(
                {"field": "ChangeDateTime", "op": "gte", "value": start_date}
            )

        if end_date:
            filters.append({"field": "ChangeDateTime", "op": "lte", "value": end_date})

        return self.query_all(filters=filters)

    def get_history_by_resource(
        self,
        resource_id: int,
        days: int = 30,
        ticket_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get history entries for changes made by a specific resource.

        Args:
            resource_id: Resource ID who made the changes
            days: Number of days to look back
            ticket_id: Optional filter by specific ticket

        Returns:
            List of history entries made by the resource
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        filters = [
            {"field": "ChangedByResourceID", "op": "eq", "value": str(resource_id)},
            {"field": "ChangeDateTime", "op": "gte", "value": start_date.isoformat()},
        ]

        if ticket_id:
            filters.append({"field": "TicketID", "op": "eq", "value": str(ticket_id)})

        return self.query_all(filters=filters)

    def get_field_change_history(
        self,
        ticket_id: int,
        field_name: str,
    ) -> EntityList:
        """
        Get complete change history for a specific field on a ticket.

        Args:
            ticket_id: Ticket ID
            field_name: Name of the field to track

        Returns:
            List of history entries for the field, ordered by date
        """
        filters = [
            {"field": "TicketID", "op": "eq", "value": str(ticket_id)},
            {"field": "FieldName", "op": "eq", "value": field_name},
        ]

        history = self.query_all(filters=filters)

        # Sort by change date if available
        try:
            history.sort(key=lambda x: x.get("ChangeDateTime", ""), reverse=True)
        except (TypeError, ValueError):
            pass

        return history

    def get_status_change_timeline(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get a timeline of status changes for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            List of status change events with timeline information
        """
        status_history = self.get_field_change_history(ticket_id, "Status")

        timeline = []
        for entry in status_history:
            timeline_entry = {
                "change_date": entry.get("ChangeDateTime"),
                "changed_by_resource_id": entry.get("ChangedByResourceID"),
                "old_status": entry.get("OldValue"),
                "new_status": entry.get("NewValue"),
                "duration_in_status": None,  # Will be calculated below
                "entry_id": entry.get("id"),
            }
            timeline.append(timeline_entry)

        # Calculate duration in each status
        for i, entry in enumerate(timeline):
            if i < len(timeline) - 1:
                try:
                    current_date = datetime.fromisoformat(
                        entry["change_date"].replace("Z", "+00:00")
                    )
                    next_date = datetime.fromisoformat(
                        timeline[i + 1]["change_date"].replace("Z", "+00:00")
                    )
                    duration = (current_date - next_date).total_seconds() / 3600
                    entry["duration_hours"] = round(duration, 2)
                except (ValueError, TypeError, AttributeError):
                    entry["duration_hours"] = None

        return timeline

    def get_assignment_change_history(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get history of assignment changes for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            List of assignment change events
        """
        assignment_fields = [
            "AssignedResourceID",
            "QueueID",
            "AssignedResourceGroupID",
        ]

        assignment_history = []

        for field in assignment_fields:
            field_history = self.get_field_change_history(ticket_id, field)

            for entry in field_history:
                assignment_event = {
                    "change_date": entry.get("ChangeDateTime"),
                    "changed_by_resource_id": entry.get("ChangedByResourceID"),
                    "assignment_type": field,
                    "old_value": entry.get("OldValue"),
                    "new_value": entry.get("NewValue"),
                    "entry_id": entry.get("id"),
                }
                assignment_history.append(assignment_event)

        # Sort by date
        try:
            assignment_history.sort(
                key=lambda x: x.get("change_date", ""), reverse=True
            )
        except (TypeError, ValueError):
            pass

        return assignment_history

    def get_priority_escalation_history(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get history of priority changes and escalations.

        Args:
            ticket_id: Ticket ID

        Returns:
            List of priority change events
        """
        priority_history = self.get_field_change_history(ticket_id, "Priority")

        escalations = []
        for entry in priority_history:
            old_priority = entry.get("OldValue")
            new_priority = entry.get("NewValue")

            # Determine if this was an escalation (lower number = higher priority)
            escalation_type = "Unknown"
            if old_priority and new_priority:
                try:
                    old_val = int(old_priority)
                    new_val = int(new_priority)
                    if new_val < old_val:
                        escalation_type = "Escalated"
                    elif new_val > old_val:
                        escalation_type = "De-escalated"
                    else:
                        escalation_type = "No Change"
                except (ValueError, TypeError):
                    pass

            escalation = {
                "change_date": entry.get("ChangeDateTime"),
                "changed_by_resource_id": entry.get("ChangedByResourceID"),
                "old_priority": old_priority,
                "new_priority": new_priority,
                "escalation_type": escalation_type,
                "entry_id": entry.get("id"),
            }
            escalations.append(escalation)

        return escalations

    def get_ticket_activity_summary(
        self,
        ticket_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get activity summary for a ticket over a specified period.

        Args:
            ticket_id: Ticket ID
            days: Number of days to analyze

        Returns:
            Dictionary with activity summary
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        history = self.get_history_by_ticket(
            ticket_id, start_date=start_date.isoformat(), end_date=end_date.isoformat()
        )

        summary = {
            "ticket_id": ticket_id,
            "period_days": days,
            "total_changes": len(history),
            "unique_resources": set(),
            "fields_changed": set(),
            "change_types": {},
            "most_active_day": None,
            "change_frequency": 0.0,
        }

        changes_by_date = {}

        for entry in history:
            # Track unique resources
            resource_id = entry.get("ChangedByResourceID")
            if resource_id:
                summary["unique_resources"].add(resource_id)

            # Track fields changed
            field_name = entry.get("FieldName")
            if field_name:
                summary["fields_changed"].add(field_name)

            # Track change types
            change_type = entry.get("ChangeType", "Unknown")
            summary["change_types"][change_type] = (
                summary["change_types"].get(change_type, 0) + 1
            )

            # Track changes by date
            change_date = entry.get("ChangeDateTime")
            if change_date:
                try:
                    date_key = (
                        datetime.fromisoformat(change_date.replace("Z", "+00:00"))
                        .date()
                        .isoformat()
                    )
                    changes_by_date[date_key] = changes_by_date.get(date_key, 0) + 1
                except (ValueError, TypeError):
                    pass

        # Convert sets to counts
        summary["unique_resources"] = len(summary["unique_resources"])
        summary["fields_changed"] = len(summary["fields_changed"])

        # Find most active day
        if changes_by_date:
            summary["most_active_day"] = max(changes_by_date, key=changes_by_date.get)
            summary["max_daily_changes"] = changes_by_date[summary["most_active_day"]]

        # Calculate change frequency
        if days > 0:
            summary["change_frequency"] = round(len(history) / days, 2)

        return summary

    def search_history_by_value(
        self,
        search_value: str,
        field_name: Optional[str] = None,
        ticket_id: Optional[int] = None,
        search_old_values: bool = True,
        search_new_values: bool = True,
    ) -> EntityList:
        """
        Search history entries by old or new values.

        Args:
            search_value: Value to search for
            field_name: Optional filter by field name
            ticket_id: Optional filter by ticket ID
            search_old_values: Whether to search in old values
            search_new_values: Whether to search in new values

        Returns:
            List of matching history entries
        """
        filters = []

        if ticket_id:
            filters.append({"field": "TicketID", "op": "eq", "value": str(ticket_id)})

        if field_name:
            filters.append({"field": "FieldName", "op": "eq", "value": field_name})

        # Build OR condition for value search
        value_filters = []
        if search_old_values:
            value_filters.append(
                {"field": "OldValue", "op": "contains", "value": search_value}
            )
        if search_new_values:
            value_filters.append(
                {"field": "NewValue", "op": "contains", "value": search_value}
            )

        # Note: Autotask API might not support OR conditions directly
        # This would need to be handled by making separate queries and combining results

        all_matches = []
        for value_filter in value_filters:
            current_filters = filters + [value_filter]
            matches = self.query_all(filters=current_filters)
            all_matches.extend(matches)

        # Remove duplicates based on ID
        seen_ids = set()
        unique_matches = []
        for match in all_matches:
            match_id = match.get("id")
            if match_id not in seen_ids:
                seen_ids.add(match_id)
                unique_matches.append(match)

        return unique_matches

    def get_bulk_change_events(
        self,
        resource_id: int,
        time_window_minutes: int = 5,
        min_changes: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Identify bulk change events by a resource within a time window.

        Args:
            resource_id: Resource ID
            time_window_minutes: Time window to group changes
            min_changes: Minimum changes to consider as bulk

        Returns:
            List of bulk change events
        """
        # Get recent changes by resource
        history = self.get_history_by_resource(resource_id, days=7)

        # Group changes by time windows
        bulk_events = []
        time_groups = {}

        for entry in history:
            change_date = entry.get("ChangeDateTime")
            if not change_date:
                continue

            try:
                change_time = datetime.fromisoformat(change_date.replace("Z", "+00:00"))
                # Round to time window
                window_key = change_time.replace(
                    minute=(change_time.minute // time_window_minutes)
                    * time_window_minutes,
                    second=0,
                    microsecond=0,
                )

                if window_key not in time_groups:
                    time_groups[window_key] = []
                time_groups[window_key].append(entry)
            except (ValueError, TypeError):
                continue

        # Identify bulk events
        for window_time, changes in time_groups.items():
            if len(changes) >= min_changes:
                tickets_affected = len(set(c.get("TicketID") for c in changes))
                fields_changed = len(set(c.get("FieldName") for c in changes))

                bulk_event = {
                    "window_start": window_time.isoformat(),
                    "window_end": (
                        window_time + timedelta(minutes=time_window_minutes)
                    ).isoformat(),
                    "resource_id": resource_id,
                    "total_changes": len(changes),
                    "tickets_affected": tickets_affected,
                    "fields_changed": fields_changed,
                    "changes": changes,
                }
                bulk_events.append(bulk_event)

        # Sort by change count (descending)
        bulk_events.sort(key=lambda x: x["total_changes"], reverse=True)

        return bulk_events

    def get_compliance_audit_trail(
        self,
        ticket_id: int,
        required_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get compliance-focused audit trail for a ticket.

        Args:
            ticket_id: Ticket ID
            required_fields: List of fields required for compliance

        Returns:
            Dictionary with compliance audit information
        """
        history = self.get_history_by_ticket(ticket_id)

        if not required_fields:
            required_fields = [
                "Status",
                "Priority",
                "AssignedResourceID",
                "Resolution",
                "CompletedDate",
                "ApprovalStatus",
            ]

        audit_trail = {
            "ticket_id": ticket_id,
            "total_changes": len(history),
            "audit_complete": True,
            "missing_trails": [],
            "compliance_score": 100.0,
            "field_coverage": {},
            "change_timeline": [],
        }

        fields_with_history = set()

        for entry in history:
            field_name = entry.get("FieldName")
            if field_name:
                fields_with_history.add(field_name)

                # Build timeline entry
                timeline_entry = {
                    "change_date": entry.get("ChangeDateTime"),
                    "field_name": field_name,
                    "old_value": entry.get("OldValue"),
                    "new_value": entry.get("NewValue"),
                    "changed_by": entry.get("ChangedByResourceID"),
                    "change_reason": entry.get("ChangeReason", ""),
                }
                audit_trail["change_timeline"].append(timeline_entry)

        # Check field coverage
        for field in required_fields:
            if field in fields_with_history:
                audit_trail["field_coverage"][field] = "Complete"
            else:
                audit_trail["field_coverage"][field] = "Missing"
                audit_trail["missing_trails"].append(field)
                audit_trail["audit_complete"] = False

        # Calculate compliance score
        if required_fields:
            coverage_percentage = (
                len([f for f in required_fields if f in fields_with_history])
                / len(required_fields)
                * 100
            )
            audit_trail["compliance_score"] = round(coverage_percentage, 1)

        # Sort timeline by date
        try:
            audit_trail["change_timeline"].sort(
                key=lambda x: x.get("change_date", ""), reverse=True
            )
        except (TypeError, ValueError):
            pass

        return audit_trail

    def export_history_report(
        self,
        ticket_id: int,
        format_type: str = "detailed",
        include_system_changes: bool = False,
    ) -> Dict[str, Any]:
        """
        Export comprehensive history report for a ticket.

        Args:
            ticket_id: Ticket ID
            format_type: Type of report ("detailed", "summary", "timeline")
            include_system_changes: Whether to include automated system changes

        Returns:
            Dictionary with formatted history report
        """
        history = self.get_history_by_ticket(ticket_id)

        if not include_system_changes:
            # Filter out system changes (would need field to identify these)
            history = [h for h in history if h.get("ChangedByResourceID")]

        report = {
            "ticket_id": ticket_id,
            "report_type": format_type,
            "generated_date": datetime.now().isoformat(),
            "total_entries": len(history),
            "include_system_changes": include_system_changes,
        }

        if format_type == "summary":
            summary = self.get_ticket_activity_summary(ticket_id)
            report["summary"] = summary

        elif format_type == "timeline":
            timeline = []
            for entry in history:
                timeline.append(
                    {
                        "date": entry.get("ChangeDateTime"),
                        "field": entry.get("FieldName"),
                        "from": entry.get("OldValue"),
                        "to": entry.get("NewValue"),
                        "by": entry.get("ChangedByResourceID"),
                    }
                )
            report["timeline"] = timeline

        else:  # detailed
            report["detailed_history"] = history
            report["status_timeline"] = self.get_status_change_timeline(ticket_id)
            report["assignment_history"] = self.get_assignment_change_history(ticket_id)
            report["priority_history"] = self.get_priority_escalation_history(ticket_id)

        return report
