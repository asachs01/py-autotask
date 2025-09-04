"""
Article Ticket Associations entity for Autotask API.

This module provides the ArticleTicketAssociationsEntity class for managing
associations between knowledge base articles and support tickets.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleTicketAssociationsEntity(BaseEntity):
    """
    Entity for managing Autotask Article Ticket Associations.

    This entity manages the relationships between knowledge base articles
    and support tickets, enabling knowledge sharing and ticket resolution tracking.
    """

    def __init__(self, client, entity_name="ArticleTicketAssociations"):
        """Initialize the Article Ticket Associations entity."""
        super().__init__(client, entity_name)

    def create(self, association_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article-ticket association.

        Args:
            association_data: Dictionary containing association information
                Required fields:
                - articleId: ID of the article
                - ticketId: ID of the ticket
                Optional fields:
                - associationType: Type of association (1=Referenced, 2=Resolved, 3=Related)
                - isActive: Whether the association is active
                - createdDate: Date the association was created
                - createdBy: ID of the user who created the association
                - relevanceScore: How relevant the article is to the ticket (0.0 to 1.0)
                - notes: Additional notes about the association

        Returns:
            CreateResponse: Response containing created association data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["articleId", "ticketId"]
        self._validate_required_fields(association_data, required_fields)

        # Set default values
        if "associationType" not in association_data:
            association_data["associationType"] = 1  # Referenced

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
        association_type: Optional[int] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all ticket associations for a specific article.

        Args:
            article_id: ID of the article
            association_type: Optional filter by association type
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of ticket associations for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if association_type is not None:
            filters.append(
                QueryFilter(field="associationType", op="eq", value=association_type)
            )

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        associations = self.query(filters=filters, max_records=limit)

        # Sort by creation date (newest first)
        return sorted(
            associations, key=lambda x: x.get("createdDate", ""), reverse=True
        )

    def get_by_ticket(
        self,
        ticket_id: int,
        association_type: Optional[int] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all article associations for a specific ticket.

        Args:
            ticket_id: ID of the ticket
            association_type: Optional filter by association type
            include_inactive: Whether to include inactive associations
            limit: Maximum number of associations to return

        Returns:
            List of article associations for the ticket
        """
        filters = [QueryFilter(field="ticketId", op="eq", value=ticket_id)]

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

    def associate_article_with_ticket(
        self,
        article_id: int,
        ticket_id: int,
        association_type: int = 1,
        relevance_score: float = 1.0,
        notes: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> CreateResponse:
        """
        Associate an article with a ticket.

        Args:
            article_id: ID of the article
            ticket_id: ID of the ticket
            association_type: Type of association (1=Referenced, 2=Resolved, 3=Related)
            relevance_score: Relevance score (0.0 to 1.0)
            notes: Optional notes about the association
            created_by: ID of the user creating the association

        Returns:
            Created association data

        Raises:
            ValidationError: If the association already exists
            AutotaskAPIError: If the creation fails
        """
        # Check for existing association
        existing = self.get_existing_association(article_id, ticket_id)
        if existing:
            if existing.get("isActive"):
                raise ValueError(
                    f"Active association already exists between article {article_id} "
                    f"and ticket {ticket_id}"
                )
            else:
                # Reactivate existing association
                return self.update(
                    existing["id"],
                    {
                        "isActive": True,
                        "associationType": association_type,
                        "relevanceScore": max(0.0, min(1.0, relevance_score)),
                    },
                )

        association_data = {
            "articleId": article_id,
            "ticketId": ticket_id,
            "associationType": association_type,
            "relevanceScore": max(0.0, min(1.0, relevance_score)),  # Clamp to 0-1
            "isActive": True,
        }

        if notes:
            association_data["notes"] = notes

        if created_by:
            association_data["createdBy"] = created_by

        return self.create(association_data)

    def mark_article_as_resolution(
        self,
        article_id: int,
        ticket_id: int,
        created_by: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> CreateResponse:
        """
        Mark an article as resolving a ticket.

        Args:
            article_id: ID of the resolving article
            ticket_id: ID of the resolved ticket
            created_by: ID of the user marking the resolution
            notes: Optional resolution notes

        Returns:
            Created association data
        """
        return self.associate_article_with_ticket(
            article_id=article_id,
            ticket_id=ticket_id,
            association_type=2,  # Resolved
            relevance_score=1.0,
            notes=notes or "Article marked as ticket resolution",
            created_by=created_by,
        )

    def get_existing_association(
        self, article_id: int, ticket_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing association between article and ticket.

        Args:
            article_id: ID of the article
            ticket_id: ID of the ticket

        Returns:
            Association data if found, None otherwise
        """
        filters = [
            QueryFilter(field="articleId", op="eq", value=article_id),
            QueryFilter(field="ticketId", op="eq", value=ticket_id),
        ]

        associations = self.query(filters=filters, max_records=1)
        return associations[0] if associations else None

    def remove_association(
        self, article_id: int, ticket_id: int, soft_delete: bool = True
    ) -> bool:
        """
        Remove association between article and ticket.

        Args:
            article_id: ID of the article
            ticket_id: ID of the ticket
            soft_delete: If True, mark as inactive; if False, hard delete

        Returns:
            True if removal was successful

        Raises:
            ValueError: If association doesn't exist
            AutotaskAPIError: If the removal fails
        """
        association = self.get_existing_association(article_id, ticket_id)
        if not association:
            raise ValueError(
                f"No association found between article {article_id} and ticket {ticket_id}"
            )

        if soft_delete:
            self.update(association["id"], {"isActive": False})
            return True
        else:
            return self.delete(association["id"])

    def bulk_associate_articles(
        self,
        ticket_id: int,
        article_data: List[Dict[str, Any]],
        replace_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Associate multiple articles with a ticket.

        Args:
            ticket_id: ID of the ticket
            article_data: List of article data dictionaries with keys:
                         - article_id: ID of the article
                         - association_type: Optional type (default: 1)
                         - relevance_score: Optional score (default: 1.0)
                         - notes: Optional notes
            replace_existing: If True, remove existing associations first

        Returns:
            Dictionary with association results
        """
        results = {
            "created": [],
            "skipped": [],
            "errors": [],
            "total_requested": len(article_data),
        }

        if replace_existing:
            # Remove existing associations
            existing_associations = self.get_by_ticket(
                ticket_id, include_inactive=False
            )
            for assoc in existing_associations:
                try:
                    self.update(assoc["id"], {"isActive": False})
                except Exception as e:
                    self.logger.warning(
                        f"Failed to deactivate association {assoc['id']}: {e}"
                    )

        for article_info in article_data:
            article_id = article_info.get("article_id")
            association_type = article_info.get("association_type", 1)
            relevance_score = article_info.get("relevance_score", 1.0)
            notes = article_info.get("notes")

            try:
                association = self.associate_article_with_ticket(
                    article_id, ticket_id, association_type, relevance_score, notes
                )
                results["created"].append(
                    {
                        "article_id": article_id,
                        "association_id": association.get("item_id"),
                    }
                )
            except ValueError as e:
                if "already exists" in str(e):
                    results["skipped"].append(
                        {
                            "article_id": article_id,
                            "reason": "Association already exists",
                        }
                    )
                else:
                    results["errors"].append(
                        {"article_id": article_id, "error": str(e)}
                    )
            except Exception as e:
                results["errors"].append({"article_id": article_id, "error": str(e)})

        return results

    def get_ticket_knowledge_base(
        self,
        ticket_id: int,
        include_related: bool = True,
        min_relevance_score: float = 0.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all knowledge base articles associated with a ticket, grouped by type.

        Args:
            ticket_id: ID of the ticket
            include_related: Whether to include related articles
            min_relevance_score: Minimum relevance score filter

        Returns:
            Dictionary with articles grouped by association type
        """
        filters = [
            QueryFilter(field="ticketId", op="eq", value=ticket_id),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        if min_relevance_score > 0.0:
            filters.append(
                QueryFilter(field="relevanceScore", op="gte", value=min_relevance_score)
            )

        associations = self.query(filters=filters)

        knowledge_base = {
            "referenced": [],  # Type 1
            "resolved": [],  # Type 2
            "related": [],  # Type 3
        }

        for assoc in associations:
            association_type = assoc.get("associationType", 1)

            if association_type == 1:
                knowledge_base["referenced"].append(assoc)
            elif association_type == 2:
                knowledge_base["resolved"].append(assoc)
            elif association_type == 3 and include_related:
                knowledge_base["related"].append(assoc)

        # Sort each group by relevance score
        for group in knowledge_base.values():
            group.sort(key=lambda x: x.get("relevanceScore", 0), reverse=True)

        return knowledge_base

    def get_article_effectiveness(
        self, article_id: int, days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Get effectiveness statistics for an article based on ticket associations.

        Args:
            article_id: ID of the article
            days_back: Number of days to look back for statistics

        Returns:
            Dictionary with effectiveness metrics
        """
        cutoff_date = datetime.now() - datetime.timedelta(days=days_back)

        filters = [
            QueryFilter(field="articleId", op="eq", value=article_id),
            QueryFilter(field="isActive", op="eq", value=True),
            QueryFilter(field="createdDate", op="gte", value=cutoff_date.isoformat()),
        ]

        associations = self.query(filters=filters)

        effectiveness = {
            "article_id": article_id,
            "analysis_period_days": days_back,
            "total_associations": len(associations),
            "by_type": {"referenced": 0, "resolved": 0, "related": 0},
            "unique_tickets": len(set(assoc.get("ticketId") for assoc in associations)),
            "avg_relevance_score": 0.0,
            "resolution_rate": 0.0,  # Percentage of associations that are resolutions
            "associations_per_day": 0.0,
            "recent_trend": "stable",  # Could be: increasing, decreasing, stable
        }

        if not associations:
            return effectiveness

        relevance_scores = []
        resolution_count = 0

        for assoc in associations:
            association_type = assoc.get("associationType", 1)
            relevance_score = assoc.get("relevanceScore", 1.0)

            relevance_scores.append(relevance_score)

            if association_type == 1:
                effectiveness["by_type"]["referenced"] += 1
            elif association_type == 2:
                effectiveness["by_type"]["resolved"] += 1
                resolution_count += 1
            elif association_type == 3:
                effectiveness["by_type"]["related"] += 1

        # Calculate metrics
        effectiveness["avg_relevance_score"] = sum(relevance_scores) / len(
            relevance_scores
        )
        effectiveness["resolution_rate"] = (resolution_count / len(associations)) * 100
        effectiveness["associations_per_day"] = len(associations) / days_back

        return effectiveness

    def find_similar_tickets(
        self, ticket_id: int, min_shared_articles: int = 1, limit: Optional[int] = 10
    ) -> List[Dict[str, Any]]:
        """
        Find tickets with similar knowledge base associations.

        Args:
            ticket_id: ID of the source ticket
            min_shared_articles: Minimum number of shared articles
            limit: Maximum number of similar tickets to return

        Returns:
            List of similar tickets with shared article counts
        """
        # Get articles associated with the source ticket
        source_associations = self.get_by_ticket(ticket_id, include_inactive=False)
        source_article_ids = [assoc.get("articleId") for assoc in source_associations]

        if not source_article_ids:
            return []

        # Find tickets with shared articles
        filters = [
            QueryFilter(field="articleId", op="in", value=source_article_ids),
            QueryFilter(
                field="ticketId", op="neq", value=ticket_id
            ),  # Exclude source ticket
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        related_associations = self.query(filters=filters)

        # Count shared articles per ticket
        ticket_article_counts = {}
        for assoc in related_associations:
            similar_ticket_id = assoc.get("ticketId")
            if similar_ticket_id not in ticket_article_counts:
                ticket_article_counts[similar_ticket_id] = {
                    "ticket_id": similar_ticket_id,
                    "shared_articles": 0,
                    "shared_article_ids": [],
                    "relevance_sum": 0.0,
                }

            ticket_article_counts[similar_ticket_id]["shared_articles"] += 1
            ticket_article_counts[similar_ticket_id]["shared_article_ids"].append(
                assoc.get("articleId")
            )
            ticket_article_counts[similar_ticket_id]["relevance_sum"] += assoc.get(
                "relevanceScore", 1.0
            )

        # Filter by minimum shared articles and calculate average relevance
        similar_tickets = []
        for ticket_data in ticket_article_counts.values():
            if ticket_data["shared_articles"] >= min_shared_articles:
                ticket_data["avg_relevance"] = (
                    ticket_data["relevance_sum"] / ticket_data["shared_articles"]
                )
                similar_tickets.append(ticket_data)

        # Sort by shared articles count (descending) then by average relevance
        similar_tickets.sort(
            key=lambda x: (x["shared_articles"], x["avg_relevance"]), reverse=True
        )

        return similar_tickets[:limit] if limit else similar_tickets

    def get_association_statistics(
        self, date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about article-ticket associations.

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
            "unique_tickets": len(set(assoc.get("ticketId") for assoc in associations)),
            "by_type": {"referenced": 0, "resolved": 0, "related": 0},
            "avg_relevance": 0.0,
            "resolution_percentage": 0.0,
            "top_articles": {},
            "associations_per_day": {},
            "relevance_distribution": {
                "high": 0,  # >= 0.8
                "medium": 0,  # 0.4 - 0.8
                "low": 0,  # < 0.4
            },
        }

        relevance_scores = []
        resolution_count = 0

        for association in associations:
            article_id = association.get("articleId")
            association_type = association.get("associationType", 1)
            relevance = association.get("relevanceScore", 1.0)
            created_date = association.get("createdDate", "")

            # Count by type
            if association_type == 1:
                stats["by_type"]["referenced"] += 1
            elif association_type == 2:
                stats["by_type"]["resolved"] += 1
                resolution_count += 1
            elif association_type == 3:
                stats["by_type"]["related"] += 1

            # Top articles
            stats["top_articles"][article_id] = (
                stats["top_articles"].get(article_id, 0) + 1
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

        # Calculate averages and percentages
        if relevance_scores:
            stats["avg_relevance"] = sum(relevance_scores) / len(relevance_scores)

        if len(associations) > 0:
            stats["resolution_percentage"] = (
                resolution_count / len(associations)
            ) * 100

        # Sort top articles
        stats["top_articles"] = sorted(
            stats["top_articles"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        return stats
