"""
NotificationHistory entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class NotificationHistoryEntity(BaseEntity):
    """
    Handles all Notification History-related operations for the Autotask API.

    Notification History tracks all notifications that have been sent by the system.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def get_notifications_by_recipient(
        self, recipient_email: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all notifications sent to a specific recipient.

        Args:
            recipient_email: Email address of the recipient
            limit: Maximum number of records to return

        Returns:
            List of notifications sent to the recipient
        """
        filters = [QueryFilter(field="RecipientEmail", op="eq", value=recipient_email)]

        return self.query(filters=filters, max_records=limit)

    def get_notifications_by_type(
        self, notification_type: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get notifications by type.

        Args:
            notification_type: Type of notification (e.g., 'Email', 'SMS', 'Push')
            limit: Maximum number of records to return

        Returns:
            List of notifications of the specified type
        """
        filters = [
            QueryFilter(field="NotificationType", op="eq", value=notification_type)
        ]

        return self.query(filters=filters, max_records=limit)

    def get_notifications_by_status(
        self, status: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get notifications by delivery status.

        Args:
            status: Delivery status (e.g., 'Sent', 'Failed', 'Pending')
            limit: Maximum number of records to return

        Returns:
            List of notifications with the specified status
        """
        filters = [QueryFilter(field="Status", op="eq", value=status)]

        return self.query(filters=filters, max_records=limit)

    def get_failed_notifications(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all failed notification deliveries.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of failed notifications
        """
        return self.get_notifications_by_status("Failed", limit=limit)

    def get_recent_notifications(
        self, days: int = 7, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get notifications from the last N days.

        Args:
            days: Number of days to look back
            limit: Maximum number of records to return

        Returns:
            List of recent notifications
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        filters = [QueryFilter(field="SentDate", op="ge", value=start_date)]

        return self.query(filters=filters, max_records=limit)

    def get_notifications_by_entity(
        self, entity_type: str, entity_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get notifications related to a specific entity.

        Args:
            entity_type: Type of entity (e.g., 'Ticket', 'Project', 'Contract')
            entity_id: ID of the entity
            limit: Maximum number of records to return

        Returns:
            List of notifications for the entity
        """
        filters = [
            QueryFilter(field="EntityType", op="eq", value=entity_type),
            QueryFilter(field="EntityID", op="eq", value=entity_id),
        ]

        return self.query(filters=filters, max_records=limit)

    def search_notifications_by_subject(
        self, subject_text: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search notifications by subject line.

        Args:
            subject_text: Text to search for in subject
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of notifications matching the subject
        """
        if exact_match:
            filters = [QueryFilter(field="Subject", op="eq", value=subject_text)]
        else:
            filters = [QueryFilter(field="Subject", op="contains", value=subject_text)]

        return self.query(filters=filters, max_records=limit)

    def get_notification_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get notification delivery statistics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with notification statistics
        """
        recent_notifications = self.get_recent_notifications(days=days)

        stats = {
            "total_notifications": len(recent_notifications),
            "sent_successfully": len(
                [n for n in recent_notifications if n.get("Status") == "Sent"]
            ),
            "failed_deliveries": len(
                [n for n in recent_notifications if n.get("Status") == "Failed"]
            ),
            "pending_deliveries": len(
                [n for n in recent_notifications if n.get("Status") == "Pending"]
            ),
        }

        # Calculate success rate
        if stats["total_notifications"] > 0:
            stats["success_rate"] = (
                stats["sent_successfully"] / stats["total_notifications"]
            ) * 100
        else:
            stats["success_rate"] = 0

        # Group by notification type
        type_counts = {}
        for notification in recent_notifications:
            notif_type = notification.get("NotificationType", "Unknown")
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1

        stats["by_type"] = type_counts

        return stats

    def get_notifications_by_date_range(
        self, start_date: str, end_date: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get notifications within a specific date range.

        Args:
            start_date: Start date for the range (YYYY-MM-DD)
            end_date: End date for the range (YYYY-MM-DD)
            limit: Maximum number of records to return

        Returns:
            List of notifications within the date range
        """
        filters = [
            QueryFilter(field="SentDate", op="ge", value=start_date),
            QueryFilter(field="SentDate", op="le", value=end_date),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_delivery_report(
        self, recipient_email: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a delivery report for a specific recipient.

        Args:
            recipient_email: Email address of the recipient
            days: Number of days to include in the report

        Returns:
            Dictionary with delivery report data
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Get notifications for the recipient in the date range
        filters = [
            QueryFilter(field="RecipientEmail", op="eq", value=recipient_email),
            QueryFilter(field="SentDate", op="ge", value=start_date),
        ]

        notifications = self.query(filters=filters)

        report = {
            "recipient": recipient_email,
            "period_days": days,
            "total_notifications": len(notifications),
            "successful_deliveries": len(
                [n for n in notifications if n.get("Status") == "Sent"]
            ),
            "failed_deliveries": len(
                [n for n in notifications if n.get("Status") == "Failed"]
            ),
            "delivery_methods": {},
            "entity_breakdown": {},
        }

        # Analyze delivery methods
        for notification in notifications:
            method = notification.get("NotificationType", "Unknown")
            if method not in report["delivery_methods"]:
                report["delivery_methods"][method] = {"total": 0, "successful": 0}

            report["delivery_methods"][method]["total"] += 1
            if notification.get("Status") == "Sent":
                report["delivery_methods"][method]["successful"] += 1

        # Analyze by entity type
        for notification in notifications:
            entity_type = notification.get("EntityType", "Unknown")
            report["entity_breakdown"][entity_type] = (
                report["entity_breakdown"].get(entity_type, 0) + 1
            )

        return report
