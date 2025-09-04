"""
Article Tag Associations entity for Autotask API.

This module provides the ArticleTagAssociationsEntity class for managing
tag associations with knowledge base articles for categorization and search.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleTagAssociationsEntity(BaseEntity):
    """
    Entity for managing Autotask Article Tag Associations.

    This entity manages the relationships between knowledge base articles
    and tags, enabling content categorization, filtering, and improved search.
    """

    def __init__(self, client, entity_name="ArticleTagAssociations"):
        """Initialize the Article Tag Associations entity."""
        super().__init__(client, entity_name)

    def create(self, association_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article-tag association.

        Args:
            association_data: Dictionary containing association information
                Required fields:
                - articleId: ID of the article
                - tagId: ID of the tag, or
                - tagName: Name of the tag (if tag doesn't exist, it may be created)
                Optional fields:
                - isActive: Whether the association is active
                - createdDate: Date the association was created
                - createdBy: ID of the user who created the association
                - relevanceScore: Relevance score for the tag (0.0 to 1.0)

        Returns:
            CreateResponse: Response containing created association data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        # Validate that either tagId or tagName is provided
        if not association_data.get("tagId") and not association_data.get("tagName"):
            raise ValueError("Either tagId or tagName must be provided")

        if not association_data.get("articleId"):
            raise ValueError("articleId is required")

        # Set default values
        if "isActive" not in association_data:
            association_data["isActive"] = True

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

    def get_by_article(
        self,
        article_id: int,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all tag associations for a specific article.

        Args:
            article_id: ID of the article
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of tag associations for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        associations = self.query(filters=filters, max_records=limit)

        # Sort by relevance score (highest first)
        return sorted(
            associations, key=lambda x: x.get("relevanceScore", 0), reverse=True
        )

    def get_by_tag(
        self, tag_id: int, include_inactive: bool = False, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all article associations for a specific tag.

        Args:
            tag_id: ID of the tag
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of article associations for the tag
        """
        filters = [QueryFilter(field="tagId", op="eq", value=tag_id)]

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_by_tag_name(
        self, tag_name: str, include_inactive: bool = False, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all article associations for a specific tag name.

        Args:
            tag_name: Name of the tag
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of article associations for the tag
        """
        filters = [QueryFilter(field="tagName", op="eq", value=tag_name)]

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def add_tag_to_article(
        self,
        article_id: int,
        tag_identifier: str,
        relevance_score: float = 1.0,
        created_by: Optional[int] = None,
        is_tag_id: bool = False,
    ) -> CreateResponse:
        """
        Add a tag to an article.

        Args:
            article_id: ID of the article
            tag_identifier: Tag ID (if is_tag_id=True) or tag name
            relevance_score: Relevance score for the tag (0.0 to 1.0)
            created_by: ID of the user creating the association
            is_tag_id: Whether tag_identifier is a tag ID or name

        Returns:
            Created association data

        Raises:
            ValidationError: If the association already exists
            AutotaskAPIError: If the creation fails
        """
        # Check for existing association
        if is_tag_id:
            existing = self.get_existing_association(
                article_id, tag_id=int(tag_identifier)
            )
            tag_field = "tagId"
            tag_value = int(tag_identifier)
        else:
            existing = self.get_existing_association(
                article_id, tag_name=tag_identifier
            )
            tag_field = "tagName"
            tag_value = tag_identifier

        if existing:
            if existing.get("isActive"):
                raise ValueError(
                    f"Active tag association already exists for article {article_id}"
                )
            else:
                # Reactivate existing association
                return self.update(
                    existing["id"],
                    {"isActive": True, "relevanceScore": relevance_score},
                )

        association_data = {
            "articleId": article_id,
            tag_field: tag_value,
            "relevanceScore": max(0.0, min(1.0, relevance_score)),  # Clamp to 0-1
            "isActive": True,
        }

        if created_by:
            association_data["createdBy"] = created_by

        return self.create(association_data)

    def remove_tag_from_article(
        self,
        article_id: int,
        tag_identifier: str,
        is_tag_id: bool = False,
        soft_delete: bool = True,
    ) -> bool:
        """
        Remove a tag from an article.

        Args:
            article_id: ID of the article
            tag_identifier: Tag ID (if is_tag_id=True) or tag name
            is_tag_id: Whether tag_identifier is a tag ID or name
            soft_delete: If True, mark as inactive; if False, hard delete

        Returns:
            True if removal was successful

        Raises:
            ValueError: If association doesn't exist
            AutotaskAPIError: If the removal fails
        """
        if is_tag_id:
            association = self.get_existing_association(
                article_id, tag_id=int(tag_identifier)
            )
        else:
            association = self.get_existing_association(
                article_id, tag_name=tag_identifier
            )

        if not association:
            raise ValueError(f"No tag association found for article {article_id}")

        if soft_delete:
            self.update(association["id"], {"isActive": False})
            return True
        else:
            return self.delete(association["id"])

    def get_existing_association(
        self,
        article_id: int,
        tag_id: Optional[int] = None,
        tag_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing association between article and tag.

        Args:
            article_id: ID of the article
            tag_id: Optional ID of the tag
            tag_name: Optional name of the tag

        Returns:
            Association data if found, None otherwise
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if tag_id:
            filters.append(QueryFilter(field="tagId", op="eq", value=tag_id))
        elif tag_name:
            filters.append(QueryFilter(field="tagName", op="eq", value=tag_name))
        else:
            raise ValueError("Either tag_id or tag_name must be provided")

        associations = self.query(filters=filters, max_records=1)
        return associations[0] if associations else None

    def bulk_tag_article(
        self,
        article_id: int,
        tag_data: List[Dict[str, Any]],
        replace_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Associate multiple tags with an article.

        Args:
            article_id: ID of the article
            tag_data: List of tag data dictionaries with keys:
                      - tag_identifier: Tag ID or name
                      - is_tag_id: Whether identifier is ID (default: False)
                      - relevance_score: Optional relevance score (default: 1.0)
            replace_existing: If True, remove existing associations first

        Returns:
            Dictionary with tagging results
        """
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
            "total_requested": len(tag_data),
        }

        if replace_existing:
            # Remove existing associations
            existing_associations = self.get_by_article(
                article_id, include_inactive=False
            )
            for assoc in existing_associations:
                try:
                    self.update(assoc["id"], {"isActive": False})
                except Exception as e:
                    self.logger.warning(
                        f"Failed to deactivate association {assoc['id']}: {e}"
                    )

        for tag_info in tag_data:
            tag_identifier = tag_info.get("tag_identifier")
            is_tag_id = tag_info.get("is_tag_id", False)
            relevance_score = tag_info.get("relevance_score", 1.0)

            try:
                association = self.add_tag_to_article(
                    article_id, tag_identifier, relevance_score, is_tag_id=is_tag_id
                )
                results["created"].append(
                    {
                        "tag_identifier": tag_identifier,
                        "association_id": association.get("item_id"),
                    }
                )
            except ValueError as e:
                if "already exists" in str(e):
                    results["skipped"].append(
                        {
                            "tag_identifier": tag_identifier,
                            "reason": "Association already exists",
                        }
                    )
                else:
                    results["errors"].append(
                        {"tag_identifier": tag_identifier, "error": str(e)}
                    )
            except Exception as e:
                results["errors"].append(
                    {"tag_identifier": tag_identifier, "error": str(e)}
                )

        return results

    def get_article_tags(
        self,
        article_id: int,
        min_relevance_score: float = 0.0,
        include_details: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get all tags associated with an article.

        Args:
            article_id: ID of the article
            min_relevance_score: Minimum relevance score filter
            include_details: Whether to include association details

        Returns:
            List of tags with optional details
        """
        filters = [
            QueryFilter(field="articleId", op="eq", value=article_id),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        if min_relevance_score > 0.0:
            filters.append(
                QueryFilter(field="relevanceScore", op="gte", value=min_relevance_score)
            )

        associations = self.query(filters=filters)

        if not include_details:
            return [
                {"tag_id": assoc.get("tagId"), "tag_name": assoc.get("tagName")}
                for assoc in associations
            ]

        # Sort by relevance score (highest first)
        return sorted(
            associations, key=lambda x: x.get("relevanceScore", 0), reverse=True
        )

    def get_popular_tags(
        self,
        limit: Optional[int] = 20,
        min_articles: int = 2,
        time_period_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get most popular tags across articles.

        Args:
            limit: Maximum number of tags to return
            min_articles: Minimum number of articles a tag must be associated with
            time_period_days: Optional time period filter in days

        Returns:
            List of popular tags with usage counts
        """
        filters = [QueryFilter(field="isActive", op="eq", value=True)]

        if time_period_days:
            cutoff_date = datetime.now() - datetime.timedelta(days=time_period_days)
            filters.append(
                QueryFilter(
                    field="createdDate", op="gte", value=cutoff_date.isoformat()
                )
            )

        associations = self.query(filters=filters)

        # Count tag usage
        tag_counts = {}
        for assoc in associations:
            tag_id = assoc.get("tagId")
            tag_name = assoc.get("tagName", f"Tag {tag_id}")

            if tag_id not in tag_counts:
                tag_counts[tag_id] = {
                    "tag_id": tag_id,
                    "tag_name": tag_name,
                    "article_count": 0,
                    "total_relevance": 0.0,
                    "avg_relevance": 0.0,
                }

            tag_counts[tag_id]["article_count"] += 1
            tag_counts[tag_id]["total_relevance"] += assoc.get("relevanceScore", 1.0)

        # Filter by minimum articles and calculate averages
        popular_tags = []
        for tag_data in tag_counts.values():
            if tag_data["article_count"] >= min_articles:
                tag_data["avg_relevance"] = (
                    tag_data["total_relevance"] / tag_data["article_count"]
                )
                popular_tags.append(tag_data)

        # Sort by article count (descending) then by average relevance
        popular_tags.sort(
            key=lambda x: (x["article_count"], x["avg_relevance"]), reverse=True
        )

        return popular_tags[:limit] if limit else popular_tags

    def find_related_articles(
        self, article_id: int, min_shared_tags: int = 1, limit: Optional[int] = 10
    ) -> List[Dict[str, Any]]:
        """
        Find articles related by shared tags.

        Args:
            article_id: ID of the source article
            min_shared_tags: Minimum number of shared tags
            limit: Maximum number of related articles to return

        Returns:
            List of related articles with shared tag counts
        """
        # Get tags for the source article
        source_tags = self.get_by_article(article_id, include_inactive=False)
        source_tag_ids = [
            assoc.get("tagId") for assoc in source_tags if assoc.get("tagId")
        ]

        if not source_tag_ids:
            return []

        # Find articles with shared tags
        filters = [
            QueryFilter(field="tagId", op="in", value=source_tag_ids),
            QueryFilter(
                field="articleId", op="neq", value=article_id
            ),  # Exclude source article
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        related_associations = self.query(filters=filters)

        # Count shared tags per article
        article_tag_counts = {}
        for assoc in related_associations:
            related_article_id = assoc.get("articleId")
            if related_article_id not in article_tag_counts:
                article_tag_counts[related_article_id] = {
                    "article_id": related_article_id,
                    "shared_tags": 0,
                    "shared_tag_ids": [],
                    "relevance_sum": 0.0,
                }

            article_tag_counts[related_article_id]["shared_tags"] += 1
            article_tag_counts[related_article_id]["shared_tag_ids"].append(
                assoc.get("tagId")
            )
            article_tag_counts[related_article_id]["relevance_sum"] += assoc.get(
                "relevanceScore", 1.0
            )

        # Filter by minimum shared tags and calculate average relevance
        related_articles = []
        for article_data in article_tag_counts.values():
            if article_data["shared_tags"] >= min_shared_tags:
                article_data["avg_relevance"] = (
                    article_data["relevance_sum"] / article_data["shared_tags"]
                )
                related_articles.append(article_data)

        # Sort by shared tags count (descending) then by average relevance
        related_articles.sort(
            key=lambda x: (x["shared_tags"], x["avg_relevance"]), reverse=True
        )

        return related_articles[:limit] if limit else related_articles

    def get_tag_statistics(self, tag_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Get statistics about tag associations.

        Args:
            tag_ids: Optional list of tag IDs to analyze

        Returns:
            Dictionary with tag association statistics
        """
        filters = [QueryFilter(field="isActive", op="eq", value=True)]

        if tag_ids:
            filters.append(QueryFilter(field="tagId", op="in", value=tag_ids))

        associations = self.query(filters=filters)

        stats = {
            "total_associations": len(associations),
            "unique_articles": len(
                set(assoc.get("articleId") for assoc in associations)
            ),
            "unique_tags": len(
                set(assoc.get("tagId") for assoc in associations if assoc.get("tagId"))
            ),
            "by_tag": {},
            "by_article": {},
            "relevance_distribution": {
                "high": 0,  # >= 0.8
                "medium": 0,  # 0.4 - 0.8
                "low": 0,  # < 0.4
            },
            "avg_relevance": 0.0,
            "avg_tags_per_article": 0.0,
        }

        relevance_scores = []

        for association in associations:
            tag_id = association.get("tagId")
            article_id = association.get("articleId")
            relevance = association.get("relevanceScore", 1.0)

            # Count by tag
            stats["by_tag"][tag_id] = stats["by_tag"].get(tag_id, 0) + 1

            # Count by article
            stats["by_article"][article_id] = stats["by_article"].get(article_id, 0) + 1

            # Relevance distribution
            if relevance >= 0.8:
                stats["relevance_distribution"]["high"] += 1
            elif relevance >= 0.4:
                stats["relevance_distribution"]["medium"] += 1
            else:
                stats["relevance_distribution"]["low"] += 1

            relevance_scores.append(relevance)

        # Calculate averages
        if relevance_scores:
            stats["avg_relevance"] = sum(relevance_scores) / len(relevance_scores)

        if stats["unique_articles"] > 0:
            stats["avg_tags_per_article"] = len(associations) / stats["unique_articles"]

        return stats
