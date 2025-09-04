"""
Service Calls entity for Autotask API.

This module provides the ServiceCallsEntity class for managing
service call scheduling and technician dispatching.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ServiceCallsEntity(BaseEntity):
    """
    Entity for managing Autotask Service Calls.

    Service Calls represent scheduled field service visits
    with technician assignment and travel time tracking.
    """

    def __init__(self, client, entity_name="ServiceCalls"):
        """Initialize the Service Calls entity."""
        super().__init__(client, entity_name)

    def create(self, service_call_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new service call.

        Args:
            service_call_data: Dictionary containing service call information
                Required fields:
                - accountID: ID of the account/company
                - ticketID: ID of the associated ticket
                - resourceID: ID of the assigned technician
                - startDateTime: Scheduled start date/time
                - description: Description of the service call
                Optional fields:
                - endDateTime: Scheduled end date/time
                - duration: Duration in minutes
                - status: Service call status
                - serviceCallCategoryID: Category ID
                - travelTime: Travel time in minutes
                - estimatedCost: Estimated cost
                - actualCost: Actual cost
                - customerSignature: Customer signature
                - notes: Additional notes

        Returns:
            CreateResponse: Response containing created service call data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = [
            "accountID",
            "ticketID",
            "resourceID",
            "startDateTime",
            "description",
        ]
        self._validate_required_fields(service_call_data, required_fields)

        return self._create(service_call_data)

    def get(self, service_call_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a service call by ID.

        Args:
            service_call_id: The service call ID

        Returns:
            Dictionary containing service call data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(service_call_id)

    def update(
        self, service_call_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing service call.

        Args:
            service_call_id: The service call ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated service call data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        return self._update(service_call_id, update_data)

    def delete(self, service_call_id: int) -> bool:
        """
        Delete a service call.

        Args:
            service_call_id: The service call ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(service_call_id)

    def get_by_technician(
        self,
        resource_id: int,
        date_range: Optional[tuple] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get service calls for a specific technician.

        Args:
            resource_id: ID of the technician/resource
            date_range: Optional tuple of (start_date, end_date)
            status_filter: Optional status filter ('scheduled', 'in_progress', 'completed')
            limit: Maximum number of service calls to return

        Returns:
            List of service calls for the technician
        """
        filters = [QueryFilter(field="resourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="startDateTime",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="startDateTime",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if status_filter:
            status_map = {
                "scheduled": 1,
                "in_progress": 2,
                "completed": 3,
                "cancelled": 4,
            }
            if status_filter.lower() in status_map:
                filters.append(
                    QueryFilter(
                        field="status", op="eq", value=status_map[status_filter.lower()]
                    )
                )

        return self.query(filters=filters, max_records=limit)

    def get_by_ticket(self, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get all service calls for a specific ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of service calls for the ticket
        """
        filters = [QueryFilter(field="ticketID", op="eq", value=ticket_id)]
        return self.query(filters=filters)

    def get_scheduled_calls(
        self, date_range: Optional[tuple] = None, resource_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get scheduled service calls.

        Args:
            date_range: Optional date range filter
            resource_id: Optional filter by technician

        Returns:
            List of scheduled service calls
        """
        filters = [QueryFilter(field="status", op="eq", value=1)]  # Scheduled

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="startDateTime",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="startDateTime",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        if resource_id:
            filters.append(QueryFilter(field="resourceID", op="eq", value=resource_id))

        return self.query(filters=filters)

    def get_todays_schedule(
        self, resource_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get today's service call schedule.

        Args:
            resource_id: Optional filter by technician

        Returns:
            List of today's service calls
        """
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        return self.get_scheduled_calls(
            date_range=(today.isoformat(), tomorrow.isoformat()),
            resource_id=resource_id,
        )

    def start_service_call(
        self, service_call_id: int, actual_start_time: Optional[datetime] = None
    ) -> UpdateResponse:
        """
        Mark a service call as started.

        Args:
            service_call_id: Service call ID
            actual_start_time: Actual start time (defaults to now)

        Returns:
            Updated service call data
        """
        start_time = actual_start_time or datetime.now()

        update_data = {
            "status": 2,  # In Progress
            "actualStartDateTime": start_time.isoformat(),
            "lastModifiedDateTime": datetime.now().isoformat(),
        }

        return self.update(service_call_id, update_data)

    def complete_service_call(
        self,
        service_call_id: int,
        completion_notes: Optional[str] = None,
        actual_end_time: Optional[datetime] = None,
        customer_signature: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Mark a service call as completed.

        Args:
            service_call_id: Service call ID
            completion_notes: Optional completion notes
            actual_end_time: Actual end time (defaults to now)
            customer_signature: Optional customer signature

        Returns:
            Updated service call data
        """
        end_time = actual_end_time or datetime.now()

        update_data = {
            "status": 3,  # Completed
            "actualEndDateTime": end_time.isoformat(),
            "completionDateTime": datetime.now().isoformat(),
        }

        if completion_notes:
            update_data["completionNotes"] = completion_notes

        if customer_signature:
            update_data["customerSignature"] = customer_signature

        return self.update(service_call_id, update_data)

    def cancel_service_call(
        self, service_call_id: int, cancellation_reason: str
    ) -> UpdateResponse:
        """
        Cancel a service call.

        Args:
            service_call_id: Service call ID
            cancellation_reason: Reason for cancellation

        Returns:
            Updated service call data
        """
        update_data = {
            "status": 4,  # Cancelled
            "cancellationReason": cancellation_reason,
            "cancellationDateTime": datetime.now().isoformat(),
        }

        return self.update(service_call_id, update_data)

    def reschedule_service_call(
        self,
        service_call_id: int,
        new_start_time: datetime,
        new_end_time: Optional[datetime] = None,
        reschedule_reason: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Reschedule a service call.

        Args:
            service_call_id: Service call ID
            new_start_time: New start date/time
            new_end_time: New end date/time
            reschedule_reason: Optional reason for rescheduling

        Returns:
            Updated service call data
        """
        update_data = {
            "startDateTime": new_start_time.isoformat(),
            "lastRescheduleDateTime": datetime.now().isoformat(),
        }

        if new_end_time:
            update_data["endDateTime"] = new_end_time.isoformat()

        if reschedule_reason:
            update_data["rescheduleReason"] = reschedule_reason

        return self.update(service_call_id, update_data)

    def assign_technician(
        self,
        service_call_id: int,
        new_resource_id: int,
        assignment_reason: Optional[str] = None,
    ) -> UpdateResponse:
        """
        Reassign a service call to a different technician.

        Args:
            service_call_id: Service call ID
            new_resource_id: ID of the new technician
            assignment_reason: Optional reason for reassignment

        Returns:
            Updated service call data
        """
        update_data = {
            "resourceID": new_resource_id,
            "lastAssignmentDateTime": datetime.now().isoformat(),
        }

        if assignment_reason:
            update_data["assignmentReason"] = assignment_reason

        return self.update(service_call_id, update_data)

    def get_technician_schedule(
        self, resource_id: int, date_range: tuple, include_travel_time: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed schedule for a technician.

        Args:
            resource_id: Technician ID
            date_range: Date range tuple (start_date, end_date)
            include_travel_time: Whether to include travel time in calculations

        Returns:
            Dictionary with detailed schedule information
        """
        service_calls = self.get_by_technician(resource_id, date_range)

        schedule = {
            "resource_id": resource_id,
            "date_range": {
                "start": (
                    date_range[0].isoformat()
                    if hasattr(date_range[0], "isoformat")
                    else date_range[0]
                ),
                "end": (
                    date_range[1].isoformat()
                    if hasattr(date_range[1], "isoformat")
                    else date_range[1]
                ),
            },
            "total_calls": len(service_calls),
            "by_status": {
                "scheduled": 0,
                "in_progress": 0,
                "completed": 0,
                "cancelled": 0,
            },
            "total_scheduled_hours": 0,
            "total_travel_time": 0,
            "daily_breakdown": {},
            "calls": service_calls,
        }

        status_map = {1: "scheduled", 2: "in_progress", 3: "completed", 4: "cancelled"}

        for call in service_calls:
            status_id = call.get("status", 1)
            status_name = status_map.get(status_id, "scheduled")
            schedule["by_status"][status_name] += 1

            # Calculate duration
            start_time = call.get("startDateTime")
            end_time = call.get("endDateTime")
            travel_time = call.get("travelTime", 0)

            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    duration_hours = (end - start).total_seconds() / 3600
                    schedule["total_scheduled_hours"] += duration_hours

                    # Daily breakdown
                    date_key = start.date().isoformat()
                    if date_key not in schedule["daily_breakdown"]:
                        schedule["daily_breakdown"][date_key] = {
                            "calls": 0,
                            "hours": 0,
                            "travel_time": 0,
                        }

                    schedule["daily_breakdown"][date_key]["calls"] += 1
                    schedule["daily_breakdown"][date_key]["hours"] += duration_hours

                except ValueError:
                    pass

            # Travel time
            if include_travel_time and travel_time:
                travel_hours = travel_time / 60
                schedule["total_travel_time"] += travel_hours

                # Add to daily breakdown
                if start_time:
                    try:
                        start = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00")
                        )
                        date_key = start.date().isoformat()
                        if date_key in schedule["daily_breakdown"]:
                            schedule["daily_breakdown"][date_key][
                                "travel_time"
                            ] += travel_hours
                    except ValueError:
                        pass

        return schedule

    def get_service_call_metrics(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get service call performance metrics.

        Args:
            date_range: Optional date range for analysis

        Returns:
            Dictionary with performance metrics
        """
        filters = []

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(
                        field="startDateTime",
                        op="gte",
                        value=(
                            start_date.isoformat()
                            if hasattr(start_date, "isoformat")
                            else start_date
                        ),
                    ),
                    QueryFilter(
                        field="startDateTime",
                        op="lte",
                        value=(
                            end_date.isoformat()
                            if hasattr(end_date, "isoformat")
                            else end_date
                        ),
                    ),
                ]
            )

        service_calls = self.query(filters=filters)

        metrics = {
            "total_calls": len(service_calls),
            "by_status": {
                "scheduled": 0,
                "in_progress": 0,
                "completed": 0,
                "cancelled": 0,
            },
            "completion_rate": 0,
            "avg_duration": 0,
            "avg_travel_time": 0,
            "on_time_percentage": 0,
            "customer_satisfaction": 0,
            "cost_analysis": {
                "total_estimated": 0,
                "total_actual": 0,
                "variance_percentage": 0,
            },
        }

        durations = []
        travel_times = []
        on_time_count = 0
        estimated_costs = []
        actual_costs = []

        status_map = {1: "scheduled", 2: "in_progress", 3: "completed", 4: "cancelled"}

        for call in service_calls:
            status_id = call.get("status", 1)
            status_name = status_map.get(status_id, "scheduled")
            metrics["by_status"][status_name] += 1

            # Duration analysis
            start_time = call.get("startDateTime")
            end_time = call.get("endDateTime")
            actual_start = call.get("actualStartDateTime")

            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    duration_hours = (end - start).total_seconds() / 3600
                    durations.append(duration_hours)
                except ValueError:
                    pass

            # On-time analysis
            if start_time and actual_start:
                try:
                    scheduled = datetime.fromisoformat(
                        start_time.replace("Z", "+00:00")
                    )
                    actual = datetime.fromisoformat(actual_start.replace("Z", "+00:00"))
                    if (
                        abs((actual - scheduled).total_seconds()) <= 900
                    ):  # Within 15 minutes
                        on_time_count += 1
                except ValueError:
                    pass

            # Travel time
            travel_time = call.get("travelTime", 0)
            if travel_time:
                travel_times.append(travel_time / 60)  # Convert to hours

            # Cost analysis
            estimated = call.get("estimatedCost", 0)
            actual = call.get("actualCost", 0)

            if estimated:
                estimated_costs.append(float(estimated))
            if actual:
                actual_costs.append(float(actual))

        # Calculate averages
        if durations:
            metrics["avg_duration"] = sum(durations) / len(durations)

        if travel_times:
            metrics["avg_travel_time"] = sum(travel_times) / len(travel_times)

        if metrics["total_calls"] > 0:
            metrics["completion_rate"] = (
                metrics["by_status"]["completed"] / metrics["total_calls"]
            ) * 100

            if on_time_count > 0:
                metrics["on_time_percentage"] = (
                    on_time_count / metrics["total_calls"]
                ) * 100

        # Cost analysis
        if estimated_costs:
            metrics["cost_analysis"]["total_estimated"] = sum(estimated_costs)

        if actual_costs:
            metrics["cost_analysis"]["total_actual"] = sum(actual_costs)

        if metrics["cost_analysis"]["total_estimated"] > 0:
            variance = (
                (
                    metrics["cost_analysis"]["total_actual"]
                    - metrics["cost_analysis"]["total_estimated"]
                )
                / metrics["cost_analysis"]["total_estimated"]
            ) * 100
            metrics["cost_analysis"]["variance_percentage"] = variance

        return metrics

    def validate_service_call_data(
        self, service_call_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate service call data.

        Args:
            service_call_data: Service call data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Validate required fields
        required_fields = [
            "accountID",
            "ticketID",
            "resourceID",
            "startDateTime",
            "description",
        ]
        for field in required_fields:
            if field not in service_call_data or service_call_data[field] is None:
                errors.append(f"Required field '{field}' is missing")

        # Validate dates
        start_time = service_call_data.get("startDateTime")
        end_time = service_call_data.get("endDateTime")

        if start_time:
            try:
                if isinstance(start_time, str):
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    if start_dt < datetime.now():
                        warnings.append("Start time is in the past")
            except ValueError:
                errors.append("Start date/time must be a valid datetime")

        if end_time:
            try:
                if isinstance(end_time, str):
                    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    if start_time:
                        start_dt = datetime.fromisoformat(
                            start_time.replace("Z", "+00:00")
                        )
                        if end_dt <= start_dt:
                            errors.append("End time must be after start time")
            except ValueError:
                errors.append("End date/time must be a valid datetime")

        # Validate description
        description = service_call_data.get("description", "")
        if description and len(description) < 10:
            warnings.append(
                "Description should be more descriptive (at least 10 characters)"
            )

        # Validate travel time
        travel_time = service_call_data.get("travelTime")
        if travel_time is not None:
            try:
                travel_val = int(travel_time)
                if travel_val < 0:
                    errors.append("Travel time cannot be negative")
                elif travel_val > 480:  # 8 hours
                    warnings.append("Travel time seems unusually high (over 8 hours)")
            except (ValueError, TypeError):
                errors.append("Travel time must be a valid number (minutes)")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
