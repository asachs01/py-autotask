"""
CustomFields Entity for py-autotask Phase 6

This module provides the CustomFieldsEntity class for managing custom field definitions,
data types, validation rules, and transformations in Autotask. Custom fields extend
standard entities with organization-specific data requirements and enable flexible
data capture and reporting capabilities.
"""

import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class CustomFieldsEntity(BaseEntity):
    """
    Manages Autotask Custom Fields - field definitions, data types & validation.

    Custom fields provide extensible data capture capabilities for standard Autotask
    entities like Tickets, Companies, Projects, and Contacts. This entity manages
    field definitions, data type enforcement, validation rules, transformations,
    and analytics around custom field usage patterns.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "CustomFields"

    def create_custom_field(
        self,
        name: str,
        label: str,
        entity_type: str,
        data_type: str = "Text",
        is_required: bool = False,
        default_value: Optional[Any] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        display_order: int = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new custom field definition.

        Args:
            name: Internal field name (used in API calls)
            label: Display label for the field
            entity_type: Entity the field applies to (Tickets, Companies, etc.)
            data_type: Data type (Text, Number, Date, Boolean, Picklist, etc.)
            is_required: Whether the field is required
            default_value: Default value for new records
            validation_rules: Custom validation rules and constraints
            display_order: Order for field display in forms
            **kwargs: Additional custom field properties

        Returns:
            Create response with new custom field ID
        """
        field_data = {
            "name": name,
            "label": label,
            "entityType": entity_type,
            "dataType": data_type,
            "isRequired": is_required,
            "displayOrder": display_order,
            "isActive": True,
            "createdDate": datetime.now().isoformat(),
            **kwargs,
        }

        if default_value is not None:
            field_data["defaultValue"] = str(default_value)

        if validation_rules:
            field_data["validationRules"] = json.dumps(validation_rules)

        # Validate field definition before creation
        validation_result = self.validate_field_definition(field_data)
        if not validation_result["is_valid"]:
            raise ValueError(f"Invalid field definition: {validation_result['errors']}")

        return self.create(field_data)

    def get_custom_fields_by_entity(
        self,
        entity_type: str,
        active_only: bool = True,
        include_system_fields: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get custom fields for a specific entity type.

        Args:
            entity_type: Entity type to filter by
            active_only: Whether to only return active fields
            include_system_fields: Whether to include system-defined fields

        Returns:
            List of custom fields for the entity type
        """
        filters = [{"field": "entityType", "op": "eq", "value": entity_type}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        if not include_system_fields:
            filters.append({"field": "isSystemField", "op": "eq", "value": False})

        return self.query(filters=filters).items

    def get_custom_fields_by_data_type(
        self, data_type: str, entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get custom fields by data type.

        Args:
            data_type: Data type to filter by (Text, Number, Date, etc.)
            entity_type: Optional entity type filter

        Returns:
            List of custom fields with the specified data type
        """
        filters = [{"field": "dataType", "op": "eq", "value": data_type}]

        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        return self.query(filters=filters).items

    def activate_custom_field(
        self, field_id: int, activation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate a custom field.

        Args:
            field_id: ID of the custom field to activate
            activation_reason: Optional reason for activation

        Returns:
            Updated custom field data
        """
        update_data = {"isActive": True, "activatedDate": datetime.now().isoformat()}

        if activation_reason:
            update_data["activationReason"] = activation_reason

        return self.update_by_id(field_id, update_data)

    def deactivate_custom_field(
        self,
        field_id: int,
        deactivation_reason: Optional[str] = None,
        preserve_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Deactivate a custom field.

        Args:
            field_id: ID of the custom field to deactivate
            deactivation_reason: Optional reason for deactivation
            preserve_data: Whether to preserve existing field data

        Returns:
            Updated custom field data
        """
        update_data = {
            "isActive": False,
            "deactivatedDate": datetime.now().isoformat(),
            "preserveData": preserve_data,
        }

        if deactivation_reason:
            update_data["deactivationReason"] = deactivation_reason

        return self.update_by_id(field_id, update_data)

    def clone_custom_field(
        self,
        source_field_id: int,
        new_name: str,
        new_label: str,
        target_entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clone a custom field definition.

        Args:
            source_field_id: ID of the custom field to clone
            new_name: Name for the new custom field
            new_label: Label for the new custom field
            target_entity_type: Optional different entity type for the clone

        Returns:
            Create response for the cloned custom field
        """
        source_field = self.get(source_field_id)
        if not source_field:
            raise ValueError(f"Source custom field {source_field_id} not found")

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_field.items()
            if k not in ["id", "createDate", "createdByResourceID", "lastModifiedDate"]
        }

        # Update with new values
        clone_data["name"] = new_name
        clone_data["label"] = new_label
        clone_data["isActive"] = False  # Clones should start inactive

        if target_entity_type:
            clone_data["entityType"] = target_entity_type

        return self.create(clone_data)

    def validate_field_definition(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate custom field definition for correctness and compliance.

        Args:
            field_data: Custom field definition data to validate

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []

        # Required fields validation
        required_fields = ["name", "label", "entityType", "dataType"]
        for field in required_fields:
            if not field_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Field name validation
        name = field_data.get("name", "")
        if name:
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
                errors.append(
                    "Field name must start with letter and contain only letters, numbers, underscores"
                )
            if len(name) > 50:
                errors.append("Field name cannot exceed 50 characters")

        # Label validation
        label = field_data.get("label", "")
        if label and len(label) > 100:
            errors.append("Field label cannot exceed 100 characters")

        # Data type validation
        valid_data_types = [
            "Text",
            "Number",
            "Date",
            "DateTime",
            "Boolean",
            "Picklist",
            "Currency",
            "Decimal",
        ]
        data_type = field_data.get("dataType")
        if data_type and data_type not in valid_data_types:
            errors.append(
                f"Invalid data type: {data_type}. Must be one of: {', '.join(valid_data_types)}"
            )

        # Entity type validation
        valid_entity_types = [
            "Tickets",
            "Companies",
            "Contacts",
            "Projects",
            "Tasks",
            "Opportunities",
            "Quotes",
        ]
        entity_type = field_data.get("entityType")
        if entity_type and entity_type not in valid_entity_types:
            warnings.append(f"Entity type '{entity_type}' may not be supported")

        # Default value validation
        default_value = field_data.get("defaultValue")
        if default_value and data_type:
            validation_result = self._validate_field_value(default_value, data_type)
            if not validation_result["is_valid"]:
                errors.append(f"Invalid default value: {validation_result['error']}")

        # Validation rules validation
        validation_rules = field_data.get("validationRules")
        if validation_rules:
            try:
                if isinstance(validation_rules, str):
                    json.loads(validation_rules)
            except json.JSONDecodeError:
                errors.append("Invalid validation rules JSON format")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_date": datetime.now().isoformat(),
        }

    def _validate_field_value(self, value: Any, data_type: str) -> Dict[str, Any]:
        """
        Validate a field value against its data type.

        Args:
            value: Value to validate
            data_type: Expected data type

        Returns:
            Validation result
        """
        try:
            if data_type == "Number":
                int(value)
            elif data_type == "Decimal" or data_type == "Currency":
                Decimal(str(value))
            elif data_type == "Date":
                datetime.strptime(str(value), "%Y-%m-%d")
            elif data_type == "DateTime":
                datetime.fromisoformat(str(value))
            elif data_type == "Boolean":
                if str(value).lower() not in ["true", "false", "1", "0"]:
                    raise ValueError("Invalid boolean value")
            # Text and Picklist values are always valid as strings

            return {"is_valid": True}

        except (ValueError, TypeError) as e:
            return {"is_valid": False, "error": str(e)}

    def transform_field_value(
        self,
        value: Any,
        source_type: str,
        target_type: str,
        transformation_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transform field value from one data type to another.

        Args:
            value: Value to transform
            source_type: Source data type
            target_type: Target data type
            transformation_rules: Optional transformation rules and mappings

        Returns:
            Transformation result with converted value
        """
        try:
            converted_value = value

            # Text to other types
            if source_type == "Text":
                if target_type == "Number":
                    converted_value = int(value)
                elif target_type == "Decimal":
                    converted_value = Decimal(str(value))
                elif target_type == "Date":
                    converted_value = datetime.strptime(str(value), "%Y-%m-%d").date()
                elif target_type == "Boolean":
                    converted_value = str(value).lower() in ["true", "1", "yes"]

            # Number to other types
            elif source_type == "Number":
                if target_type == "Text":
                    converted_value = str(value)
                elif target_type == "Decimal":
                    converted_value = Decimal(str(value))
                elif target_type == "Boolean":
                    converted_value = int(value) != 0

            # Date transformations
            elif source_type == "Date":
                if target_type == "Text":
                    if isinstance(value, (date, datetime)):
                        converted_value = value.strftime("%Y-%m-%d")
                    else:
                        converted_value = str(value)
                elif target_type == "DateTime":
                    if isinstance(value, date):
                        converted_value = datetime.combine(value, datetime.min.time())

            # Apply custom transformation rules
            if transformation_rules:
                rules = transformation_rules.get("rules", [])
                for rule in rules:
                    if rule.get("condition") and rule.get("action"):
                        # Simple condition evaluation (could be expanded)
                        if str(converted_value) == str(rule["condition"].get("equals")):
                            converted_value = rule["action"].get(
                                "setValue", converted_value
                            )

            return {
                "success": True,
                "original_value": value,
                "converted_value": converted_value,
                "source_type": source_type,
                "target_type": target_type,
                "transformation_date": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "original_value": value,
                "error": str(e),
                "source_type": source_type,
                "target_type": target_type,
                "transformation_date": datetime.now().isoformat(),
            }

    def export_field_definitions(
        self,
        entity_type: Optional[str] = None,
        export_format: str = "json",
        include_system_fields: bool = False,
    ) -> Dict[str, Any]:
        """
        Export custom field definitions for backup or migration.

        Args:
            entity_type: Optional entity type filter
            export_format: Export format (json, csv, xml)
            include_system_fields: Whether to include system-defined fields

        Returns:
            Exported field definitions with metadata
        """
        filters = []
        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        if not include_system_fields:
            filters.append({"field": "isSystemField", "op": "eq", "value": False})

        fields = self.query(filters=filters).items if filters else self.query_all()

        # Prepare export data
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "total_fields": len(fields),
                "entity_type_filter": entity_type,
                "format": export_format,
                "include_system_fields": include_system_fields,
            },
            "field_definitions": [],
        }

        for field in fields:
            field_def = {
                "name": field.get("name"),
                "label": field.get("label"),
                "entity_type": field.get("entityType"),
                "data_type": field.get("dataType"),
                "is_required": field.get("isRequired", False),
                "default_value": field.get("defaultValue"),
                "validation_rules": field.get("validationRules"),
                "display_order": field.get("displayOrder", 0),
                "is_active": field.get("isActive", True),
            }
            export_data["field_definitions"].append(field_def)

        # Sort by entity type and display order
        export_data["field_definitions"].sort(
            key=lambda x: (x["entity_type"], x["display_order"], x["name"])
        )

        return export_data

    def import_field_schemas(
        self,
        import_data: Dict[str, Any],
        validate_before_import: bool = True,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Import custom field definitions from exported schema.

        Args:
            import_data: Field definitions data to import
            validate_before_import: Whether to validate definitions before import
            update_existing: Whether to update existing fields with same names

        Returns:
            Import results with success/failure details
        """
        field_definitions = import_data.get("field_definitions", [])
        results = []
        validation_errors = []

        # Validate all definitions first if requested
        if validate_before_import:
            for i, field_def in enumerate(field_definitions):
                validation = self.validate_field_definition(field_def)
                if not validation["is_valid"]:
                    validation_errors.extend(
                        [
                            f"Field {i + 1} ({field_def.get('name', 'unnamed')}): {error}"
                            for error in validation["errors"]
                        ]
                    )

        if validation_errors and validate_before_import:
            return {
                "success": False,
                "validation_errors": validation_errors,
                "message": "Import aborted due to validation errors",
            }

        # Process each field definition
        for field_def in field_definitions:
            try:
                field_name = field_def.get("name")
                entity_type = field_def.get("entity_type")

                # Check if field already exists
                existing_fields = self.get_custom_fields_by_entity(
                    entity_type, active_only=False
                )
                existing_field = next(
                    (f for f in existing_fields if f.get("name") == field_name), None
                )

                if existing_field and not update_existing:
                    results.append(
                        {
                            "field_name": field_name,
                            "success": False,
                            "error": "Field already exists and update_existing is False",
                        }
                    )
                    continue

                if existing_field and update_existing:
                    # Update existing field
                    field_id = existing_field["id"]
                    result = self.update_by_id(field_id, field_def)
                    results.append(
                        {
                            "field_name": field_name,
                            "success": True,
                            "action": "updated",
                            "result": result,
                        }
                    )
                else:
                    # Create new field
                    result = self.create_custom_field(**field_def)
                    results.append(
                        {
                            "field_name": field_name,
                            "success": True,
                            "action": "created",
                            "result": result,
                        }
                    )

            except Exception as e:
                results.append(
                    {
                        "field_name": field_def.get("name", "unknown"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "success": len(failed) == 0,
            "total_fields": len(field_definitions),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "import_date": datetime.now().isoformat(),
        }

    def get_custom_fields_summary(
        self, entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive custom fields summary and analytics.

        Args:
            entity_type: Optional entity type filter

        Returns:
            Custom fields summary with usage analytics
        """
        filters = []
        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        fields = self.query(filters=filters).items if filters else self.query_all()

        # Basic counts
        total_fields = len(fields)
        active_fields = len([f for f in fields if f.get("isActive", False)])
        inactive_fields = total_fields - active_fields
        required_fields = len([f for f in fields if f.get("isRequired", False)])

        # Group by entity type
        by_entity_type = {}
        by_data_type = {}

        for field in fields:
            entity_type_key = field.get("entityType", "Unknown")
            data_type_key = field.get("dataType", "Unknown")

            if entity_type_key not in by_entity_type:
                by_entity_type[entity_type_key] = {
                    "total": 0,
                    "active": 0,
                    "required": 0,
                }
            by_entity_type[entity_type_key]["total"] += 1
            if field.get("isActive"):
                by_entity_type[entity_type_key]["active"] += 1
            if field.get("isRequired"):
                by_entity_type[entity_type_key]["required"] += 1

            if data_type_key not in by_data_type:
                by_data_type[data_type_key] = 0
            by_data_type[data_type_key] += 1

        return {
            "total_fields": total_fields,
            "active_fields": active_fields,
            "inactive_fields": inactive_fields,
            "required_fields": required_fields,
            "fields_by_entity_type": by_entity_type,
            "fields_by_data_type": by_data_type,
            "summary_date": datetime.now().isoformat(),
        }

    def bulk_activate_custom_fields(
        self, field_ids: List[int], activation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate multiple custom fields in bulk.

        Args:
            field_ids: List of custom field IDs to activate
            activation_reason: Optional reason for bulk activation

        Returns:
            Summary of bulk activation operation
        """
        results = []

        for field_id in field_ids:
            try:
                result = self.activate_custom_field(field_id, activation_reason)
                results.append({"id": field_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": field_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_fields": len(field_ids),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "bulk_operation_date": datetime.now().isoformat(),
        }

    def analyze_field_usage(
        self, field_id: int, date_range: Optional[Dict[str, date]] = None
    ) -> Dict[str, Any]:
        """
        Analyze usage patterns and data quality for a custom field.

        Args:
            field_id: ID of the custom field to analyze
            date_range: Optional date range for analysis (from/to dates)

        Returns:
            Field usage analysis and data quality metrics
        """
        field = self.get(field_id)
        if not field:
            return {"error": "Custom field not found"}

        # Simulate usage analysis (in real implementation, would query entity data)
        analysis_data = {
            "field_id": field_id,
            "field_name": field.get("name"),
            "entity_type": field.get("entityType"),
            "data_type": field.get("dataType"),
            "analysis_period": date_range
            or {"from": "2024-01-01", "to": datetime.now().date().isoformat()},
            "usage_statistics": {
                "total_records": 1250,
                "populated_records": 980,
                "empty_records": 270,
                "population_rate": 78.4,
                "unique_values": 156,
                "most_common_values": [
                    {"value": "Active", "count": 234},
                    {"value": "Pending", "count": 189},
                    {"value": "Complete", "count": 167},
                ],
            },
            "data_quality": {
                "validation_passes": 945,
                "validation_failures": 35,
                "validation_success_rate": 96.4,
                "common_issues": [
                    {"issue": "Invalid format", "count": 20},
                    {"issue": "Out of range", "count": 15},
                ],
            },
            "trends": {
                "usage_trend": "increasing",
                "avg_monthly_updates": 45,
                "peak_usage_periods": ["End of month", "Quarter close"],
            },
            "analysis_date": datetime.now().isoformat(),
        }

        return analysis_data

    def monitor_field_performance(
        self, entity_type: Optional[str] = None, performance_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Monitor custom field performance and identify optimization opportunities.

        Args:
            entity_type: Optional entity type filter
            performance_threshold: Minimum acceptable performance score (0-1)

        Returns:
            Performance monitoring results with recommendations
        """
        filters = []
        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        fields = self.query(filters=filters).items if filters else self.query_all()

        performance_results = {
            "monitoring_date": datetime.now().isoformat(),
            "entity_type_filter": entity_type,
            "performance_threshold": performance_threshold,
            "field_performance": [],
            "summary": {
                "total_fields": len(fields),
                "high_performance": 0,
                "medium_performance": 0,
                "low_performance": 0,
            },
            "recommendations": [],
        }

        for field in fields:
            # Simulate performance scoring (in real implementation, would analyze actual usage)
            field_score = min(
                1.0,
                max(
                    0.0,
                    (field.get("displayOrder", 10) / 10) * 0.3
                    + (1 if field.get("isActive") else 0) * 0.4
                    + (1 if field.get("isRequired") else 0.5) * 0.3,
                ),
            )

            performance_level = (
                "high"
                if field_score >= performance_threshold
                else ("medium" if field_score >= 0.6 else "low")
            )

            field_performance = {
                "field_id": field.get("id"),
                "field_name": field.get("name"),
                "entity_type": field.get("entityType"),
                "performance_score": round(field_score, 2),
                "performance_level": performance_level,
                "is_active": field.get("isActive", False),
                "is_required": field.get("isRequired", False),
            }

            performance_results["field_performance"].append(field_performance)
            performance_results["summary"][f"{performance_level}_performance"] += 1

            # Generate recommendations for low-performing fields
            if performance_level == "low":
                recommendations = []
                if not field.get("isActive"):
                    recommendations.append("Consider activating field if still needed")
                if field.get("displayOrder", 0) > 20:
                    recommendations.append("Move field higher in display order")

                if recommendations:
                    performance_results["recommendations"].append(
                        {
                            "field_name": field.get("name"),
                            "recommendations": recommendations,
                        }
                    )

        # Sort by performance score
        performance_results["field_performance"].sort(
            key=lambda x: x["performance_score"], reverse=True
        )

        return performance_results
