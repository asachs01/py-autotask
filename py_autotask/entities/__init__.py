"""
Autotask entities module.

This module provides entity classes for interacting with different
Autotask API endpoints, offering specialized functionality for each entity type.
"""

from .base import BaseEntity
from .tickets import TicketsEntity
from .companies import CompaniesEntity
from .contacts import ContactsEntity
from .projects import ProjectsEntity
from .resources import ResourcesEntity
from .contracts import ContractsEntity
from .time_entries import TimeEntriesEntity
from .attachments import AttachmentsEntity
from .manager import EntityManager

# Contract-related entities
from .contract_services import ContractServicesEntity
from .contract_blocks import ContractBlocksEntity
from .contract_adjustments import ContractAdjustmentsEntity
from .contract_exclusions import ContractExclusionsEntity

# Financial entities
from .billing_codes import BillingCodesEntity
from .billing_items import BillingItemsEntity
from .contract_charges import ContractChargesEntity
from .invoices import InvoicesEntity
from .project_charges import ProjectChargesEntity
from .quotes import QuotesEntity
from .purchase_orders import PurchaseOrdersEntity
from .expenses import ExpensesEntity

# Service desk entities
from .ticket_categories import TicketCategoriesEntity
from .ticket_statuses import TicketStatusesEntity
from .ticket_priorities import TicketPrioritiesEntity
from .ticket_sources import TicketSourcesEntity

# Human Resources & Resource Management entities
from .accounts import AccountsEntity
from .departments import DepartmentsEntity
from .resource_roles import ResourceRolesEntity
from .resource_skills import ResourceSkillsEntity
from .teams import TeamsEntity
from .work_types import WorkTypesEntity

# Service Delivery & Operations entities (Week 3)
from .subscriptions import SubscriptionsEntity
from .service_level_agreements import ServiceLevelAgreementsEntity
from .products import ProductsEntity
from .business_divisions import BusinessDivisionsEntity
from .operations import OperationsEntity
from .change_requests import ChangeRequestsEntity
from .incident_types import IncidentTypesEntity
from .vendor_types import VendorTypesEntity
from .configuration_item_types import ConfigurationItemTypesEntity

# Operational entities
from .configuration_items import ConfigurationItemsEntity
from .service_calls import ServiceCallsEntity
from .tasks import TasksEntity
from .notes import NotesEntity

# Project Management & Workflow entities (Week 4)
from .project_phases import ProjectPhasesEntity
from .project_milestones import ProjectMilestonesEntity
from .allocation_codes import AllocationCodesEntity
from .holiday_sets import HolidaySetsEntity
from .workflows import WorkflowRulesEntity
from .project_templates import ProjectTemplatesEntity
from .resource_allocation import ResourceAllocationEntity
from .project_budgets import ProjectBudgetsEntity
from .task_dependencies import TaskDependenciesEntity
from .project_reports import ProjectReportsEntity

__all__ = [
    # Core entities
    "BaseEntity",
    "TicketsEntity",
    "CompaniesEntity", 
    "ContactsEntity",
    "ProjectsEntity",
    "ResourcesEntity",
    "ContractsEntity",
    "TimeEntriesEntity",
    "AttachmentsEntity",
    
    # Contract entities
    "ContractServicesEntity",
    "ContractBlocksEntity",
    "ContractAdjustmentsEntity", 
    "ContractExclusionsEntity",
    
    # Financial entities
    "BillingCodesEntity",
    "BillingItemsEntity",
    "ContractChargesEntity",
    "InvoicesEntity",
    "ProjectChargesEntity",
    "QuotesEntity",
    "PurchaseOrdersEntity",
    "ExpensesEntity",
    
    # Service desk entities
    "TicketCategoriesEntity",
    "TicketStatusesEntity",
    "TicketPrioritiesEntity",
    "TicketSourcesEntity",
    
    # Human Resources & Resource Management entities (Week 2)
    "AccountsEntity",
    "DepartmentsEntity",
    "ResourceRolesEntity", 
    "ResourceSkillsEntity",
    "TeamsEntity",
    "WorkTypesEntity",
    
    # Service Delivery & Operations entities (Week 3)
    "SubscriptionsEntity",
    "ServiceLevelAgreementsEntity",
    "ProductsEntity",
    "BusinessDivisionsEntity",
    "OperationsEntity",
    "ChangeRequestsEntity",
    "IncidentTypesEntity",
    "VendorTypesEntity",
    "ConfigurationItemTypesEntity",
    
    # Operational entities
    "ConfigurationItemsEntity",
    "ServiceCallsEntity",
    "TasksEntity",
    "NotesEntity",
    
    # Project Management & Workflow entities (Week 4)
    "ProjectPhasesEntity",
    "ProjectMilestonesEntity",
    "AllocationCodesEntity",
    "HolidaySetsEntity",
    "WorkflowRulesEntity",
    "ProjectTemplatesEntity",
    "ResourceAllocationEntity",
    "ProjectBudgetsEntity",
    "TaskDependenciesEntity",
    "ProjectReportsEntity",
    
    # Manager
    "EntityManager",
] 