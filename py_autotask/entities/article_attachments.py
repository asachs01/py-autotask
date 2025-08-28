"""
Article Attachments entity for Autotask API.

This module provides the ArticleAttachmentsEntity class for managing
attachments associated with knowledge base articles.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..types import CreateResponse, QueryFilter, UpdateResponse
from .base import BaseEntity


class ArticleAttachmentsEntity(BaseEntity):
    """
    Entity for managing Autotask Article Attachments.

    Article attachments provide file and document management capabilities
    for knowledge base articles, supporting documentation and reference materials.
    """

    def __init__(self, client, entity_name="ArticleAttachments"):
        """Initialize the Article Attachments entity."""
        super().__init__(client, entity_name)

    def create(self, attachment_data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new article attachment.

        Args:
            attachment_data: Dictionary containing attachment information
                Required fields:
                - articleId: ID of the article
                - fileName: Name of the file
                - fileContent: Base64 encoded file content or file path
                Optional fields:
                - title: Attachment title
                - description: Attachment description
                - contentType: MIME type of the file
                - fileSize: Size of the file in bytes

        Returns:
            CreateResponse: Response containing created attachment data

        Raises:
            ValidationError: If required fields are missing or invalid
            AutotaskAPIError: If the API request fails
        """
        required_fields = ["articleId", "fileName", "fileContent"]
        self._validate_required_fields(attachment_data, required_fields)

        # Set default values
        if "uploadDateTime" not in attachment_data:
            attachment_data["uploadDateTime"] = datetime.now().isoformat()

        return self._create(attachment_data)

    def get(self, attachment_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve an article attachment by ID.

        Args:
            attachment_id: The attachment ID

        Returns:
            Dictionary containing attachment data, or None if not found

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._get(attachment_id)

    def update(self, attachment_id: int, update_data: Dict[str, Any]) -> UpdateResponse:
        """
        Update an existing article attachment.

        Args:
            attachment_id: The attachment ID to update
            update_data: Dictionary containing fields to update

        Returns:
            UpdateResponse: Response containing updated attachment data

        Raises:
            ValidationError: If the update data is invalid
            AutotaskAPIError: If the API request fails
        """
        # Update last modified timestamp
        update_data["lastModifiedDate"] = datetime.now().isoformat()

        return self._update(attachment_id, update_data)

    def delete(self, attachment_id: int) -> bool:
        """
        Delete an article attachment.

        Args:
            attachment_id: The attachment ID to delete

        Returns:
            True if deletion was successful

        Raises:
            AutotaskAPIError: If the API request fails
        """
        return self._delete(attachment_id)

    def get_by_article(
        self,
        article_id: int,
        include_inactive: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific article.

        Args:
            article_id: ID of the article
            include_inactive: Whether to include inactive attachments
            limit: Maximum number of attachments to return

        Returns:
            List of attachments for the article
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        if not include_inactive:
            filters.append(QueryFilter(field="isActive", op="eq", value=True))

        attachments = self.query(filters=filters, max_records=limit)

        # Sort by upload date (newest first)
        return sorted(
            attachments, key=lambda x: x.get("uploadDateTime", ""), reverse=True
        )

    def upload_file(
        self,
        article_id: int,
        file_path: Union[str, Path],
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> CreateResponse:
        """
        Upload a file as an article attachment.

        Args:
            article_id: ID of the article
            file_path: Path to the file to upload
            title: Optional attachment title
            description: Optional attachment description

        Returns:
            Created attachment data

        Raises:
            ValidationError: If file doesn't exist or is invalid
            AutotaskAPIError: If the upload fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Read file content and encode
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Determine content type
        content_type = self._get_content_type(file_path.suffix)

        attachment_data = {
            "articleId": article_id,
            "fileName": file_path.name,
            "fileContent": file_content,
            "contentType": content_type,
            "fileSize": len(file_content),
            "title": title or file_path.stem,
            "isActive": True,
        }

        if description:
            attachment_data["description"] = description

        return self.create(attachment_data)

    def download_file(
        self, attachment_id: int, output_path: Optional[Union[str, Path]] = None
    ) -> bytes:
        """
        Download an article attachment file.

        Args:
            attachment_id: ID of the attachment to download
            output_path: Optional path to save the file

        Returns:
            File data as bytes

        Raises:
            AutotaskAPIError: If the download fails
        """
        attachment = self.get(attachment_id)
        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found")

        file_content = attachment.get("fileContent")
        if not file_content:
            raise ValueError(
                f"No file content available for attachment {attachment_id}"
            )

        # Decode file content if it's base64 encoded
        if isinstance(file_content, str):
            import base64

            file_data = base64.b64decode(file_content)
        else:
            file_data = file_content

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(file_data)

            self.logger.info(f"Downloaded attachment {attachment_id} to {output_path}")

        return file_data

    def get_by_file_type(
        self, article_id: int, file_extension: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get article attachments by file type/extension.

        Args:
            article_id: ID of the article
            file_extension: File extension to filter by (e.g., '.pdf', '.docx')
            limit: Maximum number of attachments to return

        Returns:
            List of attachments with the specified file type
        """
        filters = [
            QueryFilter(field="articleId", op="eq", value=article_id),
            QueryFilter(field="fileName", op="contains", value=file_extension),
            QueryFilter(field="isActive", op="eq", value=True),
        ]

        return self.query(filters=filters, max_records=limit)

    def update_attachment_metadata(
        self,
        attachment_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> UpdateResponse:
        """
        Update attachment metadata without changing the file.

        Args:
            attachment_id: ID of the attachment
            title: New title for the attachment
            description: New description for the attachment
            tags: List of tags to associate with the attachment

        Returns:
            Updated attachment data
        """
        update_data = {}

        if title:
            update_data["title"] = title

        if description:
            update_data["description"] = description

        if tags:
            update_data["tags"] = ",".join(tags)

        if update_data:
            return self.update(attachment_id, update_data)

        return {"message": "No updates provided"}

    def bulk_delete_by_article(
        self, article_id: int, file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Delete multiple attachments for an article.

        Args:
            article_id: ID of the article
            file_extensions: Optional list of file extensions to delete

        Returns:
            Dictionary with deletion results
        """
        filters = [QueryFilter(field="articleId", op="eq", value=article_id)]

        attachments = self.query(filters=filters)
        deleted_count = 0
        errors = []

        for attachment in attachments:
            attachment_id = attachment.get("id")
            file_name = attachment.get("fileName", "")

            # Filter by file extension if specified
            if file_extensions:
                file_ext = Path(file_name).suffix.lower()
                if file_ext not in [ext.lower() for ext in file_extensions]:
                    continue

            try:
                if self.delete(attachment_id):
                    deleted_count += 1
                    self.logger.info(f"Deleted attachment {attachment_id}: {file_name}")
            except Exception as e:
                error_msg = f"Failed to delete attachment {attachment_id}: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        return {
            "deleted_count": deleted_count,
            "total_attachments": len(attachments),
            "errors": errors,
            "success": len(errors) == 0,
        }

    def get_attachment_statistics(
        self, article_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about article attachments.

        Args:
            article_ids: Optional list of article IDs to analyze

        Returns:
            Dictionary with attachment statistics
        """
        filters = []

        if article_ids:
            filters.append(QueryFilter(field="articleId", op="in", value=article_ids))

        attachments = self.query(filters=filters)

        stats = {
            "total_attachments": len(attachments),
            "by_article": {},
            "by_file_type": {},
            "total_size_bytes": 0,
            "avg_size_bytes": 0,
            "active_attachments": 0,
            "inactive_attachments": 0,
        }

        total_sizes = []

        for attachment in attachments:
            article_id = attachment.get("articleId")
            file_name = attachment.get("fileName", "")
            file_size = attachment.get("fileSize", 0)
            is_active = attachment.get("isActive", True)

            # Count by article
            stats["by_article"][article_id] = stats["by_article"].get(article_id, 0) + 1

            # Count by file type
            file_ext = Path(file_name).suffix.lower() or "no_extension"
            stats["by_file_type"][file_ext] = stats["by_file_type"].get(file_ext, 0) + 1

            # Size statistics
            if file_size:
                stats["total_size_bytes"] += file_size
                total_sizes.append(file_size)

            # Active/inactive count
            if is_active:
                stats["active_attachments"] += 1
            else:
                stats["inactive_attachments"] += 1

        # Calculate average size
        if total_sizes:
            stats["avg_size_bytes"] = sum(total_sizes) / len(total_sizes)

        return stats

    def _get_content_type(self, file_extension: str) -> str:
        """
        Get MIME content type from file extension.

        Args:
            file_extension: File extension including the dot

        Returns:
            MIME content type
        """
        content_types = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".txt": "text/plain",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".zip": "application/zip",
        }

        return content_types.get(file_extension.lower(), "application/octet-stream")
