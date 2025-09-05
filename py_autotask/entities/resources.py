"""
Resources entity for Autotask API operations.

This module provides comprehensive resource management functionality for Professional
Services Automation (PSA), including employee and contractor management, skills tracking,
capacity planning, billing rates, utilization analytics, and time off management.
"""

from datetime import datetime, timedelta
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union

from ..types import EntityDict, QueryFilter, ResourceData
from .base import BaseEntity


class ResourceType(IntEnum):
    """Resource type constants."""

    EMPLOYEE = 1
    CONTRACTOR = 2
    GENERIC = 3
    TEMPORARY = 4
    CONSULTANT = 5


class ResourceStatus(IntEnum):
    """Resource status constants."""

    ACTIVE = 1
    INACTIVE = 0
    ON_LEAVE = 2
    TERMINATED = 3


class SkillLevel(IntEnum):
    """Skill level constants."""

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    MASTER = 5


class CertificationStatus(IntEnum):
    """Certification status constants."""

    ACTIVE = 1
    EXPIRED = 2
    PENDING = 3
    REVOKED = 4


class PayrollType(IntEnum):
    """Payroll type constants."""

    SALARY = 1
    HOURLY = 2
    CONTRACT = 3
    COMMISSION = 4


class TimeOffType(IntEnum):
    """Time off type constants."""

    VACATION = 1
    SICK_LEAVE = 2
    PERSONAL = 3
    HOLIDAY = 4
    BEREAVEMENT = 5
    JURY_DUTY = 6
    TRAINING = 7


class ResourcesEntity(BaseEntity):
    """
    Handles all Resource-related operations for the Autotask API.

    This entity provides comprehensive Professional Services Automation (PSA) functionality
    including resource management, skills tracking, capacity planning, billing rates,
    utilization analytics, and time off management.

    Key features:
    - Resource lifecycle management (create, update, deactivate)
    - Skills and certifications tracking
    - Availability and scheduling management
    - Billing rates and cost management
    - Department and location associations
    - Role assignments and capacity planning
    - Utilization tracking and analytics
    - Time off management
    - Performance metrics and reporting
    """

    def __init__(self, client, entity_name: str = "Resources"):
        super().__init__(client, entity_name)

    # =====================================================================================
    # RESOURCE LIFECYCLE MANAGEMENT
    # =====================================================================================

    def create_resource(
        self,
        first_name: str,
        last_name: str,
        email: str,
        resource_type: Union[int, ResourceType] = ResourceType.EMPLOYEE,
        payroll_type: Union[int, PayrollType] = PayrollType.SALARY,
        hire_date: Optional[str] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        title: Optional[str] = None,
        supervisor_id: Optional[int] = None,
        hourly_rate: Optional[float] = None,
        hourly_cost: Optional[float] = None,
        salary: Optional[float] = None,
        phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        office_extension: Optional[str] = None,
        default_service_id: Optional[int] = None,
        security_level: int = 1,
        work_type_id: Optional[int] = None,
        **kwargs,
    ) -> ResourceData:
        """
        Create a new resource with comprehensive configuration options.

        Args:
            first_name: First name of the resource
            last_name: Last name of the resource
            email: Email address (must be unique)
            resource_type: Type of resource (ResourceType enum or int)
            payroll_type: Payroll type (PayrollType enum or int)
            hire_date: Date of hire (ISO format)
            department_id: Department ID
            location_id: Location ID
            title: Job title
            supervisor_id: Supervisor resource ID
            hourly_rate: Hourly billing rate
            hourly_cost: Hourly cost rate
            salary: Annual salary
            phone: Primary phone number
            mobile_phone: Mobile phone number
            office_extension: Office extension
            default_service_id: Default service ID for time entries
            security_level: Security level (1-10)
            work_type_id: Work type ID
            **kwargs: Additional resource fields

        Returns:
            Created resource data

        Raises:
            ValueError: If required fields are invalid
        """
        # Convert enums to int values
        if isinstance(resource_type, ResourceType):
            resource_type = resource_type.value
        if isinstance(payroll_type, PayrollType):
            payroll_type = payroll_type.value

        # Validate required fields
        if not first_name.strip():
            raise ValueError("First name cannot be empty")
        if not last_name.strip():
            raise ValueError("Last name cannot be empty")
        if not email or "@" not in email:
            raise ValueError("Valid email address is required")

        resource_data = {
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "ResourceType": resource_type,
            "PayrollType": payroll_type,
            "Active": True,
            "SecurityLevel": security_level,
            **kwargs,
        }

        # Add optional fields if provided
        optional_fields = {
            "HireDate": hire_date,
            "DepartmentID": department_id,
            "LocationID": location_id,
            "Title": title,
            "SupervisorID": supervisor_id,
            "HourlyRate": hourly_rate,
            "HourlyCost": hourly_cost,
            "Salary": salary,
            "Phone": phone,
            "MobilePhone": mobile_phone,
            "OfficeExtension": office_extension,
            "DefaultServiceID": default_service_id,
            "WorkTypeID": work_type_id,
        }

        for field_name, field_value in optional_fields.items():
            if field_value is not None:
                resource_data[field_name] = field_value

        return self.create(resource_data)

    def update_resource_profile(
        self,
        resource_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        title: Optional[str] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        supervisor_id: Optional[int] = None,
        phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        office_extension: Optional[str] = None,
        **kwargs,
    ) -> ResourceData:
        """
        Update resource profile information.

        Args:
            resource_id: ID of resource to update
            first_name: Updated first name
            last_name: Updated last name
            email: Updated email address
            title: Updated job title
            department_id: Updated department ID
            location_id: Updated location ID
            supervisor_id: Updated supervisor ID
            phone: Updated primary phone
            mobile_phone: Updated mobile phone
            office_extension: Updated office extension
            **kwargs: Additional fields to update

        Returns:
            Updated resource data
        """
        update_data = {}

        # Add provided fields to update
        fields_to_update = {
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "Title": title,
            "DepartmentID": department_id,
            "LocationID": location_id,
            "SupervisorID": supervisor_id,
            "Phone": phone,
            "MobilePhone": mobile_phone,
            "OfficeExtension": office_extension,
        }

        for field_name, field_value in fields_to_update.items():
            if field_value is not None:
                update_data[field_name] = field_value

        update_data.update(kwargs)

        if not update_data:
            raise ValueError("At least one field must be provided for update")

        return self.update_by_id(resource_id, update_data)

    def deactivate_resource(
        self,
        resource_id: int,
        termination_date: Optional[str] = None,
        reason: Optional[str] = None,
        final_pay_date: Optional[str] = None,
    ) -> ResourceData:
        """
        Deactivate a resource (soft delete).

        Args:
            resource_id: ID of resource to deactivate
            termination_date: Date of termination (defaults to today)
            reason: Reason for termination
            final_pay_date: Final pay date

        Returns:
            Updated resource data
        """
        update_data = {
            "Active": False,
            "TerminationDate": termination_date or datetime.now().isoformat(),
        }

        if reason:
            update_data["TerminationReason"] = reason
        if final_pay_date:
            update_data["FinalPayDate"] = final_pay_date

        return self.update_by_id(resource_id, update_data)

    def reactivate_resource(
        self,
        resource_id: int,
        rehire_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ResourceData:
        """
        Reactivate a deactivated resource.

        Args:
            resource_id: ID of resource to reactivate
            rehire_date: Date of rehire (defaults to today)
            notes: Notes about reactivation

        Returns:
            Updated resource data
        """
        update_data = {
            "Active": True,
            "RehireDate": rehire_date or datetime.now().isoformat(),
        }

        # Clear termination data
        update_data.update(
            {
                "TerminationDate": None,
                "TerminationReason": None,
                "FinalPayDate": None,
            }
        )

        if notes:
            update_data["Notes"] = notes

        return self.update_by_id(resource_id, update_data)

    # =====================================================================================
    # RESOURCE QUERYING AND FILTERING
    # =====================================================================================

    def get_active_resources(
        self,
        resource_type: Optional[Union[int, ResourceType]] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[ResourceData]:
        """
        Get all active resources with comprehensive filtering.

        Args:
            resource_type: Optional resource type filter
            department_id: Optional department filter
            location_id: Optional location filter
            limit: Maximum number of resources to return

        Returns:
            List of active resources
        """
        filters = [QueryFilter(field="Active", op="eq", value=True)]

        if resource_type is not None:
            type_value = (
                resource_type.value
                if isinstance(resource_type, ResourceType)
                else resource_type
            )
            filters.append(QueryFilter(field="ResourceType", op="eq", value=type_value))

        if department_id is not None:
            filters.append(
                QueryFilter(field="DepartmentID", op="eq", value=department_id)
            )

        if location_id is not None:
            filters.append(QueryFilter(field="LocationID", op="eq", value=location_id))

        return self.query(filters=filters, max_records=limit).items

    def search_resources_by_name(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        exact_match: bool = False,
        active_only: bool = True,
        resource_type: Optional[Union[int, ResourceType]] = None,
        limit: Optional[int] = None,
    ) -> List[ResourceData]:
        """
        Search for resources by name with enhanced filtering.

        Args:
            first_name: First name to search for
            last_name: Last name to search for
            exact_match: Whether to do exact match or partial match
            active_only: Whether to return only active resources
            resource_type: Optional resource type filter
            limit: Maximum number of resources to return

        Returns:
            List of matching resources
        """
        filters = []

        if first_name:
            op = "eq" if exact_match else "contains"
            filters.append(QueryFilter(field="FirstName", op=op, value=first_name))

        if last_name:
            op = "eq" if exact_match else "contains"
            filters.append(QueryFilter(field="LastName", op=op, value=last_name))

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        if resource_type is not None:
            type_value = (
                resource_type.value
                if isinstance(resource_type, ResourceType)
                else resource_type
            )
            filters.append(QueryFilter(field="ResourceType", op="eq", value=type_value))

        if not first_name and not last_name:
            raise ValueError("At least one name field must be provided")

        return self.query(filters=filters, max_records=limit).items

    def get_resources_by_department(
        self,
        department_id: int,
        active_only: bool = True,
        include_supervisors: bool = True,
        limit: Optional[int] = None,
    ) -> List[ResourceData]:
        """
        Get resources by department with comprehensive options.

        Args:
            department_id: Department ID to filter by
            active_only: Whether to return only active resources
            include_supervisors: Whether to include supervisors
            limit: Maximum number of resources to return

        Returns:
            List of resources in the department
        """
        filters = [QueryFilter(field="DepartmentID", op="eq", value=department_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        return self.query(filters=filters, max_records=limit).items

    def get_resources_by_location(
        self,
        location_id: int,
        active_only: bool = True,
        resource_type: Optional[Union[int, ResourceType]] = None,
        limit: Optional[int] = None,
    ) -> List[ResourceData]:
        """
        Get resources by location with filtering options.

        Args:
            location_id: Location ID to filter by
            active_only: Whether to return only active resources
            resource_type: Optional resource type filter
            limit: Maximum number of resources to return

        Returns:
            List of resources at the location
        """
        filters = [QueryFilter(field="LocationID", op="eq", value=location_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        if resource_type is not None:
            type_value = (
                resource_type.value
                if isinstance(resource_type, ResourceType)
                else resource_type
            )
            filters.append(QueryFilter(field="ResourceType", op="eq", value=type_value))

        return self.query(filters=filters, max_records=limit).items

    def get_resources_by_supervisor(
        self,
        supervisor_id: int,
        active_only: bool = True,
        include_indirect: bool = False,
        limit: Optional[int] = None,
    ) -> List[ResourceData]:
        """
        Get resources managed by a specific supervisor.

        Args:
            supervisor_id: Supervisor resource ID
            active_only: Whether to return only active resources
            include_indirect: Whether to include indirect reports
            limit: Maximum number of resources to return

        Returns:
            List of resources managed by the supervisor
        """
        filters = [QueryFilter(field="SupervisorID", op="eq", value=supervisor_id)]

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        direct_reports = self.query(filters=filters, max_records=limit).items

        if include_indirect:
            # Get indirect reports recursively
            all_reports = list(direct_reports)
            for resource in direct_reports:
                resource_id = resource.get("id") or resource.get("ID")
                if resource_id:
                    indirect_reports = self.get_resources_by_supervisor(
                        resource_id, active_only=active_only, include_indirect=True
                    )
                    all_reports.extend(indirect_reports)
            return all_reports

        return direct_reports

    def search_resources_by_skill(
        self,
        skill_name: str,
        minimum_level: Union[int, SkillLevel] = SkillLevel.BEGINNER,
        active_only: bool = True,
        available_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for resources by skill with level requirements.

        Args:
            skill_name: Name of the skill to search for
            minimum_level: Minimum skill level required
            active_only: Whether to return only active resources
            available_only: Whether to return only available resources
            limit: Maximum number of resources to return

        Returns:
            List of resources with the specified skill
        """
        level_value = (
            minimum_level.value
            if isinstance(minimum_level, SkillLevel)
            else minimum_level
        )

        # Note: In reality, this might require joining with a ResourceSkills table
        # For now, we'll use a simplified approach
        filters = []

        if active_only:
            filters.append(QueryFilter(field="Active", op="eq", value=True))

        # This is a placeholder - actual implementation would query ResourceSkills
        try:
            skill_filters = [
                QueryFilter(field="SkillName", op="contains", value=skill_name),
                QueryFilter(field="SkillLevel", op="gte", value=level_value),
            ]
            if active_only:
                skill_filters.append(
                    QueryFilter(field="ResourceActive", op="eq", value=True)
                )

            return self.client.query(
                "ResourceSkills", filters=skill_filters, max_records=limit
            )
        except Exception:
            # Fallback: search in resource notes/description
            fallback_filters = [
                QueryFilter(field="Notes", op="contains", value=skill_name)
            ]
            if active_only:
                fallback_filters.append(
                    QueryFilter(field="Active", op="eq", value=True)
                )
            return self.query(filters=fallback_filters, max_records=limit).items

    # =====================================================================================
    # SKILLS AND CERTIFICATIONS MANAGEMENT
    # =====================================================================================

    def add_resource_skill(
        self,
        resource_id: int,
        skill_name: str,
        skill_level: Union[int, SkillLevel] = SkillLevel.BEGINNER,
        date_acquired: Optional[str] = None,
        notes: Optional[str] = None,
        verified: bool = False,
    ) -> EntityDict:
        """
        Add a skill to a resource.

        Args:
            resource_id: ID of the resource
            skill_name: Name of the skill
            skill_level: Level of proficiency
            date_acquired: Date skill was acquired
            notes: Additional notes about the skill
            verified: Whether the skill has been verified

        Returns:
            Created resource skill record
        """
        level_value = (
            skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
        )

        skill_data = {
            "ResourceID": resource_id,
            "SkillName": skill_name,
            "SkillLevel": level_value,
            "Verified": verified,
        }

        if date_acquired:
            skill_data["DateAcquired"] = date_acquired
        if notes:
            skill_data["Notes"] = notes

        # Note: This assumes a ResourceSkills entity exists
        try:
            return self.client.create("ResourceSkills", skill_data)
        except Exception as e:
            raise ValueError(f"Could not add skill to resource: {e}")

    def update_resource_skill(
        self,
        resource_id: int,
        skill_name: str,
        skill_level: Union[int, SkillLevel],
        verified: Optional[bool] = None,
        notes: Optional[str] = None,
    ) -> EntityDict:
        """
        Update a resource's skill level.

        Args:
            resource_id: ID of the resource
            skill_name: Name of the skill to update
            skill_level: New skill level
            verified: Whether the skill is verified
            notes: Updated notes

        Returns:
            Updated resource skill record
        """
        level_value = (
            skill_level.value if isinstance(skill_level, SkillLevel) else skill_level
        )

        # Find existing skill record
        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="SkillName", op="eq", value=skill_name),
        ]

        try:
            skills = self.client.query("ResourceSkills", filters=filters)
            if not skills:
                raise ValueError(
                    f"Skill '{skill_name}' not found for resource {resource_id}"
                )

            skill_record = skills[0]
            skill_id = skill_record.get("id") or skill_record.get("ID")

            update_data = {"SkillLevel": level_value}
            if verified is not None:
                update_data["Verified"] = verified
            if notes is not None:
                update_data["Notes"] = notes

            return self.client.update("ResourceSkills", skill_id, update_data)
        except Exception as e:
            raise ValueError(f"Could not update resource skill: {e}")

    def remove_resource_skill(
        self,
        resource_id: int,
        skill_name: str,
    ) -> bool:
        """
        Remove a skill from a resource.

        Args:
            resource_id: ID of the resource
            skill_name: Name of the skill to remove

        Returns:
            True if successful
        """
        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="SkillName", op="eq", value=skill_name),
        ]

        try:
            skills = self.client.query("ResourceSkills", filters=filters)
            for skill in skills:
                skill_id = skill.get("id") or skill.get("ID")
                self.client.delete("ResourceSkills", skill_id)
            return True
        except Exception:
            return False

    def get_resource_skills(
        self,
        resource_id: int,
        verified_only: bool = False,
        minimum_level: Optional[Union[int, SkillLevel]] = None,
    ) -> List[EntityDict]:
        """
        Get all skills for a resource.

        Args:
            resource_id: ID of the resource
            verified_only: Whether to return only verified skills
            minimum_level: Minimum skill level to include

        Returns:
            List of resource skills
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if verified_only:
            filters.append(QueryFilter(field="Verified", op="eq", value=True))

        if minimum_level is not None:
            level_value = (
                minimum_level.value
                if isinstance(minimum_level, SkillLevel)
                else minimum_level
            )
            filters.append(QueryFilter(field="SkillLevel", op="gte", value=level_value))

        try:
            return self.client.query("ResourceSkills", filters=filters)
        except Exception:
            return []

    def add_resource_certification(
        self,
        resource_id: int,
        certification_name: str,
        certification_authority: str,
        date_earned: str,
        expiration_date: Optional[str] = None,
        certification_number: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> EntityDict:
        """
        Add a certification to a resource.

        Args:
            resource_id: ID of the resource
            certification_name: Name of the certification
            certification_authority: Issuing authority
            date_earned: Date certification was earned
            expiration_date: Optional expiration date
            certification_number: Optional certification number
            notes: Additional notes

        Returns:
            Created certification record
        """
        cert_data = {
            "ResourceID": resource_id,
            "CertificationName": certification_name,
            "IssuingAuthority": certification_authority,
            "DateEarned": date_earned,
            "Status": CertificationStatus.ACTIVE.value,
        }

        optional_fields = {
            "ExpirationDate": expiration_date,
            "CertificationNumber": certification_number,
            "Notes": notes,
        }

        for field, value in optional_fields.items():
            if value is not None:
                cert_data[field] = value

        try:
            return self.client.create("ResourceCertifications", cert_data)
        except Exception as e:
            raise ValueError(f"Could not add certification to resource: {e}")

    def update_certification_status(
        self,
        resource_id: int,
        certification_name: str,
        status: Union[int, CertificationStatus],
        expiration_date: Optional[str] = None,
    ) -> EntityDict:
        """
        Update a resource's certification status.

        Args:
            resource_id: ID of the resource
            certification_name: Name of the certification
            status: New certification status
            expiration_date: Updated expiration date

        Returns:
            Updated certification record
        """
        status_value = (
            status.value if isinstance(status, CertificationStatus) else status
        )

        filters = [
            QueryFilter(field="ResourceID", op="eq", value=resource_id),
            QueryFilter(field="CertificationName", op="eq", value=certification_name),
        ]

        try:
            certifications = self.client.query(
                "ResourceCertifications", filters=filters
            )
            if not certifications:
                raise ValueError(
                    f"Certification '{certification_name}' not found for resource {resource_id}"
                )

            cert_record = certifications[0]
            cert_id = cert_record.get("id") or cert_record.get("ID")

            update_data = {"Status": status_value}
            if expiration_date:
                update_data["ExpirationDate"] = expiration_date

            return self.client.update("ResourceCertifications", cert_id, update_data)
        except Exception as e:
            raise ValueError(f"Could not update certification status: {e}")

    def get_resource_certifications(
        self,
        resource_id: int,
        active_only: bool = True,
        expiring_soon: bool = False,
        days_ahead: int = 30,
    ) -> List[EntityDict]:
        """
        Get certifications for a resource.

        Args:
            resource_id: ID of the resource
            active_only: Whether to return only active certifications
            expiring_soon: Whether to filter for certifications expiring soon
            days_ahead: Number of days ahead to check for expiration

        Returns:
            List of resource certifications
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if active_only:
            filters.append(
                QueryFilter(
                    field="Status", op="eq", value=CertificationStatus.ACTIVE.value
                )
            )

        if expiring_soon:
            future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
            filters.append(
                QueryFilter(field="ExpirationDate", op="lte", value=future_date)
            )
            filters.append(QueryFilter(field="ExpirationDate", op="isNotNull"))

        try:
            return self.client.query("ResourceCertifications", filters=filters)
        except Exception:
            return []

    # =====================================================================================
    # AVAILABILITY AND SCHEDULING
    # =====================================================================================

    def get_resource_availability(
        self,
        resource_id: int,
        date_range: Optional[Tuple[str, str]] = None,
        include_time_off: bool = True,
        include_project_allocations: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive availability information for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Date range to check (start_date, end_date)
            include_time_off: Whether to include time off information
            include_project_allocations: Whether to include project allocations

        Returns:
            Comprehensive availability information
        """
        if date_range is None:
            start_date = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=30)).isoformat()
            date_range = (start_date, end_date)

        availability = {
            "resource_id": resource_id,
            "date_range": date_range,
            "total_capacity_hours": 0,
            "allocated_hours": 0,
            "available_hours": 0,
            "time_off_hours": 0,
            "utilization_percentage": 0,
            "time_off_entries": [],
            "project_allocations": [],
            "availability_calendar": [],
        }

        # Get resource work schedule (assuming 40 hours/week)
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        # Calculate total capacity based on work schedule
        start_date, end_date = date_range
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        weeks = (end_dt - start_dt).days / 7
        availability["total_capacity_hours"] = weeks * 40  # Assuming 40 hours/week

        # Get time off entries
        if include_time_off:
            availability["time_off_entries"] = self.get_resource_time_off(
                resource_id, date_range
            )
            availability["time_off_hours"] = sum(
                entry.get("Hours", 0) for entry in availability["time_off_entries"]
            )

        # Get project allocations
        if include_project_allocations:
            availability["project_allocations"] = self.get_resource_project_allocations(
                resource_id, date_range
            )
            availability["allocated_hours"] = sum(
                alloc.get("AllocatedHours", 0)
                for alloc in availability["project_allocations"]
            )

        # Calculate available hours
        availability["available_hours"] = (
            availability["total_capacity_hours"]
            - availability["allocated_hours"]
            - availability["time_off_hours"]
        )

        # Calculate utilization percentage
        if availability["total_capacity_hours"] > 0:
            availability["utilization_percentage"] = (
                (availability["allocated_hours"] + availability["time_off_hours"])
                / availability["total_capacity_hours"]
            ) * 100

        return availability

    def check_resource_conflicts(
        self,
        resource_id: int,
        date_range: Tuple[str, str],
        proposed_hours: float,
        exclude_project_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Check for scheduling conflicts for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Date range to check
            proposed_hours: Hours being considered for allocation
            exclude_project_id: Project ID to exclude from conflict checking

        Returns:
            List of conflicts found
        """
        conflicts = []
        availability = self.get_resource_availability(resource_id, date_range)

        # Check capacity conflict
        if availability["available_hours"] < proposed_hours:
            conflicts.append(
                {
                    "type": "capacity_conflict",
                    "message": f"Insufficient capacity: {availability['available_hours']} hours available, {proposed_hours} hours requested",
                    "available_hours": availability["available_hours"],
                    "requested_hours": proposed_hours,
                    "shortage": proposed_hours - availability["available_hours"],
                }
            )

        # Check time off conflicts
        for time_off in availability["time_off_entries"]:
            if self._date_ranges_overlap(
                date_range, (time_off.get("StartDate"), time_off.get("EndDate"))
            ):
                conflicts.append(
                    {
                        "type": "time_off_conflict",
                        "message": f"Time off scheduled: {time_off.get('TimeOffType', 'Unknown')}",
                        "time_off_entry": time_off,
                    }
                )

        # Check over-allocation with existing projects
        total_allocation = sum(
            alloc.get("AllocatedHours", 0)
            for alloc in availability["project_allocations"]
            if exclude_project_id is None
            or alloc.get("ProjectID") != exclude_project_id
        )

        if total_allocation + proposed_hours > availability["total_capacity_hours"]:
            conflicts.append(
                {
                    "type": "over_allocation",
                    "message": f"Over-allocation: {total_allocation + proposed_hours} hours vs {availability['total_capacity_hours']} capacity",
                    "current_allocation": total_allocation,
                    "proposed_allocation": proposed_hours,
                    "total_capacity": availability["total_capacity_hours"],
                    "over_allocation": (total_allocation + proposed_hours)
                    - availability["total_capacity_hours"],
                }
            )

        return conflicts

    def _date_ranges_overlap(
        self, range1: Tuple[str, str], range2: Tuple[str, str]
    ) -> bool:
        """
        Check if two date ranges overlap.

        Args:
            range1: First date range (start, end)
            range2: Second date range (start, end)

        Returns:
            True if ranges overlap
        """
        start1, end1 = range1
        start2, end2 = range2

        if not all([start1, end1, start2, end2]):
            return False

        return start1 <= end2 and start2 <= end1

    def get_resource_schedule(
        self,
        resource_id: int,
        date_range: Tuple[str, str],
        include_time_entries: bool = True,
        include_appointments: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive schedule information for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Date range to retrieve
            include_time_entries: Whether to include existing time entries
            include_appointments: Whether to include appointments

        Returns:
            Comprehensive schedule information
        """
        schedule = {
            "resource_id": resource_id,
            "date_range": date_range,
            "time_entries": [],
            "appointments": [],
            "time_off": [],
            "project_allocations": [],
            "daily_summaries": {},
        }

        if include_time_entries:
            schedule["time_entries"] = self.get_resource_time_entries(
                resource_id, date_range[0], date_range[1]
            )

        if include_appointments:
            # This would require integration with calendar systems
            schedule["appointments"] = []

        # Get time off
        schedule["time_off"] = self.get_resource_time_off(resource_id, date_range)

        # Get project allocations
        schedule["project_allocations"] = self.get_resource_project_allocations(
            resource_id, date_range
        )

        return schedule

    # =====================================================================================
    # BILLING RATES AND COST MANAGEMENT
    # =====================================================================================

    def update_resource_rates(
        self,
        resource_id: int,
        hourly_rate: Optional[float] = None,
        hourly_cost: Optional[float] = None,
        overtime_rate: Optional[float] = None,
        effective_date: Optional[str] = None,
    ) -> ResourceData:
        """
        Update billing and cost rates for a resource.

        Args:
            resource_id: ID of resource to update
            hourly_rate: New hourly billing rate
            hourly_cost: New hourly cost rate
            overtime_rate: New overtime rate
            effective_date: Date the rates become effective

        Returns:
            Updated resource data
        """
        update_data = {}

        if hourly_rate is not None:
            update_data["HourlyRate"] = hourly_rate
        if hourly_cost is not None:
            update_data["HourlyCost"] = hourly_cost
        if overtime_rate is not None:
            update_data["OvertimeRate"] = overtime_rate
        if effective_date:
            update_data["RateEffectiveDate"] = effective_date

        if not update_data:
            raise ValueError("At least one rate field must be provided")

        return self.update_by_id(resource_id, update_data)

    def get_resource_rate_history(
        self,
        resource_id: int,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get rate history for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Optional date range to filter

        Returns:
            List of rate changes
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="EffectiveDate", op="gte", value=start_date)
                )
            if end_date:
                filters.append(
                    QueryFilter(field="EffectiveDate", op="lte", value=end_date)
                )

        try:
            return self.client.query("ResourceRateHistory", filters=filters)
        except Exception:
            # Fallback: return current rates as single entry
            resource = self.get(resource_id)
            if resource:
                return [
                    {
                        "ResourceID": resource_id,
                        "HourlyRate": resource.get("HourlyRate"),
                        "HourlyCost": resource.get("HourlyCost"),
                        "EffectiveDate": resource.get("HireDate")
                        or resource.get("CreateDate"),
                    }
                ]
            return []

    def calculate_resource_cost(
        self,
        resource_id: int,
        hours: float,
        date: Optional[str] = None,
        include_overhead: bool = False,
        overhead_percentage: float = 20.0,
    ) -> Dict[str, float]:
        """
        Calculate cost for resource hours.

        Args:
            resource_id: ID of the resource
            hours: Number of hours to calculate
            date: Date for rate lookup (defaults to current date)
            include_overhead: Whether to include overhead costs
            overhead_percentage: Overhead percentage to apply

        Returns:
            Cost breakdown
        """
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        hourly_cost = resource.get("HourlyCost", 0) or 0
        hourly_rate = resource.get("HourlyRate", 0) or 0

        cost_breakdown = {
            "resource_id": resource_id,
            "hours": hours,
            "hourly_cost": hourly_cost,
            "hourly_rate": hourly_rate,
            "base_cost": hourly_cost * hours,
            "billable_amount": hourly_rate * hours,
            "overhead_cost": 0,
            "total_cost": 0,
            "profit_margin": 0,
            "markup_percentage": 0,
        }

        if include_overhead and overhead_percentage > 0:
            cost_breakdown["overhead_cost"] = cost_breakdown["base_cost"] * (
                overhead_percentage / 100
            )

        cost_breakdown["total_cost"] = (
            cost_breakdown["base_cost"] + cost_breakdown["overhead_cost"]
        )
        cost_breakdown["profit_margin"] = (
            cost_breakdown["billable_amount"] - cost_breakdown["total_cost"]
        )

        if cost_breakdown["total_cost"] > 0:
            cost_breakdown["markup_percentage"] = (
                cost_breakdown["profit_margin"] / cost_breakdown["total_cost"]
            ) * 100

        return cost_breakdown

    def get_resource_profitability(
        self,
        resource_id: int,
        date_range: Tuple[str, str],
        include_overhead: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate profitability metrics for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Date range to analyze
            include_overhead: Whether to include overhead in calculations

        Returns:
            Profitability analysis
        """
        time_entries = self.get_resource_time_entries(
            resource_id, date_range[0], date_range[1]
        )

        profitability = {
            "resource_id": resource_id,
            "date_range": date_range,
            "total_hours_worked": 0,
            "billable_hours": 0,
            "non_billable_hours": 0,
            "total_revenue": 0,
            "total_cost": 0,
            "gross_profit": 0,
            "gross_margin_percentage": 0,
            "utilization_percentage": 0,
            "average_hourly_rate": 0,
            "cost_per_hour": 0,
        }

        total_revenue = 0
        total_cost = 0
        billable_hours = 0

        for entry in time_entries:
            hours = entry.get("HoursWorked", 0)
            hourly_rate = entry.get("HourlyRate", 0)
            hourly_cost = entry.get("HourlyCost", 0)

            profitability["total_hours_worked"] += hours

            if entry.get("BillableToAccount"):
                billable_hours += hours
                total_revenue += hours * hourly_rate
            else:
                profitability["non_billable_hours"] += hours

            total_cost += hours * hourly_cost

        profitability["billable_hours"] = billable_hours
        profitability["total_revenue"] = total_revenue
        profitability["total_cost"] = total_cost
        profitability["gross_profit"] = total_revenue - total_cost

        if total_revenue > 0:
            profitability["gross_margin_percentage"] = (
                profitability["gross_profit"] / total_revenue
            ) * 100
            profitability["average_hourly_rate"] = (
                total_revenue / billable_hours if billable_hours > 0 else 0
            )

        if profitability["total_hours_worked"] > 0:
            profitability["cost_per_hour"] = (
                total_cost / profitability["total_hours_worked"]
            )

        # Calculate utilization (assuming 40 hours/week capacity)
        start_date = datetime.fromisoformat(date_range[0].replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(date_range[1].replace("Z", "+00:00"))
        weeks = (end_date - start_date).days / 7
        capacity_hours = weeks * 40

        if capacity_hours > 0:
            profitability["utilization_percentage"] = (
                billable_hours / capacity_hours
            ) * 100

        return profitability

    # =====================================================================================
    # TIME OFF MANAGEMENT
    # =====================================================================================

    def request_time_off(
        self,
        resource_id: int,
        time_off_type: Union[int, TimeOffType],
        start_date: str,
        end_date: str,
        hours: Optional[float] = None,
        reason: Optional[str] = None,
        approval_required: bool = True,
    ) -> EntityDict:
        """
        Submit a time off request for a resource.

        Args:
            resource_id: ID of the resource requesting time off
            time_off_type: Type of time off
            start_date: Start date of time off
            end_date: End date of time off
            hours: Number of hours (calculated if not provided)
            reason: Optional reason for time off
            approval_required: Whether approval is required

        Returns:
            Created time off request
        """
        type_value = (
            time_off_type.value
            if isinstance(time_off_type, TimeOffType)
            else time_off_type
        )

        # Calculate hours if not provided (assumes 8 hours per day)
        if hours is None:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            days = (end_dt - start_dt).days + 1
            hours = days * 8  # Assuming 8 hours per day

        time_off_data = {
            "ResourceID": resource_id,
            "TimeOffType": type_value,
            "StartDate": start_date,
            "EndDate": end_date,
            "Hours": hours,
            "Status": "Pending" if approval_required else "Approved",
            "RequestDate": datetime.now().isoformat(),
        }

        if reason:
            time_off_data["Reason"] = reason

        try:
            return self.client.create("ResourceTimeOff", time_off_data)
        except Exception as e:
            raise ValueError(f"Could not create time off request: {e}")

    def approve_time_off(
        self,
        time_off_id: int,
        approver_id: int,
        notes: Optional[str] = None,
    ) -> EntityDict:
        """
        Approve a time off request.

        Args:
            time_off_id: ID of the time off request
            approver_id: ID of the approving resource
            notes: Optional approval notes

        Returns:
            Updated time off request
        """
        update_data = {
            "Status": "Approved",
            "ApproverID": approver_id,
            "ApprovalDate": datetime.now().isoformat(),
        }

        if notes:
            update_data["ApprovalNotes"] = notes

        try:
            return self.client.update("ResourceTimeOff", time_off_id, update_data)
        except Exception as e:
            raise ValueError(f"Could not approve time off request: {e}")

    def deny_time_off(
        self,
        time_off_id: int,
        approver_id: int,
        reason: str,
    ) -> EntityDict:
        """
        Deny a time off request.

        Args:
            time_off_id: ID of the time off request
            approver_id: ID of the denying resource
            reason: Reason for denial

        Returns:
            Updated time off request
        """
        update_data = {
            "Status": "Denied",
            "ApproverID": approver_id,
            "ApprovalDate": datetime.now().isoformat(),
            "DenialReason": reason,
        }

        try:
            return self.client.update("ResourceTimeOff", time_off_id, update_data)
        except Exception as e:
            raise ValueError(f"Could not deny time off request: {e}")

    def get_resource_time_off(
        self,
        resource_id: int,
        date_range: Optional[Tuple[str, str]] = None,
        status_filter: Optional[str] = None,
        time_off_type: Optional[Union[int, TimeOffType]] = None,
    ) -> List[EntityDict]:
        """
        Get time off entries for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Optional date range to filter
            status_filter: Optional status filter ('pending', 'approved', 'denied')
            time_off_type: Optional time off type filter

        Returns:
            List of time off entries
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="StartDate", op="gte", value=start_date)
                )
            if end_date:
                filters.append(QueryFilter(field="EndDate", op="lte", value=end_date))

        if status_filter:
            status_map = {
                "pending": "Pending",
                "approved": "Approved",
                "denied": "Denied",
            }
            if status_filter.lower() in status_map:
                filters.append(
                    QueryFilter(
                        field="Status", op="eq", value=status_map[status_filter.lower()]
                    )
                )

        if time_off_type is not None:
            type_value = (
                time_off_type.value
                if isinstance(time_off_type, TimeOffType)
                else time_off_type
            )
            filters.append(QueryFilter(field="TimeOffType", op="eq", value=type_value))

        try:
            return self.client.query("ResourceTimeOff", filters=filters)
        except Exception:
            return []

    def get_time_off_balance(
        self,
        resource_id: int,
        time_off_type: Union[int, TimeOffType],
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get time off balance for a resource.

        Args:
            resource_id: ID of the resource
            time_off_type: Type of time off to check
            year: Year to check (defaults to current year)

        Returns:
            Time off balance information
        """
        if year is None:
            year = datetime.now().year

        type_value = (
            time_off_type.value
            if isinstance(time_off_type, TimeOffType)
            else time_off_type
        )

        # Date range for the year
        start_date = f"{year}-01-01T00:00:00Z"
        end_date = f"{year}-12-31T23:59:59Z"

        time_off_entries = self.get_resource_time_off(
            resource_id, (start_date, end_date), "approved", time_off_type
        )

        used_hours = sum(entry.get("Hours", 0) for entry in time_off_entries)

        # Get allocation from resource profile or company policy
        # resource = self.get(resource_id)  # TODO: Use resource profile
        allocated_hours = 0  # This would come from company policy or resource profile

        # Placeholder allocation based on time off type
        allocation_map = {
            TimeOffType.VACATION.value: 80,  # 2 weeks
            TimeOffType.SICK_LEAVE.value: 40,  # 1 week
            TimeOffType.PERSONAL.value: 24,  # 3 days
        }
        allocated_hours = allocation_map.get(type_value, 0)

        balance = {
            "resource_id": resource_id,
            "time_off_type": type_value,
            "year": year,
            "allocated_hours": allocated_hours,
            "used_hours": used_hours,
            "remaining_hours": allocated_hours - used_hours,
            "entries_count": len(time_off_entries),
            "entries": time_off_entries,
        }

        return balance

    # =====================================================================================
    # UTILIZATION TRACKING AND ANALYTICS
    # =====================================================================================

    def get_resource_utilization(
        self,
        resource_id: int,
        date_range: Tuple[str, str],
        include_non_billable: bool = True,
        group_by: str = "week",  # "day", "week", "month"
    ) -> Dict[str, Any]:
        """
        Get detailed utilization metrics for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Date range to analyze
            include_non_billable: Whether to include non-billable time
            group_by: How to group the utilization data

        Returns:
            Detailed utilization metrics
        """
        time_entries = self.get_resource_time_entries(
            resource_id, date_range[0], date_range[1]
        )

        utilization = {
            "resource_id": resource_id,
            "date_range": date_range,
            "group_by": group_by,
            "summary": {
                "total_hours": 0,
                "billable_hours": 0,
                "non_billable_hours": 0,
                "capacity_hours": 0,
                "utilization_percentage": 0,
                "billable_utilization_percentage": 0,
            },
            "time_series": [],
            "project_breakdown": {},
            "efficiency_metrics": {
                "average_hours_per_day": 0,
                "peak_utilization_day": None,
                "low_utilization_periods": [],
            },
        }

        # Calculate capacity based on date range
        start_date = datetime.fromisoformat(date_range[0].replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(date_range[1].replace("Z", "+00:00"))
        weeks = (end_date - start_date).days / 7
        utilization["summary"]["capacity_hours"] = weeks * 40  # Assuming 40 hours/week

        # Process time entries
        billable_hours = 0
        non_billable_hours = 0
        project_hours = {}

        for entry in time_entries:
            hours = entry.get("HoursWorked", 0)
            project_id = entry.get("ProjectID")

            utilization["summary"]["total_hours"] += hours

            if entry.get("BillableToAccount"):
                billable_hours += hours
            else:
                non_billable_hours += hours

            # Track by project
            if project_id:
                if project_id not in project_hours:
                    project_hours[project_id] = {"billable": 0, "non_billable": 0}

                if entry.get("BillableToAccount"):
                    project_hours[project_id]["billable"] += hours
                else:
                    project_hours[project_id]["non_billable"] += hours

        utilization["summary"]["billable_hours"] = billable_hours
        utilization["summary"]["non_billable_hours"] = non_billable_hours
        utilization["project_breakdown"] = project_hours

        # Calculate utilization percentages
        capacity = utilization["summary"]["capacity_hours"]
        if capacity > 0:
            total_hours = billable_hours + (
                non_billable_hours if include_non_billable else 0
            )
            utilization["summary"]["utilization_percentage"] = (
                total_hours / capacity
            ) * 100
            utilization["summary"]["billable_utilization_percentage"] = (
                billable_hours / capacity
            ) * 100

        # Calculate efficiency metrics
        total_days = (end_date - start_date).days + 1
        if total_days > 0:
            utilization["efficiency_metrics"]["average_hours_per_day"] = (
                utilization["summary"]["total_hours"] / total_days
            )

        return utilization

    def compare_resource_utilization(
        self,
        resource_ids: List[int],
        date_range: Tuple[str, str],
        sort_by: str = "utilization_percentage",
    ) -> List[Dict[str, Any]]:
        """
        Compare utilization across multiple resources.

        Args:
            resource_ids: List of resource IDs to compare
            date_range: Date range to analyze
            sort_by: Field to sort by

        Returns:
            List of resource utilization comparisons
        """
        comparisons = []

        for resource_id in resource_ids:
            try:
                utilization = self.get_resource_utilization(resource_id, date_range)
                resource = self.get(resource_id)

                comparison = {
                    "resource_id": resource_id,
                    "resource_name": f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip(),
                    "utilization_percentage": utilization["summary"][
                        "utilization_percentage"
                    ],
                    "billable_utilization_percentage": utilization["summary"][
                        "billable_utilization_percentage"
                    ],
                    "total_hours": utilization["summary"]["total_hours"],
                    "billable_hours": utilization["summary"]["billable_hours"],
                    "capacity_hours": utilization["summary"]["capacity_hours"],
                    "efficiency_score": utilization["efficiency_metrics"][
                        "average_hours_per_day"
                    ],
                }

                comparisons.append(comparison)

            except Exception as e:
                # Log error but continue with other resources
                print(f"Error analyzing resource {resource_id}: {e}")

        # Sort by specified field
        if sort_by in [
            "utilization_percentage",
            "billable_utilization_percentage",
            "total_hours",
            "efficiency_score",
        ]:
            comparisons.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        return comparisons

    def identify_underutilized_resources(
        self,
        threshold_percentage: float = 80.0,
        date_range: Optional[Tuple[str, str]] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Identify resources with utilization below threshold.

        Args:
            threshold_percentage: Utilization threshold
            date_range: Date range to analyze (defaults to last 30 days)
            department_id: Optional department filter
            location_id: Optional location filter

        Returns:
            List of underutilized resources with recommendations
        """
        if date_range is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date.isoformat(), end_date.isoformat())

        # Get active resources with filters
        resources = self.get_active_resources(
            department_id=department_id, location_id=location_id
        )

        underutilized = []

        for resource in resources:
            resource_id = resource.get("id") or resource.get("ID")
            if not resource_id:
                continue

            try:
                utilization = self.get_resource_utilization(resource_id, date_range)
                utilization_pct = utilization["summary"]["utilization_percentage"]

                if utilization_pct < threshold_percentage:
                    recommendations = []

                    # Generate recommendations
                    if utilization_pct < 50:
                        recommendations.append("Consider training or skill development")
                        recommendations.append("Evaluate project allocation priorities")
                    elif utilization_pct < 70:
                        recommendations.append("Review current project assignments")
                        recommendations.append("Consider additional project allocation")

                    underutilized.append(
                        {
                            "resource_id": resource_id,
                            "resource_name": f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip(),
                            "department_id": resource.get("DepartmentID"),
                            "location_id": resource.get("LocationID"),
                            "utilization_percentage": utilization_pct,
                            "gap_percentage": threshold_percentage - utilization_pct,
                            "total_hours": utilization["summary"]["total_hours"],
                            "capacity_hours": utilization["summary"]["capacity_hours"],
                            "available_hours": utilization["summary"]["capacity_hours"]
                            - utilization["summary"]["total_hours"],
                            "recommendations": recommendations,
                        }
                    )

            except Exception as e:
                print(f"Error analyzing resource {resource_id}: {e}")

        # Sort by utilization gap (largest gaps first)
        underutilized.sort(key=lambda x: x["gap_percentage"], reverse=True)

        return underutilized

    # =====================================================================================
    # HELPER METHODS FOR INTEGRATION
    # =====================================================================================

    def get_resource_tickets(
        self,
        resource_id: int,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get tickets assigned to a specific resource.

        Args:
            resource_id: ID of the resource
            status_filter: Optional status filter ('open', 'closed', etc.)
            priority_filter: Optional priority filter ('high', 'medium', 'low')
            date_range: Optional date range filter
            limit: Maximum number of tickets to return

        Returns:
            List of tickets assigned to the resource
        """
        filters = [QueryFilter(field="AssignedResourceID", op="eq", value=resource_id)]

        if status_filter:
            status_map = {
                "open": [1, 8, 9, 10, 11],
                "closed": [5],
                "new": [1],
                "in_progress": [8, 9, 10, 11],
            }

            if status_filter.lower() in status_map:
                status_ids = status_map[status_filter.lower()]
                if len(status_ids) == 1:
                    filters.append(
                        QueryFilter(field="Status", op="eq", value=status_ids[0])
                    )
                else:
                    filters.append(
                        QueryFilter(field="Status", op="in", value=status_ids)
                    )

        if priority_filter:
            priority_map = {
                "low": [4],
                "medium": [3],
                "high": [2],
                "critical": [1],
            }
            if priority_filter.lower() in priority_map:
                priority_ids = priority_map[priority_filter.lower()]
                filters.append(
                    QueryFilter(field="Priority", op="in", value=priority_ids)
                )

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(
                    QueryFilter(field="CreateDate", op="gte", value=start_date)
                )
            if end_date:
                filters.append(
                    QueryFilter(field="CreateDate", op="lte", value=end_date)
                )

        return self.client.query("Tickets", filters=filters, max_records=limit)

    def get_resource_time_entries(
        self,
        resource_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        project_id: Optional[int] = None,
        billable_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get time entries for a specific resource.

        Args:
            resource_id: ID of the resource
            date_from: Start date filter (ISO format)
            date_to: End date filter (ISO format)
            project_id: Optional project filter
            billable_only: Whether to return only billable entries
            limit: Maximum number of time entries to return

        Returns:
            List of time entries for the resource
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_from:
            filters.append(QueryFilter(field="DateWorked", op="gte", value=date_from))
        if date_to:
            filters.append(QueryFilter(field="DateWorked", op="lte", value=date_to))
        if project_id:
            filters.append(QueryFilter(field="ProjectID", op="eq", value=project_id))
        if billable_only:
            filters.append(QueryFilter(field="BillableToAccount", op="eq", value=True))

        return self.client.query("TimeEntries", filters=filters, max_records=limit)

    def get_resource_project_allocations(
        self,
        resource_id: int,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get project allocations for a resource.

        Args:
            resource_id: ID of the resource
            date_range: Optional date range to filter

        Returns:
            List of project allocations
        """
        filters = [QueryFilter(field="ResourceID", op="eq", value=resource_id)]

        if date_range:
            start_date, end_date = date_range
            if start_date:
                filters.append(QueryFilter(field="StartDate", op="lte", value=end_date))
            if end_date:
                filters.append(QueryFilter(field="EndDate", op="gte", value=start_date))

        try:
            return self.client.query("ProjectResourceAllocations", filters=filters)
        except Exception:
            # Fallback: estimate from time entries
            time_entries = self.get_resource_time_entries(
                resource_id,
                date_range[0] if date_range else None,
                date_range[1] if date_range else None,
            )

            # Group by project
            project_allocations = {}
            for entry in time_entries:
                project_id = entry.get("ProjectID")
                if project_id:
                    if project_id not in project_allocations:
                        project_allocations[project_id] = {
                            "ProjectID": project_id,
                            "ResourceID": resource_id,
                            "AllocatedHours": 0,
                        }
                    project_allocations[project_id]["AllocatedHours"] += entry.get(
                        "HoursWorked", 0
                    )

            return list(project_allocations.values())

    # =====================================================================================
    # ADVANCED CAPACITY PLANNING AND FORECASTING
    # =====================================================================================

    def forecast_resource_capacity(
        self,
        resource_id: int,
        forecast_weeks: int = 12,
        include_historical_trends: bool = True,
        include_seasonal_adjustments: bool = False,
    ) -> Dict[str, Any]:
        """
        Forecast future capacity and availability for a resource.

        Args:
            resource_id: ID of the resource
            forecast_weeks: Number of weeks to forecast
            include_historical_trends: Whether to include historical utilization trends
            include_seasonal_adjustments: Whether to apply seasonal adjustments

        Returns:
            Comprehensive capacity forecast
        """
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        # Get historical data for trend analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=26)  # 6 months of history

        historical_utilization = []
        if include_historical_trends:
            # Get utilization data for past 26 weeks
            for week_offset in range(26):
                week_start = start_date + timedelta(weeks=week_offset)
                week_end = week_start + timedelta(days=7)

                week_utilization = self.get_resource_utilization(
                    resource_id, (week_start.isoformat(), week_end.isoformat())
                )

                historical_utilization.append(
                    {
                        "week": week_offset,
                        "start_date": week_start.isoformat(),
                        "utilization_percentage": week_utilization["summary"][
                            "utilization_percentage"
                        ],
                        "billable_hours": week_utilization["summary"]["billable_hours"],
                        "capacity_hours": week_utilization["summary"]["capacity_hours"],
                    }
                )

        # Calculate baseline capacity (40 hours/week standard)
        standard_weekly_capacity = 40.0

        # Generate forecast
        forecast_data = []
        for week in range(forecast_weeks):
            forecast_start = end_date + timedelta(weeks=week)
            forecast_end = forecast_start + timedelta(days=7)

            # Base forecast on standard capacity
            forecast_capacity = standard_weekly_capacity
            forecast_availability = standard_weekly_capacity

            # Apply trend adjustments if requested
            if include_historical_trends and historical_utilization:
                # Calculate average utilization trend
                avg_utilization = sum(
                    h["utilization_percentage"] for h in historical_utilization
                ) / len(historical_utilization)
                trend_adjustment = avg_utilization / 100
                forecast_availability = forecast_capacity * (1 - trend_adjustment)

            # Apply seasonal adjustments (simplified)
            if include_seasonal_adjustments:
                month = forecast_start.month
                # Adjust for typical vacation months
                if month in [7, 8, 12]:  # July, August, December
                    forecast_availability *= 0.85  # 15% reduction for vacations
                elif month in [11, 1]:  # November, January
                    forecast_availability *= 0.95  # 5% reduction for holidays

            # Check for scheduled time off
            week_time_off = self.get_resource_time_off(
                resource_id,
                (forecast_start.isoformat(), forecast_end.isoformat()),
                "approved",
            )

            time_off_hours = sum(entry.get("Hours", 0) for entry in week_time_off)
            forecast_availability -= time_off_hours

            forecast_data.append(
                {
                    "week": week + 1,
                    "start_date": forecast_start.isoformat(),
                    "end_date": forecast_end.isoformat(),
                    "forecast_capacity_hours": forecast_capacity,
                    "forecast_available_hours": max(0, forecast_availability),
                    "scheduled_time_off_hours": time_off_hours,
                    "utilization_forecast_percentage": (
                        (
                            (forecast_capacity - forecast_availability)
                            / forecast_capacity
                            * 100
                        )
                        if forecast_capacity > 0
                        else 0
                    ),
                    "confidence_level": 0.8 if include_historical_trends else 0.6,
                }
            )

        return {
            "resource_id": resource_id,
            "resource_name": f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip(),
            "forecast_period": f"{forecast_weeks} weeks",
            "forecast_data": forecast_data,
            "historical_utilization": (
                historical_utilization if include_historical_trends else []
            ),
            "summary": {
                "total_forecast_capacity_hours": sum(
                    f["forecast_capacity_hours"] for f in forecast_data
                ),
                "total_forecast_available_hours": sum(
                    f["forecast_available_hours"] for f in forecast_data
                ),
                "average_weekly_availability": (
                    sum(f["forecast_available_hours"] for f in forecast_data)
                    / len(forecast_data)
                    if forecast_data
                    else 0
                ),
                "peak_availability_week": (
                    max(forecast_data, key=lambda x: x["forecast_available_hours"])
                    if forecast_data
                    else None
                ),
                "lowest_availability_week": (
                    min(forecast_data, key=lambda x: x["forecast_available_hours"])
                    if forecast_data
                    else None
                ),
            },
        }

    def optimize_workload_distribution(
        self,
        resource_ids: List[int],
        project_requirements: List[Dict[str, Any]],
        optimization_criteria: str = "balanced",  # "balanced", "efficiency", "cost"
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize workload distribution across multiple resources.

        Args:
            resource_ids: List of resource IDs to consider
            project_requirements: List of project requirements with skills and hours needed
            optimization_criteria: Optimization approach
            constraints: Additional constraints (max hours per resource, skill requirements, etc.)

        Returns:
            Optimized workload allocation recommendations
        """
        if constraints is None:
            constraints = {}

        # Get resource information and capabilities
        resources_info = {}
        for resource_id in resource_ids:
            resource = self.get(resource_id)
            if not resource:
                continue

            skills = self.get_resource_skills(resource_id, verified_only=True)
            availability = self.get_resource_availability(resource_id)

            resources_info[resource_id] = {
                "resource": resource,
                "skills": skills,
                "availability": availability,
                "hourly_rate": resource.get("HourlyRate", 0) or 0,
                "hourly_cost": resource.get("HourlyCost", 0) or 0,
            }

        # Initialize allocation matrix
        allocations = []
        unallocated_requirements = []

        # Process each project requirement
        for requirement in project_requirements:
            project_id = requirement.get("project_id")
            required_hours = requirement.get("hours", 0)
            required_skills = requirement.get("skills", [])
            priority = requirement.get("priority", 3)  # 1=high, 3=medium, 5=low
            deadline = requirement.get("deadline")

            # Find suitable resources
            suitable_resources = []
            for resource_id, info in resources_info.items():
                resource_skills = [
                    skill.get("SkillName", "") for skill in info["skills"]
                ]

                # Check skill compatibility
                skill_match_score = 0
                if required_skills:
                    matching_skills = set(required_skills) & set(resource_skills)
                    skill_match_score = len(matching_skills) / len(required_skills)
                else:
                    skill_match_score = 1.0  # No specific skills required

                if (
                    skill_match_score > 0
                ):  # At least some skills match or no skills required
                    available_hours = info["availability"]["available_hours"]
                    hourly_rate = info["hourly_rate"]
                    hourly_cost = info["hourly_cost"]

                    # Calculate suitability score based on criteria
                    if optimization_criteria == "efficiency":
                        efficiency_score = skill_match_score * (
                            available_hours / max(1, required_hours)
                        )
                        suitability_score = efficiency_score
                    elif optimization_criteria == "cost":
                        cost_factor = 1 / max(1, hourly_cost) if hourly_cost > 0 else 1
                        suitability_score = skill_match_score * cost_factor
                    else:  # balanced
                        efficiency = skill_match_score * (
                            available_hours / max(1, required_hours)
                        )
                        cost_factor = 1 / max(1, hourly_cost) if hourly_cost > 0 else 1
                        suitability_score = (efficiency + cost_factor) / 2

                    suitable_resources.append(
                        {
                            "resource_id": resource_id,
                            "skill_match_score": skill_match_score,
                            "available_hours": available_hours,
                            "hourly_rate": hourly_rate,
                            "hourly_cost": hourly_cost,
                            "suitability_score": suitability_score,
                        }
                    )

            # Sort by suitability score
            suitable_resources.sort(key=lambda x: x["suitability_score"], reverse=True)

            # Allocate hours to best suitable resources
            remaining_hours = required_hours
            allocation_for_requirement = []

            for resource in suitable_resources:
                if remaining_hours <= 0:
                    break

                resource_id = resource["resource_id"]
                available_hours = resource["available_hours"]

                # Determine allocation amount
                max_allocation = constraints.get(
                    "max_hours_per_resource_per_project", available_hours
                )
                allocation_hours = min(remaining_hours, available_hours, max_allocation)

                if allocation_hours > 0:
                    allocation_for_requirement.append(
                        {
                            "resource_id": resource_id,
                            "allocated_hours": allocation_hours,
                            "skill_match_score": resource["skill_match_score"],
                            "hourly_rate": resource["hourly_rate"],
                            "hourly_cost": resource["hourly_cost"],
                            "estimated_cost": allocation_hours
                            * resource["hourly_cost"],
                            "estimated_revenue": allocation_hours
                            * resource["hourly_rate"],
                        }
                    )

                    remaining_hours -= allocation_hours
                    # Update available hours for this resource
                    resources_info[resource_id]["availability"][
                        "available_hours"
                    ] -= allocation_hours

            if remaining_hours > 0:
                unallocated_requirements.append(
                    {
                        "project_id": project_id,
                        "unallocated_hours": remaining_hours,
                        "required_skills": required_skills,
                        "priority": priority,
                    }
                )

            if allocation_for_requirement:
                allocations.append(
                    {
                        "project_id": project_id,
                        "required_hours": required_hours,
                        "allocated_hours": required_hours - remaining_hours,
                        "allocations": allocation_for_requirement,
                        "allocation_percentage": (
                            ((required_hours - remaining_hours) / required_hours * 100)
                            if required_hours > 0
                            else 0
                        ),
                    }
                )

        # Calculate summary metrics
        total_allocated_hours = sum(
            sum(alloc["allocated_hours"] for alloc in allocation["allocations"])
            for allocation in allocations
        )

        total_estimated_cost = sum(
            sum(alloc["estimated_cost"] for alloc in allocation["allocations"])
            for allocation in allocations
        )

        total_estimated_revenue = sum(
            sum(alloc["estimated_revenue"] for alloc in allocation["allocations"])
            for allocation in allocations
        )

        return {
            "optimization_criteria": optimization_criteria,
            "total_resources_considered": len(resource_ids),
            "total_requirements_processed": len(project_requirements),
            "allocations": allocations,
            "unallocated_requirements": unallocated_requirements,
            "summary": {
                "total_allocated_hours": total_allocated_hours,
                "total_unallocated_hours": sum(
                    req["unallocated_hours"] for req in unallocated_requirements
                ),
                "allocation_success_rate": (
                    (len(allocations) / len(project_requirements) * 100)
                    if project_requirements
                    else 0
                ),
                "total_estimated_cost": total_estimated_cost,
                "total_estimated_revenue": total_estimated_revenue,
                "estimated_profit_margin": total_estimated_revenue
                - total_estimated_cost,
            },
            "resource_utilization_impact": {
                resource_id: {
                    "original_available_hours": sum(
                        alloc["allocated_hours"]
                        for allocation in allocations
                        for alloc in allocation["allocations"]
                        if alloc["resource_id"] == resource_id
                    )
                    + info["availability"]["available_hours"],
                    "allocated_hours": sum(
                        alloc["allocated_hours"]
                        for allocation in allocations
                        for alloc in allocation["allocations"]
                        if alloc["resource_id"] == resource_id
                    ),
                    "remaining_available_hours": info["availability"][
                        "available_hours"
                    ],
                }
                for resource_id, info in resources_info.items()
            },
        }

    def generate_capacity_recommendations(
        self,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        forecast_weeks: int = 12,
        utilization_threshold: float = 85.0,
    ) -> Dict[str, Any]:
        """
        Generate capacity planning recommendations for a department or organization.

        Args:
            department_id: Optional department filter
            location_id: Optional location filter
            forecast_weeks: Number of weeks to forecast
            utilization_threshold: Target utilization percentage

        Returns:
            Comprehensive capacity recommendations
        """
        # Get resources to analyze
        resources = self.get_active_resources(
            department_id=department_id, location_id=location_id
        )

        recommendations = {
            "analysis_date": datetime.now().isoformat(),
            "parameters": {
                "department_id": department_id,
                "location_id": location_id,
                "forecast_weeks": forecast_weeks,
                "target_utilization_threshold": utilization_threshold,
            },
            "resource_analysis": [],
            "capacity_gaps": [],
            "over_allocation_risks": [],
            "hiring_recommendations": [],
            "training_recommendations": [],
            "summary": {
                "total_resources_analyzed": len(resources),
                "resources_over_threshold": 0,
                "resources_under_threshold": 0,
                "average_utilization_forecast": 0,
                "total_capacity_shortfall_hours": 0,
                "total_excess_capacity_hours": 0,
            },
        }

        total_utilization = 0

        for resource in resources:
            resource_id = resource.get("id") or resource.get("ID")
            if not resource_id:
                continue

            try:
                # Get current utilization
                current_date = datetime.now()
                month_ago = current_date - timedelta(days=30)
                current_utilization = self.get_resource_utilization(
                    resource_id, (month_ago.isoformat(), current_date.isoformat())
                )

                # Get forecast
                forecast = self.forecast_resource_capacity(
                    resource_id, forecast_weeks=forecast_weeks
                )

                current_util_pct = current_utilization["summary"][
                    "utilization_percentage"
                ]
                avg_forecast_availability = forecast["summary"][
                    "average_weekly_availability"
                ]

                total_utilization += current_util_pct

                # Analyze capacity situation
                analysis = {
                    "resource_id": resource_id,
                    "resource_name": f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip(),
                    "current_utilization_percentage": current_util_pct,
                    "average_forecast_availability_hours": avg_forecast_availability,
                    "status": "optimal",
                    "recommendations": [],
                }

                # Determine status and recommendations
                if current_util_pct > utilization_threshold:
                    analysis["status"] = "over_utilized"
                    recommendations["summary"]["resources_over_threshold"] += 1

                    analysis["recommendations"].extend(
                        [
                            "Consider redistributing workload to other team members",
                            "Evaluate priority of current assignments",
                            "Monitor for burnout risk",
                        ]
                    )

                    if current_util_pct > 95:
                        recommendations["over_allocation_risks"].append(
                            {
                                "resource_id": resource_id,
                                "resource_name": analysis["resource_name"],
                                "risk_level": "high",
                                "current_utilization": current_util_pct,
                                "recommendations": [
                                    "Immediate workload redistribution required"
                                ],
                            }
                        )

                elif current_util_pct < (utilization_threshold - 20):
                    analysis["status"] = "under_utilized"
                    recommendations["summary"]["resources_under_threshold"] += 1

                    analysis["recommendations"].extend(
                        [
                            "Consider additional project assignments",
                            "Evaluate training opportunities",
                            "Review skill utilization",
                        ]
                    )

                    excess_hours = avg_forecast_availability * forecast_weeks
                    recommendations["summary"][
                        "total_excess_capacity_hours"
                    ] += excess_hours

                # Check for skill gaps
                skills = self.get_resource_skills(resource_id, verified_only=True)
                if len(skills) < 3:  # Arbitrary threshold
                    recommendations["training_recommendations"].append(
                        {
                            "resource_id": resource_id,
                            "resource_name": analysis["resource_name"],
                            "current_skills_count": len(skills),
                            "recommendation": "Expand skill set to increase versatility",
                            "priority": "medium" if current_util_pct < 50 else "low",
                        }
                    )

                recommendations["resource_analysis"].append(analysis)

            except Exception as e:
                print(f"Error analyzing resource {resource_id}: {e}")
                continue

        # Calculate summary metrics
        if recommendations["resource_analysis"]:
            recommendations["summary"]["average_utilization_forecast"] = (
                total_utilization / len(recommendations["resource_analysis"])
            )

        # Generate hiring recommendations based on overall capacity
        if (
            recommendations["summary"]["resources_over_threshold"]
            / max(1, recommendations["summary"]["total_resources_analyzed"])
            > 0.3
        ):

            recommendations["hiring_recommendations"].append(
                {
                    "type": "additional_capacity",
                    "reason": f"{recommendations['summary']['resources_over_threshold']} resources over utilization threshold",
                    "suggested_hires": max(
                        1, recommendations["summary"]["resources_over_threshold"] // 3
                    ),
                    "priority": (
                        "high"
                        if recommendations["summary"]["resources_over_threshold"] > 5
                        else "medium"
                    ),
                    "timeline": (
                        "immediate"
                        if recommendations["over_allocation_risks"]
                        else "within_quarter"
                    ),
                }
            )

        return recommendations

    # =====================================================================================
    # ADVANCED SKILL TRACKING AND COMPETENCY MANAGEMENT
    # =====================================================================================

    def create_skill_matrix(
        self,
        resource_ids: Optional[List[int]] = None,
        skill_categories: Optional[List[str]] = None,
        include_certifications: bool = True,
        include_proficiency_gaps: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a comprehensive skill matrix for resources.

        Args:
            resource_ids: Optional list of resource IDs to include
            skill_categories: Optional list of skill categories to focus on
            include_certifications: Whether to include certification information
            include_proficiency_gaps: Whether to analyze skill gaps

        Returns:
            Comprehensive skill matrix data
        """
        if resource_ids is None:
            resources = self.get_active_resources()
            resource_ids = [
                r.get("id") or r.get("ID")
                for r in resources
                if r.get("id") or r.get("ID")
            ]

        skill_matrix = {
            "created_date": datetime.now().isoformat(),
            "resources_analyzed": len(resource_ids),
            "skill_categories": skill_categories or [],
            "matrix_data": {},
            "skill_summary": {},
            "competency_gaps": [],
            "skill_distribution": {},
            "recommendations": [],
        }

        all_skills = set()
        resource_skills_data = {}

        # Collect skill data for all resources
        for resource_id in resource_ids:
            try:
                resource = self.get(resource_id)
                if not resource:
                    continue

                resource_name = f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip()
                skills = self.get_resource_skills(resource_id, verified_only=False)
                certifications = []

                if include_certifications:
                    certifications = self.get_resource_certifications(
                        resource_id, active_only=True
                    )

                # Process skills
                skill_data = {}
                for skill in skills:
                    skill_name = skill.get("SkillName", "")
                    skill_level = skill.get("SkillLevel", 1)
                    verified = skill.get("Verified", False)

                    if skill_categories and skill_name not in skill_categories:
                        continue

                    all_skills.add(skill_name)
                    skill_data[skill_name] = {
                        "level": skill_level,
                        "level_name": self._get_skill_level_name(skill_level),
                        "verified": verified,
                        "date_acquired": skill.get("DateAcquired"),
                        "notes": skill.get("Notes", ""),
                    }

                resource_skills_data[resource_id] = {
                    "resource_name": resource_name,
                    "department_id": resource.get("DepartmentID"),
                    "location_id": resource.get("LocationID"),
                    "title": resource.get("Title", ""),
                    "skills": skill_data,
                    "certifications": certifications,
                    "total_skills": len(skill_data),
                    "verified_skills": sum(
                        1 for s in skill_data.values() if s["verified"]
                    ),
                }

            except Exception as e:
                print(f"Error processing resource {resource_id}: {e}")
                continue

        # Build matrix structure
        skill_matrix["matrix_data"] = resource_skills_data
        skill_matrix["all_skills"] = sorted(list(all_skills))

        # Calculate skill distribution
        for skill_name in all_skills:
            levels = [
                data["skills"].get(skill_name, {}).get("level", 0)
                for data in resource_skills_data.values()
                if skill_name in data["skills"]
            ]

            skill_matrix["skill_distribution"][skill_name] = {
                "total_resources_with_skill": len(levels),
                "average_level": sum(levels) / len(levels) if levels else 0,
                "max_level": max(levels) if levels else 0,
                "min_level": min(levels) if levels else 0,
                "level_distribution": {
                    "beginner": len([l for l in levels if l == 1]),
                    "intermediate": len([l for l in levels if l == 2]),
                    "advanced": len([l for l in levels if l == 3]),
                    "expert": len([l for l in levels if l == 4]),
                    "master": len([l for l in levels if l == 5]),
                },
            }

        # Identify competency gaps if requested
        if include_proficiency_gaps:
            skill_matrix["competency_gaps"] = self._identify_skill_gaps(
                resource_skills_data, all_skills
            )

        # Generate recommendations
        skill_matrix["recommendations"] = self._generate_skill_matrix_recommendations(
            resource_skills_data, skill_matrix["skill_distribution"]
        )

        return skill_matrix

    def _get_skill_level_name(self, level: int) -> str:
        """Convert skill level number to name."""
        level_names = {
            1: "Beginner",
            2: "Intermediate",
            3: "Advanced",
            4: "Expert",
            5: "Master",
        }
        return level_names.get(level, "Unknown")

    def _identify_skill_gaps(
        self, resource_skills_data: Dict[str, Any], all_skills: set
    ) -> List[Dict[str, Any]]:
        """Identify skill gaps across resources."""
        gaps = []

        # Find skills that are missing or underrepresented
        for skill_name in all_skills:
            resources_with_skill = [
                (resource_id, data)
                for resource_id, data in resource_skills_data.items()
                if skill_name in data["skills"]
            ]

            total_resources = len(resource_skills_data)
            coverage_percentage = (len(resources_with_skill) / total_resources) * 100

            if coverage_percentage < 30:  # Less than 30% coverage
                gaps.append(
                    {
                        "skill_name": skill_name,
                        "coverage_percentage": coverage_percentage,
                        "resources_with_skill": len(resources_with_skill),
                        "total_resources": total_resources,
                        "gap_type": "coverage",
                        "severity": "high" if coverage_percentage < 10 else "medium",
                        "recommendation": f"Consider training more team members in {skill_name}",
                    }
                )

            # Check for skill level gaps (everyone is beginner level)
            if resources_with_skill:
                avg_level = sum(
                    data["skills"][skill_name]["level"]
                    for _, data in resources_with_skill
                ) / len(resources_with_skill)

                if avg_level < 2.5 and len(resources_with_skill) > 2:
                    gaps.append(
                        {
                            "skill_name": skill_name,
                            "average_level": avg_level,
                            "resources_with_skill": len(resources_with_skill),
                            "gap_type": "proficiency",
                            "severity": "medium",
                            "recommendation": f"Consider advanced training in {skill_name}",
                        }
                    )

        return gaps

    def _generate_skill_matrix_recommendations(
        self, resource_skills_data: Dict[str, Any], skill_distribution: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on skill matrix analysis."""
        recommendations = []

        # Find resources with very few skills
        for resource_id, data in resource_skills_data.items():
            if data["total_skills"] < 3:
                recommendations.append(
                    {
                        "type": "skill_development",
                        "resource_id": resource_id,
                        "resource_name": data["resource_name"],
                        "current_skills": data["total_skills"],
                        "recommendation": "Consider expanding skill set to increase versatility",
                        "priority": "high" if data["total_skills"] < 2 else "medium",
                    }
                )

        # Find critical skills with low coverage
        for skill_name, distribution in skill_distribution.items():
            coverage_rate = distribution["total_resources_with_skill"] / len(
                resource_skills_data
            )

            if coverage_rate < 0.2 and distribution["average_level"] > 3:
                recommendations.append(
                    {
                        "type": "knowledge_transfer",
                        "skill_name": skill_name,
                        "coverage_rate": coverage_rate,
                        "recommendation": f"Create knowledge sharing sessions for {skill_name}",
                        "priority": "high",
                    }
                )

        return recommendations

    def analyze_skill_gaps(
        self,
        target_skills: List[str],
        target_levels: Optional[Dict[str, int]] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps against target skill requirements.

        Args:
            target_skills: List of skills required
            target_levels: Optional mapping of skills to required levels
            department_id: Optional department filter
            location_id: Optional location filter

        Returns:
            Comprehensive skill gap analysis
        """
        if target_levels is None:
            target_levels = {
                skill: 3 for skill in target_skills
            }  # Default to Advanced level

        resources = self.get_active_resources(
            department_id=department_id, location_id=location_id
        )

        gap_analysis = {
            "analysis_date": datetime.now().isoformat(),
            "target_skills": target_skills,
            "target_levels": target_levels,
            "resources_analyzed": len(resources),
            "skill_gaps": [],
            "training_priorities": [],
            "resource_recommendations": [],
            "summary": {
                "total_skill_gaps": 0,
                "resources_meeting_all_requirements": 0,
                "most_critical_skill": None,
                "average_skill_coverage": 0,
            },
        }

        resources_meeting_requirements = 0
        total_gaps = 0
        skill_gap_counts = {skill: 0 for skill in target_skills}

        for resource in resources:
            resource_id = resource.get("id") or resource.get("ID")
            if not resource_id:
                continue

            try:
                resource_name = f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip()
                skills = self.get_resource_skills(resource_id, verified_only=True)
                resource_skills = {
                    skill.get("SkillName", ""): skill.get("SkillLevel", 1)
                    for skill in skills
                }

                resource_gaps = []
                meets_all_requirements = True

                for skill in target_skills:
                    required_level = target_levels.get(skill, 3)
                    current_level = resource_skills.get(skill, 0)

                    if current_level < required_level:
                        gap_severity = required_level - current_level
                        resource_gaps.append(
                            {
                                "skill": skill,
                                "required_level": required_level,
                                "current_level": current_level,
                                "gap_severity": gap_severity,
                                "training_needed": self._get_skill_level_name(
                                    required_level
                                ),
                            }
                        )

                        skill_gap_counts[skill] += 1
                        total_gaps += 1
                        meets_all_requirements = False

                if meets_all_requirements:
                    resources_meeting_requirements += 1

                if resource_gaps:
                    gap_analysis["skill_gaps"].append(
                        {
                            "resource_id": resource_id,
                            "resource_name": resource_name,
                            "department_id": resource.get("DepartmentID"),
                            "gaps": resource_gaps,
                            "total_gaps": len(resource_gaps),
                            "priority": (
                                "high"
                                if len(resource_gaps) > len(target_skills) / 2
                                else "medium"
                            ),
                        }
                    )

            except Exception as e:
                print(f"Error analyzing resource {resource_id}: {e}")
                continue

        # Generate training priorities
        for skill, gap_count in skill_gap_counts.items():
            if gap_count > 0:
                priority_score = gap_count / len(resources) * 100
                gap_analysis["training_priorities"].append(
                    {
                        "skill": skill,
                        "resources_needing_training": gap_count,
                        "percentage_needing_training": priority_score,
                        "required_level": target_levels.get(skill, 3),
                        "priority": (
                            "high"
                            if priority_score > 50
                            else "medium" if priority_score > 25 else "low"
                        ),
                    }
                )

        # Sort training priorities by percentage needing training
        gap_analysis["training_priorities"].sort(
            key=lambda x: x["percentage_needing_training"], reverse=True
        )

        # Update summary
        gap_analysis["summary"]["total_skill_gaps"] = total_gaps
        gap_analysis["summary"][
            "resources_meeting_all_requirements"
        ] = resources_meeting_requirements
        gap_analysis["summary"]["average_skill_coverage"] = (
            (resources_meeting_requirements / len(resources) * 100) if resources else 0
        )

        if gap_analysis["training_priorities"]:
            gap_analysis["summary"]["most_critical_skill"] = gap_analysis[
                "training_priorities"
            ][0]["skill"]

        return gap_analysis

    def generate_training_plan(
        self,
        resource_id: int,
        target_skills: Optional[List[str]] = None,
        skill_priorities: Optional[Dict[str, str]] = None,  # skill -> priority level
        timeline_weeks: int = 12,
    ) -> Dict[str, Any]:
        """
        Generate a personalized training plan for a resource.

        Args:
            resource_id: ID of the resource
            target_skills: Optional list of target skills to develop
            skill_priorities: Optional mapping of skills to priority levels
            timeline_weeks: Training timeline in weeks

        Returns:
            Comprehensive training plan
        """
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        resource_name = (
            f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip()
        )
        current_skills = self.get_resource_skills(resource_id, verified_only=False)
        certifications = self.get_resource_certifications(resource_id, active_only=True)

        # Create skill profile
        skill_profile = {}
        for skill in current_skills:
            skill_name = skill.get("SkillName", "")
            skill_profile[skill_name] = {
                "current_level": skill.get("SkillLevel", 1),
                "verified": skill.get("Verified", False),
                "date_acquired": skill.get("DateAcquired"),
            }

        training_plan = {
            "resource_id": resource_id,
            "resource_name": resource_name,
            "plan_created_date": datetime.now().isoformat(),
            "timeline_weeks": timeline_weeks,
            "current_skill_profile": skill_profile,
            "current_certifications": certifications,
            "training_objectives": [],
            "learning_path": [],
            "milestones": [],
            "estimated_costs": {
                "training_materials": 0,
                "certification_exams": 0,
                "external_training": 0,
                "total_estimated_cost": 0,
            },
            "success_metrics": [],
        }

        # Determine skills to develop
        skills_to_develop = target_skills or []

        # If no target skills specified, suggest improvements based on current skills
        if not skills_to_develop:
            # Suggest advancing existing beginner/intermediate skills
            for skill_name, profile in skill_profile.items():
                if profile["current_level"] < 4:  # Not expert level yet
                    skills_to_develop.append(skill_name)

        # Create training objectives and learning path
        weeks_used = 0
        for skill in skills_to_develop:
            if weeks_used >= timeline_weeks:
                break

            current_level = skill_profile.get(skill, {}).get("current_level", 0)
            priority = (
                skill_priorities.get(skill, "medium") if skill_priorities else "medium"
            )

            # Determine target level based on current level and priority
            if priority == "high":
                target_level = min(5, current_level + 2)
                weeks_needed = 4
            elif priority == "low":
                target_level = min(4, current_level + 1)
                weeks_needed = 2
            else:  # medium
                target_level = min(4, current_level + 1)
                weeks_needed = 3

            if target_level > current_level:
                training_objective = {
                    "skill": skill,
                    "current_level": current_level,
                    "target_level": target_level,
                    "priority": priority,
                    "estimated_weeks": weeks_needed,
                    "learning_activities": self._generate_learning_activities(
                        skill, current_level, target_level
                    ),
                }

                training_plan["training_objectives"].append(training_objective)

                # Add to learning path
                start_week = weeks_used + 1
                end_week = min(weeks_used + weeks_needed, timeline_weeks)

                training_plan["learning_path"].append(
                    {
                        "week_range": f"{start_week}-{end_week}",
                        "skill": skill,
                        "activities": training_objective["learning_activities"],
                        "target_milestone": f"Achieve {self._get_skill_level_name(target_level)} level",
                    }
                )

                weeks_used += weeks_needed

        # Create milestones
        for i, objective in enumerate(training_plan["training_objectives"]):
            milestone_week = min((i + 1) * 4, timeline_weeks)
            training_plan["milestones"].append(
                {
                    "week": milestone_week,
                    "skill": objective["skill"],
                    "milestone": f"Complete {objective['skill']} training to {self._get_skill_level_name(objective['target_level'])} level",
                    "success_criteria": [
                        "Pass skill assessment",
                        "Complete practical exercises",
                        "Receive peer/supervisor verification",
                    ],
                }
            )

        # Generate success metrics
        training_plan["success_metrics"] = [
            {
                "metric": "Skill Level Advancement",
                "target": f"Advance {len(training_plan['training_objectives'])} skills",
                "measurement": "Pre/post training assessments",
            },
            {
                "metric": "Training Completion Rate",
                "target": "100% completion of assigned modules",
                "measurement": "Learning management system tracking",
            },
            {
                "metric": "Knowledge Application",
                "target": "Apply new skills in real projects within 30 days",
                "measurement": "Project performance evaluation",
            },
        ]

        return training_plan

    def _generate_learning_activities(
        self, skill: str, current_level: int, target_level: int
    ) -> List[str]:
        """Generate appropriate learning activities for skill development."""
        activities = []

        level_gap = target_level - current_level

        # Base activities for all skills
        if current_level == 0:  # New skill
            activities.extend(
                [
                    f"Complete introductory course in {skill}",
                    f"Study fundamental concepts of {skill}",
                    "Find a mentor or subject matter expert",
                ]
            )

        if level_gap >= 1:
            activities.extend(
                [
                    f"Complete intermediate training in {skill}",
                    f"Practice {skill} through guided exercises",
                    "Join community or professional group",
                ]
            )

        if level_gap >= 2:
            activities.extend(
                [
                    f"Complete advanced coursework in {skill}",
                    f"Lead a project using {skill}",
                    "Attend industry conference or workshop",
                ]
            )

        if target_level >= 4:  # Expert level
            activities.extend(
                [
                    f"Obtain professional certification in {skill}",
                    f"Mentor others in {skill}",
                    f"Contribute to {skill} best practices documentation",
                ]
            )

        return activities[:6]  # Limit to 6 activities to keep manageable

    def track_competency_assessments(
        self,
        resource_id: int,
        skill_assessments: List[Dict[str, Any]],
        assessment_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Track and record competency assessment results.

        Args:
            resource_id: ID of the resource
            skill_assessments: List of skill assessment results
            assessment_date: Date of assessment (defaults to now)

        Returns:
            Assessment tracking record
        """
        if assessment_date is None:
            assessment_date = datetime.now().isoformat()

        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        resource_name = (
            f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip()
        )

        assessment_record = {
            "resource_id": resource_id,
            "resource_name": resource_name,
            "assessment_date": assessment_date,
            "assessments": [],
            "overall_performance": {},
            "improvement_areas": [],
            "strengths": [],
            "next_assessment_date": None,
        }

        total_score = 0
        total_assessments = 0
        scores_by_category = {}

        for assessment in skill_assessments:
            skill_name = assessment.get("skill")
            score = assessment.get("score", 0)  # Assuming 0-100 scale
            max_score = assessment.get("max_score", 100)
            assessor = assessment.get("assessor")
            notes = assessment.get("notes", "")
            category = assessment.get("category", "Technical")

            normalized_score = (score / max_score) * 100 if max_score > 0 else 0

            assessment_data = {
                "skill": skill_name,
                "score": score,
                "max_score": max_score,
                "normalized_score": normalized_score,
                "assessor": assessor,
                "notes": notes,
                "category": category,
                "performance_level": self._determine_performance_level(
                    normalized_score
                ),
            }

            assessment_record["assessments"].append(assessment_data)

            total_score += normalized_score
            total_assessments += 1

            # Track by category
            if category not in scores_by_category:
                scores_by_category[category] = []
            scores_by_category[category].append(normalized_score)

            # Identify improvement areas and strengths
            if normalized_score < 70:
                assessment_record["improvement_areas"].append(
                    {
                        "skill": skill_name,
                        "score": normalized_score,
                        "recommendation": f"Focus on improving {skill_name} skills",
                    }
                )
            elif normalized_score >= 85:
                assessment_record["strengths"].append(
                    {
                        "skill": skill_name,
                        "score": normalized_score,
                        "note": f"Strong performance in {skill_name}",
                    }
                )

        # Calculate overall performance
        if total_assessments > 0:
            avg_score = total_score / total_assessments
            assessment_record["overall_performance"] = {
                "average_score": avg_score,
                "performance_level": self._determine_performance_level(avg_score),
                "total_assessments": total_assessments,
                "category_breakdown": {
                    category: sum(scores) / len(scores)
                    for category, scores in scores_by_category.items()
                },
            }

        # Suggest next assessment date (quarterly)
        next_assessment = datetime.fromisoformat(
            assessment_date.replace("Z", "+00:00")
        ) + timedelta(days=90)
        assessment_record["next_assessment_date"] = next_assessment.isoformat()

        # This would typically be stored in a database
        # For now, we'll return the assessment record
        return assessment_record

    def _determine_performance_level(self, score: float) -> str:
        """Determine performance level based on score."""
        if score >= 90:
            return "Exceptional"
        elif score >= 80:
            return "Proficient"
        elif score >= 70:
            return "Developing"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Below Expectations"

    # =====================================================================================
    # ADVANCED UTILIZATION REPORTING AND PERFORMANCE METRICS
    # =====================================================================================

    def generate_utilization_dashboard(
        self,
        resource_ids: Optional[List[int]] = None,
        date_range: Optional[Tuple[str, str]] = None,
        department_id: Optional[int] = None,
        location_id: Optional[int] = None,
        include_trends: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive utilization dashboard for resources.

        Args:
            resource_ids: Optional list of specific resource IDs
            date_range: Date range for analysis (defaults to last 30 days)
            department_id: Optional department filter
            location_id: Optional location filter
            include_trends: Whether to include trend analysis

        Returns:
            Comprehensive utilization dashboard data
        """
        if date_range is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date.isoformat(), end_date.isoformat())

        # Get resources to analyze
        if resource_ids is None:
            resources = self.get_active_resources(
                department_id=department_id, location_id=location_id
            )
            resource_ids = [
                r.get("id") or r.get("ID")
                for r in resources
                if r.get("id") or r.get("ID")
            ]

        dashboard = {
            "generated_date": datetime.now().isoformat(),
            "analysis_period": date_range,
            "resources_analyzed": len(resource_ids),
            "filters": {
                "department_id": department_id,
                "location_id": location_id,
            },
            "summary_metrics": {
                "total_capacity_hours": 0,
                "total_billable_hours": 0,
                "total_non_billable_hours": 0,
                "overall_utilization_rate": 0,
                "billable_utilization_rate": 0,
                "total_revenue": 0,
                "total_cost": 0,
                "profit_margin": 0,
                "average_hourly_rate": 0,
            },
            "resource_details": [],
            "department_breakdown": {},
            "utilization_distribution": {
                "over_allocated": 0,
                "high_utilization": 0,
                "optimal_utilization": 0,
                "under_utilized": 0,
            },
            "trend_analysis": [],
            "recommendations": [],
        }

        department_totals = {}
        total_revenue = 0
        total_cost = 0
        all_hourly_rates = []

        for resource_id in resource_ids:
            try:
                resource = self.get(resource_id)
                if not resource:
                    continue

                resource_name = f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip()
                dept_id = resource.get("DepartmentID")

                # Get utilization data
                utilization = self.get_resource_utilization(resource_id, date_range)
                time_entries = self.get_resource_time_entries(
                    resource_id, date_range[0], date_range[1]
                )

                # Calculate revenue and cost
                resource_revenue = 0
                resource_cost = 0
                for entry in time_entries:
                    hours = entry.get("HoursWorked", 0)
                    hourly_rate = (
                        entry.get("HourlyRate", 0) or resource.get("HourlyRate", 0) or 0
                    )
                    hourly_cost = (
                        entry.get("HourlyCost", 0) or resource.get("HourlyCost", 0) or 0
                    )

                    if entry.get("BillableToAccount"):
                        resource_revenue += hours * hourly_rate

                    resource_cost += hours * hourly_cost

                    if hourly_rate > 0:
                        all_hourly_rates.append(hourly_rate)

                total_revenue += resource_revenue
                total_cost += resource_cost

                # Classify utilization level
                util_pct = utilization["summary"]["utilization_percentage"]
                if util_pct > 95:
                    util_category = "over_allocated"
                elif util_pct > 85:
                    util_category = "high_utilization"
                elif util_pct > 65:
                    util_category = "optimal_utilization"
                else:
                    util_category = "under_utilized"

                dashboard["utilization_distribution"][util_category] += 1

                # Add to resource details
                resource_detail = {
                    "resource_id": resource_id,
                    "resource_name": resource_name,
                    "department_id": dept_id,
                    "location_id": resource.get("LocationID"),
                    "title": resource.get("Title", ""),
                    "utilization_percentage": util_pct,
                    "billable_utilization_percentage": utilization["summary"][
                        "billable_utilization_percentage"
                    ],
                    "capacity_hours": utilization["summary"]["capacity_hours"],
                    "total_hours": utilization["summary"]["total_hours"],
                    "billable_hours": utilization["summary"]["billable_hours"],
                    "non_billable_hours": utilization["summary"]["non_billable_hours"],
                    "revenue_generated": resource_revenue,
                    "cost_incurred": resource_cost,
                    "profit_contribution": resource_revenue - resource_cost,
                    "utilization_category": util_category,
                    "hourly_rate": resource.get("HourlyRate", 0) or 0,
                }

                dashboard["resource_details"].append(resource_detail)

                # Update summary metrics
                dashboard["summary_metrics"]["total_capacity_hours"] += utilization[
                    "summary"
                ]["capacity_hours"]
                dashboard["summary_metrics"]["total_billable_hours"] += utilization[
                    "summary"
                ]["billable_hours"]
                dashboard["summary_metrics"]["total_non_billable_hours"] += utilization[
                    "summary"
                ]["non_billable_hours"]

                # Track department totals
                if dept_id:
                    if dept_id not in department_totals:
                        department_totals[dept_id] = {
                            "resources": 0,
                            "total_hours": 0,
                            "billable_hours": 0,
                            "capacity_hours": 0,
                            "revenue": 0,
                            "cost": 0,
                        }

                    dept_totals = department_totals[dept_id]
                    dept_totals["resources"] += 1
                    dept_totals["total_hours"] += utilization["summary"]["total_hours"]
                    dept_totals["billable_hours"] += utilization["summary"][
                        "billable_hours"
                    ]
                    dept_totals["capacity_hours"] += utilization["summary"][
                        "capacity_hours"
                    ]
                    dept_totals["revenue"] += resource_revenue
                    dept_totals["cost"] += resource_cost

            except Exception as e:
                print(f"Error analyzing resource {resource_id}: {e}")
                continue

        # Calculate summary metrics
        if dashboard["summary_metrics"]["total_capacity_hours"] > 0:
            dashboard["summary_metrics"]["overall_utilization_rate"] = (
                (
                    dashboard["summary_metrics"]["total_billable_hours"]
                    + dashboard["summary_metrics"]["total_non_billable_hours"]
                )
                / dashboard["summary_metrics"]["total_capacity_hours"]
                * 100
            )
            dashboard["summary_metrics"]["billable_utilization_rate"] = (
                dashboard["summary_metrics"]["total_billable_hours"]
                / dashboard["summary_metrics"]["total_capacity_hours"]
                * 100
            )

        dashboard["summary_metrics"]["total_revenue"] = total_revenue
        dashboard["summary_metrics"]["total_cost"] = total_cost
        dashboard["summary_metrics"]["profit_margin"] = total_revenue - total_cost

        if all_hourly_rates:
            dashboard["summary_metrics"]["average_hourly_rate"] = sum(
                all_hourly_rates
            ) / len(all_hourly_rates)

        # Calculate department breakdown
        for dept_id, totals in department_totals.items():
            dashboard["department_breakdown"][dept_id] = {
                "resources_count": totals["resources"],
                "utilization_percentage": (
                    (totals["total_hours"] / totals["capacity_hours"] * 100)
                    if totals["capacity_hours"] > 0
                    else 0
                ),
                "billable_utilization_percentage": (
                    (totals["billable_hours"] / totals["capacity_hours"] * 100)
                    if totals["capacity_hours"] > 0
                    else 0
                ),
                "revenue": totals["revenue"],
                "cost": totals["cost"],
                "profit_margin": totals["revenue"] - totals["cost"],
                "average_utilization": (
                    (totals["total_hours"] / totals["capacity_hours"] * 100)
                    if totals["capacity_hours"] > 0
                    else 0
                ),
            }

        # Generate trend analysis if requested
        if include_trends:
            dashboard["trend_analysis"] = self._generate_utilization_trends(
                resource_ids, date_range
            )

        # Generate recommendations
        dashboard["recommendations"] = self._generate_utilization_recommendations(
            dashboard
        )

        return dashboard

    def _generate_utilization_trends(
        self, resource_ids: List[int], date_range: Tuple[str, str]
    ) -> List[Dict[str, Any]]:
        """Generate trend analysis for utilization data."""
        trends = []

        start_date = datetime.fromisoformat(date_range[0].replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(date_range[1].replace("Z", "+00:00"))

        # Split into weekly periods
        current_date = start_date
        weekly_data = []

        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)
            week_range = (current_date.isoformat(), week_end.isoformat())

            week_utilization = []
            week_revenue = 0

            for resource_id in resource_ids[:10]:  # Limit for performance
                try:
                    utilization = self.get_resource_utilization(resource_id, week_range)
                    week_utilization.append(
                        utilization["summary"]["utilization_percentage"]
                    )

                    # Estimate revenue for the week
                    time_entries = self.get_resource_time_entries(
                        resource_id, week_range[0], week_range[1]
                    )
                    for entry in time_entries:
                        if entry.get("BillableToAccount"):
                            week_revenue += entry.get("HoursWorked", 0) * entry.get(
                                "HourlyRate", 0
                            )

                except Exception:
                    continue

            if week_utilization:
                weekly_data.append(
                    {
                        "week_start": current_date.isoformat(),
                        "average_utilization": sum(week_utilization)
                        / len(week_utilization),
                        "revenue": week_revenue,
                        "resources_tracked": len(week_utilization),
                    }
                )

            current_date = week_end

        # Calculate trends
        if len(weekly_data) >= 2:
            utilization_trend = (
                weekly_data[-1]["average_utilization"]
                - weekly_data[0]["average_utilization"]
            )
            revenue_trend = weekly_data[-1]["revenue"] - weekly_data[0]["revenue"]

            trends.append(
                {
                    "metric": "utilization",
                    "trend_direction": (
                        "increasing" if utilization_trend > 0 else "decreasing"
                    ),
                    "trend_magnitude": abs(utilization_trend),
                    "weekly_data": weekly_data,
                }
            )

            trends.append(
                {
                    "metric": "revenue",
                    "trend_direction": (
                        "increasing" if revenue_trend > 0 else "decreasing"
                    ),
                    "trend_magnitude": abs(revenue_trend),
                    "weekly_data": [
                        {"week_start": w["week_start"], "revenue": w["revenue"]}
                        for w in weekly_data
                    ],
                }
            )

        return trends

    def _generate_utilization_recommendations(
        self, dashboard: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on utilization analysis."""
        recommendations = []

        # Check overall utilization rates
        overall_util = dashboard["summary_metrics"]["overall_utilization_rate"]
        billable_util = dashboard["summary_metrics"]["billable_utilization_rate"]

        if overall_util < 65:
            recommendations.append(
                {
                    "type": "capacity_optimization",
                    "priority": "high",
                    "message": "Overall team utilization is low. Consider reallocating resources or reducing capacity.",
                    "target_metric": "overall_utilization_rate",
                    "current_value": overall_util,
                    "target_value": 80,
                }
            )

        if billable_util < 70:
            recommendations.append(
                {
                    "type": "billability_improvement",
                    "priority": "medium",
                    "message": "Billable utilization is below target. Focus on reducing non-billable time.",
                    "target_metric": "billable_utilization_rate",
                    "current_value": billable_util,
                    "target_value": 75,
                }
            )

        # Check for over-allocated resources
        over_allocated = dashboard["utilization_distribution"]["over_allocated"]
        total_resources = dashboard["resources_analyzed"]

        if over_allocated / total_resources > 0.2:  # More than 20% over-allocated
            recommendations.append(
                {
                    "type": "workload_balancing",
                    "priority": "high",
                    "message": f"{over_allocated} resources are over-allocated. Redistribute workload to prevent burnout.",
                    "affected_resources": over_allocated,
                }
            )

        # Check profit margins
        profit_margin = dashboard["summary_metrics"]["profit_margin"]
        total_revenue = dashboard["summary_metrics"]["total_revenue"]

        if profit_margin > 0 and total_revenue > 0:
            margin_percentage = (profit_margin / total_revenue) * 100
            if margin_percentage < 20:
                recommendations.append(
                    {
                        "type": "profitability_improvement",
                        "priority": "medium",
                        "message": f"Profit margin is {margin_percentage:.1f}%. Consider reviewing rates or reducing costs.",
                        "current_margin_percentage": margin_percentage,
                    }
                )

        return recommendations

    def generate_performance_scorecard(
        self,
        resource_id: int,
        evaluation_period_months: int = 6,
        include_peer_comparison: bool = True,
        include_goal_tracking: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive performance scorecard for a resource.

        Args:
            resource_id: ID of the resource
            evaluation_period_months: Number of months to evaluate
            include_peer_comparison: Whether to include peer comparisons
            include_goal_tracking: Whether to include goal tracking metrics

        Returns:
            Comprehensive performance scorecard
        """
        resource = self.get(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")

        resource_name = (
            f"{resource.get('FirstName', '')} {resource.get('LastName', '')}".strip()
        )
        department_id = resource.get("DepartmentID")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=evaluation_period_months * 30)
        date_range = (start_date.isoformat(), end_date.isoformat())

        scorecard = {
            "resource_id": resource_id,
            "resource_name": resource_name,
            "evaluation_period": f"{evaluation_period_months} months",
            "evaluation_date_range": date_range,
            "overall_score": 0,
            "performance_metrics": {},
            "skill_assessment": {},
            "project_contributions": [],
            "utilization_analysis": {},
            "financial_impact": {},
            "peer_comparison": {},
            "goal_tracking": {},
            "strengths": [],
            "improvement_areas": [],
            "development_recommendations": [],
        }

        # Get utilization data
        utilization = self.get_resource_utilization(resource_id, date_range)
        scorecard["utilization_analysis"] = {
            "average_utilization": utilization["summary"]["utilization_percentage"],
            "billable_utilization": utilization["summary"][
                "billable_utilization_percentage"
            ],
            "total_hours_worked": utilization["summary"]["total_hours"],
            "billable_hours": utilization["summary"]["billable_hours"],
            "efficiency_score": utilization["efficiency_metrics"][
                "average_hours_per_day"
            ],
        }

        # Calculate financial impact
        profitability = self.get_resource_profitability(resource_id, date_range)
        scorecard["financial_impact"] = {
            "total_revenue_generated": profitability["total_revenue"],
            "total_cost": profitability["total_cost"],
            "profit_contribution": profitability["gross_profit"],
            "profit_margin_percentage": profitability["gross_margin_percentage"],
            "average_hourly_rate": profitability["average_hourly_rate"],
        }

        # Get skills assessment
        skills = self.get_resource_skills(resource_id, verified_only=True)
        certifications = self.get_resource_certifications(resource_id, active_only=True)

        scorecard["skill_assessment"] = {
            "total_verified_skills": len(skills),
            "active_certifications": len(certifications),
            "skill_diversity_score": min(len(skills) / 10, 1) * 100,  # Scale to 100
            "certification_currency": len(
                [
                    c
                    for c in certifications
                    if not self._is_certification_expiring_soon(c)
                ]
            ),
        }

        # Project contributions (simplified)
        time_entries = self.get_resource_time_entries(
            resource_id, date_range[0], date_range[1]
        )

        projects_worked = set()
        for entry in time_entries:
            project_id = entry.get("ProjectID")
            if project_id:
                projects_worked.add(project_id)

        scorecard["project_contributions"] = [
            {
                "project_id": pid,
                "hours_contributed": sum(
                    entry.get("HoursWorked", 0)
                    for entry in time_entries
                    if entry.get("ProjectID") == pid
                ),
                "billable_hours": sum(
                    entry.get("HoursWorked", 0)
                    for entry in time_entries
                    if entry.get("ProjectID") == pid and entry.get("BillableToAccount")
                ),
            }
            for pid in projects_worked
        ]

        # Performance metrics scoring
        metrics = {
            "utilization_score": min(
                utilization["summary"]["utilization_percentage"] / 85 * 100, 100
            ),
            "billability_score": min(
                utilization["summary"]["billable_utilization_percentage"] / 75 * 100,
                100,
            ),
            "profitability_score": (
                min(profitability["gross_margin_percentage"] / 30 * 100, 100)
                if profitability["gross_margin_percentage"] > 0
                else 50
            ),
            "skill_development_score": scorecard["skill_assessment"][
                "skill_diversity_score"
            ],
            "project_diversity_score": min(len(projects_worked) / 5 * 100, 100),
        }

        scorecard["performance_metrics"] = metrics
        scorecard["overall_score"] = sum(metrics.values()) / len(metrics)

        # Peer comparison if requested
        if include_peer_comparison and department_id:
            peer_resources = self.get_active_resources(department_id=department_id)
            peer_ids = [
                r.get("id") or r.get("ID")
                for r in peer_resources
                if (r.get("id") or r.get("ID")) != resource_id
            ]

            if peer_ids:
                peer_comparisons = self.compare_resource_utilization(
                    peer_ids, date_range
                )
                avg_peer_util = sum(
                    p["utilization_percentage"] for p in peer_comparisons
                ) / len(peer_comparisons)
                avg_peer_billable = sum(
                    p["billable_utilization_percentage"] for p in peer_comparisons
                ) / len(peer_comparisons)

                scorecard["peer_comparison"] = {
                    "department_average_utilization": avg_peer_util,
                    "department_average_billable_utilization": avg_peer_billable,
                    "utilization_percentile": self._calculate_percentile(
                        utilization["summary"]["utilization_percentage"],
                        [p["utilization_percentage"] for p in peer_comparisons],
                    ),
                    "peers_analyzed": len(peer_ids),
                }

        # Identify strengths and improvement areas
        if metrics["utilization_score"] >= 85:
            scorecard["strengths"].append("Excellent utilization rate")
        if metrics["billability_score"] >= 85:
            scorecard["strengths"].append("High billable utilization")
        if metrics["profitability_score"] >= 85:
            scorecard["strengths"].append("Strong profit contribution")
        if len(projects_worked) >= 3:
            scorecard["strengths"].append("Good project diversity")

        if metrics["utilization_score"] < 70:
            scorecard["improvement_areas"].append("Increase overall utilization")
        if metrics["billability_score"] < 70:
            scorecard["improvement_areas"].append("Focus on billable activities")
        if len(skills) < 5:
            scorecard["improvement_areas"].append("Expand skill set")

        # Development recommendations
        if len(scorecard["improvement_areas"]) > 0:
            scorecard["development_recommendations"] = [
                "Create development plan to address improvement areas",
                "Consider additional training or mentoring",
                "Set specific performance goals for next evaluation period",
            ]

        return scorecard

    def _is_certification_expiring_soon(
        self, certification: Dict[str, Any], days_ahead: int = 90
    ) -> bool:
        """Check if a certification is expiring soon."""
        expiry_date_str = certification.get("ExpirationDate")
        if not expiry_date_str:
            return False

        try:
            expiry_date = datetime.fromisoformat(expiry_date_str.replace("Z", "+00:00"))
            return (expiry_date - datetime.now()).days <= days_ahead
        except (ValueError, AttributeError):
            return False

    def _calculate_percentile(self, value: float, peer_values: List[float]) -> float:
        """Calculate the percentile ranking of a value among peers."""
        if not peer_values:
            return 50.0

        all_values = peer_values + [value]
        all_values.sort()
        rank = all_values.index(value) + 1
        return (rank / len(all_values)) * 100

    def analyze_resource_efficiency_trends(
        self,
        resource_ids: Optional[List[int]] = None,
        analysis_months: int = 12,
        trend_metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze efficiency trends for resources over time.

        Args:
            resource_ids: Optional list of resource IDs to analyze
            analysis_months: Number of months to analyze
            trend_metrics: Specific metrics to track trends for

        Returns:
            Comprehensive trend analysis
        """
        if resource_ids is None:
            resources = self.get_active_resources()
            resource_ids = [
                r.get("id") or r.get("ID")
                for r in resources
                if r.get("id") or r.get("ID")
            ]

        if trend_metrics is None:
            trend_metrics = [
                "utilization_percentage",
                "billable_utilization_percentage",
                "revenue_per_hour",
                "project_completion_rate",
            ]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=analysis_months * 30)

        trend_analysis = {
            "analysis_date": end_date.isoformat(),
            "analysis_period_months": analysis_months,
            "resources_analyzed": len(resource_ids),
            "trend_metrics": trend_metrics,
            "monthly_data": [],
            "resource_trends": {},
            "summary_trends": {},
            "insights": [],
        }

        # Generate monthly data points
        current_date = start_date
        monthly_data = []

        while current_date < end_date:
            month_end = min(current_date.replace(day=28) + timedelta(days=4), end_date)
            month_end = month_end.replace(day=1) - timedelta(
                days=1
            )  # Last day of month

            if month_end <= current_date:
                break

            month_range = (current_date.isoformat(), month_end.isoformat())

            month_data = {
                "month": current_date.strftime("%Y-%m"),
                "start_date": current_date.isoformat(),
                "end_date": month_end.isoformat(),
                "metrics": {metric: [] for metric in trend_metrics},
            }

            # Collect data for all resources for this month
            for resource_id in resource_ids[:20]:  # Limit for performance
                try:
                    utilization = self.get_resource_utilization(
                        resource_id, month_range
                    )
                    profitability = self.get_resource_profitability(
                        resource_id, month_range
                    )

                    if (
                        utilization["summary"]["total_hours"] > 0
                    ):  # Only include if resource was active
                        month_data["metrics"]["utilization_percentage"].append(
                            utilization["summary"]["utilization_percentage"]
                        )
                        month_data["metrics"]["billable_utilization_percentage"].append(
                            utilization["summary"]["billable_utilization_percentage"]
                        )

                        revenue_per_hour = (
                            profitability["total_revenue"]
                            / utilization["summary"]["total_hours"]
                            if utilization["summary"]["total_hours"] > 0
                            else 0
                        )
                        month_data["metrics"]["revenue_per_hour"].append(
                            revenue_per_hour
                        )

                        # Placeholder for project completion rate
                        month_data["metrics"]["project_completion_rate"].append(85.0)

                except Exception as e:
                    continue

            # Calculate averages for the month
            for metric in trend_metrics:
                values = month_data["metrics"][metric]
                month_data["metrics"][metric] = (
                    sum(values) / len(values) if values else 0
                )

            monthly_data.append(month_data)
            current_date = month_end + timedelta(days=1)
            current_date = current_date.replace(day=1)  # First day of next month

        trend_analysis["monthly_data"] = monthly_data

        # Calculate trends for each metric
        for metric in trend_metrics:
            metric_values = [month["metrics"][metric] for month in monthly_data]

            if len(metric_values) >= 2:
                # Simple trend calculation
                start_value = metric_values[0]
                end_value = metric_values[-1]
                trend_direction = (
                    "improving" if end_value > start_value else "declining"
                )
                trend_magnitude = abs(end_value - start_value)

                # Calculate average monthly change
                monthly_changes = []
                for i in range(1, len(metric_values)):
                    monthly_changes.append(metric_values[i] - metric_values[i - 1])

                avg_monthly_change = (
                    sum(monthly_changes) / len(monthly_changes)
                    if monthly_changes
                    else 0
                )

                trend_analysis["summary_trends"][metric] = {
                    "trend_direction": trend_direction,
                    "trend_magnitude": trend_magnitude,
                    "average_monthly_change": avg_monthly_change,
                    "start_value": start_value,
                    "end_value": end_value,
                    "peak_value": max(metric_values),
                    "lowest_value": min(metric_values),
                }

        # Generate insights
        insights = []

        for metric, trend in trend_analysis["summary_trends"].items():
            if trend["trend_direction"] == "improving":
                insights.append(
                    {
                        "type": "positive_trend",
                        "metric": metric,
                        "message": f"{metric.replace('_', ' ').title()} has improved by {trend['trend_magnitude']:.1f} over the analysis period",
                    }
                )
            elif trend["trend_magnitude"] > 5:  # Significant decline
                insights.append(
                    {
                        "type": "negative_trend",
                        "metric": metric,
                        "message": f"{metric.replace('_', ' ').title()} has declined by {trend['trend_magnitude']:.1f}, requiring attention",
                    }
                )

        trend_analysis["insights"] = insights

        return trend_analysis
