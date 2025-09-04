"""
Article Configuration Item Category Associations entity for Autotask API.

This module provides the ArticleConfigurationItemCategoryAssociationsEntity class for managing
associations between knowledge base articles and configuration item categories.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleConfigurationItemCategoryAssociationsEntity(BaseEntity):
    """
    Entity for managing Autotask Article Configuration Item Category Associations.

    This entity manages the relationships between knowledge base articles
    and configuration item categories, enabling content categorization and filtering.
    """

    def __init__(
        self, client, entity_name="ArticleConfigurationItemCategoryAssociations"
    ):
        """Initialize the Article Configuration Item Category Associations entity."""
        super().__init__(client, entity_name)

    def create(self, association_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article-configuration item category association.

        Args:
            association_data: Dictionary containing association information
                Required fields:
                - articleId: ID of the article
                - configurationItemCategoryId: ID of the configuration item category
                Optional fields:
                - isActive: Whether the association is active
                - createdDate: Date the association was created
                - createdBy: ID of the user who created the association

        Returns:
            CreateResponse: Response containing created association data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["articleId", "configurationItemCategoryId"]
        self._validate_required_fields(association_data, required_fields)

        # Set default values
        if "isActive" not in association_data:
            association_data["isActive"] = True

        if "createdDate" not in association_data:
            association_data["createdDate"] = datetime.now().isoformat()

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
        Get all configuration item category associations for a specific article.

        Args:
            article_id: ID of the article
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of associations for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def get_by_category(
        self,
        category_id: int,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all article associations for a specific configuration item category.

        Args:
            category_id: ID of the configuration item category
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of associations for the category
        """
        filters = [
            QueryFilter(field="configurationItemCategoryId", op="eq", value=category_id)
        ]

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        return self.query(filters=filters, max_records=limit)

    def create_association(
        self, article_id: int, category_id: int, created_by: Optional[int] = None
    ) -> CreateResponse:
        """
        Create an association between an article and a configuration item category.

        Args:
            article_id: ID of the article
            category_id: ID of the configuration item category
            created_by: ID of the user creating the association

        Returns:
            Created association data

        Raises:
            ValidationError: If the association already exists
            AutotaskAPIError: If the creation fails
        """
        # Check if association already exists
        existing = self.get_existing_association(article_id, category_id)
        if existing:
            if existing.get("isActive"):
                raise ValueError(
                    f"Active association already exists between article {article_id} "
                    f"and category {category_id}"
                )
            else:
                # Reactivate existing association
                return self.update(existing["id"], {"isActive": True})

        association_data = {
            "articleId": article_id,
            "configurationItemCategoryId": category_id,
            "isActive": True,
        }

        if created_by:
            association_data["createdBy"] = created_by

        return self.create(association_data)

    def remove_association(
        self, article_id: int, category_id: int, soft_delete: bool = True
    ) -> bool:
        """
        Remove an association between an article and configuration item category.

        Args:
            article_id: ID of the article
            category_id: ID of the configuration item category
            soft_delete: If True, mark as inactive; if False, hard delete

        Returns:
            True if removal was successful

        Raises:
            ValueError: If association doesn't exist
            AutotaskAPIError: If the removal fails
        """
        association = self.get_existing_association(article_id, category_id)
        if not association:
            raise ValueError(
                f"No association found between article {article_id} "
                f"and category {category_id}"
            )

        if soft_delete:
            self.update(association["id"], {"isActive": False})
            return True
        else:
            return self.delete(association["id"])

    def get_existing_association(
        self, article_id: int, category_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing association between article and category.

        Args:
            article_id: ID of the article
            category_id: ID of the configuration item category

        Returns:
            Association data if found, None otherwise
        """
        filters = [
            QueryFilter(field="articleId", op="eq", value=article_id),
            QueryFilter(
                field="configurationItemCategoryId", op="eq", value=category_id
            ),
        ]

        associations = self.query(filters=filters, max_records=1)
        return associations[0] if associations else None

    def bulk_associate_categories(
        self,
        article_id: int,
        category_ids: List[int],
        created_by: Optional[int] = None,
        replace_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Associate an article with multiple configuration item categories.

        Args:
            article_id: ID of the article
            category_ids: List of configuration item category IDs
            created_by: ID of the user creating the associations
            replace_existing: If True, remove existing associations first

        Returns:
            Dictionary with association results
        """
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
            "total_requested": len(category_ids),
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

        for category_id in category_ids:
            try:
                association = self.create_association(
                    article_id, category_id, created_by
                )
                results["created"].append(
                    {
                        "category_id": category_id,
                        "association_id": association.get("item_id"),
                    }
                )
            except ValueError as e:
                if "already exists" in str(e):
                    results["skipped"].append(
                        {
                            "category_id": category_id,
                            "reason": "Association already exists",
                        }
                    )
                else:
                    results["errors"].append(
                        {"category_id": category_id, "error": str(e)}
                    )
            except Exception as e:
                results["errors"].append({"category_id": category_id, "error": str(e)})

        return results

    def get_article_categories(
        self, article_id: int, include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all configuration item categories associated with an article.

        Args:
            article_id: ID of the article
            include_details: Whether to include category details

        Returns:
            List of categories with optional details
        """
        associations = self.get_by_article(article_id, include_inactive=False)

        if not include_details:
            return [
                {"category_id": assoc.get("configurationItemCategoryId")}
                for assoc in associations
            ]

        # Get category details (would need ConfigurationItemCategories entity)
        categories = []
        for assoc in associations:
            category_info = {
                "association_id": assoc.get("id"),
                "category_id": assoc.get("configurationItemCategoryId"),
                "created_date": assoc.get("createdDate"),
                "created_by": assoc.get("createdBy"),
            }
            categories.append(category_info)

        return categories

    def get_category_articles(
        self,
        category_id: int,
        include_details: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all articles associated with a configuration item category.

        Args:
            category_id: ID of the configuration item category
            include_details: Whether to include article details
            limit: Maximum number of articles to return

        Returns:
            List of articles with optional details
        """
        associations = self.get_by_category(
            category_id, include_inactive=False, limit=limit
        )

        if not include_details:
            return [{"article_id": assoc.get("articleId")} for assoc in associations]

        # Return association details
        articles = []
        for assoc in associations:
            article_info = {
                "association_id": assoc.get("id"),
                "article_id": assoc.get("articleId"),
                "created_date": assoc.get("createdDate"),
                "created_by": assoc.get("createdBy"),
            }
            articles.append(article_info)

        return articles

    def get_association_statistics(
        self, category_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about article-category associations.

        Args:
            category_ids: Optional list of category IDs to analyze

        Returns:
            Dictionary with association statistics
        """
        filters = []

        if category_ids:
            filters.append(
                QueryFilter(
                    field="configurationItemCategoryId", op="in", value=category_ids
                )
            )

        associations = self.query(filters=filters)

        stats = {
            "total_associations": len(associations),
            "active_associations": 0,
            "inactive_associations": 0,
            "by_category": {},
            "by_article": {},
            "top_categories": {},
            "top_articles": {},
        }

        for association in associations:
            article_id = association.get("articleId")
            category_id = association.get("configurationItemCategoryId")
            is_active = association.get("isActive", True)

            # Active/inactive count
            if is_active:
                stats["active_associations"] += 1
            else:
                stats["inactive_associations"] += 1

            # Count by category
            if is_active:  # Only count active associations
                stats["by_category"][category_id] = (
                    stats["by_category"].get(category_id, 0) + 1
                )

                # Count by article
                stats["by_article"][article_id] = (
                    stats["by_article"].get(article_id, 0) + 1
                )

        # Get top categories and articles
        stats["top_categories"] = sorted(
            stats["by_category"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        stats["top_articles"] = sorted(
            stats["by_article"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        return stats
