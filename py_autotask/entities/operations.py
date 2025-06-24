"""
Operations Entity for py-autotask

This module provides the OperationsEntity class for managing operations
in Autotask. Operations represent business processes, workflows, and
operational procedures for service delivery and management.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class OperationsEntity(BaseEntity):
    """
    Manages Autotask Operations - workflow and process management.

    Operations represent business processes, workflows, and operational
    procedures within Autotask. They support process automation,
    workflow management, and operational efficiency tracking.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Operations"

    def create_operation(
        self,
        name: str,
        operation_type: str,
        description: Optional[str] = None,
        owner_resource_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new operation.

        Args:
            name: Name of the operation
            operation_type: Type of operation (Workflow, Process, etc.)
            description: Description of the operation
            owner_resource_id: ID of the operation owner/manager
            **kwargs: Additional fields for the operation

        Returns:
            Create response with new operation ID
        """
        operation_data = {"name": name, "operationType": operation_type, **kwargs}

        if description:
            operation_data["description"] = description
        if owner_resource_id:
            operation_data["ownerResourceID"] = owner_resource_id

        return self.create(operation_data)

    def get_active_operations(
        self, operation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active operations.

        Args:
            operation_type: Optional operation type to filter by

        Returns:
            List of active operations
        """
        filters = ["isActive eq true"]

        if operation_type:
            filters.append(f"operationType eq '{operation_type}'")

        return self.query(filter=" and ".join(filters))

    def get_operations_by_owner(self, owner_resource_id: int) -> List[Dict[str, Any]]:
        """
        Get operations owned by a specific resource.

        Args:
            owner_resource_id: ID of the operation owner

        Returns:
            List of operations owned by the resource
        """
        return self.query(filter=f"ownerResourceID eq {owner_resource_id}")

    def get_operation_performance(
        self, operation_id: int, date_from: date, date_to: date
    ) -> Dict[str, Any]:
        """
        Get performance metrics for an operation.

        Args:
            operation_id: ID of the operation
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Operation performance metrics
        """
        # This would typically analyze operation execution data
        # For now, return structure that could be populated

        return {
            "operation_id": operation_id,
            "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "performance": {
                "total_executions": 0,  # Would count executions
                "successful_executions": 0,  # Would count successes
                "failed_executions": 0,  # Would count failures
                "average_execution_time": 0.0,  # Would calculate avg time
                "efficiency_score": 0.0,  # Would calculate efficiency
            },
        }
