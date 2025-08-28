"""
Entity manager for organizing and accessing different Autotask entities.

This module provides the EntityManager class that creates and manages
entity instances, providing both direct access and dynamic entity creation.
"""

import logging
from typing import TYPE_CHECKING, Dict

# Week 2 entities - Human Resources & Resource Management
from .accounts import AccountsEntity
from .action_types import ActionTypesEntity
from .additional_invoice_field_values import AdditionalInvoiceFieldValuesEntity
from .allocation_codes import AllocationCodesEntity

# Fourth batch - System and Analytics entities
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
from .automation_rules import AutomationRulesEntity
from .backup_configuration import BackupConfigurationEntity
from .base import BaseEntity
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
from .contract_services import ContractServicesEntity
from .contracts import ContractsEntity
from .countries import CountriesEntity
from .currencies import CurrenciesEntity
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

# Week 4 entities - Project Management & Workflow
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

# Week 5 entities - Security & Compliance
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

# Week 3 entities - Service Delivery & Operations
from .subscriptions import SubscriptionsEntity
from .survey_results import SurveyResultsEntity
from .system_configuration import SystemConfigurationEntity

# Week 6 entities - System Management
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
        "AdditionalInvoiceFieldValues": AdditionalInvoiceFieldValuesEntity,
        "BillingItemApprovalLevels": BillingItemApprovalLevelsEntity,
        "ChangeOrderCharges": ChangeOrderChargesEntity,
        "ChangeRequestLinks": ChangeRequestLinksEntity,
        "ChecklistLibraries": ChecklistLibrariesEntity,
        "ChecklistLibraryChecklistItems": ChecklistLibraryChecklistItemsEntity,
        "ClassificationIcons": ClassificationIconsEntity,
        "ClientPortalUsers": ClientPortalUsersEntity,
        "ComanagedAssociations": ComanagedAssociationsEntity,
        "CompanyAlerts": CompanyAlertsEntity,
        "CompanyAttachments": CompanyAttachmentsEntity,
        "CompanyCategories": CompanyCategoriesEntity,
        "CompanyLocations": CompanyLocationsEntity,
        "CompanyNoteAttachments": CompanyNoteAttachmentsEntity,
        "CompanyNotes": CompanyNotesEntity,
        "CompanySiteConfigurations": CompanySiteConfigurationsEntity,
        "CompanyTeams": CompanyTeamsEntity,
        "CompanyToDos": CompanyToDosEntity,
        "ContactBillingProductAssociations": ContactBillingProductAssociationsEntity,
        "ContactGroupContacts": ContactGroupContactsEntity,
        "Contacts": ContactsEntity,
        "Projects": ProjectsEntity,
        "Resources": ResourcesEntity,
        "Contracts": ContractsEntity,
        "TimeEntries": TimeEntriesEntity,
        "Attachments": AttachmentsEntity,
        # Article/Knowledge Base entities
        "ArticleAttachments": ArticleAttachmentsEntity,
        "ArticleConfigurationItemCategoryAssociations": ArticleConfigurationItemCategoryAssociationsEntity,
        "ArticleNotes": ArticleNotesEntity,
        "ArticlePlainTextContent": ArticlePlainTextContentEntity,
        "ArticleTagAssociations": ArticleTagAssociationsEntity,
        "ArticleTicketAssociations": ArticleTicketAssociationsEntity,
        "ArticleToArticleAssociations": ArticleToArticleAssociationsEntity,
        "ArticleToDocumentAssociations": ArticleToDocumentAssociationsEntity,
        # Contract-related entities
        "ContractServices": ContractServicesEntity,
        "ContractBlocks": ContractBlocksEntity,
        "ContractAdjustments": ContractAdjustmentsEntity,
        "ContractBillingRules": ContractBillingRulesEntity,
        "ContractBlockHourFactors": ContractBlockHourFactorsEntity,
        "ContractExclusionBillingCodes": ContractExclusionBillingCodesEntity,
        "ContractExclusionRoles": ContractExclusionRolesEntity,
        "ContractExclusionSetExcludedRoles": ContractExclusionSetExcludedRolesEntity,
        "ContractExclusionSetExcludedWorkTypes": ContractExclusionSetExcludedWorkTypesEntity,
        "ContractExclusions": ContractExclusionsEntity,
        "ContractMilestones": ContractMilestonesEntity,
        "ContractNotes": ContractNotesEntity,
        "ContractRetainers": ContractRetainersEntity,
        "ContractRoles": ContractRolesEntity,
        "ContractServiceAdjustments": ContractServiceAdjustmentsEntity,
        # Financial entities
        "BillingCodes": BillingCodesEntity,
        "BillingItems": BillingItemsEntity,
        "ContractCharges": ContractChargesEntity,
        "Invoices": InvoicesEntity,
        "ProjectCharges": ProjectChargesEntity,
        "Quotes": QuotesEntity,
        "PurchaseOrders": PurchaseOrdersEntity,
        "Expenses": ExpensesEntity,
        "ExpenseItems": ExpenseItemsEntity,
        "ExpenseReports": ExpenseReportsEntity,
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
        # Configuration Item related entities
        "ConfigurationItemAttachments": ConfigurationItemAttachmentsEntity,
        "ConfigurationItemBillingProductAssociations": ConfigurationItemBillingProductAssociationsEntity,
        "ConfigurationItemCategories": ConfigurationItemCategoriesEntity,
        "ConfigurationItemCategoryUdfAssociations": ConfigurationItemCategoryUdfAssociationsEntity,
        "ConfigurationItemDnsRecords": ConfigurationItemDnsRecordsEntity,
        "ConfigurationItemNoteAttachments": ConfigurationItemNoteAttachmentsEntity,
        "ConfigurationItemNotes": ConfigurationItemNotesEntity,
        "ConfigurationItemRelatedItems": ConfigurationItemRelatedItemsEntity,
        "ConfigurationItemSslSubjectAlternativeName": ConfigurationItemSslSubjectAlternativeNameEntity,
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
        "WorkflowRules": WorkflowRulesEntity,
        "Workflows": WorkflowsEntity,
        "ProjectTemplates": ProjectTemplatesEntity,
        "ResourceAllocation": ResourceAllocationEntity,
        "ResourceAttachments": ResourceAttachmentsEntity,
        "ResourceRoleDepartments": ResourceRoleDepartmentsEntity,
        "ResourceRoleQueues": ResourceRoleQueuesEntity,
        "ResourceServiceDeskRoles": ResourceServiceDeskRolesEntity,
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
        "UserDefinedFieldListItems": UserDefinedFieldListItemsEntity,
        "BusinessRules": BusinessRulesEntity,
        "NotificationRules": NotificationRulesEntity,
        # System Management entities (Week 6)
        "SystemHealth": SystemHealthEntity,
        "SystemConfiguration": SystemConfigurationEntity,
        "Dashboards": DashboardsEntity,
        # New entities - Phase 1 & 2
        "ActionTypes": ActionTypesEntity,
        "Appointments": AppointmentsEntity,
        "AttachmentInfo": AttachmentInfoEntity,
        "CompanyLocations": CompanyLocationsEntity,
        "ContactGroups": ContactGroupsEntity,
        "Countries": CountriesEntity,
        "Currencies": CurrenciesEntity,
        "Documents": DocumentsEntity,
        "InstalledProducts": InstalledProductsEntity,
        "InventoryItems": InventoryItemsEntity,
        "InventoryLocations": InventoryLocationsEntity,
        "InventoryStockedItems": InventoryStockedItemsEntity,
        "InventoryTransfers": InventoryTransfersEntity,
        "NotificationHistory": NotificationHistoryEntity,
        "Opportunities": OpportunitiesEntity,
        "OpportunityAttachments": OpportunityAttachmentsEntity,
        "PaymentTerms": PaymentTermsEntity,
        "ProductCategories": ProductCategoriesEntity,
        "ProductNotes": ProductNotesEntity,
        "ProductTiers": ProductTiersEntity,
        "ProjectNotes": ProjectNotesEntity,
        "PurchaseOrderItems": PurchaseOrderItemsEntity,
        "QuoteItems": QuoteItemsEntity,
        "QuoteLocations": QuoteLocationsEntity,
        "QuoteTemplates": QuoteTemplatesEntity,
        "Roles": RolesEntity,
        "SalesOrders": SalesOrdersEntity,
        "ServiceCallTicketResources": ServiceCallTicketResourcesEntity,
        "ServiceCallTickets": ServiceCallTicketsEntity,
        "TaskNotes": TaskNotesEntity,
        "TicketAdditionalContacts": TicketAdditionalContactsEntity,
        "TicketAdditionalConfigurationItems": TicketAdditionalConfigurationItemsEntity,
        "TicketAttachments": TicketAttachmentsEntity,
        "TicketChangeRequestApprovals": TicketChangeRequestApprovalsEntity,
        "TicketChecklistItems": TicketChecklistItemsEntity,
        "TicketChecklistLibraries": TicketChecklistLibrariesEntity,
        "TicketCosts": TicketCostsEntity,
        "TicketHistory": TicketHistoryEntity,
        "TicketNotes": TicketNotesEntity,
        "TicketSecondaryResources": TicketSecondaryResourcesEntity,
        # Third batch of additional entities
        "ServiceLevelAgreementResults": ServiceLevelAgreementResultsEntity,
        "ShippingTypes": ShippingTypesEntity,
        "SubscriptionPeriods": SubscriptionPeriodsEntity,
        "SurveyResults": SurveyResultsEntity,
        "TaxCategories": TaxCategoriesEntity,
        "TaxRegions": TaxRegionsEntity,
        "TaskPredecessors": TaskPredecessorsEntity,
        "TaskSecondaryResources": TaskSecondaryResourcesEntity,
        "DocumentAttachments": DocumentAttachmentsEntity,
        "ProjectAttachments": ProjectAttachmentsEntity,
        "ProjectCosts": ProjectCostsEntity,
        # Final batch of missing entities
        "DocumentCategories": DocumentCategoriesEntity,
        "DocumentToProcedureAssociations": DocumentToProcedureAssociationsEntity,
        "ExpenseCategories": ExpenseCategoriesEntity,
        "NotificationTemplates": NotificationTemplatesEntity,
        "OrganizationalLevelAssociations": OrganizationalLevelAssociationsEntity,
        "OrganizationalLevels": OrganizationalLevelsEntity,
        "PriceListMaterialCodes": PriceListMaterialCodesEntity,
        "PriceListProducts": PriceListProductsEntity,
        "PriceListRoles": PriceListRolesEntity,
        "PriceListServices": PriceListServicesEntity,
        "PriceListServiceBundles": PriceListServiceBundlesEntity,
        "PriceListWorkTypeModifiers": PriceListWorkTypeModifiersEntity,
        "ProductVendors": ProductVendorsEntity,
        "PurchaseApprovals": PurchaseApprovalsEntity,
        "ResourceRoleSkills": ResourceRoleSkillsEntity,
        # System and Analytics entities
        "Analytics": AnalyticsEntity,
        "APIUsageMetrics": APIUsageMetricsEntity,
        "AuditLogs": AuditLogsEntity,
        "AutomationRules": AutomationRulesEntity,
        "BackupConfiguration": BackupConfigurationEntity,
        "DataExport": DataExportEntity,
        "DataIntegrations": DataIntegrationsEntity,
        "IntegrationEndpoints": IntegrationEndpointsEntity,
        "PerformanceMetrics": PerformanceMetricsEntity,
        "Reports": ReportsEntity,
        "UserDefinedFields": UserDefinedFieldsEntity,
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
    def company_alerts(self) -> CompanyAlertsEntity:
        """Access to Company Alerts entity operations."""
        return self.get_entity("CompanyAlerts")

    @property
    def company_attachments(self) -> CompanyAttachmentsEntity:
        """Access to Company Attachments entity operations."""
        return self.get_entity("CompanyAttachments")

    @property
    def company_categories(self) -> CompanyCategoriesEntity:
        """Access to Company Categories entity operations."""
        return self.get_entity("CompanyCategories")

    @property
    def company_locations(self) -> CompanyLocationsEntity:
        """Access to Company Locations entity operations."""
        return self.get_entity("CompanyLocations")

    @property
    def company_note_attachments(self) -> CompanyNoteAttachmentsEntity:
        """Access to Company Note Attachments entity operations."""
        return self.get_entity("CompanyNoteAttachments")

    @property
    def company_notes(self) -> CompanyNotesEntity:
        """Access to Company Notes entity operations."""
        return self.get_entity("CompanyNotes")

    @property
    def company_site_configurations(self) -> CompanySiteConfigurationsEntity:
        """Access to Company Site Configurations entity operations."""
        return self.get_entity("CompanySiteConfigurations")

    @property
    def company_teams(self) -> CompanyTeamsEntity:
        """Access to Company Teams entity operations."""
        return self.get_entity("CompanyTeams")

    @property
    def company_to_dos(self) -> CompanyToDosEntity:
        """Access to Company To-Dos entity operations."""
        return self.get_entity("CompanyToDos")

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

    # Article/Knowledge Base entities
    @property
    def article_attachments(self) -> ArticleAttachmentsEntity:
        """Access to Article Attachments entity operations."""
        return self.get_entity("ArticleAttachments")

    @property
    def article_configuration_item_category_associations(
        self,
    ) -> ArticleConfigurationItemCategoryAssociationsEntity:
        """Access to Article Configuration Item Category Associations entity operations."""
        return self.get_entity("ArticleConfigurationItemCategoryAssociations")

    @property
    def article_notes(self) -> ArticleNotesEntity:
        """Access to Article Notes entity operations."""
        return self.get_entity("ArticleNotes")

    @property
    def article_plain_text_content(self) -> ArticlePlainTextContentEntity:
        """Access to Article Plain Text Content entity operations."""
        return self.get_entity("ArticlePlainTextContent")

    @property
    def article_tag_associations(self) -> ArticleTagAssociationsEntity:
        """Access to Article Tag Associations entity operations."""
        return self.get_entity("ArticleTagAssociations")

    @property
    def article_ticket_associations(self) -> ArticleTicketAssociationsEntity:
        """Access to Article Ticket Associations entity operations."""
        return self.get_entity("ArticleTicketAssociations")

    @property
    def article_to_article_associations(self) -> ArticleToArticleAssociationsEntity:
        """Access to Article to Article Associations entity operations."""
        return self.get_entity("ArticleToArticleAssociations")

    @property
    def article_to_document_associations(self) -> ArticleToDocumentAssociationsEntity:
        """Access to Article to Document Associations entity operations."""
        return self.get_entity("ArticleToDocumentAssociations")

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

    @property
    def ticket_additional_configuration_items(
        self,
    ) -> TicketAdditionalConfigurationItemsEntity:
        """Access to Ticket Additional Configuration Items entity operations."""
        return self.get_entity("TicketAdditionalConfigurationItems")

    @property
    def ticket_attachments(self) -> TicketAttachmentsEntity:
        """Access to Ticket Attachments entity operations."""
        return self.get_entity("TicketAttachments")

    @property
    def ticket_change_request_approvals(self) -> TicketChangeRequestApprovalsEntity:
        """Access to Ticket Change Request Approvals entity operations."""
        return self.get_entity("TicketChangeRequestApprovals")

    @property
    def ticket_checklist_items(self) -> TicketChecklistItemsEntity:
        """Access to Ticket Checklist Items entity operations."""
        return self.get_entity("TicketChecklistItems")

    @property
    def ticket_checklist_libraries(self) -> TicketChecklistLibrariesEntity:
        """Access to Ticket Checklist Libraries entity operations."""
        return self.get_entity("TicketChecklistLibraries")

    @property
    def ticket_costs(self) -> TicketCostsEntity:
        """Access to Ticket Costs entity operations."""
        return self.get_entity("TicketCosts")

    @property
    def ticket_history(self) -> TicketHistoryEntity:
        """Access to Ticket History entity operations."""
        return self.get_entity("TicketHistory")

    @property
    def ticket_secondary_resources(self) -> TicketSecondaryResourcesEntity:
        """Access to Ticket Secondary Resources entity operations."""
        return self.get_entity("TicketSecondaryResources")

    # Operational entities
    @property
    def configuration_items(self) -> ConfigurationItemsEntity:
        """Access to Configuration Items entity operations."""
        return self.get_entity("ConfigurationItems")

    # Configuration Item related entities
    @property
    def configuration_item_attachments(self) -> ConfigurationItemAttachmentsEntity:
        """Access to Configuration Item Attachments entity operations."""
        return self.get_entity("ConfigurationItemAttachments")

    @property
    def configuration_item_billing_product_associations(
        self,
    ) -> ConfigurationItemBillingProductAssociationsEntity:
        """Access to Configuration Item Billing Product Associations entity operations."""
        return self.get_entity("ConfigurationItemBillingProductAssociations")

    @property
    def configuration_item_categories(self) -> ConfigurationItemCategoriesEntity:
        """Access to Configuration Item Categories entity operations."""
        return self.get_entity("ConfigurationItemCategories")

    @property
    def configuration_item_category_udf_associations(
        self,
    ) -> ConfigurationItemCategoryUdfAssociationsEntity:
        """Access to Configuration Item Category UDF Associations entity operations."""
        return self.get_entity("ConfigurationItemCategoryUdfAssociations")

    @property
    def configuration_item_dns_records(self) -> ConfigurationItemDnsRecordsEntity:
        """Access to Configuration Item DNS Records entity operations."""
        return self.get_entity("ConfigurationItemDnsRecords")

    @property
    def configuration_item_note_attachments(
        self,
    ) -> ConfigurationItemNoteAttachmentsEntity:
        """Access to Configuration Item Note Attachments entity operations."""
        return self.get_entity("ConfigurationItemNoteAttachments")

    @property
    def configuration_item_notes(self) -> ConfigurationItemNotesEntity:
        """Access to Configuration Item Notes entity operations."""
        return self.get_entity("ConfigurationItemNotes")

    @property
    def configuration_item_related_items(self) -> ConfigurationItemRelatedItemsEntity:
        """Access to Configuration Item Related Items entity operations."""
        return self.get_entity("ConfigurationItemRelatedItems")

    @property
    def configuration_item_ssl_subject_alternative_name(
        self,
    ) -> ConfigurationItemSslSubjectAlternativeNameEntity:
        """Access to Configuration Item SSL Subject Alternative Name entity operations."""
        return self.get_entity("ConfigurationItemSslSubjectAlternativeName")

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

    # Final batch of missing entities
    @property
    def document_categories(self) -> DocumentCategoriesEntity:
        """Access to Document Categories entity operations."""
        return self.get_entity("DocumentCategories")

    @property
    def document_to_procedure_associations(
        self,
    ) -> DocumentToProcedureAssociationsEntity:
        """Access to Document to Procedure Associations entity operations."""
        return self.get_entity("DocumentToProcedureAssociations")

    @property
    def expense_categories(self) -> ExpenseCategoriesEntity:
        """Access to Expense Categories entity operations."""
        return self.get_entity("ExpenseCategories")

    @property
    def notification_templates(self) -> NotificationTemplatesEntity:
        """Access to Notification Templates entity operations."""
        return self.get_entity("NotificationTemplates")

    @property
    def organizational_level_associations(
        self,
    ) -> OrganizationalLevelAssociationsEntity:
        """Access to Organizational Level Associations entity operations."""
        return self.get_entity("OrganizationalLevelAssociations")

    @property
    def organizational_levels(self) -> OrganizationalLevelsEntity:
        """Access to Organizational Levels entity operations."""
        return self.get_entity("OrganizationalLevels")

    @property
    def price_list_material_codes(self) -> PriceListMaterialCodesEntity:
        """Access to Price List Material Codes entity operations."""
        return self.get_entity("PriceListMaterialCodes")

    @property
    def price_list_products(self) -> PriceListProductsEntity:
        """Access to Price List Products entity operations."""
        return self.get_entity("PriceListProducts")

    @property
    def price_list_roles(self) -> PriceListRolesEntity:
        """Access to Price List Roles entity operations."""
        return self.get_entity("PriceListRoles")

    @property
    def price_list_services(self) -> PriceListServicesEntity:
        """Access to Price List Services entity operations."""
        return self.get_entity("PriceListServices")

    @property
    def price_list_service_bundles(self) -> PriceListServiceBundlesEntity:
        """Access to Price List Service Bundles entity operations."""
        return self.get_entity("PriceListServiceBundles")

    @property
    def price_list_work_type_modifiers(self) -> PriceListWorkTypeModifiersEntity:
        """Access to Price List Work Type Modifiers entity operations."""
        return self.get_entity("PriceListWorkTypeModifiers")

    @property
    def product_vendors(self) -> ProductVendorsEntity:
        """Access to Product Vendors entity operations."""
        return self.get_entity("ProductVendors")

    @property
    def purchase_approvals(self) -> PurchaseApprovalsEntity:
        """Access to Purchase Approvals entity operations."""
        return self.get_entity("PurchaseApprovals")

    @property
    def resource_role_skills(self) -> ResourceRoleSkillsEntity:
        """Access to Resource Role Skills entity operations."""
        return self.get_entity("ResourceRoleSkills")

    def list_available_entities(self) -> list:
        """
        List all available entity types.

        Returns:
            List of entity names that have specific handlers
        """
        return list(self.ENTITY_CLASSES.keys())
