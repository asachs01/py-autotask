"""
Project Notes entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class ProjectNotesEntity(BaseEntity):
    """
    Handles Project Note operations for the Autotask API.

    Manages notes and documentation associated with projects,
    providing project communication, status updates, and knowledge capture.
    """

    def __init__(self, client, entity_name: str = "ProjectNotes"):
        super().__init__(client, entity_name)

    def create_project_note(
        self,
        project_id: int,
        description: str,
        note_type: int = 1,
        title: Optional[str] = None,
        publish: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new project note.

        Args:
            project_id: ID of the project to add note to
            description: Note content/description
            note_type: Type of note (1=Activity Log, 2=Detailed Description)
            title: Optional note title
            publish: Publish setting (1=All, 2=Internal Only)
            **kwargs: Additional note fields

        Returns:
            Created project note data
        """
        note_data = {
            "ProjectID": project_id,
            "Description": description,
            "NoteType": note_type,
            "Publish": publish,
            **kwargs,
        }

        if title:
            note_data["Title"] = title

        return self.create(note_data)

    def get_notes_by_project(
        self,
        project_id: int,
        note_type: Optional[int] = None,
        include_private: bool = True,
    ) -> EntityList:
        """
        Get all notes for a specific project.

        Args:
            project_id: Project ID to filter by
            note_type: Optional note type filter
            include_private: Whether to include private/internal notes

        Returns:
            List of project notes
        """
        filters = [{"field": "ProjectID", "op": "eq", "value": str(project_id)}]

        if note_type is not None:
            filters.append({"field": "NoteType", "op": "eq", "value": str(note_type)})

        if not include_private:
            filters.append({"field": "Publish", "op": "ne", "value": "2"})

        return self.query_all(filters=filters)

    def get_recent_project_notes(
        self,
        days: int = 7,
        account_id: Optional[int] = None,
        project_manager_id: Optional[int] = None,
    ) -> EntityList:
        """
        Get recent project notes within specified timeframe.

        Args:
            days: Number of days back to search
            account_id: Optional account filter
            project_manager_id: Optional project manager filter

        Returns:
            List of recent project notes
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        filters = [
            {"field": "CreateDateTime", "op": "gte", "value": cutoff_date.isoformat()}
        ]

        # Note: Filtering by account or PM would require joining with projects table
        # For now, we'll return all recent notes and let caller filter further
        if account_id or project_manager_id:
            self.logger.warning("Account/PM filtering requires additional project data")

        return self.query_all(filters=filters)

    def add_milestone_note(
        self,
        project_id: int,
        milestone_name: str,
        status: str,
        details: Optional[str] = None,
        next_steps: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a milestone-related note to a project.

        Args:
            project_id: Project ID
            milestone_name: Name of the milestone
            status: Milestone status (e.g., "Completed", "Delayed", "In Progress")
            details: Optional milestone details
            next_steps: Optional next steps

        Returns:
            Created note data
        """
        description = f"Milestone Update: {milestone_name}\nStatus: {status}"

        if details:
            description += f"\n\nDetails:\n{details}"

        if next_steps:
            description += f"\n\nNext Steps:\n{next_steps}"

        return self.create_project_note(
            project_id=project_id,
            description=description,
            title=f"Milestone: {milestone_name}",
            note_type=1,  # Activity Log
        )

    def add_status_report_note(
        self,
        project_id: int,
        overall_status: str,
        progress_summary: str,
        accomplishments: Optional[str] = None,
        upcoming_tasks: Optional[str] = None,
        risks_issues: Optional[str] = None,
        budget_status: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a comprehensive project status report note.

        Args:
            project_id: Project ID
            overall_status: Overall project status
            progress_summary: Summary of progress made
            accomplishments: Recent accomplishments
            upcoming_tasks: Tasks planned for next period
            risks_issues: Current risks and issues
            budget_status: Budget/financial status

        Returns:
            Created note data
        """
        description = f"PROJECT STATUS REPORT\n\nOverall Status: {overall_status}\n\nProgress Summary:\n{progress_summary}"

        if accomplishments:
            description += f"\n\nRecent Accomplishments:\n{accomplishments}"

        if upcoming_tasks:
            description += f"\n\nUpcoming Tasks:\n{upcoming_tasks}"

        if risks_issues:
            description += f"\n\nRisks & Issues:\n{risks_issues}"

        if budget_status:
            description += f"\n\nBudget Status:\n{budget_status}"

        return self.create_project_note(
            project_id=project_id,
            description=description,
            title="Project Status Report",
            note_type=2,  # Detailed Description
            publish=1,  # All - stakeholders should see status
        )

    def add_decision_note(
        self,
        project_id: int,
        decision_summary: str,
        decision_maker: str,
        rationale: Optional[str] = None,
        alternatives_considered: Optional[str] = None,
        impact: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a note documenting an important project decision.

        Args:
            project_id: Project ID
            decision_summary: Summary of the decision made
            decision_maker: Who made the decision
            rationale: Rationale behind the decision
            alternatives_considered: Other options that were considered
            impact: Expected impact of the decision

        Returns:
            Created note data
        """
        description = f"PROJECT DECISION\n\nDecision: {decision_summary}\nDecision Maker: {decision_maker}"

        if rationale:
            description += f"\n\nRationale:\n{rationale}"

        if alternatives_considered:
            description += f"\n\nAlternatives Considered:\n{alternatives_considered}"

        if impact:
            description += f"\n\nExpected Impact:\n{impact}"

        return self.create_project_note(
            project_id=project_id,
            description=description,
            title="Project Decision",
            note_type=2,  # Detailed Description
            publish=1,  # All - important for stakeholder awareness
        )

    def add_risk_note(
        self,
        project_id: int,
        risk_description: str,
        probability: str,
        impact_level: str,
        mitigation_plan: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a note documenting a project risk.

        Args:
            project_id: Project ID
            risk_description: Description of the risk
            probability: Risk probability (High/Medium/Low)
            impact_level: Impact level if risk occurs
            mitigation_plan: Plan to mitigate the risk
            owner: Who owns managing this risk

        Returns:
            Created note data
        """
        description = f"PROJECT RISK IDENTIFIED\n\nRisk: {risk_description}\nProbability: {probability}\nImpact: {impact_level}"

        if owner:
            description += f"\nRisk Owner: {owner}"

        if mitigation_plan:
            description += f"\n\nMitigation Plan:\n{mitigation_plan}"

        return self.create_project_note(
            project_id=project_id,
            description=description,
            title=f"Risk: {probability}/{impact_level}",
            note_type=1,  # Activity Log
            publish=1,  # All - risks should be visible
        )

    def add_lesson_learned_note(
        self,
        project_id: int,
        lesson_title: str,
        what_happened: str,
        what_was_learned: str,
        recommendations: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a lessons learned note to capture project insights.

        Args:
            project_id: Project ID
            lesson_title: Title/summary of the lesson
            what_happened: Description of what occurred
            what_was_learned: Key insights gained
            recommendations: Recommendations for future projects

        Returns:
            Created note data
        """
        description = f"LESSON LEARNED: {lesson_title}\n\nWhat Happened:\n{what_happened}\n\nWhat Was Learned:\n{what_was_learned}"

        if recommendations:
            description += f"\n\nRecommendations:\n{recommendations}"

        return self.create_project_note(
            project_id=project_id,
            description=description,
            title=f"Lesson Learned: {lesson_title}",
            note_type=2,  # Detailed Description
            publish=2,  # Internal Only - for organizational learning
        )

    def add_stakeholder_communication_note(
        self,
        project_id: int,
        communication_type: str,
        stakeholders: str,
        key_points: str,
        feedback_received: Optional[str] = None,
        action_items: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a note documenting stakeholder communication.

        Args:
            project_id: Project ID
            communication_type: Type of communication (meeting, email, call, etc.)
            stakeholders: Who was involved
            key_points: Key points discussed
            feedback_received: Feedback from stakeholders
            action_items: Action items resulting from communication

        Returns:
            Created note data
        """
        description = f"STAKEHOLDER COMMUNICATION\n\nType: {communication_type}\nParticipants: {stakeholders}\n\nKey Points Discussed:\n{key_points}"

        if feedback_received:
            description += f"\n\nFeedback Received:\n{feedback_received}"

        if action_items:
            description += f"\n\nAction Items:\n{action_items}"

        return self.create_project_note(
            project_id=project_id,
            description=description,
            title=f"Stakeholder {communication_type.title()}",
            note_type=1,  # Activity Log
        )

    def get_project_timeline(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get a chronological timeline of all notes for a project.

        Args:
            project_id: Project ID

        Returns:
            List of notes ordered chronologically with categorization
        """
        notes = self.get_notes_by_project(project_id)

        # Sort by creation date if available
        sorted_notes = sorted(
            notes,
            key=lambda n: n.get("CreateDateTime", ""),
            reverse=False,  # Oldest first
        )

        timeline = []
        for note in sorted_notes:
            # Categorize based on title/content
            category = "General"
            title = note.get("Title", "").lower()
            description = note.get("Description", "").lower()

            if "milestone" in title:
                category = "Milestone"
            elif "status report" in title:
                category = "Status Report"
            elif "decision" in title:
                category = "Decision"
            elif "risk" in title or "risk" in description:
                category = "Risk"
            elif "lesson learned" in title:
                category = "Lesson Learned"
            elif "stakeholder" in title:
                category = "Communication"

            timeline_item = {
                "id": note.get("id"),
                "date": note.get("CreateDateTime"),
                "title": note.get("Title", "Note"),
                "description": note.get("Description", ""),
                "type": note.get("NoteType"),
                "category": category,
                "creator": note.get("CreatorResourceID"),
                "is_private": note.get("Publish") == 2,
            }
            timeline.append(timeline_item)

        return timeline

    def get_project_communication_summary(
        self, project_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get a summary of project communication activity.

        Args:
            project_id: Project ID
            days: Number of days to look back

        Returns:
            Dictionary with communication summary
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        all_notes = self.get_notes_by_project(project_id)

        # Filter to recent notes
        recent_notes = [
            note
            for note in all_notes
            if note.get("CreateDateTime")
            and datetime.fromisoformat(note["CreateDateTime"].replace("Z", "+00:00"))
            >= cutoff_date
        ]

        summary = {
            "total_recent_notes": len(recent_notes),
            "activity_logs": 0,
            "detailed_descriptions": 0,
            "public_notes": 0,
            "internal_notes": 0,
            "unique_contributors": set(),
            "notes_by_category": {
                "Milestone": 0,
                "Status Report": 0,
                "Decision": 0,
                "Risk": 0,
                "Communication": 0,
                "General": 0,
            },
            "period_days": days,
        }

        for note in recent_notes:
            # Count by type
            if note.get("NoteType") == 1:
                summary["activity_logs"] += 1
            else:
                summary["detailed_descriptions"] += 1

            # Count by visibility
            if note.get("Publish") == 2:
                summary["internal_notes"] += 1
            else:
                summary["public_notes"] += 1

            # Track contributors
            if note.get("CreatorResourceID"):
                summary["unique_contributors"].add(note["CreatorResourceID"])

            # Categorize notes
            title = note.get("Title", "").lower()
            if "milestone" in title:
                summary["notes_by_category"]["Milestone"] += 1
            elif "status report" in title:
                summary["notes_by_category"]["Status Report"] += 1
            elif "decision" in title:
                summary["notes_by_category"]["Decision"] += 1
            elif "risk" in title:
                summary["notes_by_category"]["Risk"] += 1
            elif "stakeholder" in title:
                summary["notes_by_category"]["Communication"] += 1
            else:
                summary["notes_by_category"]["General"] += 1

        # Convert set to count
        summary["unique_contributors"] = len(summary["unique_contributors"])

        return summary

    def search_project_notes(
        self,
        search_text: str,
        project_id: Optional[int] = None,
        days: Optional[int] = None,
        note_categories: Optional[List[str]] = None,
    ) -> EntityList:
        """
        Search project notes with advanced filtering options.

        Args:
            search_text: Text to search for
            project_id: Optional project ID filter
            days: Optional days filter for recent notes
            note_categories: Optional categories to filter by

        Returns:
            List of matching notes
        """
        filters = [{"field": "Description", "op": "contains", "value": search_text}]

        if project_id is not None:
            filters.append({"field": "ProjectID", "op": "eq", "value": str(project_id)})

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

        results = self.query_all(filters=filters)

        # Filter by categories if specified
        if note_categories:
            filtered_results = []
            for note in results:
                title = note.get("Title", "").lower()
                if any(category.lower() in title for category in note_categories):
                    filtered_results.append(note)
            results = filtered_results

        return results
