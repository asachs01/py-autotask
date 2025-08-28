"""
Article to Article Associations entity for Autotask API.

This module provides the ArticleToArticleAssociationsEntity class for managing
cross-references and relationships between knowledge base articles.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleToArticleAssociationsEntity(BaseEntity):
    """
    Entity for managing Autotask Article to Article Associations.

    This entity manages cross-references and relationships between knowledge base articles,
    enabling content linking, navigation, and related article suggestions.
    """

    def __init__(self, client, entity_name="ArticleToArticleAssociations"):
        """Initialize the Article to Article Associations entity."""
        super().__init__(client, entity_name)

    def create(self, association_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article-to-article association.

        Args:
            association_data: Dictionary containing association information
                Required fields:
                - sourceArticleId: ID of the source article
                - targetArticleId: ID of the target article
                Optional fields:
                - associationType: Type of association (1=Related, 2=Prerequisites, 3=FollowUp, 4=Alternative)
                - isActive: Whether the association is active
                - isBidirectional: Whether the association works both ways
                - createdDate: Date the association was created
                - createdBy: ID of the user who created the association
                - relevanceScore: How relevant the target is to source (0.0 to 1.0)
                - description: Description of the relationship

        Returns:
            CreateResponse: Response containing created association data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["sourceArticleId", "targetArticleId"]
        self._validate_required_fields(association_data, required_fields)

        # Prevent self-referencing articles
        if association_data["sourceArticleId"] == association_data["targetArticleId"]:
            raise ValueError("Source and target articles cannot be the same")

        # Set default values
        if "associationType" not in association_data:
            association_data["associationType"] = 1  # Related

        if "isActive" not in association_data:
            association_data["isActive"] = True

        if "isBidirectional" not in association_data:
            association_data["isBidirectional"] = False

        if "createdDate" not in association_data:
            association_data["createdDate"] = datetime.now().isoformat()

        if "relevanceScore" not in association_data:
            association_data["relevanceScore"] = 1.0

        return self._create(association_data)

    def get(self, association_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an association by ID.

        Args:
            association_id: The association ID

        Returns:
            Dictionary containing association data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(association_id)

    def update(
        self, association_id: int, update_data: Dict[str, Any]
    ) -> UpdateResponse:
        """
        Update an existing association.

        Args:
            association_id: The association ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated association data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        # Update last modified timestamp
        update_data["lastModifiedDate"] = datetime.now().isoformat()

        return self._update(association_id, update_data)

    def delete(self, association_id: int) -> bool:
        """
        Delete an association.

        Args:
            association_id: The association ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(association_id)

    def get_by_source_article(
        self,
        source_article_id: int,
        association_type: Optional[int] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all associations where the article is the source.

        Args:
            source_article_id: ID of the source article
            association_type: Optional filter by association type
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of associations from the source article
        """
        filters = [
            QueryFilter(field="sourceArticleId", op="eq", value=source_article_id)
        ]

        if association_type is not None:
            filters.append(
                QueryFilter(field="associationType", op="eq", value=association_type)
            )

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        associations = self.query(filters=filters, max_records=limit)

        # Sort by relevance score (highest first)
        return sorted(
            associations, key=lambda x: x.get("relevanceScore", 0), reverse=True
        )

    def get_by_target_article(
        self,
        target_article_id: int,
        association_type: Optional[int] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all associations where the article is the target.

        Args:
            target_article_id: ID of the target article
            association_type: Optional filter by association type
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of associations to the target article
        """
        filters = [
            QueryFilter(field="targetArticleId", op="eq", value=target_article_id)
        ]

        if association_type is not None:
            filters.append(
                QueryFilter(field="associationType", op="eq", value=association_type)
            )

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        associations = self.query(filters=filters, max_records=limit)

        # Sort by relevance score (highest first)
        return sorted(
            associations, key=lambda x: x.get("relevanceScore", 0), reverse=True
        )

    def get_all_related_articles(
        self,
        article_id: int,
        include_bidirectional: bool = True,
        association_type: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all articles related to the given article (both as source and target).

        Args:
            article_id: ID of the article
            include_bidirectional: Whether to include bidirectional associations
            association_type: Optional filter by association type
            limit: Maximum number of associations to return (per direction)

        Returns:
            Dictionary with 'outgoing' and 'incoming' associations
        """
        related_articles = {
            "outgoing": self.get_by_source_article(
                article_id, association_type, limit=limit
            ),
            "incoming": self.get_by_target_article(
                article_id, association_type, limit=limit
            ),
        }

        # If bidirectional associations exist, merge them appropriately
        if include_bidirectional:
            bidirectional_outgoing = [
                assoc
                for assoc in related_articles["outgoing"]
                if assoc.get("isBidirectional", False)
            ]

            # Add bidirectional associations to incoming list with swapped source/target
            for assoc in bidirectional_outgoing:
                bidirectional_copy = assoc.copy()
                bidirectional_copy["sourceArticleId"] = assoc["targetArticleId"]
                bidirectional_copy["targetArticleId"] = assoc["sourceArticleId"]
                related_articles["incoming"].append(bidirectional_copy)

        return related_articles

    def create_association(
        self,
        source_article_id: int,
        target_article_id: int,
        association_type: int = 1,
        relevance_score: float = 1.0,
        is_bidirectional: bool = False,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> CreateResponse:
        """
        Create an association between two articles.

        Args:
            source_article_id: ID of the source article
            target_article_id: ID of the target article
            association_type: Type of association (1=Related, 2=Prerequisites, 3=FollowUp, 4=Alternative)
            relevance_score: Relevance score (0.0 to 1.0)
            is_bidirectional: Whether the association works both ways
            description: Optional description of the relationship
            created_by: ID of the user creating the association

        Returns:
            Created association data

        Raises:
            ValidationError: If the association already exists or is invalid
            AutotaskAPIError: If the creation fails
        """
        # Check for existing association
        existing = self.get_existing_association(source_article_id, target_article_id)
        if existing:
            if existing.get("isActive"):
                raise ValueError(
                    f"Active association already exists between articles {source_article_id} "
                    f"and {target_article_id}"
                )
            else:
                # Reactivate existing association
                return self.update(
                    existing["id"],
                    {
                        "isActive": True,
                        "associationType": association_type,
                        "relevanceScore": max(0.0, min(1.0, relevance_score)),
                        "isBidirectional": is_bidirectional,
                    },
                )

        association_data = {
            "sourceArticleId": source_article_id,
            "targetArticleId": target_article_id,
            "associationType": association_type,
            "relevanceScore": max(0.0, min(1.0, relevance_score)),  # Clamp to 0-1
            "isBidirectional": is_bidirectional,
            "isActive": True,
        }

        if description:
            association_data["description"] = description

        if created_by:
            association_data["createdBy"] = created_by

        return self.create(association_data)

    def create_prerequisite_association(
        self,
        prerequisite_article_id: int,
        main_article_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
    ) -> CreateResponse:
        """
        Create a prerequisite association between articles.

        Args:
            prerequisite_article_id: ID of the prerequisite article
            main_article_id: ID of the main article
            created_by: ID of the user creating the association
            description: Optional description

        Returns:
            Created association data
        """
        return self.create_association(
            source_article_id=prerequisite_article_id,
            target_article_id=main_article_id,
            association_type=2,  # Prerequisites
            relevance_score=1.0,
            is_bidirectional=False,
            description=description or "Prerequisite relationship",
            created_by=created_by,
        )

    def create_follow_up_association(
        self,
        main_article_id: int,
        follow_up_article_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
    ) -> CreateResponse:
        """
        Create a follow-up association between articles.

        Args:
            main_article_id: ID of the main article
            follow_up_article_id: ID of the follow-up article
            created_by: ID of the user creating the association
            description: Optional description

        Returns:
            Created association data
        """
        return self.create_association(
            source_article_id=main_article_id,
            target_article_id=follow_up_article_id,
            association_type=3,  # FollowUp
            relevance_score=1.0,
            is_bidirectional=False,
            description=description or "Follow-up relationship",
            created_by=created_by,
        )

    def get_existing_association(
        self, source_article_id: int, target_article_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing association between two articles.

        Args:
            source_article_id: ID of the source article
            target_article_id: ID of the target article

        Returns:
            Association data if found, None otherwise
        """
        filters = [
            QueryFilter(field="sourceArticleId", op="eq", value=source_article_id),
            QueryFilter(field="targetArticleId", op="eq", value=target_article_id),
        ]

        associations = self.query(filters=filters, max_records=1)
        return associations[0] if associations else None

    def remove_association(
        self, source_article_id: int, target_article_id: int, soft_delete: bool = True
    ) -> bool:
        """
        Remove association between two articles.

        Args:
            source_article_id: ID of the source article
            target_article_id: ID of the target article
            soft_delete: If True, mark as inactive; if False, hard delete

        Returns:
            True if removal was successful

        Raises:
            ValueError: If association doesn't exist
            AutotaskAPIError: If the removal fails
        """
        association = self.get_existing_association(
            source_article_id, target_article_id
        )
        if not association:
            raise ValueError(
                f"No association found between articles {source_article_id} and {target_article_id}"
            )

        if soft_delete:
            self.update(association["id"], {"isActive": False})
            return True
        else:
            return self.delete(association["id"])

    def bulk_create_associations(
        self,
        source_article_id: int,
        association_data: List[Dict[str, Any]],
        replace_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Create multiple associations from a source article.

        Args:
            source_article_id: ID of the source article
            association_data: List of association dictionaries with keys:
                             - target_article_id: ID of target article
                             - association_type: Optional type (default: 1)
                             - relevance_score: Optional score (default: 1.0)
                             - is_bidirectional: Optional (default: False)
                             - description: Optional description
            replace_existing: If True, remove existing associations first

        Returns:
            Dictionary with association results
        """
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
            "total_requested": len(association_data),
        }

        if replace_existing:
            # Remove existing associations
            existing_associations = self.get_by_source_article(
                source_article_id, include_inactive=False
            )
            for assoc in existing_associations:
                try:
                    self.update(assoc["id"], {"isActive": False})
                except Exception as e:
                    self.logger.warning(
                        f"Failed to deactivate association {assoc['id']}: {e}"
                    )

        for assoc_info in association_data:
            target_article_id = assoc_info.get("target_article_id")
            association_type = assoc_info.get("association_type", 1)
            relevance_score = assoc_info.get("relevance_score", 1.0)
            is_bidirectional = assoc_info.get("is_bidirectional", False)
            description = assoc_info.get("description")

            try:
                association = self.create_association(
                    source_article_id,
                    target_article_id,
                    association_type,
                    relevance_score,
                    is_bidirectional,
                    description,
                )
                results["created"].append(
                    {
                        "target_article_id": target_article_id,
                        "association_id": association.get("item_id"),
                    }
                )
            except ValueError as e:
                if "already exists" in str(e):
                    results["skipped"].append(
                        {
                            "target_article_id": target_article_id,
                            "reason": "Association already exists",
                        }
                    )
                else:
                    results["errors"].append(
                        {"target_article_id": target_article_id, "error": str(e)}
                    )
            except Exception as e:
                results["errors"].append(
                    {"target_article_id": target_article_id, "error": str(e)}
                )

        return results

    def get_article_network(
        self,
        article_id: int,
        max_depth: int = 2,
        association_types: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Get the network of articles connected to the given article.

        Args:
            article_id: ID of the root article
            max_depth: Maximum depth to traverse
            association_types: Optional list of association types to include

        Returns:
            Dictionary representing the article network
        """
        visited = set()
        network = {
            "root_article_id": article_id,
            "nodes": {},
            "edges": [],
            "depth_levels": {},
        }

        def traverse_article(current_id, current_depth):
            if current_depth > max_depth or current_id in visited:
                return

            visited.add(current_id)

            if current_depth not in network["depth_levels"]:
                network["depth_levels"][current_depth] = []
            network["depth_levels"][current_depth].append(current_id)

            network["nodes"][current_id] = {
                "article_id": current_id,
                "depth": current_depth,
                "outgoing_connections": 0,
                "incoming_connections": 0,
            }

            # Get outgoing associations
            outgoing_filters = [
                QueryFilter(field="sourceArticleId", op="eq", value=current_id),
                QueryFilter(field="isActive", op="eq", value=True),
            ]

            if association_types:
                outgoing_filters.append(
                    QueryFilter(
                        field="associationType", op="in", value=association_types
                    )
                )

            outgoing = self.query(filters=outgoing_filters)

            for assoc in outgoing:
                target_id = assoc.get("targetArticleId")
                edge = {
                    "source": current_id,
                    "target": target_id,
                    "association_type": assoc.get("associationType"),
                    "relevance_score": assoc.get("relevanceScore"),
                    "is_bidirectional": assoc.get("isBidirectional", False),
                }
                network["edges"].append(edge)
                network["nodes"][current_id]["outgoing_connections"] += 1

                if current_depth < max_depth:
                    traverse_article(target_id, current_depth + 1)

            # Get incoming associations (for completeness at current level)
            if current_depth < max_depth:
                incoming_filters = [
                    QueryFilter(field="targetArticleId", op="eq", value=current_id),
                    QueryFilter(field="isActive", op="eq", value=True),
                ]

                if association_types:
                    incoming_filters.append(
                        QueryFilter(
                            field="associationType", op="in", value=association_types
                        )
                    )

                incoming = self.query(filters=incoming_filters)

                for assoc in incoming:
                    source_id = assoc.get("sourceArticleId")
                    if source_id not in visited:
                        traverse_article(source_id, current_depth + 1)

        traverse_article(article_id, 0)

        # Calculate network statistics
        network["statistics"] = {
            "total_nodes": len(network["nodes"]),
            "total_edges": len(network["edges"]),
            "max_depth_reached": (
                max(network["depth_levels"].keys()) if network["depth_levels"] else 0
            ),
            "avg_connections_per_node": (
                sum(
                    node["outgoing_connections"] + node["incoming_connections"]
                    for node in network["nodes"].values()
                )
                / len(network["nodes"])
                if network["nodes"]
                else 0
            ),
        }

        return network

    def find_circular_references(self, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Find circular references in article associations.

        Args:
            max_depth: Maximum depth to check for circular references

        Returns:
            List of circular reference chains found
        """
        # Get all active associations
        filters = [QueryFilter(field="isActive", op="eq", value=True)]
        all_associations = self.query(filters=filters)

        # Build adjacency graph
        graph = {}
        for assoc in all_associations:
            source = assoc.get("sourceArticleId")
            target = assoc.get("targetArticleId")

            if source not in graph:
                graph[source] = []
            graph[source].append(
                {
                    "target": target,
                    "association_id": assoc.get("id"),
                    "association_type": assoc.get("associationType"),
                }
            )

        circular_refs = []

        def find_cycles(node, path, depth):
            if depth > max_depth:
                return

            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                circular_refs.append(
                    {"cycle": cycle, "length": len(cycle) - 1, "associations": []}
                )
                return

            if node in graph:
                new_path = path + [node]
                for edge in graph[node]:
                    find_cycles(edge["target"], new_path, depth + 1)

        # Check each article as a starting point
        for article_id in graph.keys():
            find_cycles(article_id, [], 0)

        # Remove duplicates (same cycle from different starting points)
        unique_cycles = []
        seen_cycles = set()

        for cycle_info in circular_refs:
            cycle = cycle_info["cycle"]
            # Normalize cycle to start with smallest ID
            min_idx = cycle[:-1].index(min(cycle[:-1]))
            normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
            cycle_key = tuple(normalized)

            if cycle_key not in seen_cycles:
                seen_cycles.add(cycle_key)
                cycle_info["normalized_cycle"] = normalized
                unique_cycles.append(cycle_info)

        return unique_cycles

    def get_association_statistics(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about article-to-article associations.

        Args:
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            Dictionary with association statistics
        """
        filters = [QueryFilter(field="isActive", op="eq", value=True)]

        if date_range:
            start_date, end_date = date_range
            filters.extend(
                [
                    QueryFilter(field="createdDate", op="gte", value=start_date),
                    QueryFilter(field="createdDate", op="lte", value=end_date),
                ]
            )

        associations = self.query(filters=filters)

        stats = {
            "total_associations": len(associations),
            "unique_source_articles": len(
                set(assoc.get("sourceArticleId") for assoc in associations)
            ),
            "unique_target_articles": len(
                set(assoc.get("targetArticleId") for assoc in associations)
            ),
            "by_type": {
                "related": 0,  # Type 1
                "prerequisites": 0,  # Type 2
                "follow_up": 0,  # Type 3
                "alternative": 0,  # Type 4
            },
            "bidirectional_count": 0,
            "avg_relevance": 0.0,
            "top_source_articles": {},
            "top_target_articles": {},
            "relevance_distribution": {
                "high": 0,  # >= 0.8
                "medium": 0,  # 0.4 - 0.8
                "low": 0,  # < 0.4
            },
        }

        relevance_scores = []

        for association in associations:
            source_id = association.get("sourceArticleId")
            target_id = association.get("targetArticleId")
            association_type = association.get("associationType", 1)
            relevance = association.get("relevanceScore", 1.0)
            is_bidirectional = association.get("isBidirectional", False)

            # Count by type
            if association_type == 1:
                stats["by_type"]["related"] += 1
            elif association_type == 2:
                stats["by_type"]["prerequisites"] += 1
            elif association_type == 3:
                stats["by_type"]["follow_up"] += 1
            elif association_type == 4:
                stats["by_type"]["alternative"] += 1

            # Bidirectional count
            if is_bidirectional:
                stats["bidirectional_count"] += 1

            # Top articles
            stats["top_source_articles"][source_id] = (
                stats["top_source_articles"].get(source_id, 0) + 1
            )
            stats["top_target_articles"][target_id] = (
                stats["top_target_articles"].get(target_id, 0) + 1
            )

            # Relevance distribution
            if relevance >= 0.8:
                stats["relevance_distribution"]["high"] += 1
            elif relevance >= 0.4:
                stats["relevance_distribution"]["medium"] += 1
            else:
                stats["relevance_distribution"]["low"] += 1

            relevance_scores.append(relevance)

        # Calculate average relevance
        if relevance_scores:
            stats["avg_relevance"] = sum(relevance_scores) / len(relevance_scores)

        # Sort top articles
        stats["top_source_articles"] = sorted(
            stats["top_source_articles"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        stats["top_target_articles"] = sorted(
            stats["top_target_articles"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        return stats
