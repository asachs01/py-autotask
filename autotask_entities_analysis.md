# Comprehensive Autotask REST API Entities Analysis

## Current Implementation Status
**Project has 69 entities implemented** in `/home/asachs/Documents/wyre/projects/py-autotask/py_autotask/entities/`

## ✅ ENTITIES ALREADY IMPLEMENTED (69)

1. **Accounts** ✅
2. **Allocation_Codes** ✅ (API name: AllocationCodes)
3. **Analytics** ✅
4. **Api_Usage_Metrics** ✅
5. **Attachments** ✅
6. **Audit_Logs** ✅
7. **Automation_Rules** ✅
8. **Backup_Configuration** ✅
9. **Billing_Codes** ✅ (API name: BillingCodes)
10. **Billing_Items** ✅ (API name: BillingItems)
11. **Business_Divisions** ✅
12. **Business_Rules** ✅
13. **Change_Requests** ✅
14. **Companies** ✅ (API name: Companies)
15. **Compliance_Frameworks** ✅
16. **Configuration_Items** ✅ (API name: ConfigurationItems)
17. **Configuration_Item_Types** ✅ (API name: ConfigurationItemTypes)
18. **Contacts** ✅ (API name: Contacts)
19. **Contract_Adjustments** ✅
20. **Contract_Blocks** ✅ (API name: ContractBlocks)
21. **Contract_Charges** ✅ (API name: ContractCharges)
22. **Contract_Exclusions** ✅
23. **Contract_Services** ✅
24. **Contracts** ✅ (API name: Contracts)
25. **Custom_Fields** ✅
26. **Dashboards** ✅
27. **Data_Export** ✅
28. **Data_Integrations** ✅
29. **Departments** ✅
30. **Expenses** ✅
31. **Holiday_Sets** ✅
32. **Incident_Types** ✅
33. **Integration_Endpoints** ✅
34. **Invoices** ✅ (API name: Invoices)
35. **Notes** ✅
36. **Notification_Rules** ✅
37. **Operations** ✅
38. **Performance_Metrics** ✅
39. **Products** ✅
40. **Project_Budgets** ✅
41. **Project_Charges** ✅
42. **Project_Milestones** ✅
43. **Project_Phases** ✅
44. **Project_Reports** ✅
45. **Project_Templates** ✅
46. **Projects** ✅ (API name: Projects)
47. **Purchase_Orders** ✅ (API name: PurchaseOrders)
48. **Query_Builder** ✅
49. **Quotes** ✅
50. **Reports** ✅
51. **Resource_Allocation** ✅
52. **Resource_Roles** ✅
53. **Resource_Skills** ✅
54. **Resources** ✅
55. **Security_Policies** ✅
56. **Service_Calls** ✅
57. **Service_Level_Agreements** ✅
58. **Subscriptions** ✅
59. **System_Configuration** ✅
60. **System_Health** ✅
61. **Task_Dependencies** ✅
62. **Tasks** ✅ (API name: Tasks)
63. **Teams** ✅
64. **Ticket_Categories** ✅
65. **Ticket_Priorities** ✅
66. **Ticket_Sources** ✅
67. **Ticket_Statuses** ✅
68. **Tickets** ✅ (API name: Tickets)
69. **Time_Entries** ✅ (API name: TimeEntries)
70. **User_Defined_Fields** ✅
71. **Vendor_Types** ✅
72. **Workflow_Rules** ✅
73. **Workflows** ✅
74. **Work_Types** ✅

## ❌ MISSING ENTITIES (From Official Autotask Documentation)

### **Core Missing Entities (High Priority)**

1. **ActionTypes** ❌
2. **AdditionalInvoiceFieldValues** ❌
3. **Appointments** ❌
4. **AttachmentInfo** ❌ (vs current "Attachments")
5. **BillingItemApprovalLevels** ❌
6. **ChangeOrderCharges** ❌
7. **ChangeRequestLinks** ❌
8. **ChecklistLibraries** ❌
9. **ChecklistLibraryChecklistItems** ❌
10. **ClassificationIcons** ❌
11. **ClientPortalUsers** ❌
12. **ComanagedAssociations** ❌

### **Company-Related Missing Entities**

13. **CompanyAlerts** ❌
14. **CompanyAttachments** ❌
15. **CompanyCategories** ❌
16. **CompanyLocations** ❌
17. **CompanyNoteAttachments** ❌
18. **CompanyNotes** ❌
19. **CompanySiteConfigurations** ❌
20. **CompanyTeams** ❌
21. **CompanyToDos** ❌

### **Configuration Item Related Missing Entities**

22. **ConfigurationItemAttachments** ❌
23. **ConfigurationItemBillingProductAssociations** ❌
24. **ConfigurationItemCategories** ❌
25. **ConfigurationItemCategoryUdfAssociations** ❌
26. **ConfigurationItemDnsRecords** ❌
27. **ConfigurationItemNoteAttachments** ❌
28. **ConfigurationItemNotes** ❌
29. **ConfigurationItemRelatedItems** ❌
30. **ConfigurationItemSslSubjectAlternativeName** ❌

### **Contact-Related Missing Entities**

31. **ContactBillingProductAssociations** ❌
32. **ContactGroupContacts** ❌
33. **ContactGroups** ❌

### **Contract-Related Missing Entities**

34. **ContractBillingRules** ❌
35. **ContractBlockHourFactors** ❌
36. **ContractExclusionBillingCodes** ❌
37. **ContractExclusionRoles** ❌
38. **ContractExclusionSetExcludedRoles** ❌
39. **ContractExclusionSetExcludedWorkTypes** ❌
40. **ContractMilestones** ❌
41. **ContractNotes** ❌
42. **ContractRetainers** ❌
43. **ContractRoles** ❌
44. **ContractServiceAdjustments** ❌
45. **ContractServices** ❌ (May overlap with Contract_Services)

### **Article/Knowledge Base Missing Entities**

46. **ArticleAttachments** ❌
47. **ArticleConfigurationItemCategoryAssociations** ❌
48. **ArticleNotes** ❌
49. **ArticlePlainTextContent** ❌
50. **ArticleTagAssociations** ❌
51. **ArticleTicketAssociations** ❌
52. **ArticleToArticleAssociations** ❌
53. **ArticleToDocumentAssociations** ❌

### **Purchase Order Related Missing Entities**

54. **PurchaseOrderItems** ❌
55. **PurchaseOrderItemReceiving** ❌

### **Ticket-Related Missing Entities**

56. **TicketAdditionalContacts** ❌
57. **TicketAdditionalConfigurationItems** ❌
58. **TicketAttachments** ❌
59. **TicketChangeRequestApprovals** ❌
60. **TicketChecklistItems** ❌
61. **TicketChecklistLibraries** ❌
62. **TicketCosts** ❌
63. **TicketHistory** ❌
64. **TicketNotes** ❌
65. **TicketSecondaryResources** ❌

### **Task-Related Missing Entities**

66. **TaskNotes** ❌
67. **TaskPredecessors** ❌
68. **TaskSecondaryResources** ❌

### **Project-Related Missing Entities**

69. **ProjectAttachments** ❌
70. **ProjectCosts** ❌
71. **ProjectNotes** ❌

### **Resource/User Related Missing Entities**

72. **ResourceAttachments** ❌
73. **ResourceRoleDepartments** ❌
74. **ResourceRoleQueues** ❌
75. **ResourceServiceDeskRoles** ❌
76. **UserDefinedFieldListItems** ❌

### **Additional Missing Entities**

77. **Countries** ❌
78. **Currencies** ❌
79. **DocumentAttachments** ❌
80. **Documents** ❌
81. **ExpenseItems** ❌
82. **ExpenseReports** ❌
83. **HolidaySets** ❌ (vs Holiday_Sets - check naming)
84. **InstalledProducts** ❌
85. **InventoryItems** ❌
86. **InventoryLocations** ❌
87. **InventoryStockedItems** ❌
88. **InventoryTransfers** ❌
89. **NotificationHistory** ❌
90. **Opportunities** ❌
91. **OpportunityAttachments** ❌
92. **PaymentTerms** ❌
93. **ProductCategories** ❌
94. **ProductNotes** ❌
95. **ProductTiers** ❌
96. **QuoteItems** ❌
97. **QuoteLocations** ❌
98. **QuoteTemplates** ❌
99. **Roles** ❌
100. **SalesOrders** ❌
101. **ServiceCallTicketResources** ❌
102. **ServiceCallTickets** ❌
103. **ServiceLevelAgreementResults** ❌
104. **ShippingTypes** ❌
105. **SubscriptionPeriods** ❌
106. **SurveyResults** ❌
107. **TaxCategories** ❌
108. **TaxRegions** ❌
109. **TicketCategories** ❌ (Check if different from current implementation)

## SUMMARY

- **Current Implementation**: 69 entities ✅
- **Estimated Total Autotask Entities**: ~180+ entities
- **Missing Entities**: ~110+ entities ❌
- **Coverage**: Approximately 38% of all available entities

## RECOMMENDATIONS

### **Phase 1: Core Business Entities (High Priority)**
Focus on implementing the most commonly used entities:

1. **TicketNotes** - Critical for ticket management
2. **TicketAdditionalContacts** - Important for ticket associations
3. **CompanyLocations** - Essential for multi-location companies
4. **ContactGroups** - Important for contact management
5. **PurchaseOrderItems** - Critical for procurement
6. **TaskNotes** - Important for project management
7. **ProjectNotes** - Essential for project documentation
8. **Opportunities** - Critical for sales process
9. **AttachmentInfo** - Better attachment handling
10. **Documents** - Document management

### **Phase 2: Advanced Features (Medium Priority)**
11. **TicketHistory** - Audit trail capability
12. **ContractServiceAdjustments** - Contract management
13. **ConfigurationItemBillingProductAssociations** - Asset billing
14. **InventoryItems** - Inventory management
15. **ExpenseReports** - Expense tracking

### **Phase 3: Integration & Workflow (Lower Priority)**
16. **ChecklistLibraries** - Workflow automation
17. **ArticleAttachments** - Knowledge base
18. **SurveyResults** - Customer feedback
19. **NotificationHistory** - Communication tracking
20. **ServiceLevelAgreementResults** - SLA monitoring

## NOTES

1. Some entities may have different naming conventions between the API and your implementation
2. Certain entities might be region-specific or version-dependent
3. Access to some entities may depend on Autotask license features
4. This analysis is based on available documentation and may not be 100% complete
5. Consider using the Autotask `entityInformation` API call to get the definitive list for your instance

## VERIFICATION STEPS

To get the complete entity list for your specific Autotask instance:

1. Use Swagger UI at `[your-autotask-url]/swagger/ui/index`
2. Call the `entityInformation` API endpoint
3. Check official documentation updates
4. Verify entity access based on your Autotask license and permissions