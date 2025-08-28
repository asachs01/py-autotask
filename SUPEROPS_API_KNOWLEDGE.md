# SuperOps API Migration Knowledge Base

## Critical API Knowledge for Kaseya Autotask to SuperOps Migration

### API Authentication & Setup

**ALWAYS use these headers:**
```python
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
```

**GraphQL Endpoints:**
- US: `https://{subdomain}.superops.ai/api/graphql`
- EU: `https://{subdomain}.superops.eu/api/graphql`

### Core API Patterns Discovered

#### 1. Visibility Field Structure (CRITICAL)

**The visibility field was the hardest thing to figure out. Here's what works:**

For any entity that needs visibility settings (KB articles, documents, etc.), you MUST provide the correct combination of fields based on portal type:

```python
# REQUESTER Portal - Requires ALL THREE fields
{
    "portalType": "REQUESTER",
    "clientSharedType": "AllClients",    # Required
    "siteSharedType": "AllSites",        # Required  
    "userRoleSharedType": "AllRoles"     # Required
}

# TECHNICIAN Portal - Requires exactly TWO fields
{
    "portalType": "TECHNICIAN",
    "userSharedType": "AllUsers",        # Required
    "groupSharedType": "AllGroups"       # Required
}
```

**NEVER mix fields between portal types or the API will return "Internal Server Error"**

#### 2. Enum Values (Case Sensitive!)

SuperOps uses specific enum values that MUST match exactly:

**Portal Types:**
- `REQUESTER` (not "Requester" or "requester")
- `TECHNICIAN` (not "Technician" or "technician")

**Sharing Types for REQUESTER:**
- `AllClients`, `SelectedClients`, `AllUsersOfSelectedClients`
- `AllSites`, `SelectedSites`, `AllUsersOfSelectedSites`
- `AllRoles`, `SelectedRoles`

**Sharing Types for TECHNICIAN:**
- `AllUsers`, `SelectedUsers`
- `AllGroups`, `SelectedGroups`

#### 3. GraphQL Mutation Structure

**Always use this pattern for mutations:**
```graphql
mutation CreateEntity($input: CreateEntityInput!) {
    createEntity(input: $input) {
        id
        # other fields
    }
}
```

**Variables structure:**
```python
variables = {
    "input": {
        # entity fields here
        "visibility": {
            "added": [
                # visibility objects
            ]
        }
    }
}
```

### Entity-Specific Migration Patterns

#### Knowledge Base Articles (Proven Working)
```python
mutation = """
mutation CreateKbArticle($input: CreateKbArticleInput!) {
    createKbArticle(input: $input) {
        id
        title
        content
    }
}
"""

variables = {
    "input": {
        "collectionId": collection_id,  # Required
        "title": title,
        "content": html_content,
        "visibility": {
            "added": [
                {
                    "portalType": "REQUESTER",
                    "clientSharedType": "AllClients",
                    "siteSharedType": "AllSites",
                    "userRoleSharedType": "AllRoles"
                },
                {
                    "portalType": "TECHNICIAN",
                    "userSharedType": "AllUsers",
                    "groupSharedType": "AllGroups"
                }
            ]
        }
    }
}
```

#### Expected Pattern for Other Entities

Based on the KB pattern, here's what likely works for other entities:

**Tickets:**
```graphql
mutation CreateTicket($input: CreateTicketInput!) {
    createTicket(input: $input) {
        id
        ticketNumber
        subject
        status
    }
}
```

**Contacts:**
```graphql
mutation CreateContact($input: CreateContactInput!) {
    createContact(input: $input) {
        id
        firstName
        lastName
        email
    }
}
```

**Projects:**
```graphql
mutation CreateProject($input: CreateProjectInput!) {
    createProject(input: $input) {
        id
        name
        status
        startDate
        endDate
    }
}
```

**Tasks:**
```graphql
mutation CreateTask($input: CreateTaskInput!) {
    createTask(input: $input) {
        id
        title
        description
        status
        assignedTo
    }
}
```

**Contracts:**
```graphql
mutation CreateContract($input: CreateContractInput!) {
    createContract(input: $input) {
        id
        name
        startDate
        endDate
        value
    }
}
```

### Critical Discovery Methods

#### 1. Introspection Queries (Use These First!)

**Get all available mutations:**
```graphql
{
    __schema {
        mutationType {
            fields {
                name
                description
                args {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                        }
                    }
                }
            }
        }
    }
}
```

**Get input type structure for any entity:**
```graphql
{
    __type(name: "CreateTicketInput") {
        kind
        inputFields {
            name
            type {
                name
                kind
                ofType {
                    name
                    kind
                }
            }
        }
    }
}
```

**Get enum values:**
```graphql
{
    __type(name: "TicketStatus") {
        enumValues {
            name
            description
        }
    }
}
```

#### 2. Test Pattern for New Entities

1. **First, introspect to find the mutation:**
```python
# Find all mutations related to entity
introspection_query = """
{
    __schema {
        mutationType {
            fields {
                name
                description
            }
        }
    }
}
"""
```

2. **Get the input type structure:**
```python
# Replace EntityName with actual entity
input_type_query = """
{
    __type(name: "Create{EntityName}Input") {
        inputFields {
            name
            type {
                name
                kind
                ofType {
                    name
                }
            }
        }
    }
}
"""
```

3. **Test with minimal fields first:**
```python
# Start with only required fields
test_mutation = """
mutation Create{EntityName}($input: Create{EntityName}Input!) {
    create{EntityName}(input: $input) {
        id
    }
}
"""

minimal_variables = {
    "input": {
        # Only include fields marked as NON_NULL in introspection
    }
}
```

4. **Gradually add fields until working**

### Rate Limiting & Error Handling

**Rate Limits:**
- 800 requests per minute maximum
- Use 750 as safe limit
- Implement exponential backoff

**Error Patterns:**
- "Internal Server Error" = Usually visibility field structure issue
- "Invalid input" = Check enum values and field types
- "Unauthorized" = Token issue
- "Not found" = ID doesn't exist

**Retry Strategy:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def api_call():
    # API call here
    pass
```

### Migration Strategy for Full PSA Data

#### Phase 1: Foundation Entities (Order Matters!)
1. **Companies/Clients** - These are referenced by everything else
2. **Contacts** - Linked to companies
3. **Sites/Locations** - Linked to companies

#### Phase 2: Configuration & Setup
1. **Categories/Types** - For tickets, tasks, projects
2. **Priorities** - For tickets and tasks
3. **Statuses** - Custom statuses if needed
4. **User Roles** - For permission management

#### Phase 3: Core Business Data
1. **Contracts** - Linked to companies
2. **Projects** - Linked to companies and contracts
3. **Tasks** - Linked to projects or standalone
4. **Tickets** - The big one, linked to companies, contacts, contracts

#### Phase 4: Supporting Data
1. **Time Entries** - Linked to tickets, tasks, projects
2. **Notes/Comments** - Linked to various entities
3. **Attachments** - Files linked to entities
4. **Knowledge Base** - Documentation and procedures

### Query Patterns for Fetching Existing Data

**Check if entity exists before creating:**
```graphql
query GetExistingEntity {
    entities(filter: { 
        externalId: { eq: "AUTOTASK_ID_12345" }
    }) {
        items {
            id
            externalId
        }
    }
}
```

**Pagination pattern:**
```graphql
query GetEntities($cursor: String) {
    entities(first: 100, after: $cursor) {
        items {
            id
            # fields
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
```

### Mapping Autotask Fields to SuperOps

**Store mappings in a configuration:**
```python
FIELD_MAPPINGS = {
    "ticket": {
        "Title": "subject",
        "Description": "description",
        "TicketNumber": "externalId",  # Store Autotask ID
        "CompanyID": "clientId",
        "ContactID": "contactId",
        "Status": "status",  # Will need enum mapping
        "Priority": "priority",  # Will need enum mapping
        "DueDateTime": "dueDate",
        "CreateDate": "createdAt"
    },
    "contact": {
        "FirstName": "firstName",
        "LastName": "lastName",
        "EmailAddress": "email",
        "Phone": "phone",
        "CompanyID": "clientId"
    },
    # Add more mappings
}

STATUS_MAPPINGS = {
    "ticket": {
        # Autotask -> SuperOps
        "New": "OPEN",
        "In Progress": "IN_PROGRESS",
        "Complete": "CLOSED",
        "Waiting Customer": "ON_HOLD"
    }
}
```

### Testing & Validation Approach

1. **Create test script for each entity type:**
```python
# test_create_ticket.py
async def test_create_minimal_ticket():
    """Test with absolute minimum fields"""
    pass

async def test_create_full_ticket():
    """Test with all fields populated"""
    pass

async def test_ticket_relationships():
    """Test linking to company, contact, contract"""
    pass
```

2. **Validate data integrity after migration:**
```python
def validate_migration():
    # Count records in source
    autotask_count = get_autotask_ticket_count()
    
    # Count records in destination
    superops_count = get_superops_ticket_count()
    
    # Compare
    assert autotask_count == superops_count
    
    # Spot check relationships
    sample_tickets = get_sample_tickets(10)
    for ticket in sample_tickets:
        validate_ticket_relationships(ticket)
```

### SuperOps-Specific Gotchas & Solutions

1. **HTML Content:** SuperOps accepts HTML in description/content fields but may strip certain tags
2. **Date Formats:** Use ISO 8601 format: "2024-01-15T10:30:00Z"
3. **IDs:** Most IDs are strings, not integers
4. **Pagination:** GraphQL uses cursor-based pagination, not offset
5. **Attachments:** Use REST endpoint for file uploads, then link via GraphQL
6. **Bulk Operations:** No bulk create mutations - must loop
7. **Transactions:** No transaction support - implement rollback logic

### REST API Endpoints (When GraphQL Isn't Enough)

```python
# File uploads
POST https://{subdomain}.superops.ai/api/upload
Headers: {
    "Authorization": "Bearer {token}",
    "Content-Type": "multipart/form-data"
}

# Webhooks
POST https://{subdomain}.superops.ai/api/webhooks

# Reports
GET https://{subdomain}.superops.ai/api/reports/{report_id}
```

### Emergency Rollback Strategy

```python
class MigrationRollback:
    def __init__(self):
        self.created_entities = []
    
    def track_creation(self, entity_type, entity_id):
        self.created_entities.append({
            "type": entity_type,
            "id": entity_id,
            "timestamp": datetime.now()
        })
    
    def rollback(self):
        # Delete in reverse order
        for entity in reversed(self.created_entities):
            delete_entity(entity["type"], entity["id"])
```

### Recommended Migration Tool Structure

```
autotask-superops-migrator/
├── extractors/          # Pull data from Autotask
│   ├── tickets.py
│   ├── contacts.py
│   ├── projects.py
│   └── contracts.py
├── transformers/        # Map Autotask -> SuperOps
│   ├── field_mapper.py
│   ├── enum_mapper.py
│   └── relationship_mapper.py
├── loaders/            # Push to SuperOps
│   ├── graphql_client.py
│   ├── rest_client.py
│   └── entity_creators/
│       ├── ticket_creator.py
│       ├── contact_creator.py
│       └── project_creator.py
├── validators/         # Verify migration
│   └── integrity_checker.py
└── rollback/          # Emergency cleanup
    └── rollback_manager.py
```

## Next Steps for Full Migration

1. **Get Autotask API access** and document all available endpoints
2. **Run introspection queries** on SuperOps for all entity types needed
3. **Create test scripts** for each entity type with minimal data
4. **Build field mapping configuration** between systems
5. **Implement extraction scripts** for Autotask data
6. **Test with small batches** (10 records) of each type
7. **Add relationship linking** after base entities work
8. **Implement full migration** with progress tracking
9. **Validate data integrity** post-migration
10. **Document any manual steps** needed post-migration

## Remember

- **ALWAYS test in a sandbox/test environment first**
- **The visibility field pattern applies to many entities, not just KB**
- **Use introspection liberally - the schema is your friend**
- **Start with minimal fields, add complexity gradually**
- **Track everything for rollback capability**
- **Rate limit yourself before SuperOps does**