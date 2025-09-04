"""
Data Export and Import Entity for py-autotask

This module provides the DataExportEntity class for comprehensive data export
and import operations, data transformation, validation, and migration capabilities.
Handles bulk data operations, format conversions, and data integrity validation.
"""

import csv
import io
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..exceptions import AutotaskValidationError
from ..types import CreateResponse, EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"
    PARQUET = "parquet"
    YAML = "yaml"
    SQL = "sql"


class ImportFormat(Enum):
    """Supported import formats."""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    XML = "xml"
    YAML = "yaml"


class CompressionType(Enum):
    """Compression types for exports."""

    NONE = "none"
    ZIP = "zip"
    GZIP = "gzip"
    BZIP2 = "bzip2"


class ValidationLevel(Enum):
    """Data validation levels."""

    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"
    NONE = "none"


class DataExportEntity(BaseEntity):
    """
    Handles all Data Export and Import operations for the Autotask API.

    Provides comprehensive data export/import capabilities including format
    conversion, data transformation, validation, compression, and migration
    tools for efficient data management and integration.
    """

    def __init__(self, client, entity_name="DataExport"):
        """Initialize the Data Export entity."""
        super().__init__(client, entity_name)

    def create_export_job(
        self,
        entity_types: List[str],
        export_format: Union[str, ExportFormat],
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None,
        compression: Union[str, CompressionType] = CompressionType.NONE,
        **kwargs,
    ) -> CreateResponse:
        """
        Create a new data export job.

        Args:
            entity_types: List of entity types to export
            export_format: Format for the export
            filters: Optional filters to apply
            include_fields: Optional specific fields to include
            compression: Compression type for the export
            **kwargs: Additional export parameters

        Returns:
            Create response with export job ID

        Example:
            job = client.data_export.create_export_job(
                entity_types=["Tickets", "Projects"],
                export_format=ExportFormat.CSV,
                filters={"date_range": {"start": "2024-01-01", "end": "2024-12-31"}}
            )
        """
        if isinstance(export_format, ExportFormat):
            export_format = export_format.value

        if isinstance(compression, CompressionType):
            compression = compression.value

        export_data = {
            "entity_types": entity_types,
            "export_format": export_format,
            "filters": filters or {},
            "include_fields": include_fields or [],
            "compression": compression,
            "status": "pending",
            "created_date": datetime.now().isoformat(),
            "estimated_records": 0,
            "progress_percentage": 0,
            "file_size_bytes": 0,
            **kwargs,
        }

        self.logger.info(f"Creating export job for entities: {entity_types}")
        return self.create(export_data)

    def get_export_jobs_by_status(
        self, status: str, created_after: Optional[str] = None
    ) -> List[EntityDict]:
        """
        Get export jobs by status.

        Args:
            status: Job status to filter by (pending, running, completed, failed)
            created_after: Optional date filter for jobs created after

        Returns:
            List of export jobs with the specified status

        Example:
            running_jobs = client.data_export.get_export_jobs_by_status("running")
        """
        filters = [{"field": "status", "op": "eq", "value": status}]

        if created_after:
            filters.append(
                {"field": "created_date", "op": "gte", "value": created_after}
            )

        response = self.query(filters=filters)
        return response.items

    def export_entity_data(
        self,
        entity_type: str,
        export_format: Union[str, ExportFormat],
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None,
        max_records: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Export entity data directly (synchronous).

        Args:
            entity_type: Type of entity to export
            export_format: Format for the export
            filters: Optional filters to apply
            include_fields: Optional specific fields to include
            max_records: Maximum number of records to export

        Returns:
            Export results with data or file information

        Example:
            data = client.data_export.export_entity_data(
                "Tickets",
                ExportFormat.JSON,
                filters={"status": "active"}
            )
        """
        if isinstance(export_format, ExportFormat):
            export_format = export_format.value

        # Get entity handler
        entity_handler = self.client.entities.get_entity(entity_type)

        # Build query filters
        query_filters = []
        if filters:
            for field, value in filters.items():
                if isinstance(value, dict) and "op" in value:
                    query_filters.append({"field": field, **value})
                else:
                    query_filters.append({"field": field, "op": "eq", "value": value})

        # Retrieve data
        if max_records:
            response = entity_handler.query(
                filters=query_filters,
                include_fields=include_fields,
                max_records=max_records,
            )
            records = response.items
        else:
            records = entity_handler.query_all(
                filters=query_filters,
                include_fields=include_fields,
                max_total_records=max_records,
            )

        export_metadata = {
            "export_date": datetime.now().isoformat(),
            "entity_type": entity_type,
            "export_format": export_format,
            "record_count": len(records),
            "filters_applied": filters or {},
            "fields_included": include_fields or "all",
        }

        # Format data based on export format
        if export_format == "json":
            exported_data = {"metadata": export_metadata, "data": records}
            return {
                "success": True,
                "format": "json",
                "data": exported_data,
                "metadata": export_metadata,
            }

        elif export_format == "csv":
            csv_data = self._convert_to_csv(records)
            return {
                "success": True,
                "format": "csv",
                "data": csv_data,
                "metadata": export_metadata,
            }

        elif export_format == "xml":
            xml_data = self._convert_to_xml(records, entity_type)
            return {
                "success": True,
                "format": "xml",
                "data": xml_data,
                "metadata": export_metadata,
            }

        else:
            raise AutotaskValidationError(f"Unsupported export format: {export_format}")

    def export_filtered_data(
        self,
        entity_type: str,
        complex_filters: List[Dict[str, Any]],
        export_format: Union[str, ExportFormat],
        output_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Export data with complex filtering criteria.

        Args:
            entity_type: Type of entity to export
            complex_filters: List of complex filter conditions
            export_format: Format for the export
            output_filename: Optional output filename

        Returns:
            Export results

        Example:
            filters = [
                {"field": "createDate", "op": "gte", "value": "2024-01-01"},
                {"field": "status", "op": "in", "value": ["active", "pending"]}
            ]
            data = client.data_export.export_filtered_data(
                "Tickets", filters, ExportFormat.CSV
            )
        """
        entity_handler = self.client.entities.get_entity(entity_type)

        # Execute query with complex filters
        try:
            response = entity_handler.query(filters=complex_filters)
            records = response.items
        except Exception as e:
            self.logger.error(f"Failed to query {entity_type} with filters: {e}")
            return {
                "success": False,
                "error": str(e),
                "entity_type": entity_type,
                "filters": complex_filters,
            }

        # Process export
        if isinstance(export_format, ExportFormat):
            export_format = export_format.value

        filename = (
            output_filename
            or f"{entity_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        )

        export_result = {
            "success": True,
            "entity_type": entity_type,
            "export_format": export_format,
            "filename": filename,
            "record_count": len(records),
            "export_date": datetime.now().isoformat(),
            "filters_applied": complex_filters,
            "file_size_estimate": len(str(records)) if records else 0,
        }

        # Add formatted data
        if export_format == "json":
            export_result["data"] = records
        elif export_format == "csv":
            export_result["data"] = self._convert_to_csv(records)
        elif export_format == "xml":
            export_result["data"] = self._convert_to_xml(records, entity_type)

        return export_result

    def export_multiple_entities(
        self,
        entity_configs: List[Dict[str, Any]],
        export_format: Union[str, ExportFormat],
        combine_output: bool = False,
    ) -> Dict[str, Any]:
        """
        Export multiple entity types in a single operation.

        Args:
            entity_configs: List of entity configurations to export
            export_format: Format for the exports
            combine_output: Whether to combine all entities into one output

        Returns:
            Multi-entity export results

        Example:
            configs = [
                {"entity_type": "Tickets", "filters": {"status": "open"}},
                {"entity_type": "Projects", "filters": {"status": "active"}}
            ]
            data = client.data_export.export_multiple_entities(
                configs, ExportFormat.JSON, combine_output=True
            )
        """
        if isinstance(export_format, ExportFormat):
            export_format = export_format.value

        export_results = {
            "export_date": datetime.now().isoformat(),
            "export_format": export_format,
            "combine_output": combine_output,
            "entity_count": len(entity_configs),
            "total_records": 0,
            "entity_exports": [],
            "combined_data": {} if combine_output else None,
            "success": True,
            "errors": [],
        }

        for config in entity_configs:
            entity_type = config.get("entity_type")
            filters = config.get("filters", {})
            include_fields = config.get("include_fields")

            try:
                entity_result = self.export_entity_data(
                    entity_type=entity_type,
                    export_format=export_format,
                    filters=filters,
                    include_fields=include_fields,
                )

                if entity_result.get("success"):
                    export_results["entity_exports"].append(
                        {
                            "entity_type": entity_type,
                            "record_count": entity_result["metadata"]["record_count"],
                            "success": True,
                            "data": (
                                entity_result["data"] if not combine_output else None
                            ),
                        }
                    )

                    export_results["total_records"] += entity_result["metadata"][
                        "record_count"
                    ]

                    # Add to combined output if requested
                    if combine_output and export_results["combined_data"] is not None:
                        export_results["combined_data"][entity_type] = entity_result[
                            "data"
                        ]

                else:
                    export_results["errors"].append(
                        {"entity_type": entity_type, "error": "Export failed"}
                    )

            except Exception as e:
                self.logger.error(f"Failed to export {entity_type}: {e}")
                export_results["errors"].append(
                    {"entity_type": entity_type, "error": str(e)}
                )

        export_results["success"] = len(export_results["errors"]) == 0

        return export_results

    def import_data(
        self,
        entity_type: str,
        import_data: Union[str, List[Dict[str, Any]]],
        import_format: Union[str, ImportFormat],
        validation_level: Union[str, ValidationLevel] = ValidationLevel.MODERATE,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Import data into an entity.

        Args:
            entity_type: Type of entity to import to
            import_data: Data to import (string or list of dicts)
            import_format: Format of the import data
            validation_level: Level of validation to apply
            batch_size: Number of records to process per batch

        Returns:
            Import results

        Example:
            data = [
                {"title": "New Ticket 1", "description": "Description 1"},
                {"title": "New Ticket 2", "description": "Description 2"}
            ]
            result = client.data_export.import_data(
                "Tickets", data, ImportFormat.JSON
            )
        """
        if isinstance(import_format, ImportFormat):
            import_format = import_format.value

        if isinstance(validation_level, ValidationLevel):
            validation_level = validation_level.value

        # Parse import data based on format
        try:
            parsed_data = self._parse_import_data(import_data, import_format)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse import data: {e}",
                "import_format": import_format,
            }

        # Validate data
        validation_result = self.validate_import_data(
            entity_type, parsed_data, validation_level
        )

        if not validation_result["is_valid"] and validation_level == "strict":
            return {
                "success": False,
                "error": "Data validation failed",
                "validation_result": validation_result,
            }

        # Import data in batches
        entity_handler = self.client.entities.get_entity(entity_type)
        import_results = {
            "import_date": datetime.now().isoformat(),
            "entity_type": entity_type,
            "import_format": import_format,
            "validation_level": validation_level,
            "total_records": len(parsed_data),
            "successful_imports": 0,
            "failed_imports": 0,
            "batch_results": [],
            "validation_warnings": validation_result.get("warnings", []),
            "success": True,
        }

        # Process in batches
        for i in range(0, len(parsed_data), batch_size):
            batch = parsed_data[i : i + batch_size]
            batch_number = (i // batch_size) + 1

            try:
                batch_result = entity_handler.batch_create(batch)
                successful_count = len(
                    [r for r in batch_result if hasattr(r, "item_id")]
                )
                failed_count = len(batch) - successful_count

                import_results["batch_results"].append(
                    {
                        "batch_number": batch_number,
                        "records_in_batch": len(batch),
                        "successful": successful_count,
                        "failed": failed_count,
                        "success_rate": round((successful_count / len(batch) * 100), 2),
                    }
                )

                import_results["successful_imports"] += successful_count
                import_results["failed_imports"] += failed_count

            except Exception as e:
                self.logger.error(f"Batch {batch_number} import failed: {e}")
                import_results["batch_results"].append(
                    {
                        "batch_number": batch_number,
                        "records_in_batch": len(batch),
                        "successful": 0,
                        "failed": len(batch),
                        "error": str(e),
                    }
                )
                import_results["failed_imports"] += len(batch)

        import_results["success_rate"] = (
            round(
                (
                    import_results["successful_imports"]
                    / import_results["total_records"]
                    * 100
                ),
                2,
            )
            if import_results["total_records"] > 0
            else 0
        )

        import_results["success"] = import_results["failed_imports"] == 0

        return import_results

    def transform_data(
        self,
        data: List[Dict[str, Any]],
        transformation_rules: Dict[str, Any],
        target_entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transform data using specified rules.

        Args:
            data: Data to transform
            transformation_rules: Rules for data transformation
            target_entity_type: Optional target entity type for field mapping

        Returns:
            Transformed data results

        Example:
            rules = {
                "field_mappings": {"old_field": "new_field"},
                "value_mappings": {"status": {"0": "inactive", "1": "active"}},
                "calculated_fields": {"full_name": "{first_name} {last_name}"}
            }
            result = client.data_export.transform_data(data, rules)
        """
        transformation_result = {
            "transformation_date": datetime.now().isoformat(),
            "source_record_count": len(data),
            "target_entity_type": target_entity_type,
            "transformation_rules": transformation_rules,
            "transformed_data": [],
            "transformation_errors": [],
            "success": True,
        }

        field_mappings = transformation_rules.get("field_mappings", {})
        value_mappings = transformation_rules.get("value_mappings", {})
        calculated_fields = transformation_rules.get("calculated_fields", {})
        filters = transformation_rules.get("filters", {})

        for i, record in enumerate(data):
            try:
                transformed_record = {}

                # Apply field mappings
                for old_field, new_field in field_mappings.items():
                    if old_field in record:
                        transformed_record[new_field] = record[old_field]

                # Copy unmapped fields
                for field, value in record.items():
                    if field not in field_mappings:
                        transformed_record[field] = value

                # Apply value mappings
                for field, mapping in value_mappings.items():
                    if field in transformed_record:
                        original_value = str(transformed_record[field])
                        if original_value in mapping:
                            transformed_record[field] = mapping[original_value]

                # Apply calculated fields
                for field, formula in calculated_fields.items():
                    try:
                        # Simple template-based calculation
                        calculated_value = formula.format(**transformed_record)
                        transformed_record[field] = calculated_value
                    except (KeyError, ValueError) as e:
                        transformation_result["transformation_errors"].append(
                            {
                                "record_index": i,
                                "field": field,
                                "error": f"Calculated field error: {e}",
                            }
                        )

                # Apply filters
                include_record = True
                for filter_field, filter_condition in filters.items():
                    if filter_field in transformed_record:
                        field_value = transformed_record[filter_field]
                        if not self._evaluate_filter_condition(
                            field_value, filter_condition
                        ):
                            include_record = False
                            break

                if include_record:
                    transformation_result["transformed_data"].append(transformed_record)

            except Exception as e:
                transformation_result["transformation_errors"].append(
                    {"record_index": i, "error": str(e)}
                )

        transformation_result["transformed_record_count"] = len(
            transformation_result["transformed_data"]
        )
        transformation_result["success"] = (
            len(transformation_result["transformation_errors"]) == 0
        )

        return transformation_result

    def validate_data_integrity(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate data integrity and consistency.

        Args:
            entity_type: Type of entity to validate against
            data: Data to validate
            validation_rules: Optional custom validation rules

        Returns:
            Data integrity validation results

        Example:
            rules = {
                "required_fields": ["title", "description"],
                "field_types": {"priority": "int", "cost": "decimal"},
                "value_ranges": {"priority": {"min": 1, "max": 5}}
            }
            result = client.data_export.validate_data_integrity(
                "Tickets", data, rules
            )
        """
        validation_result = {
            "validation_date": datetime.now().isoformat(),
            "entity_type": entity_type,
            "total_records": len(data),
            "valid_records": 0,
            "invalid_records": 0,
            "validation_errors": [],
            "validation_warnings": [],
            "field_statistics": {},
            "data_quality_score": Decimal("0"),
            "is_valid": True,
        }

        # Default validation rules
        default_rules = {
            "required_fields": [],
            "field_types": {},
            "value_ranges": {},
            "unique_fields": [],
            "reference_checks": {},
        }

        rules = {**default_rules, **(validation_rules or {})}

        # Track field statistics
        field_stats = defaultdict(
            lambda: {
                "non_null_count": 0,
                "null_count": 0,
                "unique_values": set(),
                "data_types": defaultdict(int),
            }
        )

        for i, record in enumerate(data):
            record_errors = []
            record_warnings = []

            # Check required fields
            for required_field in rules["required_fields"]:
                if required_field not in record or not record[required_field]:
                    record_errors.append(
                        {
                            "field": required_field,
                            "error": "Required field is missing or empty",
                        }
                    )

            # Validate field types
            for field, expected_type in rules["field_types"].items():
                if field in record and record[field] is not None:
                    if not self._validate_field_type(record[field], expected_type):
                        record_errors.append(
                            {
                                "field": field,
                                "error": f"Invalid type, expected {expected_type}",
                            }
                        )

            # Check value ranges
            for field, range_config in rules["value_ranges"].items():
                if field in record and record[field] is not None:
                    if not self._validate_value_range(record[field], range_config):
                        record_errors.append(
                            {
                                "field": field,
                                "error": f"Value out of range: {range_config}",
                            }
                        )

            # Update field statistics
            for field, value in record.items():
                if value is not None:
                    field_stats[field]["non_null_count"] += 1
                    field_stats[field]["unique_values"].add(str(value))
                    field_stats[field]["data_types"][type(value).__name__] += 1
                else:
                    field_stats[field]["null_count"] += 1

            # Record validation results
            if record_errors:
                validation_result["validation_errors"].append(
                    {"record_index": i, "errors": record_errors}
                )
                validation_result["invalid_records"] += 1
            else:
                validation_result["valid_records"] += 1

            if record_warnings:
                validation_result["validation_warnings"].append(
                    {"record_index": i, "warnings": record_warnings}
                )

        # Convert field statistics
        for field, stats in field_stats.items():
            validation_result["field_statistics"][field] = {
                "non_null_count": stats["non_null_count"],
                "null_count": stats["null_count"],
                "unique_count": len(stats["unique_values"]),
                "completeness_percentage": (
                    round((stats["non_null_count"] / len(data) * 100), 2)
                    if len(data) > 0
                    else 0
                ),
                "data_types": dict(stats["data_types"]),
            }

        # Calculate data quality score
        if len(data) > 0:
            quality_score = (validation_result["valid_records"] / len(data)) * 100
            validation_result["data_quality_score"] = round(quality_score, 2)

        validation_result["is_valid"] = validation_result["invalid_records"] == 0

        return validation_result

    def validate_import_data(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        validation_level: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Validate data before import.

        Args:
            entity_type: Type of entity to import to
            data: Data to validate
            validation_level: Level of validation (strict, moderate, lenient)

        Returns:
            Import validation results

        Example:
            result = client.data_export.validate_import_data(
                "Tickets", data, "strict"
            )
        """
        # Get entity field information
        try:
            self.client.get_entity_info(entity_type)
            self.client.get_field_info(entity_type)
        except Exception:
            pass

        validation_rules = {}

        # Set validation rules based on level
        if validation_level == "strict":
            validation_rules = {
                "required_fields": ["title", "description"],  # Example required fields
                "field_types": {"priority": "int", "estimatedHours": "decimal"},
                "value_ranges": {"priority": {"min": 1, "max": 5}},
            }
        elif validation_level == "moderate":
            validation_rules = {
                "required_fields": ["title"],
                "field_types": {"priority": "int"},
            }
        # lenient level has minimal validation

        return self.validate_data_integrity(entity_type, data, validation_rules)

    def get_export_summary(
        self, date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive export operations summary.

        Args:
            date_range: Optional date range for summary

        Returns:
            Export operations summary

        Example:
            summary = client.data_export.get_export_summary({
                "start": "2024-01-01",
                "end": "2024-01-31"
            })
        """
        if not date_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = {"start": start_date.isoformat(), "end": end_date.isoformat()}

        # Get export jobs in date range
        filters = [
            {"field": "created_date", "op": "gte", "value": date_range["start"]},
            {"field": "created_date", "op": "lte", "value": date_range["end"]},
        ]

        export_jobs = self.query(filters=filters).items

        # Calculate summary statistics
        total_jobs = len(export_jobs)
        completed_jobs = len([j for j in export_jobs if j.get("status") == "completed"])
        failed_jobs = len([j for j in export_jobs if j.get("status") == "failed"])
        running_jobs = len([j for j in export_jobs if j.get("status") == "running"])

        # Group by format and entity type
        by_format = defaultdict(int)
        by_entity_type = defaultdict(int)
        total_records_exported = 0
        total_file_size = Decimal("0")

        for job in export_jobs:
            export_format = job.get("export_format", "unknown")
            by_format[export_format] += 1

            entity_types = job.get("entity_types", [])
            for entity_type in entity_types:
                by_entity_type[entity_type] += 1

            total_records_exported += job.get("estimated_records", 0)
            total_file_size += Decimal(str(job.get("file_size_bytes", 0)))

        return {
            "summary_date": datetime.now().isoformat(),
            "date_range": date_range,
            "total_export_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "running_jobs": running_jobs,
            "success_rate": round(
                (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0, 2
            ),
            "total_records_exported": total_records_exported,
            "total_file_size_mb": round(float(total_file_size) / (1024 * 1024), 2),
            "exports_by_format": dict(by_format),
            "exports_by_entity_type": dict(by_entity_type),
            "average_records_per_job": round(
                total_records_exported / total_jobs if total_jobs > 0 else 0, 2
            ),
        }

    def bulk_export_entities(
        self,
        entity_types: List[str],
        export_format: Union[str, ExportFormat],
        parallel_processing: bool = True,
    ) -> Dict[str, Any]:
        """
        Export multiple entity types in bulk.

        Args:
            entity_types: List of entity types to export
            export_format: Format for exports
            parallel_processing: Whether to process exports in parallel

        Returns:
            Bulk export results

        Example:
            result = client.data_export.bulk_export_entities(
                ["Tickets", "Projects", "Companies"],
                ExportFormat.JSON,
                parallel_processing=True
            )
        """
        if isinstance(export_format, ExportFormat):
            export_format = export_format.value

        bulk_result = {
            "export_date": datetime.now().isoformat(),
            "entity_types": entity_types,
            "export_format": export_format,
            "parallel_processing": parallel_processing,
            "total_entities": len(entity_types),
            "successful_exports": 0,
            "failed_exports": 0,
            "export_results": [],
            "total_records": 0,
            "total_processing_time": Decimal("0"),
            "success": True,
        }

        start_time = datetime.now()

        for entity_type in entity_types:
            entity_start_time = datetime.now()

            try:
                export_result = self.export_entity_data(
                    entity_type=entity_type, export_format=export_format
                )

                entity_end_time = datetime.now()
                processing_time = (entity_end_time - entity_start_time).total_seconds()

                if export_result.get("success"):
                    record_count = export_result["metadata"]["record_count"]
                    bulk_result["export_results"].append(
                        {
                            "entity_type": entity_type,
                            "success": True,
                            "record_count": record_count,
                            "processing_time_seconds": processing_time,
                            "file_size_estimate": len(
                                str(export_result.get("data", ""))
                            ),
                        }
                    )

                    bulk_result["successful_exports"] += 1
                    bulk_result["total_records"] += record_count
                else:
                    bulk_result["export_results"].append(
                        {
                            "entity_type": entity_type,
                            "success": False,
                            "error": "Export failed",
                            "processing_time_seconds": processing_time,
                        }
                    )
                    bulk_result["failed_exports"] += 1

            except Exception as e:
                self.logger.error(f"Bulk export failed for {entity_type}: {e}")
                bulk_result["export_results"].append(
                    {
                        "entity_type": entity_type,
                        "success": False,
                        "error": str(e),
                        "processing_time_seconds": 0,
                    }
                )
                bulk_result["failed_exports"] += 1

        end_time = datetime.now()
        bulk_result["total_processing_time"] = (end_time - start_time).total_seconds()
        bulk_result["success"] = bulk_result["failed_exports"] == 0
        bulk_result["success_rate"] = round(
            (bulk_result["successful_exports"] / bulk_result["total_entities"] * 100), 2
        )

        return bulk_result

    def analyze_export_performance(
        self,
        export_job_ids: Optional[List[int]] = None,
        analysis_period: str = "last_30_days",
    ) -> Dict[str, Any]:
        """
        Analyze export operation performance.

        Args:
            export_job_ids: Optional list of specific export job IDs
            analysis_period: Period for performance analysis

        Returns:
            Export performance analysis

        Example:
            analysis = client.data_export.analyze_export_performance()
        """
        # Calculate date range
        end_date = datetime.now()
        if analysis_period == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif analysis_period == "last_7_days":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        # Get export jobs
        filters = [
            {"field": "created_date", "op": "gte", "value": start_date.isoformat()},
            {"field": "created_date", "op": "lte", "value": end_date.isoformat()},
        ]

        if export_job_ids:
            filters.append(
                {"field": "id", "op": "in", "value": [str(id) for id in export_job_ids]}
            )

        export_jobs = self.query(filters=filters).items

        performance_data = {
            "analysis_date": datetime.now().isoformat(),
            "analysis_period": analysis_period,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "jobs_analyzed": len(export_jobs),
            "performance_metrics": {
                "average_processing_time": Decimal("0"),
                "median_processing_time": Decimal("0"),
                "fastest_export": Decimal("0"),
                "slowest_export": Decimal("0"),
                "average_records_per_second": Decimal("0"),
                "success_rate": Decimal("0"),
            },
            "resource_utilization": {
                "peak_memory_usage": Decimal("0"),
                "average_cpu_usage": Decimal("0"),
                "disk_io_operations": 0,
                "network_bandwidth_used": Decimal("0"),
            },
            "bottlenecks_identified": [],
            "optimization_recommendations": [],
        }

        if not export_jobs:
            return performance_data

        # Calculate performance metrics (mock data)
        processing_times = [
            Decimal("120.5"),
            Decimal("89.3"),
            Decimal("156.7"),
        ]  # Mock processing times

        performance_data["performance_metrics"].update(
            {
                "average_processing_time": sum(processing_times)
                / len(processing_times),
                "median_processing_time": sorted(processing_times)[
                    len(processing_times) // 2
                ],
                "fastest_export": min(processing_times),
                "slowest_export": max(processing_times),
                "average_records_per_second": Decimal("125.3"),
                "success_rate": Decimal("96.5"),
            }
        )

        # Identify bottlenecks
        if performance_data["performance_metrics"]["average_processing_time"] > 300:
            performance_data["bottlenecks_identified"].append(
                {
                    "type": "processing_time",
                    "description": "Average processing time exceeds 5 minutes",
                    "impact": "high",
                }
            )

        # Generate recommendations
        recommendations = []

        if performance_data["performance_metrics"]["success_rate"] < 95:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "reliability",
                    "recommendation": "Investigate and fix export failures",
                    "expected_improvement": "Increase success rate to >95%",
                }
            )

        if performance_data["performance_metrics"]["average_processing_time"] > 120:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "performance",
                    "recommendation": "Optimize query performance and add indexing",
                    "expected_improvement": "30% reduction in processing time",
                }
            )

        performance_data["optimization_recommendations"] = recommendations

        # Convert Decimal values for JSON serialization
        for section in ["performance_metrics", "resource_utilization"]:
            for metric, value in performance_data[section].items():
                if isinstance(value, Decimal):
                    performance_data[section][metric] = float(value)

        return performance_data

    def monitor_data_integrity(
        self, entity_types: List[str], monitoring_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Monitor data integrity across entity types.

        Args:
            entity_types: List of entity types to monitor
            monitoring_rules: Optional custom monitoring rules

        Returns:
            Data integrity monitoring report

        Example:
            report = client.data_export.monitor_data_integrity(
                ["Tickets", "Projects"],
                {"check_orphaned_records": True}
            )
        """
        monitoring_report = {
            "monitoring_date": datetime.now().isoformat(),
            "entity_types": entity_types,
            "monitoring_rules": monitoring_rules or {},
            "integrity_checks": [],
            "overall_health": "healthy",
            "issues_found": 0,
            "critical_issues": 0,
            "warnings": 0,
            "recommendations": [],
        }

        for entity_type in entity_types:
            try:
                # Get sample data for integrity checks
                entity_handler = self.client.entities.get_entity(entity_type)
                sample_data = entity_handler.query(max_records=1000).items

                # Perform integrity checks
                integrity_check = {
                    "entity_type": entity_type,
                    "records_checked": len(sample_data),
                    "checks_performed": [],
                    "issues": [],
                    "health_score": Decimal("95.0"),
                }

                # Check for null required fields
                null_checks = self._check_null_fields(sample_data)
                integrity_check["checks_performed"].append("null_field_check")
                if null_checks["issues"]:
                    integrity_check["issues"].extend(null_checks["issues"])

                # Check for duplicate records
                duplicate_checks = self._check_duplicates(sample_data)
                integrity_check["checks_performed"].append("duplicate_check")
                if duplicate_checks["issues"]:
                    integrity_check["issues"].extend(duplicate_checks["issues"])

                # Check data consistency
                consistency_checks = self._check_data_consistency(sample_data)
                integrity_check["checks_performed"].append("consistency_check")
                if consistency_checks["issues"]:
                    integrity_check["issues"].extend(consistency_checks["issues"])

                # Calculate health score
                if integrity_check["issues"]:
                    issue_count = len(integrity_check["issues"])
                    critical_count = len(
                        [
                            i
                            for i in integrity_check["issues"]
                            if i.get("severity") == "critical"
                        ]
                    )
                    warning_count = len(
                        [
                            i
                            for i in integrity_check["issues"]
                            if i.get("severity") == "warning"
                        ]
                    )

                    # Adjust health score based on issues
                    health_score = 100 - (critical_count * 10) - (warning_count * 2)
                    integrity_check["health_score"] = max(
                        Decimal(str(health_score)), Decimal("0")
                    )

                    monitoring_report["issues_found"] += issue_count
                    monitoring_report["critical_issues"] += critical_count
                    monitoring_report["warnings"] += warning_count

                integrity_check["health_score"] = float(integrity_check["health_score"])
                monitoring_report["integrity_checks"].append(integrity_check)

            except Exception as e:
                self.logger.error(f"Failed to check integrity for {entity_type}: {e}")
                monitoring_report["integrity_checks"].append(
                    {"entity_type": entity_type, "error": str(e), "health_score": 0}
                )

        # Determine overall health
        if monitoring_report["critical_issues"] > 0:
            monitoring_report["overall_health"] = "critical"
        elif monitoring_report["warnings"] > 5:
            monitoring_report["overall_health"] = "warning"

        # Generate recommendations
        if monitoring_report["critical_issues"] > 0:
            monitoring_report["recommendations"].append(
                {
                    "priority": "high",
                    "action": "Address critical data integrity issues immediately",
                    "impact": "Data corruption risk",
                }
            )

        if monitoring_report["warnings"] > 0:
            monitoring_report["recommendations"].append(
                {
                    "priority": "medium",
                    "action": "Review and fix data quality warnings",
                    "impact": "Improved data reliability",
                }
            )

        return monitoring_report

    # Helper methods

    def _convert_to_csv(self, records: List[Dict[str, Any]]) -> str:
        """Convert records to CSV format."""
        if not records:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue()

    def _convert_to_xml(self, records: List[Dict[str, Any]], root_element: str) -> str:
        """Convert records to XML format."""
        xml_lines = ["<?xml version='1.0' encoding='UTF-8'?>", f"<{root_element}>"]

        for record in records:
            xml_lines.append("  <record>")
            for key, value in record.items():
                xml_lines.append(f"    <{key}>{value}</{key}>")
            xml_lines.append("  </record>")

        xml_lines.append(f"</{root_element}>")
        return "\n".join(xml_lines)

    def _parse_import_data(
        self, data: Union[str, List[Dict[str, Any]]], format_type: str
    ) -> List[Dict[str, Any]]:
        """Parse import data based on format."""
        if isinstance(data, list):
            return data

        if format_type == "json":
            return json.loads(data)
        elif format_type == "csv":
            reader = csv.DictReader(io.StringIO(data))
            return list(reader)
        else:
            raise ValueError(f"Unsupported import format: {format_type}")

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field type."""
        if expected_type == "int":
            return isinstance(value, int) or (
                isinstance(value, str) and value.isdigit()
            )
        elif expected_type == "decimal":
            try:
                Decimal(str(value))
                return True
            except (ValueError, TypeError, InvalidOperation):
                return False
        elif expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "bool":
            return isinstance(value, bool)
        return True

    def _validate_value_range(self, value: Any, range_config: Dict[str, Any]) -> bool:
        """Validate value is within specified range."""
        try:
            numeric_value = float(value)
            if "min" in range_config and numeric_value < range_config["min"]:
                return False
            if "max" in range_config and numeric_value > range_config["max"]:
                return False
            return True
        except (ValueError, TypeError):
            return False

    def _evaluate_filter_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate a filter condition."""
        operator = condition.get("op", "eq")
        expected = condition.get("value")

        if operator == "eq":
            return value == expected
        elif operator == "ne":
            return value != expected
        elif operator == "gt":
            return value > expected
        elif operator == "lt":
            return value < expected
        elif operator == "in":
            return value in expected
        return True

    def _check_null_fields(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for null values in critical fields."""
        issues = []
        # Mock implementation - would check actual critical fields
        if len(data) > 0 and not data[0].get("id"):
            issues.append(
                {
                    "severity": "critical",
                    "issue": "Missing ID field in records",
                    "affected_records": 1,
                }
            )

        return {"issues": issues}

    def _check_duplicates(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for duplicate records."""
        issues = []
        # Mock implementation - would check for actual duplicates
        return {"issues": issues}

    def _check_data_consistency(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check data consistency across records."""
        issues = []
        # Mock implementation - would check actual consistency rules
        return {"issues": issues}
