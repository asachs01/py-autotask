#!/usr/bin/env python3
"""Debug the flow to see where the conversion goes wrong."""

import os
from py_autotask import AutotaskClient
from py_autotask.types import QueryRequest, QueryFilter

# Get credentials from environment
username = os.getenv("AUTOTASK_USERNAME")
integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
secret = os.getenv("AUTOTASK_SECRET")

# Create client
client = AutotaskClient.create(
    username=username,
    integration_code=integration_code,
    secret=secret
)

# Let's trace what happens when we call companies.query with a dict
print("Testing entities/base.py flow:")

# This is what test_final_verification.py calls
input_dict = {
    "filter": [{"op": "gte", "field": "id", "value": 0}],
    "maxRecords": 2
}

print(f"1. Input dict: {input_dict}")

# See what entities/base.py does
from py_autotask.types import QueryRequest, QueryFilter

# From entities/base.py query() method
filters = input_dict
query_request = QueryRequest()

if filters:
    from py_autotask.types import QueryFilter
    if isinstance(filters, dict):
        print(f"2. Filters is a dict: {filters}")
        # Single filter dict or nested filter format
        if "op" in filters and "field" in filters:
            # Already in correct format
            query_request.filter = [QueryFilter(**filters)]
            print("   - Has op and field, treating as single filter")
        else:
            # Might be nested format like {"id": {"gte": 0}}
            from py_autotask.utils import convert_filter_format
            print("   - No op/field, trying to convert filter format")
            converted_filters = convert_filter_format(filters)
            print(f"   - Converted filters: {converted_filters}")
            query_request.filter = [QueryFilter(**f) for f in converted_filters]

print(f"3. QueryRequest filter: {query_request.filter}")
print(f"4. QueryRequest as dict: {query_request.model_dump(exclude_unset=True, by_alias=True)}")

# The problem is that when entities/base.py passes a DICT to client.companies.query,
# it has "filter" and "maxRecords" keys, not "op" and "field"!