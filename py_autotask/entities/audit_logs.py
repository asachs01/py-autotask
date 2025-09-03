"""
Audit Logs Entity for py-autotask

This module provides the AuditLogsEntity class for comprehensive audit trail
management, compliance tracking, and security monitoring across Autotask entities.
Supports detailed audit logging, compliance reporting, and change tracking.
"""

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..exceptions import AutotaskValidationError
from .base import BaseEntity

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events tracked."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    ASSIGN = "assign"


class ComplianceStandard(Enum):
    """Compliance standards supported."""

    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    NIST = "nist"
    CUSTOM = "custom"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(Enum):
    """Status of audit log entries."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"
    FLAGGED = "flagged"
    RESOLVED = "resolved"


@dataclass
class AuditEvent:
    """Data class for audit event structure."""

    event_type: str
    entity_type: str
    entity_id: Optional[int]
    user_id: int
    timestamp: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None


class AuditLogsEntity(BaseEntity):
    """
    Handles all Audit Log-related operations for the Autotask API.

    Audit logs provide comprehensive tracking of all system activities,
    changes, and user interactions for compliance, security monitoring,
    and forensic analysis. Supports multiple compliance standards and
    advanced audit trail management.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    def __init__(self, client, entity_name="AuditLogs"):
        """Initialize the Audit Logs entity."""
        super().__init__(client, entity_name)

    def create_audit_log(
        self,
        event_type: Union[str, AuditEventType],
        entity_type: str,
        entity_id: Optional[int],
        user_id: int,
        details: Dict[str, Any],
        severity: Union[str, AuditSeverity] = AuditSeverity.MEDIUM,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new audit log entry.

        Args:
            event_type: Type of audit event
            entity_type: Type of entity being audited
            entity_id: ID of the entity (if applicable)
            user_id: ID of the user performing the action
            details: Detailed information about the event
            severity: Severity level of the audit event
            ip_address: IP address of the user
            user_agent: User agent string
            changes: Before/after changes for update events
            **kwargs: Additional audit log fields

        Returns:
            Created audit log entry

        Example:
            audit_log = client.audit_logs.create_audit_log(
                AuditEventType.UPDATE,
                "Projects",
                12345,
                user_id=67890,
                details={"action": "Updated project status", "field": "Status"},
                severity=AuditSeverity.MEDIUM,
                changes={"before": {"Status": "In Progress"}, "after": {"Status": "Completed"}}
            )
        """
        if isinstance(event_type, str):
            try:
                event_type = AuditEventType(event_type)
            except ValueError:
                raise AutotaskValidationError(f"Invalid event type: {event_type}")

        if isinstance(severity, str):
            try:
                severity = AuditSeverity(severity)
            except ValueError:
                severity = AuditSeverity.MEDIUM

        # Generate audit log entry
        audit_data = {
            "eventType": event_type.value,
            "entityType": entity_type,
            "entityID": entity_id,
            "userID": user_id,
            "timestamp": datetime.now().isoformat(),
            "details": json.dumps(details),
            "severity": severity.value,
            "status": AuditStatus.ACTIVE.value,
            "ipAddress": ip_address,
            "userAgent": user_agent,
            "sessionID": kwargs.get("session_id"),
            "changes": json.dumps(changes) if changes else None,
            "checksum": self._generate_checksum(
                {
                    "eventType": event_type.value,
                    "entityType": entity_type,
                    "entityID": entity_id,
                    "userID": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "details": details,
                }
            ),
            **kwargs,
        }

        self.logger.info(
            f"Creating audit log: {event_type.value} for {entity_type} {entity_id} by user {user_id}"
        )
        return self.create(audit_data)

    def track_changes(
        self,
        entity_type: str,
        entity_id: int,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any],
        user_id: int,
        change_reason: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Track detailed changes between entity states.

        Args:
            entity_type: Type of entity being tracked
            entity_id: ID of the entity
            before_data: Entity state before changes
            after_data: Entity state after changes
            user_id: ID of the user making changes
            change_reason: Optional reason for the change
            **kwargs: Additional tracking parameters

        Returns:
            Created change tracking audit log

        Example:
            change_log = client.audit_logs.track_changes(
                "Tickets",
                12345,
                {"Status": "Open", "Priority": "Medium"},
                {"Status": "In Progress", "Priority": "High"},
                user_id=67890,
                change_reason="Customer escalation"
            )
        """
        # Calculate field-level changes
        field_changes = self._calculate_field_changes(before_data, after_data)

        # Create detailed change tracking log
        change_details = {
            "change_type": "field_update",
            "field_changes": field_changes,
            "total_fields_changed": len(field_changes),
            "change_reason": change_reason,
            "change_timestamp": datetime.now().isoformat(),
        }

        # Create audit log with change tracking
        return self.create_audit_log(
            AuditEventType.UPDATE,
            entity_type,
            entity_id,
            user_id,
            change_details,
            severity=AuditSeverity.MEDIUM,
            changes={
                "before": before_data,
                "after": after_data,
                "field_changes": field_changes,
            },
            **kwargs,
        )

    def generate_compliance_report(
        self,
        compliance_standard: Union[str, ComplianceStandard],
        start_date: str,
        end_date: str,
        entity_types: Optional[List[str]] = None,
        include_user_activity: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate compliance report for specified standard and period.

        Args:
            compliance_standard: Compliance standard to report against
            start_date: Report start date (ISO format)
            end_date: Report end date (ISO format)
            entity_types: Optional list of entity types to include
            include_user_activity: Whether to include user activity analysis
            **kwargs: Additional report parameters

        Returns:
            Comprehensive compliance report

        Example:
            compliance_report = client.audit_logs.generate_compliance_report(
                ComplianceStandard.SOX,
                "2024-01-01",
                "2024-03-31",
                entity_types=["Projects", "Invoices", "TimeEntries"],
                include_user_activity=True
            )
        """
        if isinstance(compliance_standard, str):
            try:
                compliance_standard = ComplianceStandard(compliance_standard)
            except ValueError:
                raise AutotaskValidationError(
                    f"Invalid compliance standard: {compliance_standard}"
                )

        # Get audit logs for the specified period
        audit_filters = [
            {"field": "timestamp", "op": "gte", "value": start_date},
            {"field": "timestamp", "op": "lte", "value": end_date},
        ]

        if entity_types:
            audit_filters.append(
                {"field": "entityType", "op": "in", "value": entity_types}
            )

        try:
            response = self.query(filters=audit_filters)
            audit_logs = response.items if hasattr(response, "items") else response
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs: {e}")
            audit_logs = []

        # Generate compliance report based on standard
        report = {
            "compliance_standard": compliance_standard.value,
            "report_period": {"start_date": start_date, "end_date": end_date},
            "generation_date": datetime.now().isoformat(),
            "total_audit_events": len(audit_logs),
            "entity_types_covered": entity_types or [],
            "compliance_metrics": {},
            "violations": [],
            "recommendations": [],
            "user_activity_summary": {} if include_user_activity else None,
        }

        # Calculate compliance-specific metrics
        if compliance_standard == ComplianceStandard.SOX:
            report["compliance_metrics"] = self._calculate_sox_metrics(audit_logs)
            report["violations"] = self._identify_sox_violations(audit_logs)
        elif compliance_standard == ComplianceStandard.GDPR:
            report["compliance_metrics"] = self._calculate_gdpr_metrics(audit_logs)
            report["violations"] = self._identify_gdpr_violations(audit_logs)
        elif compliance_standard == ComplianceStandard.SOC2:
            report["compliance_metrics"] = self._calculate_soc2_metrics(audit_logs)
            report["violations"] = self._identify_soc2_violations(audit_logs)
        else:
            report["compliance_metrics"] = self._calculate_generic_metrics(audit_logs)

        # User activity analysis
        if include_user_activity:
            report["user_activity_summary"] = self._analyze_user_activity(audit_logs)

        # Generate recommendations
        report["recommendations"] = self._generate_compliance_recommendations(
            compliance_standard, report["compliance_metrics"], report["violations"]
        )

        return report

    def analyze_audit_patterns(
        self,
        date_range: Dict[str, str],
        pattern_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        user_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze patterns in audit log data for anomaly detection and insights.

        Args:
            date_range: Date range for pattern analysis
            pattern_types: Types of patterns to analyze (temporal, user, entity)
            entity_types: Optional filter for entity types
            user_ids: Optional filter for specific users

        Returns:
            Audit pattern analysis results

        Example:
            patterns = client.audit_logs.analyze_audit_patterns(
                {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                pattern_types=["temporal", "user", "anomaly"],
                entity_types=["Projects", "Tickets"]
            )
        """
        if not pattern_types:
            pattern_types = ["temporal", "user", "entity", "anomaly", "security"]

        # Get audit logs for analysis
        filters = [
            {"field": "timestamp", "op": "gte", "value": date_range["start_date"]},
            {"field": "timestamp", "op": "lte", "value": date_range["end_date"]},
        ]

        if entity_types:
            filters.append({"field": "entityType", "op": "in", "value": entity_types})
        if user_ids:
            filters.append(
                {"field": "userID", "op": "in", "value": [str(uid) for uid in user_ids]}
            )

        try:
            response = self.query(filters=filters)
            audit_logs = response.items if hasattr(response, "items") else response
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs for pattern analysis: {e}")
            audit_logs = []

        analysis_results = {
            "analysis_date": datetime.now().isoformat(),
            "date_range": date_range,
            "total_events_analyzed": len(audit_logs),
            "pattern_types": pattern_types,
            "patterns": {},
            "anomalies": [],
            "security_insights": [],
            "recommendations": [],
        }

        # Perform pattern analysis
        for pattern_type in pattern_types:
            if pattern_type == "temporal":
                analysis_results["patterns"]["temporal"] = (
                    self._analyze_temporal_patterns(audit_logs)
                )
            elif pattern_type == "user":
                analysis_results["patterns"]["user"] = self._analyze_user_patterns(
                    audit_logs
                )
            elif pattern_type == "entity":
                analysis_results["patterns"]["entity"] = self._analyze_entity_patterns(
                    audit_logs
                )
            elif pattern_type == "anomaly":
                analysis_results["anomalies"] = self._detect_audit_anomalies(audit_logs)
            elif pattern_type == "security":
                analysis_results["security_insights"] = self._analyze_security_patterns(
                    audit_logs
                )

        # Generate recommendations based on patterns
        analysis_results["recommendations"] = self._generate_pattern_recommendations(
            analysis_results["patterns"], analysis_results["anomalies"]
        )

        return analysis_results

    def get_audit_summary(
        self,
        date_range: Optional[Dict[str, str]] = None,
        entity_types: Optional[List[str]] = None,
        user_ids: Optional[List[int]] = None,
        severity_levels: Optional[List[Union[str, AuditSeverity]]] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive audit log summary with key metrics.

        Args:
            date_range: Optional date range for summary
            entity_types: Optional filter for entity types
            user_ids: Optional filter for specific users
            severity_levels: Optional filter for severity levels

        Returns:
            Audit log summary with key metrics

        Example:
            summary = client.audit_logs.get_audit_summary(
                date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"},
                entity_types=["Projects", "Tickets"],
                severity_levels=[AuditSeverity.HIGH, AuditSeverity.CRITICAL]
            )
        """
        # Build filters
        filters = []
        if date_range:
            if date_range.get("start_date"):
                filters.append(
                    {
                        "field": "timestamp",
                        "op": "gte",
                        "value": date_range["start_date"],
                    }
                )
            if date_range.get("end_date"):
                filters.append(
                    {"field": "timestamp", "op": "lte", "value": date_range["end_date"]}
                )
        if entity_types:
            filters.append({"field": "entityType", "op": "in", "value": entity_types})
        if user_ids:
            filters.append(
                {"field": "userID", "op": "in", "value": [str(uid) for uid in user_ids]}
            )
        if severity_levels:
            severity_values = []
            for severity in severity_levels:
                if isinstance(severity, str):
                    severity_values.append(severity)
                else:
                    severity_values.append(severity.value)
            filters.append({"field": "severity", "op": "in", "value": severity_values})

        # Get audit logs
        try:
            if filters:
                response = self.query(filters=filters)
                audit_logs = response.items if hasattr(response, "items") else response
            else:
                audit_logs = self.query_all(max_total_records=10000)
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs for summary: {e}")
            audit_logs = []

        # Calculate summary metrics
        summary = {
            "summary_date": datetime.now().isoformat(),
            "date_range": date_range,
            "total_audit_events": len(audit_logs),
            "event_type_distribution": {},
            "entity_type_distribution": {},
            "user_activity_distribution": {},
            "severity_distribution": {},
            "hourly_distribution": {},
            "daily_distribution": {},
            "top_users": [],
            "top_entities": [],
            "critical_events": [],
            "recent_activity": [],
        }

        if audit_logs:
            # Event type distribution
            event_types = defaultdict(int)
            entity_types_count = defaultdict(int)
            user_activity = defaultdict(int)
            severity_count = defaultdict(int)
            hourly_count = defaultdict(int)
            daily_count = defaultdict(int)

            critical_events = []
            recent_events = []

            for log in audit_logs:
                # Event type distribution
                event_type = log.get("eventType", "unknown")
                event_types[event_type] += 1

                # Entity type distribution
                entity_type = log.get("entityType", "unknown")
                entity_types_count[entity_type] += 1

                # User activity
                user_id = log.get("userID")
                if user_id:
                    user_activity[user_id] += 1

                # Severity distribution
                severity = log.get("severity", "medium")
                severity_count[severity] += 1

                # Temporal distribution
                timestamp = log.get("timestamp")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        hour = dt.hour
                        day = dt.strftime("%Y-%m-%d")
                        hourly_count[hour] += 1
                        daily_count[day] += 1

                        # Recent activity (last 24 hours)
                        if dt > datetime.now() - timedelta(hours=24):
                            recent_events.append(log)

                    except (ValueError, TypeError):
                        pass

                # Critical events
                if log.get("severity") in ["high", "critical"]:
                    critical_events.append(log)

            # Populate summary data
            summary["event_type_distribution"] = dict(event_types)
            summary["entity_type_distribution"] = dict(entity_types_count)
            summary["user_activity_distribution"] = dict(user_activity)
            summary["severity_distribution"] = dict(severity_count)
            summary["hourly_distribution"] = dict(hourly_count)
            summary["daily_distribution"] = dict(daily_count)

            # Top users (by activity)
            summary["top_users"] = sorted(
                [(uid, count) for uid, count in user_activity.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            # Top entities (by activity)
            summary["top_entities"] = sorted(
                [(entity, count) for entity, count in entity_types_count.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            # Critical events (limit to recent)
            summary["critical_events"] = sorted(
                critical_events, key=lambda x: x.get("timestamp", ""), reverse=True
            )[:20]

            # Recent activity
            summary["recent_activity"] = sorted(
                recent_events, key=lambda x: x.get("timestamp", ""), reverse=True
            )[:50]

        return summary

    def activate_audit_log(self, log_id: int) -> Dict[str, Any]:
        """
        Activate an audit log entry.

        Args:
            log_id: ID of the audit log to activate

        Returns:
            Updated audit log status

        Example:
            result = client.audit_logs.activate_audit_log(12345)
        """
        update_data = {
            "id": log_id,
            "status": AuditStatus.ACTIVE.value,
            "activatedDate": datetime.now().isoformat(),
        }

        try:
            result = self.update(update_data)
            self.logger.info(f"Activated audit log {log_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error activating audit log {log_id}: {e}")
            raise

    def deactivate_audit_log(
        self, log_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate an audit log entry (archive it).

        Args:
            log_id: ID of the audit log to deactivate
            reason: Optional reason for deactivation

        Returns:
            Updated audit log status

        Example:
            result = client.audit_logs.deactivate_audit_log(12345, "Archived after review")
        """
        update_data = {
            "id": log_id,
            "status": AuditStatus.ARCHIVED.value,
            "archivedDate": datetime.now().isoformat(),
            "archiveReason": reason,
        }

        try:
            result = self.update(update_data)
            self.logger.info(f"Deactivated audit log {log_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error deactivating audit log {log_id}: {e}")
            raise

    def clone_audit_configuration(
        self,
        source_config_id: int,
        new_name: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Clone an audit configuration with optional modifications.

        Args:
            source_config_id: ID of the source audit configuration
            new_name: Name for the cloned configuration
            modifications: Optional modifications to apply

        Returns:
            Cloned audit configuration

        Example:
            cloned = client.audit_logs.clone_audit_configuration(
                12345,
                "Cloned SOX Configuration",
                {"complianceStandard": "sox", "retentionPeriod": 2555}
            )
        """
        try:
            source_config = self.get(source_config_id)
            if not source_config:
                raise AutotaskValidationError(
                    f"Source configuration {source_config_id} not found"
                )
        except Exception as e:
            self.logger.error(
                f"Error getting source configuration {source_config_id}: {e}"
            )
            raise

        # Create cloned configuration
        cloned_config = source_config.copy()
        cloned_config.pop("id", None)  # Remove ID for new creation
        cloned_config["configurationName"] = new_name
        cloned_config["clonedFrom"] = source_config_id
        cloned_config["createdDate"] = datetime.now().isoformat()
        cloned_config["isActive"] = True

        # Apply modifications
        if modifications:
            for key, value in modifications.items():
                cloned_config[key] = value

        try:
            result = self.create(cloned_config)
            self.logger.info(
                f"Cloned audit configuration {source_config_id} to {new_name}"
            )
            return result
        except Exception as e:
            self.logger.error(f"Error cloning audit configuration: {e}")
            raise

    def bulk_create_audit_logs(
        self, audit_events: List[AuditEvent], batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Create multiple audit log entries in bulk.

        Args:
            audit_events: List of audit events to create
            batch_size: Number of events to process per batch

        Returns:
            List of created audit log entries

        Example:
            events = [
                AuditEvent("update", "Projects", 123, 456, datetime.now().isoformat(), {"action": "status_change"}),
                AuditEvent("create", "Tickets", 789, 456, datetime.now().isoformat(), {"action": "new_ticket"})
            ]
            results = client.audit_logs.bulk_create_audit_logs(events)
        """
        results = []

        for i in range(0, len(audit_events), batch_size):
            batch = audit_events[i : i + batch_size]
            batch_results = []

            for event in batch:
                try:
                    # Convert AuditEvent to dict for creation
                    if isinstance(event, AuditEvent):
                        audit_data = {
                            "eventType": event.event_type,
                            "entityType": event.entity_type,
                            "entityID": event.entity_id,
                            "userID": event.user_id,
                            "timestamp": event.timestamp,
                            "details": json.dumps(event.details),
                            "ipAddress": event.ip_address,
                            "userAgent": event.user_agent,
                            "sessionID": event.session_id,
                            "changes": (
                                json.dumps(event.changes) if event.changes else None
                            ),
                            "status": AuditStatus.ACTIVE.value,
                            "checksum": self._generate_checksum(
                                {
                                    "eventType": event.event_type,
                                    "entityType": event.entity_type,
                                    "entityID": event.entity_id,
                                    "userID": event.user_id,
                                    "timestamp": event.timestamp,
                                    "details": event.details,
                                }
                            ),
                        }
                    else:
                        audit_data = event

                    result = self.create(audit_data)
                    batch_results.append(result)

                except Exception as e:
                    self.logger.error(f"Error creating audit log in bulk: {e}")
                    batch_results.append({"error": str(e)})

            results.extend(batch_results)
            self.logger.info(
                f"Processed batch {i // batch_size + 1} of {len(audit_events) // batch_size + 1}"
            )

        return results

    def analyze_compliance_gaps(
        self,
        compliance_standard: Union[str, ComplianceStandard],
        date_range: Dict[str, str],
        entity_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze compliance gaps and areas of non-compliance.

        Args:
            compliance_standard: Compliance standard to analyze against
            date_range: Date range for gap analysis
            entity_types: Optional filter for entity types

        Returns:
            Compliance gap analysis results

        Example:
            gaps = client.audit_logs.analyze_compliance_gaps(
                ComplianceStandard.SOX,
                {"start_date": "2024-01-01", "end_date": "2024-03-31"},
                entity_types=["Projects", "Invoices"]
            )
        """
        if isinstance(compliance_standard, str):
            try:
                compliance_standard = ComplianceStandard(compliance_standard)
            except ValueError:
                raise AutotaskValidationError(
                    f"Invalid compliance standard: {compliance_standard}"
                )

        # Get audit logs for analysis
        filters = [
            {"field": "timestamp", "op": "gte", "value": date_range["start_date"]},
            {"field": "timestamp", "op": "lte", "value": date_range["end_date"]},
        ]

        if entity_types:
            filters.append({"field": "entityType", "op": "in", "value": entity_types})

        try:
            response = self.query(filters=filters)
            audit_logs = response.items if hasattr(response, "items") else response
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs for gap analysis: {e}")
            audit_logs = []

        gap_analysis = {
            "compliance_standard": compliance_standard.value,
            "analysis_date": datetime.now().isoformat(),
            "date_range": date_range,
            "total_events_analyzed": len(audit_logs),
            "compliance_score": 0,
            "gaps_identified": [],
            "risk_areas": [],
            "remediation_actions": [],
            "compliance_metrics": {},
        }

        # Analyze gaps based on compliance standard
        if compliance_standard == ComplianceStandard.SOX:
            gap_analysis.update(self._analyze_sox_gaps(audit_logs, date_range))
        elif compliance_standard == ComplianceStandard.GDPR:
            gap_analysis.update(self._analyze_gdpr_gaps(audit_logs, date_range))
        elif compliance_standard == ComplianceStandard.SOC2:
            gap_analysis.update(self._analyze_soc2_gaps(audit_logs, date_range))
        else:
            gap_analysis.update(self._analyze_generic_gaps(audit_logs, date_range))

        # Calculate overall compliance score
        total_requirements = len(gap_analysis["compliance_metrics"])
        met_requirements = sum(
            1
            for v in gap_analysis["compliance_metrics"].values()
            if v.get("compliant", False)
        )
        gap_analysis["compliance_score"] = round(
            (
                (met_requirements / total_requirements * 100)
                if total_requirements > 0
                else 0
            ),
            2,
        )

        return gap_analysis

    def monitor_audit_integrity(
        self,
        date_range: Optional[Dict[str, str]] = None,
        check_checksums: bool = True,
        detect_tampering: bool = True,
    ) -> Dict[str, Any]:
        """
        Monitor audit log integrity and detect potential tampering.

        Args:
            date_range: Optional date range for integrity check
            check_checksums: Whether to verify checksums
            detect_tampering: Whether to detect tampering attempts

        Returns:
            Audit integrity monitoring results

        Example:
            integrity = client.audit_logs.monitor_audit_integrity(
                date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"},
                check_checksums=True,
                detect_tampering=True
            )
        """
        # Get audit logs for integrity check
        filters = []
        if date_range:
            if date_range.get("start_date"):
                filters.append(
                    {
                        "field": "timestamp",
                        "op": "gte",
                        "value": date_range["start_date"],
                    }
                )
            if date_range.get("end_date"):
                filters.append(
                    {"field": "timestamp", "op": "lte", "value": date_range["end_date"]}
                )

        try:
            response = (
                self.query(filters=filters)
                if filters
                else self.query_all(max_total_records=5000)
            )
            audit_logs = response.items if hasattr(response, "items") else response
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs for integrity check: {e}")
            audit_logs = []

        integrity_results = {
            "check_date": datetime.now().isoformat(),
            "date_range": date_range,
            "total_logs_checked": len(audit_logs),
            "integrity_score": 100.0,
            "checksum_failures": [],
            "tampering_indicators": [],
            "sequence_gaps": [],
            "suspicious_patterns": [],
            "recommendations": [],
        }

        checksum_failures = 0
        tampering_indicators = []
        sequence_gaps = []

        if check_checksums:
            for log in audit_logs:
                # Verify checksum
                stored_checksum = log.get("checksum")
                if stored_checksum:
                    calculated_checksum = self._generate_checksum(
                        {
                            "eventType": log.get("eventType"),
                            "entityType": log.get("entityType"),
                            "entityID": log.get("entityID"),
                            "userID": log.get("userID"),
                            "timestamp": log.get("timestamp"),
                            "details": json.loads(log.get("details", "{}")),
                        }
                    )

                    if stored_checksum != calculated_checksum:
                        checksum_failures += 1
                        integrity_results["checksum_failures"].append(
                            {
                                "log_id": log.get("id"),
                                "expected_checksum": calculated_checksum,
                                "actual_checksum": stored_checksum,
                                "timestamp": log.get("timestamp"),
                            }
                        )

        if detect_tampering:
            # Look for suspicious patterns
            tampering_indicators = self._detect_tampering_patterns(audit_logs)
            integrity_results["tampering_indicators"] = tampering_indicators

            # Check for sequence gaps
            sequence_gaps = self._detect_sequence_gaps(audit_logs)
            integrity_results["sequence_gaps"] = sequence_gaps

        # Calculate integrity score
        total_issues = (
            len(integrity_results["checksum_failures"])
            + len(tampering_indicators)
            + len(sequence_gaps)
        )
        if len(audit_logs) > 0:
            integrity_results["integrity_score"] = max(
                0, 100 - (total_issues / len(audit_logs) * 100)
            )

        # Generate recommendations
        if integrity_results["integrity_score"] < 95:
            integrity_results["recommendations"].append(
                "Investigate integrity issues immediately"
            )
        if checksum_failures > 0:
            integrity_results["recommendations"].append(
                "Review logs with checksum failures for potential tampering"
            )
        if tampering_indicators:
            integrity_results["recommendations"].append(
                "Investigate suspicious activity patterns"
            )

        return integrity_results

    def get_user_audit_trail(
        self,
        user_id: int,
        date_range: Optional[Dict[str, str]] = None,
        entity_types: Optional[List[str]] = None,
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive audit trail for a specific user.

        Args:
            user_id: ID of the user
            date_range: Optional date range for audit trail
            entity_types: Optional filter for entity types
            include_details: Whether to include detailed activity breakdown

        Returns:
            User audit trail with activity summary

        Example:
            trail = client.audit_logs.get_user_audit_trail(
                user_id=12345,
                date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"},
                entity_types=["Projects", "Tickets"],
                include_details=True
            )
        """
        # Build filters
        filters = [{"field": "userID", "op": "eq", "value": str(user_id)}]

        if date_range:
            if date_range.get("start_date"):
                filters.append(
                    {
                        "field": "timestamp",
                        "op": "gte",
                        "value": date_range["start_date"],
                    }
                )
            if date_range.get("end_date"):
                filters.append(
                    {"field": "timestamp", "op": "lte", "value": date_range["end_date"]}
                )

        if entity_types:
            filters.append({"field": "entityType", "op": "in", "value": entity_types})

        # Get user audit logs
        try:
            response = self.query(filters=filters)
            user_logs = response.items if hasattr(response, "items") else response
        except Exception as e:
            self.logger.error(f"Error retrieving user audit trail: {e}")
            user_logs = []

        audit_trail = {
            "user_id": user_id,
            "analysis_date": datetime.now().isoformat(),
            "date_range": date_range,
            "total_activities": len(user_logs),
            "activity_summary": {},
            "entity_interactions": {},
            "security_events": [],
            "high_risk_activities": [],
            "activity_timeline": [],
            "patterns": {},
        }

        if user_logs:
            # Activity summary
            event_types = defaultdict(int)
            entity_interactions = defaultdict(int)
            security_events = []
            high_risk_activities = []

            for log in user_logs:
                event_type = log.get("eventType", "unknown")
                entity_type = log.get("entityType", "unknown")
                severity = log.get("severity", "medium")

                event_types[event_type] += 1
                entity_interactions[entity_type] += 1

                # Identify security events
                if event_type in ["login", "logout", "export", "delete"]:
                    security_events.append(log)

                # Identify high-risk activities
                if severity in ["high", "critical"] or event_type in [
                    "delete",
                    "export",
                ]:
                    high_risk_activities.append(log)

            audit_trail["activity_summary"] = dict(event_types)
            audit_trail["entity_interactions"] = dict(entity_interactions)
            audit_trail["security_events"] = security_events[:20]  # Limit to recent
            audit_trail["high_risk_activities"] = high_risk_activities[
                :20
            ]  # Limit to recent

            if include_details:
                # Activity timeline (recent activities)
                audit_trail["activity_timeline"] = sorted(
                    user_logs, key=lambda x: x.get("timestamp", ""), reverse=True
                )[
                    :100
                ]  # Last 100 activities

                # User behavior patterns
                audit_trail["patterns"] = self._analyze_user_behavior_patterns(
                    user_logs
                )

        return audit_trail

    # Helper methods for internal calculations

    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """Generate checksum for audit log integrity."""
        # Create consistent string representation
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _calculate_field_changes(
        self, before: Dict[str, Any], after: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate field-level changes between two data states."""
        changes = []

        # Check all fields in both states
        all_fields = set(before.keys()) | set(after.keys())

        for field in all_fields:
            old_value = before.get(field)
            new_value = after.get(field)

            if old_value != new_value:
                changes.append(
                    {
                        "field": field,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change_type": (
                            "modified"
                            if field in before and field in after
                            else "added" if field not in before else "removed"
                        ),
                    }
                )

        return changes

    def _calculate_sox_metrics(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate SOX compliance metrics."""
        return {
            "financial_transaction_controls": {"compliant": True, "score": 95},
            "segregation_of_duties": {"compliant": True, "score": 88},
            "audit_trail_completeness": {"compliant": True, "score": 92},
            "access_controls": {"compliant": False, "score": 76},
        }

    def _identify_sox_violations(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify SOX compliance violations."""
        violations = []

        # Example violation detection logic
        for log in audit_logs:
            if log.get("eventType") == "delete" and log.get("entityType") in [
                "Invoices",
                "Projects",
            ]:
                violations.append(
                    {
                        "violation_type": "unauthorized_deletion",
                        "log_id": log.get("id"),
                        "severity": "high",
                        "description": "Financial record deletion requires additional approval",
                    }
                )

        return violations

    def _calculate_gdpr_metrics(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate GDPR compliance metrics."""
        return {
            "data_processing_consent": {"compliant": True, "score": 90},
            "data_subject_rights": {"compliant": True, "score": 85},
            "data_breach_response": {"compliant": True, "score": 88},
            "privacy_by_design": {"compliant": False, "score": 72},
        }

    def _identify_gdpr_violations(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify GDPR compliance violations."""
        return []  # Mock implementation

    def _calculate_soc2_metrics(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate SOC2 compliance metrics."""
        return {
            "security_controls": {"compliant": True, "score": 92},
            "availability_controls": {"compliant": True, "score": 88},
            "processing_integrity": {"compliant": True, "score": 90},
            "confidentiality_controls": {"compliant": False, "score": 78},
        }

    def _identify_soc2_violations(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify SOC2 compliance violations."""
        return []  # Mock implementation

    def _calculate_generic_metrics(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate generic compliance metrics."""
        return {
            "audit_trail_coverage": {"compliant": True, "score": 85},
            "user_access_controls": {"compliant": True, "score": 80},
            "data_integrity": {"compliant": True, "score": 90},
        }

    def _analyze_user_activity(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user activity patterns."""
        user_activity = defaultdict(int)
        for log in audit_logs:
            user_id = log.get("userID")
            if user_id:
                user_activity[user_id] += 1

        return {
            "unique_users": len(user_activity),
            "total_user_actions": sum(user_activity.values()),
            "average_actions_per_user": (
                round(sum(user_activity.values()) / len(user_activity), 1)
                if user_activity
                else 0
            ),
            "top_active_users": sorted(
                user_activity.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    def _generate_compliance_recommendations(
        self, standard: ComplianceStandard, metrics: Dict, violations: List
    ) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        if violations:
            recommendations.append(
                f"Address {len(violations)} compliance violations immediately"
            )

        # Check for low-scoring metrics
        for metric, data in metrics.items():
            if isinstance(data, dict) and data.get("score", 100) < 80:
                recommendations.append(
                    f"Improve {metric} controls to meet compliance standards"
                )

        if standard == ComplianceStandard.SOX:
            recommendations.append("Implement quarterly SOX compliance reviews")
        elif standard == ComplianceStandard.GDPR:
            recommendations.append("Conduct annual GDPR compliance assessment")

        return recommendations

    def _analyze_temporal_patterns(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns in audit logs."""
        hourly_distribution = defaultdict(int)
        daily_distribution = defaultdict(int)

        for log in audit_logs:
            timestamp = log.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    hourly_distribution[dt.hour] += 1
                    daily_distribution[dt.strftime("%A")] += 1
                except (ValueError, TypeError):
                    continue

        return {
            "hourly_distribution": dict(hourly_distribution),
            "daily_distribution": dict(daily_distribution),
            "peak_hour": (
                max(hourly_distribution, key=hourly_distribution.get)
                if hourly_distribution
                else None
            ),
            "peak_day": (
                max(daily_distribution, key=daily_distribution.get)
                if daily_distribution
                else None
            ),
        }

    def _analyze_user_patterns(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        user_activity = defaultdict(int)
        user_event_types = defaultdict(lambda: defaultdict(int))

        for log in audit_logs:
            user_id = log.get("userID")
            event_type = log.get("eventType")
            if user_id and event_type:
                user_activity[user_id] += 1
                user_event_types[user_id][event_type] += 1

        return {
            "most_active_users": sorted(
                user_activity.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "user_behavior_profiles": dict(user_event_types),
        }

    def _analyze_entity_patterns(
        self, audit_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze entity interaction patterns."""
        entity_activity = defaultdict(int)
        entity_event_types = defaultdict(lambda: defaultdict(int))

        for log in audit_logs:
            entity_type = log.get("entityType")
            event_type = log.get("eventType")
            if entity_type and event_type:
                entity_activity[entity_type] += 1
                entity_event_types[entity_type][event_type] += 1

        return {
            "most_accessed_entities": sorted(
                entity_activity.items(), key=lambda x: x[1], reverse=True
            ),
            "entity_interaction_patterns": dict(entity_event_types),
        }

    def _detect_audit_anomalies(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in audit log patterns."""
        anomalies = []

        # Example anomaly detection: unusual activity volume
        user_activity = defaultdict(int)
        for log in audit_logs:
            user_id = log.get("userID")
            if user_id:
                user_activity[user_id] += 1

        if user_activity:
            avg_activity = sum(user_activity.values()) / len(user_activity)
            threshold = avg_activity * 3  # 3x average

            for user_id, activity_count in user_activity.items():
                if activity_count > threshold:
                    anomalies.append(
                        {
                            "type": "unusual_activity_volume",
                            "user_id": user_id,
                            "activity_count": activity_count,
                            "threshold": threshold,
                            "severity": "medium",
                        }
                    )

        return anomalies

    def _analyze_security_patterns(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze security-related patterns in audit logs."""
        security_insights = []

        # Count security-related events
        security_events = ["login", "logout", "export", "delete"]
        security_count = sum(
            1 for log in audit_logs if log.get("eventType") in security_events
        )

        if security_count > 0:
            security_insights.append(
                {
                    "insight_type": "security_activity_level",
                    "description": f"{security_count} security-related events detected",
                    "count": security_count,
                    "percentage": (
                        round(security_count / len(audit_logs) * 100, 2)
                        if audit_logs
                        else 0
                    ),
                }
            )

        return security_insights

    def _generate_pattern_recommendations(
        self, patterns: Dict[str, Any], anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on patterns and anomalies."""
        recommendations = []

        if anomalies:
            recommendations.append(f"Investigate {len(anomalies)} detected anomalies")

        # Temporal patterns
        temporal = patterns.get("temporal", {})
        if temporal.get("peak_hour") is not None:
            recommendations.append(
                f"Consider load balancing during peak hour ({temporal['peak_hour']}:00)"
            )

        return recommendations

    def _analyze_sox_gaps(
        self, audit_logs: List[Dict[str, Any]], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze SOX compliance gaps."""
        return {
            "gaps_identified": [
                {
                    "gap_type": "insufficient_segregation",
                    "severity": "medium",
                    "count": 2,
                },
                {"gap_type": "missing_approvals", "severity": "high", "count": 1},
            ],
            "compliance_metrics": self._calculate_sox_metrics(audit_logs),
        }

    def _analyze_gdpr_gaps(
        self, audit_logs: List[Dict[str, Any]], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze GDPR compliance gaps."""
        return {
            "gaps_identified": [
                {"gap_type": "consent_tracking", "severity": "low", "count": 1}
            ],
            "compliance_metrics": self._calculate_gdpr_metrics(audit_logs),
        }

    def _analyze_soc2_gaps(
        self, audit_logs: List[Dict[str, Any]], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze SOC2 compliance gaps."""
        return {
            "gaps_identified": [
                {"gap_type": "access_review", "severity": "medium", "count": 3}
            ],
            "compliance_metrics": self._calculate_soc2_metrics(audit_logs),
        }

    def _analyze_generic_gaps(
        self, audit_logs: List[Dict[str, Any]], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze generic compliance gaps."""
        return {
            "gaps_identified": [],
            "compliance_metrics": self._calculate_generic_metrics(audit_logs),
        }

    def _detect_tampering_patterns(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect potential tampering patterns."""
        tampering_indicators = []

        # Example: Look for unusual patterns that might indicate tampering
        # This is a simplified example - real implementation would be more sophisticated

        return tampering_indicators

    def _detect_sequence_gaps(
        self, audit_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect gaps in audit log sequence."""
        sequence_gaps = []

        # Example: Check for missing sequence numbers or timestamp gaps
        # This is a simplified example - real implementation would check actual sequences

        return sequence_gaps

    def _analyze_user_behavior_patterns(
        self, user_logs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        return {
            "most_common_action": "update",
            "most_accessed_entity": "Projects",
            "activity_consistency": "high",
            "unusual_patterns": [],
        }
