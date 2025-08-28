"""
Pandas integration for py-autotask.

This module provides seamless integration between Autotask API data and pandas DataFrames,
enabling powerful data analysis, manipulation, and visualization capabilities.
"""

import asyncio
import logging
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    import pandas as pd
except ImportError:
    raise ImportError(
        "Pandas integration requires pandas and numpy. "
        "Install with: pip install 'py-autotask[pandas]'"
    )

from .async_client import AsyncAutotaskClient
from .client import AutotaskClient

logger = logging.getLogger(__name__)


class AutotaskDataFrame(pd.DataFrame):
    """
    Enhanced DataFrame with Autotask-specific functionality.

    Provides additional methods for working with Autotask data including
    relationship resolution, bulk operations, and entity-specific analytics.
    """

    _metadata = ["_client", "_entity_type", "_source_query"]

    def __init__(
        self, data=None, client=None, entity_type=None, source_query=None, **kwargs
    ):
        super().__init__(data, **kwargs)
        self._client = client
        self._entity_type = entity_type
        self._source_query = source_query

    @property
    def _constructor(self):
        return AutotaskDataFrame

    def to_autotask(self, operation: str = "update") -> Dict[str, Any]:
        """
        Convert DataFrame back to Autotask entities.

        Args:
            operation: Operation type ('create', 'update', 'upsert')

        Returns:
            Dictionary with operation results
        """
        if not self._client:
            raise ValueError("DataFrame was not created from Autotask client")

        records = self.to_dict("records")

        if operation == "create":
            return asyncio.run(self._bulk_create(records))
        elif operation == "update":
            return asyncio.run(self._bulk_update(records))
        elif operation == "upsert":
            return asyncio.run(self._bulk_upsert(records))
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    async def _bulk_create(self, records: List[Dict]) -> Dict[str, Any]:
        """Bulk create records in Autotask."""
        if hasattr(self._client, "bulk_manager"):
            bulk_manager = self._client.bulk_manager
        else:
            from .bulk_manager import IntelligentBulkManager

            bulk_manager = IntelligentBulkManager(self._client)

        return await bulk_manager.bulk_create(self._entity_type, records)

    async def _bulk_update(self, records: List[Dict]) -> Dict[str, Any]:
        """Bulk update records in Autotask."""
        if hasattr(self._client, "bulk_manager"):
            bulk_manager = self._client.bulk_manager
        else:
            from .bulk_manager import IntelligentBulkManager

            bulk_manager = IntelligentBulkManager(self._client)

        return await bulk_manager.bulk_update(self._entity_type, records)

    async def _bulk_upsert(self, records: List[Dict]) -> Dict[str, Any]:
        """Bulk upsert (update or create) records in Autotask."""
        # Separate records with and without IDs
        create_records = [r for r in records if not r.get("id")]
        update_records = [r for r in records if r.get("id")]

        results = {"create": None, "update": None}

        if create_records:
            results["create"] = await self._bulk_create(create_records)

        if update_records:
            results["update"] = await self._bulk_update(update_records)

        return results

    def resolve_relationships(self, relationships: List[str]) -> "AutotaskDataFrame":
        """
        Resolve entity relationships and add related data as columns.

        Args:
            relationships: List of relationships to resolve
                          Format: ['field_name:target_entity', ...]
                          Example: ['accountID:companies', 'assignedResourceID:resources']

        Returns:
            New AutotaskDataFrame with relationship data
        """
        if not self._client:
            raise ValueError("DataFrame was not created from Autotask client")

        return asyncio.run(self._resolve_relationships_async(relationships))

    async def _resolve_relationships_async(
        self, relationships: List[str]
    ) -> "AutotaskDataFrame":
        """Async implementation of relationship resolution."""
        df = self.copy()

        for relationship in relationships:
            try:
                field_name, target_entity = relationship.split(":")

                if field_name not in df.columns:
                    logger.warning(f"Field {field_name} not found in DataFrame")
                    continue

                # Get unique IDs
                unique_ids = df[field_name].dropna().unique().tolist()

                if not unique_ids:
                    continue

                # Fetch related entities
                if hasattr(self._client, f"{target_entity}"):
                    entity_handler = getattr(self._client, target_entity)

                    related_data = {}
                    for entity_id in unique_ids:
                        try:
                            if hasattr(entity_handler, "get_async"):
                                entity = await entity_handler.get_async(entity_id)
                            else:
                                entity = entity_handler.get(entity_id)

                            if entity:
                                related_data[entity_id] = entity
                        except Exception as e:
                            logger.warning(
                                f"Failed to fetch {target_entity} {entity_id}: {e}"
                            )

                    # Add related data columns
                    for key in [
                        "name",
                        "title",
                        "firstName",
                        "lastName",
                        "companyName",
                    ]:
                        if not related_data:
                            continue

                        # Check if any related entity has this field
                        sample_entity = next(iter(related_data.values()))
                        if key in sample_entity:
                            column_name = f"{target_entity}_{key}"
                            df[column_name] = df[field_name].map(
                                lambda x: (
                                    related_data.get(x, {}).get(key)
                                    if pd.notna(x)
                                    else None
                                )
                            )

            except ValueError:
                logger.error(
                    f"Invalid relationship format: {relationship}. Use 'field:entity'"
                )
                continue
            except Exception as e:
                logger.error(f"Error resolving relationship {relationship}: {e}")
                continue

        return AutotaskDataFrame(
            df,
            client=self._client,
            entity_type=self._entity_type,
            source_query=self._source_query,
        )

    def analyze_trends(
        self,
        date_column: str = "createDate",
        group_by: Optional[str] = None,
        period: str = "D",
    ) -> pd.DataFrame:
        """
        Analyze trends over time.

        Args:
            date_column: Column containing dates
            group_by: Optional column to group by
            period: Pandas frequency string ('D', 'W', 'M', 'Q', 'Y')

        Returns:
            DataFrame with trend analysis
        """
        if date_column not in self.columns:
            raise ValueError(f"Date column '{date_column}' not found")

        df = self.copy()

        # Convert date column to datetime
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

        # Remove rows with invalid dates
        df = df.dropna(subset=[date_column])

        if df.empty:
            return pd.DataFrame()

        # Set date as index for resampling
        df.set_index(date_column, inplace=True)

        if group_by and group_by in df.columns:
            # Group by category and resample
            result = df.groupby(group_by).resample(period).size().unstack(fill_value=0)
        else:
            # Simple time series
            result = df.resample(period).size().to_frame("count")

        return result

    def ticket_analytics(self) -> Dict[str, Any]:
        """
        Perform ticket-specific analytics.

        Returns:
            Dictionary with various ticket metrics
        """
        if self._entity_type != "tickets":
            warnings.warn("ticket_analytics() is designed for ticket data")

        analytics = {}

        # Basic counts
        analytics["total_tickets"] = len(self)

        # Status distribution
        if "status" in self.columns:
            analytics["status_distribution"] = self["status"].value_counts().to_dict()

        # Priority distribution
        if "priority" in self.columns:
            analytics["priority_distribution"] = (
                self["priority"].value_counts().to_dict()
            )

        # Average resolution time (if available)
        if all(col in self.columns for col in ["createDate", "completedDate"]):
            df = self.copy()
            df["createDate"] = pd.to_datetime(df["createDate"], errors="coerce")
            df["completedDate"] = pd.to_datetime(df["completedDate"], errors="coerce")

            completed_tickets = df.dropna(subset=["createDate", "completedDate"])
            if not completed_tickets.empty:
                resolution_times = (
                    completed_tickets["completedDate"] - completed_tickets["createDate"]
                )
                analytics["avg_resolution_time_hours"] = (
                    resolution_times.dt.total_seconds().mean() / 3600
                )
                analytics["median_resolution_time_hours"] = (
                    resolution_times.dt.total_seconds().median() / 3600
                )

        # Top accounts by ticket count
        if "accountID" in self.columns:
            analytics["top_accounts"] = (
                self["accountID"].value_counts().head(10).to_dict()
            )

        # Tickets by queue
        if "queueID" in self.columns:
            analytics["queue_distribution"] = self["queueID"].value_counts().to_dict()

        return analytics

    def time_entry_analytics(self) -> Dict[str, Any]:
        """
        Perform time entry specific analytics.

        Returns:
            Dictionary with time entry metrics
        """
        if self._entity_type != "time_entries":
            warnings.warn("time_entry_analytics() is designed for time entry data")

        analytics = {}

        # Total time metrics
        if "hoursWorked" in self.columns:
            analytics["total_hours"] = self["hoursWorked"].sum()
            analytics["average_hours_per_entry"] = self["hoursWorked"].mean()

        if "hoursToBill" in self.columns:
            analytics["total_billable_hours"] = self["hoursToBill"].sum()

            # Utilization rate
            if "hoursWorked" in self.columns:
                analytics["utilization_rate"] = (
                    self["hoursToBill"].sum() / self["hoursWorked"].sum() * 100
                    if self["hoursWorked"].sum() > 0
                    else 0
                )

        # Resource productivity
        if "resourceID" in self.columns:
            resource_stats = (
                self.groupby("resourceID")
                .agg({"hoursWorked": "sum", "hoursToBill": "sum"})
                .to_dict()
            )
            analytics["resource_productivity"] = resource_stats

        # Time by project
        if "projectID" in self.columns and "hoursWorked" in self.columns:
            analytics["project_time_distribution"] = (
                self.groupby("projectID")["hoursWorked"].sum().to_dict()
            )

        return analytics


class PandasIntegration:
    """
    Main class for pandas integration with Autotask API.

    Provides convenient methods to convert Autotask data to/from pandas DataFrames
    and perform common data analysis operations.
    """

    def __init__(self, client: Union[AutotaskClient, AsyncAutotaskClient]):
        """
        Initialize pandas integration.

        Args:
            client: Autotask client instance
        """
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.PandasIntegration")

    async def to_dataframe(
        self,
        entity_type: str,
        filters: Optional[List[Dict]] = None,
        date_range: Optional[tuple] = None,
        include_relationships: Optional[List[str]] = None,
        max_records: Optional[int] = None,
    ) -> AutotaskDataFrame:
        """
        Convert Autotask entity data to pandas DataFrame.

        Args:
            entity_type: Type of entity to query
            filters: Query filters
            date_range: Tuple of (start_date, end_date) as strings
            include_relationships: List of relationships to resolve
            max_records: Maximum records to fetch

        Returns:
            AutotaskDataFrame with Autotask data

        Example:
            df = await integration.to_dataframe(
                "tickets",
                filters=[{"field": "status", "op": "ne", "value": "5"}],
                date_range=("2024-01-01", "2024-12-31"),
                include_relationships=["accountID:companies"]
            )
        """
        # Build query
        query_params = {}
        if filters:
            query_params["filters"] = filters
        if max_records:
            query_params["max_records"] = max_records

        # Add date range filter
        if date_range:
            start_date, end_date = date_range
            date_filter = {
                "field": "createDate",
                "op": "between",
                "value": f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
            }
            if filters:
                query_params["filters"].append(date_filter)
            else:
                query_params["filters"] = [date_filter]

        # Query data
        entity_handler = getattr(self.client.entities, entity_type)

        if hasattr(entity_handler, "query_all_async"):
            response = await entity_handler.query_all_async(**query_params)
            records = response.items if hasattr(response, "items") else response
        else:
            response = entity_handler.query_all(**query_params)
            records = response.items if hasattr(response, "items") else response

        # Convert to DataFrame
        df = AutotaskDataFrame(
            records,
            client=self.client,
            entity_type=entity_type,
            source_query=query_params,
        )

        # Resolve relationships if requested
        if include_relationships and not df.empty:
            df = await df._resolve_relationships_async(include_relationships)

        self.logger.info(f"Created DataFrame with {len(df)} {entity_type} records")

        return df

    def from_dataframe(
        self, df: pd.DataFrame, entity_type: str, operation: str = "create"
    ) -> Dict[str, Any]:
        """
        Upload DataFrame data to Autotask.

        Args:
            df: Pandas DataFrame with entity data
            entity_type: Target entity type
            operation: Operation type ('create', 'update', 'upsert')

        Returns:
            Dictionary with operation results
        """
        df.to_dict("records")

        # Create AutotaskDataFrame for bulk operations
        autotask_df = AutotaskDataFrame(df, client=self.client, entity_type=entity_type)

        return autotask_df.to_autotask(operation)

    async def analyze_entity_trends(
        self,
        entity_type: str,
        date_range: tuple,
        group_by: Optional[str] = None,
        period: str = "D",
    ) -> pd.DataFrame:
        """
        Analyze trends for an entity type.

        Args:
            entity_type: Entity type to analyze
            date_range: Tuple of (start_date, end_date)
            group_by: Optional field to group by
            period: Time period for analysis

        Returns:
            DataFrame with trend analysis
        """
        df = await self.to_dataframe(
            entity_type,
            date_range=date_range,
            max_records=10000,  # Reasonable limit for trend analysis
        )

        return df.analyze_trends(group_by=group_by, period=period)

    async def generate_report(
        self, entity_type: str, date_range: tuple, report_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive reports for entity data.

        Args:
            entity_type: Entity type to report on
            date_range: Date range for the report
            report_type: Type of report ('summary', 'detailed', 'trends')

        Returns:
            Dictionary with report data
        """
        df = await self.to_dataframe(entity_type, date_range=date_range)

        if df.empty:
            return {"error": "No data found for the specified criteria"}

        report = {
            "entity_type": entity_type,
            "date_range": date_range,
            "total_records": len(df),
            "generated_at": datetime.now().isoformat(),
        }

        if report_type in ["summary", "detailed"]:
            # Basic statistics
            report["basic_stats"] = {
                "record_count": len(df),
                "date_range_actual": {
                    "start": (
                        df["createDate"].min() if "createDate" in df.columns else None
                    ),
                    "end": (
                        df["createDate"].max() if "createDate" in df.columns else None
                    ),
                },
            }

            # Entity-specific analytics
            if entity_type == "tickets":
                report["analytics"] = df.ticket_analytics()
            elif entity_type == "time_entries":
                report["analytics"] = df.time_entry_analytics()

        if report_type in ["trends", "detailed"]:
            # Trend analysis
            if "createDate" in df.columns:
                trends = df.analyze_trends(period="D")
                report["trends"] = trends.to_dict() if not trends.empty else {}

        return report


# Convenience functions for global use
async def to_dataframe(
    entity_type: str, client: Union[AutotaskClient, AsyncAutotaskClient], **kwargs
) -> AutotaskDataFrame:
    """
    Convenience function to create DataFrame from Autotask data.

    Args:
        entity_type: Entity type to query
        client: Autotask client
        **kwargs: Additional arguments for to_dataframe

    Returns:
        AutotaskDataFrame with data
    """
    integration = PandasIntegration(client)
    return await integration.to_dataframe(entity_type, **kwargs)


def from_dataframe(
    df: pd.DataFrame,
    entity_type: str,
    client: Union[AutotaskClient, AsyncAutotaskClient],
    operation: str = "create",
) -> Dict[str, Any]:
    """
    Convenience function to upload DataFrame to Autotask.

    Args:
        df: Pandas DataFrame
        entity_type: Target entity type
        client: Autotask client
        operation: Operation type

    Returns:
        Operation results
    """
    integration = PandasIntegration(client)
    return integration.from_dataframe(df, entity_type, operation)
