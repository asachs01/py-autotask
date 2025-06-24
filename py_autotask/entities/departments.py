"""
Departments Entity for py-autotask

This module provides the DepartmentsEntity class for managing departments
in Autotask. Departments represent organizational units for structuring
resources and managing workflow organization.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class DepartmentsEntity(BaseEntity):
    """
    Manages Autotask Departments - organizational department structures.

    Departments represent organizational units within Autotask for structuring
    resources, managing workflows, and organizing business operations. They
    support hierarchical organization and resource assignment.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "Departments"

    def create_department(
        self,
        name: str,
        description: Optional[str] = None,
        parent_department_id: Optional[int] = None,
        department_lead_resource_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new department.

        Args:
            name: Name of the department
            description: Description of the department
            parent_department_id: ID of parent department for hierarchy
            department_lead_resource_id: ID of the department lead resource
            **kwargs: Additional fields for the department

        Returns:
            Create response with new department ID
        """
        department_data = {"name": name, **kwargs}

        if description:
            department_data["description"] = description
        if parent_department_id:
            department_data["parentDepartmentID"] = parent_department_id
        if department_lead_resource_id:
            department_data["departmentLeadResourceID"] = department_lead_resource_id

        return self.create(department_data)

    def get_department_hierarchy(
        self, parent_department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get department hierarchy starting from a parent department.

        Args:
            parent_department_id: ID of parent department (None for root level)

        Returns:
            List of departments in hierarchy
        """
        if parent_department_id is None:
            filters = ["parentDepartmentID eq null"]
        else:
            filters = [f"parentDepartmentID eq {parent_department_id}"]

        return self.query(filter=" and ".join(filters))

    def get_root_departments(self) -> List[Dict[str, Any]]:
        """
        Get all root-level departments (no parent).

        Returns:
            List of root departments
        """
        return self.query(filter="parentDepartmentID eq null")

    def get_department_tree(
        self, department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get complete department tree structure.

        Args:
            department_id: Root department ID (None for full tree)

        Returns:
            Nested department tree structure
        """

        def build_tree(parent_id: Optional[int]) -> List[Dict[str, Any]]:
            children = self.get_department_hierarchy(parent_id)
            tree = []

            for child in children:
                child_id = child.get("id")
                child["children"] = build_tree(child_id)
                tree.append(child)

            return tree

        if department_id:
            department = self.get(department_id)
            department["children"] = build_tree(department_id)
            return department
        else:
            return {
                "departments": build_tree(None),
                "total_departments": len(self.query()),
            }

    def get_departments_by_lead(self, lead_resource_id: int) -> List[Dict[str, Any]]:
        """
        Get departments led by a specific resource.

        Args:
            lead_resource_id: ID of the department lead resource

        Returns:
            List of departments led by the resource
        """
        return self.query(filter=f"departmentLeadResourceID eq {lead_resource_id}")

    def search_departments(
        self, search_term: str, search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search departments by name or description.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (defaults to name and description)

        Returns:
            List of matching departments
        """
        if search_fields is None:
            search_fields = ["name", "description"]

        filters = []
        for field in search_fields:
            filters.append(f"contains({field}, '{search_term}')")

        return self.query(filter=" or ".join(filters))

    def get_department_resources(
        self, department_id: int, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get resources assigned to a department.

        Args:
            department_id: ID of the department
            include_inactive: Whether to include inactive resources

        Returns:
            List of resources in the department
        """
        # This would typically query the Resources entity
        # For now, return placeholder structure

        return []  # Would be populated with actual resource query

    def assign_resource_to_department(
        self, resource_id: int, department_id: int
    ) -> Dict[str, Any]:
        """
        Assign a resource to a department.

        Args:
            resource_id: ID of the resource
            department_id: ID of the department

        Returns:
            Assignment result
        """
        # This would typically update the resource's department
        # For now, return placeholder structure

        return {
            "resource_id": resource_id,
            "department_id": department_id,
            "assigned_date": datetime.now().isoformat(),
            "success": True,
        }

    def get_department_summary(self, department_id: int) -> Dict[str, Any]:
        """
        Get comprehensive summary for a department.

        Args:
            department_id: ID of the department

        Returns:
            Department summary with related data
        """
        department = self.get(department_id)

        # This would typically query related entities
        # For now, return structure with placeholder data

        return {
            "department": department,
            "summary": {
                "department_id": department_id,
                "total_resources": 0,  # Would query resources
                "active_resources": 0,  # Would query active resources
                "child_departments": len(self.get_department_hierarchy(department_id)),
                "open_tickets": 0,  # Would query tickets
                "active_projects": 0,  # Would query projects
                "total_time_entries": 0,  # Would query time entries
            },
        }

    def update_department_lead(
        self, department_id: int, new_lead_resource_id: int
    ) -> Dict[str, Any]:
        """
        Update department lead resource.

        Args:
            department_id: ID of the department
            new_lead_resource_id: ID of the new lead resource

        Returns:
            Update response
        """
        return self.update(
            department_id, {"departmentLeadResourceID": new_lead_resource_id}
        )

    def move_department(
        self, department_id: int, new_parent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Move department to a new parent (or make it root level).

        Args:
            department_id: ID of the department to move
            new_parent_id: ID of new parent department (None for root level)

        Returns:
            Update response
        """
        update_data = {}

        if new_parent_id is None:
            update_data["parentDepartmentID"] = None
        else:
            update_data["parentDepartmentID"] = new_parent_id

        return self.update(department_id, update_data)

    def get_department_path(self, department_id: int) -> List[Dict[str, Any]]:
        """
        Get the full path from root to the specified department.

        Args:
            department_id: ID of the department

        Returns:
            List of departments from root to specified department
        """
        path = []
        current_dept = self.get(department_id)

        while current_dept:
            path.insert(0, current_dept)
            parent_id = current_dept.get("parentDepartmentID")
            if parent_id:
                current_dept = self.get(parent_id)
            else:
                break

        return path

    def bulk_move_departments(
        self, department_moves: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Move multiple departments to new parents.

        Args:
            department_moves: List of moves
                Each should contain: department_id, new_parent_id

        Returns:
            Summary of bulk move operation
        """
        results = []

        for move in department_moves:
            department_id = move["department_id"]
            new_parent_id = move.get("new_parent_id")

            try:
                result = self.move_department(department_id, new_parent_id)
                results.append({"id": department_id, "success": True, "result": result})
            except Exception as e:
                results.append({"id": department_id, "success": False, "error": str(e)})

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_moves": len(department_moves),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_department_workload_summary(
        self,
        department_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get workload summary for a department.

        Args:
            department_id: ID of the department
            date_from: Start date for workload analysis
            date_to: End date for workload analysis

        Returns:
            Department workload summary
        """
        # This would typically query related workload data
        # For now, return structure that could be populated

        return {
            "department_id": department_id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "workload_summary": {
                "total_hours": Decimal("0"),  # Would calculate from time entries
                "billable_hours": Decimal("0"),  # Would calculate billable time
                "utilization_rate": 0.0,  # Would calculate utilization
                "active_tickets": 0,  # Would count tickets
                "active_projects": 0,  # Would count projects
                "resource_count": 0,  # Would count resources
            },
        }
