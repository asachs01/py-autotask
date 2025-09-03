"""
DocumentAttachments Entity for py-autotask

This module provides the DocumentAttachmentsEntity class for managing file
attachments to documents in Autotask. Document Attachments handle file storage,
retrieval, and management for various document types.
"""

import base64
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class DocumentAttachmentsEntity(BaseEntity):
    """
    Manages Autotask DocumentAttachments - file attachments for documents.

    Document Attachments handle file storage, retrieval, and management for
    various document types in Autotask. They support multiple file formats,
    version control, and secure access to attached files.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "DocumentAttachments"

    def create_document_attachment(
        self,
        document_id: int,
        file_name: str,
        file_data: Union[bytes, str],
        content_type: str,
        file_size: Optional[int] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new document attachment.

        Args:
            document_id: ID of the document to attach to
            file_name: Name of the file
            file_data: File content (bytes or base64 string)
            content_type: MIME type of the file
            file_size: Size of the file in bytes
            description: Optional description of the attachment
            **kwargs: Additional fields for the attachment

        Returns:
            Create response with new attachment ID
        """
        # Convert bytes to base64 if necessary
        if isinstance(file_data, bytes):
            file_data_b64 = base64.b64encode(file_data).decode("utf-8")
        else:
            file_data_b64 = file_data

        attachment_data = {
            "documentID": document_id,
            "fileName": file_name,
            "fileData": file_data_b64,
            "contentType": content_type,
            "uploadDate": datetime.now().isoformat(),
            **kwargs,
        }

        if file_size is not None:
            attachment_data["fileSize"] = file_size
        if description:
            attachment_data["description"] = description

        return self.create(attachment_data)

    def get_document_attachments(
        self, document_id: int, include_file_data: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get attachments for a specific document.

        Args:
            document_id: ID of the document
            include_file_data: Whether to include file content in response

        Returns:
            List of attachments for the document
        """
        filters = [{"field": "documentID", "op": "eq", "value": str(document_id)}]

        include_fields = None
        if not include_file_data:
            # Exclude file data to reduce response size
            include_fields = [
                "id",
                "documentID",
                "fileName",
                "contentType",
                "fileSize",
                "description",
                "uploadDate",
                "createdBy",
            ]

        return self.query(filters=filters, include_fields=include_fields).items

    def download_attachment(self, attachment_id: int) -> Dict[str, Any]:
        """
        Download an attachment's file content.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Attachment data including file content
        """
        attachment = self.get(attachment_id)

        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found")

        # Decode base64 file data
        file_data_b64 = attachment.get("fileData", "")
        try:
            file_content = base64.b64decode(file_data_b64)
        except Exception:
            file_content = file_data_b64.encode("utf-8")

        return {
            "attachment_id": attachment_id,
            "document_id": attachment["documentID"],
            "file_name": attachment["fileName"],
            "content_type": attachment["contentType"],
            "file_size": attachment.get("fileSize", len(file_content)),
            "file_content": file_content,
            "download_date": datetime.now().isoformat(),
        }

    def get_attachments_by_file_type(
        self, file_extensions: List[str], document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get attachments by file type/extension.

        Args:
            file_extensions: List of file extensions to filter by (e.g., ['pdf', 'docx'])
            document_ids: Optional list of document IDs to limit search

        Returns:
            List of attachments matching file types
        """
        # Build filter for file extensions
        extension_filters = []
        for ext in file_extensions:
            extension_filters.append(
                {"field": "fileName", "op": "endswith", "value": f".{ext.lower()}"}
            )

        filters = []
        if len(extension_filters) == 1:
            filters.append(extension_filters[0])
        elif len(extension_filters) > 1:
            # Use OR logic for multiple extensions
            filters.append(
                {
                    "field": "fileName",
                    "op": "regex",
                    "value": f"\\.({'|'.join(file_extensions)})$",
                }
            )

        if document_ids:
            document_filter = {
                "field": "documentID",
                "op": "in",
                "value": [str(doc_id) for doc_id in document_ids],
            }
            filters.append(document_filter)

        return self.query(filters=filters).items

    def get_large_attachments(
        self, min_size_mb: float = 10.0, document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get attachments larger than specified size.

        Args:
            min_size_mb: Minimum file size in MB
            document_ids: Optional list of document IDs to limit search

        Returns:
            List of large attachments
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)

        filters = [{"field": "fileSize", "op": "gte", "value": str(min_size_bytes)}]

        if document_ids:
            document_filter = {
                "field": "documentID",
                "op": "in",
                "value": [str(doc_id) for doc_id in document_ids],
            }
            filters.append(document_filter)

        return self.query(filters=filters).items

    def update_attachment_metadata(
        self,
        attachment_id: int,
        new_file_name: Optional[str] = None,
        new_description: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Update attachment metadata without changing file content.

        Args:
            attachment_id: ID of the attachment
            new_file_name: Optional new file name
            new_description: Optional new description
            **kwargs: Additional fields to update

        Returns:
            Updated attachment data
        """
        update_data = {"id": attachment_id, **kwargs}

        if new_file_name:
            update_data["fileName"] = new_file_name
        if new_description is not None:
            update_data["description"] = new_description

        return self.update(update_data)

    def replace_attachment_file(
        self,
        attachment_id: int,
        new_file_data: Union[bytes, str],
        new_content_type: Optional[str] = None,
        new_file_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Replace the file content of an existing attachment.

        Args:
            attachment_id: ID of the attachment
            new_file_data: New file content (bytes or base64 string)
            new_content_type: Optional new MIME type
            new_file_size: Optional new file size

        Returns:
            Updated attachment data
        """
        # Convert bytes to base64 if necessary
        if isinstance(new_file_data, bytes):
            file_data_b64 = base64.b64encode(new_file_data).decode("utf-8")
        else:
            file_data_b64 = new_file_data

        update_data = {
            "id": attachment_id,
            "fileData": file_data_b64,
            "lastModifiedDate": datetime.now().isoformat(),
        }

        if new_content_type:
            update_data["contentType"] = new_content_type
        if new_file_size is not None:
            update_data["fileSize"] = new_file_size

        return self.update(update_data)

    def bulk_upload_attachments(
        self, document_id: int, file_uploads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Upload multiple attachments to a document in bulk.

        Args:
            document_id: ID of the document
            file_uploads: List of file upload data
                Each should contain: file_name, file_data, content_type, description

        Returns:
            Summary of bulk upload operation
        """
        results = []

        for file_upload in file_uploads:
            try:
                upload_data = {"document_id": document_id, **file_upload}

                create_result = self.create_document_attachment(**upload_data)

                results.append(
                    {
                        "file_name": file_upload["file_name"],
                        "success": True,
                        "attachment_id": create_result["item_id"],
                        "file_size": file_upload.get("file_size", 0),
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "file_name": file_upload.get("file_name", "unknown"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        total_size = sum(r.get("file_size", 0) for r in successful)

        return {
            "document_id": document_id,
            "upload_summary": {
                "total_files": len(file_uploads),
                "successful_uploads": len(successful),
                "failed_uploads": len(failed),
                "total_size_uploaded": total_size,
            },
            "upload_date": datetime.now().isoformat(),
            "results": results,
        }

    def get_attachment_usage_statistics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get attachment usage statistics and analytics.

        Args:
            date_from: Optional start date for analysis
            date_to: Optional end date for analysis

        Returns:
            Attachment usage statistics
        """
        filters = []

        if date_from:
            filters.append(
                {"field": "uploadDate", "op": "gte", "value": date_from.isoformat()}
            )
        if date_to:
            filters.append(
                {"field": "uploadDate", "op": "lte", "value": date_to.isoformat()}
            )

        attachments = self.query(filters=filters).items if filters else self.query_all()

        # Calculate statistics
        total_count = len(attachments)
        total_size = sum(int(att.get("fileSize", 0)) for att in attachments)

        # Group by file type
        file_type_stats = {}
        for attachment in attachments:
            content_type = attachment.get("contentType", "unknown")
            if content_type not in file_type_stats:
                file_type_stats[content_type] = {"count": 0, "total_size": 0}

            file_type_stats[content_type]["count"] += 1
            file_type_stats[content_type]["total_size"] += int(
                attachment.get("fileSize", 0)
            )

        # Get largest and smallest files
        files_with_size = [att for att in attachments if att.get("fileSize")]
        largest_file = (
            max(files_with_size, key=lambda x: int(x["fileSize"]))
            if files_with_size
            else None
        )
        smallest_file = (
            min(files_with_size, key=lambda x: int(x["fileSize"]))
            if files_with_size
            else None
        )

        return {
            "analysis_period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "overall_statistics": {
                "total_attachments": total_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "average_size_bytes": (
                    round(total_size / total_count, 2) if total_count > 0 else 0
                ),
            },
            "file_type_breakdown": file_type_stats,
            "size_analysis": {
                "largest_file": (
                    {
                        "attachment_id": largest_file["id"],
                        "file_name": largest_file["fileName"],
                        "size_bytes": int(largest_file["fileSize"]),
                    }
                    if largest_file
                    else None
                ),
                "smallest_file": (
                    {
                        "attachment_id": smallest_file["id"],
                        "file_name": smallest_file["fileName"],
                        "size_bytes": int(smallest_file["fileSize"]),
                    }
                    if smallest_file
                    else None
                ),
            },
        }

    def search_attachments_by_content(
        self, search_terms: List[str], document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search attachments by filename and description content.

        Args:
            search_terms: List of terms to search for
            document_ids: Optional list of document IDs to limit search

        Returns:
            List of matching attachments
        """
        filters = []

        # Build search filters for filename and description
        search_filters = []
        for term in search_terms:
            search_filters.extend(
                [
                    {"field": "fileName", "op": "contains", "value": term},
                    {"field": "description", "op": "contains", "value": term},
                ]
            )

        if search_filters:
            filters.extend(search_filters)

        if document_ids:
            document_filter = {
                "field": "documentID",
                "op": "in",
                "value": [str(doc_id) for doc_id in document_ids],
            }
            filters.append(document_filter)

        return self.query(filters=filters).items

    def move_attachments_between_documents(
        self, attachment_ids: List[int], target_document_id: int
    ) -> Dict[str, Any]:
        """
        Move attachments from one document to another.

        Args:
            attachment_ids: List of attachment IDs to move
            target_document_id: ID of the target document

        Returns:
            Summary of move operation
        """
        results = []

        for attachment_id in attachment_ids:
            try:
                # Get current attachment details
                attachment = self.get(attachment_id)
                if not attachment:
                    results.append(
                        {
                            "attachment_id": attachment_id,
                            "success": False,
                            "error": "Attachment not found",
                        }
                    )
                    continue

                # Update document ID
                updated_attachment = self.update(
                    {
                        "id": attachment_id,
                        "documentID": target_document_id,
                        "moveDate": datetime.now().isoformat(),
                        "previousDocumentID": attachment["documentID"],
                    }
                )

                results.append(
                    {
                        "attachment_id": attachment_id,
                        "file_name": attachment["fileName"],
                        "previous_document_id": attachment["documentID"],
                        "success": True,
                    }
                )

            except Exception as e:
                results.append(
                    {"attachment_id": attachment_id, "success": False, "error": str(e)}
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "target_document_id": target_document_id,
            "move_summary": {
                "total_attachments": len(attachment_ids),
                "successful_moves": len(successful),
                "failed_moves": len(failed),
            },
            "move_date": datetime.now().isoformat(),
            "results": results,
        }

    def create_attachment_version(
        self,
        original_attachment_id: int,
        new_file_data: Union[bytes, str],
        version_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new version of an existing attachment.

        Args:
            original_attachment_id: ID of the original attachment
            new_file_data: New file content for the version
            version_notes: Optional notes about this version

        Returns:
            Create response for the new version
        """
        original = self.get(original_attachment_id)

        if not original:
            raise ValueError(f"Original attachment {original_attachment_id} not found")

        # Create new attachment as version
        version_data = {
            "document_id": original["documentID"],
            "file_name": original["fileName"],
            "file_data": new_file_data,
            "content_type": original["contentType"],
            "description": original.get("description", ""),
            "parentAttachmentID": original_attachment_id,
            "isVersion": True,
            "versionNumber": self._get_next_version_number(original_attachment_id),
            "versionNotes": version_notes,
        }

        return self.create_document_attachment(**version_data)

    def _get_next_version_number(self, parent_attachment_id: int) -> int:
        """Get the next version number for an attachment."""
        # This would typically query for existing versions
        # For now, return a simple increment
        versions = self.query(
            filters=[
                {
                    "field": "parentAttachmentID",
                    "op": "eq",
                    "value": str(parent_attachment_id),
                }
            ]
        ).items

        return len(versions) + 2  # +2 because original is version 1

    def get_attachment_versions(
        self, parent_attachment_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all versions of an attachment.

        Args:
            parent_attachment_id: ID of the parent attachment

        Returns:
            List of attachment versions
        """
        # Get the original attachment
        original = self.get(parent_attachment_id)
        versions = [original] if original else []

        # Get version attachments
        version_attachments = self.query(
            filters=[
                {
                    "field": "parentAttachmentID",
                    "op": "eq",
                    "value": str(parent_attachment_id),
                }
            ]
        ).items

        versions.extend(version_attachments)

        # Sort by version number or upload date
        versions.sort(key=lambda x: x.get("versionNumber", 1))

        return versions
