"""
Ticket Sources entity for Autotask API.

This module provides the TicketSourcesEntity class for managing
ticket source tracking and integration mapping.
"""

from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class TicketSourcesEntity(BaseEntity):
    """
    Entity for managing Autotask Ticket Sources.

    Ticket Sources track how tickets are created and provide
    integration mapping for automation and reporting.
    """

    def __init__(self, client, entity_name="TicketSources"):
        """Initialize the Ticket Sources entity."""
        super().__init__(client, entity_name)

    def create(self, source_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new ticket source.

        Args:
            source_data: Dictionary containing source information
                Required fields:
                - name: Name of the source
                - active: Whether the source is active
                Optional fields:
                - description: Description of the source
                - isDefault: Whether this is a default source
                - sortOrder: Sort order for display
                - integrationCode: Code for integration mapping
                - automationRules: JSON string with automation rules

        Returns:
            CreateResponse: Response containing created source data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["name", "active"]
        self._validate_required_fields(source_data, required_fields)

        return self._create(source_data)

    def get(self, source_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ticket source by ID.

        Args:
            source_id: The source ID

        Returns:
            Dictionary containing source data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(source_id)

    def update(self, source_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing ticket source.

        Args:
            source_id: The source ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated source data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(source_id, update_data)

    def delete(self, source_id: int) -> bool:
        """
        Delete a ticket source.

        Args:
            source_id: The source ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(source_id)

    def get_active_sources(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all active ticket sources.

        Args:
            include_inactive: Whether to include inactive sources

        Returns:
            List of active sources ordered by sort order
        """
        filters = []

        if not include_inactive:
            filters.append(QueryFilter(field="active", op="eq", value=True))

        sources = self.query(filters=filters)

        # Sort by sort order
        return sorted(sources, key=lambda x: x.get("sortOrder", 999))

    def get_default_source(self) -> Optional[Dict[str, Any]]:
        """
        Get the default source.

        Returns:
            Default source data
        """
        filters = [
            QueryFilter(field="isDefault", op="eq", value=True),
            QueryFilter(field="active", op="eq", value=True),
        ]

        sources = self.query(filters=filters)
        return sources[0] if sources else None

    def get_source_by_integration_code(
        self, integration_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get source by integration code.

        Args:
            integration_code: Integration code to search for

        Returns:
            Source data for the specified integration code
        """
        filters = [
            QueryFilter(field="integrationCode", op="eq", value=integration_code),
            QueryFilter(field="active", op="eq", value=True),
        ]

        sources = self.query(filters=filters)
        return sources[0] if sources else None

    def get_source_usage_stats(
        self, source_id: int, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a source.

        Args:
            source_id: Source ID to get stats for
            date_range: Optional date range for ticket counts

        Returns:
            Dictionary with usage statistics
        """
        # Build filter for tickets with this source
        filters = [QueryFilter(field="ticketSource", op="eq", value=source_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="createDate",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="createDate",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        # Query tickets with this source
        tickets = self.client.query("Tickets", filters=filters)

        # Calculate statistics
        stats = {
            "source_id": source_id,
            "total_tickets": len(tickets),
            "open_tickets": 0,
            "closed_tickets": 0,
            "avg_resolution_time": 0,
            "by_priority": {1: 0, 2: 0, 3: 0, 4: 0},
            "by_status": {},
            "by_category": {},
            "by_month": {},
        }

        resolution_times = []

        for ticket in tickets:
            status = ticket.get("status", 1)
            priority = ticket.get("priority", 4)
            category = ticket.get("ticketCategory", "Other")
            create_date = ticket.get("createDate", "")

            # Count by status
            if status in [5, 6]:  # Closed/Complete statuses
                stats["closed_tickets"] += 1
            else:
                stats["open_tickets"] += 1

            # Count by priority
            if priority in stats["by_priority"]:
                stats["by_priority"][priority] += 1

            # Count by status
            status_name = f"status_{status}"
            stats["by_status"][status_name] = stats["by_status"].get(status_name, 0) + 1

            # Count by category
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # Count by month
            if create_date:
                try:
                    from datetime import datetime

                    created = datetime.fromisoformat(create_date.replace("Z", "+00:00"))
                    month_key = created.strftime("%Y-%m")
                    stats["by_month"][month_key] = (
                        stats["by_month"].get(month_key, 0) + 1
                    )
                except ValueError:
                    pass

            # Calculate resolution time for closed tickets
            if status in [5, 6]:
                close_date = ticket.get("lastActivityDate")

                if create_date and close_date:
                    try:
                        from datetime import datetime

                        created = datetime.fromisoformat(
                            create_date.replace("Z", "+00:00")
                        )
                        closed = datetime.fromisoformat(
                            close_date.replace("Z", "+00:00")
                        )
                        resolution_time = (
                            closed - created
                        ).total_seconds() / 3600  # Hours
                        resolution_times.append(resolution_time)
                    except ValueError:
                        pass

        # Calculate average resolution time
        if resolution_times:
            stats["avg_resolution_time"] = sum(resolution_times) / len(resolution_times)

        return stats

    def get_source_comparison(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get comparative statistics across all sources.

        Args:
            date_range: Optional date range for analysis

        Returns:
            Dictionary with comparative source statistics
        """
        sources = self.get_active_sources()
        comparison = {
            "total_sources": len(sources),
            "by_source": {},
            "summary": {
                "total_tickets": 0,
                "avg_resolution_time": 0,
                "most_used_source": None,
                "least_used_source": None,
            },
        }

        all_resolution_times = []
        source_ticket_counts = {}

        for source in sources:
            source_id = source["id"]
            name = source.get("name", f"Source {source_id}")

            stats = self.get_source_usage_stats(source_id, date_range)

            comparison["by_source"][source_id] = {"name": name, "stats": stats}

            # Track for summary
            ticket_count = stats["total_tickets"]
            source_ticket_counts[source_id] = {"name": name, "count": ticket_count}
            comparison["summary"]["total_tickets"] += ticket_count

            if stats["avg_resolution_time"] > 0:
                all_resolution_times.append(stats["avg_resolution_time"])

        # Calculate overall averages
        if all_resolution_times:
            comparison["summary"]["avg_resolution_time"] = sum(
                all_resolution_times
            ) / len(all_resolution_times)

        # Find most and least used sources
        if source_ticket_counts:
            most_used = max(source_ticket_counts.items(), key=lambda x: x[1]["count"])
            least_used = min(source_ticket_counts.items(), key=lambda x: x[1]["count"])

            comparison["summary"]["most_used_source"] = {
                "id": most_used[0],
                "name": most_used[1]["name"],
                "count": most_used[1]["count"],
            }

            comparison["summary"]["least_used_source"] = {
                "id": least_used[0],
                "name": least_used[1]["name"],
                "count": least_used[1]["count"],
            }

        return comparison

    def set_source_order(
        self, source_orders: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Set the sort order for multiple sources.

        Args:
            source_orders: List of dictionaries with 'id' and 'sortOrder'

        Returns:
            List of update responses
        """
        results = []

        for order_data in source_orders:
            source_id = order_data.get("id")
            sort_order = order_data.get("sortOrder")

            if source_id and sort_order is not None:
                update_data = {"sortOrder": sort_order}
                result = self.update(source_id, update_data)
                results.append(result)

        return results

    def create_integration_source(
        self, integration_data: Dict[str, Any]
    ) -> CreateResponse:
        """
        Create a source specifically for integration purposes.

        Args:
            integration_data: Dictionary containing integration information
                Required fields:
                - name: Name of the integration source
                - integrationCode: Unique code for the integration
                Optional fields:
                - description: Description of the integration
                - automationRules: JSON string with automation rules

        Returns:
            CreateResponse: Response containing created source data
        """
        source_data = {
            "name": integration_data["name"],
            "integrationCode": integration_data["integrationCode"],
            "active": True,
            "description": integration_data.get("description", ""),
            "automationRules": integration_data.get("automationRules", "{}"),
        }

        return self.create(source_data)

    def update_automation_rules(
        self, source_id: int, automation_rules: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update automation rules for a source.

        Args:
            source_id: Source ID to update
            automation_rules: Dictionary with automation rules

        Returns:
            Updated source data
        """
        import json

        update_data = {"automationRules": json.dumps(automation_rules)}

        return self.update(source_id, update_data)

    def get_automation_rules(self, source_id: int) -> Dict[str, Any]:
        """
        Get automation rules for a source.

        Args:
            source_id: Source ID to get rules for

        Returns:
            Dictionary with automation rules
        """
        source = self.get(source_id)
        if not source:
            return {}

        automation_rules = source.get("automationRules", "{}")

        try:
            import json

            return json.loads(automation_rules)
        except (ValueError, TypeError):
            return {}

    def bulk_update_sources(
        self, source_updates: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Update multiple sources in bulk.

        Args:
            source_updates: List of dictionaries with 'id' and update data

        Returns:
            List of update responses
        """
        results = []

        for update_info in source_updates:
            source_id = update_info.get("id")
            update_data = update_info.get("data", {})

            if source_id and update_data:
                try:
                    result = self.update(source_id, update_data)
                    results.append(result)
                except Exception as e:
                    self.client.logger.error(
                        f"Failed to update source {source_id}: {e}"
                    )
                    results.append({"error": str(e), "source_id": source_id})

        return results

    def get_ticket_source_trends(
        self, date_range: Optional[tuple] = None, granularity: str = "month"
    ) -> Dict[str, Any]:
        """
        Get trends showing ticket volume by source over time.

        Args:
            date_range: Optional date range for analysis
            granularity: Time granularity ('day', 'week', 'month')

        Returns:
            Dictionary with trend data
        """
        sources = self.get_active_sources()
        trends = {
            "granularity": granularity,
            "date_range": {
                "start": (
                    date_range[0].isoformat()
                    if date_range and hasattr(date_range[0], "isoformat")
                    else date_range[0] if date_range else None
                ),
                "end": (
                    date_range[1].isoformat()
                    if date_range and hasattr(date_range[1], "isoformat")
                    else date_range[1] if date_range else None
                ),
            },
            "by_source": {},
            "timeline": {},
        }

        for source in sources:
            source_id = source["id"]
            source_name = source.get("name", f"Source {source_id}")

            # Get tickets for this source
            filters = [QueryFilter(field="ticketSource", op="eq", value=source_id)]

            if date_range:
                start_date, end_date = date_range
                filters.extend(
                    [
                        QueryFilter(
                            field="createDate",
                            op="gte",
                            value=(
                                start_date.isoformat()
                                if hasattr(start_date, "isoformat")
                                else start_date
                            ),
                        ),
                        QueryFilter(
                            field="createDate",
                            op="lte",
                            value=(
                                end_date.isoformat()
                                if hasattr(end_date, "isoformat")
                                else end_date
                            ),
                        ),
                    ]
                )

            tickets = self.client.query("Tickets", filters=filters)

            source_timeline = {}

            for ticket in tickets:
                create_date = ticket.get("createDate", "")
                if create_date:
                    try:
                        from datetime import datetime

                        created = datetime.fromisoformat(
                            create_date.replace("Z", "+00:00")
                        )

                        if granularity == "day":
                            period_key = created.strftime("%Y-%m-%d")
                        elif granularity == "week":
                            # ISO week
                            year, week, _ = created.isocalendar()
                            period_key = f"{year}-W{week:02d}"
                        else:  # month
                            period_key = created.strftime("%Y-%m")

                        source_timeline[period_key] = (
                            source_timeline.get(period_key, 0) + 1
                        )

                        # Add to overall timeline
                        if period_key not in trends["timeline"]:
                            trends["timeline"][period_key] = {}
                        trends["timeline"][period_key][source_name] = source_timeline[
                            period_key
                        ]

                    except ValueError:
                        pass

            trends["by_source"][source_id] = {
                "name": source_name,
                "timeline": source_timeline,
                "total_tickets": len(tickets),
            }

        return trends

    def validate_source_data(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate source data.

        Args:
            source_data: Source data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = ["name", "active"]
        for field in required_fields:
            if field not in source_data or source_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate name
        name = source_data.get("name", "")
        if name:
            if len(name) < 2:
                errors.append("Source name must be at least 2 characters")
            elif len(name) > 100:
                errors.append("Source name must not exceed 100 characters")

        # Validate integration code uniqueness
        integration_code = source_data.get("integrationCode")
        if integration_code:
            existing_source = self.get_source_by_integration_code(integration_code)
            if existing_source and existing_source.get("id") != source_data.get("id"):
                warnings.append(
                    f"Integration code '{integration_code}' is already in use"
                )

        # Validate automation rules JSON
        automation_rules = source_data.get("automationRules")
        if automation_rules:
            try:
                import json

                json.loads(automation_rules)
            except (ValueError, TypeError):
                errors.append("Automation rules must be valid JSON")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
