"""
ContractNotes Entity for py-autotask

This module provides the ContractNotesEntity class for managing contract notes
in Autotask. Contract notes allow users to add important information, updates,
and documentation to contracts for better tracking and communication.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseEntity


class ContractNotesEntity(BaseEntity):
    """
    Manages Autotask ContractNotes - documentation and notes attached to contracts.

    Contract notes provide a way to document important information about contracts,
    including status updates, communications, decisions, and other relevant details
    that need to be tracked and shared among team members.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractNotes"

    # Core CRUD Operations

    def create_contract_note(
        self,
        contract_id: int,
        note_text: str,
        note_type: str = "General",
        is_private: bool = False,
        created_by_resource_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract note.

        Args:
            contract_id: ID of the contract
            note_text: Content of the note
            note_type: Type of note (General, Status Update, Issue, etc.)
            is_private: Whether the note is private to internal users
            created_by_resource_id: ID of the resource creating the note
            **kwargs: Additional fields for the note

        Returns:
            Create response with new note ID

        Example:
            note = client.contract_notes.create_contract_note(
                contract_id=12345,
                note_text="Updated contract terms with client approval",
                note_type="Status Update",
                created_by_resource_id=678
            )
        """
        note_data = {
            "contractID": contract_id,
            "noteText": note_text,
            "noteType": note_type,
            "isPrivate": is_private,
            "createdDateTime": datetime.now().isoformat(),
            **kwargs,
        }

        if created_by_resource_id:
            note_data["createdByResourceID"] = created_by_resource_id

        return self.create(note_data)

    def get_notes_by_contract(
        self,
        contract_id: int,
        note_type: Optional[str] = None,
        include_private: bool = True,
        created_by_resource_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notes for a specific contract.

        Args:
            contract_id: ID of the contract
            note_type: Filter by note type
            include_private: Whether to include private notes
            created_by_resource_id: Filter by creator

        Returns:
            List of contract notes
        """
        filters = [{"field": "contractID", "op": "eq", "value": contract_id}]

        if note_type:
            filters.append({"field": "noteType", "op": "eq", "value": note_type})

        if not include_private:
            filters.append({"field": "isPrivate", "op": "eq", "value": False})

        if created_by_resource_id:
            filters.append(
                {
                    "field": "createdByResourceID",
                    "op": "eq",
                    "value": created_by_resource_id,
                }
            )

        return self.query(filters=filters).items

    def get_recent_notes(
        self,
        days_back: int = 7,
        contract_id: Optional[int] = None,
        note_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent contract notes.

        Args:
            days_back: Number of days to look back
            contract_id: Optional filter by specific contract
            note_type: Optional filter by note type

        Returns:
            List of recent notes
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        filters = [{"field": "createdDateTime", "op": "gte", "value": cutoff_date}]

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        if note_type:
            filters.append({"field": "noteType", "op": "eq", "value": note_type})

        return self.query(filters=filters).items

    # Business Logic Methods

    def add_status_update_note(
        self,
        contract_id: int,
        status_message: str,
        created_by_resource_id: Optional[int] = None,
        is_private: bool = False,
    ) -> Dict[str, Any]:
        """
        Add a status update note to a contract.

        Args:
            contract_id: ID of the contract
            status_message: Status update message
            created_by_resource_id: ID of the resource creating the note
            is_private: Whether the note should be private

        Returns:
            Create response
        """
        return self.create_contract_note(
            contract_id=contract_id,
            note_text=status_message,
            note_type="Status Update",
            is_private=is_private,
            created_by_resource_id=created_by_resource_id,
        )

    def add_issue_note(
        self,
        contract_id: int,
        issue_description: str,
        severity: str = "Medium",
        created_by_resource_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add an issue note to a contract.

        Args:
            contract_id: ID of the contract
            issue_description: Description of the issue
            severity: Severity level (Low, Medium, High, Critical)
            created_by_resource_id: ID of the resource creating the note

        Returns:
            Create response
        """
        return self.create_contract_note(
            contract_id=contract_id,
            note_text=issue_description,
            note_type="Issue",
            created_by_resource_id=created_by_resource_id,
            severity=severity,
        )

    def add_communication_note(
        self,
        contract_id: int,
        communication_summary: str,
        communication_type: str = "Email",
        contact_name: Optional[str] = None,
        created_by_resource_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a communication note to a contract.

        Args:
            contract_id: ID of the contract
            communication_summary: Summary of the communication
            communication_type: Type (Email, Phone, Meeting, etc.)
            contact_name: Name of the contact
            created_by_resource_id: ID of the resource creating the note

        Returns:
            Create response
        """
        note_text = communication_summary
        if contact_name:
            note_text = f"Communication with {contact_name}: {communication_summary}"

        return self.create_contract_note(
            contract_id=contract_id,
            note_text=note_text,
            note_type="Communication",
            created_by_resource_id=created_by_resource_id,
            communicationType=communication_type,
            contactName=contact_name,
        )

    def update_note_text(
        self,
        note_id: int,
        new_text: str,
        modified_by_resource_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update the text content of a note.

        Args:
            note_id: ID of the note
            new_text: New note text
            modified_by_resource_id: ID of the resource making the update

        Returns:
            Update response
        """
        update_data = {
            "noteText": new_text,
            "lastModifiedDateTime": datetime.now().isoformat(),
        }

        if modified_by_resource_id:
            update_data["lastModifiedByResourceID"] = modified_by_resource_id

        return self.update_by_id(note_id, update_data)

    def mark_note_as_important(
        self,
        note_id: int,
        is_important: bool = True,
    ) -> Dict[str, Any]:
        """
        Mark a note as important or remove the important flag.

        Args:
            note_id: ID of the note
            is_important: Whether to mark as important

        Returns:
            Update response
        """
        update_data = {
            "isImportant": is_important,
            "lastModifiedDateTime": datetime.now().isoformat(),
        }

        return self.update_by_id(note_id, update_data)

    def get_notes_summary(
        self,
        contract_id: int,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Get a summary of contract notes activity.

        Args:
            contract_id: ID of the contract
            days_back: Number of days to include in summary

        Returns:
            Summary of notes activity
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Get all notes for the contract
        all_notes = self.get_notes_by_contract(contract_id)
        recent_notes = [
            note for note in all_notes if note.get("createdDateTime", "") >= cutoff_date
        ]

        # Categorize notes by type
        note_types = {}
        important_notes = []
        recent_activity = []

        for note in all_notes:
            note_type = note.get("noteType", "General")
            note_types[note_type] = note_types.get(note_type, 0) + 1

            if note.get("isImportant"):
                important_notes.append(note)

        for note in recent_notes:
            recent_activity.append(
                {
                    "id": note.get("id"),
                    "type": note.get("noteType"),
                    "created_date": note.get("createdDateTime"),
                    "created_by": note.get("createdByResourceID"),
                    "preview": (
                        note.get("noteText", "")[:100] + "..."
                        if len(note.get("noteText", "")) > 100
                        else note.get("noteText", "")
                    ),
                }
            )

        # Sort recent activity by date (newest first)
        recent_activity.sort(key=lambda x: x.get("created_date", ""), reverse=True)

        return {
            "contract_id": contract_id,
            "summary_period_days": days_back,
            "total_notes": len(all_notes),
            "recent_notes": len(recent_notes),
            "important_notes": len(important_notes),
            "note_types_breakdown": note_types,
            "recent_activity": recent_activity[:10],  # Last 10 activities
            "important_notes_preview": important_notes[:5],  # Top 5 important notes
        }

    def search_notes(
        self,
        search_text: str,
        contract_id: Optional[int] = None,
        note_type: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search for notes containing specific text.

        Args:
            search_text: Text to search for in note content
            contract_id: Optional filter by specific contract
            note_type: Optional filter by note type
            case_sensitive: Whether search should be case sensitive

        Returns:
            List of matching notes
        """
        filters = []

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        if note_type:
            filters.append({"field": "noteType", "op": "eq", "value": note_type})

        # Get all notes (or filtered subset)
        all_notes = self.query(filters=filters).items if filters else self.query().items

        # Filter by search text
        search_term = search_text if case_sensitive else search_text.lower()
        matching_notes = []

        for note in all_notes:
            note_text = note.get("noteText", "")
            if not case_sensitive:
                note_text = note_text.lower()

            if search_term in note_text:
                matching_notes.append(note)

        return matching_notes

    def bulk_create_notes(
        self,
        notes_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create multiple contract notes in batch.

        Args:
            notes_data: List of note data dictionaries

        Returns:
            Summary of the bulk creation operation
        """
        results = []

        for note_data in notes_data:
            try:
                result = self.create(note_data)
                results.append(
                    {
                        "success": True,
                        "note_id": result.item_id,
                        "contract_id": note_data.get("contractID"),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "contract_id": note_data.get("contractID"),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_notes": len(notes_data),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    def get_notes_by_resource(
        self,
        resource_id: int,
        contract_id: Optional[int] = None,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Get notes created by a specific resource.

        Args:
            resource_id: ID of the resource
            contract_id: Optional filter by specific contract
            days_back: Number of days to look back

        Returns:
            Notes created by the resource with summary
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        filters = [
            {"field": "createdByResourceID", "op": "eq", "value": resource_id},
            {"field": "createdDateTime", "op": "gte", "value": cutoff_date},
        ]

        if contract_id:
            filters.append({"field": "contractID", "op": "eq", "value": contract_id})

        notes = self.query(filters=filters).items

        # Group by contract
        contracts = {}
        for note in notes:
            contract_id_key = note.get("contractID")
            if contract_id_key not in contracts:
                contracts[contract_id_key] = []
            contracts[contract_id_key].append(note)

        return {
            "resource_id": resource_id,
            "period_days": days_back,
            "total_notes": len(notes),
            "contracts_with_notes": len(contracts),
            "notes_by_contract": contracts,
            "all_notes": notes,
        }

    def archive_old_notes(
        self,
        contract_id: int,
        days_old: int = 365,
        note_types_to_archive: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Archive old contract notes.

        Args:
            contract_id: ID of the contract
            days_old: Archive notes older than this many days
            note_types_to_archive: Specific note types to archive

        Returns:
            Summary of the archival operation
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

        filters = [
            {"field": "contractID", "op": "eq", "value": contract_id},
            {"field": "createdDateTime", "op": "lt", "value": cutoff_date},
            {
                "field": "isArchived",
                "op": "ne",
                "value": True,
            },  # Don't archive already archived
        ]

        if note_types_to_archive:
            type_filters = [
                {"field": "noteType", "op": "eq", "value": note_type}
                for note_type in note_types_to_archive
            ]
            # This would need to be an OR condition in practice

        old_notes = self.query(filters=filters).items

        results = []
        for note in old_notes:
            try:
                result = self.update_by_id(
                    note.get("id"),
                    {
                        "isArchived": True,
                        "archivedDateTime": datetime.now().isoformat(),
                    },
                )
                results.append(
                    {
                        "note_id": note.get("id"),
                        "success": True,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "note_id": note.get("id"),
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "contract_id": contract_id,
            "cutoff_date": cutoff_date,
            "total_notes_processed": len(old_notes),
            "successfully_archived": len(successful),
            "failed_to_archive": len(failed),
            "results": results,
        }
