"""
Entity manager for organizing and accessing different Autotask entities.

This module provides the EntityManager class that creates and manages
entity instances, providing both direct access and dynamic entity creation.
"""

import logging
from typing import TYPE_CHECKING, Dict

# Week 2 entities - Human Resources & Resource Management
from .accounts import AccountsEntity
from .allocation_codes import AllocationCodesEntity
from .attachments import AttachmentsEntity
from .base import BaseEntity
from .billing_codes import BillingCodesEntity
from .billing_items import BillingItemsEntity
from .business_divisions import BusinessDivisionsEntity
from .business_rules import BusinessRulesEntity
from .change_requests import ChangeRequestsEntity
from .companies import CompaniesEntity
from .compliance_frameworks import ComplianceFrameworksEntity
from .configuration_item_types import ConfigurationItemTypesEntity
from .configuration_items import ConfigurationItemsEntity
from .contacts import ContactsEntity
from .contract_adjustments import ContractAdjustmentsEntity
from .contract_blocks import ContractBlocksEntity
from .contract_charges import ContractChargesEntity
from .contract_exclusions import ContractExclusionsEntity
from .contract_services import ContractServicesEntity
from .contracts import ContractsEntity
from .custom_fields import CustomFieldsEntity
from .dashboards import DashboardsEntity
from .departments import DepartmentsEntity
from .expenses import ExpensesEntity
from .holiday_sets import HolidaySetsEntity
from .incident_types import IncidentTypesEntity
from .invoices import InvoicesEntity
from .notes import NotesEntity
from .notification_rules import NotificationRulesEntity
from .operations import OperationsEntity
from .products import ProductsEntity
from .project_budgets import ProjectBudgetsEntity
from .project_charges import ProjectChargesEntity
from .project_milestones import ProjectMilestonesEntity

# Week 4 entities - Project Management & Workflow
from .project_phases import ProjectPhasesEntity
from .project_reports import ProjectReportsEntity
from .project_templates import ProjectTemplatesEntity
from .projects import ProjectsEntity
from .purchase_orders import PurchaseOrdersEntity
from .quotes import QuotesEntity
from .resource_allocation import ResourceAllocationEntity
from .resource_roles import ResourceRolesEntity
from .resource_skills import ResourceSkillsEntity
from .resources import ResourcesEntity

# Week 5 entities - Security & Compliance
from .security_policies import SecurityPoliciesEntity
from .service_calls import ServiceCallsEntity
from .service_level_agreements import ServiceLevelAgreementsEntity

# Week 3 entities - Service Delivery & Operations
from .subscriptions import SubscriptionsEntity
from .system_configuration import SystemConfigurationEntity

# Week 6 entities - System Management
from .system_health import SystemHealthEntity
from .task_dependencies import TaskDependenciesEntity
from .tasks import TasksEntity
from .teams import TeamsEntity
from .ticket_categories import TicketCategoriesEntity
from .ticket_priorities import TicketPrioritiesEntity
from .ticket_sources import TicketSourcesEntity
from .ticket_statuses import TicketStatusesEntity
from .tickets import TicketsEntity
from .time_entries import TimeEntriesEntity
from .vendor_types import VendorTypesEntity
from .work_types import WorkTypesEntity
from .workflow_rules import WorkflowRulesEntity as WorkflowRulesEntityActual
from .workflows import WorkflowRulesEntity
from .workflows import WorkflowRulesEntity as WorkflowsEntity

if TYPE_CHECKING:
    from ..client import AutotaskClient

logger = logging.getLogger(__name__)


class EntityManager:
    """
    Manager for all entity operations.

    Provides access to entity-specific handlers and can dynamically
    create handlers for entities not explicitly defined.
    """

    # Mapping of entity names to their specific handler classes
    ENTITY_CLASSES = {
        # Core entities
        "Tickets": TicketsEntity,
        "Companies": CompaniesEntity,
        "Contacts": ContactsEntity,
        "Projects": ProjectsEntity,
        "Resources": ResourcesEntity,
        "Contracts": ContractsEntity,
        "TimeEntries": TimeEntriesEntity,
        "Attachments": AttachmentsEntity,
        # Contract-related entities
        "ContractServices": ContractServicesEntity,
        "ContractBlocks": ContractBlocksEntity,
        "ContractAdjustments": ContractAdjustmentsEntity,
        "ContractExclusions": ContractExclusionsEntity,
        # Financial entities
        "BillingCodes": BillingCodesEntity,
        "BillingItems": BillingItemsEntity,
        "ContractCharges": ContractChargesEntity,
        "Invoices": InvoicesEntity,
        "ProjectCharges": ProjectChargesEntity,
        "Quotes": QuotesEntity,
        "PurchaseOrders": PurchaseOrdersEntity,
        "Expenses": ExpensesEntity,
        # Service desk entities
        "TicketCategories": TicketCategoriesEntity,
        "TicketStatuses": TicketStatusesEntity,
        "TicketPriorities": TicketPrioritiesEntity,
        "TicketSources": TicketSourcesEntity,
        # Human Resources & Resource Management entities (Week 2)
        "Accounts": AccountsEntity,
        "Departments": DepartmentsEntity,
        "ResourceRoles": ResourceRolesEntity,
        "ResourceSkills": ResourceSkillsEntity,
        "Teams": TeamsEntity,
        "WorkTypes": WorkTypesEntity,
        # Service Delivery & Operations entities (Week 3)
        "Subscriptions": SubscriptionsEntity,
        "ServiceLevelAgreements": ServiceLevelAgreementsEntity,
        "Products": ProductsEntity,
        "BusinessDivisions": BusinessDivisionsEntity,
        "Operations": OperationsEntity,
        # Operational entities
        "ConfigurationItems": ConfigurationItemsEntity,
        "ServiceCalls": ServiceCallsEntity,
        "Tasks": TasksEntity,
        "Notes": NotesEntity,
        # Project Management & Workflow entities (Week 4)
        "ProjectPhases": ProjectPhasesEntity,
        "ProjectMilestones": ProjectMilestonesEntity,
        "AllocationCodes": AllocationCodesEntity,
        "HolidaySets": HolidaySetsEntity,
        "WorkflowRules": WorkflowRulesEntityActual,
        "Workflows": WorkflowsEntity,
        "ProjectTemplates": ProjectTemplatesEntity,
        "ResourceAllocation": ResourceAllocationEntity,
        "ProjectBudgets": ProjectBudgetsEntity,
        "TaskDependencies": TaskDependenciesEntity,
        "ProjectReports": ProjectReportsEntity,
        # Additional Service Delivery & Operations entities
        "ChangeRequests": ChangeRequestsEntity,
        "VendorTypes": VendorTypesEntity,
        "IncidentTypes": IncidentTypesEntity,
        "ConfigurationItemTypes": ConfigurationItemTypesEntity,
        # Security & Compliance entities (Week 5)
        "SecurityPolicies": SecurityPoliciesEntity,
        "ComplianceFrameworks": ComplianceFrameworksEntity,
        "CustomFields": CustomFieldsEntity,
        "BusinessRules": BusinessRulesEntity,
        "NotificationRules": NotificationRulesEntity,
        # System Management entities (Week 6)
        "SystemHealth": SystemHealthEntity,
        "SystemConfiguration": SystemConfigurationEntity,
        "Dashboards": DashboardsEntity,
    }

    def __init__(self, client: "AutotaskClient") -> None:
        """
        Initialize the entity manager.

        Args:
            client: The AutotaskClient instance
        """
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.EntityManager")
        self._entity_cache: Dict[str, BaseEntity] = {}
        self._time_entries: TimeEntriesEntity | None = None
        self._attachments: AttachmentsEntity | None = None

    def get_entity(self, entity_name: str) -> BaseEntity:
        """
        Get an entity handler, creating it if necessary.

        Args:
            entity_name: Name of the entity (e.g., 'Tickets', 'Companies')

        Returns:
            Entity handler instance
        """
        if entity_name not in self._entity_cache:
            # Check if we have a specific class for this entity
            entity_class = self.ENTITY_CLASSES.get(entity_name, BaseEntity)
            self._entity_cache[entity_name] = entity_class(self.client, entity_name)
            self.logger.debug(f"Created {entity_class.__name__} for {entity_name}")

        return self._entity_cache[entity_name]

    def __getattr__(self, name: str) -> BaseEntity:
        """
        Dynamically access entities as attributes.

        This allows for accessing entities like:
        manager.tickets, manager.companies, etc.

        Args:
            name: Entity name in lowercase

        Returns:
            Entity handler instance
        """
        # Convert attribute name to proper entity name
        entity_name = name.capitalize()

        # Handle special cases for entity naming
        if entity_name == "Companies":
            entity_name = "Companies"
        elif entity_name == "Tickets":
            entity_name = "Tickets"
        # Add more special cases as needed

        return self.get_entity(entity_name)

    # Direct properties for common entities (for better IDE support)
    @property
    def tickets(self) -> TicketsEntity:
        """Access to Tickets entity operations."""
        return self.get_entity("Tickets")

    @property
    def companies(self) -> CompaniesEntity:
        """Access to Companies entity operations."""
        return self.get_entity("Companies")

    @property
    def contacts(self) -> ContactsEntity:
        """Access to Contacts entity operations."""
        return self.get_entity("Contacts")

    @property
    def projects(self) -> ProjectsEntity:
        """Access to Projects entity operations."""
        return self.get_entity("Projects")

    @property
    def resources(self) -> ResourcesEntity:
        """Access to Resources entity operations."""
        return self.get_entity("Resources")

    @property
    def contracts(self) -> ContractsEntity:
        """Access to Contracts entity operations."""
        return self.get_entity("Contracts")

    @property
    def time_entries(self) -> TimeEntriesEntity:
        """Access to Time Entries entity operations."""
        return self.get_entity("TimeEntries")

    @property
    def attachments(self) -> AttachmentsEntity:
        """Access to Attachments entity operations."""
        return self.get_entity("Attachments")

    # Contract-related entities
    @property
    def contract_services(self) -> ContractServicesEntity:
        """Access to Contract Services entity operations."""
        return self.get_entity("ContractServices")

    @property
    def contract_blocks(self) -> ContractBlocksEntity:
        """Access to Contract Blocks entity operations."""
        return self.get_entity("ContractBlocks")

    @property
    def contract_adjustments(self) -> ContractAdjustmentsEntity:
        """Access to Contract Adjustments entity operations."""
        return self.get_entity("ContractAdjustments")

    @property
    def contract_exclusions(self) -> ContractExclusionsEntity:
        """Access to Contract Exclusions entity operations."""
        return self.get_entity("ContractExclusions")

    # Financial entities
    @property
    def billing_codes(self) -> BillingCodesEntity:
        """Access to Billing Codes entity operations."""
        return self.get_entity("BillingCodes")

    @property
    def billing_items(self) -> BillingItemsEntity:
        """Access to Billing Items entity operations."""
        return self.get_entity("BillingItems")

    @property
    def contract_charges(self) -> ContractChargesEntity:
        """Access to Contract Charges entity operations."""
        return self.get_entity("ContractCharges")

    @property
    def invoices(self) -> InvoicesEntity:
        """Access to Invoices entity operations."""
        return self.get_entity("Invoices")

    @property
    def project_charges(self) -> ProjectChargesEntity:
        """Access to Project Charges entity operations."""
        return self.get_entity("ProjectCharges")

    @property
    def quotes(self) -> QuotesEntity:
        """Access to Quotes entity operations."""
        return self.get_entity("Quotes")

    @property
    def purchase_orders(self) -> PurchaseOrdersEntity:
        """Access to Purchase Orders entity operations."""
        return self.get_entity("PurchaseOrders")

    @property
    def expenses(self) -> ExpensesEntity:
        """Access to Expenses entity operations."""
        return self.get_entity("Expenses")

    # Service desk entities
    @property
    def ticket_categories(self) -> TicketCategoriesEntity:
        """Access to Ticket Categories entity operations."""
        return self.get_entity("TicketCategories")

    @property
    def ticket_statuses(self) -> TicketStatusesEntity:
        """Access to Ticket Statuses entity operations."""
        return self.get_entity("TicketStatuses")

    @property
    def ticket_priorities(self) -> TicketPrioritiesEntity:
        """Access to Ticket Priorities entity operations."""
        return self.get_entity("TicketPriorities")

    @property
    def ticket_sources(self) -> TicketSourcesEntity:
        """Access to Ticket Sources entity operations."""
        return self.get_entity("TicketSources")

    # Operational entities
    @property
    def configuration_items(self) -> ConfigurationItemsEntity:
        """Access to Configuration Items entity operations."""
        return self.get_entity("ConfigurationItems")

    @property
    def service_calls(self) -> ServiceCallsEntity:
        """Access to Service Calls entity operations."""
        return self.get_entity("ServiceCalls")

    @property
    def tasks(self) -> TasksEntity:
        """Access to Tasks entity operations."""
        return self.get_entity("Tasks")

    @property
    def notes(self) -> NotesEntity:
        """Access to Notes entity operations."""
        return self.get_entity("Notes")

    # Human Resources & Resource Management entities (Week 2)
    @property
    def accounts(self) -> AccountsEntity:
        """Access to Accounts entity operations."""
        return self.get_entity("Accounts")

    @property
    def departments(self) -> DepartmentsEntity:
        """Access to Departments entity operations."""
        return self.get_entity("Departments")

    @property
    def resource_roles(self) -> ResourceRolesEntity:
        """Access to Resource Roles entity operations."""
        return self.get_entity("ResourceRoles")

    @property
    def resource_skills(self) -> ResourceSkillsEntity:
        """Access to Resource Skills entity operations."""
        return self.get_entity("ResourceSkills")

    @property
    def teams(self) -> TeamsEntity:
        """Access to Teams entity operations."""
        return self.get_entity("Teams")

    @property
    def work_types(self) -> WorkTypesEntity:
        """Access to Work Types entity operations."""
        return self.get_entity("WorkTypes")

    # Project Management & Workflow entities (Week 4)
    @property
    def project_phases(self) -> ProjectPhasesEntity:
        """Access to Project Phases entity operations."""
        return self.get_entity("ProjectPhases")

    @property
    def project_milestones(self) -> ProjectMilestonesEntity:
        """Access to Project Milestones entity operations."""
        return self.get_entity("ProjectMilestones")

    @property
    def allocation_codes(self) -> AllocationCodesEntity:
        """Access to Allocation Codes entity operations."""
        return self.get_entity("AllocationCodes")

    @property
    def holiday_sets(self) -> HolidaySetsEntity:
        """Access to Holiday Sets entity operations."""
        return self.get_entity("HolidaySets")

    @property
    def workflow_rules(self) -> WorkflowRulesEntity:
        """Access to Workflow Rules entity operations."""
        return self.get_entity("WorkflowRules")

    @property
    def project_templates(self) -> ProjectTemplatesEntity:
        """Access to Project Templates entity operations."""
        return self.get_entity("ProjectTemplates")

    @property
    def resource_allocation(self) -> ResourceAllocationEntity:
        """Access to Resource Allocation entity operations."""
        return self.get_entity("ResourceAllocation")

    @property
    def project_budgets(self) -> ProjectBudgetsEntity:
        """Access to Project Budgets entity operations."""
        return self.get_entity("ProjectBudgets")

    @property
    def task_dependencies(self) -> TaskDependenciesEntity:
        """Access to Task Dependencies entity operations."""
        return self.get_entity("TaskDependencies")

    @property
    def project_reports(self) -> ProjectReportsEntity:
        """Access to Project Reports entity operations."""
        return self.get_entity("ProjectReports")

    @property
    def workflows(self) -> WorkflowsEntity:
        """Access to Workflows entity operations."""
        return self.get_entity("Workflows")

    # Additional Service Delivery & Operations entities
    @property
    def change_requests(self) -> ChangeRequestsEntity:
        """Access to Change Requests entity operations."""
        return self.get_entity("ChangeRequests")

    @property
    def vendor_types(self) -> VendorTypesEntity:
        """Access to Vendor Types entity operations."""
        return self.get_entity("VendorTypes")

    @property
    def incident_types(self) -> IncidentTypesEntity:
        """Access to Incident Types entity operations."""
        return self.get_entity("IncidentTypes")

    @property
    def configuration_item_types(self) -> ConfigurationItemTypesEntity:
        """Access to Configuration Item Types entity operations."""
        return self.get_entity("ConfigurationItemTypes")

    # Security & Compliance entities (Week 5)
    @property
    def security_policies(self) -> SecurityPoliciesEntity:
        """Access to Security Policies entity operations."""
        return self.get_entity("SecurityPolicies")

    @property
    def compliance_frameworks(self) -> ComplianceFrameworksEntity:
        """Access to Compliance Frameworks entity operations."""
        return self.get_entity("ComplianceFrameworks")

    @property
    def custom_fields(self) -> CustomFieldsEntity:
        """Access to Custom Fields entity operations."""
        return self.get_entity("CustomFields")

    @property
    def business_rules(self) -> BusinessRulesEntity:
        """Access to Business Rules entity operations."""
        return self.get_entity("BusinessRules")

    @property
    def notification_rules(self) -> NotificationRulesEntity:
        """Access to Notification Rules entity operations."""
        return self.get_entity("NotificationRules")

    # System Management entities (Week 6)
    @property
    def system_health(self) -> SystemHealthEntity:
        """Access to System Health entity operations."""
        return self.get_entity("SystemHealth")

    @property
    def system_configuration(self) -> SystemConfigurationEntity:
        """Access to System Configuration entity operations."""
        return self.get_entity("SystemConfiguration")

    @property
    def dashboards(self) -> DashboardsEntity:
        """Access to Dashboards entity operations."""
        return self.get_entity("Dashboards")

    def list_available_entities(self) -> list:
        """
        List all available entity types.

        Returns:
            List of entity names that have specific handlers
        """
        return list(self.ENTITY_CLASSES.keys())
