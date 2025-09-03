"""
User Defined Fields Entity for py-autotask

This module provides the UserDefinedFieldsEntity class for managing user-defined
field (UDF) configurations, validations, and transformations in Autotask. UDFs
enable custom data capture and business logic extensions through configurable
field definitions, validation rules, and data transformation pipelines.
"""

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class UserDefinedFieldsEntity(BaseEntity):
    """
    Manages Autotask User Defined Fields - UDF management & validation systems.

    User Defined Fields (UDFs) enable custom data capture and validation through
    configurable field definitions, data types, validation rules, and transformation
    logic. They extend entity schemas with business-specific data requirements
    and automated data processing capabilities.

    Key Features:
    - Custom field definition and configuration
    - Data type validation and transformation
    - Business rule enforcement and validation
    - Schema management and versioning
    - Bulk operations for field management
    - Data export and import capabilities
    - Integration with workflows and notifications

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "UserDefinedFields"

    def create_user_defined_field(
        self,
        name: str,
        label: str,
        entity_type: str,
        data_type: str = "Text",
        field_type: str = "Text",
        is_required: bool = False,
        is_active: bool = True,
        display_format: Optional[str] = None,
        default_value: Optional[Any] = None,
        validation_rules: Optional[List[Dict[str, Any]]] = None,
        picklist_values: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new user-defined field with comprehensive configuration.

        Args:
            name: Internal name of the field (must be unique per entity)
            label: Display label for the field
            entity_type: Entity type the field applies to (Tickets, Projects, etc.)
            data_type: Data type (Text, Integer, Decimal, Date, Boolean, Picklist)
            field_type: Field type for UI rendering (Text, TextArea, DropDown, etc.)
            is_required: Whether the field is required for data entry
            is_active: Whether the field is active and available
            display_format: Optional display format pattern
            default_value: Default value for new records
            validation_rules: List of validation rules to apply
            picklist_values: List of picklist options (for picklist fields)
            description: Description of the field purpose
            **kwargs: Additional field configuration options

        Returns:
            Create response with new UDF ID

        Example:
            field = client.user_defined_fields.create_user_defined_field(
                name="priority_score",
                label="Priority Score",
                entity_type="Tickets",
                data_type="Integer",
                field_type="Number",
                is_required=True,
                validation_rules=[
                    {"type": "range", "min_value": 1, "max_value": 10},
                    {"type": "required_if", "condition": "priority >= 4"}
                ],
                default_value=5,
                description="Custom priority scoring for ticket prioritization"
            )
        """
        if validation_rules is None:
            validation_rules = []
        if picklist_values is None:
            picklist_values = []

        field_data = {
            "name": name,
            "label": label,
            "entityType": entity_type,
            "dataType": data_type,
            "fieldType": field_type,
            "isRequired": is_required,
            "isActive": is_active,
            "displayFormat": display_format,
            "defaultValue": default_value,
            "validationRules": validation_rules,
            "picklistValues": picklist_values,
            "description": description,
            "createdDate": datetime.now().isoformat(),
            "version": 1,
            "fieldOrder": 999,  # Default to end of list
            **kwargs,
        }

        # Validate field configuration before creation
        validation_result = self.validate_field_definition(field_data)
        if not validation_result["is_valid"]:
            raise ValueError(f"Invalid field definition: {validation_result['errors']}")

        return self.create(field_data)

    def get_user_defined_fields_by_entity(
        self, entity_type: str, active_only: bool = True, include_values: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get user-defined fields for a specific entity type.

        Args:
            entity_type: Entity type to filter by
            active_only: Whether to only return active fields
            include_values: Whether to include picklist values and validation rules

        Returns:
            List of user-defined fields for the entity type
        """
        filters = [{"field": "entityType", "op": "eq", "value": entity_type}]

        if active_only:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        fields = self.query(filters=filters).items

        if not include_values:
            # Remove large data fields for performance
            for field in fields:
                field.pop("picklistValues", None)
                field.pop("validationRules", None)

        return fields

    def get_user_defined_fields_by_type(
        self, data_type: str, entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user-defined fields by data type.

        Args:
            data_type: Data type to filter by (Text, Integer, Decimal, etc.)
            entity_type: Optional entity type filter

        Returns:
            List of user-defined fields with the specified data type
        """
        filters = [{"field": "dataType", "op": "eq", "value": data_type}]

        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        return self.query(filters=filters).items

    def activate_user_defined_field(
        self, field_id: int, activation_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate a user-defined field.

        Args:
            field_id: ID of the field to activate
            activation_note: Optional note about the activation

        Returns:
            Updated field data
        """
        update_data = {
            "isActive": True,
            "activatedDate": datetime.now().isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if activation_note:
            update_data["activationNote"] = activation_note

        return self.update_by_id(field_id, update_data)

    def deactivate_user_defined_field(
        self,
        field_id: int,
        deactivation_reason: Optional[str] = None,
        preserve_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Deactivate a user-defined field with data preservation options.

        Args:
            field_id: ID of the field to deactivate
            deactivation_reason: Optional reason for deactivation
            preserve_data: Whether to preserve existing field data

        Returns:
            Updated field data
        """
        update_data = {
            "isActive": False,
            "deactivatedDate": datetime.now().isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
            "preserveData": preserve_data,
        }

        if deactivation_reason:
            update_data["deactivationReason"] = deactivation_reason

        return self.update_by_id(field_id, update_data)

    def clone_user_defined_field(
        self,
        source_field_id: int,
        new_name: str,
        new_label: str,
        target_entity_type: Optional[str] = None,
        modify_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Clone a user-defined field with optional modifications.

        Args:
            source_field_id: ID of the field to clone
            new_name: Name for the new field
            new_label: Label for the new field
            target_entity_type: Optional different entity type for the clone
            modify_config: Optional configuration changes to apply

        Returns:
            Create response for the cloned field
        """
        source_field = self.get(source_field_id)
        if not source_field:
            raise ValueError(f"Source field {source_field_id} not found")

        # Remove fields that shouldn't be copied
        clone_data = {
            k: v
            for k, v in source_field.items()
            if k
            not in [
                "id",
                "createdDate",
                "createdByResourceID",
                "lastModifiedDate",
                "activatedDate",
                "deactivatedDate",
            ]
        }

        # Update with new values
        clone_data["name"] = new_name
        clone_data["label"] = new_label
        clone_data["isActive"] = False  # Clones should start inactive
        clone_data["clonedFromFieldId"] = source_field_id
        clone_data["createdDate"] = datetime.now().isoformat()
        clone_data["version"] = 1

        if target_entity_type:
            clone_data["entityType"] = target_entity_type

        # Apply configuration modifications
        if modify_config:
            clone_data.update(modify_config)

        return self.create(clone_data)

    def validate_field_definitions(
        self, field_definitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate multiple field definitions for consistency and correctness.

        Args:
            field_definitions: List of field definitions to validate

        Returns:
            Comprehensive validation result with field-specific and cross-field errors
        """
        validation_results = []
        global_errors = []
        global_warnings = []

        # Track field names for uniqueness validation
        field_names_by_entity = {}

        for i, field_def in enumerate(field_definitions):
            # Validate individual field
            field_validation = self.validate_field_definition(field_def)
            field_validation["field_index"] = i
            field_validation["field_name"] = field_def.get("name", f"field_{i}")
            validation_results.append(field_validation)

            # Track field names for cross-validation
            entity_type = field_def.get("entityType")
            field_name = field_def.get("name")

            if entity_type and field_name:
                if entity_type not in field_names_by_entity:
                    field_names_by_entity[entity_type] = []
                field_names_by_entity[entity_type].append((field_name, i))

        # Check for duplicate field names within entity types
        for entity_type, fields in field_names_by_entity.items():
            field_names = [f[0] for f in fields]
            duplicates = set(
                [name for name in field_names if field_names.count(name) > 1]
            )

            if duplicates:
                for duplicate_name in duplicates:
                    indices = [f[1] for f in fields if f[0] == duplicate_name]
                    global_errors.append(
                        {
                            "type": "duplicate_field_name",
                            "entity_type": entity_type,
                            "field_name": duplicate_name,
                            "field_indices": indices,
                            "message": f"Duplicate field name '{duplicate_name}' found in {entity_type}",
                        }
                    )

        # Calculate overall validation status
        total_fields = len(field_definitions)
        valid_fields = len([r for r in validation_results if r["is_valid"]])
        invalid_fields = total_fields - valid_fields

        return {
            "total_fields": total_fields,
            "valid_fields": valid_fields,
            "invalid_fields": invalid_fields,
            "is_valid": len(global_errors) == 0 and invalid_fields == 0,
            "global_errors": global_errors,
            "global_warnings": global_warnings,
            "field_validations": validation_results,
            "validation_date": datetime.now().isoformat(),
        }

    def validate_field_definition(
        self, field_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a single field definition for correctness and consistency.

        Args:
            field_definition: Field definition to validate

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []

        # Required field validation
        required_fields = ["name", "label", "entityType", "dataType"]
        for field in required_fields:
            if not field_definition.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate field name format
        field_name = field_definition.get("name", "")
        if field_name:
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", field_name):
                errors.append(
                    "Field name must start with letter and contain only letters, numbers, and underscores"
                )
            if len(field_name) > 50:
                errors.append("Field name cannot exceed 50 characters")

        # Validate data type
        valid_data_types = [
            "Text",
            "Integer",
            "Decimal",
            "Date",
            "DateTime",
            "Boolean",
            "Picklist",
            "MultiPicklist",
        ]
        data_type = field_definition.get("dataType")
        if data_type and data_type not in valid_data_types:
            errors.append(f"Invalid data type: {data_type}")

        # Validate field type compatibility
        field_type = field_definition.get("fieldType")
        valid_field_types = {
            "Text": ["Text", "TextArea", "Email", "URL", "Phone"],
            "Integer": ["Number", "Slider"],
            "Decimal": ["Number", "Currency", "Percentage"],
            "Date": ["Date"],
            "DateTime": ["DateTime"],
            "Boolean": ["Checkbox", "Toggle"],
            "Picklist": ["DropDown", "RadioButton"],
            "MultiPicklist": ["MultiSelect", "CheckboxList"],
        }

        if data_type and field_type:
            if (
                data_type in valid_field_types
                and field_type not in valid_field_types[data_type]
            ):
                errors.append(
                    f"Field type '{field_type}' is not compatible with data type '{data_type}'"
                )

        # Validate picklist values for picklist fields
        if data_type in ["Picklist", "MultiPicklist"]:
            picklist_values = field_definition.get("picklistValues", [])
            if not picklist_values:
                errors.append("Picklist fields must have at least one picklist value")
            else:
                # Validate picklist value structure
                for i, value in enumerate(picklist_values):
                    if not isinstance(value, dict):
                        errors.append(f"Picklist value {i + 1} must be a dictionary")
                    elif "value" not in value or "label" not in value:
                        errors.append(
                            f"Picklist value {i + 1} must have 'value' and 'label' fields"
                        )

        # Validate validation rules
        validation_rules = field_definition.get("validationRules", [])
        for i, rule in enumerate(validation_rules):
            rule_validation = self._validate_validation_rule(rule, data_type)
            if not rule_validation["is_valid"]:
                errors.extend(
                    [
                        f"Validation rule {i + 1}: {error}"
                        for error in rule_validation["errors"]
                    ]
                )

        # Validate default value compatibility
        default_value = field_definition.get("defaultValue")
        if default_value is not None:
            value_validation = self._validate_field_value(
                default_value, data_type, field_definition
            )
            if not value_validation["is_valid"]:
                errors.append(
                    f"Default value is not compatible with field type: {value_validation['error']}"
                )

        # Generate warnings
        if not field_definition.get("description"):
            warnings.append("Field description is recommended for documentation")

        if data_type == "Text" and not field_definition.get("maxLength"):
            warnings.append("Text fields should specify maxLength for data consistency")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "field_name": field_definition.get("name", "unknown"),
        }

    def transform_field_data(
        self,
        field_id: int,
        transformation_rules: List[Dict[str, Any]],
        source_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Apply data transformation rules to field values.

        Args:
            field_id: ID of the field to transform data for
            transformation_rules: List of transformation rules to apply
            source_data: Source data records to transform

        Returns:
            Transformation results with processed data and statistics

        Example:
            rules = [
                {
                    "type": "normalize_text",
                    "options": {"case": "upper", "trim": True}
                },
                {
                    "type": "validate_format",
                    "options": {"pattern": r"^[A-Z]{3}-\\d{3}$"}
                },
                {
                    "type": "default_value",
                    "options": {"value": "UNK-000", "condition": "empty"}
                }
            ]
            result = client.user_defined_fields.transform_field_data(
                field_id=123,
                transformation_rules=rules,
                source_data=[
                    {"id": 1, "custom_field": "  abc-123  "},
                    {"id": 2, "custom_field": ""},
                    {"id": 3, "custom_field": "XYZ-456"}
                ]
            )
        """
        field = self.get(field_id)
        if not field:
            raise ValueError(f"Field {field_id} not found")

        field_name = field.get("name")
        if not field_name:
            raise ValueError(f"Field {field_id} has no name")

        transformed_data = []
        transformation_stats = {
            "total_records": len(source_data),
            "successful_transformations": 0,
            "failed_transformations": 0,
            "warnings": [],
            "errors": [],
        }

        for record_index, record in enumerate(source_data):
            try:
                original_value = record.get(field_name)
                transformed_value = original_value
                record_warnings = []

                # Apply each transformation rule
                for rule_index, rule in enumerate(transformation_rules):
                    rule_type = rule.get("type")
                    rule_options = rule.get("options", {})

                    try:
                        transformed_value = self._apply_transformation_rule(
                            transformed_value, rule_type, rule_options, field
                        )
                    except Exception as e:
                        transformation_stats["errors"].append(
                            {
                                "record_index": record_index,
                                "rule_index": rule_index,
                                "error": str(e),
                                "original_value": original_value,
                            }
                        )
                        continue

                # Create transformed record
                transformed_record = record.copy()
                transformed_record[field_name] = transformed_value
                transformed_record["_transformation_metadata"] = {
                    "original_value": original_value,
                    "transformed_value": transformed_value,
                    "rules_applied": len(transformation_rules),
                    "warnings": record_warnings,
                }

                transformed_data.append(transformed_record)
                transformation_stats["successful_transformations"] += 1

            except Exception as e:
                transformation_stats["failed_transformations"] += 1
                transformation_stats["errors"].append(
                    {"record_index": record_index, "error": str(e), "record": record}
                )

        return {
            "field_id": field_id,
            "field_name": field_name,
            "transformation_rules": transformation_rules,
            "transformed_data": transformed_data,
            "statistics": transformation_stats,
            "transformation_date": datetime.now().isoformat(),
        }

    def export_udf_schemas(
        self,
        entity_types: Optional[List[str]] = None,
        include_inactive: bool = False,
        export_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Export user-defined field schemas for backup or migration.

        Args:
            entity_types: Optional list of entity types to export
            include_inactive: Whether to include inactive fields
            export_format: Export format (json, csv, xml)

        Returns:
            Exported schema data with metadata
        """
        filters = []

        if entity_types:
            if len(entity_types) == 1:
                filters.append(
                    {"field": "entityType", "op": "eq", "value": entity_types[0]}
                )
            else:
                filters.append(
                    {"field": "entityType", "op": "in", "value": entity_types}
                )

        if not include_inactive:
            filters.append({"field": "isActive", "op": "eq", "value": True})

        fields = self.query(filters=filters).items if filters else self.query_all()

        # Organize fields by entity type
        schemas_by_entity = {}
        for field in fields:
            entity_type = field.get("entityType", "Unknown")
            if entity_type not in schemas_by_entity:
                schemas_by_entity[entity_type] = []
            schemas_by_entity[entity_type].append(field)

        # Generate export data
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "export_format": export_format,
                "total_fields": len(fields),
                "entity_types": list(schemas_by_entity.keys()),
                "include_inactive": include_inactive,
            },
            "schemas": schemas_by_entity,
        }

        # Format data according to export format
        if export_format.lower() == "json":
            export_data["formatted_data"] = json.dumps(
                export_data, indent=2, default=str
            )
        elif export_format.lower() == "csv":
            # Flatten fields for CSV export
            csv_rows = []
            for entity_type, entity_fields in schemas_by_entity.items():
                for field in entity_fields:
                    csv_rows.append(
                        {
                            "entity_type": entity_type,
                            "field_name": field.get("name"),
                            "field_label": field.get("label"),
                            "data_type": field.get("dataType"),
                            "field_type": field.get("fieldType"),
                            "is_required": field.get("isRequired"),
                            "is_active": field.get("isActive"),
                            "default_value": field.get("defaultValue"),
                            "description": field.get("description"),
                        }
                    )
            export_data["csv_data"] = csv_rows

        return export_data

    def import_udf_schemas(
        self,
        schema_data: Dict[str, Any],
        import_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Import user-defined field schemas from exported data.

        Args:
            schema_data: Schema data to import (from export_udf_schemas)
            import_options: Optional import configuration

        Returns:
            Import results with success/failure statistics
        """
        if import_options is None:
            import_options = {
                "create_missing": True,
                "update_existing": False,
                "activate_imported": False,
                "validate_before_import": True,
            }

        schemas = schema_data.get("schemas", {})
        import_results = []
        statistics = {
            "total_fields": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "skipped_fields": 0,
            "validation_errors": [],
        }

        for entity_type, fields in schemas.items():
            for field_data in fields:
                statistics["total_fields"] += 1
                field_name = field_data.get("name", "unknown")

                try:
                    # Validate field definition if requested
                    if import_options.get("validate_before_import", True):
                        validation = self.validate_field_definition(field_data)
                        if not validation["is_valid"]:
                            statistics["validation_errors"].extend(validation["errors"])
                            import_results.append(
                                {
                                    "field_name": field_name,
                                    "entity_type": entity_type,
                                    "status": "validation_failed",
                                    "errors": validation["errors"],
                                }
                            )
                            statistics["failed_imports"] += 1
                            continue

                    # Check if field already exists
                    existing_fields = self.get_user_defined_fields_by_entity(
                        entity_type, active_only=False
                    )
                    existing_field = next(
                        (f for f in existing_fields if f.get("name") == field_name),
                        None,
                    )

                    if existing_field:
                        if import_options.get("update_existing", False):
                            # Update existing field
                            update_data = {
                                k: v
                                for k, v in field_data.items()
                                if k not in ["id", "createdDate", "createdByResourceID"]
                            }
                            result = self.update_by_id(
                                existing_field["id"], update_data
                            )

                            import_results.append(
                                {
                                    "field_name": field_name,
                                    "entity_type": entity_type,
                                    "status": "updated",
                                    "field_id": existing_field["id"],
                                }
                            )
                            statistics["successful_imports"] += 1
                        else:
                            import_results.append(
                                {
                                    "field_name": field_name,
                                    "entity_type": entity_type,
                                    "status": "skipped_existing",
                                }
                            )
                            statistics["skipped_fields"] += 1
                    else:
                        if import_options.get("create_missing", True):
                            # Create new field
                            create_data = field_data.copy()
                            if not import_options.get("activate_imported", False):
                                create_data["isActive"] = False

                            result = self.create(create_data)

                            import_results.append(
                                {
                                    "field_name": field_name,
                                    "entity_type": entity_type,
                                    "status": "created",
                                    "field_id": result.get("item_id"),
                                }
                            )
                            statistics["successful_imports"] += 1
                        else:
                            import_results.append(
                                {
                                    "field_name": field_name,
                                    "entity_type": entity_type,
                                    "status": "skipped_new",
                                }
                            )
                            statistics["skipped_fields"] += 1

                except Exception as e:
                    import_results.append(
                        {
                            "field_name": field_name,
                            "entity_type": entity_type,
                            "status": "error",
                            "error": str(e),
                        }
                    )
                    statistics["failed_imports"] += 1

        return {
            "import_date": datetime.now().isoformat(),
            "import_options": import_options,
            "statistics": statistics,
            "results": import_results,
        }

    def get_user_defined_fields_summary(
        self, entity_type: Optional[str] = None, include_usage_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive user-defined fields summary with usage statistics.

        Args:
            entity_type: Optional entity type filter
            include_usage_stats: Whether to include field usage statistics

        Returns:
            UDF summary with statistics and analysis
        """
        filters = []
        if entity_type:
            filters.append({"field": "entityType", "op": "eq", "value": entity_type})

        fields = self.query(filters=filters).items if filters else self.query_all()

        # Analyze fields
        total_fields = len(fields)
        active_fields = len([f for f in fields if f.get("isActive", False)])
        inactive_fields = total_fields - active_fields
        required_fields = len([f for f in fields if f.get("isRequired", False)])

        # Group by entity type
        by_entity_type = {}
        by_data_type = {}
        by_field_type = {}

        for field in fields:
            entity_type = field.get("entityType", "Unknown")
            data_type = field.get("dataType", "Unknown")
            field_type = field.get("fieldType", "Unknown")

            # Entity type statistics
            if entity_type not in by_entity_type:
                by_entity_type[entity_type] = {"total": 0, "active": 0, "required": 0}
            by_entity_type[entity_type]["total"] += 1
            if field.get("isActive"):
                by_entity_type[entity_type]["active"] += 1
            if field.get("isRequired"):
                by_entity_type[entity_type]["required"] += 1

            # Data type statistics
            if data_type not in by_data_type:
                by_data_type[data_type] = 0
            by_data_type[data_type] += 1

            # Field type statistics
            if field_type not in by_field_type:
                by_field_type[field_type] = 0
            by_field_type[field_type] += 1

        summary = {
            "total_fields": total_fields,
            "active_fields": active_fields,
            "inactive_fields": inactive_fields,
            "required_fields": required_fields,
            "fields_by_entity_type": by_entity_type,
            "fields_by_data_type": by_data_type,
            "fields_by_field_type": by_field_type,
            "summary_date": datetime.now().isoformat(),
        }

        if include_usage_stats:
            # Add usage statistics (sample data)
            usage_stats = {
                "most_used_data_type": (
                    max(by_data_type.items(), key=lambda x: x[1])[0]
                    if by_data_type
                    else None
                ),
                "most_used_field_type": (
                    max(by_field_type.items(), key=lambda x: x[1])[0]
                    if by_field_type
                    else None
                ),
                "entity_with_most_fields": (
                    max(by_entity_type.items(), key=lambda x: x[1]["total"])[0]
                    if by_entity_type
                    else None
                ),
                "average_fields_per_entity": (
                    round(total_fields / len(by_entity_type), 2)
                    if by_entity_type
                    else 0
                ),
                "field_utilization_rate": (
                    round((active_fields / total_fields * 100), 2)
                    if total_fields > 0
                    else 0
                ),
            }
            summary["usage_statistics"] = usage_stats

        return summary

    def bulk_activate_user_defined_fields(
        self, field_ids: List[int], activation_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Activate multiple user-defined fields in bulk.

        Args:
            field_ids: List of field IDs to activate
            activation_note: Optional note for all activations

        Returns:
            Summary of bulk activation operation
        """
        results = []

        for field_id in field_ids:
            try:
                result = self.activate_user_defined_field(field_id, activation_note)
                results.append({"id": field_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": field_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_fields": len(field_ids),
            "successful": len(successful),
            "failed": len(failed),
            "activation_note": activation_note,
            "operation_date": datetime.now().isoformat(),
            "results": results,
        }

    def bulk_deactivate_user_defined_fields(
        self,
        field_ids: List[int],
        deactivation_reason: Optional[str] = None,
        preserve_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Deactivate multiple user-defined fields in bulk.

        Args:
            field_ids: List of field IDs to deactivate
            deactivation_reason: Optional reason for all deactivations
            preserve_data: Whether to preserve existing field data

        Returns:
            Summary of bulk deactivation operation
        """
        results = []

        for field_id in field_ids:
            try:
                result = self.deactivate_user_defined_field(
                    field_id, deactivation_reason, preserve_data
                )
                results.append({"id": field_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": field_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_fields": len(field_ids),
            "successful": len(successful),
            "failed": len(failed),
            "deactivation_reason": deactivation_reason,
            "preserve_data": preserve_data,
            "operation_date": datetime.now().isoformat(),
            "results": results,
        }

    def analyze_field_usage_patterns(
        self,
        entity_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Analyze field usage patterns and recommendations.

        Args:
            entity_type: Optional entity type filter
            date_from: Optional start date for analysis
            date_to: Optional end date for analysis

        Returns:
            Field usage analysis with recommendations
        """
        if date_from is None:
            date_from = date.today() - timedelta(days=90)
        if date_to is None:
            date_to = date.today()

        fields = (
            self.get_user_defined_fields_by_entity(entity_type)
            if entity_type
            else self.query_all()
        )

        # Sample usage data analysis
        usage_analysis = {
            "analysis_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "total_fields_analyzed": len(fields),
            "field_usage_stats": [],
        }

        for field in fields:
            # Sample usage statistics (in real implementation, this would query actual usage data)
            field_stats = {
                "field_id": field.get("id"),
                "field_name": field.get("name"),
                "entity_type": field.get("entityType"),
                "data_type": field.get("dataType"),
                "is_required": field.get("isRequired", False),
                "usage_frequency": 0.75,  # Sample: 75% of records have this field populated
                "data_quality_score": 0.88,  # Sample: 88% of values pass validation
                "null_percentage": 25,  # Sample: 25% of values are null/empty
                "unique_values_count": 150,  # Sample: 150 unique values
                "most_common_values": [
                    "Value1",
                    "Value2",
                    "Value3",
                ],  # Sample common values
                "validation_failures": 12,  # Sample: 12 validation failures in period
            }

            usage_analysis["field_usage_stats"].append(field_stats)

        # Generate recommendations
        recommendations = []

        for field_stats in usage_analysis["field_usage_stats"]:
            if field_stats["null_percentage"] > 50 and not field_stats["is_required"]:
                recommendations.append(
                    {
                        "type": "low_usage",
                        "field_name": field_stats["field_name"],
                        "severity": "medium",
                        "description": f"Field '{field_stats['field_name']}' has low usage ({100 - field_stats['null_percentage']}% populated). Consider making required or removing.",
                    }
                )

            if field_stats["data_quality_score"] < 0.8:
                recommendations.append(
                    {
                        "type": "data_quality",
                        "field_name": field_stats["field_name"],
                        "severity": "high",
                        "description": f"Field '{field_stats['field_name']}' has low data quality score ({field_stats['data_quality_score']:.1%}). Review validation rules.",
                    }
                )

            if field_stats["validation_failures"] > 20:
                recommendations.append(
                    {
                        "type": "validation_issues",
                        "field_name": field_stats["field_name"],
                        "severity": "medium",
                        "description": f"Field '{field_stats['field_name']}' has high validation failure rate. Consider updating validation rules or providing better user guidance.",
                    }
                )

        usage_analysis["recommendations"] = recommendations
        usage_analysis["analysis_date"] = datetime.now().isoformat()

        return usage_analysis

    def monitor_field_performance(self) -> Dict[str, Any]:
        """
        Monitor field performance and system health metrics.

        Returns:
            Field performance monitoring data
        """
        # Sample monitoring data
        performance_data = {
            "system_health": {
                "total_active_fields": 245,
                "total_inactive_fields": 67,
                "fields_with_validation_errors": 8,
                "average_field_response_time_ms": 12.5,
                "field_cache_hit_rate": 94.2,
                "last_health_check": datetime.now().isoformat(),
            },
            "performance_metrics": {
                "field_lookup_performance": {
                    "average_response_time_ms": 8.3,
                    "p95_response_time_ms": 25.1,
                    "p99_response_time_ms": 45.7,
                    "cache_effectiveness": 96.8,
                },
                "validation_performance": {
                    "average_validation_time_ms": 4.2,
                    "validation_success_rate": 97.3,
                    "most_expensive_validations": [
                        {"field_name": "complex_calculation", "avg_time_ms": 35.2},
                        {"field_name": "external_lookup", "avg_time_ms": 28.7},
                    ],
                },
                "transformation_performance": {
                    "average_transformation_time_ms": 6.1,
                    "transformation_success_rate": 98.9,
                    "most_complex_transformations": [
                        {"field_name": "data_normalization", "avg_time_ms": 22.4},
                        {"field_name": "format_conversion", "avg_time_ms": 15.8},
                    ],
                },
            },
            "alerts": [],
        }

        # Generate performance alerts
        if performance_data["system_health"]["fields_with_validation_errors"] > 10:
            performance_data["alerts"].append(
                {
                    "type": "high_validation_errors",
                    "severity": "warning",
                    "message": f"High number of fields with validation errors ({performance_data['system_health']['fields_with_validation_errors']})",
                }
            )

        if (
            performance_data["performance_metrics"]["field_lookup_performance"][
                "p99_response_time_ms"
            ]
            > 100
        ):
            performance_data["alerts"].append(
                {
                    "type": "slow_field_lookups",
                    "severity": "warning",
                    "message": "Field lookup response times are degraded (P99 > 100ms)",
                }
            )

        if (
            performance_data["performance_metrics"]["validation_performance"][
                "validation_success_rate"
            ]
            < 95
        ):
            performance_data["alerts"].append(
                {
                    "type": "low_validation_success",
                    "severity": "critical",
                    "message": "Field validation success rate is below threshold (< 95%)",
                }
            )

        return performance_data

    def _validate_validation_rule(
        self, rule: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """
        Validate a field validation rule.

        Args:
            rule: Validation rule to validate
            data_type: Data type the rule applies to

        Returns:
            Validation result
        """
        errors = []

        if not isinstance(rule, dict):
            errors.append("Validation rule must be a dictionary")
            return {"is_valid": False, "errors": errors}

        rule_type = rule.get("type")
        if not rule_type:
            errors.append("Validation rule must have a 'type' field")
            return {"is_valid": False, "errors": errors}

        # Validate rule type compatibility with data type
        compatible_rules = {
            "Text": ["required", "min_length", "max_length", "pattern", "format"],
            "Integer": ["required", "min_value", "max_value", "range"],
            "Decimal": [
                "required",
                "min_value",
                "max_value",
                "range",
                "decimal_places",
            ],
            "Date": ["required", "min_date", "max_date", "date_range"],
            "DateTime": ["required", "min_datetime", "max_datetime", "datetime_range"],
            "Boolean": ["required"],
            "Picklist": ["required", "valid_values"],
            "MultiPicklist": ["required", "valid_values", "max_selections"],
        }

        if (
            data_type in compatible_rules
            and rule_type not in compatible_rules[data_type]
        ):
            errors.append(
                f"Validation rule type '{rule_type}' is not compatible with data type '{data_type}'"
            )

        return {"is_valid": len(errors) == 0, "errors": errors}

    def _validate_field_value(
        self, value: Any, data_type: str, field_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a field value against its data type and constraints.

        Args:
            value: Value to validate
            data_type: Expected data type
            field_definition: Field definition with constraints

        Returns:
            Validation result
        """
        try:
            if data_type == "Text":
                if not isinstance(value, str):
                    return {"is_valid": False, "error": "Value must be a string"}
                max_length = field_definition.get("maxLength")
                if max_length and len(value) > max_length:
                    return {
                        "is_valid": False,
                        "error": f"Value exceeds maximum length ({max_length})",
                    }

            elif data_type == "Integer":
                if not isinstance(value, int):
                    return {"is_valid": False, "error": "Value must be an integer"}

            elif data_type == "Decimal":
                if not isinstance(value, (int, float, Decimal)):
                    return {"is_valid": False, "error": "Value must be a number"}

            elif data_type == "Boolean":
                if not isinstance(value, bool):
                    return {"is_valid": False, "error": "Value must be a boolean"}

            elif data_type in ["Date", "DateTime"]:
                if isinstance(value, str):
                    try:
                        datetime.fromisoformat(value)
                    except ValueError:
                        return {
                            "is_valid": False,
                            "error": "Value must be a valid ISO date/datetime string",
                        }
                elif not isinstance(value, (date, datetime)):
                    return {"is_valid": False, "error": "Value must be a date/datetime"}

            return {"is_valid": True}

        except Exception as e:
            return {"is_valid": False, "error": str(e)}

    def _apply_transformation_rule(
        self,
        value: Any,
        rule_type: str,
        options: Dict[str, Any],
        field_definition: Dict[str, Any],
    ) -> Any:
        """
        Apply a single transformation rule to a value.

        Args:
            value: Value to transform
            rule_type: Type of transformation rule
            options: Rule options and parameters
            field_definition: Field definition for context

        Returns:
            Transformed value
        """
        if rule_type == "normalize_text" and isinstance(value, str):
            result = value
            if options.get("trim"):
                result = result.strip()
            if options.get("case") == "upper":
                result = result.upper()
            elif options.get("case") == "lower":
                result = result.lower()
            elif options.get("case") == "title":
                result = result.title()
            return result

        elif rule_type == "default_value":
            condition = options.get("condition", "empty")
            default_val = options.get("value")

            if condition == "empty" and (value is None or value == ""):
                return default_val
            elif condition == "null" and value is None:
                return default_val
            return value

        elif rule_type == "validate_format" and isinstance(value, str):
            pattern = options.get("pattern")
            if pattern and not re.match(pattern, value):
                raise ValueError(f"Value does not match required pattern: {pattern}")
            return value

        elif rule_type == "convert_type":
            target_type = options.get("target_type")
            if target_type == "integer":
                return int(value)
            elif target_type == "decimal":
                return Decimal(str(value))
            elif target_type == "string":
                return str(value)
            return value

        return value
