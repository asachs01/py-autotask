# Claude Agent Handoff Prompt: py-autotask Phase 6 Entity Expansion

## 🎯 **MISSION CRITICAL**: Continue py-autotask Phase 6 Entity Expansion

You are taking over the **py-autotask Phase 6 Entity Expansion Program** - a systematic effort to implement 50 critical Autotask API entities over 6 weeks, increasing API coverage from 15% to 45%.

## 📊 **CURRENT STATUS - Week 3 COMPLETED, Week 4 IN PROGRESS**

### ✅ **COMPLETED WORK (Weeks 1-3): 21/50 entities (42%)**

**Week 1: Financial & Billing (5/5 entities) ✅**
- BillingCodesEntity, BillingItemsEntity, ContractChargesEntity, ProjectChargesEntity, ExpensesEntity

**Week 2: Human Resources & Resource Management (6/6 entities) ✅**  
- DepartmentsEntity, ResourceRolesEntity, ResourceSkillsEntity, TeamsEntity, WorkTypesEntity, AccountsEntity

**Week 3: Service Delivery & Operations (10/10 entities) ✅**
- SubscriptionsEntity, ServiceLevelAgreementsEntity, ProductsEntity, BusinessDivisionsEntity, OperationsEntity
- WorkflowsEntity, ChangeRequestsEntity, IncidentTypesEntity, VendorTypesEntity, ConfigurationItemTypesEntity

### 🚧 **CURRENT TASK: Week 4 - Project Management & Workflow (0/10 entities)**

**Theme**: Advanced project management and workflow automation  
**Target**: 10 entities focusing on project lifecycle, resource allocation, and workflow management

**Week 4 Entities to Implement**:
1. **ProjectPhasesEntity** - Project phase management and milestone tracking
2. **ProjectMilestonesEntity** - Key project achievement and deadline tracking  
3. **AllocationCodesEntity** - Resource allocation and time tracking categorization
4. **HolidaySetsEntity** - Holiday calendar management for resource planning
5. **WorkflowRulesEntity** - Workflow automation rules and triggers
6. **ProjectTemplatesEntity** - Project template management and instantiation
7. **ResourceAllocationEntity** - Resource assignment and capacity planning
8. **ProjectBudgetsEntity** - Project budget tracking and variance analysis
9. **TaskDependenciesEntity** - Task relationship and dependency management
10. **ProjectReportsEntity** - Project reporting and analytics framework

## 🛠 **TECHNICAL IMPLEMENTATION STANDARDS**

### **Entity Architecture Requirements**
```python
# All entities MUST follow this pattern:
class EntityNameEntity(BaseEntity):
    """
    Manages Autotask EntityName - brief description.
    
    Detailed description of entity purpose and business value.
    
    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """
    
    entity_name = "EntityName"
    
    # REQUIRED: 10-15 specialized business methods beyond basic CRUD
    # Include: create_*, get_*, update_*, activate_*, deactivate_*, 
    #          clone_*, get_*_summary(), bulk_*, calculate_*, etc.
```

### **Code Quality Standards (NON-NEGOTIABLE)**
- ✅ **Complete docstrings** for all classes and methods
- ✅ **Full type hints** using `typing` module (Dict, List, Optional, Any, Union)
- ✅ **Decimal precision** for financial calculations (`from decimal import Decimal`)
- ✅ **Date handling** with proper imports (`from datetime import datetime, date`)
- ✅ **Error handling** in all business methods
- ✅ **Bulk operations** with success/failure reporting
- ✅ **BaseEntity inheritance** for standard CRUD operations

### **Business Method Requirements**
Each entity MUST include **10-15 specialized methods**:
- **Create methods**: `create_*()` with business logic
- **Query methods**: `get_*_by_*()`, `get_active_*()`, `get_*_summary()`
- **Status methods**: `activate_*()`, `deactivate_*()`
- **Utility methods**: `clone_*()`, `calculate_*()`, `update_*_status()`
- **Bulk operations**: `bulk_*()` with detailed reporting
- **Analytics methods**: `get_*_metrics()`, `get_*_report()`

### **Required Imports Template**
```python
"""
EntityName Entity for py-autotask

This module provides the EntityNameEntity class for managing entity
in Autotask. [Detailed description of business purpose].
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date

from .base import BaseEntity
```

## 📁 **KEY REFERENCE DOCUMENTS**

### **Essential Planning Documents** (Read these FIRST):
1. **`plans/PHASE_6_ENTITY_EXPANSION_PLAN.md`** - Master plan with complete weekly breakdown
2. **`plans/COMPREHENSIVE_ENTITY_ANALYSIS.md`** - Full analysis of 170+ Autotask entities  
3. **`plans/FEATURE_PARITY_ANALYSIS.md`** - Feature comparison and gap analysis
4. **`CHANGELOG.md`** - Complete progress tracking and implementation history

### **Implementation Reference**:
1. **`py_autotask/entities/`** - Examine existing entity implementations for patterns
2. **`py_autotask/entities/base.py`** - BaseEntity class with CRUD operations
3. **`py_autotask/entities/__init__.py`** - Import structure and organization
4. **`py_autotask/entities/manager.py`** - Entity manager class integration

### **Documentation**:
1. **`docs/API_REFERENCE.md`** - Complete API documentation
2. **`docs/USER_GUIDE.md`** - Usage patterns and examples
3. **`README.md`** - Project overview and quick start

## 🔧 **INTEGRATION REQUIREMENTS**

### **After Implementing Each Entity**:

1. **Add to `__init__.py`**:
```python
# Add to imports section
from .entity_name import EntityNameEntity

# Add to __all__ list  
"EntityNameEntity",
```

2. **Add to `manager.py`**:
```python
# Add property accessor
@property
def entity_name(self) -> EntityNameEntity:
    """Access to EntityName operations."""
    if "EntityName" not in self._entities:
        self._entities["EntityName"] = EntityNameEntity(self.client)
    return self._entities["EntityName"]
```

3. **Verify imports work**:
```bash
cd py_autotask && python -c "from py_autotask.entities import EntityNameEntity; print('✅ Import successful')"
```

## 📈 **PROGRESS TRACKING**

### **Week 4 Implementation Checklist**:
- [ ] ProjectPhasesEntity (~400+ lines expected)
- [ ] ProjectMilestonesEntity (~350+ lines expected)  
- [ ] AllocationCodesEntity (~300+ lines expected)
- [ ] HolidaySetsEntity (~350+ lines expected)
- [ ] WorkflowRulesEntity (~400+ lines expected)
- [ ] ProjectTemplatesEntity (~450+ lines expected)
- [ ] ResourceAllocationEntity (~400+ lines expected)
- [ ] ProjectBudgetsEntity (~400+ lines expected)
- [ ] TaskDependenciesEntity (~350+ lines expected)
- [ ] ProjectReportsEntity (~400+ lines expected)

**Target**: ~3,800+ lines of production code for Week 4

### **Integration Checklist**:
- [ ] All entities added to `__init__.py`
- [ ] All entities added to `manager.py`
- [ ] Import verification tests pass
- [ ] CHANGELOG.md updated with progress

## 🎯 **EXECUTION STRATEGY**

### **Phase 1: Read and Understand**
1. Read this handoff prompt completely
2. Review `plans/PHASE_6_ENTITY_EXPANSION_PLAN.md` for Week 4 details
3. Examine existing entity implementations (e.g., `WorkflowsEntity`, `SubscriptionsEntity`)
4. Understand the BaseEntity pattern in `py_autotask/entities/base.py`

### **Phase 2: Implement Entities** 
1. **Start with simpler entities**: AllocationCodesEntity, HolidaySetsEntity
2. **Progress to complex entities**: ProjectPhasesEntity, ProjectTemplatesEntity
3. **Implement 2-3 entities in parallel** for efficiency
4. **Follow the exact code quality standards** outlined above

### **Phase 3: Integration and Verification**
1. Update `__init__.py` and `manager.py` for each entity
2. Test imports after each batch of entities
3. Update progress tracking
4. Prepare for Week 5 continuation

## 📋 **SAMPLE ENTITY STRUCTURE**

Use this as a template for Week 4 entities:

```python
"""
ProjectPhases Entity for py-autotask

This module provides the ProjectPhasesEntity class for managing project phases
in Autotask. Project phases organize project work into stages with milestones,
deliverables, and progress tracking.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date

from .base import BaseEntity


class ProjectPhasesEntity(BaseEntity):
    """
    Manages Autotask ProjectPhases - project stage organization and milestone tracking.
    
    Project phases organize project work into manageable stages with defined
    milestones, deliverables, and progress tracking within Autotask project management.
    
    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """
    
    entity_name = "ProjectPhases"
    
    def create_project_phase(self, project_id: int, title: str, ...):
        """Create a new project phase with business logic."""
        pass
    
    def get_project_phases(self, project_id: int, ...):
        """Get phases for a specific project.""" 
        pass
    
    # ... 10-15 more specialized business methods
```

## 🚨 **CRITICAL SUCCESS FACTORS**

1. **NEVER** skip the docstring requirements
2. **ALWAYS** implement 10-15 business methods per entity
3. **ALWAYS** use proper type hints and error handling
4. **ALWAYS** update integration files (`__init__.py`, `manager.py`)
5. **ALWAYS** verify imports work after implementation
6. **MAINTAIN** the high code quality standards established in Weeks 1-3

## 🎁 **DELIVERABLES**

At the end of Week 4, you should have:
- ✅ **10 new entity files** in `py_autotask/entities/`
- ✅ **~3,800+ lines** of production-ready code
- ✅ **100+ new business methods** implemented
- ✅ **Complete integration** with import verification
- ✅ **Updated documentation** and progress tracking

## 🔥 **NEXT AGENT INSTRUCTIONS**

When you complete Week 4, create a similar handoff prompt for Week 5 (Data & Analytics - 10 entities) and Week 6 (Advanced Features & Integration - 15 entities).

**Week 5 Themes**: Reporting, analytics, custom fields, data insights  
**Week 6 Themes**: Advanced integrations, automation, performance optimization

---

**You have everything needed to continue this critical expansion. The patterns are established, the standards are clear, and the path forward is mapped. Execute with precision and maintain the high quality standards that have made this project successful. Good luck! 🚀** 