"""
CompanyAlerts entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyAlertsEntity(BaseEntity):
    """
    Handles all Company Alert-related operations for the Autotask API.

    Company Alerts in Autotask represent automated notifications and alerts
    configured at the company level.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company_alert(
        self,
        company_id: int,
        alert_type_id: int,
        alert_criteria: Dict[str, Any],
        notification_recipients: List[str],
        is_active: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company alert.

        Args:
            company_id: ID of the company
            alert_type_id: Type of alert to create
            alert_criteria: Criteria that triggers the alert
            notification_recipients: List of recipients for notifications
            is_active: Whether the alert is active
            **kwargs: Additional alert fields

        Returns:
            Created company alert data
        """
        alert_data = {
            "CompanyID": company_id,
            "AlertTypeID": alert_type_id,
            "AlertCriteria": alert_criteria,
            "NotificationRecipients": notification_recipients,
            "IsActive": is_active,
            **kwargs,
        }

        return self.create(alert_data)

    def get_company_alerts(
        self,
        company_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all alerts for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active alerts
            limit: Maximum number of alerts to return

        Returns:
            List of company alerts
        """
        filters = [QueryFilter(field="CompanyID", op="eq", value=company_id)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_alerts_by_type(
        self,
        alert_type_id: int,
        company_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get alerts by alert type, optionally filtered by company.

        Args:
            alert_type_id: Type of alert to filter by
            company_id: Optional company ID to filter by
            limit: Maximum number of alerts to return

        Returns:
            List of alerts matching the criteria
        """
        filters = [QueryFilter(field="AlertTypeID", op="eq", value=alert_type_id)]

        if company_id:
            filters.append(QueryFilter(field="CompanyID", op="eq", value=company_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def activate_alert(self, alert_id: int) -> Dict[str, Any]:
        """
        Activate a company alert.

        Args:
            alert_id: ID of alert to activate

        Returns:
            Updated alert data
        """
        return self.update_by_id(alert_id, {"IsActive": True})

    def deactivate_alert(self, alert_id: int) -> Dict[str, Any]:
        """
        Deactivate a company alert.

        Args:
            alert_id: ID of alert to deactivate

        Returns:
            Updated alert data
        """
        return self.update_by_id(alert_id, {"IsActive": False})

    def update_alert_criteria(
        self,
        alert_id: int,
        alert_criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update alert criteria for a company alert.

        Args:
            alert_id: ID of alert to update
            alert_criteria: New alert criteria

        Returns:
            Updated alert data
        """
        return self.update_by_id(alert_id, {"AlertCriteria": alert_criteria})

    def update_notification_recipients(
        self,
        alert_id: int,
        recipients: List[str],
    ) -> Dict[str, Any]:
        """
        Update notification recipients for a company alert.

        Args:
            alert_id: ID of alert to update
            recipients: List of new recipients

        Returns:
            Updated alert data
        """
        return self.update_by_id(alert_id, {"NotificationRecipients": recipients})

    def get_triggered_alerts(
        self,
        company_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get alerts that have been triggered for a company.

        Args:
            company_id: ID of the company
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            limit: Maximum number of alerts to return

        Returns:
            List of triggered alerts
        """
        filters = [
            QueryFilter(field="CompanyID", op="eq", value=company_id),
            QueryFilter(field="IsTriggered", op="eq", value=True),
        ]

        if start_date:
            filters.append(QueryFilter(field="TriggerDate", op="gte", value=start_date))
        if end_date:
            filters.append(QueryFilter(field="TriggerDate", op="lte", value=end_date))

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def bulk_activate_alerts(self, alert_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Activate multiple company alerts in bulk.

        Args:
            alert_ids: List of alert IDs to activate

        Returns:
            List of updated alert data
        """
        update_data = [{"id": alert_id, "IsActive": True} for alert_id in alert_ids]
        return self.batch_update(update_data)

    def bulk_deactivate_alerts(self, alert_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Deactivate multiple company alerts in bulk.

        Args:
            alert_ids: List of alert IDs to deactivate

        Returns:
            List of updated alert data
        """
        update_data = [{"id": alert_id, "IsActive": False} for alert_id in alert_ids]
        return self.batch_update(update_data)
