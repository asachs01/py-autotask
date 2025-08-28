"""
Tests for newly added entities in the py-autotask library.

This module tests the extensive set of entities that were added to provide
complete Autotask API coverage, focusing on entity-specific functionality
and specialized operations.
"""

import pytest
from unittest.mock import Mock, patch

try:
    import responses

    HAS_RESPONSES = True
except ImportError:
    HAS_RESPONSES = False
    responses = None

from py_autotask.client import AutotaskClient
from py_autotask.entities import (
    # Advanced entities from Week 6
    ActionTypesEntity,
    AdditionalInvoiceFieldValuesEntity,
    APIUsageMetricsEntity,
    AppointmentsEntity,
    AttachmentInfoEntity,
    AutomationRulesEntity,
    BackupConfigurationEntity,
    # Article/Knowledge Base entities
    ArticleAttachmentsEntity,
    ArticleConfigurationItemCategoryAssociationsEntity,
    ArticleNotesEntity,
    ArticlePlainTextContentEntity,
    ArticleTagAssociationsEntity,
    ArticleTicketAssociationsEntity,
    ArticleToArticleAssociationsEntity,
    ArticleToDocumentAssociationsEntity,
    # Business & Financial entities
    BillingItemApprovalLevelsEntity,
    BusinessRulesEntity,
    ChangeOrderChargesEntity,
    ChangeRequestLinksEntity,
    ChecklistLibrariesEntity,
    ChecklistLibraryChecklistItemsEntity,
    ClassificationIconsEntity,
    ClientPortalUsersEntity,
    ComanagedAssociationsEntity,
    ComplianceFrameworksEntity,
    # Company-related entities
    CompanyAlertsEntity,
    CompanyAttachmentsEntity,
    CompanyCategoriesEntity,
    CompanyLocationsEntity,
    CompanyNoteAttachmentsEntity,
    CompanyNotesEntity,
    CompanySiteConfigurationsEntity,
    CompanyTeamsEntity,
    CompanyToDosEntity,
    # Configuration Item entities
    ConfigurationItemAttachmentsEntity,
    ConfigurationItemBillingProductAssociationsEntity,
    ConfigurationItemCategoriesEntity,
    ConfigurationItemCategoryUdfAssociationsEntity,
    ConfigurationItemDnsRecordsEntity,
    ConfigurationItemNoteAttachmentsEntity,
    ConfigurationItemNotesEntity,
    ConfigurationItemRelatedItemsEntity,
    ConfigurationItemSslSubjectAlternativeNameEntity,
    # Contact entities
    ContactBillingProductAssociationsEntity,
    ContactGroupsEntity,
    ContactGroupContactsEntity,
    # Contract entities
    ContractBillingRulesEntity,
    ContractBlockHourFactorsEntity,
    ContractExclusionBillingCodesEntity,
    ContractExclusionRolesEntity,
    ContractExclusionSetExcludedRolesEntity,
    ContractExclusionSetExcludedWorkTypesEntity,
    ContractMilestonesEntity,
    ContractNotesEntity,
    ContractRetainersEntity,
    ContractRolesEntity,
    ContractServiceAdjustmentsEntity,
    # Financial entities
    CountriesEntity,
    CurrenciesEntity,
    CustomFieldsEntity,
    DashboardsEntity,
    DataExportEntity,
    DataIntegrationsEntity,
    # Document entities
    DocumentCategoriesEntity,
    DocumentToProcedureAssociationsEntity,
    DocumentAttachmentsEntity,
    # Expense entities
    ExpenseCategoriesEntity,
    ExpenseItemsEntity,
    ExpenseReportsEntity,
    # System entities
    IntegrationEndpointsEntity,
    InventoryItemsEntity,
    InventoryLocationsEntity,
    InventoryStockedItemsEntity,
    InventoryTransfersEntity,
    # Notification entities
    NotificationHistoryEntity,
    NotificationTemplatesEntity,
    # Product entities
    ProductCategoriesEntity,
    ProductNotesEntity,
    ProductTiersEntity,
    ProductVendorsEntity,
    # Project entities
    ProjectAttachmentsEntity,
    ProjectCostsEntity,
    ProjectNotesEntity,
    # Purchase entities
    PurchaseApprovalsEntity,
    PurchaseOrderItemsEntity,
    # Quote entities
    QuoteItemsEntity,
    QuoteLocationsEntity,
    QuoteTemplatesEntity,
    # Resource entities
    ResourceAttachmentsEntity,
    ResourceRoleDepartmentsEntity,
    ResourceRoleQueuesEntity,
    ResourceRoleSkillsEntity,
    ResourceServiceDeskRolesEntity,
    # Service entities
    ServiceCallTicketResourcesEntity,
    ServiceCallTicketsEntity,
    ServiceLevelAgreementResultsEntity,
    # System configuration entities
    SecurityPoliciesEntity,
    SystemConfigurationEntity,
    SystemHealthEntity,
    # Task entities
    TaskNotesEntity,
    TaskPredecessorsEntity,
    TaskSecondaryResourcesEntity,
    # Ticket entities
    TicketAdditionalContactsEntity,
    TicketAdditionalConfigurationItemsEntity,
    TicketAttachmentsEntity,
    TicketChangeRequestApprovalsEntity,
    TicketChecklistItemsEntity,
    TicketChecklistLibrariesEntity,
    TicketCostsEntity,
    TicketHistoryEntity,
    TicketNotesEntity,
    TicketSecondaryResourcesEntity,
    # Additional entities
    UserDefinedFieldListItemsEntity,
    # Tax and shipping entities
    TaxCategoriesEntity,
    TaxRegionsEntity,
    ShippingTypesEntity,
    # Survey and subscription entities
    SurveyResultsEntity,
    SubscriptionPeriodsEntity,
    # Price list entities
    PriceListMaterialCodesEntity,
    PriceListProductsEntity,
    PriceListRolesEntity,
    PriceListServicesEntity,
    PriceListServiceBundlesEntity,
    PriceListWorkTypeModifiersEntity,
    # Organizational entities
    OrganizationalLevelsEntity,
    OrganizationalLevelAssociationsEntity,
    PaymentTermsEntity,
    PerformanceMetricsEntity,
)


class TestNewEntities:
    """Test cases for newly added entities."""

    def test_action_types_entity(self, mock_auth):
        """Test ActionTypesEntity functionality."""
        client = AutotaskClient(mock_auth)
        entity = ActionTypesEntity(client, "ActionTypes")

        assert entity.entity_name == "ActionTypes"
        assert entity.client is client
        assert hasattr(entity, "get")
        assert hasattr(entity, "query")
        assert hasattr(entity, "create")

    def test_additional_invoice_field_values_entity(self, mock_auth):
        """Test AdditionalInvoiceFieldValuesEntity functionality."""
        client = AutotaskClient(mock_auth)
        entity = AdditionalInvoiceFieldValuesEntity(
            client, "AdditionalInvoiceFieldValues"
        )

        assert entity.entity_name == "AdditionalInvoiceFieldValues"
        assert entity.client is client

    def test_api_usage_metrics_entity(self, mock_auth):
        """Test APIUsageMetricsEntity functionality."""
        client = AutotaskClient(mock_auth)
        entity = APIUsageMetricsEntity(client, "APIUsageMetrics")

        assert entity.entity_name == "APIUsageMetrics"
        assert entity.client is client

    def test_appointments_entity(self, mock_auth):
        """Test AppointmentsEntity functionality."""
        client = AutotaskClient(mock_auth)
        entity = AppointmentsEntity(client, "Appointments")

        assert entity.entity_name == "Appointments"
        assert entity.client is client

    def test_article_entities(self, mock_auth):
        """Test all article-related entities."""
        client = AutotaskClient(mock_auth)

        article_entities = [
            ("ArticleAttachments", ArticleAttachmentsEntity),
            (
                "ArticleConfigurationItemCategoryAssociations",
                ArticleConfigurationItemCategoryAssociationsEntity,
            ),
            ("ArticleNotes", ArticleNotesEntity),
            ("ArticlePlainTextContent", ArticlePlainTextContentEntity),
            ("ArticleTagAssociations", ArticleTagAssociationsEntity),
            ("ArticleTicketAssociations", ArticleTicketAssociationsEntity),
            ("ArticleToArticleAssociations", ArticleToArticleAssociationsEntity),
            ("ArticleToDocumentAssociations", ArticleToDocumentAssociationsEntity),
        ]

        for entity_name, entity_class in article_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_company_related_entities(self, mock_auth):
        """Test all company-related entities."""
        client = AutotaskClient(mock_auth)

        company_entities = [
            ("CompanyAlerts", CompanyAlertsEntity),
            ("CompanyAttachments", CompanyAttachmentsEntity),
            ("CompanyCategories", CompanyCategoriesEntity),
            ("CompanyLocations", CompanyLocationsEntity),
            ("CompanyNoteAttachments", CompanyNoteAttachmentsEntity),
            ("CompanyNotes", CompanyNotesEntity),
            ("CompanySiteConfigurations", CompanySiteConfigurationsEntity),
            ("CompanyTeams", CompanyTeamsEntity),
            ("CompanyToDos", CompanyToDosEntity),
        ]

        for entity_name, entity_class in company_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_configuration_item_entities(self, mock_auth):
        """Test all configuration item related entities."""
        client = AutotaskClient(mock_auth)

        ci_entities = [
            ("ConfigurationItemAttachments", ConfigurationItemAttachmentsEntity),
            (
                "ConfigurationItemBillingProductAssociations",
                ConfigurationItemBillingProductAssociationsEntity,
            ),
            ("ConfigurationItemCategories", ConfigurationItemCategoriesEntity),
            (
                "ConfigurationItemCategoryUdfAssociations",
                ConfigurationItemCategoryUdfAssociationsEntity,
            ),
            ("ConfigurationItemDnsRecords", ConfigurationItemDnsRecordsEntity),
            (
                "ConfigurationItemNoteAttachments",
                ConfigurationItemNoteAttachmentsEntity,
            ),
            ("ConfigurationItemNotes", ConfigurationItemNotesEntity),
            ("ConfigurationItemRelatedItems", ConfigurationItemRelatedItemsEntity),
            (
                "ConfigurationItemSslSubjectAlternativeName",
                ConfigurationItemSslSubjectAlternativeNameEntity,
            ),
        ]

        for entity_name, entity_class in ci_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_contract_entities(self, mock_auth):
        """Test all contract-related entities."""
        client = AutotaskClient(mock_auth)

        contract_entities = [
            ("ContractBillingRules", ContractBillingRulesEntity),
            ("ContractBlockHourFactors", ContractBlockHourFactorsEntity),
            ("ContractExclusionBillingCodes", ContractExclusionBillingCodesEntity),
            ("ContractExclusionRoles", ContractExclusionRolesEntity),
            (
                "ContractExclusionSetExcludedRoles",
                ContractExclusionSetExcludedRolesEntity,
            ),
            (
                "ContractExclusionSetExcludedWorkTypes",
                ContractExclusionSetExcludedWorkTypesEntity,
            ),
            ("ContractMilestones", ContractMilestonesEntity),
            ("ContractNotes", ContractNotesEntity),
            ("ContractRetainers", ContractRetainersEntity),
            ("ContractRoles", ContractRolesEntity),
            ("ContractServiceAdjustments", ContractServiceAdjustmentsEntity),
        ]

        for entity_name, entity_class in contract_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_ticket_related_entities(self, mock_auth):
        """Test all ticket-related entities."""
        client = AutotaskClient(mock_auth)

        ticket_entities = [
            ("TicketAdditionalContacts", TicketAdditionalContactsEntity),
            (
                "TicketAdditionalConfigurationItems",
                TicketAdditionalConfigurationItemsEntity,
            ),
            ("TicketAttachments", TicketAttachmentsEntity),
            ("TicketChangeRequestApprovals", TicketChangeRequestApprovalsEntity),
            ("TicketChecklistItems", TicketChecklistItemsEntity),
            ("TicketChecklistLibraries", TicketChecklistLibrariesEntity),
            ("TicketCosts", TicketCostsEntity),
            ("TicketHistory", TicketHistoryEntity),
            ("TicketNotes", TicketNotesEntity),
            ("TicketSecondaryResources", TicketSecondaryResourcesEntity),
        ]

        for entity_name, entity_class in ticket_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    @pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not available")
    def test_entity_crud_operations(self, mock_auth, sample_ticket_data):
        """Test CRUD operations for new entities."""
        if not HAS_RESPONSES:
            pytest.skip("responses library not available")

        # Mock API responses
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{mock_auth.api_url}/v1.0/ActionTypes/12345",
                json={"item": sample_ticket_data},
                status=200,
            )

            rsps.add(
                responses.POST,
                f"{mock_auth.api_url}/v1.0/ActionTypes",
                json={"itemId": 12345},
                status=201,
            )

            rsps.add(
                responses.PATCH,
                f"{mock_auth.api_url}/v1.0/ActionTypes",
                json={"item": sample_ticket_data},
                status=200,
            )

            rsps.add(
                responses.DELETE,
                f"{mock_auth.api_url}/v1.0/ActionTypes/12345",
                status=200,
            )

            client = AutotaskClient(mock_auth)
            entity = ActionTypesEntity(client, "ActionTypes")

            # Test get
            result = entity.get(12345)
            assert result == sample_ticket_data

            # Test create
            create_result = entity.create(sample_ticket_data)
            assert create_result.item_id == 12345

            # Test update
            sample_ticket_data["id"] = 12345
            update_result = entity.update(sample_ticket_data)
            assert update_result == sample_ticket_data

            # Test delete
            delete_result = entity.delete(12345)
            assert delete_result is True

    @pytest.mark.skipif(not HAS_RESPONSES, reason="responses library not available")
    def test_entity_query_operations(self, mock_auth, sample_query_response):
        """Test query operations for new entities."""
        if not HAS_RESPONSES:
            pytest.skip("responses library not available")

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                f"{mock_auth.api_url}/v1.0/ActionTypes/query",
                json=sample_query_response,
                status=200,
            )

            client = AutotaskClient(mock_auth)
            entity = ActionTypesEntity(client, "ActionTypes")

            # Test query with filters
            filters = {"field": "isActive", "op": "eq", "value": "true"}
            result = entity.query(filters)

            assert result.items == sample_query_response["items"]
            assert len(result.items) == 1

    def test_automation_rules_entity(self, mock_auth):
        """Test AutomationRulesEntity functionality."""
        client = AutotaskClient(mock_auth)
        entity = AutomationRulesEntity(client, "AutomationRules")

        assert entity.entity_name == "AutomationRules"
        assert entity.client is client

    def test_backup_configuration_entity(self, mock_auth):
        """Test BackupConfigurationEntity functionality."""
        client = AutotaskClient(mock_auth)
        entity = BackupConfigurationEntity(client, "BackupConfiguration")

        assert entity.entity_name == "BackupConfiguration"
        assert entity.client is client

    def test_system_entities(self, mock_auth):
        """Test system-related entities."""
        client = AutotaskClient(mock_auth)

        system_entities = [
            ("SystemConfiguration", SystemConfigurationEntity),
            ("SystemHealth", SystemHealthEntity),
            ("SecurityPolicies", SecurityPoliciesEntity),
            ("PerformanceMetrics", PerformanceMetricsEntity),
            ("IntegrationEndpoints", IntegrationEndpointsEntity),
            ("ComplianceFrameworks", ComplianceFrameworksEntity),
        ]

        for entity_name, entity_class in system_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_financial_entities(self, mock_auth):
        """Test financial-related entities."""
        client = AutotaskClient(mock_auth)

        financial_entities = [
            ("TaxCategories", TaxCategoriesEntity),
            ("TaxRegions", TaxRegionsEntity),
            ("PaymentTerms", PaymentTermsEntity),
            ("Currencies", CurrenciesEntity),
        ]

        for entity_name, entity_class in financial_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_inventory_entities(self, mock_auth):
        """Test inventory-related entities."""
        client = AutotaskClient(mock_auth)

        inventory_entities = [
            ("InventoryItems", InventoryItemsEntity),
            ("InventoryLocations", InventoryLocationsEntity),
            ("InventoryStockedItems", InventoryStockedItemsEntity),
            ("InventoryTransfers", InventoryTransfersEntity),
        ]

        for entity_name, entity_class in inventory_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_price_list_entities(self, mock_auth):
        """Test price list related entities."""
        client = AutotaskClient(mock_auth)

        price_list_entities = [
            ("PriceListMaterialCodes", PriceListMaterialCodesEntity),
            ("PriceListProducts", PriceListProductsEntity),
            ("PriceListRoles", PriceListRolesEntity),
            ("PriceListServices", PriceListServicesEntity),
            ("PriceListServiceBundles", PriceListServiceBundlesEntity),
            ("PriceListWorkTypeModifiers", PriceListWorkTypeModifiersEntity),
        ]

        for entity_name, entity_class in price_list_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_resource_entities(self, mock_auth):
        """Test resource-related entities."""
        client = AutotaskClient(mock_auth)

        resource_entities = [
            ("ResourceAttachments", ResourceAttachmentsEntity),
            ("ResourceRoleDepartments", ResourceRoleDepartmentsEntity),
            ("ResourceRoleQueues", ResourceRoleQueuesEntity),
            ("ResourceRoleSkills", ResourceRoleSkillsEntity),
            ("ResourceServiceDeskRoles", ResourceServiceDeskRolesEntity),
        ]

        for entity_name, entity_class in resource_entities:
            entity = entity_class(client, entity_name)
            assert entity.entity_name == entity_name
            assert entity.client is client

    def test_entity_error_handling(self, mock_auth):
        """Test error handling in entity operations."""
        client = AutotaskClient(mock_auth)
        entity = ActionTypesEntity(client, "ActionTypes")

        # Mock error responses
        with patch.object(client, "get", side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                entity.get(12345)

    def test_entity_logging(self, mock_auth, caplog):
        """Test that entities log operations correctly."""
        client = AutotaskClient(mock_auth)
        entity = ActionTypesEntity(client, "ActionTypes")

        with patch.object(client, "get", return_value=None):
            entity.get(12345)

        # Check that debug logging occurred
        assert "Getting ActionTypes with ID 12345" in caplog.text

    def test_entity_inheritance(self, mock_auth):
        """Test that all new entities properly inherit from BaseEntity."""
        from py_autotask.entities.base import BaseEntity

        client = AutotaskClient(mock_auth)

        # Test a sample of entities
        test_entities = [
            ActionTypesEntity(client, "ActionTypes"),
            CompanyAlertsEntity(client, "CompanyAlerts"),
            TicketNotesEntity(client, "TicketNotes"),
            SystemHealthEntity(client, "SystemHealth"),
        ]

        for entity in test_entities:
            assert isinstance(entity, BaseEntity)
            assert hasattr(entity, "get")
            assert hasattr(entity, "query")
            assert hasattr(entity, "create")
            assert hasattr(entity, "update")
            assert hasattr(entity, "delete")
