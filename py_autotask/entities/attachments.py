"""
Attachment handling for Autotask entities.

This module provides functionality for uploading, downloading, and managing
file attachments for Autotask entities like tickets, projects, and contacts.
"""

import mimetypes
from pathlib import Path
from typing import List, Optional, Union

import requests

from ..exceptions import (
    AutotaskConnectionError,
    AutotaskTimeoutError,
    AutotaskValidationError,
)
from ..types import AttachmentData
from .base import BaseEntity


class AttachmentsEntity(BaseEntity):
    """
    Entity manager for file attachments.

    Handles uploading, downloading, and managing attachments for various
    Autotask entities including tickets, projects, and contacts.
    """

    def __init__(self, client, entity_name="Attachments"):
        """Initialize the attachments entity manager."""
        super().__init__(client, entity_name)

    def upload_file(
        self,
        parent_type: str,
        parent_id: int,
        file_path: Union[str, Path],
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AttachmentData:
        """
        Upload a file attachment to an entity.

        Args:
            parent_type: Parent entity type (e.g., 'Ticket', 'Project', 'Contact')
            parent_id: ID of the parent entity
            file_path: Path to the file to upload
            title: Optional title for the attachment
            description: Optional description

        Returns:
            Attachment data with ID and metadata

        Example:
            # Upload a file to a ticket
            attachment = client.attachments.upload_file(
                parent_type="Ticket",
                parent_id=12345,
                file_path="/path/to/screenshot.png",
                title="Error Screenshot",
                description="Screenshot showing the error state"
            )
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise AutotaskValidationError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise AutotaskValidationError(f"Path is not a file: {file_path}")

        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        # Prepare attachment metadata
        attachment_data = {
            "parentType": parent_type,
            "parentId": parent_id,
            "title": title or file_path.name,
            "fileName": file_path.name,
            "fileSize": file_path.stat().st_size,
            "contentType": content_type,
        }

        if description:
            attachment_data["description"] = description

        try:
            with open(file_path, "rb") as file_data:
                # Upload the file
                url = f"{self.client.auth.api_url}/v1.0/Attachments"

                files = {"file": (file_path.name, file_data, content_type)}

                data = {"attachment": attachment_data}

                response = self.client.session.post(
                    url, files=files, data=data, timeout=self.client.config.timeout
                )

                response.raise_for_status()
                result = response.json()

                self.logger.info(f"Successfully uploaded attachment: {file_path.name}")
                return AttachmentData(**result.get("item", result))

        except requests.exceptions.Timeout:
            raise AutotaskTimeoutError(f"Upload timed out for file: {file_path.name}")
        except requests.exceptions.ConnectionError as e:
            raise AutotaskConnectionError(f"Upload failed for {file_path.name}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to upload {file_path.name}: {e}")
            raise

    def upload_from_data(
        self,
        parent_type: str,
        parent_id: int,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AttachmentData:
        """
        Upload file data as an attachment.

        Args:
            parent_type: Parent entity type
            parent_id: ID of the parent entity
            file_data: Raw file data as bytes
            filename: Name for the file
            content_type: MIME type (auto-detected if None)
            title: Optional title for the attachment
            description: Optional description

        Returns:
            Attachment data with ID and metadata
        """
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"

        attachment_data = {
            "parentType": parent_type,
            "parentId": parent_id,
            "title": title or filename,
            "fileName": filename,
            "fileSize": len(file_data),
            "contentType": content_type,
        }

        if description:
            attachment_data["description"] = description

        try:
            url = f"{self.client.auth.api_url}/v1.0/Attachments"

            files = {"file": (filename, file_data, content_type)}

            data = {"attachment": attachment_data}

            response = self.client.session.post(
                url, files=files, data=data, timeout=self.client.config.timeout
            )

            response.raise_for_status()
            result = response.json()

            self.logger.info(f"Successfully uploaded attachment from data: {filename}")
            return AttachmentData(**result.get("item", result))

        except Exception as e:
            self.logger.error(f"Failed to upload data as {filename}: {e}")
            raise

    def download_file(
        self, attachment_id: int, output_path: Optional[Union[str, Path]] = None
    ) -> bytes:
        """
        Download an attachment file.

        Args:
            attachment_id: ID of the attachment to download
            output_path: Optional path to save the file (if None, returns bytes)

        Returns:
            File data as bytes
        """
        url = f"{self.client.auth.api_url}/v1.0/Attachments/{attachment_id}/download"

        try:
            response = self.client.session.get(url, timeout=self.client.config.timeout)

            response.raise_for_status()
            file_data = response.content

            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(file_data)

                self.logger.info(
                    f"Downloaded attachment {attachment_id} to {output_path}"
                )

            return file_data

        except Exception as e:
            self.logger.error(f"Failed to download attachment {attachment_id}: {e}")
            raise

    def get_attachments_for_entity(
        self, parent_type: str, parent_id: int
    ) -> List[AttachmentData]:
        """
        Get all attachments for a specific entity.

        Args:
            parent_type: Parent entity type
            parent_id: ID of the parent entity

        Returns:
            List of attachment metadata
        """
        query = {
            "filter": [
                {"op": "eq", "field": "parentType", "value": parent_type},
                {"op": "eq", "field": "parentId", "value": parent_id},
            ]
        }

        response = self.query(query)
        return [AttachmentData(**item) for item in response.items]

    def delete_attachment(self, attachment_id: int) -> bool:
        """
        Delete an attachment.

        Args:
            attachment_id: ID of the attachment to delete

        Returns:
            True if successful
        """
        return self.delete(attachment_id)

    def get_attachment_info(self, attachment_id: int) -> Optional[AttachmentData]:
        """
        Get attachment metadata without downloading the file.

        Args:
            attachment_id: ID of the attachment

        Returns:
            Attachment metadata or None if not found
        """
        data = self.get(attachment_id)
        return AttachmentData(**data) if data else None

    def batch_upload(
        self,
        parent_type: str,
        parent_id: int,
        file_paths: List[Union[str, Path]],
        batch_size: int = 10,
    ) -> List[AttachmentData]:
        """
        Upload multiple files as attachments.

        Args:
            parent_type: Parent entity type
            parent_id: ID of the parent entity
            file_paths: List of file paths to upload
            batch_size: Number of files to upload concurrently

        Returns:
            List of attachment data for successfully uploaded files
        """
        results = []
        total_batches = (len(file_paths) + batch_size - 1) // batch_size

        self.logger.info(f"Starting batch upload of {len(file_paths)} files")

        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            self.logger.info(
                f"Processing upload batch {batch_num}/{total_batches} ({len(batch)} files)"
            )

            for file_path in batch:
                try:
                    result = self.upload_file(parent_type, parent_id, file_path)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to upload {file_path}: {e}")
                    # Continue with other files
                    continue

        self.logger.info(
            f"Batch upload complete: {len(results)}/{len(file_paths)} files uploaded"
        )
        return results
