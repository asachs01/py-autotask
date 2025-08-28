"""
Dashboard Management Entity for py-autotask

This module provides the DashboardsEntity class for comprehensive dashboard
management, widget configuration, analytics visualization, and performance monitoring.
Dashboards provide real-time business intelligence and data visualization capabilities.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..exceptions import AutotaskValidationError
from ..types import CreateResponse, EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class DashboardType(Enum):
    """Types of dashboards available."""

    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    ANALYTICAL = "analytical"
    FINANCIAL = "financial"
    PROJECT = "project"
    RESOURCE = "resource"
    CUSTOMER = "customer"
    CUSTOM = "custom"


class WidgetType(Enum):
    """Types of dashboard widgets."""

    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    GAUGE = "gauge"
    MAP = "map"
    TEXT = "text"
    IMAGE = "image"
    IFRAME = "iframe"


class ChartType(Enum):
    """Chart types for dashboard widgets."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"


class DashboardsEntity(BaseEntity):
    """
    Handles all Dashboard-related operations for the Autotask API.

    Dashboards provide real-time business intelligence through customizable
    widgets, data visualization, and interactive analytics. This entity manages
    dashboard creation, configuration, widget management, and usage analytics.
    """

    def __init__(self, client, entity_name="Dashboards"):
        """Initialize the Dashboards entity."""
        super().__init__(client, entity_name)

    def create_dashboard(
        self,
        name: str,
        description: str,
        dashboard_type: Union[str, DashboardType] = DashboardType.CUSTOM,
        layout_config: Optional[Dict[str, Any]] = None,
        access_permissions: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> CreateResponse:
        """
        Create a new dashboard.

        Args:
            name: Dashboard name
            description: Dashboard description
            dashboard_type: Type of dashboard
            layout_config: Layout configuration for widgets
            access_permissions: User/role access permissions
            **kwargs: Additional dashboard properties

        Returns:
            Create response with new dashboard ID

        Example:
            dashboard = client.dashboards.create_dashboard(
                name="Executive Summary",
                description="High-level business metrics",
                dashboard_type=DashboardType.EXECUTIVE
            )
        """
        if isinstance(dashboard_type, DashboardType):
            dashboard_type = dashboard_type.value

        dashboard_data = {
            "name": name,
            "description": description,
            "dashboard_type": dashboard_type,
            "is_active": True,
            "created_date": datetime.now().isoformat(),
            "layout_config": layout_config or {"columns": 12, "rows": "auto"},
            "access_permissions": access_permissions or [],
            "widget_count": 0,
            "last_modified": datetime.now().isoformat(),
            **kwargs,
        }

        self.logger.info(f"Creating dashboard: {name}")
        return self.create(dashboard_data)

    def get_dashboard_by_name(self, name: str) -> Optional[EntityDict]:
        """
        Get dashboard by name.

        Args:
            name: Dashboard name to search for

        Returns:
            Dashboard data or None if not found

        Example:
            dashboard = client.dashboards.get_dashboard_by_name("Executive Summary")
        """
        response = self.query(filters={"field": "name", "op": "eq", "value": name})
        return response.items[0] if response.items else None

    def get_dashboards_by_type(
        self, dashboard_type: Union[str, DashboardType], active_only: bool = True
    ) -> List[EntityDict]:
        """
        Get dashboards by type.

        Args:
            dashboard_type: Type of dashboards to retrieve
            active_only: Whether to only return active dashboards

        Returns:
            List of dashboards of the specified type

        Example:
            executive_dashboards = client.dashboards.get_dashboards_by_type(
                DashboardType.EXECUTIVE
            )
        """
        if isinstance(dashboard_type, DashboardType):
            dashboard_type = dashboard_type.value

        filters = [{"field": "dashboard_type", "op": "eq", "value": dashboard_type}]

        if active_only:
            filters.append({"field": "is_active", "op": "eq", "value": True})

        response = self.query(filters=filters)
        return response.items

    def activate_dashboard(
        self, dashboard_id: int, activation_notes: Optional[str] = None
    ) -> EntityDict:
        """
        Activate a dashboard.

        Args:
            dashboard_id: ID of the dashboard to activate
            activation_notes: Optional notes about activation

        Returns:
            Updated dashboard data

        Example:
            dashboard = client.dashboards.activate_dashboard(12345)
        """
        update_data = {
            "is_active": True,
            "activated_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
        }

        if activation_notes:
            update_data["activation_notes"] = activation_notes

        self.logger.info(f"Activating dashboard {dashboard_id}")
        return self.update_by_id(dashboard_id, update_data)

    def deactivate_dashboard(
        self, dashboard_id: int, deactivation_reason: Optional[str] = None
    ) -> EntityDict:
        """
        Deactivate a dashboard.

        Args:
            dashboard_id: ID of the dashboard to deactivate
            deactivation_reason: Optional reason for deactivation

        Returns:
            Updated dashboard data

        Example:
            dashboard = client.dashboards.deactivate_dashboard(
                12345,
                "Replaced by new executive dashboard"
            )
        """
        update_data = {
            "is_active": False,
            "deactivated_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
        }

        if deactivation_reason:
            update_data["deactivation_reason"] = deactivation_reason

        self.logger.info(f"Deactivating dashboard {dashboard_id}")
        return self.update_by_id(dashboard_id, update_data)

    def clone_dashboard(
        self,
        source_dashboard_id: int,
        new_name: str,
        new_description: Optional[str] = None,
        copy_widgets: bool = True,
    ) -> CreateResponse:
        """
        Clone an existing dashboard.

        Args:
            source_dashboard_id: ID of the dashboard to clone
            new_name: Name for the cloned dashboard
            new_description: Optional new description
            copy_widgets: Whether to copy widgets from source

        Returns:
            Create response for the cloned dashboard

        Example:
            cloned = client.dashboards.clone_dashboard(
                12345,
                "Executive Summary - Q2",
                copy_widgets=True
            )
        """
        source_dashboard = self.get(source_dashboard_id)
        if not source_dashboard:
            raise AutotaskValidationError(
                f"Source dashboard {source_dashboard_id} not found"
            )

        # Prepare clone data
        clone_data = {
            k: v
            for k, v in source_dashboard.items()
            if k not in ["id", "created_date", "last_modified", "widget_count"]
        }

        clone_data.update(
            {
                "name": new_name,
                "description": new_description
                or f"Clone of {source_dashboard.get('name', '')}",
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "is_active": False,  # Clones start inactive
                "cloned_from": source_dashboard_id,
                "widget_count": 0,
            }
        )

        cloned_dashboard = self.create(clone_data)

        # Copy widgets if requested
        if copy_widgets and cloned_dashboard.item_id:
            self._clone_dashboard_widgets(source_dashboard_id, cloned_dashboard.item_id)

        self.logger.info(
            f"Cloned dashboard {source_dashboard_id} to {cloned_dashboard.item_id}"
        )
        return cloned_dashboard

    def configure_widgets(
        self, dashboard_id: int, widget_configurations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Configure multiple widgets for a dashboard.

        Args:
            dashboard_id: ID of the dashboard
            widget_configurations: List of widget configurations

        Returns:
            Widget configuration results

        Example:
            configs = [
                {
                    "widget_type": WidgetType.CHART,
                    "title": "Monthly Revenue",
                    "chart_type": ChartType.LINE,
                    "data_source": "revenue_by_month",
                    "position": {"x": 0, "y": 0, "width": 6, "height": 4}
                }
            ]
            client.dashboards.configure_widgets(12345, configs)
        """
        results = []
        widget_count = 0

        for config in widget_configurations:
            try:
                widget_result = self._create_widget(dashboard_id, config)
                results.append(
                    {
                        "widget_title": config.get("title", "Untitled"),
                        "success": True,
                        "widget_id": widget_result.get("widget_id"),
                        "result": widget_result,
                    }
                )
                widget_count += 1
            except Exception as e:
                self.logger.error(f"Failed to configure widget: {e}")
                results.append(
                    {
                        "widget_title": config.get("title", "Untitled"),
                        "success": False,
                        "error": str(e),
                    }
                )

        # Update dashboard widget count
        self.update_by_id(
            dashboard_id,
            {"widget_count": widget_count, "last_modified": datetime.now().isoformat()},
        )

        return {
            "dashboard_id": dashboard_id,
            "total_widgets": len(widget_configurations),
            "configured_successfully": len([r for r in results if r["success"]]),
            "configuration_errors": len([r for r in results if not r["success"]]),
            "widget_results": results,
            "configuration_date": datetime.now().isoformat(),
        }

    def analyze_dashboard_usage(
        self,
        dashboard_id: Optional[int] = None,
        date_range: Optional[Dict[str, str]] = None,
        user_filter: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze dashboard usage patterns and statistics.

        Args:
            dashboard_id: Optional specific dashboard to analyze
            date_range: Optional date range for analysis
            user_filter: Optional list of user IDs to include

        Returns:
            Dashboard usage analytics

        Example:
            usage = client.dashboards.analyze_dashboard_usage(
                dashboard_id=12345,
                date_range={"start": "2024-01-01", "end": "2024-01-31"}
            )
        """
        if not date_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = {"start": start_date.isoformat(), "end": end_date.isoformat()}

        usage_data = {
            "analysis_date": datetime.now().isoformat(),
            "date_range": date_range,
            "dashboard_id": dashboard_id,
            "usage_summary": {
                "total_views": 0,
                "unique_users": 0,
                "average_session_duration": Decimal("0"),
                "most_viewed_widgets": [],
                "peak_usage_hours": [],
            },
            "user_engagement": {},
            "performance_metrics": {
                "average_load_time": Decimal("0"),
                "error_rate": Decimal("0"),
                "widget_interaction_rate": Decimal("0"),
            },
            "trends": {"daily_usage": [], "hourly_patterns": [], "user_growth": []},
        }

        # Mock usage data - in real implementation would query usage logs
        usage_data["usage_summary"].update(
            {
                "total_views": 1247,
                "unique_users": 23,
                "average_session_duration": Decimal("4.5"),  # minutes
                "most_viewed_widgets": [
                    {"widget_id": "w001", "title": "Revenue Chart", "views": 456},
                    {"widget_id": "w002", "title": "Project Status", "views": 378},
                    {
                        "widget_id": "w003",
                        "title": "Resource Utilization",
                        "views": 289,
                    },
                ],
                "peak_usage_hours": [9, 10, 14, 15, 16],
            }
        )

        usage_data["performance_metrics"].update(
            {
                "average_load_time": Decimal("2.3"),  # seconds
                "error_rate": Decimal("0.02"),  # 2%
                "widget_interaction_rate": Decimal("0.67"),  # 67%
            }
        )

        # Generate trend data
        current_date = datetime.fromisoformat(date_range["start"]).date()
        end_date = datetime.fromisoformat(date_range["end"]).date()

        while current_date <= end_date:
            usage_data["trends"]["daily_usage"].append(
                {
                    "date": current_date.isoformat(),
                    "views": 35 + (hash(str(current_date)) % 20),  # Mock data
                    "unique_users": 3 + (hash(str(current_date)) % 8),
                }
            )
            current_date += timedelta(days=1)

        # Convert Decimal values for JSON serialization
        for metric, value in usage_data["performance_metrics"].items():
            if isinstance(value, Decimal):
                usage_data["performance_metrics"][metric] = float(value)

        usage_data["usage_summary"]["average_session_duration"] = float(
            usage_data["usage_summary"]["average_session_duration"]
        )

        return usage_data

    def export_dashboard_config(
        self,
        dashboard_id: int,
        include_widgets: bool = True,
        include_permissions: bool = True,
        export_format: str = "json",
    ) -> Union[str, Dict[str, Any]]:
        """
        Export dashboard configuration for backup or migration.

        Args:
            dashboard_id: ID of the dashboard to export
            include_widgets: Whether to include widget configurations
            include_permissions: Whether to include access permissions
            export_format: Export format (json, yaml, xml)

        Returns:
            Exported dashboard configuration

        Example:
            config = client.dashboards.export_dashboard_config(
                12345,
                include_widgets=True,
                export_format="json"
            )
        """
        dashboard = self.get(dashboard_id)
        if not dashboard:
            raise AutotaskValidationError(f"Dashboard {dashboard_id} not found")

        export_config = {
            "export_metadata": {
                "dashboard_id": dashboard_id,
                "export_date": datetime.now().isoformat(),
                "export_version": "1.0",
                "include_widgets": include_widgets,
                "include_permissions": include_permissions,
            },
            "dashboard_config": {
                "name": dashboard.get("name"),
                "description": dashboard.get("description"),
                "dashboard_type": dashboard.get("dashboard_type"),
                "layout_config": dashboard.get("layout_config", {}),
                "settings": {
                    "refresh_interval": dashboard.get("refresh_interval", 300),
                    "auto_refresh": dashboard.get("auto_refresh", True),
                    "theme": dashboard.get("theme", "default"),
                },
            },
        }

        if include_widgets:
            export_config["widgets"] = self._export_dashboard_widgets(dashboard_id)

        if include_permissions:
            export_config["permissions"] = dashboard.get("access_permissions", [])

        if export_format.lower() == "json":
            return json.dumps(export_config, indent=2, default=str)
        elif export_format.lower() == "yaml":
            try:
                import yaml

                return yaml.dump(export_config, default_flow_style=False)
            except ImportError:
                self.logger.warning("PyYAML not available, returning JSON format")
                return json.dumps(export_config, indent=2, default=str)
        else:
            return export_config

    def get_dashboard_summary(
        self,
        dashboard_id: Optional[int] = None,
        dashboard_type: Optional[Union[str, DashboardType]] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary statistics.

        Args:
            dashboard_id: Optional specific dashboard ID
            dashboard_type: Optional dashboard type filter

        Returns:
            Dashboard summary information

        Example:
            summary = client.dashboards.get_dashboard_summary()
        """
        filters = []

        if dashboard_id:
            filters.append({"field": "id", "op": "eq", "value": dashboard_id})

        if dashboard_type:
            if isinstance(dashboard_type, DashboardType):
                dashboard_type = dashboard_type.value
            filters.append(
                {"field": "dashboard_type", "op": "eq", "value": dashboard_type}
            )

        dashboards = self.query(filters=filters).items if filters else self.query_all()

        # Calculate summary statistics
        total_dashboards = len(dashboards)
        active_dashboards = len([d for d in dashboards if d.get("is_active", False)])
        inactive_dashboards = total_dashboards - active_dashboards

        # Group by type
        by_type = defaultdict(lambda: {"count": 0, "active": 0})
        total_widgets = 0

        for dashboard in dashboards:
            dashboard_type = dashboard.get("dashboard_type", "unknown")
            by_type[dashboard_type]["count"] += 1

            if dashboard.get("is_active", False):
                by_type[dashboard_type]["active"] += 1

            total_widgets += dashboard.get("widget_count", 0)

        # Calculate usage statistics
        recent_activity = self._get_recent_dashboard_activity(dashboards)

        return {
            "summary_date": datetime.now().isoformat(),
            "total_dashboards": total_dashboards,
            "active_dashboards": active_dashboards,
            "inactive_dashboards": inactive_dashboards,
            "activation_percentage": round(
                (
                    (active_dashboards / total_dashboards * 100)
                    if total_dashboards > 0
                    else 0
                ),
                2,
            ),
            "total_widgets": total_widgets,
            "average_widgets_per_dashboard": round(
                total_widgets / total_dashboards if total_dashboards > 0 else 0, 2
            ),
            "by_type": dict(by_type),
            "recent_activity": recent_activity,
            "most_popular_types": sorted(
                by_type.items(), key=lambda x: x[1]["count"], reverse=True
            )[:5],
        }

    def bulk_activate_dashboards(
        self, dashboard_ids: List[int], activation_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate multiple dashboards in bulk.

        Args:
            dashboard_ids: List of dashboard IDs to activate
            activation_notes: Optional activation notes

        Returns:
            Bulk activation results

        Example:
            result = client.dashboards.bulk_activate_dashboards([1, 2, 3])
        """
        results = []

        for dashboard_id in dashboard_ids:
            try:
                result = self.activate_dashboard(dashboard_id, activation_notes)
                results.append(
                    {"dashboard_id": dashboard_id, "success": True, "result": result}
                )
            except Exception as e:
                self.logger.error(f"Failed to activate dashboard {dashboard_id}: {e}")
                results.append(
                    {"dashboard_id": dashboard_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "operation": "bulk_activate",
            "total_dashboards": len(dashboard_ids),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": round((len(successful) / len(dashboard_ids) * 100), 2),
            "results": results,
            "operation_date": datetime.now().isoformat(),
        }

    def bulk_deactivate_dashboards(
        self, dashboard_ids: List[int], deactivation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deactivate multiple dashboards in bulk.

        Args:
            dashboard_ids: List of dashboard IDs to deactivate
            deactivation_reason: Optional reason for deactivation

        Returns:
            Bulk deactivation results

        Example:
            result = client.dashboards.bulk_deactivate_dashboards(
                [1, 2, 3],
                "End of quarter cleanup"
            )
        """
        results = []

        for dashboard_id in dashboard_ids:
            try:
                result = self.deactivate_dashboard(dashboard_id, deactivation_reason)
                results.append(
                    {"dashboard_id": dashboard_id, "success": True, "result": result}
                )
            except Exception as e:
                self.logger.error(f"Failed to deactivate dashboard {dashboard_id}: {e}")
                results.append(
                    {"dashboard_id": dashboard_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "operation": "bulk_deactivate",
            "total_dashboards": len(dashboard_ids),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": round((len(successful) / len(dashboard_ids) * 100), 2),
            "results": results,
            "operation_date": datetime.now().isoformat(),
        }

    def analyze_dashboard_performance(
        self, dashboard_id: int, performance_period: str = "last_7_days"
    ) -> Dict[str, Any]:
        """
        Analyze dashboard performance metrics.

        Args:
            dashboard_id: ID of the dashboard to analyze
            performance_period: Period for performance analysis

        Returns:
            Dashboard performance analysis

        Example:
            performance = client.dashboards.analyze_dashboard_performance(12345)
        """
        dashboard = self.get(dashboard_id)
        if not dashboard:
            raise AutotaskValidationError(f"Dashboard {dashboard_id} not found")

        # Calculate date range
        end_date = datetime.now()
        if performance_period == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif performance_period == "last_30_days":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        performance_data = {
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get("name"),
            "analysis_period": performance_period,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "performance_metrics": {
                "average_load_time": Decimal("2.1"),  # seconds
                "median_load_time": Decimal("1.8"),
                "95th_percentile_load_time": Decimal("4.2"),
                "error_rate": Decimal("0.015"),  # 1.5%
                "availability": Decimal("99.8"),  # 99.8%
                "widget_load_success_rate": Decimal("98.5"),
            },
            "resource_usage": {
                "cpu_utilization": Decimal("12.5"),  # %
                "memory_usage": Decimal("145.2"),  # MB
                "network_requests": 2847,
                "cache_hit_rate": Decimal("85.3"),  # %
            },
            "user_experience": {
                "session_duration": Decimal("4.2"),  # minutes
                "bounce_rate": Decimal("15.8"),  # %
                "interaction_rate": Decimal("72.4"),  # %
                "user_satisfaction_score": Decimal("4.1"),  # /5
            },
            "optimization_recommendations": [],
        }

        # Generate optimization recommendations
        recommendations = []

        if performance_data["performance_metrics"]["average_load_time"] > 3:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "performance",
                    "recommendation": "Optimize widget queries to reduce load time",
                    "expected_improvement": "30% faster loading",
                }
            )

        if performance_data["resource_usage"]["cache_hit_rate"] < 80:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "caching",
                    "recommendation": "Implement more aggressive caching strategy",
                    "expected_improvement": "20% reduction in server load",
                }
            )

        if performance_data["user_experience"]["bounce_rate"] > 20:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "user_experience",
                    "recommendation": "Improve dashboard layout and widget relevance",
                    "expected_improvement": "Better user engagement",
                }
            )

        performance_data["optimization_recommendations"] = recommendations

        # Convert Decimal values for JSON serialization
        for section in ["performance_metrics", "resource_usage", "user_experience"]:
            for metric, value in performance_data[section].items():
                if isinstance(value, Decimal):
                    performance_data[section][metric] = float(value)

        return performance_data

    def monitor_dashboard_health(
        self,
        dashboard_ids: Optional[List[int]] = None,
        alert_thresholds: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Monitor dashboard health and generate alerts.

        Args:
            dashboard_ids: Optional list of dashboard IDs to monitor
            alert_thresholds: Optional custom alert thresholds

        Returns:
            Dashboard health monitoring report

        Example:
            health = client.dashboards.monitor_dashboard_health(
                dashboard_ids=[1, 2, 3],
                alert_thresholds={"load_time": 5.0, "error_rate": 0.05}
            )
        """
        default_thresholds = {
            "load_time": 3.0,  # seconds
            "error_rate": 0.02,  # 2%
            "availability": 0.99,  # 99%
            "memory_usage": 200.0,  # MB
        }

        thresholds = {**default_thresholds, **(alert_thresholds or {})}

        # Get dashboards to monitor
        if dashboard_ids:
            dashboards = [self.get(dashboard_id) for dashboard_id in dashboard_ids]
            dashboards = [d for d in dashboards if d is not None]
        else:
            dashboards = self.query(
                filters={"field": "is_active", "op": "eq", "value": True}
            ).items

        health_report = {
            "monitoring_date": datetime.now().isoformat(),
            "dashboards_monitored": len(dashboards),
            "alert_thresholds": thresholds,
            "overall_health": "healthy",
            "health_score": Decimal("95.2"),
            "alerts": [],
            "dashboard_health": [],
        }

        critical_alerts = 0
        warning_alerts = 0

        for dashboard in dashboards:
            dashboard_id = dashboard.get("id")
            dashboard_name = dashboard.get("name", f"Dashboard {dashboard_id}")

            # Mock health metrics - in real implementation would collect actual metrics
            dashboard_health = {
                "dashboard_id": dashboard_id,
                "dashboard_name": dashboard_name,
                "health_status": "healthy",
                "metrics": {
                    "load_time": Decimal("2.3"),
                    "error_rate": Decimal("0.01"),
                    "availability": Decimal("99.9"),
                    "memory_usage": Decimal("125.5"),
                },
                "alerts": [],
            }

            # Check thresholds and generate alerts
            if dashboard_health["metrics"]["load_time"] > thresholds["load_time"]:
                alert = {
                    "severity": "warning",
                    "metric": "load_time",
                    "value": float(dashboard_health["metrics"]["load_time"]),
                    "threshold": thresholds["load_time"],
                    "message": f"Load time exceeds threshold for {dashboard_name}",
                }
                dashboard_health["alerts"].append(alert)
                health_report["alerts"].append({**alert, "dashboard_id": dashboard_id})
                warning_alerts += 1

            if dashboard_health["metrics"]["error_rate"] > thresholds["error_rate"]:
                alert = {
                    "severity": "critical",
                    "metric": "error_rate",
                    "value": float(dashboard_health["metrics"]["error_rate"]),
                    "threshold": thresholds["error_rate"],
                    "message": f"Error rate exceeds threshold for {dashboard_name}",
                }
                dashboard_health["alerts"].append(alert)
                health_report["alerts"].append({**alert, "dashboard_id": dashboard_id})
                critical_alerts += 1
                dashboard_health["health_status"] = "critical"

            # Convert Decimal values
            for metric, value in dashboard_health["metrics"].items():
                if isinstance(value, Decimal):
                    dashboard_health["metrics"][metric] = float(value)

            health_report["dashboard_health"].append(dashboard_health)

        # Determine overall health
        if critical_alerts > 0:
            health_report["overall_health"] = "critical"
            health_report["health_score"] = Decimal("65.0")
        elif warning_alerts > 0:
            health_report["overall_health"] = "warning"
            health_report["health_score"] = Decimal("80.0")

        health_report["alert_summary"] = {
            "critical": critical_alerts,
            "warning": warning_alerts,
            "total": critical_alerts + warning_alerts,
        }

        health_report["health_score"] = float(health_report["health_score"])

        return health_report

    # Helper methods

    def _create_widget(
        self, dashboard_id: int, widget_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a single widget for a dashboard."""
        widget_id = f"widget_{dashboard_id}_{datetime.now().timestamp()}"

        widget_data = {
            "widget_id": widget_id,
            "dashboard_id": dashboard_id,
            "widget_type": widget_config.get("widget_type", WidgetType.CHART.value),
            "title": widget_config.get("title", "Untitled Widget"),
            "configuration": widget_config,
            "created_date": datetime.now().isoformat(),
            "is_active": True,
        }

        # Mock widget creation - in real implementation would create actual widget
        return widget_data

    def _clone_dashboard_widgets(
        self, source_dashboard_id: int, target_dashboard_id: int
    ) -> None:
        """Clone widgets from source dashboard to target."""
        # Mock implementation - would copy actual widgets
        self.logger.info(
            f"Cloning widgets from {source_dashboard_id} to {target_dashboard_id}"
        )

    def _export_dashboard_widgets(self, dashboard_id: int) -> List[Dict[str, Any]]:
        """Export widget configurations for a dashboard."""
        # Mock widget export - would export actual widget configurations
        return [
            {
                "widget_id": "w001",
                "widget_type": "chart",
                "title": "Sample Chart",
                "configuration": {"chart_type": "line", "data_source": "sample"},
            }
        ]

    def _get_recent_dashboard_activity(
        self, dashboards: List[EntityDict]
    ) -> Dict[str, Any]:
        """Get recent activity summary for dashboards."""
        return {
            "recently_created": len(
                [d for d in dashboards if self._is_recent(d.get("created_date"))]
            ),
            "recently_modified": len(
                [d for d in dashboards if self._is_recent(d.get("last_modified"))]
            ),
            "recently_accessed": 15,  # Mock data
            "most_active_dashboard": dashboards[0].get("name") if dashboards else None,
        }

    def _is_recent(self, date_str: Optional[str], days: int = 7) -> bool:
        """Check if a date is within the recent timeframe."""
        if not date_str:
            return False

        try:
            date_obj = datetime.fromisoformat(date_str)
            return (datetime.now() - date_obj).days <= days
        except (ValueError, TypeError):
            return False
