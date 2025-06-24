"""
Autotask entities module.

This module provides entity classes for interacting with different
Autotask API endpoints, offering specialized functionality for each entity type.
"""

# Human Resources & Resource Management entities
from .accounts import AccountsEntity
from .allocation_codes import AllocationCodesEntity
from .analytics import AnalyticsEntity
from .api_usage_metrics import APIUsageMetricsEntity
from .attachments import AttachmentsEntity
from .audit_logs import AuditLogsEntity

# Advanced Features & Integration entities (Week 6)
from .automation_rules import AutomationRulesEntity
from .backup_configuration import BackupConfigurationEntity
from .base import BaseEntity

# Financial entities
from .billing_codes import BillingCodesEntity
from .billing_items import BillingItemsEntity
from .business_divisions import BusinessDivisionsEntity
from .business_rules import BusinessRulesEntity
from .change_requests import ChangeRequestsEntity
from .companies import CompaniesEntity
from .compliance_frameworks import ComplianceFrameworksEntity
from .configuration_item_types import ConfigurationItemTypesEntity

# Operational entities
from .configuration_items import ConfigurationItemsEntity
from .contacts import ContactsEntity
from .contract_adjustments import ContractAdjustmentsEntity
from .contract_blocks import ContractBlocksEntity
from .contract_charges import ContractChargesEntity
from .contract_exclusions import ContractExclusionsEntity

# Contract-related entities
from .contract_services import ContractServicesEntity
from .contracts import ContractsEntity

# Data & Analytics entities (Week 5)
from .custom_fields import CustomFieldsEntity
from .dashboards import DashboardsEntity
from .data_export import DataExportEntity
from .data_integrations import DataIntegrationsEntity
from .departments import DepartmentsEntity
from .expenses import ExpensesEntity
from .holiday_sets import HolidaySetsEntity
from .incident_types import IncidentTypesEntity
from .integration_endpoints import IntegrationEndpointsEntity
from .invoices import InvoicesEntity
from .manager import EntityManager
from .notes import NotesEntity
from .notification_rules import NotificationRulesEntity
from .operations import OperationsEntity
from .performance_metrics import PerformanceMetricsEntity
from .products import ProductsEntity
from .project_budgets import ProjectBudgetsEntity
from .project_charges import ProjectChargesEntity
from .project_milestones import ProjectMilestonesEntity

# Project Management & Workflow entities (Week 4)
from .project_phases import ProjectPhasesEntity
from .project_reports import ProjectReportsEntity
from .project_templates import ProjectTemplatesEntity
from .projects import ProjectsEntity
from .purchase_orders import PurchaseOrdersEntity
from .quotes import QuotesEntity
from .reports import ReportsEntity
from .resource_allocation import ResourceAllocationEntity
from .resource_roles import ResourceRolesEntity
from .resource_skills import ResourceSkillsEntity
from .resources import ResourcesEntity
from .security_policies import SecurityPoliciesEntity
from .service_calls import ServiceCallsEntity
from .service_level_agreements import ServiceLevelAgreementsEntity

# Service Delivery & Operations entities (Week 3)
from .subscriptions import SubscriptionsEntity
from .system_configuration import SystemConfigurationEntity
from .system_health import SystemHealthEntity
from .task_dependencies import TaskDependenciesEntity
from .tasks import TasksEntity
from .teams import TeamsEntity

# Service desk entities
from .ticket_categories import TicketCategoriesEntity
from .ticket_priorities import TicketPrioritiesEntity
from .ticket_sources import TicketSourcesEntity
from .ticket_statuses import TicketStatusesEntity
from .tickets import TicketsEntity
from .time_entries import TimeEntriesEntity
from .user_defined_fields import UserDefinedFieldsEntity
from .vendor_types import VendorTypesEntity
from .work_types import WorkTypesEntity
from .workflow_rules import WorkflowRulesEntity
from .workflows import WorkflowRulesEntity as WorkflowsEntity

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
    "WorkflowsEntity",
    "ProjectTemplatesEntity",
    "ResourceAllocationEntity",
    "ProjectBudgetsEntity",
    "TaskDependenciesEntity",
    "ProjectReportsEntity",
    # Data & Analytics entities (Week 5)
    "CustomFieldsEntity",
    "ReportsEntity",
    "DashboardsEntity",
    "DataExportEntity",
    "AnalyticsEntity",
    "AuditLogsEntity",
    "NotificationRulesEntity",
    "UserDefinedFieldsEntity",
    "BusinessRulesEntity",
    "DataIntegrationsEntity",
    # Advanced Features & Integration entities (Week 6)
    "AutomationRulesEntity",
    "IntegrationEndpointsEntity",
    "SystemConfigurationEntity",
    "PerformanceMetricsEntity",
    "SecurityPoliciesEntity",
    "BackupConfigurationEntity",
    "ComplianceFrameworksEntity",
    "APIUsageMetricsEntity",
    "SystemHealthEntity",
    # Manager
    "EntityManager",
]
