#!/usr/bin/env python3
"""
Simple test runner to verify our test structure without full pytest dependencies.

This script performs basic validation of our test files to ensure they are
correctly structured and importable.
"""

import sys
import os
import importlib.util

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_module_from_path(name, path):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_test_file(test_path):
    """Validate a test file structure."""
    print(f"Validating {test_path}...")

    try:
        # Load the module
        module_name = os.path.basename(test_path).replace(".py", "")
        module = load_module_from_path(module_name, test_path)

        # Check for test classes
        test_classes = [
            name
            for name in dir(module)
            if name.startswith("Test") and hasattr(getattr(module, name), "__bases__")
        ]

        if not test_classes:
            print(f"  WARNING: No test classes found in {test_path}")
            return False

        print(f"  Found test classes: {test_classes}")

        # Check test methods in each class
        total_tests = 0
        for class_name in test_classes:
            test_class = getattr(module, class_name)
            test_methods = [
                name for name in dir(test_class) if name.startswith("test_")
            ]
            total_tests += len(test_methods)
            print(f"    {class_name}: {len(test_methods)} test methods")

        print(f"  Total test methods: {total_tests}")
        print(f"  ✅ {test_path} validation passed")
        return True

    except Exception as e:
        print(f"  ❌ {test_path} validation failed: {e}")
        return False


def main():
    """Main test validation."""
    print("=" * 60)
    print("PY-AUTOTASK TEST VALIDATION")
    print("=" * 60)

    test_files = [
        "tests/test_new_entities.py",
        "tests/test_entity_integration.py",
        "tests/test_api_coverage.py",
        "tests/test_client.py",
    ]

    passed = 0
    failed = 0

    for test_file in test_files:
        if os.path.exists(test_file):
            if validate_test_file(test_file):
                passed += 1
            else:
                failed += 1
        else:
            print(f"❌ {test_file} not found")
            failed += 1
        print()

    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")

    if failed == 0:
        print("\n🎉 All test files validated successfully!")
        print("Tests are ready for execution with pytest.")
    else:
        print(f"\n⚠️  {failed} test files failed validation.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
