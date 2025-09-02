#!/usr/bin/env python3
"""
Test script to verify query pattern consistency across entities.

This script tests that all entities now use consistent QueryFilter patterns
and that the query helpers work correctly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from py_autotask.entities.query_helpers import (
    build_equality_filter,
    build_active_filter,
    build_null_filter,
    build_gte_filter,
    build_lte_filter,
    build_search_filters,
    build_in_filter,
    combine_filters,
    convert_string_filter_to_query_filter,
)
from py_autotask.types import FilterOperation, QueryFilter


def test_query_helpers():
    """Test all query helper functions."""
    print("Testing query helper functions...")
    
    # Test basic equality filter
    filter1 = build_equality_filter("isActive", True)
    assert filter1.field == "isActive"
    assert filter1.op == FilterOperation.EQ
    assert filter1.value is True
    print("  ✓ build_equality_filter works")
    
    # Test active filter
    filter2 = build_active_filter(False)
    assert filter2.field == "isActive"
    assert filter2.op == FilterOperation.EQ
    assert filter2.value is False
    print("  ✓ build_active_filter works")
    
    # Test null filter
    filter3 = build_null_filter("parentID", is_null=True)
    assert filter3.field == "parentID"
    assert filter3.op == FilterOperation.IS_NULL
    assert filter3.value is None
    print("  ✓ build_null_filter works")
    
    # Test GTE filter
    filter4 = build_gte_filter("createdDate", "2023-01-01")
    assert filter4.field == "createdDate"
    assert filter4.op == FilterOperation.GTE
    assert filter4.value == "2023-01-01"
    print("  ✓ build_gte_filter works")
    
    # Test LTE filter
    filter5 = build_lte_filter("createdDate", "2023-12-31")
    assert filter5.field == "createdDate"
    assert filter5.op == FilterOperation.LTE
    assert filter5.value == "2023-12-31"
    print("  ✓ build_lte_filter works")
    
    # Test search filters
    search_filters = build_search_filters("test", ["name", "description"])
    assert len(search_filters) == 2
    assert search_filters[0].op == FilterOperation.CONTAINS
    assert search_filters[1].op == FilterOperation.CONTAINS
    print("  ✓ build_search_filters works")
    
    # Test in filter
    in_filter = build_in_filter("status", ["Open", "In Progress", "Closed"])
    assert in_filter.op == FilterOperation.IN
    assert in_filter.value == ["Open", "In Progress", "Closed"]
    print("  ✓ build_in_filter works")
    
    # Test combine filters
    combined = combine_filters([filter1, filter2, filter3])
    assert len(combined) == 3
    print("  ✓ combine_filters works")
    
    # Test string filter conversion
    converted = convert_string_filter_to_query_filter("isActive eq true and accountType eq 'Customer'")
    assert len(converted) == 2
    assert converted[0].field == "isActive"
    assert converted[0].value is True
    assert converted[1].field == "accountType"
    assert converted[1].value == "Customer"
    print("  ✓ convert_string_filter_to_query_filter works")
    
    print("All query helper tests passed!")


def test_entity_imports():
    """Test that entities can import and use query helpers."""
    print("\nTesting entity imports...")
    
    try:
        from py_autotask.entities.accounts import AccountsEntity
        from py_autotask.entities.companies import CompaniesEntity
        from py_autotask.entities.tickets import TicketsEntity
        print("  ✓ Core entities import successfully")
        
        # Test that they have the required methods (without instantiating)
        assert hasattr(AccountsEntity, 'get_customer_accounts')
        assert hasattr(CompaniesEntity, 'get_companies_by_type')
        print("  ✓ Entity classes have expected methods")
        
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Other error: {e}")
        return False
    
    print("All entity import tests passed!")
    return True


def scan_for_remaining_issues():
    """Scan entities for any remaining string-based filter patterns."""
    print("\nScanning for remaining string-based filter patterns...")
    
    entities_dir = Path('py_autotask/entities')
    issues_found = []
    
    for file_path in entities_dir.glob('*.py'):
        if file_path.name in ['__init__.py', 'base.py', 'manager.py', 'query_helpers.py']:
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for remaining string patterns
        if 'filter="' in content:
            issues_found.append(f"{file_path}: Contains filter=\"...\" pattern")
        
        if "filter=f\"" in content:
            issues_found.append(f"{file_path}: Contains filter=f\"...\" pattern")
        
        if 'filter=" and ".join(' in content:
            issues_found.append(f"{file_path}: Contains filter=\" and \".join(...) pattern")
        
        if 'filter=" or ".join(' in content:
            issues_found.append(f"{file_path}: Contains filter=\" or \".join(...) pattern")
    
    if issues_found:
        print("  Issues found:")
        for issue in issues_found:
            print(f"    - {issue}")
        return False
    else:
        print("  ✓ No remaining string-based filter patterns found")
        return True


def main():
    """Main test function."""
    print("=== Query Pattern Consistency Test ===")
    
    try:
        test_query_helpers()
        
        if test_entity_imports():
            if scan_for_remaining_issues():
                print("\n🎉 All query pattern tests passed! The refactoring is complete.")
                return True
            else:
                print("\n⚠️  Some issues remain that need manual fixing.")
                return False
        else:
            print("\n❌ Entity import tests failed.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
