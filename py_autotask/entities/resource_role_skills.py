"""
Resource Role Skills entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class ResourceRoleSkillsEntity(BaseEntity):
    """
    Handles all Resource Role Skill-related operations for the Autotask API.

    Resource role skills define the skill requirements and proficiency levels
    for different resource roles, enabling skill-based resource allocation
    and competency management.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_role_skill_requirement(
        self,
        resource_role_id: int,
        skill_id: int,
        required_proficiency_level: int = 1,
        is_required: bool = True,
        weight: Optional[float] = None,
        **kwargs,
    ) -> EntityDict:
        """Create a new role skill requirement."""
        skill_data = {
            "ResourceRoleID": resource_role_id,
            "SkillID": skill_id,
            "RequiredProficiencyLevel": required_proficiency_level,
            "IsRequired": is_required,
            **kwargs,
        }

        if weight is not None:
            skill_data["Weight"] = weight

        return self.create(skill_data)

    def get_skills_for_role(
        self, resource_role_id: int, required_only: bool = False
    ) -> List[EntityDict]:
        """Get all skills required for a specific role."""
        filters = [{"field": "ResourceRoleID", "op": "eq", "value": resource_role_id}]

        if required_only:
            filters.append({"field": "IsRequired", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_roles_for_skill(
        self, skill_id: int, min_proficiency_level: Optional[int] = None
    ) -> List[EntityDict]:
        """Get all roles that require a specific skill."""
        filters = [{"field": "SkillID", "op": "eq", "value": skill_id}]

        if min_proficiency_level is not None:
            filters.append(
                {
                    "field": "RequiredProficiencyLevel",
                    "op": "gte",
                    "value": min_proficiency_level,
                }
            )

        return self.query_all(filters=filters)

    def update_skill_requirement(
        self,
        resource_role_id: int,
        skill_id: int,
        new_proficiency_level: Optional[int] = None,
        is_required: Optional[bool] = None,
        weight: Optional[float] = None,
    ) -> EntityDict:
        """Update skill requirement for a role."""
        existing_requirements = self.query_all(
            filters=[
                {"field": "ResourceRoleID", "op": "eq", "value": resource_role_id},
                {"field": "SkillID", "op": "eq", "value": skill_id},
            ]
        )

        if not existing_requirements:
            raise ValueError(
                f"No skill requirement found for role {resource_role_id} and skill {skill_id}"
            )

        update_data = {}
        if new_proficiency_level is not None:
            update_data["RequiredProficiencyLevel"] = new_proficiency_level
        if is_required is not None:
            update_data["IsRequired"] = is_required
        if weight is not None:
            update_data["Weight"] = weight

        return self.update_by_id(existing_requirements[0]["id"], update_data)

    def get_role_skill_profile(self, resource_role_id: int) -> Dict[str, Any]:
        """Get complete skill profile for a role."""
        skills = self.get_skills_for_role(resource_role_id)

        profile = {
            "resource_role_id": resource_role_id,
            "total_skills": len(skills),
            "required_skills": len([s for s in skills if s.get("IsRequired")]),
            "optional_skills": len([s for s in skills if not s.get("IsRequired")]),
            "skill_breakdown": {},
            "proficiency_distribution": {},
        }

        # Group by proficiency level
        for skill in skills:
            proficiency = skill.get("RequiredProficiencyLevel", 1)
            if proficiency not in profile["proficiency_distribution"]:
                profile["proficiency_distribution"][proficiency] = 0
            profile["proficiency_distribution"][proficiency] += 1

        # Calculate skill weights if available
        weighted_skills = [s for s in skills if s.get("Weight") is not None]
        if weighted_skills:
            total_weight = sum(s.get("Weight", 0) for s in weighted_skills)
            profile["total_weight"] = total_weight
            profile["avg_skill_weight"] = total_weight / len(weighted_skills)

        return profile

    def compare_role_skill_requirements(
        self, role_id_1: int, role_id_2: int
    ) -> Dict[str, Any]:
        """Compare skill requirements between two roles."""
        role_1_skills = self.get_skills_for_role(role_id_1)
        role_2_skills = self.get_skills_for_role(role_id_2)

        role_1_skill_ids = set(s.get("SkillID") for s in role_1_skills)
        role_2_skill_ids = set(s.get("SkillID") for s in role_2_skills)

        common_skills = role_1_skill_ids.intersection(role_2_skill_ids)
        role_1_unique = role_1_skill_ids - role_2_skill_ids
        role_2_unique = role_2_skill_ids - role_1_skill_ids

        # Compare proficiency levels for common skills
        proficiency_differences = []
        for skill_id in common_skills:
            role_1_skill = next(
                s for s in role_1_skills if s.get("SkillID") == skill_id
            )
            role_2_skill = next(
                s for s in role_2_skills if s.get("SkillID") == skill_id
            )

            level_1 = role_1_skill.get("RequiredProficiencyLevel", 1)
            level_2 = role_2_skill.get("RequiredProficiencyLevel", 1)

            if level_1 != level_2:
                proficiency_differences.append(
                    {
                        "skill_id": skill_id,
                        "role_1_level": level_1,
                        "role_2_level": level_2,
                        "difference": level_1 - level_2,
                    }
                )

        return {
            "role_1_id": role_id_1,
            "role_2_id": role_id_2,
            "role_1_total_skills": len(role_1_skills),
            "role_2_total_skills": len(role_2_skills),
            "common_skills": len(common_skills),
            "role_1_unique_skills": len(role_1_unique),
            "role_2_unique_skills": len(role_2_unique),
            "skill_overlap_percentage": (
                len(common_skills)
                / max(len(role_1_skill_ids), len(role_2_skill_ids))
                * 100
                if (role_1_skill_ids or role_2_skill_ids)
                else 0
            ),
            "proficiency_differences": proficiency_differences,
        }

    def bulk_update_skill_requirements(
        self,
        resource_role_id: int,
        skill_updates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Update multiple skill requirements for a role."""
        results = []

        for update in skill_updates:
            skill_id = update["skill_id"]

            try:
                updated = self.update_skill_requirement(
                    resource_role_id=resource_role_id,
                    skill_id=skill_id,
                    new_proficiency_level=update.get("proficiency_level"),
                    is_required=update.get("is_required"),
                    weight=update.get("weight"),
                )
                results.append(
                    {"skill_id": skill_id, "status": "success", "updated_data": updated}
                )
            except Exception as e:
                results.append(
                    {"skill_id": skill_id, "status": "failed", "error": str(e)}
                )

        return results

    def remove_skill_requirement(self, resource_role_id: int, skill_id: int) -> bool:
        """Remove a skill requirement from a role."""
        existing_requirements = self.query_all(
            filters=[
                {"field": "ResourceRoleID", "op": "eq", "value": resource_role_id},
                {"field": "SkillID", "op": "eq", "value": skill_id},
            ]
        )

        if not existing_requirements:
            return False

        return self.delete(existing_requirements[0]["id"])

    def get_skill_demand_analysis(self, skill_id: int) -> Dict[str, Any]:
        """Analyze demand for a specific skill across roles."""
        role_requirements = self.get_roles_for_skill(skill_id)

        if not role_requirements:
            return {
                "skill_id": skill_id,
                "total_roles_requiring": 0,
                "demand_analysis": None,
            }

        required_roles = [r for r in role_requirements if r.get("IsRequired")]
        proficiency_levels = [
            r.get("RequiredProficiencyLevel", 1) for r in role_requirements
        ]

        return {
            "skill_id": skill_id,
            "total_roles_requiring": len(role_requirements),
            "roles_requiring_mandatory": len(required_roles),
            "roles_requiring_optional": len(role_requirements) - len(required_roles),
            "proficiency_demand": {
                "min_level_required": min(proficiency_levels),
                "max_level_required": max(proficiency_levels),
                "avg_level_required": sum(proficiency_levels) / len(proficiency_levels),
                "level_distribution": {
                    level: proficiency_levels.count(level)
                    for level in set(proficiency_levels)
                },
            },
        }

    def clone_role_skills(
        self,
        source_role_id: int,
        target_role_id: int,
        proficiency_adjustment: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Clone skill requirements from one role to another."""
        source_skills = self.get_skills_for_role(source_role_id)

        results = {
            "source_role_id": source_role_id,
            "target_role_id": target_role_id,
            "total_skills": len(source_skills),
            "successful_copies": 0,
            "failed_copies": 0,
        }

        for skill in source_skills:
            skill_id = skill.get("SkillID")
            proficiency_level = skill.get("RequiredProficiencyLevel", 1)

            # Apply proficiency adjustment if specified
            if proficiency_adjustment:
                proficiency_level = max(1, proficiency_level + proficiency_adjustment)

            try:
                self.create_role_skill_requirement(
                    resource_role_id=target_role_id,
                    skill_id=skill_id,
                    required_proficiency_level=proficiency_level,
                    is_required=skill.get("IsRequired", True),
                    weight=skill.get("Weight"),
                )
                results["successful_copies"] += 1
            except Exception:
                results["failed_copies"] += 1

        return results
