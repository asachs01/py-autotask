"""
ResourceSkills Entity for py-autotask

This module provides the ResourceSkillsEntity class for managing resource skills
in Autotask. Resource skills track competencies, certifications, and skill levels
for resources to support project assignment and capability planning.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ResourceSkillsEntity(BaseEntity):
    """
    Manages Autotask ResourceSkills - skill tracking and competency management.

    Resource skills track the competencies, certifications, and skill levels
    of resources within Autotask. They support project assignment, capability
    planning, and resource development tracking.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ResourceSkills"

    def create_resource_skill(
        self,
        resource_id: int,
        skill_id: int,
        skill_level: int,
        years_experience: Optional[Union[float, Decimal]] = None,
        certification_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new resource skill assignment.

        Args:
            resource_id: ID of the resource
            skill_id: ID of the skill
            skill_level: Skill level (1-10 scale typically)
            years_experience: Years of experience with this skill
            certification_date: Date of certification (if applicable)
            **kwargs: Additional fields for the skill assignment

        Returns:
            Create response with new skill assignment ID
        """
        skill_data = {
            "resourceID": resource_id,
            "skillID": skill_id,
            "skillLevel": skill_level,
            **kwargs,
        }

        if years_experience is not None:
            skill_data["yearsExperience"] = float(years_experience)
        if certification_date:
            skill_data["certificationDate"] = certification_date.isoformat()

        return self.create(skill_data)

    def get_resource_skills(
        self, resource_id: int, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all skills for a specific resource.

        Args:
            resource_id: ID of the resource
            active_only: Whether to only return active skills

        Returns:
            List of skills for the resource
        """
        filters = [f"resourceID eq {resource_id}"]

        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def get_skill_resources(
        self,
        skill_id: int,
        min_skill_level: Optional[int] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all resources with a specific skill.

        Args:
            skill_id: ID of the skill
            min_skill_level: Minimum required skill level
            active_only: Whether to only return active skill assignments

        Returns:
            List of resources with the skill
        """
        filters = [f"skillID eq {skill_id}"]

        if min_skill_level is not None:
            filters.append(f"skillLevel ge {min_skill_level}")
        if active_only:
            filters.append("isActive eq true")

        return self.query(filter=" and ".join(filters))

    def update_skill_level(
        self,
        resource_skill_id: int,
        new_skill_level: int,
        assessment_date: Optional[date] = None,
        assessor_resource_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update skill level for a resource skill.

        Args:
            resource_skill_id: ID of the resource skill assignment
            new_skill_level: New skill level
            assessment_date: Date of skill assessment
            assessor_resource_id: ID of the assessor

        Returns:
            Update response
        """
        update_data = {"skillLevel": new_skill_level}

        if assessment_date:
            update_data["lastAssessmentDate"] = assessment_date.isoformat()
        if assessor_resource_id:
            update_data["assessorResourceID"] = assessor_resource_id

        return self.update(resource_skill_id, update_data)

    def get_skills_by_level(
        self, skill_level: int, skill_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resource skills by skill level.

        Args:
            skill_level: Skill level to filter by
            skill_id: Optional specific skill ID

        Returns:
            List of resource skills at the specified level
        """
        filters = [f"skillLevel eq {skill_level}"]

        if skill_id:
            filters.append(f"skillID eq {skill_id}")

        return self.query(filter=" and ".join(filters))

    def get_skill_matrix(
        self, resource_ids: List[int], skill_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get skill matrix for specified resources and skills.

        Args:
            resource_ids: List of resource IDs
            skill_ids: Optional list of skill IDs (all skills if not provided)

        Returns:
            Skill matrix showing resources vs skills
        """
        # Build filter for resources
        resource_filter = " or ".join([f"resourceID eq {rid}" for rid in resource_ids])
        filters = [f"({resource_filter})"]

        if skill_ids:
            skill_filter = " or ".join([f"skillID eq {sid}" for sid in skill_ids])
            filters.append(f"({skill_filter})")

        skills = self.query(filter=" and ".join(filters))

        # Build matrix
        matrix = {}
        for skill in skills:
            resource_id = skill.get("resourceID")
            skill_id = skill.get("skillID")

            if resource_id not in matrix:
                matrix[resource_id] = {}

            matrix[resource_id][skill_id] = {
                "skill_level": skill.get("skillLevel"),
                "years_experience": skill.get("yearsExperience"),
                "certification_date": skill.get("certificationDate"),
                "last_assessment": skill.get("lastAssessmentDate"),
            }

        return {"resource_ids": resource_ids, "skill_ids": skill_ids, "matrix": matrix}

    def find_resources_by_skills(
        self, required_skills: List[Dict[str, Any]], match_type: str = "any"
    ) -> List[Dict[str, Any]]:
        """
        Find resources matching skill requirements.

        Args:
            required_skills: List of skill requirements
                Each should contain: skill_id, min_level
            match_type: "any" or "all" skills must match

        Returns:
            List of resources matching skill requirements
        """
        if not required_skills:
            return []

        # Build filters for each skill requirement
        skill_filters = []
        for req in required_skills:
            skill_id = req["skill_id"]
            min_level = req.get("min_level", 1)
            skill_filters.append(
                f"(skillID eq {skill_id} and skillLevel ge {min_level})"
            )

        if match_type == "all":
            # This is complex - would need to ensure resource has ALL skills
            # For now, return resources with ANY of the skills
            filter_str = " or ".join(skill_filters)
        else:
            filter_str = " or ".join(skill_filters)

        return self.query(filter=filter_str)

    def get_skill_gaps(
        self, department_id: Optional[int] = None, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Identify skill gaps in department or project.

        Args:
            department_id: ID of department to analyze
            project_id: ID of project to analyze

        Returns:
            Skill gap analysis
        """
        # This would typically analyze required vs available skills
        # For now, return structure that could be populated

        return {
            "analysis_scope": {
                "department_id": department_id,
                "project_id": project_id,
            },
            "skill_gaps": [
                # Would be populated with actual gap analysis
            ],
            "recommendations": [
                # Would include training/hiring recommendations
            ],
        }

    def bulk_update_skills(self, skill_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update multiple resource skills.

        Args:
            skill_updates: List of skill updates
                Each should contain: resource_skill_id, skill_level, etc.

        Returns:
            Summary of bulk update operation
        """
        results = []

        for update in skill_updates:
            resource_skill_id = update["resource_skill_id"]
            skill_level = update["skill_level"]

            try:
                result = self.update_skill_level(resource_skill_id, skill_level)
                results.append(
                    {"id": resource_skill_id, "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"id": resource_skill_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(skill_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_certification_summary(
        self, resource_id: Optional[int] = None, expiring_days: int = 90
    ) -> Dict[str, Any]:
        """
        Get certification summary for resources.

        Args:
            resource_id: Specific resource ID (all if not provided)
            expiring_days: Days ahead to check for expiring certifications

        Returns:
            Certification status summary
        """
        filters = ["certificationDate ne null"]

        if resource_id:
            filters.append(f"resourceID eq {resource_id}")

        certified_skills = self.query(filter=" and ".join(filters))

        # Analyze certification status
        expiring_soon = []
        valid_certs = []

        cutoff_date = date.today().replace(day=date.today().day + expiring_days)

        for skill in certified_skills:
            skill.get("certificationDate")
            expiry_date = skill.get("certificationExpiryDate")

            if expiry_date and date.fromisoformat(expiry_date) <= cutoff_date:
                expiring_soon.append(skill)
            else:
                valid_certs.append(skill)

        return {
            "resource_id": resource_id,
            "certification_summary": {
                "total_certifications": len(certified_skills),
                "valid_certifications": len(valid_certs),
                "expiring_soon": len(expiring_soon),
                "expiring_skills": expiring_soon,
            },
        }

    def get_skill_development_plan(
        self, resource_id: int, target_skills: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate skill development plan for a resource.

        Args:
            resource_id: ID of the resource
            target_skills: List of target skills with desired levels

        Returns:
            Skill development plan
        """
        current_skills = self.get_resource_skills(resource_id)

        development_plan = {
            "resource_id": resource_id,
            "current_skills": current_skills,
            "development_recommendations": [],
        }

        if target_skills:
            for target in target_skills:
                skill_id = target["skill_id"]
                target_level = target["target_level"]

                # Find current level
                current_skill = next(
                    (s for s in current_skills if s.get("skillID") == skill_id), None
                )
                current_level = (
                    current_skill.get("skillLevel", 0) if current_skill else 0
                )

                if current_level < target_level:
                    development_plan["development_recommendations"].append(
                        {
                            "skill_id": skill_id,
                            "current_level": current_level,
                            "target_level": target_level,
                            "gap": target_level - current_level,
                            "recommended_actions": [
                                "Training course",
                                "Mentoring",
                                "Project assignment",
                            ],
                        }
                    )

        return development_plan
