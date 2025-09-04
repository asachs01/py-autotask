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
