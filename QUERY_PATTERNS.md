# Query Pattern Standards

This document outlines the standardized query patterns used across all entities in the py-autotask SDK.

## Overview

All entities now use consistent `QueryFilter` objects instead of string-based filter patterns. This provides better type safety, validation, and maintainability.

## Migration Summary

### Before (Old Patterns)
```python
# String-based filters
self.query(filter="isActive eq true")
self.query(filter=f"accountID eq {account_id}")
self.query(filter=" and ".join(filters))

# Mixed patterns
filters.append({"field": "isActive", "op": "eq", "value": True})
filters.append("status eq 'Active'")
```

### After (New Patterns)
```python
# QueryFilter objects with helper functions
from .query_helpers import (
    build_equality_filter,
    build_active_filter,
    build_null_filter,
    combine_filters,
)

filters = [
    build_active_filter(True),
    build_equality_filter("accountID", account_id)
]
self.query(filters=combine_filters(filters))
```

## Query Helper Functions

### Basic Filters

#### `build_equality_filter(field, value, udf=False)`
Creates an equality filter.
```python
filter = build_equality_filter("status", "Active")
filter = build_equality_filter("accountID", 123)
```

#### `build_active_filter(active=True)`
Creates a standard active/inactive filter.
```python
active_filter = build_active_filter(True)   # isActive eq true
inactive_filter = build_active_filter(False) # isActive eq false
```

#### `build_null_filter(field, is_null=True, udf=False)`
Creates null/not null filters.
```python
null_filter = build_null_filter("parentID", is_null=True)      # parentID eq null
not_null_filter = build_null_filter("parentID", is_null=False) # parentID ne null
```

### Comparison Filters

#### `build_gte_filter(field, value, udf=False)`
Creates greater-than-or-equal filter.
```python
date_filter = build_gte_filter("createdDate", "2023-01-01")
price_filter = build_gte_filter("unitPrice", 100.0)
```

#### `build_lte_filter(field, value, udf=False)`
Creates less-than-or-equal filter.
```python
date_filter = build_lte_filter("createdDate", "2023-12-31")
price_filter = build_lte_filter("unitPrice", 1000.0)
```

### Advanced Filters

#### `build_search_filters(search_term, fields, case_sensitive=False)`
Creates contains filters for multiple fields.
```python
search_filters = build_search_filters("test", ["name", "description"])
# Returns list of filters with 'contains' operation
```

#### `build_in_filter(field, values, udf=False)`
Creates an 'in' filter for multiple values.
```python
status_filter = build_in_filter("status", ["Open", "In Progress", "Closed"])
id_filter = build_in_filter("id", [1, 2, 3, 4, 5])
```

#### `build_date_range_filters(field, start_date=None, end_date=None)`
Creates date range filters.
```python
from datetime import date
date_filters = build_date_range_filters(
    "createdDate", 
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)
# Returns list with GTE and LTE filters
```

### Combining Filters

#### `combine_filters(filters, logic="and")`
Combines multiple filters (currently only AND logic supported).
```python
filters = [
    build_active_filter(True),
    build_equality_filter("accountType", "Customer"),
    build_gte_filter("createdDate", "2023-01-01")
]
combined = combine_filters(filters)
results = self.query(filters=combined)
```

## Standard Patterns

### Entity Retrieval Patterns

#### Get Active Items
```python
def get_active_items(self, additional_filter_field=None, additional_filter_value=None):
    filters = [build_active_filter(True)]
    
    if additional_filter_field and additional_filter_value:
        filters.append(build_equality_filter(additional_filter_field, additional_filter_value))
    
    return self.query(filters=combine_filters(filters))
```

#### Get Items by Parent
```python
def get_items_by_parent(self, parent_id, parent_field="parentID"):
    filters = [build_equality_filter(parent_field, parent_id)]
    return self.query(filters=combine_filters(filters))
```

#### Search Items
```python
def search_items(self, search_term, search_fields=None):
    if search_fields is None:
        search_fields = ["name", "description"]
    
    # For OR logic, perform separate queries and merge
    all_results = []
    for field in search_fields:
        search_filters = build_search_filters(search_term, [field])
        results = self.query(filters=search_filters)
        if hasattr(results, 'items'):
            all_results.extend(results.items)
        else:
            all_results.extend(results)
    
    # Remove duplicates
    seen_ids = set()
    unique_results = []
    for item in all_results:
        item_id = item.get('id')
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            unique_results.append(item)
    
    return unique_results
```

#### Date Range Queries
```python
def get_items_by_date_range(self, date_field, start_date=None, end_date=None):
    filters = []
    
    if start_date:
        filters.append(build_gte_filter(date_field, start_date.isoformat()))
    if end_date:
        filters.append(build_lte_filter(date_field, end_date.isoformat()))
    
    return self.query(filters=combine_filters(filters) if filters else None)
```

## Migration Guide

### Step 1: Add Imports
Add query helper imports to entity files:
```python
from .query_helpers import (
    build_equality_filter,
    build_active_filter,
    build_null_filter,
    build_gte_filter,
    build_lte_filter,
    build_search_filters,
    build_in_filter,
    combine_filters,
)
from ..types import QueryFilter
```

### Step 2: Convert String Filters

#### Simple Equality
```python
# Old
self.query(filter="isActive eq true")
# New
filters = [build_active_filter(True)]
self.query(filters=combine_filters(filters))
```

#### Variable Substitution
```python
# Old
self.query(filter=f"accountID eq {account_id}")
# New
filters = [build_equality_filter("accountID", account_id)]
self.query(filters=combine_filters(filters))
```

#### Combined Filters
```python
# Old
filters = ["isActive eq true", f"accountType eq '{account_type}'"]
self.query(filter=" and ".join(filters))

# New
filters = [
    build_active_filter(True),
    build_equality_filter("accountType", account_type)
]
self.query(filters=combine_filters(filters))
```

### Step 3: Handle Dict-Based Filters
```python
# Old
filters.append({"field": "isActive", "op": "eq", "value": True})

# New
filters.append(build_equality_filter("isActive", True))
```

## Known Limitations

### OR Logic Handling
The Autotask API treats filter lists as AND logic by default. For OR logic:

1. **Simple OR with single field**: Use `build_in_filter()`
   ```python
   # Multiple values for same field
   filter = build_in_filter("status", ["Open", "In Progress"])
   ```

2. **Complex OR across fields**: Perform separate queries and merge results
   ```python
   # Search across multiple fields
   all_results = []
   for field in ["name", "description"]:
       search_filters = build_search_filters(term, [field])
       results = self.query(filters=search_filters)
       all_results.extend(results)
   # Deduplicate by ID
   ```

3. **Legacy complex patterns**: Some complex OR patterns are kept as-is due to complexity
   ```python
   # These remain as string patterns for now
   filter_str = " or ".join(complex_patterns)
   self.query(filter=filter_str)  # TODO: Convert when API supports it
   ```

## Validation

To verify your entity follows the new patterns:

1. **No string-based filters**: Search for `filter="` and `filter=f"`
2. **Consistent imports**: Ensure query_helpers are imported
3. **Use combine_filters()**: All filter lists should use `combine_filters()`
4. **Handle OR logic properly**: Use separate queries or `build_in_filter()`

## Benefits

1. **Type Safety**: QueryFilter objects provide compile-time validation
2. **Consistency**: All entities use the same patterns
3. **Maintainability**: Centralized query building logic
4. **Readability**: Clear, intention-revealing helper function names
5. **Validation**: Built-in validation of filter operations and values
6. **Testing**: Easier to unit test query building logic

## Testing Query Patterns

Run the test script to verify patterns:
```bash
python3 test_query_patterns.py
```

This will:
- Test all query helper functions
- Verify entity imports work
- Scan for remaining string-based patterns
- Report any issues found
