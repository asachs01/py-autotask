"""
Documents entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class DocumentsEntity(BaseEntity):
    """
    Handles Document operations for the Autotask API.

    Manages document storage, organization, versioning,
    and access control within the Autotask system.
    """

    def __init__(self, client, entity_name: str = "Documents"):
        super().__init__(client, entity_name)

    def create_document(
        self,
        title: str,
        description: str,
        document_type: int,
        folder_id: Optional[int] = None,
        is_published: bool = True,
        publish_date: Optional[str] = None,
        expiration_date: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new document.

        Args:
            title: Document title
            description: Document description/content
            document_type: Type of document (ID)
            folder_id: Optional folder to organize document
            is_published: Whether document is published
            publish_date: Date to publish document (ISO format)
            expiration_date: Date when document expires (ISO format)
            **kwargs: Additional document fields

        Returns:
            Created document data
        """
        doc_data = {
            "Title": title,
            "Description": description,
            "DocumentType": document_type,
            "IsPublished": is_published,
            **kwargs,
        }

        if folder_id is not None:
            doc_data["FolderID"] = folder_id

        if publish_date:
            doc_data["PublishDate"] = publish_date

        if expiration_date:
            doc_data["ExpirationDate"] = expiration_date

        return self.create(doc_data)

    def get_published_documents(
        self,
        document_type: Optional[int] = None,
        folder_id: Optional[int] = None,
        exclude_expired: bool = True,
    ) -> EntityList:
        """
        Get all published documents.

        Args:
            document_type: Optional document type filter
            folder_id: Optional folder filter
            exclude_expired: Whether to exclude expired documents

        Returns:
            List of published documents
        """
        filters = [{"field": "IsPublished", "op": "eq", "value": "true"}]

        if document_type is not None:
            filters.append(
                {"field": "DocumentType", "op": "eq", "value": str(document_type)}
            )

        if folder_id is not None:
            filters.append({"field": "FolderID", "op": "eq", "value": str(folder_id)})

        if exclude_expired:
            today = datetime.now().date().isoformat()
            filters.append(
                [
                    {"field": "ExpirationDate", "op": "gt", "value": today},
                    {
                        "field": "ExpirationDate",
                        "op": "eq",
                        "value": "",
                    },  # No expiration
                ]
            )

        return self.query_all(filters=filters)

    def get_documents_by_type(
        self,
        document_type: int,
        published_only: bool = True,
    ) -> EntityList:
        """
        Get documents filtered by type.

        Args:
            document_type: Document type ID
            published_only: Whether to include only published documents

        Returns:
            List of documents of specified type
        """
        filters = [{"field": "DocumentType", "op": "eq", "value": str(document_type)}]

        if published_only:
            filters.append({"field": "IsPublished", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_documents_by_folder(
        self,
        folder_id: int,
        published_only: bool = True,
        include_subfolders: bool = False,
    ) -> EntityList:
        """
        Get documents in a specific folder.

        Args:
            folder_id: Folder ID
            published_only: Whether to include only published documents
            include_subfolders: Whether to include documents from subfolders

        Returns:
            List of documents in the folder
        """
        filters = [{"field": "FolderID", "op": "eq", "value": str(folder_id)}]

        if published_only:
            filters.append({"field": "IsPublished", "op": "eq", "value": "true"})

        documents = self.query_all(filters=filters)

        # If including subfolders, we'd need to recursively get subfolder documents
        # This would require additional folder hierarchy queries
        if include_subfolders:
            self.logger.warning(
                "Subfolder inclusion requires additional folder queries"
            )

        return documents

    def search_documents_by_content(
        self,
        search_term: str,
        document_type: Optional[int] = None,
        published_only: bool = True,
    ) -> EntityList:
        """
        Search documents by title or description content.

        Args:
            search_term: Term to search for
            document_type: Optional document type filter
            published_only: Whether to search only published documents

        Returns:
            List of matching documents
        """
        # Search in both title and description
        title_filters = [{"field": "Title", "op": "contains", "value": search_term}]
        desc_filters = [
            {"field": "Description", "op": "contains", "value": search_term}
        ]

        if published_only:
            published_filter = {"field": "IsPublished", "op": "eq", "value": "true"}
            title_filters.append(published_filter)
            desc_filters.append(published_filter)

        if document_type is not None:
            type_filter = {
                "field": "DocumentType",
                "op": "eq",
                "value": str(document_type),
            }
            title_filters.append(type_filter)
            desc_filters.append(type_filter)

        title_matches = self.query_all(filters=title_filters)
        desc_matches = self.query_all(filters=desc_filters)

        # Combine and deduplicate results
        all_matches = {}
        for doc in title_matches + desc_matches:
            all_matches[doc["id"]] = doc

        return list(all_matches.values())

    def get_expiring_documents(
        self, days_ahead: int = 30, document_type: Optional[int] = None
    ) -> EntityList:
        """
        Get documents that will expire within specified timeframe.

        Args:
            days_ahead: Number of days ahead to check
            document_type: Optional document type filter

        Returns:
            List of expiring documents
        """
        future_date = (datetime.now() + timedelta(days=days_ahead)).date().isoformat()
        today = datetime.now().date().isoformat()

        filters = [
            {"field": "ExpirationDate", "op": "gte", "value": today},
            {"field": "ExpirationDate", "op": "lte", "value": future_date},
            {"field": "IsPublished", "op": "eq", "value": "true"},
        ]

        if document_type is not None:
            filters.append(
                {"field": "DocumentType", "op": "eq", "value": str(document_type)}
            )

        return self.query_all(filters=filters)

    def get_expired_documents(
        self, days_back: int = 7, document_type: Optional[int] = None
    ) -> EntityList:
        """
        Get documents that have recently expired.

        Args:
            days_back: Number of days back to check
            document_type: Optional document type filter

        Returns:
            List of recently expired documents
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).date().isoformat()
        today = datetime.now().date().isoformat()

        filters = [
            {"field": "ExpirationDate", "op": "lt", "value": today},
            {"field": "ExpirationDate", "op": "gte", "value": cutoff_date},
        ]

        if document_type is not None:
            filters.append(
                {"field": "DocumentType", "op": "eq", "value": str(document_type)}
            )

        return self.query_all(filters=filters)

    def publish_document(
        self,
        document_id: int,
        publish_date: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Publish a document, making it available.

        Args:
            document_id: Document ID to publish
            publish_date: Optional publish date (defaults to today)

        Returns:
            Updated document data
        """
        update_data = {"IsPublished": True}

        if publish_date:
            update_data["PublishDate"] = publish_date
        else:
            update_data["PublishDate"] = datetime.now().date().isoformat()

        return self.update_by_id(document_id, update_data)

    def unpublish_document(self, document_id: int) -> Optional[EntityDict]:
        """
        Unpublish a document, making it unavailable.

        Args:
            document_id: Document ID to unpublish

        Returns:
            Updated document data
        """
        return self.update_by_id(document_id, {"IsPublished": False})

    def extend_document_expiration(
        self,
        document_id: int,
        new_expiration_date: str,
        reason: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Extend the expiration date of a document.

        Args:
            document_id: Document ID
            new_expiration_date: New expiration date (ISO format)
            reason: Optional reason for extension

        Returns:
            Updated document data
        """
        update_data = {"ExpirationDate": new_expiration_date}

        # If there's a reason, add it to description or a notes field
        if reason:
            current_doc = self.get(document_id)
            if current_doc:
                existing_desc = current_doc.get("Description", "")
                timestamp = datetime.now().strftime("%Y-%m-%d")
                extension_note = f"\n\n[{timestamp}] Expiration extended to {new_expiration_date}. Reason: {reason}"
                update_data["Description"] = existing_desc + extension_note

        return self.update_by_id(document_id, update_data)

    def create_document_version(
        self,
        original_document_id: int,
        new_title: Optional[str] = None,
        new_description: Optional[str] = None,
        version_notes: Optional[str] = None,
    ) -> EntityDict:
        """
        Create a new version of an existing document.

        Args:
            original_document_id: ID of original document
            new_title: Optional new title (defaults to original + version)
            new_description: Optional new description
            version_notes: Optional notes about this version

        Returns:
            Created document version data
        """
        original_doc = self.get(original_document_id)
        if not original_doc:
            raise ValueError(f"Original document {original_document_id} not found")

        # Prepare new document data
        new_doc_data = {
            "Title": new_title or f"{original_doc.get('Title', 'Document')} v2",
            "Description": new_description or original_doc.get("Description", ""),
            "DocumentType": original_doc.get("DocumentType"),
            "FolderID": original_doc.get("FolderID"),
            "IsPublished": False,  # New versions start unpublished
            "ParentDocumentID": original_document_id,  # If this field exists
        }

        if version_notes:
            new_doc_data["Description"] += f"\n\nVersion Notes: {version_notes}"

        # Copy other relevant fields
        for field in ["Keywords", "Category", "AccessLevel"]:
            if field in original_doc:
                new_doc_data[field] = original_doc[field]

        return self.create(new_doc_data)

    def get_document_versions(self, parent_document_id: int) -> EntityList:
        """
        Get all versions of a document.

        Args:
            parent_document_id: ID of the parent document

        Returns:
            List of document versions
        """
        filters = [
            {"field": "ParentDocumentID", "op": "eq", "value": str(parent_document_id)}
        ]
        return self.query_all(filters=filters)

    def get_document_statistics(
        self, folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics about documents.

        Args:
            folder_id: Optional folder to limit statistics to

        Returns:
            Dictionary with document statistics
        """
        filters = []
        if folder_id:
            filters = [{"field": "FolderID", "op": "eq", "value": str(folder_id)}]

        documents = self.query_all(filters=filters) if filters else self.query_all()

        stats = {
            "total_documents": len(documents),
            "published_documents": 0,
            "unpublished_documents": 0,
            "expired_documents": 0,
            "expiring_soon": 0,  # Within 30 days
            "by_document_type": {},
            "by_folder": {},
            "without_expiration": 0,
            "creation_dates": [],
        }

        today = datetime.now().date()
        thirty_days_future = today + timedelta(days=30)

        for doc in documents:
            # Publication status
            if doc.get("IsPublished", False):
                stats["published_documents"] += 1
            else:
                stats["unpublished_documents"] += 1

            # Expiration analysis
            expiration_str = doc.get("ExpirationDate")
            if expiration_str:
                try:
                    expiration_date = datetime.fromisoformat(expiration_str).date()
                    if expiration_date < today:
                        stats["expired_documents"] += 1
                    elif expiration_date <= thirty_days_future:
                        stats["expiring_soon"] += 1
                except (ValueError, TypeError):
                    pass
            else:
                stats["without_expiration"] += 1

            # Document type distribution
            doc_type = doc.get("DocumentType", "unknown")
            if doc_type not in stats["by_document_type"]:
                stats["by_document_type"][doc_type] = 0
            stats["by_document_type"][doc_type] += 1

            # Folder distribution
            folder = doc.get("FolderID", "root")
            if folder not in stats["by_folder"]:
                stats["by_folder"][folder] = 0
            stats["by_folder"][folder] += 1

            # Creation date tracking
            create_date_str = doc.get("CreateDate")
            if create_date_str:
                stats["creation_dates"].append(create_date_str)

        # Calculate creation trends
        if stats["creation_dates"]:
            stats["creation_dates"].sort()
            stats["oldest_document"] = stats["creation_dates"][0]
            stats["newest_document"] = stats["creation_dates"][-1]

        # Remove the raw dates from output
        del stats["creation_dates"]

        return stats

    def bulk_update_expiration_dates(
        self,
        document_ids: List[int],
        new_expiration_date: str,
    ) -> Dict[str, Any]:
        """
        Update expiration dates for multiple documents.

        Args:
            document_ids: List of document IDs to update
            new_expiration_date: New expiration date for all documents

        Returns:
            Dictionary with update results
        """
        results = {
            "total_requested": len(document_ids),
            "successful_updates": [],
            "failed_updates": [],
        }

        for doc_id in document_ids:
            try:
                updated_doc = self.update_by_id(
                    doc_id, {"ExpirationDate": new_expiration_date}
                )
                if updated_doc:
                    results["successful_updates"].append(doc_id)
                else:
                    results["failed_updates"].append(
                        {"document_id": doc_id, "error": "Update returned no data"}
                    )
            except Exception as e:
                results["failed_updates"].append(
                    {"document_id": doc_id, "error": str(e)}
                )

        return results

    def archive_old_documents(
        self,
        days_old: int = 365,
        document_types: Optional[List[int]] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Archive documents older than specified days.

        Args:
            days_old: Number of days to consider "old"
            document_types: Optional list of document types to include
            dry_run: If True, only identify documents without archiving

        Returns:
            Dictionary with archival results
        """
        cutoff_date = (datetime.now() - timedelta(days=days_old)).date().isoformat()

        filters = [{"field": "CreateDate", "op": "lt", "value": cutoff_date}]

        if document_types:
            if len(document_types) == 1:
                filters.append(
                    {
                        "field": "DocumentType",
                        "op": "eq",
                        "value": str(document_types[0]),
                    }
                )
            else:
                filters.append(
                    {
                        "field": "DocumentType",
                        "op": "in",
                        "value": [str(dt) for dt in document_types],
                    }
                )

        old_documents = self.query_all(filters=filters)

        results = {
            "total_old_documents": len(old_documents),
            "cutoff_date": cutoff_date,
            "archived_documents": [],
            "failed_archives": [],
            "dry_run": dry_run,
        }

        if not dry_run:
            for doc in old_documents:
                try:
                    # Archive by unpublishing and adding archive note
                    archive_note = f"\n\n[ARCHIVED {datetime.now().date()}] Document archived due to age (>{days_old} days)"

                    updated_doc = self.update_by_id(
                        int(doc["id"]),
                        {
                            "IsPublished": False,
                            "Description": doc.get("Description", "") + archive_note,
                        },
                    )

                    if updated_doc:
                        results["archived_documents"].append(int(doc["id"]))
                    else:
                        results["failed_archives"].append(int(doc["id"]))

                except Exception as e:
                    results["failed_archives"].append(
                        {"document_id": int(doc["id"]), "error": str(e)}
                    )

        return results
