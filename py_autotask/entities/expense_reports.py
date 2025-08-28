"""
ExpenseReports entity for Autotask API operations.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ExpenseReportsEntity(BaseEntity):
    """
    Handles all ExpenseReports-related operations for the Autotask API.

    ExpenseReports represent collections of expense items submitted by resources
    for reimbursement, tracking the overall expense submission and approval process.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_expense_report(
        self,
        resource_id: int,
        name: str,
        period_start: date,
        period_end: date,
        status: int = 1,  # Draft
        **kwargs,
    ) -> EntityDict:
        """
        Create a new expense report.

        Args:
            resource_id: ID of the resource submitting the report
            name: Name/title of the expense report
            period_start: Start date of expense period
            period_end: End date of expense period
            status: Status of the report (1=Draft, 2=Submitted, 3=Approved, etc.)
            **kwargs: Additional expense report properties

        Returns:
            Created expense report data
        """
        report_data = {
            "ResourceID": resource_id,
            "Name": name,
            "PeriodStartDate": period_start.isoformat(),
            "PeriodEndDate": period_end.isoformat(),
            "Status": status,
            "CreateDate": date.today().isoformat(),
            **kwargs,
        }

        return self.create(report_data)

    def get_reports_by_resource(
        self,
        resource_id: int,
        status: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get expense reports for a specific resource.

        Args:
            resource_id: ID of the resource
            status: Optional status filter
            limit: Maximum number of reports to return

        Returns:
            List of expense reports for the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if status is not None:
            filters.append(QueryFilter(field="Status", op="eq", value=status))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_reports_by_status(
        self, status: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get expense reports by status.

        Args:
            status: Status to filter by
            limit: Maximum number of reports to return

        Returns:
            List of expense reports with the specified status
        """
        filters = [QueryFilter(field="Status", op="eq", value=status)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_reports_by_date_range(
        self,
        start_date: date,
        end_date: date,
        date_field: str = "CreateDate",
        limit: Optional[int] = None,
    ) -> List[EntityDict]:
        """
        Get expense reports within a date range.

        Args:
            start_date: Start date of range
            end_date: End date of range
            date_field: Date field to filter on (CreateDate, SubmitDate, etc.)
            limit: Maximum number of reports to return

        Returns:
            List of expense reports within the date range
        """
        filters = [
            QueryFilter(field=date_field, op="gte", value=start_date.isoformat()),
            QueryFilter(field=date_field, op="lte", value=end_date.isoformat()),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def submit_expense_report(
        self, report_id: int, submit_date: Optional[date] = None
    ) -> EntityDict:
        """
        Submit an expense report for approval.

        Args:
            report_id: ID of the expense report
            submit_date: Date of submission (defaults to today)

        Returns:
            Updated expense report data
        """
        if not submit_date:
            submit_date = date.today()

        update_data = {
            "Status": 2,  # Submitted
            "SubmitDate": submit_date.isoformat(),
            "LastModifiedDate": datetime.now().isoformat(),
        }

        return self.update_by_id(report_id, update_data)

    def approve_expense_report(
        self,
        report_id: int,
        approver_resource_id: int,
        approval_note: Optional[str] = None,
    ) -> EntityDict:
        """
        Approve an expense report.

        Args:
            report_id: ID of the expense report
            approver_resource_id: ID of the approver
            approval_note: Optional approval note

        Returns:
            Updated expense report data
        """
        update_data = {
            "Status": 3,  # Approved
            "ApproverResourceID": approver_resource_id,
            "ApprovalDate": datetime.now().isoformat(),
        }

        if approval_note:
            update_data["ApprovalNote"] = approval_note

        return self.update_by_id(report_id, update_data)

    def reject_expense_report(
        self, report_id: int, rejector_resource_id: int, rejection_reason: str
    ) -> EntityDict:
        """
        Reject an expense report.

        Args:
            report_id: ID of the expense report
            rejector_resource_id: ID of the rejector
            rejection_reason: Reason for rejection

        Returns:
            Updated expense report data
        """
        update_data = {
            "Status": 4,  # Rejected
            "ApproverResourceID": rejector_resource_id,
            "ApprovalDate": datetime.now().isoformat(),
            "RejectionReason": rejection_reason,
        }

        return self.update_by_id(report_id, update_data)

    def get_pending_approval_reports(
        self, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get expense reports pending approval.

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of expense reports pending approval
        """
        return self.get_reports_by_status(2, limit)  # Submitted status

    def get_draft_reports(
        self, resource_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get draft expense reports.

        Args:
            resource_id: Optional resource ID filter
            limit: Maximum number of reports to return

        Returns:
            List of draft expense reports
        """
        filters = [QueryFilter(field="Status", op="eq", value=1)]  # Draft status

        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def bulk_create_expense_reports(
        self, reports_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple expense reports in batch.

        Args:
            reports_data: List of expense report data dictionaries

        Returns:
            List of created expense report responses
        """
        return self.batch_create(reports_data)

    def calculate_report_summary(self, report_id: int) -> Dict[str, Any]:
        """
        Calculate summary statistics for an expense report.

        Args:
            report_id: ID of the expense report

        Returns:
            Dictionary containing report summary
        """
        report = self.get(report_id)
        if not report:
            return {"error": "Report not found"}

        # Get expense items (would typically use ExpenseItems entity)
        # For now, we'll return basic report information

        summary = {
            "report_id": report_id,
            "report_name": report.get("Name"),
            "resource_id": report.get("ResourceID"),
            "status": report.get("Status"),
            "period_start": report.get("PeriodStartDate"),
            "period_end": report.get("PeriodEndDate"),
            "create_date": report.get("CreateDate"),
            "submit_date": report.get("SubmitDate"),
            "approval_date": report.get("ApprovalDate"),
            "total_amount": report.get("TotalAmount", 0.0),
            "billable_amount": report.get("BillableAmount", 0.0),
            "item_count": report.get("ItemCount", 0),
            "currency": report.get("Currency", "USD"),
        }

        return summary

    def get_expense_report_statistics(
        self, resource_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get expense report statistics.

        Args:
            resource_id: Optional resource ID to filter by

        Returns:
            Dictionary containing expense report statistics
        """
        filters = []
        if resource_id:
            filters.append(QueryFilter(field="ResourceID", op="eq", value=resource_id))

        response = self.query(filters=filters) if filters else self.query_all()
        reports = response.items if hasattr(response, "items") else response

        statistics = {
            "total_reports": len(reports),
            "status_breakdown": {},
            "resource_breakdown": {},
            "monthly_breakdown": {},
            "total_amount": 0.0,
            "average_amount": 0.0,
            "approval_time_stats": {
                "avg_approval_days": 0.0,
                "pending_approval_count": 0,
            },
        }

        # Process reports
        for report in reports:
            status = report.get("Status", 0)
            resource = report.get("ResourceID", 0)
            amount = float(report.get("TotalAmount", 0))
            create_date = report.get("CreateDate")

            # Status breakdown
            if status not in statistics["status_breakdown"]:
                statistics["status_breakdown"][status] = 0
            statistics["status_breakdown"][status] += 1

            # Resource breakdown
            if resource not in statistics["resource_breakdown"]:
                statistics["resource_breakdown"][resource] = {
                    "count": 0,
                    "total_amount": 0.0,
                }
            statistics["resource_breakdown"][resource]["count"] += 1
            statistics["resource_breakdown"][resource]["total_amount"] += amount

            # Monthly breakdown
            if create_date:
                try:
                    month_key = create_date[:7]  # YYYY-MM
                    if month_key not in statistics["monthly_breakdown"]:
                        statistics["monthly_breakdown"][month_key] = {
                            "count": 0,
                            "amount": 0.0,
                        }
                    statistics["monthly_breakdown"][month_key]["count"] += 1
                    statistics["monthly_breakdown"][month_key]["amount"] += amount
                except (ValueError, IndexError):
                    pass

            statistics["total_amount"] += amount

            # Approval time tracking
            if status == 2:  # Submitted/Pending
                statistics["approval_time_stats"]["pending_approval_count"] += 1

        # Calculate averages
        if len(reports) > 0:
            statistics["average_amount"] = statistics["total_amount"] / len(reports)

        return statistics

    def export_expense_report_data(
        self, report_id: int, include_items: bool = True
    ) -> Dict[str, Any]:
        """
        Export expense report data for external systems.

        Args:
            report_id: ID of the expense report
            include_items: Whether to include expense items

        Returns:
            Dictionary containing export data
        """
        report = self.get(report_id)
        if not report:
            return {"error": "Report not found"}

        export_data = {
            "report_info": {
                "id": report_id,
                "name": report.get("Name"),
                "resource_id": report.get("ResourceID"),
                "status": report.get("Status"),
                "period_start": report.get("PeriodStartDate"),
                "period_end": report.get("PeriodEndDate"),
                "total_amount": report.get("TotalAmount", 0.0),
                "currency": report.get("Currency", "USD"),
                "export_date": datetime.now().isoformat(),
            },
            "items": [],
            "summary": {},
        }

        if include_items:
            # Would get expense items from ExpenseItems entity
            export_data["items"] = []  # Placeholder

        export_data["summary"] = self.calculate_report_summary(report_id)

        return export_data

    def clone_expense_report(
        self,
        source_report_id: int,
        new_name: str,
        new_period_start: date,
        new_period_end: date,
    ) -> EntityDict:
        """
        Clone an existing expense report with a new period.

        Args:
            source_report_id: ID of the source report
            new_name: Name for the new report
            new_period_start: Start date for new period
            new_period_end: End date for new period

        Returns:
            Created expense report data
        """
        source_report = self.get(source_report_id)
        if not source_report:
            raise ValueError(f"Source report {source_report_id} not found")

        # Create new report with same resource but new period
        new_report_data = {
            "ResourceID": source_report.get("ResourceID"),
            "Name": new_name,
            "PeriodStartDate": new_period_start.isoformat(),
            "PeriodEndDate": new_period_end.isoformat(),
            "Status": 1,  # Draft
            "Currency": source_report.get("Currency", "USD"),
        }

        return self.create_expense_report(**new_report_data)

    def get_overdue_reports(
        self, days_overdue: int = 30, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get expense reports that are overdue for submission or approval.

        Args:
            days_overdue: Number of days past period end to consider overdue
            limit: Maximum number of reports to return

        Returns:
            List of overdue expense reports
        """
        cutoff_date = date.today() - datetime.timedelta(days=days_overdue)

        filters = [
            QueryFilter(field="PeriodEndDate", op="lt", value=cutoff_date.isoformat()),
            QueryFilter(field="Status", op="in", value=[1, 2]),  # Draft or Submitted
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def validate_expense_report_period(
        self, period_start: date, period_end: date, resource_id: int
    ) -> Dict[str, Any]:
        """
        Validate expense report period for overlaps and business rules.

        Args:
            period_start: Start date of the period
            period_end: End date of the period
            resource_id: ID of the resource

        Returns:
            Dictionary containing validation results
        """
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Basic date validation
        if period_start >= period_end:
            validation_results["errors"].append(
                "Period start date must be before end date"
            )
            validation_results["is_valid"] = False

        # Check for future dates
        if period_end > date.today():
            validation_results["warnings"].append("Period extends into the future")

        # Check for overlapping periods for the same resource
        existing_reports = self.get_reports_by_resource(resource_id)

        for report in existing_reports:
            if report.get("Status") in [1, 2, 3]:  # Active reports
                existing_start = datetime.fromisoformat(
                    report["PeriodStartDate"]
                ).date()
                existing_end = datetime.fromisoformat(report["PeriodEndDate"]).date()

                # Check for overlap
                if period_start <= existing_end and period_end >= existing_start:
                    validation_results["warnings"].append(
                        f"Period overlaps with existing report: {report.get('Name', 'Unnamed')}"
                    )

        return validation_results
