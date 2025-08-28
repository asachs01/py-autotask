"""
Configuration Item Related Items entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemRelatedItemsEntity(BaseEntity):
    """
    Handles all Configuration Item Related Item-related operations for the Autotask API.

    Configuration Item Related Items represent relationships between configuration items,
    enabling the modeling of dependencies, hierarchies, and associations between assets.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ci_relationship(
        self,
        parent_configuration_item_id: int,
        child_configuration_item_id: int,
        relationship_type: str,
        relationship_notes: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item relationship.

        Args:
            parent_configuration_item_id: ID of the parent configuration item
            child_configuration_item_id: ID of the child configuration item
            relationship_type: Type of relationship (e.g., "Depends On", "Connected To", "Part Of")
            relationship_notes: Optional notes about the relationship
            **kwargs: Additional relationship fields

        Returns:
            Created configuration item relationship data
        """
        relationship_data = {
            "ParentConfigurationItemID": parent_configuration_item_id,
            "ChildConfigurationItemID": child_configuration_item_id,
            "RelationshipType": relationship_type,
            **kwargs,
        }

        if relationship_notes:
            relationship_data["RelationshipNotes"] = relationship_notes

        # Validate that parent and child are different
        if parent_configuration_item_id == child_configuration_item_id:
            raise ValueError("Parent and child configuration items cannot be the same")

        return self.create(relationship_data)

    def get_ci_relationships(
        self,
        configuration_item_id: int,
        relationship_type: Optional[str] = None,
        as_parent: bool = True,
        as_child: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            relationship_type: Optional filter by relationship type
            as_parent: Whether to include relationships where CI is the parent
            as_child: Whether to include relationships where CI is the child
            limit: Maximum number of relationships to return

        Returns:
            List of configuration item relationships
        """
        relationships = []

        # Get relationships where CI is the parent
        if as_parent:
            parent_filters = [
                QueryFilter(
                    field="ParentConfigurationItemID",
                    op="eq",
                    value=configuration_item_id,
                )
            ]
            if relationship_type:
                parent_filters.append(
                    QueryFilter(
                        field="RelationshipType", op="eq", value=relationship_type
                    )
                )

            parent_response = self.query(filters=parent_filters)
            parent_relationships = parent_response.items

            # Mark these as parent relationships
            for rel in parent_relationships:
                rel["role"] = "parent"

            relationships.extend(parent_relationships)

        # Get relationships where CI is the child
        if as_child:
            child_filters = [
                QueryFilter(
                    field="ChildConfigurationItemID",
                    op="eq",
                    value=configuration_item_id,
                )
            ]
            if relationship_type:
                child_filters.append(
                    QueryFilter(
                        field="RelationshipType", op="eq", value=relationship_type
                    )
                )

            child_response = self.query(filters=child_filters)
            child_relationships = child_response.items

            # Mark these as child relationships
            for rel in child_relationships:
                rel["role"] = "child"

            relationships.extend(child_relationships)

        # Sort by creation date if available
        relationships.sort(key=lambda x: x.get("CreateDateTime", ""), reverse=True)

        if limit and len(relationships) > limit:
            relationships = relationships[:limit]

        return relationships

    def get_child_relationships(
        self,
        parent_configuration_item_id: int,
        relationship_type: Optional[str] = None,
        recursive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get child relationships for a specific configuration item.

        Args:
            parent_configuration_item_id: ID of the parent configuration item
            relationship_type: Optional filter by relationship type
            recursive: Whether to include all descendants recursively
            limit: Maximum number of relationships to return

        Returns:
            List of child relationships
        """
        filters = [
            QueryFilter(
                field="ParentConfigurationItemID",
                op="eq",
                value=parent_configuration_item_id,
            )
        ]

        if relationship_type:
            filters.append(
                QueryFilter(field="RelationshipType", op="eq", value=relationship_type)
            )

        response = self.query(filters=filters, max_records=limit)
        children = response.items

        if recursive and not limit:  # Avoid infinite recursion with limits
            # Recursively get all descendants
            all_children = children.copy()
            for child in children:
                child_ci_id = child.get("ChildConfigurationItemID")
                if child_ci_id:
                    descendants = self.get_child_relationships(
                        child_ci_id, relationship_type, recursive=True
                    )
                    all_children.extend(descendants)
            return all_children

        return children

    def get_parent_relationships(
        self,
        child_configuration_item_id: int,
        relationship_type: Optional[str] = None,
        recursive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get parent relationships for a specific configuration item.

        Args:
            child_configuration_item_id: ID of the child configuration item
            relationship_type: Optional filter by relationship type
            recursive: Whether to include all ancestors recursively
            limit: Maximum number of relationships to return

        Returns:
            List of parent relationships
        """
        filters = [
            QueryFilter(
                field="ChildConfigurationItemID",
                op="eq",
                value=child_configuration_item_id,
            )
        ]

        if relationship_type:
            filters.append(
                QueryFilter(field="RelationshipType", op="eq", value=relationship_type)
            )

        response = self.query(filters=filters, max_records=limit)
        parents = response.items

        if recursive and not limit:  # Avoid infinite recursion with limits
            # Recursively get all ancestors
            all_parents = parents.copy()
            for parent in parents:
                parent_ci_id = parent.get("ParentConfigurationItemID")
                if parent_ci_id:
                    ancestors = self.get_parent_relationships(
                        parent_ci_id, relationship_type, recursive=True
                    )
                    all_parents.extend(ancestors)
            return all_parents

        return parents

    def get_relationships_by_type(
        self,
        relationship_type: str,
        configuration_item_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get relationships filtered by type.

        Args:
            relationship_type: Relationship type to filter by
            configuration_item_id: Optional filter by specific configuration item
            limit: Maximum number of relationships to return

        Returns:
            List of relationships of the specified type
        """
        filters = [
            QueryFilter(field="RelationshipType", op="eq", value=relationship_type)
        ]

        if configuration_item_id:
            # Include relationships where CI is either parent or child
            parent_filter = QueryFilter(
                field="ParentConfigurationItemID", op="eq", value=configuration_item_id
            )
            child_filter = QueryFilter(
                field="ChildConfigurationItemID", op="eq", value=configuration_item_id
            )

            # This would require OR logic - simplified implementation
            # Get both separately and combine
            parent_relationships = self.query(filters=[parent_filter] + filters).items
            child_relationships = self.query(filters=[child_filter] + filters).items

            all_relationships = parent_relationships + child_relationships

            if limit and len(all_relationships) > limit:
                all_relationships = all_relationships[:limit]

            return all_relationships

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_relationship_notes(
        self, relationship_id: int, new_notes: str
    ) -> Dict[str, Any]:
        """
        Update the notes for a configuration item relationship.

        Args:
            relationship_id: ID of relationship to update
            new_notes: New relationship notes

        Returns:
            Updated relationship data
        """
        return self.update_by_id(relationship_id, {"RelationshipNotes": new_notes})

    def update_relationship_type(
        self, relationship_id: int, new_type: str
    ) -> Dict[str, Any]:
        """
        Update the type of a configuration item relationship.

        Args:
            relationship_id: ID of relationship to update
            new_type: New relationship type

        Returns:
            Updated relationship data
        """
        return self.update_by_id(relationship_id, {"RelationshipType": new_type})

    def remove_relationship(
        self,
        parent_configuration_item_id: int,
        child_configuration_item_id: int,
        relationship_type: Optional[str] = None,
    ) -> bool:
        """
        Remove a specific relationship between two configuration items.

        Args:
            parent_configuration_item_id: ID of the parent configuration item
            child_configuration_item_id: ID of the child configuration item
            relationship_type: Optional relationship type to match

        Returns:
            True if successfully removed
        """
        # Find the relationship
        filters = [
            QueryFilter(
                field="ParentConfigurationItemID",
                op="eq",
                value=parent_configuration_item_id,
            ),
            QueryFilter(
                field="ChildConfigurationItemID",
                op="eq",
                value=child_configuration_item_id,
            ),
        ]

        if relationship_type:
            filters.append(
                QueryFilter(field="RelationshipType", op="eq", value=relationship_type)
            )

        response = self.query(filters=filters)
        relationships = response.items

        if relationships:
            relationship_id = relationships[0].get("id")
            if relationship_id:
                return self.delete(relationship_id)

        return False

    def get_ci_dependency_tree(
        self, configuration_item_id: int, max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Build a dependency tree for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing the dependency tree
        """

        def build_tree(ci_id: int, current_depth: int, visited: set) -> Dict[str, Any]:
            if current_depth > max_depth or ci_id in visited:
                return {
                    "id": ci_id,
                    "children": [],
                    "depth": current_depth,
                    "circular": ci_id in visited,
                }

            visited.add(ci_id)

            # Get CI details
            ci_details = self.client.get("ConfigurationItems", ci_id)

            node = {
                "id": ci_id,
                "name": (
                    ci_details.get("configurationItemName")
                    if ci_details
                    else f"CI {ci_id}"
                ),
                "type": ci_details.get("configurationItemType") if ci_details else None,
                "children": [],
                "depth": current_depth,
                "circular": False,
            }

            # Get child relationships
            child_relationships = self.get_child_relationships(ci_id)

            for relationship in child_relationships:
                child_ci_id = relationship.get("ChildConfigurationItemID")
                if child_ci_id:
                    child_node = build_tree(
                        child_ci_id, current_depth + 1, visited.copy()
                    )
                    child_node["relationship_type"] = relationship.get(
                        "RelationshipType"
                    )
                    child_node["relationship_notes"] = relationship.get(
                        "RelationshipNotes"
                    )
                    node["children"].append(child_node)

            return node

        return build_tree(configuration_item_id, 0, set())

    def get_relationship_summary(self, configuration_item_id: int) -> Dict[str, Any]:
        """
        Get a summary of relationships for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item

        Returns:
            Dictionary with relationship statistics
        """
        relationships = self.get_ci_relationships(configuration_item_id)

        summary = {
            "configuration_item_id": configuration_item_id,
            "total_relationships": len(relationships),
            "as_parent": 0,
            "as_child": 0,
            "by_type": {},
            "unique_related_items": set(),
        }

        for relationship in relationships:
            role = relationship.get("role")
            relationship_type = relationship.get("RelationshipType", "Unknown")

            # Count by role
            if role == "parent":
                summary["as_parent"] += 1
                related_id = relationship.get("ChildConfigurationItemID")
            else:
                summary["as_child"] += 1
                related_id = relationship.get("ParentConfigurationItemID")

            # Count by type
            summary["by_type"][relationship_type] = (
                summary["by_type"].get(relationship_type, 0) + 1
            )

            # Track unique related items
            if related_id:
                summary["unique_related_items"].add(related_id)

        # Convert set to count
        summary["unique_related_items"] = len(summary["unique_related_items"])

        return summary

    def bulk_create_relationships(
        self, relationship_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple configuration item relationships in bulk.

        Args:
            relationship_data: List of relationship dictionaries

        Returns:
            List of created relationship data
        """
        created_relationships = []

        for rel_data in relationship_data:
            try:
                parent_id = rel_data.get("parent_configuration_item_id")
                child_id = rel_data.get("child_configuration_item_id")
                rel_type = rel_data.get("relationship_type")

                if not all([parent_id, child_id, rel_type]):
                    continue

                relationship = self.create_ci_relationship(
                    parent_configuration_item_id=parent_id,
                    child_configuration_item_id=child_id,
                    relationship_type=rel_type,
                    relationship_notes=rel_data.get("relationship_notes"),
                )
                created_relationships.append(relationship)

            except Exception as e:
                # Log error but continue with other relationships
                self.client.logger.error(
                    f"Failed to create relationship {rel_data}: {e}"
                )

        return created_relationships

    def find_circular_dependencies(
        self, configuration_item_id: int, max_depth: int = 10
    ) -> List[List[int]]:
        """
        Find circular dependencies starting from a configuration item.

        Args:
            configuration_item_id: ID of the starting configuration item
            max_depth: Maximum depth to search

        Returns:
            List of circular dependency paths (each path is a list of CI IDs)
        """
        circular_paths = []

        def find_cycles(current_id: int, path: List[int], depth: int):
            if depth > max_depth:
                return

            if current_id in path:
                # Found a cycle
                cycle_start = path.index(current_id)
                circular_paths.append(path[cycle_start:] + [current_id])
                return

            # Add current ID to path
            new_path = path + [current_id]

            # Get child relationships
            child_relationships = self.get_child_relationships(current_id)

            for relationship in child_relationships:
                child_id = relationship.get("ChildConfigurationItemID")
                if child_id:
                    find_cycles(child_id, new_path, depth + 1)

        find_cycles(configuration_item_id, [], 0)
        return circular_paths
