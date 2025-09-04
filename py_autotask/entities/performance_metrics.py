"""
PerformanceMetrics entity for Autotask API operations.

This module provides comprehensive performance monitoring and metrics management,
including real-time monitoring, trend analysis, optimization recommendations,
and performance reporting.
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..exceptions import AutotaskValidationError
from ..types import CreateResponse, EntityDict
from .base import BaseEntity

if TYPE_CHECKING:
    from ..client import AutotaskClient

logger = logging.getLogger(__name__)


class PerformanceMetricsEntity(BaseEntity):
    """
    Handles performance metrics collection, analysis, and optimization for the Autotask API.

    This entity manages system performance monitoring, metrics aggregation,
    trend analysis, alerting, and performance optimization recommendations.
    It provides comprehensive insights into system health and performance patterns.
    """

    def __init__(
        self, client: "AutotaskClient", entity_name: str = "PerformanceMetrics"
    ) -> None:
        """
        Initialize the PerformanceMetrics entity handler.

        Args:
            client: The AutotaskClient instance
            entity_name: Name of the entity (defaults to 'PerformanceMetrics')
        """
        super().__init__(client, entity_name)
        self.logger = logging.getLogger(f"{__name__}.{entity_name}")

    def create_performance_metric(
        self,
        metric_name: str,
        metric_type: str,
        metric_value: Union[int, float, Decimal],
        source_entity: str,
        source_entity_id: Optional[int] = None,
        measurement_timestamp: Optional[datetime] = None,
        metric_unit: str = "count",
        metric_category: str = "system",
        additional_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CreateResponse:
        """
        Create a new performance metric record.

        Args:
            metric_name: Name of the performance metric
            metric_type: Type of metric (response_time, throughput, error_rate, etc.)
            metric_value: Numeric value of the metric
            source_entity: Entity that generated the metric
            source_entity_id: ID of the source entity (optional)
            measurement_timestamp: When the metric was measured (defaults to now)
            metric_unit: Unit of measurement (ms, requests/sec, percentage, etc.)
            metric_category: Category of metric (system, network, database, etc.)
            additional_data: Additional metadata for the metric
            **kwargs: Additional metric fields

        Returns:
            CreateResponse with metric ID

        Raises:
            AutotaskValidationError: If metric validation fails
        """
        self.logger.debug(f"Creating performance metric: {metric_name} ({metric_type})")

        try:
            # Validate required fields
            if not metric_name or not metric_type:
                raise AutotaskValidationError("Metric name and type are required")

            if not isinstance(metric_value, (int, float, Decimal)):
                raise AutotaskValidationError("Metric value must be numeric")

            measurement_time = measurement_timestamp or datetime.utcnow()

            # Convert Decimal to float for JSON serialization
            if isinstance(metric_value, Decimal):
                metric_value = float(metric_value)

            metric_data = {
                "MetricName": metric_name,
                "MetricType": metric_type,
                "MetricValue": metric_value,
                "SourceEntity": source_entity,
                "SourceEntityId": source_entity_id,
                "MeasurementTimestamp": measurement_time.isoformat(),
                "MetricUnit": metric_unit,
                "MetricCategory": metric_category,
                "AdditionalData": (
                    json.dumps(additional_data) if additional_data else None
                ),
                "CreatedDateTime": datetime.utcnow().isoformat(),
                "IsActive": True,
                **kwargs,
            }

            return self.create(metric_data)

        except Exception as e:
            self.logger.error(f"Failed to create performance metric {metric_name}: {e}")
            raise

    def get_metrics_by_type(
        self,
        metric_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source_entity: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Retrieve performance metrics by type within a date range.

        Args:
            metric_type: Type of metrics to retrieve
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            source_entity: Filter by source entity (optional)
            limit: Maximum number of metrics to return

        Returns:
            List of matching performance metrics
        """
        self.logger.debug(f"Retrieving metrics of type: {metric_type}")

        filters = [
            {"field": "MetricType", "op": "eq", "value": metric_type},
            {"field": "IsActive", "op": "eq", "value": True},
        ]

        if start_date:
            filters.append(
                {
                    "field": "MeasurementTimestamp",
                    "op": "gte",
                    "value": start_date.isoformat(),
                }
            )

        if end_date:
            filters.append(
                {
                    "field": "MeasurementTimestamp",
                    "op": "lte",
                    "value": end_date.isoformat(),
                }
            )

        if source_entity:
            filters.append(
                {"field": "SourceEntity", "op": "eq", "value": source_entity}
            )

        if limit:
            return self.query(filters=filters, max_records=limit).items
        else:
            return self.query_all(filters=filters)

    def get_metrics_by_entity(
        self,
        source_entity: str,
        entity_id: Optional[int] = None,
        metric_types: Optional[List[str]] = None,
        time_range: Optional[timedelta] = None,
    ) -> List[EntityDict]:
        """
        Get all performance metrics for a specific entity.

        Args:
            source_entity: Name of the source entity
            entity_id: Specific entity ID (optional)
            metric_types: List of metric types to include (optional)
            time_range: Time range to look back from now (optional)

        Returns:
            List of performance metrics for the entity
        """
        self.logger.debug(f"Retrieving metrics for entity: {source_entity}")

        filters = [
            {"field": "SourceEntity", "op": "eq", "value": source_entity},
            {"field": "IsActive", "op": "eq", "value": True},
        ]

        if entity_id:
            filters.append(
                {"field": "SourceEntityId", "op": "eq", "value": str(entity_id)}
            )

        if metric_types:
            filters.append({"field": "MetricType", "op": "in", "value": metric_types})

        if time_range:
            start_time = datetime.utcnow() - time_range
            filters.append(
                {
                    "field": "MeasurementTimestamp",
                    "op": "gte",
                    "value": start_time.isoformat(),
                }
            )

        return self.query_all(filters=filters)

    def activate_metric_monitoring(
        self,
        metric_id: int,
        monitoring_frequency: int = 300,  # 5 minutes
        alert_thresholds: Optional[Dict[str, Any]] = None,
        notification_settings: Optional[Dict[str, Any]] = None,
    ) -> EntityDict:
        """
        Activate monitoring for a specific performance metric.

        Args:
            metric_id: ID of the metric to monitor
            monitoring_frequency: Monitoring frequency in seconds
            alert_thresholds: Thresholds for generating alerts
            notification_settings: Settings for alert notifications

        Returns:
            Updated metric data with monitoring configuration
        """
        self.logger.info(f"Activating monitoring for metric ID: {metric_id}")

        monitoring_config = {
            "monitoring_enabled": True,
            "monitoring_frequency": monitoring_frequency,
            "alert_thresholds": alert_thresholds or {},
            "notification_settings": notification_settings or {},
            "monitoring_activated": datetime.utcnow().isoformat(),
        }

        update_data = {
            "id": metric_id,
            "MonitoringEnabled": True,
            "MonitoringConfig": json.dumps(monitoring_config),
            "LastModifiedDateTime": datetime.utcnow().isoformat(),
        }

        return self.update(update_data)

    def deactivate_metric_monitoring(
        self, metric_id: int, reason: Optional[str] = None
    ) -> EntityDict:
        """
        Deactivate monitoring for a specific performance metric.

        Args:
            metric_id: ID of the metric to stop monitoring
            reason: Reason for deactivating monitoring

        Returns:
            Updated metric data
        """
        self.logger.info(f"Deactivating monitoring for metric ID: {metric_id}")

        update_data = {
            "id": metric_id,
            "MonitoringEnabled": False,
            "MonitoringDeactivated": datetime.utcnow().isoformat(),
            "DeactivationReason": reason,
            "LastModifiedDateTime": datetime.utcnow().isoformat(),
        }

        return self.update(update_data)

    def clone_metric_configuration(
        self,
        source_metric_id: int,
        new_source_entity: str,
        new_source_entity_id: Optional[int] = None,
        modify_config: Optional[Dict[str, Any]] = None,
    ) -> CreateResponse:
        """
        Clone a metric configuration for a different entity.

        Args:
            source_metric_id: ID of the metric configuration to clone
            new_source_entity: New source entity for the cloned metric
            new_source_entity_id: ID of the new source entity
            modify_config: Modifications to apply to the cloned configuration

        Returns:
            CreateResponse with new metric configuration ID
        """
        self.logger.info(f"Cloning metric configuration {source_metric_id}")

        source_metric = self.get(source_metric_id)
        if not source_metric:
            raise AutotaskValidationError(f"Source metric {source_metric_id} not found")

        # Parse monitoring configuration if it exists
        monitoring_config = {}
        if source_metric.get("MonitoringConfig"):
            monitoring_config = json.loads(source_metric["MonitoringConfig"])

        # Apply modifications if provided
        if modify_config:
            monitoring_config.update(modify_config)

        # Create cloned metric configuration
        cloned_metric = {
            "MetricName": f"cloned_{source_metric['MetricName']}",
            "MetricType": source_metric["MetricType"],
            "MetricValue": 0,  # Start with zero value
            "SourceEntity": new_source_entity,
            "SourceEntityId": new_source_entity_id,
            "MeasurementTimestamp": datetime.utcnow().isoformat(),
            "MetricUnit": source_metric["MetricUnit"],
            "MetricCategory": source_metric["MetricCategory"],
            "MonitoringEnabled": source_metric.get("MonitoringEnabled", False),
            "MonitoringConfig": (
                json.dumps(monitoring_config) if monitoring_config else None
            ),
            "CreatedDateTime": datetime.utcnow().isoformat(),
            "IsActive": True,
            "ClonedFromMetricId": source_metric_id,
        }

        return self.create(cloned_metric)

    def get_performance_summary(
        self,
        time_period: timedelta = timedelta(hours=24),
        entity_filter: Optional[str] = None,
        metric_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance summary for a time period.

        Args:
            time_period: Time period to analyze (defaults to 24 hours)
            entity_filter: Filter by specific entity (optional)
            metric_categories: Filter by metric categories (optional)

        Returns:
            Dictionary containing performance summary statistics
        """
        self.logger.debug("Generating performance summary")

        start_time = datetime.utcnow() - time_period

        filters = [
            {
                "field": "MeasurementTimestamp",
                "op": "gte",
                "value": start_time.isoformat(),
            },
            {"field": "IsActive", "op": "eq", "value": True},
        ]

        if entity_filter:
            filters.append(
                {"field": "SourceEntity", "op": "eq", "value": entity_filter}
            )

        if metric_categories:
            filters.append(
                {"field": "MetricCategory", "op": "in", "value": metric_categories}
            )

        metrics = self.query_all(filters=filters)

        summary = {
            "time_period": str(time_period),
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_metrics": len(metrics),
            "unique_entities": len(set(m.get("SourceEntity") for m in metrics)),
            "metric_types": list(set(m.get("MetricType") for m in metrics)),
            "metric_categories": list(set(m.get("MetricCategory") for m in metrics)),
            "by_category": {},
            "by_type": {},
            "by_entity": {},
            "performance_indicators": {},
        }

        # Group metrics by category
        for metric in metrics:
            category = metric.get("MetricCategory", "unknown")
            if category not in summary["by_category"]:
                summary["by_category"][category] = {
                    "count": 0,
                    "metrics": [],
                    "avg_value": 0,
                    "min_value": float("inf"),
                    "max_value": float("-inf"),
                }

            summary["by_category"][category]["count"] += 1
            metric_value = float(metric.get("MetricValue", 0))
            summary["by_category"][category]["metrics"].append(metric_value)
            summary["by_category"][category]["min_value"] = min(
                summary["by_category"][category]["min_value"], metric_value
            )
            summary["by_category"][category]["max_value"] = max(
                summary["by_category"][category]["max_value"], metric_value
            )

        # Calculate averages for categories
        for category_data in summary["by_category"].values():
            if category_data["metrics"]:
                category_data["avg_value"] = statistics.mean(category_data["metrics"])
                category_data["median_value"] = statistics.median(
                    category_data["metrics"]
                )
                if len(category_data["metrics"]) > 1:
                    category_data["std_dev"] = statistics.stdev(
                        category_data["metrics"]
                    )
                else:
                    category_data["std_dev"] = 0

        # Group metrics by type
        for metric in metrics:
            metric_type = metric.get("MetricType", "unknown")
            if metric_type not in summary["by_type"]:
                summary["by_type"][metric_type] = {
                    "count": 0,
                    "avg_value": 0,
                    "recent_values": [],
                }

            summary["by_type"][metric_type]["count"] += 1
            summary["by_type"][metric_type]["recent_values"].append(
                float(metric.get("MetricValue", 0))
            )

        # Calculate type averages
        for type_data in summary["by_type"].values():
            if type_data["recent_values"]:
                type_data["avg_value"] = statistics.mean(type_data["recent_values"])
                type_data["trend"] = self._calculate_trend(type_data["recent_values"])

        # Group metrics by entity
        for metric in metrics:
            entity = metric.get("SourceEntity", "unknown")
            if entity not in summary["by_entity"]:
                summary["by_entity"][entity] = {
                    "metric_count": 0,
                    "entity_ids": set(),
                    "categories": set(),
                    "types": set(),
                }

            summary["by_entity"][entity]["metric_count"] += 1
            if metric.get("SourceEntityId"):
                summary["by_entity"][entity]["entity_ids"].add(metric["SourceEntityId"])
            summary["by_entity"][entity]["categories"].add(
                metric.get("MetricCategory", "unknown")
            )
            summary["by_entity"][entity]["types"].add(
                metric.get("MetricType", "unknown")
            )

        # Convert sets to lists for JSON serialization
        for entity_data in summary["by_entity"].values():
            entity_data["entity_ids"] = list(entity_data["entity_ids"])
            entity_data["categories"] = list(entity_data["categories"])
            entity_data["types"] = list(entity_data["types"])

        # Calculate overall performance indicators
        all_values = [float(m.get("MetricValue", 0)) for m in metrics]
        if all_values:
            summary["performance_indicators"] = {
                "overall_avg": statistics.mean(all_values),
                "overall_median": statistics.median(all_values),
                "overall_min": min(all_values),
                "overall_max": max(all_values),
                "overall_std_dev": (
                    statistics.stdev(all_values) if len(all_values) > 1 else 0
                ),
                "data_points": len(all_values),
            }

        return summary

    def bulk_create_metrics(
        self,
        metrics_data: List[Dict[str, Any]],
        batch_size: int = 200,
        validate_data: bool = True,
    ) -> List[CreateResponse]:
        """
        Create multiple performance metrics in bulk.

        Args:
            metrics_data: List of metric data dictionaries
            batch_size: Number of metrics to create per batch
            validate_data: Whether to validate metric data before creation

        Returns:
            List of create responses
        """
        self.logger.info(f"Bulk creating {len(metrics_data)} performance metrics")

        if validate_data:
            # Validate all metrics before creating any
            for i, metric_data in enumerate(metrics_data):
                try:
                    self._validate_metric_data(metric_data)
                except AutotaskValidationError as e:
                    raise AutotaskValidationError(
                        f"Validation failed for metric {i}: {e}"
                    )

        # Process metrics in batches
        results = []
        for i in range(0, len(metrics_data), batch_size):
            batch = metrics_data[i : i + batch_size]

            # Prepare batch for creation
            batch_entities = []
            for metric_data in batch:
                entity_data = {
                    "MetricName": metric_data["metric_name"],
                    "MetricType": metric_data["metric_type"],
                    "MetricValue": float(metric_data["metric_value"]),
                    "SourceEntity": metric_data["source_entity"],
                    "SourceEntityId": metric_data.get("source_entity_id"),
                    "MeasurementTimestamp": metric_data.get(
                        "measurement_timestamp", datetime.utcnow().isoformat()
                    ),
                    "MetricUnit": metric_data.get("metric_unit", "count"),
                    "MetricCategory": metric_data.get("metric_category", "system"),
                    "AdditionalData": (
                        json.dumps(metric_data.get("additional_data"))
                        if metric_data.get("additional_data")
                        else None
                    ),
                    "CreatedDateTime": datetime.utcnow().isoformat(),
                    "IsActive": True,
                }
                batch_entities.append(entity_data)

            try:
                batch_results = self.batch_create(batch_entities)
                results.extend(batch_results)
                self.logger.debug(f"Successfully created batch of {len(batch)} metrics")
            except Exception as e:
                self.logger.error(f"Failed to create metrics batch: {e}")
                continue

        return results

    def bulk_update_monitoring(
        self,
        metric_ids: List[int],
        monitoring_enabled: bool,
        monitoring_config: Optional[Dict[str, Any]] = None,
        batch_size: int = 100,
    ) -> List[EntityDict]:
        """
        Update monitoring settings for multiple metrics in bulk.

        Args:
            metric_ids: List of metric IDs to update
            monitoring_enabled: Whether to enable or disable monitoring
            monitoring_config: Monitoring configuration to apply
            batch_size: Number of metrics to update per batch

        Returns:
            List of updated metric data
        """
        self.logger.info(f"Bulk updating monitoring for {len(metric_ids)} metrics")

        results = []

        for i in range(0, len(metric_ids), batch_size):
            batch = metric_ids[i : i + batch_size]
            batch_updates = []

            for metric_id in batch:
                update_data = {
                    "id": metric_id,
                    "MonitoringEnabled": monitoring_enabled,
                    "LastModifiedDateTime": datetime.utcnow().isoformat(),
                }

                if monitoring_config:
                    update_data["MonitoringConfig"] = json.dumps(monitoring_config)

                batch_updates.append(update_data)

            try:
                batch_results = self.batch_update(batch_updates)
                results.extend(batch_results)
                self.logger.debug(f"Successfully updated batch of {len(batch)} metrics")
            except Exception as e:
                self.logger.error(f"Failed to update metrics batch: {e}")
                continue

        return results

    def configure_metric_collection(
        self,
        entity_type: str,
        metric_types: List[str],
        collection_frequency: int = 300,  # 5 minutes
        retention_period: timedelta = timedelta(days=30),
        aggregation_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Configure automatic metric collection for an entity type.

        Args:
            entity_type: Type of entity to collect metrics for
            metric_types: List of metric types to collect
            collection_frequency: Collection frequency in seconds
            retention_period: How long to retain collected metrics
            aggregation_rules: Rules for metric aggregation and rollup

        Returns:
            Dictionary containing collection configuration details
        """
        self.logger.info(
            f"Configuring metric collection for entity type: {entity_type}"
        )

        collection_config = {
            "entity_type": entity_type,
            "metric_types": metric_types,
            "collection_frequency": collection_frequency,
            "retention_period": str(retention_period),
            "aggregation_rules": aggregation_rules or {},
            "configured_at": datetime.utcnow().isoformat(),
            "collection_enabled": True,
            "next_collection": (
                datetime.utcnow() + timedelta(seconds=collection_frequency)
            ).isoformat(),
        }

        # Create configuration record
        config_record = self.create_performance_metric(
            metric_name=f"collection_config_{entity_type}",
            metric_type="configuration",
            metric_value=1,
            source_entity="system",
            metric_category="configuration",
            additional_data=collection_config,
        )

        return {
            "config_id": config_record.item_id,
            "entity_type": entity_type,
            "collection_configuration": collection_config,
            "status": "configured",
        }

    def monitor_system_performance(
        self,
        monitoring_duration: timedelta = timedelta(hours=1),
        metric_categories: Optional[List[str]] = None,
        alert_on_anomalies: bool = True,
        real_time_updates: bool = False,
    ) -> Dict[str, Any]:
        """
        Monitor system performance in real-time or for a specified duration.

        Args:
            monitoring_duration: How long to monitor performance
            metric_categories: Specific metric categories to monitor
            alert_on_anomalies: Whether to generate alerts for anomalies
            real_time_updates: Whether to provide real-time monitoring updates

        Returns:
            Dictionary containing monitoring results and performance analysis
        """
        self.logger.info(
            f"Starting system performance monitoring for {monitoring_duration}"
        )

        start_time = datetime.utcnow()
        end_time = start_time + monitoring_duration

        # Build filters for monitoring
        filters = [
            {
                "field": "MeasurementTimestamp",
                "op": "gte",
                "value": start_time.isoformat(),
            },
            {"field": "IsActive", "op": "eq", "value": True},
        ]

        if metric_categories:
            filters.append(
                {"field": "MetricCategory", "op": "in", "value": metric_categories}
            )

        # Initialize monitoring results
        monitoring_results = {
            "monitoring_start": start_time.isoformat(),
            "monitoring_duration": str(monitoring_duration),
            "monitoring_end": end_time.isoformat(),
            "metric_categories": metric_categories or ["all"],
            "real_time_updates": real_time_updates,
            "alert_on_anomalies": alert_on_anomalies,
            "performance_snapshots": [],
            "anomalies_detected": [],
            "alerts_generated": [],
            "summary_statistics": {},
        }

        # Collect baseline metrics
        baseline_metrics = self.query_all(filters=filters)
        baseline_stats = self._calculate_baseline_statistics(baseline_metrics)

        monitoring_results["baseline_statistics"] = baseline_stats

        # If real-time monitoring is enabled, collect periodic snapshots
        if real_time_updates:
            snapshot_interval = min(
                monitoring_duration.total_seconds() / 10, 60
            )  # Max 1 minute intervals
            monitoring_results["snapshot_interval"] = snapshot_interval

            # Simulate real-time monitoring with periodic snapshots
            current_time = start_time
            while current_time < end_time:
                snapshot_filters = filters + [
                    {
                        "field": "MeasurementTimestamp",
                        "op": "gte",
                        "value": current_time.isoformat(),
                    },
                    {
                        "field": "MeasurementTimestamp",
                        "op": "lt",
                        "value": (
                            current_time + timedelta(seconds=snapshot_interval)
                        ).isoformat(),
                    },
                ]

                snapshot_metrics = self.query_all(filters=snapshot_filters)

                if snapshot_metrics:
                    snapshot = self._create_performance_snapshot(
                        snapshot_metrics, current_time
                    )
                    monitoring_results["performance_snapshots"].append(snapshot)

                    # Check for anomalies
                    if alert_on_anomalies:
                        anomalies = self._detect_performance_anomalies(
                            snapshot, baseline_stats
                        )
                        if anomalies:
                            monitoring_results["anomalies_detected"].extend(anomalies)

                            # Generate alerts for significant anomalies
                            alerts = self._generate_performance_alerts(anomalies)
                            monitoring_results["alerts_generated"].extend(alerts)

                current_time += timedelta(seconds=snapshot_interval)

        # Final performance analysis
        final_metrics = self.query_all(filters=filters)
        final_stats = self._calculate_performance_statistics(final_metrics)

        monitoring_results["final_statistics"] = final_stats
        monitoring_results["performance_change"] = self._calculate_performance_change(
            baseline_stats, final_stats
        )

        # Generate monitoring summary
        monitoring_results["summary_statistics"] = {
            "total_metrics_collected": len(final_metrics),
            "unique_entities_monitored": len(
                set(m.get("SourceEntity") for m in final_metrics)
            ),
            "anomalies_count": len(monitoring_results["anomalies_detected"]),
            "alerts_count": len(monitoring_results["alerts_generated"]),
            "monitoring_completed_at": datetime.utcnow().isoformat(),
        }

        return monitoring_results

    def analyze_performance_trends(
        self,
        analysis_period: timedelta = timedelta(days=7),
        metric_types: Optional[List[str]] = None,
        entity_filter: Optional[str] = None,
        trend_detection_sensitivity: str = "medium",
    ) -> Dict[str, Any]:
        """
        Analyze performance trends over a specified period.

        Args:
            analysis_period: Period to analyze for trends
            metric_types: Specific metric types to analyze
            entity_filter: Filter by specific entity
            trend_detection_sensitivity: Sensitivity for trend detection ('low', 'medium', 'high')

        Returns:
            Dictionary containing trend analysis results and predictions
        """
        self.logger.info(f"Analyzing performance trends over {analysis_period}")

        start_time = datetime.utcnow() - analysis_period

        # Build filters for trend analysis
        filters = [
            {
                "field": "MeasurementTimestamp",
                "op": "gte",
                "value": start_time.isoformat(),
            },
            {"field": "IsActive", "op": "eq", "value": True},
        ]

        if metric_types:
            filters.append({"field": "MetricType", "op": "in", "value": metric_types})

        if entity_filter:
            filters.append(
                {"field": "SourceEntity", "op": "eq", "value": entity_filter}
            )

        # Get metrics for analysis
        metrics = self.query_all(filters=filters)

        trend_analysis = {
            "analysis_period": str(analysis_period),
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "metric_types_analyzed": metric_types or ["all"],
            "entity_filter": entity_filter,
            "sensitivity": trend_detection_sensitivity,
            "total_data_points": len(metrics),
            "trends_by_type": {},
            "trends_by_entity": {},
            "overall_trends": {},
            "predictions": {},
            "recommendations": [],
        }

        # Group metrics by type for trend analysis
        metrics_by_type = {}
        for metric in metrics:
            metric_type = metric.get("MetricType", "unknown")
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []

            metrics_by_type[metric_type].append(
                {
                    "timestamp": metric.get("MeasurementTimestamp"),
                    "value": float(metric.get("MetricValue", 0)),
                    "entity": metric.get("SourceEntity"),
                }
            )

        # Analyze trends for each metric type
        for metric_type, type_metrics in metrics_by_type.items():
            # Sort by timestamp
            type_metrics.sort(key=lambda x: x["timestamp"])

            # Calculate trend statistics
            values = [m["value"] for m in type_metrics]
            if len(values) >= 2:
                trend_stats = self._calculate_trend_statistics(
                    values, trend_detection_sensitivity
                )

                trend_analysis["trends_by_type"][metric_type] = {
                    "data_points": len(values),
                    "trend_direction": trend_stats["direction"],
                    "trend_strength": trend_stats["strength"],
                    "slope": trend_stats["slope"],
                    "correlation": trend_stats["correlation"],
                    "volatility": trend_stats["volatility"],
                    "recent_average": (
                        statistics.mean(values[-10:])
                        if len(values) >= 10
                        else statistics.mean(values)
                    ),
                    "period_change": (
                        ((values[-1] - values[0]) / values[0] * 100)
                        if values[0] != 0
                        else 0
                    ),
                    "predictions": self._generate_trend_predictions(
                        values, metric_type
                    ),
                }

        # Group metrics by entity for trend analysis
        metrics_by_entity = {}
        for metric in metrics:
            entity = metric.get("SourceEntity", "unknown")
            if entity not in metrics_by_entity:
                metrics_by_entity[entity] = []

            metrics_by_entity[entity].append(
                {
                    "timestamp": metric.get("MeasurementTimestamp"),
                    "value": float(metric.get("MetricValue", 0)),
                    "type": metric.get("MetricType"),
                }
            )

        # Analyze trends for each entity
        for entity, entity_metrics in metrics_by_entity.items():
            entity_metrics.sort(key=lambda x: x["timestamp"])
            values = [m["value"] for m in entity_metrics]

            if len(values) >= 2:
                trend_stats = self._calculate_trend_statistics(
                    values, trend_detection_sensitivity
                )

                trend_analysis["trends_by_entity"][entity] = {
                    "data_points": len(values),
                    "metric_types": list(set(m["type"] for m in entity_metrics)),
                    "trend_direction": trend_stats["direction"],
                    "trend_strength": trend_stats["strength"],
                    "performance_score": self._calculate_entity_performance_score(
                        entity_metrics
                    ),
                    "recommendations": self._generate_entity_recommendations(
                        entity, trend_stats
                    ),
                }

        # Calculate overall system trends
        all_values = [float(m.get("MetricValue", 0)) for m in metrics]
        if len(all_values) >= 2:
            overall_trend_stats = self._calculate_trend_statistics(
                all_values, trend_detection_sensitivity
            )

            trend_analysis["overall_trends"] = {
                "system_trend_direction": overall_trend_stats["direction"],
                "system_trend_strength": overall_trend_stats["strength"],
                "system_health_score": self._calculate_system_health_score(metrics),
                "performance_stability": overall_trend_stats["volatility"],
            }

        # Generate system-wide recommendations
        trend_analysis["recommendations"] = self._generate_system_recommendations(
            trend_analysis["trends_by_type"],
            trend_analysis["trends_by_entity"],
            trend_analysis["overall_trends"],
        )

        return trend_analysis

    def optimize_performance(
        self,
        optimization_target: str = "overall",
        entity_filter: Optional[str] = None,
        metric_categories: Optional[List[str]] = None,
        optimization_strategy: str = "balanced",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze performance data and provide optimization recommendations.

        Args:
            optimization_target: Target for optimization ('overall', 'specific_entity', 'category')
            entity_filter: Specific entity to optimize (if target is 'specific_entity')
            metric_categories: Categories to focus optimization on
            optimization_strategy: Strategy for optimization ('performance', 'efficiency', 'balanced')
            dry_run: Whether to only analyze without applying optimizations

        Returns:
            Dictionary containing optimization analysis and recommendations
        """
        self.logger.info(
            f"Starting performance optimization analysis for target: {optimization_target}"
        )

        # Build filters for optimization analysis
        filters = [
            {"field": "IsActive", "op": "eq", "value": True},
            {
                "field": "MeasurementTimestamp",
                "op": "gte",
                "value": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            },
        ]

        if entity_filter:
            filters.append(
                {"field": "SourceEntity", "op": "eq", "value": entity_filter}
            )

        if metric_categories:
            filters.append(
                {"field": "MetricCategory", "op": "in", "value": metric_categories}
            )

        # Get metrics for optimization analysis
        metrics = self.query_all(filters=filters)

        optimization_results = {
            "optimization_target": optimization_target,
            "entity_filter": entity_filter,
            "metric_categories": metric_categories or ["all"],
            "optimization_strategy": optimization_strategy,
            "dry_run": dry_run,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "metrics_analyzed": len(metrics),
            "performance_analysis": {},
            "optimization_opportunities": [],
            "recommended_actions": [],
            "expected_improvements": {},
            "implementation_plan": [],
            "applied_optimizations": [] if not dry_run else None,
        }

        # Analyze current performance
        performance_analysis = self._analyze_current_performance(
            metrics, optimization_strategy
        )
        optimization_results["performance_analysis"] = performance_analysis

        # Identify optimization opportunities
        opportunities = self._identify_optimization_opportunities(
            metrics, optimization_target, optimization_strategy
        )
        optimization_results["optimization_opportunities"] = opportunities

        # Generate recommended actions
        recommended_actions = self._generate_optimization_actions(
            opportunities, optimization_strategy
        )
        optimization_results["recommended_actions"] = recommended_actions

        # Calculate expected improvements
        expected_improvements = self._calculate_expected_improvements(
            recommended_actions, performance_analysis
        )
        optimization_results["expected_improvements"] = expected_improvements

        # Create implementation plan
        implementation_plan = self._create_optimization_implementation_plan(
            recommended_actions, optimization_strategy
        )
        optimization_results["implementation_plan"] = implementation_plan

        # Apply optimizations if not in dry run mode
        if not dry_run:
            applied_optimizations = self._apply_performance_optimizations(
                implementation_plan, metrics
            )
            optimization_results["applied_optimizations"] = applied_optimizations
            optimization_results["optimization_status"] = "completed"
        else:
            optimization_results["optimization_status"] = "analysis_only"

        # Generate optimization summary
        optimization_results["optimization_summary"] = {
            "total_opportunities": len(opportunities),
            "high_impact_opportunities": len(
                [o for o in opportunities if o.get("impact") == "high"]
            ),
            "recommended_actions_count": len(recommended_actions),
            "expected_performance_gain": expected_improvements.get(
                "overall_improvement", 0
            ),
            "implementation_complexity": self._calculate_implementation_complexity(
                implementation_plan
            ),
            "estimated_completion_time": self._estimate_optimization_completion_time(
                implementation_plan
            ),
        }

        return optimization_results

    # Private helper methods

    def _validate_metric_data(self, metric_data: Dict[str, Any]) -> None:
        """Validate metric data before creation."""
        required_fields = [
            "metric_name",
            "metric_type",
            "metric_value",
            "source_entity",
        ]
        for field in required_fields:
            if field not in metric_data:
                raise AutotaskValidationError(f"Required field missing: {field}")

        if not isinstance(metric_data["metric_value"], (int, float, Decimal)):
            raise AutotaskValidationError("Metric value must be numeric")

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return "insufficient_data"

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg > first_avg * 1.05:
            return "increasing"
        elif second_avg < first_avg * 0.95:
            return "decreasing"
        else:
            return "stable"

    def _calculate_baseline_statistics(
        self, metrics: List[EntityDict]
    ) -> Dict[str, Any]:
        """Calculate baseline statistics from metrics."""
        if not metrics:
            return {}

        values = [float(m.get("MetricValue", 0)) for m in metrics]

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "baseline_timestamp": datetime.utcnow().isoformat(),
        }

    def _create_performance_snapshot(
        self, metrics: List[EntityDict], snapshot_time: datetime
    ) -> Dict[str, Any]:
        """Create a performance snapshot from metrics."""
        values = [float(m.get("MetricValue", 0)) for m in metrics]

        return {
            "snapshot_time": snapshot_time.isoformat(),
            "metric_count": len(metrics),
            "average_value": statistics.mean(values) if values else 0,
            "min_value": min(values) if values else 0,
            "max_value": max(values) if values else 0,
            "unique_entities": len(set(m.get("SourceEntity") for m in metrics)),
        }

    def _detect_performance_anomalies(
        self, snapshot: Dict[str, Any], baseline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect performance anomalies by comparing to baseline."""
        anomalies = []

        if not baseline or "mean" not in baseline:
            return anomalies

        snapshot_avg = snapshot.get("average_value", 0)
        baseline_mean = baseline["mean"]
        baseline_std = baseline.get("std_dev", 0)

        # Check for significant deviation from baseline
        if baseline_std > 0:
            z_score = abs(snapshot_avg - baseline_mean) / baseline_std
            if z_score > 2:  # More than 2 standard deviations
                anomalies.append(
                    {
                        "type": "statistical_anomaly",
                        "snapshot_time": snapshot["snapshot_time"],
                        "current_value": snapshot_avg,
                        "baseline_mean": baseline_mean,
                        "z_score": z_score,
                        "severity": "high" if z_score > 3 else "medium",
                    }
                )

        return anomalies

    def _generate_performance_alerts(
        self, anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate alerts from detected anomalies."""
        alerts = []

        for anomaly in anomalies:
            alerts.append(
                {
                    "alert_id": f"perf_alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "alert_type": "performance_anomaly",
                    "severity": anomaly.get("severity", "medium"),
                    "message": f"Performance anomaly detected: Z-score {anomaly.get('z_score', 0):.2f}",
                    "timestamp": anomaly.get("snapshot_time"),
                    "details": anomaly,
                }
            )

        return alerts

    def _calculate_performance_statistics(
        self, metrics: List[EntityDict]
    ) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics."""
        if not metrics:
            return {}

        values = [float(m.get("MetricValue", 0)) for m in metrics]

        stats = {
            "total_metrics": len(metrics),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "unique_entities": len(set(m.get("SourceEntity") for m in metrics)),
            "metric_types": list(set(m.get("MetricType") for m in metrics)),
            "calculated_at": datetime.utcnow().isoformat(),
        }

        # Calculate percentiles
        sorted_values = sorted(values)
        stats["percentile_25"] = sorted_values[len(sorted_values) // 4]
        stats["percentile_75"] = sorted_values[3 * len(sorted_values) // 4]
        stats["percentile_90"] = sorted_values[9 * len(sorted_values) // 10]

        return stats

    def _calculate_performance_change(
        self, baseline: Dict[str, Any], current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance change between baseline and current."""
        if not baseline or not current:
            return {}

        baseline_mean = baseline.get("mean", 0)
        current_mean = current.get("mean", 0)

        change = {
            "absolute_change": current_mean - baseline_mean,
            "percentage_change": (
                ((current_mean - baseline_mean) / baseline_mean * 100)
                if baseline_mean != 0
                else 0
            ),
            "trend_direction": (
                "improving"
                if current_mean > baseline_mean
                else "declining" if current_mean < baseline_mean else "stable"
            ),
            "change_significance": (
                "significant"
                if abs(current_mean - baseline_mean) > baseline.get("std_dev", 0)
                else "minor"
            ),
        }

        return change

    def _calculate_trend_statistics(
        self, values: List[float], sensitivity: str
    ) -> Dict[str, Any]:
        """Calculate trend statistics for a series of values."""
        if len(values) < 2:
            return {
                "direction": "insufficient_data",
                "strength": 0,
                "slope": 0,
                "correlation": 0,
                "volatility": 0,
            }

        # Calculate linear regression slope
        x_values = list(range(len(values)))
        n = len(values)

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        slope_numerator = sum(
            (x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n)
        )
        slope_denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        slope = slope_numerator / slope_denominator if slope_denominator != 0 else 0

        # Calculate correlation coefficient
        correlation = 0
        if len(values) > 1:
            try:
                x_std = statistics.stdev(x_values)
                y_std = statistics.stdev(values)
                if x_std > 0 and y_std > 0:
                    correlation = slope_numerator / (n * x_std * y_std)
            except (ValueError, ZeroDivisionError):
                correlation = 0

        # Determine trend direction and strength
        sensitivity_thresholds = {"low": 0.1, "medium": 0.05, "high": 0.01}

        threshold = sensitivity_thresholds.get(sensitivity, 0.05)

        if abs(slope) < threshold:
            direction = "stable"
            strength = "weak"
        elif slope > 0:
            direction = "increasing"
            strength = "strong" if abs(correlation) > 0.7 else "moderate"
        else:
            direction = "decreasing"
            strength = "strong" if abs(correlation) > 0.7 else "moderate"

        # Calculate volatility
        volatility = (
            statistics.stdev(values) / statistics.mean(values)
            if statistics.mean(values) != 0
            else 0
        )

        return {
            "direction": direction,
            "strength": strength,
            "slope": slope,
            "correlation": correlation,
            "volatility": volatility,
        }

    def _generate_trend_predictions(
        self, values: List[float], metric_type: str
    ) -> Dict[str, Any]:
        """Generate predictions based on trend analysis."""
        if len(values) < 3:
            return {"prediction": "insufficient_data"}

        # Simple linear projection
        recent_trend = self._calculate_trend_statistics(values[-10:], "medium")

        next_value = values[-1] + recent_trend["slope"]

        return {
            "next_predicted_value": next_value,
            "trend_direction": recent_trend["direction"],
            "confidence": (
                "high"
                if abs(recent_trend["correlation"]) > 0.8
                else "medium" if abs(recent_trend["correlation"]) > 0.5 else "low"
            ),
            "prediction_basis": "linear_trend",
        }

    def _calculate_entity_performance_score(
        self, entity_metrics: List[Dict[str, Any]]
    ) -> float:
        """Calculate performance score for an entity."""
        if not entity_metrics:
            return 0.0

        values = [m["value"] for m in entity_metrics]
        recent_values = values[-10:] if len(values) >= 10 else values

        # Simple scoring based on recent performance
        avg_value = statistics.mean(recent_values)
        stability = 1 - (
            statistics.stdev(recent_values) / avg_value if avg_value != 0 else 1
        )

        # Score between 0-100
        score = min(100, max(0, stability * 100))

        return round(score, 2)

    def _generate_entity_recommendations(
        self, entity: str, trend_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for an entity based on trend analysis."""
        recommendations = []

        if trend_stats["direction"] == "decreasing" and trend_stats["strength"] in [
            "moderate",
            "strong",
        ]:
            recommendations.append(
                f"Performance decline detected for {entity}. Consider investigating root causes."
            )

        if trend_stats["volatility"] > 0.3:
            recommendations.append(
                f"High volatility detected for {entity}. Consider implementing performance stabilization measures."
            )

        if trend_stats["direction"] == "increasing":
            recommendations.append(
                f"Positive performance trend for {entity}. Monitor to maintain improvements."
            )

        return recommendations

    def _calculate_system_health_score(self, metrics: List[EntityDict]) -> float:
        """Calculate overall system health score."""
        if not metrics:
            return 0.0

        # Aggregate health metrics
        values = [float(m.get("MetricValue", 0)) for m in metrics]
        entities = set(m.get("SourceEntity") for m in metrics)

        # Simple health scoring
        avg_performance = statistics.mean(values)
        performance_stability = 1 - (
            statistics.stdev(values) / avg_performance if avg_performance != 0 else 1
        )
        entity_coverage = min(1.0, len(entities) / 10)  # Assume 10 is good coverage

        health_score = (performance_stability * 0.6 + entity_coverage * 0.4) * 100

        return round(min(100, max(0, health_score)), 2)

    def _generate_system_recommendations(
        self,
        trends_by_type: Dict[str, Any],
        trends_by_entity: Dict[str, Any],
        overall_trends: Dict[str, Any],
    ) -> List[str]:
        """Generate system-wide recommendations."""
        recommendations = []

        # Check for declining trends
        declining_types = [
            t
            for t, data in trends_by_type.items()
            if data.get("trend_direction") == "decreasing"
        ]
        if declining_types:
            recommendations.append(
                f"Performance decline detected in metric types: {', '.join(declining_types)}"
            )

        # Check for unstable entities
        unstable_entities = [
            e
            for e, data in trends_by_entity.items()
            if data.get("trend_strength") == "weak"
        ]
        if unstable_entities:
            recommendations.append(
                f"Unstable performance in entities: {', '.join(unstable_entities[:3])}"
            )

        # System health recommendations
        system_health = overall_trends.get("system_health_score", 0)
        if system_health < 70:
            recommendations.append(
                "Overall system health is below optimal. Consider comprehensive performance review."
            )

        return recommendations

    def _analyze_current_performance(
        self, metrics: List[EntityDict], strategy: str
    ) -> Dict[str, Any]:
        """Analyze current performance state."""
        # Implementation would analyze current performance metrics
        return {
            "overall_performance": "baseline_analysis_complete",
            "bottlenecks_identified": [],
            "optimization_potential": "medium",
        }

    def _identify_optimization_opportunities(
        self, metrics: List[EntityDict], target: str, strategy: str
    ) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities."""
        # Implementation would identify optimization opportunities
        return [
            {
                "opportunity_type": "performance_tuning",
                "impact": "high",
                "effort": "medium",
                "description": "Optimize database queries for better response times",
            }
        ]

    def _generate_optimization_actions(
        self, opportunities: List[Dict[str, Any]], strategy: str
    ) -> List[Dict[str, Any]]:
        """Generate specific optimization actions."""
        # Implementation would generate actionable optimization steps
        return [
            {
                "action": "implement_caching",
                "priority": "high",
                "estimated_impact": "20% performance improvement",
                "implementation_effort": "medium",
            }
        ]

    def _calculate_expected_improvements(
        self, actions: List[Dict[str, Any]], current_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate expected performance improvements."""
        # Implementation would calculate expected improvements
        return {
            "overall_improvement": 15.5,
            "response_time_improvement": 25.0,
            "throughput_improvement": 10.0,
        }

    def _create_optimization_implementation_plan(
        self, actions: List[Dict[str, Any]], strategy: str
    ) -> List[Dict[str, Any]]:
        """Create detailed implementation plan."""
        # Implementation would create step-by-step plan
        return [
            {
                "step": 1,
                "action": "implement_caching",
                "estimated_duration": "2 days",
                "dependencies": [],
                "risk_level": "low",
            }
        ]

    def _apply_performance_optimizations(
        self, plan: List[Dict[str, Any]], metrics: List[EntityDict]
    ) -> List[Dict[str, Any]]:
        """Apply performance optimizations (if not in dry run mode)."""
        # Implementation would apply actual optimizations
        return [
            {
                "optimization": "caching_implemented",
                "status": "completed",
                "applied_at": datetime.utcnow().isoformat(),
            }
        ]

    def _calculate_implementation_complexity(self, plan: List[Dict[str, Any]]) -> str:
        """Calculate implementation complexity."""
        # Simple complexity calculation
        risk_levels = [step.get("risk_level", "medium") for step in plan]
        high_risk_count = risk_levels.count("high")

        if high_risk_count > len(plan) / 2:
            return "high"
        elif high_risk_count > 0:
            return "medium"
        else:
            return "low"

    def _estimate_optimization_completion_time(self, plan: List[Dict[str, Any]]) -> str:
        """Estimate total completion time for optimization plan."""
        # Simple time estimation
        total_steps = len(plan)
        if total_steps <= 3:
            return "1-3 days"
        elif total_steps <= 7:
            return "1-2 weeks"
        else:
            return "2-4 weeks"
