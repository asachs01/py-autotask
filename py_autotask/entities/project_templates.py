"""
Project Templates entity for Autotask API operations.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity

logger = logging.getLogger(__name__)


class ProjectTemplatesEntity(BaseEntity):
    """
    Handles all Project Template-related operations for the Autotask API.

    Project templates enable standardized project creation with predefined
    phases, tasks, milestones, and resource allocations.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_project_template(
        self,
        name: str,
        description: Optional[str] = None,
        project_type: int = 1,  # 1 = Fixed Price
        is_active: bool = True,
        estimated_hours: Optional[float] = None,
        estimated_cost: Optional[Decimal] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new project template.

        Args:
            name: Name of the project template
            description: Description of the template
            project_type: Type of project (1=Fixed Price, 2=Time & Materials, etc.)
            is_active: Whether the template is active
            estimated_hours: Estimated total hours for projects using this template
            estimated_cost: Estimated total cost for projects using this template
            **kwargs: Additional template fields

        Returns:
            Created project template data

        Example:
            template = client.project_templates.create_project_template(
                "Website Development Template",
                description="Standard template for website development projects",
                estimated_hours=320.0,
                estimated_cost=Decimal('25000.00')
            )
        """
        template_data = {
            "Name": name,
            "ProjectType": project_type,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            template_data["Description"] = description
        if estimated_hours is not None:
            template_data["EstimatedHours"] = estimated_hours
        if estimated_cost is not None:
            template_data["EstimatedCost"] = str(estimated_cost)

        return self.create(template_data)

    def get_active_project_templates(
        self, project_type: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all active project templates.

        Args:
            project_type: Optional project type filter
            limit: Maximum number of templates to return

        Returns:
            List of active project templates

        Example:
            templates = client.project_templates.get_active_project_templates()
        """
        filters = [{"field": "IsActive", "op": "eq", "value": True}]

        if project_type:
            filters.append({"field": "ProjectType", "op": "eq", "value": project_type})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_template_phases(self, template_id: int) -> List[EntityDict]:
        """
        Get all phases for a specific project template.

        Args:
            template_id: ID of the project template

        Returns:
            List of template phases

        Example:
            phases = client.project_templates.get_template_phases(12345)
        """
        filters = [{"field": "ProjectTemplateID", "op": "eq", "value": template_id}]

        # Query project template phases entity
        response = self.client.query("ProjectTemplatePhases", filters)
        return response.items if hasattr(response, "items") else response

    def get_template_tasks(self, template_id: int) -> List[EntityDict]:
        """
        Get all tasks for a specific project template.

        Args:
            template_id: ID of the project template

        Returns:
            List of template tasks

        Example:
            tasks = client.project_templates.get_template_tasks(12345)
        """
        filters = [{"field": "ProjectTemplateID", "op": "eq", "value": template_id}]

        # Query project template tasks entity
        response = self.client.query("ProjectTemplateTasks", filters)
        return response.items if hasattr(response, "items") else response

    def instantiate_project_from_template(
        self,
        template_id: int,
        project_name: str,
        account_id: int,
        start_date: Optional[str] = None,
        project_manager_id: Optional[int] = None,
        **project_kwargs,
    ) -> EntityDict:
        """
        Create a new project from a template.

        Args:
            template_id: ID of the template to use
            project_name: Name for the new project
            account_id: Account ID for the new project
            start_date: Start date for the new project (ISO format)
            project_manager_id: Optional project manager resource ID
            **project_kwargs: Additional project fields

        Returns:
            Created project data

        Example:
            project = client.project_templates.instantiate_project_from_template(
                12345,
                "ACME Corp Website",
                67890,
                start_date="2024-01-15",
                project_manager_id=100
            )
        """
        template = self.get(template_id)
        if not template:
            raise ValueError(f"Project template {template_id} not found")

        # Create project from template
        project_data = {
            "ProjectName": project_name,
            "AccountID": account_id,
            "Type": template.get("ProjectType", 1),
            "Description": template.get("Description"),
            "EstimatedHours": template.get("EstimatedHours"),
            "EstimatedCost": template.get("EstimatedCost"),
            "TemplateID": template_id,
            **project_kwargs,
        }

        if start_date:
            project_data["StartDate"] = start_date
        if project_manager_id:
            project_data["ProjectManagerResourceID"] = project_manager_id

        # Create the project
        new_project = self.client.create_entity("Projects", project_data)
        new_project_id = new_project.get("item_id") or new_project.get("id")

        if new_project_id:
            # Create phases from template
            self._create_phases_from_template(template_id, new_project_id, start_date)

            # Create tasks from template
            self._create_tasks_from_template(template_id, new_project_id, start_date)

        return new_project

    def activate_project_template(self, template_id: int) -> EntityDict:
        """
        Activate a project template.

        Args:
            template_id: ID of template to activate

        Returns:
            Updated template data

        Example:
            activated = client.project_templates.activate_project_template(12345)
        """
        return self.update_by_id(template_id, {"IsActive": True})

    def deactivate_project_template(self, template_id: int) -> EntityDict:
        """
        Deactivate a project template.

        Args:
            template_id: ID of template to deactivate

        Returns:
            Updated template data

        Example:
            deactivated = client.project_templates.deactivate_project_template(12345)
        """
        return self.update_by_id(template_id, {"IsActive": False})

    def clone_project_template(
        self,
        template_id: int,
        new_name: str,
        copy_phases: bool = True,
        copy_tasks: bool = True,
    ) -> EntityDict:
        """
        Clone a project template with its phases and tasks.

        Args:
            template_id: ID of template to clone
            new_name: Name for the cloned template
            copy_phases: Whether to copy template phases
            copy_tasks: Whether to copy template tasks

        Returns:
            Created cloned template data

        Example:
            cloned = client.project_templates.clone_project_template(
                12345, "Advanced Website Development Template"
            )
        """
        original = self.get(template_id)
        if not original:
            raise ValueError(f"Project template {template_id} not found")

        # Create new template
        clone_data = {
            "Name": new_name,
            "Description": original.get("Description"),
            "ProjectType": original.get("ProjectType"),
            "EstimatedHours": original.get("EstimatedHours"),
            "EstimatedCost": original.get("EstimatedCost"),
            "IsActive": True,
        }

        new_template = self.create(clone_data)
        new_template_id = new_template.get("item_id") or new_template.get("id")

        # Copy phases if requested
        if copy_phases and new_template_id:
            phases = self.get_template_phases(template_id)
            for phase in phases:
                phase_data = {
                    "ProjectTemplateID": new_template_id,
                    "Name": phase.get("Name"),
                    "Description": phase.get("Description"),
                    "EstimatedHours": phase.get("EstimatedHours"),
                    "Order": phase.get("Order"),
                }

                try:
                    self.client.create_entity("ProjectTemplatePhases", phase_data)
                except Exception as e:
                    self.logger.error(f"Failed to copy phase {phase.get('Name')}: {e}")

        # Copy tasks if requested
        if copy_tasks and new_template_id:
            tasks = self.get_template_tasks(template_id)
            for task in tasks:
                task_data = {
                    "ProjectTemplateID": new_template_id,
                    "Title": task.get("Title"),
                    "Description": task.get("Description"),
                    "EstimatedHours": task.get("EstimatedHours"),
                    "PhaseID": task.get("PhaseID"),
                    "Order": task.get("Order"),
                }

                try:
                    self.client.create_entity("ProjectTemplateTasks", task_data)
                except Exception as e:
                    self.logger.error(f"Failed to copy task {task.get('Title')}: {e}")

        return new_template

    def get_project_template_summary(self, template_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a project template.

        Args:
            template_id: ID of the project template

        Returns:
            Template summary with statistics

        Example:
            summary = client.project_templates.get_project_template_summary(12345)
        """
        template = self.get(template_id)
        if not template:
            return {}

        phases = self.get_template_phases(template_id)
        tasks = self.get_template_tasks(template_id)

        # Calculate statistics
        total_estimated_hours = sum(
            float(task.get("EstimatedHours", 0)) for task in tasks
        )
        phase_count = len(phases)
        task_count = len(tasks)

        # Get usage statistics (projects created from this template)
        usage_filters = [{"field": "TemplateID", "op": "eq", "value": template_id}]
        try:
            usage_response = self.client.query("Projects", usage_filters)
            usage_count = len(
                usage_response.items
                if hasattr(usage_response, "items")
                else usage_response
            )
        except Exception:
            usage_count = 0

        return {
            "template_id": template_id,
            "name": template.get("Name"),
            "description": template.get("Description"),
            "project_type": template.get("ProjectType"),
            "is_active": template.get("IsActive"),
            "estimated_hours": template.get("EstimatedHours", 0),
            "estimated_cost": template.get("EstimatedCost"),
            "phase_count": phase_count,
            "task_count": task_count,
            "calculated_hours": total_estimated_hours,
            "projects_created": usage_count,
            "created_date": template.get("CreateDate"),
            "last_modified_date": template.get("LastModifiedDate"),
        }

    def get_templates_by_type(
        self, project_type: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get project templates by project type.

        Args:
            project_type: Project type to filter by
            active_only: Whether to return only active templates
            limit: Maximum number of templates to return

        Returns:
            List of templates for the project type

        Example:
            fixed_price_templates = client.project_templates.get_templates_by_type(1)
        """
        filters = [{"field": "ProjectType", "op": "eq", "value": project_type}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def search_project_templates(
        self, name_pattern: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search project templates by name pattern.

        Args:
            name_pattern: Pattern to search for in template names
            active_only: Whether to return only active templates
            limit: Maximum number of templates to return

        Returns:
            List of matching project templates

        Example:
            web_templates = client.project_templates.search_project_templates("website")
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]

        if active_only:
            filters.append({"field": "IsActive", "op": "eq", "value": True})

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_project_template(self, template_id: int) -> Dict[str, Any]:
        """
        Validate a project template for completeness.

        Args:
            template_id: ID of the template to validate

        Returns:
            Validation results with warnings and recommendations

        Example:
            validation = client.project_templates.validate_project_template(12345)
        """
        template = self.get(template_id)
        if not template:
            return {"error": f"Project template {template_id} not found"}

        phases = self.get_template_phases(template_id)
        tasks = self.get_template_tasks(template_id)
        warnings = []
        recommendations = []

        # Check for phases
        if not phases:
            warnings.append("No phases defined in this template")
            recommendations.append("Add phases to structure the project")

        # Check for tasks
        if not tasks:
            warnings.append("No tasks defined in this template")
            recommendations.append("Add tasks to define project deliverables")

        # Check estimates
        if not template.get("EstimatedHours"):
            warnings.append("No estimated hours defined")
            recommendations.append("Set estimated hours for better project planning")

        if not template.get("EstimatedCost"):
            warnings.append("No estimated cost defined")
            recommendations.append("Set estimated cost for budget planning")

        # Check task estimates
        tasks_without_estimates = [t for t in tasks if not t.get("EstimatedHours")]
        if tasks_without_estimates:
            warnings.append(
                f"{len(tasks_without_estimates)} tasks without hour estimates"
            )
            recommendations.append("Add hour estimates to all tasks")

        return {
            "template_id": template_id,
            "is_valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": recommendations,
            "phase_count": len(phases),
            "task_count": len(tasks),
            "tasks_without_estimates": len(tasks_without_estimates),
        }

    def bulk_activate_templates(
        self, template_ids: List[int], batch_size: int = 20
    ) -> List[EntityDict]:
        """
        Activate multiple project templates in batches.

        Args:
            template_ids: List of template IDs to activate
            batch_size: Number of templates to process per batch

        Returns:
            List of updated template data

        Example:
            activated = client.project_templates.bulk_activate_templates([12345, 12346])
        """
        results = []

        for i in range(0, len(template_ids), batch_size):
            batch = template_ids[i : i + batch_size]

            for template_id in batch:
                try:
                    result = self.activate_project_template(template_id)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to activate template {template_id}: {e}")
                    continue

        return results

    def get_template_usage_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for all project templates.

        Returns:
            Usage statistics showing template popularity

        Example:
            stats = client.project_templates.get_template_usage_statistics()
        """
        all_templates = self.query_all()
        usage_stats = {}

        for template in all_templates:
            template_id = template.get("id")
            template_name = template.get("Name")

            if template_id:
                # Count projects created from this template
                usage_filters = [
                    {"field": "TemplateID", "op": "eq", "value": template_id}
                ]
                try:
                    usage_response = self.client.query("Projects", usage_filters)
                    usage_count = len(
                        usage_response.items
                        if hasattr(usage_response, "items")
                        else usage_response
                    )
                    usage_stats[template_name] = usage_count
                except Exception:
                    usage_stats[template_name] = 0

        # Calculate statistics
        total_usage = sum(usage_stats.values())
        most_used = (
            max(usage_stats.items(), key=lambda x: x[1]) if usage_stats else ("None", 0)
        )
        least_used = (
            min(usage_stats.items(), key=lambda x: x[1]) if usage_stats else ("None", 0)
        )

        return {
            "total_templates": len(all_templates),
            "active_templates": len([t for t in all_templates if t.get("IsActive")]),
            "total_projects_created": total_usage,
            "average_usage_per_template": (
                round(total_usage / len(all_templates), 2) if all_templates else 0
            ),
            "most_used_template": {"name": most_used[0], "usage_count": most_used[1]},
            "least_used_template": {
                "name": least_used[0],
                "usage_count": least_used[1],
            },
            "template_usage_details": usage_stats,
        }

    def _create_phases_from_template(
        self, template_id: int, project_id: int, start_date: Optional[str] = None
    ) -> None:
        """
        Create project phases from template phases.

        Args:
            template_id: ID of the template
            project_id: ID of the new project
            start_date: Start date for phase scheduling
        """
        phases = self.get_template_phases(template_id)

        for phase in phases:
            phase_data = {
                "ProjectID": project_id,
                "Name": phase.get("Name"),
                "Description": phase.get("Description"),
                "EstimatedHours": phase.get("EstimatedHours"),
            }

            # TODO: Calculate phase dates based on start_date and dependencies
            if start_date:
                phase_data["StartDate"] = start_date

            try:
                self.client.create_entity("ProjectPhases", phase_data)
            except Exception as e:
                self.logger.error(f"Failed to create phase {phase.get('Name')}: {e}")

    def _create_tasks_from_template(
        self, template_id: int, project_id: int, start_date: Optional[str] = None
    ) -> None:
        """
        Create project tasks from template tasks.

        Args:
            template_id: ID of the template
            project_id: ID of the new project
            start_date: Start date for task scheduling
        """
        tasks = self.get_template_tasks(template_id)

        for task in tasks:
            task_data = {
                "ProjectID": project_id,
                "Title": task.get("Title"),
                "Description": task.get("Description"),
                "EstimatedHours": task.get("EstimatedHours"),
                "Status": 1,  # New status
            }

            # TODO: Map template phase to actual project phase
            # TODO: Calculate task dates based on start_date and dependencies

            try:
                self.client.create_entity("Tasks", task_data)
            except Exception as e:
                self.logger.error(f"Failed to create task {task.get('Title')}: {e}")
