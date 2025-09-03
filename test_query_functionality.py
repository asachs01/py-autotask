#!/usr/bin/env python3
"""
Simple test to verify query functionality works after refactoring.

This test creates mock scenarios to ensure the query patterns
work correctly without requiring a live API connection.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_query_helpers_functionality():
    """Test that query helpers produce correct output."""
    print("Testing query helper functionality...")

    from py_autotask.entities.query_helpers import (
        build_equality_filter,
        build_active_filter,
        build_null_filter,
        build_gte_filter,
        build_lte_filter,
        build_search_filters,
        build_in_filter,
        combine_filters,
    )
    from py_autotask.types import FilterOperation

    # Test equality filter
    eq_filter = build_equality_filter("accountType", "Customer")
    assert eq_filter.field == "accountType"
    assert eq_filter.op == FilterOperation.EQ
    assert eq_filter.value == "Customer"
    print("  ✓ Equality filter works")

    # Test active filter
    active_filter = build_active_filter(True)
    assert active_filter.field == "isActive"
    assert active_filter.op == FilterOperation.EQ
    assert active_filter.value is True
    print("  ✓ Active filter works")

    # Test null filter
    null_filter = build_null_filter("parentID")
    assert null_filter.field == "parentID"
    assert null_filter.op == FilterOperation.IS_NULL
    assert null_filter.value is None
    print("  ✓ Null filter works")

    # Test comparison filters
    gte_filter = build_gte_filter("createdDate", "2023-01-01")
    assert gte_filter.op == FilterOperation.GTE
    print("  ✓ GTE filter works")

    lte_filter = build_lte_filter("createdDate", "2023-12-31")
    assert lte_filter.op == FilterOperation.LTE
    print("  ✓ LTE filter works")

    # Test search filters
    search_filters = build_search_filters("test term", ["name", "description"])
    assert len(search_filters) == 2
    assert all(f.op == FilterOperation.CONTAINS for f in search_filters)
    print("  ✓ Search filters work")

    # Test in filter
    in_filter = build_in_filter("status", ["Open", "Closed", "In Progress"])
    assert in_filter.op == FilterOperation.IN
    assert len(in_filter.value) == 3
    print("  ✓ IN filter works")

    # Test combine filters
    all_filters = [eq_filter, active_filter, null_filter]
    combined = combine_filters(all_filters)
    assert len(combined) == 3
    print("  ✓ Combine filters works")

    print("All query helper functionality tests passed!")


def test_entity_query_methods():
    """Test that entity query methods use correct patterns."""
    print("\nTesting entity query method patterns...")

    # Mock the client and base query method
    mock_client = Mock()
    mock_response = {"items": [{"id": 1, "name": "Test"}]}

    # Test AccountsEntity
    from py_autotask.entities.accounts import AccountsEntity

    accounts = AccountsEntity(mock_client, "Accounts")
    accounts.query = Mock(return_value=mock_response["items"])

    # Test that methods call query with filters parameter
    result = accounts.get_customer_accounts(include_inactive=False)
    accounts.query.assert_called_once()
    call_args = accounts.query.call_args
    assert "filters" in call_args.kwargs
    print("  ✓ AccountsEntity uses new query patterns")

    # Test CompaniesEntity
    from py_autotask.entities.companies import CompaniesEntity

    companies = CompaniesEntity(mock_client, "Companies")
    companies.query = Mock(return_value=mock_response["items"])

    # Call a method that should use the new patterns
    if hasattr(companies, "get_companies_by_type"):
        result = companies.get_companies_by_type("Customer")
        companies.query.assert_called_once()
        call_args = companies.query.call_args
        assert "filters" in call_args.kwargs
        print("  ✓ CompaniesEntity uses new query patterns")

    print("Entity query method tests passed!")


def test_backwards_compatibility():
    """Test that the changes don't break basic functionality."""
    print("\nTesting backwards compatibility...")

    # Test that we can still import all entities
    try:
        from py_autotask.entities import (
            AccountsEntity,
            CompaniesEntity,
            TicketsEntity,
            ProjectsEntity,
            ResourcesEntity,
        )

        print("  ✓ Core entities import successfully")
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False

    # Test that BaseEntity still works
    from py_autotask.entities.base import BaseEntity

    mock_client = Mock()
    base_entity = BaseEntity(mock_client, "TestEntity")
    assert base_entity.entity_name == "TestEntity"
    assert base_entity.client == mock_client
    print("  ✓ BaseEntity functionality preserved")

    print("Backwards compatibility tests passed!")
    return True


def main():
    """Main test function."""
    print("=== Query Functionality Test ===")

    try:
        test_query_helpers_functionality()
        test_entity_query_methods()
        if test_backwards_compatibility():
            print("\n🎉 All query functionality tests passed!")
            print("\nThe query pattern refactoring is complete and functional.")
            return True
        else:
            print("\n❌ Backwards compatibility issues found.")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
