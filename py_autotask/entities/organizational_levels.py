"""
Organizational Levels entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class OrganizationalLevelsEntity(BaseEntity):
    """
    Handles all Organizational Level-related operations for the Autotask API.

    Organizational levels define hierarchical structures within organizations,
    such as departments, divisions, teams, or business units, enabling
    structured reporting and management within Autotask.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_organizational_level(
        self,
        level_name: str,
        level_type: str,
        parent_level_id: Optional[int] = None,
        description: Optional[str] = None,
        is_active: bool = True,
        level_code: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new organizational level.

        Args:
            level_name: Name of the organizational level
            level_type: Type of level (e.g., 'Department', 'Division', 'Team')
            parent_level_id: ID of parent level for hierarchical organization
            description: Optional description of the level
            is_active: Whether the level is active
            level_code: Optional code for the level
            **kwargs: Additional level fields

        Returns:
            Created organizational level data
        """
        level_data = {
            "LevelName": level_name,
            "LevelType": level_type,
            "IsActive": is_active,
            **kwargs,
        }

        if parent_level_id:
            level_data["ParentLevelID"] = parent_level_id
        if description:
            level_data["Description"] = description
        if level_code:
            level_data["LevelCode"] = level_code

        return self.create(level_data)

    def get_active_levels(self, level_type: Optional[str] = None) -> List[EntityDict]:
        """
        Get all active organizational levels, optionally filtered by type.

        Args:
            level_type: Optional level type filter

        Returns:
            List of active organizational levels
        """
        filters = [{"field": "IsActive", "op": "eq", "value": "true"}]

        if level_type:
            filters.append({"field": "LevelType", "op": "eq", "value": level_type})

        return self.query_all(filters=filters)

    def get_levels_by_type(self, level_type: str) -> List[EntityDict]:
        """
        Get organizational levels by type.

        Args:
            level_type: Level type to filter by

        Returns:
            List of levels of the specified type
        """
        return self.query_all(
            filters={"field": "LevelType", "op": "eq", "value": level_type}
        )

    def get_root_levels(self) -> List[EntityDict]:
        """
        Get root organizational levels (those without parent levels).

        Returns:
            List of root organizational levels
        """
        return self.query_all(
            filters=[
                {"field": "ParentLevelID", "op": "isnull", "value": ""},
                {"field": "IsActive", "op": "eq", "value": "true"},
            ]
        )

    def get_child_levels(
        self, parent_id: int, recursive: bool = False
    ) -> List[EntityDict]:
        """
        Get child levels of a specific parent level.

        Args:
            parent_id: Parent level ID
            recursive: Whether to get all descendants recursively

        Returns:
            List of child organizational levels
        """
        direct_children = self.query_all(
            filters={"field": "ParentLevelID", "op": "eq", "value": parent_id}
        )

        if not recursive:
            return direct_children

        # Get all descendants recursively
        all_descendants = direct_children.copy()
        for child in direct_children:
            child_descendants = self.get_child_levels(child["id"], recursive=True)
            all_descendants.extend(child_descendants)

        return all_descendants

    def get_level_hierarchy_path(self, level_id: int) -> Dict[str, Any]:
        """
        Get the complete hierarchy path for an organizational level.

        Args:
            level_id: Level ID to get hierarchy for

        Returns:
            Dictionary containing level hierarchy information
        """
        hierarchy = []
        current_id = level_id

        while current_id:
            level = self.get(current_id)
            if not level:
                break

            hierarchy.insert(
                0,
                {
                    "id": level["id"],
                    "name": level.get("LevelName", ""),
                    "type": level.get("LevelType", ""),
                    "code": level.get("LevelCode", ""),
                    "description": level.get("Description", ""),
                },
            )

            current_id = level.get("ParentLevelID")

        return {
            "level_id": level_id,
            "hierarchy": hierarchy,
            "full_path": " > ".join([item["name"] for item in hierarchy]),
            "depth": len(hierarchy),
        }

    def search_levels_by_name(self, search_term: str) -> List[EntityDict]:
        """
        Search organizational levels by name.

        Args:
            search_term: Term to search for in level names

        Returns:
            List of matching organizational levels
        """
        return self.query_all(
            filters={"field": "LevelName", "op": "contains", "value": search_term}
        )

    def get_levels_by_code(self, level_code: str) -> List[EntityDict]:
        """
        Get organizational levels by level code.

        Args:
            level_code: Level code to search for

        Returns:
            List of levels with the specified code
        """
        return self.query_all(
            filters={"field": "LevelCode", "op": "eq", "value": level_code}
        )

    def deactivate_level(self, level_id: int, cascade: bool = False) -> Dict[str, Any]:
        """
        Deactivate an organizational level.

        Args:
            level_id: ID of the level to deactivate
            cascade: Whether to also deactivate child levels

        Returns:
            Dictionary with deactivation results
        """
        results = {"deactivated_levels": []}

        # Deactivate the main level
        try:
            updated_level = self.update_by_id(level_id, {"IsActive": False})
            results["deactivated_levels"].append(
                {
                    "id": level_id,
                    "name": updated_level.get("LevelName", ""),
                    "status": "success",
                }
            )
        except Exception as e:
            results["deactivated_levels"].append(
                {"id": level_id, "status": "failed", "error": str(e)}
            )
            return results

        # Cascade to child levels if requested
        if cascade:
            child_levels = self.get_child_levels(level_id, recursive=True)
            for child in child_levels:
                if child.get("IsActive"):
                    try:
                        self.update_by_id(child["id"], {"IsActive": False})
                        results["deactivated_levels"].append(
                            {
                                "id": child["id"],
                                "name": child.get("LevelName", ""),
                                "status": "success",
                            }
                        )
                    except Exception as e:
                        results["deactivated_levels"].append(
                            {
                                "id": child["id"],
                                "name": child.get("LevelName", ""),
                                "status": "failed",
                                "error": str(e),
                            }
                        )

        return results

    def move_level(self, level_id: int, new_parent_id: Optional[int]) -> EntityDict:
        """
        Move an organizational level to a new parent.

        Args:
            level_id: ID of level to move
            new_parent_id: ID of new parent level (None for root)

        Returns:
            Updated level data
        """
        # Validate that we're not creating a circular reference
        if new_parent_id:
            parent_hierarchy = self.get_level_hierarchy_path(new_parent_id)
            if level_id in [level["id"] for level in parent_hierarchy["hierarchy"]]:
                raise ValueError("Cannot move level: would create circular reference")

        return self.update_by_id(level_id, {"ParentLevelID": new_parent_id})

    def get_organization_tree(self, include_inactive: bool = False) -> Dict[str, Any]:
        """
        Get the complete organizational tree structure.

        Args:
            include_inactive: Whether to include inactive levels

        Returns:
            Dictionary representing the organizational tree
        """
        # Get all levels
        if include_inactive:
            all_levels = self.query_all()
        else:
            all_levels = self.get_active_levels()

        # Build tree structure
        level_map = {level["id"]: level for level in all_levels}
        tree = {"root_levels": [], "total_levels": len(all_levels)}

        def build_subtree(level_id):
            level = level_map.get(level_id)
            if not level:
                return None

            node = {
                "id": level["id"],
                "name": level.get("LevelName", ""),
                "type": level.get("LevelType", ""),
                "code": level.get("LevelCode", ""),
                "is_active": level.get("IsActive", False),
                "children": [],
            }

            # Find children
            for potential_child in all_levels:
                if potential_child.get("ParentLevelID") == level_id:
                    child_node = build_subtree(potential_child["id"])
                    if child_node:
                        node["children"].append(child_node)

            return node

        # Build tree starting from root levels
        for level in all_levels:
            if not level.get("ParentLevelID"):
                root_node = build_subtree(level["id"])
                if root_node:
                    tree["root_levels"].append(root_node)

        return tree

    def get_level_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about organizational levels.

        Returns:
            Dictionary containing organizational level statistics
        """
        all_levels = self.query_all()
        active_levels = [level for level in all_levels if level.get("IsActive")]

        # Group by type
        by_type = {}
        for level in active_levels:
            level_type = level.get("LevelType", "unspecified")
            if level_type not in by_type:
                by_type[level_type] = []
            by_type[level_type].append(level)

        # Count root levels and levels with children
        root_levels = [
            level for level in active_levels if not level.get("ParentLevelID")
        ]
        levels_with_children = set()
        for level in active_levels:
            parent_id = level.get("ParentLevelID")
            if parent_id:
                levels_with_children.add(parent_id)

        return {
            "total_levels": len(all_levels),
            "active_levels": len(active_levels),
            "inactive_levels": len(all_levels) - len(active_levels),
            "root_levels": len(root_levels),
            "levels_with_children": len(levels_with_children),
            "leaf_levels": len(active_levels) - len(levels_with_children),
            "levels_by_type": {
                type_name: len(levels) for type_name, levels in by_type.items()
            },
            "available_types": list(by_type.keys()),
            "max_depth": (
                max(
                    [
                        self.get_level_hierarchy_path(level["id"])["depth"]
                        for level in active_levels
                    ]
                )
                if active_levels
                else 0
            ),
        }
