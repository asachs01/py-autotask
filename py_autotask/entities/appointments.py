"""
Appointments entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class AppointmentsEntity(BaseEntity):
    """
    Handles Appointment operations for the Autotask API.

    Manages calendar appointments, scheduling, and resource booking
    within the Autotask system.
    """

    def __init__(self, client, entity_name: str = "Appointments"):
        super().__init__(client, entity_name)

    def create_appointment(
        self,
        title: str,
        start_datetime: str,
        end_datetime: str,
        resource_id: int,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_all_day: bool = False,
        reminder_minutes: Optional[int] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new appointment.

        Args:
            title: Appointment title
            start_datetime: Start date and time (ISO format)
            end_datetime: End date and time (ISO format)
            resource_id: ID of the assigned resource
            description: Optional appointment description
            location: Optional location
            is_all_day: Whether this is an all-day appointment
            reminder_minutes: Minutes before appointment for reminder
            **kwargs: Additional appointment fields

        Returns:
            Created appointment data
        """
        appointment_data = {
            "Title": title,
            "StartDateTime": start_datetime,
            "EndDateTime": end_datetime,
            "ResourceID": resource_id,
            "IsAllDay": is_all_day,
            **kwargs,
        }

        if description:
            appointment_data["Description"] = description

        if location:
            appointment_data["Location"] = location

        if reminder_minutes is not None:
            appointment_data["ReminderMinutes"] = reminder_minutes

        return self.create(appointment_data)

    def get_appointments_by_resource(
        self,
        resource_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_all_day: bool = True,
    ) -> EntityList:
        """
        Get appointments for a specific resource within a date range.

        Args:
            resource_id: Resource ID
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            include_all_day: Whether to include all-day appointments

        Returns:
            List of appointments for the resource
        """
        filters = [{"field": "ResourceID", "op": "eq", "value": str(resource_id)}]

        if start_date:
            filters.append({"field": "StartDateTime", "op": "gte", "value": start_date})

        if end_date:
            filters.append({"field": "EndDateTime", "op": "lte", "value": end_date})

        if not include_all_day:
            filters.append({"field": "IsAllDay", "op": "eq", "value": "false"})

        return self.query_all(filters=filters)

    def get_appointments_by_date_range(
        self,
        start_date: str,
        end_date: str,
        resource_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get appointments within a specific date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            resource_id: Optional resource filter

        Returns:
            List of appointments in the date range
        """
        filters = [
            {"field": "StartDateTime", "op": "gte", "value": start_date},
            {"field": "EndDateTime", "op": "lte", "value": end_date},
        ]

        if resource_id is not None:
            filters.append(
                {"field": "ResourceID", "op": "eq", "value": str(resource_id)}
            )

        return self.query_all(filters=filters)

    def get_todays_appointments(self, resource_id: Optional[int] = None) -> EntityList:
        """
        Get appointments scheduled for today.

        Args:
            resource_id: Optional resource filter

        Returns:
            List of today's appointments
        """
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
        end_of_day = datetime.combine(today, datetime.max.time()).isoformat()

        return self.get_appointments_by_date_range(
            start_of_day, end_of_day, resource_id
        )

    def get_upcoming_appointments(
        self,
        resource_id: Optional[int] = None,
        days_ahead: int = 7,
        limit: Optional[int] = None,
    ) -> EntityList:
        """
        Get upcoming appointments within specified days.

        Args:
            resource_id: Optional resource filter
            days_ahead: Number of days to look ahead
            limit: Optional limit on number of results

        Returns:
            List of upcoming appointments
        """
        now = datetime.now()
        future_date = now + timedelta(days=days_ahead)

        filters = [
            {"field": "StartDateTime", "op": "gte", "value": now.isoformat()},
            {"field": "StartDateTime", "op": "lte", "value": future_date.isoformat()},
        ]

        if resource_id is not None:
            filters.append(
                {"field": "ResourceID", "op": "eq", "value": str(resource_id)}
            )

        return self.query(filters=filters, max_records=limit).items

    def get_conflicting_appointments(
        self,
        resource_id: int,
        start_datetime: str,
        end_datetime: str,
        exclude_appointment_id: Optional[int] = None,
    ) -> EntityList:
        """
        Find appointments that conflict with a proposed time slot.

        Args:
            resource_id: Resource ID to check conflicts for
            start_datetime: Proposed start time (ISO format)
            end_datetime: Proposed end time (ISO format)
            exclude_appointment_id: Optional appointment ID to exclude from check

        Returns:
            List of conflicting appointments
        """
        filters = [
            {"field": "ResourceID", "op": "eq", "value": str(resource_id)},
            # Appointments that start before the proposed end time
            {"field": "StartDateTime", "op": "lt", "value": end_datetime},
            # Appointments that end after the proposed start time
            {"field": "EndDateTime", "op": "gt", "value": start_datetime},
        ]

        if exclude_appointment_id is not None:
            filters.append(
                {"field": "id", "op": "ne", "value": str(exclude_appointment_id)}
            )

        return self.query_all(filters=filters)

    def reschedule_appointment(
        self,
        appointment_id: int,
        new_start_datetime: str,
        new_end_datetime: str,
        reason: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Reschedule an existing appointment.

        Args:
            appointment_id: Appointment ID to reschedule
            new_start_datetime: New start date/time (ISO format)
            new_end_datetime: New end date/time (ISO format)
            reason: Optional reason for rescheduling

        Returns:
            Updated appointment data
        """
        update_data = {
            "StartDateTime": new_start_datetime,
            "EndDateTime": new_end_datetime,
        }

        if reason:
            # Add rescheduling note to description
            current_appointment = self.get(appointment_id)
            if current_appointment:
                existing_desc = current_appointment.get("Description", "")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                reschedule_note = f"\n\n[{timestamp}] Rescheduled: {reason}"
                update_data["Description"] = existing_desc + reschedule_note

        return self.update_by_id(appointment_id, update_data)

    def cancel_appointment(
        self,
        appointment_id: int,
        cancellation_reason: str,
        notify_attendees: bool = True,
    ) -> Optional[EntityDict]:
        """
        Cancel an appointment.

        Args:
            appointment_id: Appointment ID to cancel
            cancellation_reason: Reason for cancellation
            notify_attendees: Whether to notify attendees (placeholder)

        Returns:
            Updated appointment data
        """
        update_data = {"Status": "Cancelled"}

        # Add cancellation note
        current_appointment = self.get(appointment_id)
        if current_appointment:
            existing_desc = current_appointment.get("Description", "")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            cancel_note = f"\n\n[{timestamp}] CANCELLED: {cancellation_reason}"
            update_data["Description"] = existing_desc + cancel_note

        # Note: notify_attendees would trigger notification logic in a full implementation
        if notify_attendees:
            self.logger.info(
                f"Appointment {appointment_id} cancelled - attendees should be notified"
            )

        return self.update_by_id(appointment_id, update_data)

    def find_available_time_slots(
        self,
        resource_id: int,
        duration_minutes: int,
        search_start_date: str,
        search_end_date: str,
        business_hours_only: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Find available time slots for scheduling appointments.

        Args:
            resource_id: Resource ID to check availability
            duration_minutes: Required duration in minutes
            search_start_date: Start of search range (ISO format)
            search_end_date: End of search range (ISO format)
            business_hours_only: Whether to consider only business hours

        Returns:
            List of available time slots with start/end times
        """
        # Get existing appointments in the search range
        existing_appointments = self.get_appointments_by_resource(
            resource_id, search_start_date, search_end_date
        )

        # Sort appointments by start time
        sorted_appointments = sorted(
            existing_appointments, key=lambda x: x.get("StartDateTime", "")
        )

        available_slots = []
        current_time = datetime.fromisoformat(search_start_date.replace("Z", "+00:00"))
        search_end = datetime.fromisoformat(search_end_date.replace("Z", "+00:00"))
        duration_delta = timedelta(minutes=duration_minutes)

        # Business hours (9 AM to 5 PM) - this could be configurable
        business_start_hour = 9
        business_end_hour = 17

        for appointment in sorted_appointments:
            appointment_start = datetime.fromisoformat(
                appointment["StartDateTime"].replace("Z", "+00:00")
            )

            # Check if there's a gap before this appointment
            if current_time + duration_delta <= appointment_start:
                # Found a potential slot
                slot_start = current_time
                slot_end = slot_start + duration_delta

                # Apply business hours filter if requested
                if business_hours_only:
                    if (
                        slot_start.hour >= business_start_hour
                        and slot_end.hour <= business_end_hour
                        and slot_start.weekday() < 5
                    ):  # Monday-Friday
                        available_slots.append(
                            {
                                "start_datetime": slot_start.isoformat(),
                                "end_datetime": slot_end.isoformat(),
                            }
                        )
                else:
                    available_slots.append(
                        {
                            "start_datetime": slot_start.isoformat(),
                            "end_datetime": slot_end.isoformat(),
                        }
                    )

            # Move to the end of this appointment
            appointment_end = datetime.fromisoformat(
                appointment["EndDateTime"].replace("Z", "+00:00")
            )
            current_time = max(current_time, appointment_end)

        # Check for availability after the last appointment
        if current_time + duration_delta <= search_end:
            slot_start = current_time
            slot_end = slot_start + duration_delta

            if business_hours_only:
                if (
                    slot_start.hour >= business_start_hour
                    and slot_end.hour <= business_end_hour
                    and slot_start.weekday() < 5
                ):
                    available_slots.append(
                        {
                            "start_datetime": slot_start.isoformat(),
                            "end_datetime": slot_end.isoformat(),
                        }
                    )
            else:
                available_slots.append(
                    {
                        "start_datetime": slot_start.isoformat(),
                        "end_datetime": slot_end.isoformat(),
                    }
                )

        return available_slots

    def get_resource_schedule_summary(
        self,
        resource_id: int,
        date: str,
    ) -> Dict[str, Any]:
        """
        Get a summary of a resource's schedule for a specific date.

        Args:
            resource_id: Resource ID
            date: Date to summarize (ISO format YYYY-MM-DD)

        Returns:
            Dictionary with schedule summary
        """
        # Get appointments for the specific date
        start_of_day = f"{date}T00:00:00"
        end_of_day = f"{date}T23:59:59"

        appointments = self.get_appointments_by_resource(
            resource_id, start_of_day, end_of_day
        )

        summary = {
            "date": date,
            "resource_id": resource_id,
            "total_appointments": len(appointments),
            "total_scheduled_minutes": 0,
            "all_day_appointments": 0,
            "earliest_appointment": None,
            "latest_appointment": None,
            "appointment_details": [],
        }

        earliest_time = None
        latest_time = None

        for appointment in appointments:
            if appointment.get("IsAllDay", False):
                summary["all_day_appointments"] += 1
            else:
                # Calculate duration
                start_time = datetime.fromisoformat(
                    appointment["StartDateTime"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    appointment["EndDateTime"].replace("Z", "+00:00")
                )

                duration_minutes = (end_time - start_time).total_seconds() / 60
                summary["total_scheduled_minutes"] += duration_minutes

                # Track earliest and latest times
                if earliest_time is None or start_time < earliest_time:
                    earliest_time = start_time
                    summary["earliest_appointment"] = start_time.strftime("%H:%M")

                if latest_time is None or end_time > latest_time:
                    latest_time = end_time
                    summary["latest_appointment"] = end_time.strftime("%H:%M")

            # Add appointment details
            summary["appointment_details"].append(
                {
                    "id": appointment.get("id"),
                    "title": appointment.get("Title", ""),
                    "start_time": appointment.get("StartDateTime"),
                    "end_time": appointment.get("EndDateTime"),
                    "is_all_day": appointment.get("IsAllDay", False),
                    "location": appointment.get("Location", ""),
                }
            )

        # Convert total minutes to hours and minutes
        total_hours = int(summary["total_scheduled_minutes"] // 60)
        remaining_minutes = int(summary["total_scheduled_minutes"] % 60)
        summary["total_scheduled_time"] = f"{total_hours}h {remaining_minutes}m"

        return summary

    def get_appointment_statistics(
        self, resource_id: Optional[int] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get appointment statistics for a resource or system-wide.

        Args:
            resource_id: Optional resource ID filter
            days: Number of days to analyze

        Returns:
            Dictionary with appointment statistics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        filters = [
            {"field": "StartDateTime", "op": "gte", "value": start_date.isoformat()},
            {"field": "StartDateTime", "op": "lte", "value": end_date.isoformat()},
        ]

        if resource_id is not None:
            filters.append(
                {"field": "ResourceID", "op": "eq", "value": str(resource_id)}
            )

        appointments = self.query_all(filters=filters)

        stats = {
            "period_days": days,
            "total_appointments": len(appointments),
            "all_day_appointments": 0,
            "cancelled_appointments": 0,
            "average_duration_minutes": 0.0,
            "total_scheduled_time_hours": 0.0,
            "by_resource": {},
            "by_day_of_week": {
                "Monday": 0,
                "Tuesday": 0,
                "Wednesday": 0,
                "Thursday": 0,
                "Friday": 0,
                "Saturday": 0,
                "Sunday": 0,
            },
            "peak_hours": {},  # Hour of day -> count
        }

        total_duration_minutes = 0
        appointment_count_for_avg = 0

        for appointment in appointments:
            # Count all-day appointments
            if appointment.get("IsAllDay", False):
                stats["all_day_appointments"] += 1
            else:
                # Calculate duration for non-all-day appointments
                try:
                    start_time = datetime.fromisoformat(
                        appointment["StartDateTime"].replace("Z", "+00:00")
                    )
                    end_time = datetime.fromisoformat(
                        appointment["EndDateTime"].replace("Z", "+00:00")
                    )
                    duration_minutes = (end_time - start_time).total_seconds() / 60
                    total_duration_minutes += duration_minutes
                    appointment_count_for_avg += 1

                    # Track peak hours
                    hour = start_time.hour
                    if hour not in stats["peak_hours"]:
                        stats["peak_hours"][hour] = 0
                    stats["peak_hours"][hour] += 1

                    # Track by day of week
                    day_name = start_time.strftime("%A")
                    stats["by_day_of_week"][day_name] += 1

                except (ValueError, TypeError):
                    pass

            # Count cancelled appointments
            if appointment.get("Status") == "Cancelled":
                stats["cancelled_appointments"] += 1

            # Count by resource
            resource_id = appointment.get("ResourceID")
            if resource_id:
                if resource_id not in stats["by_resource"]:
                    stats["by_resource"][resource_id] = 0
                stats["by_resource"][resource_id] += 1

        # Calculate averages
        if appointment_count_for_avg > 0:
            stats["average_duration_minutes"] = (
                total_duration_minutes / appointment_count_for_avg
            )
            stats["total_scheduled_time_hours"] = total_duration_minutes / 60

        return stats
