"""
Article Plain Text Content entity for Autotask API.

This module provides the ArticlePlainTextContentEntity class for managing
plain text content versions of knowledge base articles for search and indexing.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticlePlainTextContentEntity(BaseEntity):
    """
    Entity for managing Autotask Article Plain Text Content.

    This entity manages plain text versions of article content,
    which are used for full-text search, indexing, and content analysis.
    """

    def __init__(self, client, entity_name="ArticlePlainTextContent"):
        """Initialize the Article Plain Text Content entity."""
        super().__init__(client, entity_name)

    def create(self, content_data: Dict[str, Any]) -> CreateResponse:
        """
        Create new article plain text content.

        Args:
            content_data: Dictionary containing content information
                Required fields:
                - articleId: ID of the article
                - plainTextContent: Plain text version of the article content
                Optional fields:
                - contentVersion: Version number of the content
                - extractedDate: Date the plain text was extracted
                - wordCount: Number of words in the content
                - characterCount: Number of characters in the content
                - languageCode: Language code (e.g., 'en', 'es', 'fr')
                - isSearchable: Whether content is included in search index

        Returns:
            CreateResponse: Response containing created content data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["articleId", "plainTextContent"]
        self._validate_required_fields(content_data, required_fields)

        # Auto-calculate content metrics
        plain_text = content_data["plainTextContent"]
        if "wordCount" not in content_data:
            content_data["wordCount"] = self._count_words(plain_text)

        if "characterCount" not in content_data:
            content_data["characterCount"] = len(plain_text)

        # Set default values
        if "extractedDate" not in content_data:
            content_data["extractedDate"] = datetime.now().isoformat()

        if "contentVersion" not in content_data:
            content_data["contentVersion"] = 1

        if "isSearchable" not in content_data:
            content_data["isSearchable"] = True

        if "languageCode" not in content_data:
            content_data["languageCode"] = "en"

        return self._create(content_data)

    def get(self, content_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve plain text content by ID.

        Args:
            content_id: The content ID

        Returns:
            Dictionary containing content data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(content_id)

    def update(self, content_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update existing plain text content.

        Args:
            content_id: The content ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated content data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        # Auto-calculate content metrics if content is updated
        if "plainTextContent" in update_data:
            plain_text = update_data["plainTextContent"]
            update_data["wordCount"] = self._count_words(plain_text)
            update_data["characterCount"] = len(plain_text)

        # Update last modified timestamp
        update_data["lastModifiedDate"] = datetime.now().isoformat()

        return self._update(content_id, update_data)

    def delete(self, content_id: int) -> bool:
        """
        Delete plain text content.

        Args:
            content_id: The content ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(content_id)

    def get_by_article(
        self,
        article_id: int,
        include_non_searchable: bool = False,
        latest_version_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get plain text content for a specific article.

        Args:
            article_id: ID of the article
            include_non_searchable: Whether to include non-searchable content
            latest_version_only: Whether to return only the latest version

        Returns:
            List of plain text content versions for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if not include_non_searchable:
            filters.append(QueryFilter(field="isSearchable", op="eq", value=True))

        content_versions = self.query(filters=filters)

        if latest_version_only and content_versions:
            # Return only the latest version
            latest = max(content_versions, key=lambda x: x.get("contentVersion", 0))
            return [latest]

        # Sort by version (newest first)
        return sorted(
            content_versions, key=lambda x: x.get("contentVersion", 0), reverse=True
        )

    def create_from_html(
        self,
        article_id: int,
        html_content: str,
        content_version: Optional[int] = None,
        language_code: str = "en",
    ) -> CreateResponse:
        """
        Create plain text content from HTML content.

        Args:
            article_id: ID of the article
            html_content: HTML content to convert
            content_version: Version number of the content
            language_code: Language code

        Returns:
            Created plain text content data
        """
        # Strip HTML tags and clean text
        plain_text = self._html_to_plain_text(html_content)

        content_data = {
            "articleId": article_id,
            "plainTextContent": plain_text,
            "languageCode": language_code,
        }

        if content_version:
            content_data["contentVersion"] = content_version

        return self.create(content_data)

    def update_article_content(
        self, article_id: int, new_content: str, increment_version: bool = True
    ) -> CreateResponse:
        """
        Update or create new version of article plain text content.

        Args:
            article_id: ID of the article
            new_content: New plain text content
            increment_version: Whether to increment the version number

        Returns:
            Created or updated content data
        """
        # Get existing content to determine version number
        existing_content = self.get_by_article(article_id, latest_version_only=True)

        if existing_content and increment_version:
            current_version = existing_content[0].get("contentVersion", 1)
            new_version = current_version + 1
        else:
            new_version = 1

        content_data = {
            "articleId": article_id,
            "plainTextContent": new_content,
            "contentVersion": new_version,
        }

        return self.create(content_data)

    def search_content(
        self,
        search_text: str,
        language_code: Optional[str] = None,
        min_word_count: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search plain text content.

        Args:
            search_text: Text to search for
            language_code: Optional language filter
            min_word_count: Minimum word count filter
            limit: Maximum number of results to return

        Returns:
            List of matching content records
        """
        filters = [
            QueryFilter(field="plainTextContent", op="contains", value=search_text),
            QueryFilter(field="isSearchable", op="eq", value=True),
        ]

        if language_code:
            filters.append(
                QueryFilter(field="languageCode", op="eq", value=language_code)
            )

        if min_word_count:
            filters.append(
                QueryFilter(field="wordCount", op="gte", value=min_word_count)
            )

        return self.query(filters=filters, max_records=limit)

    def get_content_statistics(
        self,
        article_ids: Optional[List[int]] = None,
        language_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about plain text content.

        Args:
            article_ids: Optional list of article IDs to analyze
            language_code: Optional language filter

        Returns:
            Dictionary with content statistics
        """
        filters = []

        if article_ids:
            filters.append(QueryFilter(field="articleId", op="in", value=article_ids))

        if language_code:
            filters.append(
                QueryFilter(field="languageCode", op="eq", value=language_code)
            )

        content_records = self.query(filters=filters)

        stats = {
            "total_records": len(content_records),
            "by_language": {},
            "by_article": {},
            "total_words": 0,
            "total_characters": 0,
            "avg_word_count": 0,
            "avg_character_count": 0,
            "searchable_records": 0,
            "version_distribution": {},
            "content_length_ranges": {
                "short": 0,  # < 500 words
                "medium": 0,  # 500-2000 words
                "long": 0,  # 2000-5000 words
                "very_long": 0,  # > 5000 words
            },
        }

        word_counts = []
        character_counts = []

        for record in content_records:
            article_id = record.get("articleId")
            language = record.get("languageCode", "unknown")
            word_count = record.get("wordCount", 0)
            char_count = record.get("characterCount", 0)
            is_searchable = record.get("isSearchable", True)
            version = record.get("contentVersion", 1)

            # Count by language
            stats["by_language"][language] = stats["by_language"].get(language, 0) + 1

            # Count by article
            stats["by_article"][article_id] = stats["by_article"].get(article_id, 0) + 1

            # Word and character totals
            stats["total_words"] += word_count
            stats["total_characters"] += char_count
            word_counts.append(word_count)
            character_counts.append(char_count)

            # Searchable count
            if is_searchable:
                stats["searchable_records"] += 1

            # Version distribution
            stats["version_distribution"][version] = (
                stats["version_distribution"].get(version, 0) + 1
            )

            # Content length categorization
            if word_count < 500:
                stats["content_length_ranges"]["short"] += 1
            elif word_count < 2000:
                stats["content_length_ranges"]["medium"] += 1
            elif word_count < 5000:
                stats["content_length_ranges"]["long"] += 1
            else:
                stats["content_length_ranges"]["very_long"] += 1

        # Calculate averages
        if word_counts:
            stats["avg_word_count"] = sum(word_counts) / len(word_counts)

        if character_counts:
            stats["avg_character_count"] = sum(character_counts) / len(character_counts)

        return stats

    def get_articles_without_content(self, limit: Optional[int] = None) -> List[int]:
        """
        Get article IDs that don't have plain text content.

        Args:
            limit: Maximum number of article IDs to return

        Returns:
            List of article IDs without plain text content
        """
        # This would require cross-entity query or separate Articles entity call
        # For now, return placeholder implementation
        self.logger.warning(
            "get_articles_without_content requires cross-entity query - "
            "consider implementing with Articles entity"
        )
        return []

    def bulk_create_content(
        self, content_list: List[Dict[str, Any]], batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Create multiple plain text content records in batches.

        Args:
            content_list: List of content data dictionaries
            batch_size: Number of records to process per batch

        Returns:
            Dictionary with creation results
        """
        results = {"created": [], "errors": [], "total_requested": len(content_list)}

        for i in range(0, len(content_list), batch_size):
            batch = content_list[i : i + batch_size]

            for content_data in batch:
                try:
                    created = self.create(content_data)
                    results["created"].append(
                        {
                            "article_id": content_data.get("articleId"),
                            "content_id": created.get("item_id"),
                        }
                    )
                except Exception as e:
                    results["errors"].append(
                        {"article_id": content_data.get("articleId"), "error": str(e)}
                    )

        return results

    def update_searchable_status(
        self, content_ids: List[int], is_searchable: bool
    ) -> List[UpdateResponse]:
        """
        Update searchable status for multiple content records.

        Args:
            content_ids: List of content IDs to update
            is_searchable: New searchable status

        Returns:
            List of update responses
        """
        results = []

        for content_id in content_ids:
            try:
                result = self.update(content_id, {"isSearchable": is_searchable})
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to update content {content_id}: {e}")
                results.append({"error": str(e), "content_id": content_id})

        return results

    def find_duplicate_content(
        self, similarity_threshold: float = 0.8, min_word_count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find potentially duplicate content across articles.

        Args:
            similarity_threshold: Similarity threshold (0.0 to 1.0)
            min_word_count: Minimum word count to consider

        Returns:
            List of potential duplicate content pairs
        """
        filters = [QueryFilter(field="wordCount", op="gte", value=min_word_count)]

        content_records = self.query(filters=filters)

        # Simple duplicate detection based on exact matches
        # In a real implementation, you might use fuzzy matching or NLP
        content_map = {}
        duplicates = []

        for record in content_records:
            content = record.get("plainTextContent", "").strip().lower()
            content_hash = hash(content)

            if content_hash in content_map:
                duplicates.append(
                    {
                        "original": content_map[content_hash],
                        "duplicate": record,
                        "similarity": 1.0,  # Exact match
                    }
                )
            else:
                content_map[content_hash] = record

        return duplicates

    def _count_words(self, text: str) -> int:
        """
        Count words in text.

        Args:
            text: Text to count words in

        Returns:
            Number of words
        """
        if not text:
            return 0

        # Remove extra whitespace and split on word boundaries
        words = re.findall(r"\b\w+\b", text.lower())
        return len(words)

    def _html_to_plain_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.

        Args:
            html_content: HTML content

        Returns:
            Plain text version
        """
        if not html_content:
            return ""

        # Simple HTML tag removal (in production, consider using BeautifulSoup)
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)

        # Replace HTML entities
        html_entities = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&nbsp;": " ",
        }

        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text.strip())

        return text
