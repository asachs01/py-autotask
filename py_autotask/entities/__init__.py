"""
Autotask entities module.

This module provides entity classes for interacting with different
Autotask API endpoints, offering specialized functionality for each entity type.
"""

# Human Resources & Resource Management entities
from .accounts import AccountsEntity
from .action_types import ActionTypesEntity
from .additional_invoice_field_values import AdditionalInvoiceFieldValuesEntity
from .allocation_codes import AllocationCodesEntity
from .analytics import AnalyticsEntity
from .api_usage_metrics import APIUsageMetricsEntity
from .appointments import AppointmentsEntity

# Article/Knowledge Base entities
from .article_attachments import ArticleAttachmentsEntity
from .article_configuration_item_category_associations import (
    ArticleConfigurationItemCategoryAssociationsEntity,
)
from .article_notes import ArticleNotesEntity
from .article_plain_text_content import ArticlePlainTextContentEntity
from .article_tag_associations import ArticleTagAssociationsEntity
from .article_ticket_associations import ArticleTicketAssociationsEntity
from .article_to_article_associations import ArticleToArticleAssociationsEntity
from .article_to_document_associations import ArticleToDocumentAssociationsEntity
from .attachment_info import AttachmentInfoEntity
from .attachments import AttachmentsEntity
from .audit_logs import AuditLogsEntity

# Advanced Features & Integration entities (Week 6)
from .automation_rules import AutomationRulesEntity
from .backup_configuration import BackupConfigurationEntity
from .base import BaseEntity

# Financial entities
from .billing_codes import BillingCodesEntity
from .billing_item_approval_levels import BillingItemApprovalLevelsEntity
from .billing_items import BillingItemsEntity
from .business_divisions import BusinessDivisionsEntity
from .business_rules import BusinessRulesEntity
from .change_order_charges import ChangeOrderChargesEntity
from .change_request_links import ChangeRequestLinksEntity
from .change_requests import ChangeRequestsEntity
from .checklist_libraries import ChecklistLibrariesEntity
from .checklist_library_checklist_items import ChecklistLibraryChecklistItemsEntity
from .classification_icons import ClassificationIconsEntity
from .client_portal_users import ClientPortalUsersEntity
from .comanaged_associations import ComanagedAssociationsEntity
from .companies import CompaniesEntity
from .company_alerts import CompanyAlertsEntity
from .company_attachments import CompanyAttachmentsEntity
from .company_categories import CompanyCategoriesEntity
from .company_locations import CompanyLocationsEntity
from .company_note_attachments import CompanyNoteAttachmentsEntity
from .company_notes import CompanyNotesEntity
from .company_site_configurations import CompanySiteConfigurationsEntity
from .company_teams import CompanyTeamsEntity
from .company_to_dos import CompanyToDosEntity
from .compliance_frameworks import ComplianceFrameworksEntity

# Configuration Item related entities
from .configuration_item_attachments import ConfigurationItemAttachmentsEntity
from .configuration_item_billing_product_associations import (
    ConfigurationItemBillingProductAssociationsEntity,
)
from .configuration_item_categories import ConfigurationItemCategoriesEntity
from .configuration_item_category_udf_associations import (
    ConfigurationItemCategoryUdfAssociationsEntity,
)
from .configuration_item_dns_records import ConfigurationItemDnsRecordsEntity
from .configuration_item_note_attachments import ConfigurationItemNoteAttachmentsEntity
from .configuration_item_notes import ConfigurationItemNotesEntity
from .configuration_item_related_items import ConfigurationItemRelatedItemsEntity
from .configuration_item_ssl_subject_alternative_name import (
    ConfigurationItemSslSubjectAlternativeNameEntity,
)
from .configuration_item_types import ConfigurationItemTypesEntity

# Operational entities
from .configuration_items import ConfigurationItemsEntity
from .contact_billing_product_associations import (
    ContactBillingProductAssociationsEntity,
)
from .contact_group_contacts import ContactGroupContactsEntity
from .contact_groups import ContactGroupsEntity
from .contacts import ContactsEntity
from .contract_adjustments import ContractAdjustmentsEntity
from .contract_billing_rules import ContractBillingRulesEntity
from .contract_block_hour_factors import ContractBlockHourFactorsEntity
from .contract_blocks import ContractBlocksEntity
from .contract_charges import ContractChargesEntity
from .contract_exclusion_billing_codes import ContractExclusionBillingCodesEntity
from .contract_exclusion_roles import ContractExclusionRolesEntity
from .contract_exclusion_set_excluded_roles import (
    ContractExclusionSetExcludedRolesEntity,
)
from .contract_exclusion_set_excluded_work_types import (
    ContractExclusionSetExcludedWorkTypesEntity,
)
from .contract_exclusions import ContractExclusionsEntity
from .contract_milestones import ContractMilestonesEntity
from .contract_notes import ContractNotesEntity
from .contract_retainers import ContractRetainersEntity
from .contract_roles import ContractRolesEntity
from .contract_service_adjustments import ContractServiceAdjustmentsEntity

# Contract-related entities
from .contract_services import ContractServicesEntity
from .contracts import ContractsEntity
from .countries import CountriesEntity
from .currencies import CurrenciesEntity

# Data & Analytics entities (Week 5)
from .custom_fields import CustomFieldsEntity
from .dashboards import DashboardsEntity
from .data_export import DataExportEntity
from .data_integrations import DataIntegrationsEntity
from .departments import DepartmentsEntity
from .document_attachments import DocumentAttachmentsEntity
from .document_categories import DocumentCategoriesEntity
from .document_to_procedure_associations import DocumentToProcedureAssociationsEntity
from .documents import DocumentsEntity
from .expense_categories import ExpenseCategoriesEntity
from .expense_items import ExpenseItemsEntity
from .expense_reports import ExpenseReportsEntity
from .expenses import ExpensesEntity
from .holiday_sets import HolidaySetsEntity
from .incident_types import IncidentTypesEntity
from .installed_products import InstalledProductsEntity
from .integration_endpoints import IntegrationEndpointsEntity
from .inventory_items import InventoryItemsEntity
from .inventory_locations import InventoryLocationsEntity
from .inventory_stocked_items import InventoryStockedItemsEntity
from .inventory_transfers import InventoryTransfersEntity
from .invoices import InvoicesEntity
from .manager import EntityManager
from .notes import NotesEntity
from .notification_history import NotificationHistoryEntity
from .notification_rules import NotificationRulesEntity
from .notification_templates import NotificationTemplatesEntity
from .operations import OperationsEntity
from .opportunities import OpportunitiesEntity
from .opportunity_attachments import OpportunityAttachmentsEntity
from .organizational_level_associations import OrganizationalLevelAssociationsEntity
from .organizational_levels import OrganizationalLevelsEntity
from .payment_terms import PaymentTermsEntity
from .performance_metrics import PerformanceMetricsEntity
from .price_list_material_codes import PriceListMaterialCodesEntity
from .price_list_products import PriceListProductsEntity
from .price_list_roles import PriceListRolesEntity
from .price_list_service_bundles import PriceListServiceBundlesEntity
from .price_list_services import PriceListServicesEntity
from .price_list_work_type_modifiers import PriceListWorkTypeModifiersEntity
from .product_categories import ProductCategoriesEntity
from .product_notes import ProductNotesEntity
from .product_tiers import ProductTiersEntity
from .product_vendors import ProductVendorsEntity
from .products import ProductsEntity
from .project_attachments import ProjectAttachmentsEntity
from .project_budgets import ProjectBudgetsEntity
from .project_charges import ProjectChargesEntity
from .project_costs import ProjectCostsEntity
from .project_milestones import ProjectMilestonesEntity
from .project_notes import ProjectNotesEntity

# Project Management & Workflow entities (Week 4)
from .project_phases import ProjectPhasesEntity
from .project_reports import ProjectReportsEntity
from .project_templates import ProjectTemplatesEntity
from .projects import ProjectsEntity
from .purchase_approvals import PurchaseApprovalsEntity
from .purchase_order_items import PurchaseOrderItemsEntity
from .purchase_orders import PurchaseOrdersEntity
from .quote_items import QuoteItemsEntity
from .quote_locations import QuoteLocationsEntity
from .quote_templates import QuoteTemplatesEntity
from .quotes import QuotesEntity
from .reports import ReportsEntity
from .resource_allocation import ResourceAllocationEntity
from .resource_attachments import ResourceAttachmentsEntity
from .resource_role_departments import ResourceRoleDepartmentsEntity
from .resource_role_queues import ResourceRoleQueuesEntity
from .resource_role_skills import ResourceRoleSkillsEntity
from .resource_roles import ResourceRolesEntity
from .resource_service_desk_roles import ResourceServiceDeskRolesEntity
from .resource_skills import ResourceSkillsEntity
from .resources import ResourcesEntity
from .roles import RolesEntity
from .sales_orders import SalesOrdersEntity
from .security_policies import SecurityPoliciesEntity
from .service_call_ticket_resources import ServiceCallTicketResourcesEntity
from .service_call_tickets import ServiceCallTicketsEntity
from .service_calls import ServiceCallsEntity

# Third batch of additional entities
from .service_level_agreement_results import ServiceLevelAgreementResultsEntity
from .service_level_agreements import ServiceLevelAgreementsEntity
from .shipping_types import ShippingTypesEntity
from .subscription_periods import SubscriptionPeriodsEntity

# Service Delivery & Operations entities (Week 3)
from .subscriptions import SubscriptionsEntity
from .survey_results import SurveyResultsEntity
from .system_configuration import SystemConfigurationEntity
from .system_health import SystemHealthEntity
from .task_dependencies import TaskDependenciesEntity
from .task_notes import TaskNotesEntity
from .task_predecessors import TaskPredecessorsEntity
from .task_secondary_resources import TaskSecondaryResourcesEntity
from .tasks import TasksEntity
from .tax_categories import TaxCategoriesEntity
from .tax_regions import TaxRegionsEntity
from .teams import TeamsEntity
from .ticket_additional_configuration_items import (
    TicketAdditionalConfigurationItemsEntity,
)
from .ticket_additional_contacts import TicketAdditionalContactsEntity
from .ticket_attachments import TicketAttachmentsEntity

# Service desk entities
from .ticket_categories import TicketCategoriesEntity
from .ticket_change_request_approvals import TicketChangeRequestApprovalsEntity
from .ticket_checklist_items import TicketChecklistItemsEntity
from .ticket_checklist_libraries import TicketChecklistLibrariesEntity
from .ticket_costs import TicketCostsEntity
from .ticket_history import TicketHistoryEntity
from .ticket_notes import TicketNotesEntity
from .ticket_priorities import TicketPrioritiesEntity
from .ticket_secondary_resources import TicketSecondaryResourcesEntity
from .ticket_sources import TicketSourcesEntity
from .ticket_statuses import TicketStatusesEntity
from .tickets import TicketsEntity
from .time_entries import TimeEntriesEntity
from .user_defined_field_list_items import UserDefinedFieldListItemsEntity
from .user_defined_fields import UserDefinedFieldsEntity
from .vendor_types import VendorTypesEntity
from .work_types import WorkTypesEntity
from .workflow_rules import WorkflowRulesEntity
from .workflows import WorkflowsEntity

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
    # Article/Knowledge Base entities
    "ArticleAttachmentsEntity",
    "ArticleConfigurationItemCategoryAssociationsEntity",
    "ArticleNotesEntity",
    "ArticlePlainTextContentEntity",
    "ArticleTagAssociationsEntity",
    "ArticleTicketAssociationsEntity",
    "ArticleToArticleAssociationsEntity",
    "ArticleToDocumentAssociationsEntity",
    # New Phase 1 entities
    "ActionTypesEntity",
    "AdditionalInvoiceFieldValuesEntity",
    "AppointmentsEntity",
    "AttachmentInfoEntity",
    "BillingItemApprovalLevelsEntity",
    "ChangeOrderChargesEntity",
    "ChangeRequestLinksEntity",
    "ChecklistLibrariesEntity",
    "ChecklistLibraryChecklistItemsEntity",
    "ClassificationIconsEntity",
    "ClientPortalUsersEntity",
    "ComanagedAssociationsEntity",
    "CompanyAlertsEntity",
    "CompanyAttachmentsEntity",
    "CompanyCategoriesEntity",
    "CompanyLocationsEntity",
    "CompanyNoteAttachmentsEntity",
    "CompanyNotesEntity",
    "CompanySiteConfigurationsEntity",
    "CompanyTeamsEntity",
    "CompanyToDosEntity",
    "ContactBillingProductAssociationsEntity",
    "ContactGroupsEntity",
    "ContactGroupContactsEntity",
    "CountriesEntity",
    "CurrenciesEntity",
    "DocumentsEntity",
    "InstalledProductsEntity",
    "InventoryItemsEntity",
    "InventoryLocationsEntity",
    "InventoryStockedItemsEntity",
    "InventoryTransfersEntity",
    "NotificationHistoryEntity",
    "OpportunitiesEntity",
    "OpportunityAttachmentsEntity",
    "PaymentTermsEntity",
    "ProductCategoriesEntity",
    "ProductNotesEntity",
    "ProductTiersEntity",
    "ProjectNotesEntity",
    "PurchaseOrderItemsEntity",
    "QuoteItemsEntity",
    "QuoteLocationsEntity",
    "QuoteTemplatesEntity",
    "RolesEntity",
    "SalesOrdersEntity",
    "TaskNotesEntity",
    "TicketAdditionalContactsEntity",
    "TicketAdditionalConfigurationItemsEntity",
    "TicketAttachmentsEntity",
    "TicketChangeRequestApprovalsEntity",
    "TicketChecklistItemsEntity",
    "TicketChecklistLibrariesEntity",
    "TicketCostsEntity",
    "TicketHistoryEntity",
    "TicketNotesEntity",
    "TicketSecondaryResourcesEntity",
    # Contract entities
    "ContractServicesEntity",
    "ContractBlocksEntity",
    "ContractAdjustmentsEntity",
    "ContractBillingRulesEntity",
    "ContractBlockHourFactorsEntity",
    "ContractExclusionBillingCodesEntity",
    "ContractExclusionRolesEntity",
    "ContractExclusionSetExcludedRolesEntity",
    "ContractExclusionSetExcludedWorkTypesEntity",
    "ContractExclusionsEntity",
    "ContractMilestonesEntity",
    "ContractNotesEntity",
    "ContractRetainersEntity",
    "ContractRolesEntity",
    "ContractServiceAdjustmentsEntity",
    # Financial entities
    "BillingCodesEntity",
    "BillingItemsEntity",
    "ContractChargesEntity",
    "InvoicesEntity",
    "ProjectChargesEntity",
    "QuotesEntity",
    "PurchaseOrdersEntity",
    "ExpensesEntity",
    "ExpenseItemsEntity",
    "ExpenseReportsEntity",
    # Service desk entities
    "TicketCategoriesEntity",
    "TicketStatusesEntity",
    "TicketPrioritiesEntity",
    "TicketSourcesEntity",
    "ServiceCallTicketResourcesEntity",
    "ServiceCallTicketsEntity",
    # Human Resources & Resource Management entities (Week 2)
    "AccountsEntity",
    "DepartmentsEntity",
    "ResourceAttachmentsEntity",
    "ResourceRoleDepartmentsEntity",
    "ResourceRoleQueuesEntity",
    "ResourceServiceDeskRolesEntity",
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
    # Configuration Item related entities
    "ConfigurationItemAttachmentsEntity",
    "ConfigurationItemBillingProductAssociationsEntity",
    "ConfigurationItemCategoriesEntity",
    "ConfigurationItemCategoryUdfAssociationsEntity",
    "ConfigurationItemDnsRecordsEntity",
    "ConfigurationItemNoteAttachmentsEntity",
    "ConfigurationItemNotesEntity",
    "ConfigurationItemRelatedItemsEntity",
    "ConfigurationItemSslSubjectAlternativeNameEntity",
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
    "UserDefinedFieldListItemsEntity",
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
    # Third batch of additional entities
    "ServiceLevelAgreementResultsEntity",
    "ShippingTypesEntity",
    "SubscriptionPeriodsEntity",
    "SurveyResultsEntity",
    "TaxCategoriesEntity",
    "TaxRegionsEntity",
    "TaskPredecessorsEntity",
    "TaskSecondaryResourcesEntity",
    "DocumentAttachmentsEntity",
    "ProjectAttachmentsEntity",
    "ProjectCostsEntity",
    # Final batch of missing entities
    "DocumentCategoriesEntity",
    "DocumentToProcedureAssociationsEntity",
    "ExpenseCategoriesEntity",
    "NotificationTemplatesEntity",
    "OrganizationalLevelAssociationsEntity",
    "OrganizationalLevelsEntity",
    "PriceListMaterialCodesEntity",
    "PriceListProductsEntity",
    "PriceListRolesEntity",
    "PriceListServicesEntity",
    "PriceListServiceBundlesEntity",
    "PriceListWorkTypeModifiersEntity",
    "ProductVendorsEntity",
    "PurchaseApprovalsEntity",
    "ResourceRoleSkillsEntity",
    # Manager
    "EntityManager",
]
