"""
Task Notes entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class TaskNotesEntity(BaseEntity):
    """
    Handles Task Note operations for the Autotask API.

    Manages notes and documentation associated with tasks,
    providing progress tracking and communication capabilities.
    """

    def __init__(self, client, entity_name: str = "TaskNotes"):
        super().__init__(client, entity_name)

    def create_task_note(
        self,
        task_id: int,
        description: str,
        note_type: int = 1,
        title: Optional[str] = None,
        publish: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new task note.

        Args:
            task_id: ID of the task to add note to
            description: Note content/description
            note_type: Type of note (1=Activity Log, 2=Detailed Description)
            title: Optional note title
            publish: Publish setting (1=All, 2=Internal Only)
            **kwargs: Additional note fields

        Returns:
            Created task note data
        """
        note_data = {
            "TaskID": task_id,
            "Description": description,
            "NoteType": note_type,
            "Publish": publish,
            **kwargs,
        }

        if title:
            note_data["Title"] = title

        return self.create(note_data)

    def get_notes_by_task(
        self,
        task_id: int,
        note_type: Optional[int] = None,
        include_private: bool = True,
    ) -> EntityList:
        """
        Get all notes for a specific task.

        Args:
            task_id: Task ID to filter by
            note_type: Optional note type filter
            include_private: Whether to include private/internal notes

        Returns:
            List of task notes
        """
        filters = [{"field": "TaskID", "op": "eq", "value": str(task_id)}]

        if note_type is not None:
            filters.append({"field": "NoteType", "op": "eq", "value": str(note_type)})

        if not include_private:
            filters.append({"field": "Publish", "op": "ne", "value": "2"})

        return self.query_all(filters=filters)

    def get_recent_task_notes(
        self,
        days: int = 7,
        project_id: Optional[int] = None,
        resource_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get recent task notes within specified timeframe.

        Args:
            days: Number of days back to search
            project_id: Optional project filter
            resource_id: Optional resource filter

        Returns:
            List of recent task notes
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        filters = [
            {"field": "CreateDateTime", "op": "gte", "value": cutoff_date.isoformat()}
        ]

        # If filtering by project or resource, we'd need to join with tasks
        # For now, we'll return all recent notes and let the caller filter further
        if project_id or resource_id:
            self.logger.warning(
                "Project/Resource filtering requires additional task data"
            )

        return self.query_all(filters=filters)

    def get_notes_by_creator(
        self,
        creator_resource_id: int,
        days: Optional[int] = None,
        task_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get notes created by a specific resource.

        Args:
            creator_resource_id: ID of the creator resource
            days: Optional days filter for recent notes
            task_id: Optional task ID filter

        Returns:
            List of notes created by the resource
        """
        filters = [
            {
                "field": "CreatorResourceID",
                "op": "eq",
                "value": str(creator_resource_id),
            }
        ]

        if days is not None:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            filters.append(
                {
                    "field": "CreateDateTime",
                    "op": "gte",
                    "value": cutoff_date.isoformat(),
                }
            )

        if task_id is not None:
            filters.append({"field": "TaskID", "op": "eq", "value": str(task_id)})

        return self.query_all(filters=filters)

    def add_progress_note(
        self,
        task_id: int,
        progress_description: str,
        percent_complete: Optional[float] = None,
        time_spent: Optional[str] = None,
        blockers: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a progress update note to a task.

        Args:
            task_id: Task ID
            progress_description: Description of progress made
            percent_complete: Optional percentage complete
            time_spent: Optional time spent description
            blockers: Optional description of blockers/issues

        Returns:
            Created note data
        """
        description = f"Progress Update: {progress_description}"

        if percent_complete is not None:
            description += f"\nCompletion: {percent_complete}%"

        if time_spent:
            description += f"\nTime Spent: {time_spent}"

        if blockers:
            description += f"\nBlockers/Issues: {blockers}"

        return self.create_task_note(
            task_id=task_id,
            description=description,
            title="Progress Update",
            note_type=1,  # Activity Log
        )

    def add_status_change_note(
        self,
        task_id: int,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a note documenting a task status change.

        Args:
            task_id: Task ID
            old_status: Previous status
            new_status: New status
            reason: Optional reason for status change

        Returns:
            Created note data
        """
        description = f"Status changed from {old_status} to {new_status}"
        if reason:
            description += f". Reason: {reason}"

        return self.create_task_note(
            task_id=task_id,
            description=description,
            title="Status Change",
            note_type=1,  # Activity Log
        )

    def add_completion_note(
        self,
        task_id: int,
        completion_summary: str,
        deliverables: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        next_steps: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a task completion note with summary and details.

        Args:
            task_id: Task ID
            completion_summary: Summary of what was completed
            deliverables: Optional deliverables description
            lessons_learned: Optional lessons learned
            next_steps: Optional next steps

        Returns:
            Created note data
        """
        description = f"Task Completed: {completion_summary}"

        if deliverables:
            description += f"\n\nDeliverables:\n{deliverables}"

        if lessons_learned:
            description += f"\n\nLessons Learned:\n{lessons_learned}"

        if next_steps:
            description += f"\n\nNext Steps:\n{next_steps}"

        return self.create_task_note(
            task_id=task_id,
            description=description,
            title="Task Completion",
            note_type=2,  # Detailed Description
            publish=1,  # All - stakeholders can see completion details
        )

    def add_blocker_note(
        self,
        task_id: int,
        blocker_description: str,
        impact: str,
        proposed_resolution: Optional[str] = None,
        escalation_needed: bool = False,
    ) -> EntityDict:
        """
        Add a note documenting a task blocker or impediment.

        Args:
            task_id: Task ID
            blocker_description: Description of the blocker
            impact: Impact on the task/project
            proposed_resolution: Optional proposed resolution
            escalation_needed: Whether escalation is needed

        Returns:
            Created note data
        """
        description = f"BLOCKER IDENTIFIED\n\nDescription: {blocker_description}\nImpact: {impact}"

        if proposed_resolution:
            description += f"\n\nProposed Resolution: {proposed_resolution}"

        if escalation_needed:
            description += "\n\n⚠️ ESCALATION REQUIRED"

        return self.create_task_note(
            task_id=task_id,
            description=description,
            title="Task Blocker",
            note_type=1,  # Activity Log
            publish=1,  # All - ensure visibility
        )

    def get_task_timeline(self, task_id: int) -> List[Dict[str, Any]]:
        """
        Get a chronological timeline of all notes for a task.

        Args:
            task_id: Task ID

        Returns:
            List of notes ordered chronologically with additional context
        """
        notes = self.get_notes_by_task(task_id)

        # Sort by creation date if available
        sorted_notes = sorted(
            notes,
            key=lambda n: n.get("CreateDateTime", ""),
            reverse=False,  # Oldest first
        )

        timeline = []
        for note in sorted_notes:
            timeline_item = {
                "id": note.get("id"),
                "date": note.get("CreateDateTime"),
                "title": note.get("Title", "Note"),
                "description": note.get("Description", ""),
                "type": note.get("NoteType"),
                "creator": note.get("CreatorResourceID"),
                "is_private": note.get("Publish") == 2,
            }
            timeline.append(timeline_item)

        return timeline

    def search_task_notes_by_content(
        self,
        search_text: str,
        task_id: Optional[int] = None,
        days: Optional[int] = None,
    ) -> EntityList:
        """
        Search task notes by content text.

        Args:
            search_text: Text to search for in note descriptions
            task_id: Optional task ID filter
            days: Optional days filter for recent notes

        Returns:
            List of matching notes
        """
        filters = [{"field": "Description", "op": "contains", "value": search_text}]

        if task_id is not None:
            filters.append({"field": "TaskID", "op": "eq", "value": str(task_id)})

        if days is not None:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            filters.append(
                {
                    "field": "CreateDateTime",
                    "op": "gte",
                    "value": cutoff_date.isoformat(),
                }
            )

        return self.query_all(filters=filters)

    def get_notes_requiring_attention(self, keywords: List[str] = None) -> EntityList:
        """
        Get task notes that may require attention based on keywords.

        Args:
            keywords: List of keywords to search for (default: common attention words)

        Returns:
            List of notes requiring attention
        """
        if keywords is None:
            keywords = [
                "blocker",
                "blocked",
                "urgent",
                "escalation",
                "help needed",
                "stuck",
                "problem",
                "issue",
                "delay",
                "behind schedule",
            ]

        all_matching_notes = []

        for keyword in keywords:
            matching_notes = self.search_task_notes_by_content(keyword, days=30)
            for note in matching_notes:
                # Avoid duplicates
                if not any(
                    existing["id"] == note["id"] for existing in all_matching_notes
                ):
                    all_matching_notes.append(note)

        return all_matching_notes

    def get_task_note_statistics(self, task_id: int) -> Dict[str, Any]:
        """
        Get statistics about notes for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with note statistics
        """
        all_notes = self.get_notes_by_task(task_id)

        stats = {
            "total_notes": len(all_notes),
            "internal_notes": 0,
            "external_notes": 0,
            "activity_logs": 0,
            "detailed_descriptions": 0,
            "unique_creators": set(),
            "notes_by_day": {},
        }

        for note in all_notes:
            # Count by visibility
            if note.get("Publish") == 2:
                stats["internal_notes"] += 1
            else:
                stats["external_notes"] += 1

            # Count by type
            if note.get("NoteType") == 1:
                stats["activity_logs"] += 1
            elif note.get("NoteType") == 2:
                stats["detailed_descriptions"] += 1

            # Track creators
            if note.get("CreatorResourceID"):
                stats["unique_creators"].add(note["CreatorResourceID"])

            # Group by day
            if note.get("CreateDateTime"):
                date_str = note["CreateDateTime"][:10]  # YYYY-MM-DD
                if date_str not in stats["notes_by_day"]:
                    stats["notes_by_day"][date_str] = 0
                stats["notes_by_day"][date_str] += 1

        # Convert set to count
        stats["unique_creators"] = len(stats["unique_creators"])

        return stats

    def update_note_visibility(
        self, note_id: int, publish: int
    ) -> Optional[EntityDict]:
        """
        Update a note's visibility/publish setting.

        Args:
            note_id: ID of note to update
            publish: New publish setting (1=All, 2=Internal Only)

        Returns:
            Updated note data
        """
        return self.update_by_id(note_id, {"Publish": publish})
