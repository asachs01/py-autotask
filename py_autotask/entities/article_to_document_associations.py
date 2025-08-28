"""
Article to Document Associations entity for Autotask API.

This module provides the ArticleToDocumentAssociationsEntity class for managing
associations between knowledge base articles and documents.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleToDocumentAssociationsEntity(BaseEntity):
    """
    Entity for managing Autotask Article to Document Associations.

    This entity manages the relationships between knowledge base articles
    and documents, enabling content linking and reference management.
    """

    def __init__(self, client, entity_name="ArticleToDocumentAssociations"):
        """Initialize the Article to Document Associations entity."""
        super().__init__(client, entity_name)

    def create(self, association_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article-to-document association.

        Args:
            association_data: Dictionary containing association information
                Required fields:
                - articleId: ID of the article
                - documentId: ID of the document
                Optional fields:
                - associationType: Type of association (1=Reference, 2=Supporting, 3=Template, 4=Attachment)
                - isActive: Whether the association is active
                - createdDate: Date the association was created
                - createdBy: ID of the user who created the association
                - relevanceScore: How relevant the document is to the article (0.0 to 1.0)
                - description: Description of the relationship
                - displayOrder: Order for displaying documents in the article

        Returns:
            CreateResponse: Response containing created association data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["articleId", "documentId"]
        self._validate_required_fields(association_data, required_fields)

        # Set default values
        if "associationType" not in association_data:
            association_data["associationType"] = 1  # Reference

        if "isActive" not in association_data:
            association_data["isActive"] = True

        if "createdDate" not in association_data:
            association_data["createdDate"] = datetime.now().isoformat()

        if "relevanceScore" not in association_data:
            association_data["relevanceScore"] = 1.0

        if "displayOrder" not in association_data:
            association_data["displayOrder"] = 1

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
        association_type: Optional[int] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all document associations for a specific article.

        Args:
            article_id: ID of the article
            association_type: Optional filter by association type
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of document associations for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if association_type is not None:
            filters.append(
                QueryFilter(field="associationType", op="eq", value=association_type)
            )

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        associations = self.query(filters=filters, max_records=limit)

        # Sort by display order, then relevance score
        return sorted(
            associations,
            key=lambda x: (x.get("displayOrder", 999), -x.get("relevanceScore", 0)),
        )

    def get_by_document(
        self,
        document_id: int,
        association_type: Optional[int] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all article associations for a specific document.

        Args:
            document_id: ID of the document
            association_type: Optional filter by association type
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of article associations for the document
        """
        filters = [QueryFilter(field="documentId", op="eq", value=document_id)]

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

    def associate_document_with_article(
        self,
        article_id: int,
        document_id: int,
        association_type: int = 1,
        relevance_score: float = 1.0,
        display_order: Optional[int] = None,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> CreateResponse:
        """
        Associate a document with an article.

        Args:
            article_id: ID of the article
            document_id: ID of the document
            association_type: Type of association (1=Reference, 2=Supporting, 3=Template, 4=Attachment)
            relevance_score: Relevance score (0.0 to 1.0)
            display_order: Order for displaying the document
            description: Optional description of the relationship
            created_by: ID of the user creating the association

        Returns:
            Created association data

        Raises:
            ValidationError: If the association already exists
            AutotaskAPIError: If the creation fails
        """
        # Check for existing association
        existing = self.get_existing_association(article_id, document_id)
        if existing:
            if existing.get("isActive"):
                raise ValueError(
                    f"Active association already exists between article {article_id} "
                    f"and document {document_id}"
                )
            else:
                # Reactivate existing association
                return self.update(
                    existing["id"],
                    {
                        "isActive": True,
                        "associationType": association_type,
                        "relevanceScore": max(0.0, min(1.0, relevance_score)),
                        "displayOrder": display_order
                        or existing.get("displayOrder", 1),
                    },
                )

        # Auto-assign display order if not provided
        if display_order is None:
            existing_associations = self.get_by_article(
                article_id, include_inactive=False
            )
            max_order = max(
                [assoc.get("displayOrder", 0) for assoc in existing_associations],
                default=0,
            )
            display_order = max_order + 1

        association_data = {
            "articleId": article_id,
            "documentId": document_id,
            "associationType": association_type,
            "relevanceScore": max(0.0, min(1.0, relevance_score)),  # Clamp to 0-1
            "displayOrder": display_order,
            "isActive": True,
        }

        if description:
            association_data["description"] = description

        if created_by:
            association_data["createdBy"] = created_by

        return self.create(association_data)

    def add_supporting_document(
        self,
        article_id: int,
        document_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
    ) -> CreateResponse:
        """
        Add a supporting document to an article.

        Args:
            article_id: ID of the article
            document_id: ID of the supporting document
            created_by: ID of the user adding the document
            description: Optional description

        Returns:
            Created association data
        """
        return self.associate_document_with_article(
            article_id=article_id,
            document_id=document_id,
            association_type=2,  # Supporting
            relevance_score=1.0,
            description=description or "Supporting document",
            created_by=created_by,
        )

    def add_template_document(
        self,
        article_id: int,
        document_id: int,
        created_by: Optional[int] = None,
        description: Optional[str] = None,
    ) -> CreateResponse:
        """
        Add a template document to an article.

        Args:
            article_id: ID of the article
            document_id: ID of the template document
            created_by: ID of the user adding the document
            description: Optional description

        Returns:
            Created association data
        """
        return self.associate_document_with_article(
            article_id=article_id,
            document_id=document_id,
            association_type=3,  # Template
            relevance_score=1.0,
            description=description or "Template document",
            created_by=created_by,
        )

    def get_existing_association(
        self, article_id: int, document_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing association between article and document.

        Args:
            article_id: ID of the article
            document_id: ID of the document

        Returns:
            Association data if found, None otherwise
        """
        filters = [
            QueryFilter(field="articleId", op="eq", value=article_id),
            QueryFilter(field="documentId", op="eq", value=document_id),
        ]

        associations = self.query(filters=filters, max_records=1)
        return associations[0] if associations else None

    def remove_association(
        self, article_id: int, document_id: int, soft_delete: bool = True
    ) -> bool:
        """
        Remove association between article and document.

        Args:
            article_id: ID of the article
            document_id: ID of the document
            soft_delete: If True, mark as inactive; if False, hard delete

        Returns:
            True if removal was successful

        Raises:
            ValueError: If association doesn't exist
            AutotaskAPIError: If the removal fails
        """
        association = self.get_existing_association(article_id, document_id)
        if not association:
            raise ValueError(
                f"No association found between article {article_id} and document {document_id}"
            )

        if soft_delete:
            self.update(association["id"], {"isActive": False})
            return True
        else:
            return self.delete(association["id"])

    def reorder_documents(
        self, article_id: int, document_order: List[Dict[str, Any]]
    ) -> List[UpdateResponse]:
        """
        Reorder documents for an article.

        Args:
            article_id: ID of the article
            document_order: List of dictionaries with 'document_id' and 'display_order'

        Returns:
            List of update responses
        """
        results = []

        for order_info in document_order:
            document_id = order_info.get("document_id")
            display_order = order_info.get("display_order")

            if not document_id or display_order is None:
                continue

            association = self.get_existing_association(article_id, document_id)
            if association:
                try:
                    result = self.update(
                        association["id"], {"displayOrder": display_order}
                    )
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to update display order for document {document_id}: {e}"
                    )
                    results.append({"error": str(e), "document_id": document_id})

        return results

    def bulk_associate_documents(
        self,
        article_id: int,
        document_data: List[Dict[str, Any]],
        replace_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Associate multiple documents with an article.

        Args:
            article_id: ID of the article
            document_data: List of document data dictionaries with keys:
                          - document_id: ID of the document
                          - association_type: Optional type (default: 1)
                          - relevance_score: Optional score (default: 1.0)
                          - display_order: Optional order
                          - description: Optional description
            replace_existing: If True, remove existing associations first

        Returns:
            Dictionary with association results
        """
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
            "total_requested": len(document_data),
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

        for doc_info in document_data:
            document_id = doc_info.get("document_id")
            association_type = doc_info.get("association_type", 1)
            relevance_score = doc_info.get("relevance_score", 1.0)
            display_order = doc_info.get("display_order")
            description = doc_info.get("description")

            try:
                association = self.associate_document_with_article(
                    article_id,
                    document_id,
                    association_type,
                    relevance_score,
                    display_order,
                    description,
                )
                results["created"].append(
                    {
                        "document_id": document_id,
                        "association_id": association.get("item_id"),
                    }
                )
            except ValueError as e:
                if "already exists" in str(e):
                    results["skipped"].append(
                        {
                            "document_id": document_id,
                            "reason": "Association already exists",
                        }
                    )
                else:
                    results["errors"].append(
                        {"document_id": document_id, "error": str(e)}
                    )
            except Exception as e:
                results["errors"].append({"document_id": document_id, "error": str(e)})

        return results

    def get_article_document_library(
        self, article_id: int, group_by_type: bool = True, include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get all documents associated with an article, optionally grouped by type.

        Args:
            article_id: ID of the article
            group_by_type: Whether to group documents by association type
            include_details: Whether to include association details

        Returns:
            Dictionary with documents and optional grouping
        """
        associations = self.get_by_article(article_id, include_inactive=False)

        if not group_by_type:
            return {
                "article_id": article_id,
                "total_documents": len(associations),
                "documents": (
                    associations
                    if include_details
                    else [
                        {"document_id": assoc.get("documentId")}
                        for assoc in associations
                    ]
                ),
            }

        # Group by association type
        document_library = {
            "article_id": article_id,
            "total_documents": len(associations),
            "by_type": {
                "references": [],  # Type 1
                "supporting": [],  # Type 2
                "templates": [],  # Type 3
                "attachments": [],  # Type 4
            },
        }

        for assoc in associations:
            association_type = assoc.get("associationType", 1)
            document_info = (
                assoc if include_details else {"document_id": assoc.get("documentId")}
            )

            if association_type == 1:
                document_library["by_type"]["references"].append(document_info)
            elif association_type == 2:
                document_library["by_type"]["supporting"].append(document_info)
            elif association_type == 3:
                document_library["by_type"]["templates"].append(document_info)
            elif association_type == 4:
                document_library["by_type"]["attachments"].append(document_info)

        return document_library

    def get_document_usage(
        self, document_id: int, include_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a document across articles.

        Args:
            document_id: ID of the document
            include_statistics: Whether to include detailed statistics

        Returns:
            Dictionary with document usage information
        """
        associations = self.get_by_document(document_id, include_inactive=False)

        usage_info = {
            "document_id": document_id,
            "total_articles": len(associations),
            "articles": associations,
        }

        if include_statistics:
            stats = {
                "by_type": {
                    "references": 0,
                    "supporting": 0,
                    "templates": 0,
                    "attachments": 0,
                },
                "avg_relevance_score": 0.0,
                "most_recent_association": None,
                "oldest_association": None,
                "top_articles_by_relevance": [],
            }

            if associations:
                relevance_scores = []
                sorted_by_date = sorted(
                    associations, key=lambda x: x.get("createdDate", ""), reverse=True
                )

                stats["most_recent_association"] = sorted_by_date[0]
                stats["oldest_association"] = sorted_by_date[-1]

                for assoc in associations:
                    association_type = assoc.get("associationType", 1)
                    relevance_score = assoc.get("relevanceScore", 1.0)
                    relevance_scores.append(relevance_score)

                    if association_type == 1:
                        stats["by_type"]["references"] += 1
                    elif association_type == 2:
                        stats["by_type"]["supporting"] += 1
                    elif association_type == 3:
                        stats["by_type"]["templates"] += 1
                    elif association_type == 4:
                        stats["by_type"]["attachments"] += 1

                # Calculate average relevance
                stats["avg_relevance_score"] = sum(relevance_scores) / len(
                    relevance_scores
                )

                # Top articles by relevance
                stats["top_articles_by_relevance"] = sorted(
                    associations, key=lambda x: x.get("relevanceScore", 0), reverse=True
                )[:5]

            usage_info["statistics"] = stats

        return usage_info

    def find_orphaned_documents(
        self,
        document_ids: Optional[List[int]] = None,
        association_types: Optional[List[int]] = None,
    ) -> List[int]:
        """
        Find documents that have no active article associations.

        Args:
            document_ids: Optional list of document IDs to check
            association_types: Optional list of association types to consider

        Returns:
            List of document IDs with no active associations
        """
        filters = [QueryFilter(field="isActive", op="eq", value=True)]

        if document_ids:
            filters.append(QueryFilter(field="documentId", op="in", value=document_ids))

        if association_types:
            filters.append(
                QueryFilter(field="associationType", op="in", value=association_types)
            )

        active_associations = self.query(filters=filters)
        associated_document_ids = set(
            assoc.get("documentId") for assoc in active_associations
        )

        if document_ids:
            # Return documents from the provided list that have no associations
            return [
                doc_id
                for doc_id in document_ids
                if doc_id not in associated_document_ids
            ]
        else:
            # This would require querying the Documents entity to get all document IDs
            # For now, return placeholder
            self.logger.warning(
                "find_orphaned_documents without document_ids requires Documents entity query"
            )
            return []

    def get_association_statistics(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about article-to-document associations.

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
            "unique_articles": len(
                set(assoc.get("articleId") for assoc in associations)
            ),
            "unique_documents": len(
                set(assoc.get("documentId") for assoc in associations)
            ),
            "by_type": {
                "references": 0,  # Type 1
                "supporting": 0,  # Type 2
                "templates": 0,  # Type 3
                "attachments": 0,  # Type 4
            },
            "avg_relevance": 0.0,
            "avg_documents_per_article": 0.0,
            "top_articles": {},
            "top_documents": {},
            "associations_per_day": {},
            "relevance_distribution": {
                "high": 0,  # >= 0.8
                "medium": 0,  # 0.4 - 0.8
                "low": 0,  # < 0.4
            },
        }

        relevance_scores = []

        for association in associations:
            article_id = association.get("articleId")
            document_id = association.get("documentId")
            association_type = association.get("associationType", 1)
            relevance = association.get("relevanceScore", 1.0)
            created_date = association.get("createdDate", "")

            # Count by type
            if association_type == 1:
                stats["by_type"]["references"] += 1
            elif association_type == 2:
                stats["by_type"]["supporting"] += 1
            elif association_type == 3:
                stats["by_type"]["templates"] += 1
            elif association_type == 4:
                stats["by_type"]["attachments"] += 1

            # Top articles and documents
            stats["top_articles"][article_id] = (
                stats["top_articles"].get(article_id, 0) + 1
            )
            stats["top_documents"][document_id] = (
                stats["top_documents"].get(document_id, 0) + 1
            )

            # Relevance distribution
            if relevance >= 0.8:
                stats["relevance_distribution"]["high"] += 1
            elif relevance >= 0.4:
                stats["relevance_distribution"]["medium"] += 1
            else:
                stats["relevance_distribution"]["low"] += 1

            relevance_scores.append(relevance)

            # Associations per day
            if created_date:
                try:
                    assoc_dt = datetime.fromisoformat(
                        created_date.replace("Z", "+00:00")
                    )
                    day_key = assoc_dt.date().isoformat()
                    stats["associations_per_day"][day_key] = (
                        stats["associations_per_day"].get(day_key, 0) + 1
                    )
                except ValueError:
                    pass

        # Calculate averages
        if relevance_scores:
            stats["avg_relevance"] = sum(relevance_scores) / len(relevance_scores)

        if stats["unique_articles"] > 0:
            stats["avg_documents_per_article"] = (
                len(associations) / stats["unique_articles"]
            )

        # Sort top items
        stats["top_articles"] = sorted(
            stats["top_articles"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        stats["top_documents"] = sorted(
            stats["top_documents"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        return stats
