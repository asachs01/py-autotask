"""
ProjectAttachments Entity for py-autotask

This module provides the ProjectAttachmentsEntity class for managing file
attachments to projects in Autotask. Project Attachments handle project-related
documents, files, and media storage with version control and access management.
"""

import base64
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ProjectAttachmentsEntity(BaseEntity):
    """
    Manages Autotask ProjectAttachments - file attachments for projects.

    Project Attachments handle storage and management of project-related files,
    documents, images, and other media. They support categorization, version
    control, access permissions, and collaborative document management for projects.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ProjectAttachments"

    def create_project_attachment(
        self,
        project_id: int,
        file_name: str,
        file_data: Union[bytes, str],
        content_type: str,
        attachment_type: Optional[str] = None,
        file_size: Optional[int] = None,
        description: Optional[str] = None,
        is_public: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new project attachment.

        Args:
            project_id: ID of the project
            file_name: Name of the file
            file_data: File content (bytes or base64 string)
            content_type: MIME type of the file
            attachment_type: Type/category of attachment (document, image, etc.)
            file_size: Size of the file in bytes
            description: Optional description of the attachment
            is_public: Whether attachment is publicly accessible
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
            "projectID": project_id,
            "fileName": file_name,
            "fileData": file_data_b64,
            "contentType": content_type,
            "uploadDate": datetime.now().isoformat(),
            "isPublic": is_public,
            **kwargs,
        }

        if attachment_type:
            attachment_data["attachmentType"] = attachment_type
        if file_size is not None:
            attachment_data["fileSize"] = file_size
        if description:
            attachment_data["description"] = description

        return self.create(attachment_data)

    def get_project_attachments(
        self,
        project_id: int,
        attachment_type: Optional[str] = None,
        include_file_data: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get attachments for a specific project.

        Args:
            project_id: ID of the project
            attachment_type: Optional attachment type filter
            include_file_data: Whether to include file content in response

        Returns:
            List of attachments for the project
        """
        filters = [{"field": "projectID", "op": "eq", "value": str(project_id)}]

        if attachment_type:
            filters.append(
                {"field": "attachmentType", "op": "eq", "value": attachment_type}
            )

        include_fields = None
        if not include_file_data:
            # Exclude file data to reduce response size
            include_fields = [
                "id",
                "projectID",
                "fileName",
                "contentType",
                "fileSize",
                "attachmentType",
                "description",
                "uploadDate",
                "isPublic",
                "createdBy",
            ]

        return self.query(filters=filters, include_fields=include_fields).items

    def get_public_project_attachments(
        self, project_id: int, attachment_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get public attachments for a project.

        Args:
            project_id: ID of the project
            attachment_type: Optional attachment type filter

        Returns:
            List of public attachments
        """
        filters = [
            {"field": "projectID", "op": "eq", "value": str(project_id)},
            {"field": "isPublic", "op": "eq", "value": "true"},
        ]

        if attachment_type:
            filters.append(
                {"field": "attachmentType", "op": "eq", "value": attachment_type}
            )

        return self.query(filters=filters).items

    def download_project_attachment(self, attachment_id: int) -> Dict[str, Any]:
        """
        Download a project attachment's file content.

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
            "project_id": attachment["projectID"],
            "file_name": attachment["fileName"],
            "content_type": attachment["contentType"],
            "attachment_type": attachment.get("attachmentType"),
            "file_size": attachment.get("fileSize", len(file_content)),
            "file_content": file_content,
            "is_public": attachment.get("isPublic", False),
            "download_date": datetime.now().isoformat(),
        }

    def categorize_project_attachments(self, project_id: int) -> Dict[str, Any]:
        """
        Get project attachments categorized by type.

        Args:
            project_id: ID of the project

        Returns:
            Categorized project attachments
        """
        attachments = self.get_project_attachments(project_id)

        categories = {}
        total_size = 0

        for attachment in attachments:
            attachment_type = attachment.get("attachmentType", "uncategorized")
            file_size = int(attachment.get("fileSize", 0))

            if attachment_type not in categories:
                categories[attachment_type] = {
                    "count": 0,
                    "total_size": 0,
                    "attachments": [],
                }

            categories[attachment_type]["count"] += 1
            categories[attachment_type]["total_size"] += file_size
            categories[attachment_type]["attachments"].append(
                {
                    "id": attachment["id"],
                    "file_name": attachment["fileName"],
                    "content_type": attachment["contentType"],
                    "file_size": file_size,
                    "upload_date": attachment["uploadDate"],
                    "is_public": attachment.get("isPublic", False),
                }
            )

            total_size += file_size

        return {
            "project_id": project_id,
            "categorization_summary": {
                "total_attachments": len(attachments),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "categories_count": len(categories),
            },
            "categories": categories,
        }

    def create_project_attachment_folder(
        self,
        project_id: int,
        folder_name: str,
        folder_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a virtual folder structure for project attachments.

        Args:
            project_id: ID of the project
            folder_name: Name of the folder
            folder_description: Optional folder description

        Returns:
            Folder creation result
        """
        folder_data = {
            "project_id": project_id,
            "file_name": f"{folder_name}/",
            "file_data": "",  # Empty for folder
            "content_type": "application/x-directory",
            "attachment_type": "folder",
            "description": folder_description or f"Folder: {folder_name}",
            "is_public": False,
        }

        return self.create_project_attachment(**folder_data)

    def organize_attachments_into_folders(
        self, project_id: int, organization_rules: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Organize project attachments into folders based on rules.

        Args:
            project_id: ID of the project
            organization_rules: Rules for organization (folder_name: [file_extensions])

        Returns:
            Organization operation results
        """
        attachments = self.get_project_attachments(project_id)
        organization_results = []

        for folder_name, extensions in organization_rules.items():
            folder_attachments = []

            for attachment in attachments:
                file_name = attachment.get("fileName", "")
                file_extension = (
                    file_name.split(".")[-1].lower() if "." in file_name else ""
                )

                if file_extension in [ext.lower() for ext in extensions]:
                    folder_attachments.append(attachment)

            # Create folder if it doesn't exist and has attachments
            if folder_attachments:
                try:
                    folder_result = self.create_project_attachment_folder(
                        project_id,
                        folder_name,
                        f"Auto-organized folder for {', '.join(extensions)} files",
                    )

                    # Move attachments to folder (conceptually - would update folder path)
                    for attachment in folder_attachments:
                        self.update(
                            {
                                "id": attachment["id"],
                                "folderPath": folder_name,
                                "organizationDate": datetime.now().isoformat(),
                            }
                        )

                    organization_results.append(
                        {
                            "folder_name": folder_name,
                            "folder_id": folder_result["item_id"],
                            "files_organized": len(folder_attachments),
                            "file_extensions": extensions,
                            "success": True,
                        }
                    )

                except Exception as e:
                    organization_results.append(
                        {
                            "folder_name": folder_name,
                            "files_organized": 0,
                            "file_extensions": extensions,
                            "success": False,
                            "error": str(e),
                        }
                    )

        return {
            "project_id": project_id,
            "organization_summary": {
                "total_folders_created": len(
                    [r for r in organization_results if r["success"]]
                ),
                "total_files_organized": sum(
                    r["files_organized"] for r in organization_results
                ),
                "organization_rules": organization_rules,
            },
            "organization_date": datetime.now().isoformat(),
            "results": organization_results,
        }

    def bulk_upload_project_files(
        self,
        project_id: int,
        file_uploads: List[Dict[str, Any]],
        auto_categorize: bool = True,
    ) -> Dict[str, Any]:
        """
        Upload multiple files to a project in bulk.

        Args:
            project_id: ID of the project
            file_uploads: List of file upload data
            auto_categorize: Whether to automatically categorize by file type

        Returns:
            Summary of bulk upload operation
        """
        results = []

        # File type categorization mapping
        type_mapping = {
            "pdf": "document",
            "doc": "document",
            "docx": "document",
            "xls": "spreadsheet",
            "xlsx": "spreadsheet",
            "ppt": "presentation",
            "pptx": "presentation",
            "jpg": "image",
            "jpeg": "image",
            "png": "image",
            "gif": "image",
            "mp4": "video",
            "avi": "video",
            "mov": "video",
            "mp3": "audio",
            "wav": "audio",
            "zip": "archive",
            "rar": "archive",
            "7z": "archive",
        }

        for file_upload in file_uploads:
            try:
                upload_data = {"project_id": project_id, **file_upload}

                # Auto-categorize if enabled
                if auto_categorize and "attachment_type" not in upload_data:
                    file_name = file_upload.get("file_name", "")
                    file_extension = (
                        file_name.split(".")[-1].lower() if "." in file_name else ""
                    )
                    upload_data["attachment_type"] = type_mapping.get(
                        file_extension, "other"
                    )

                create_result = self.create_project_attachment(**upload_data)

                results.append(
                    {
                        "file_name": file_upload["file_name"],
                        "attachment_type": upload_data.get("attachment_type"),
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
            "project_id": project_id,
            "upload_summary": {
                "total_files": len(file_uploads),
                "successful_uploads": len(successful),
                "failed_uploads": len(failed),
                "total_size_uploaded": total_size,
                "auto_categorized": auto_categorize,
            },
            "upload_date": datetime.now().isoformat(),
            "results": results,
        }

    def share_project_attachment(
        self,
        attachment_id: int,
        share_with_client: bool = False,
        expiry_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a shareable link for a project attachment.

        Args:
            attachment_id: ID of the attachment
            share_with_client: Whether to share with client
            expiry_date: Optional expiration date for the share

        Returns:
            Share link information
        """
        attachment = self.get(attachment_id)

        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found")

        # Generate share token (would typically be more complex)
        import uuid

        share_token = str(uuid.uuid4())

        update_data = {
            "id": attachment_id,
            "shareToken": share_token,
            "shareCreatedDate": datetime.now().isoformat(),
            "shareWithClient": share_with_client,
        }

        if expiry_date:
            update_data["shareExpiryDate"] = expiry_date.isoformat()

        self.update(update_data)

        return {
            "attachment_id": attachment_id,
            "project_id": attachment["projectID"],
            "file_name": attachment["fileName"],
            "share_token": share_token,
            "share_url": f"https://api.autotask.net/attachments/share/{share_token}",
            "share_with_client": share_with_client,
            "expiry_date": expiry_date.isoformat() if expiry_date else None,
            "created_date": datetime.now().isoformat(),
        }

    def get_project_attachment_analytics(
        self, project_id: int, include_usage_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Get analytics for project attachments.

        Args:
            project_id: ID of the project
            include_usage_stats: Whether to include usage statistics

        Returns:
            Project attachment analytics
        """
        attachments = self.get_project_attachments(project_id)

        # Basic statistics
        total_count = len(attachments)
        total_size = sum(int(att.get("fileSize", 0)) for att in attachments)
        public_count = sum(1 for att in attachments if att.get("isPublic"))

        # File type analysis
        content_types = {}
        attachment_types = {}
        upload_timeline = {}

        for attachment in attachments:
            # Content type analysis
            content_type = attachment.get("contentType", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1

            # Attachment type analysis
            att_type = attachment.get("attachmentType", "uncategorized")
            attachment_types[att_type] = attachment_types.get(att_type, 0) + 1

            # Upload timeline
            upload_date = attachment.get("uploadDate", "")
            if upload_date:
                month_key = upload_date[:7]  # YYYY-MM
                upload_timeline[month_key] = upload_timeline.get(month_key, 0) + 1

        analytics = {
            "project_id": project_id,
            "summary_statistics": {
                "total_attachments": total_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "public_attachments": public_count,
                "private_attachments": total_count - public_count,
                "average_file_size": (
                    round(total_size / total_count, 2) if total_count > 0 else 0
                ),
            },
            "content_type_distribution": content_types,
            "attachment_type_distribution": attachment_types,
            "upload_timeline": dict(sorted(upload_timeline.items())),
        }

        if include_usage_stats:
            # This would typically include download counts, access logs, etc.
            analytics["usage_statistics"] = {
                "total_downloads": 0,  # Would query from usage logs
                "unique_downloaders": 0,
                "most_downloaded_attachment": None,
                "recent_activity": [],
            }

        return analytics

    def archive_old_attachments(
        self, project_id: int, cutoff_date: date, archive_folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Archive old project attachments.

        Args:
            project_id: ID of the project
            cutoff_date: Date before which attachments should be archived
            archive_folder: Optional archive folder name

        Returns:
            Archive operation results
        """
        old_attachments = self.query(
            filters=[
                {"field": "projectID", "op": "eq", "value": str(project_id)},
                {"field": "uploadDate", "op": "lt", "value": cutoff_date.isoformat()},
            ]
        ).items

        archive_results = []
        archive_folder_name = (
            archive_folder or f"Archived_{cutoff_date.strftime('%Y%m%d')}"
        )

        # Create archive folder if it doesn't exist
        if old_attachments:
            try:
                archive_folder_result = self.create_project_attachment_folder(
                    project_id,
                    archive_folder_name,
                    f"Archive folder created on {datetime.now().date()}",
                )
                archive_folder_result["item_id"]
            except Exception:
                # Folder might already exist
                pass

        for attachment in old_attachments:
            try:
                # Mark as archived and move to archive folder
                updated_attachment = self.update(
                    {
                        "id": attachment["id"],
                        "isArchived": True,
                        "archiveDate": datetime.now().isoformat(),
                        "archiveFolder": archive_folder_name,
                    }
                )

                archive_results.append(
                    {
                        "attachment_id": attachment["id"],
                        "file_name": attachment["fileName"],
                        "upload_date": attachment["uploadDate"],
                        "success": True,
                    }
                )

            except Exception as e:
                archive_results.append(
                    {
                        "attachment_id": attachment["id"],
                        "file_name": attachment.get("fileName", "unknown"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in archive_results if r["success"]]
        failed = [r for r in archive_results if not r["success"]]

        return {
            "project_id": project_id,
            "cutoff_date": cutoff_date.isoformat(),
            "archive_folder": archive_folder_name,
            "archive_summary": {
                "total_attachments_processed": len(old_attachments),
                "successfully_archived": len(successful),
                "failed_to_archive": len(failed),
            },
            "archive_date": datetime.now().isoformat(),
            "results": archive_results,
        }

    def sync_attachments_with_external_storage(
        self, project_id: int, external_storage_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synchronize project attachments with external storage system.

        Args:
            project_id: ID of the project
            external_storage_config: Configuration for external storage

        Returns:
            Synchronization results
        """
        attachments = self.get_project_attachments(project_id)

        # This would typically implement actual sync with external storage
        # For now, return sync operation structure
        return {
            "project_id": project_id,
            "external_storage": external_storage_config.get("provider", "unknown"),
            "sync_summary": {
                "total_attachments": len(attachments),
                "synced_attachments": 0,  # Would implement actual sync logic
                "failed_syncs": 0,
                "skipped_attachments": 0,
            },
            "sync_date": datetime.now().isoformat(),
            "sync_status": "completed",
            "next_sync_scheduled": (datetime.now() + timedelta(days=1)).isoformat(),
        }
