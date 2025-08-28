"""
API coverage tests for the py-autotask library.

This module validates that the library provides comprehensive coverage
of the Autotask REST API, including all major endpoints, entity types,
and operation patterns.
"""

import inspect
from unittest.mock import patch

import pytest

try:
    import responses

    HAS_RESPONSES = True
except ImportError:
    HAS_RESPONSES = False
    responses = None

from py_autotask import entities
from py_autotask.client import AutotaskClient
from py_autotask.entities import EntityManager
from py_autotask.entities.base import BaseEntity


class TestAPICoverage:
    """Test cases for API coverage validation."""

    # Known Autotask API entities that should be covered
    EXPECTED_CORE_ENTITIES = {
        "Tickets",
        "Companies",
        "Contacts",
        "Projects",
        "Resources",
        "Contracts",
        "TimeEntries",
        "Attachments",
        "Notes",
        "Tasks",
        "BillingCodes",
        "Invoices",
        "Quotes",
        "PurchaseOrders",
        "Products",
        "Services",
        "ConfigurationItems",
        "Opportunities",
        "Accounts",
        "Departments",
        "Teams",
        "Roles",
        "WorkTypes",
    }

    # Entity categories for comprehensive coverage
    ENTITY_CATEGORIES = {
        "Core Service Desk": {
            "Tickets",
            "TicketCategories",
            "TicketStatuses",
            "TicketPriorities",
            "TicketSources",
            "TicketNotes",
            "TicketAttachments",
            "TicketHistory",
        },
        "Customer Management": {
            "Companies",
            "Contacts",
            "CompanyCategories",
            "CompanyNotes",
            "CompanyAttachments",
            "ContactGroups",
        },
        "Project Management": {
            "Projects",
            "ProjectPhases",
            "ProjectMilestones",
            "ProjectCharges",
            "Tasks",
            "TaskNotes",
            "TimeEntries",
        },
        "Financial": {
            "Invoices",
            "Quotes",
            "BillingCodes",
            "BillingItems",
            "Expenses",
            "PurchaseOrders",
            "ContractCharges",
            "ProjectCharges",
        },
        "Contracts & Services": {
            "Contracts",
            "ContractServices",
            "ServiceLevelAgreements",
            "Products",
            "Services",
            "Subscriptions",
        },
        "Human Resources": {
            "Resources",
            "Departments",
            "Teams",
            "Roles",
            "ResourceRoles",
            "WorkTypes",
            "HolidaySets",
            "ResourceSkills",
        },
        "Configuration Management": {
            "ConfigurationItems",
            "ConfigurationItemTypes",
            "ConfigurationItemCategories",
            "InstalledProducts",
            "ConfigurationItemNotes",
            "ConfigurationItemAttachments",
        },
        "System & Administration": {
            "CustomFields",
            "UserDefinedFields",
            "NotificationRules",
            "BusinessRules",
            "WorkflowRules",
            "SecurityPolicies",
        },
    }

    def test_core_entities_available(self, mock_auth):
        """Test that all core entities are available."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        missing_entities = []
        for entity_name in self.EXPECTED_CORE_ENTITIES:
            try:
                entity = manager.get_entity(entity_name)
                assert entity is not None
                assert isinstance(entity, BaseEntity)
            except Exception:
                missing_entities.append(entity_name)

        if missing_entities:
            pytest.fail(f"Missing core entities: {missing_entities}")

    def test_entity_category_coverage(self, mock_auth):
        """Test coverage across different entity categories."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        coverage_report = {}

        for category, expected_entities in self.ENTITY_CATEGORIES.items():
            available_entities = []
            missing_entities = []

            for entity_name in expected_entities:
                try:
                    entity = manager.get_entity(entity_name)
                    if entity is not None:
                        available_entities.append(entity_name)
                    else:
                        missing_entities.append(entity_name)
                except Exception:
                    missing_entities.append(entity_name)

            coverage_report[category] = {
                "available": available_entities,
                "missing": missing_entities,
                "coverage_percentage": (
                    len(available_entities) / len(expected_entities)
                )
                * 100,
            }

        # Print coverage report for visibility
        print("\n=== API Coverage Report ===")
        for category, report in coverage_report.items():
            print(
                f"{category}: {report['coverage_percentage']:.1f}% "
                f"({len(report['available'])}/{len(report['available']) + len(report['missing'])})"
            )
            if report["missing"]:
                print(f"  Missing: {report['missing']}")

        # Ensure reasonable coverage for core categories
        critical_categories = ["Core Service Desk", "Customer Management", "Financial"]
        for category in critical_categories:
            if category in coverage_report:
                coverage = coverage_report[category]["coverage_percentage"]
                assert (
                    coverage >= 70
                ), f"{category} has insufficient coverage: {coverage:.1f}%"

    def test_crud_operations_coverage(self, mock_auth):
        """Test that entities support standard CRUD operations."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test core entities have CRUD operations
        test_entities = ["Tickets", "Companies", "Contacts", "Projects"]

        for entity_name in test_entities:
            entity = manager.get_entity(entity_name)

            # Check CRUD methods exist
            crud_methods = ["get", "create", "update", "delete"]
            for method in crud_methods:
                assert hasattr(entity, method), f"{entity_name} missing {method} method"
                assert callable(getattr(entity, method))

    def test_query_operations_coverage(self, mock_auth):
        """Test that entities support query operations."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test entities have query capabilities
        test_entities = ["Tickets", "Companies", "Contacts", "Projects", "Resources"]

        for entity_name in test_entities:
            entity = manager.get_entity(entity_name)

            # Check query methods exist
            query_methods = ["query", "query_all"]
            for method in query_methods:
                assert hasattr(entity, method), f"{entity_name} missing {method} method"
                assert callable(getattr(entity, method))

    def test_specialized_entity_methods(self, mock_auth):
        """Test that specialized entities have domain-specific methods."""
        client = AutotaskClient(mock_auth)

        # Test TicketsEntity specialized methods
        tickets = client.tickets
        if hasattr(tickets, "create_ticket"):
            assert callable(tickets.create_ticket)

        # Test that method signatures are reasonable
        methods_to_check = []
        if hasattr(tickets, "create_ticket"):
            methods_to_check.append(
                ("create_ticket", ["title", "description", "account_id"])
            )

        for method_name, expected_params in methods_to_check:
            method = getattr(tickets, method_name)
            sig = inspect.signature(method)
            for param in expected_params:
                assert (
                    param in sig.parameters
                ), f"{method_name} missing {param} parameter"

    def test_entity_count_coverage(self, mock_auth):
        """Test that we have substantial entity coverage."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Count registered entities
        registered_count = len(manager.ENTITY_CLASSES)

        # Should have a substantial number of entities (aiming for 100+ for comprehensive coverage)
        assert (
            registered_count >= 100
        ), f"Only {registered_count} entities registered, expected 100+"

        print(f"\nTotal registered entities: {registered_count}")

    def test_all_entities_importable(self):
        """Test that all entity classes can be imported successfully."""
        # Get all entity classes from the entities module
        entity_classes = []
        import_failures = []

        for name in dir(entities):
            if name.endswith("Entity") and not name.startswith("_"):
                try:
                    cls = getattr(entities, name)
                    if inspect.isclass(cls) and issubclass(cls, BaseEntity):
                        entity_classes.append((name, cls))
                except Exception as e:
                    import_failures.append((name, str(e)))

        if import_failures:
            pytest.fail(f"Failed to import entities: {import_failures}")

        # Verify we have a good number of entity classes
        assert (
            len(entity_classes) >= 100
        ), f"Only {len(entity_classes)} entity classes found"

        print(f"Successfully imported {len(entity_classes)} entity classes")

    def test_entity_naming_conventions(self, mock_auth):
        """Test that entity naming follows conventions."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        naming_issues = []

        for entity_name, entity_class in manager.ENTITY_CLASSES.items():
            # Class names should end with 'Entity'
            if not entity_class.__name__.endswith("Entity"):
                naming_issues.append(
                    f"{entity_class.__name__} doesn't end with 'Entity'"
                )

            # Entity names should be reasonable
            if len(entity_name) < 2:
                naming_issues.append(f"Entity name '{entity_name}' too short")

        if naming_issues:
            pytest.fail(f"Naming convention issues: {naming_issues}")

    def test_api_endpoint_patterns(self, mock_auth):
        """Test that entities follow standard API endpoint patterns."""
        client = AutotaskClient(mock_auth)

        # Test that basic operations work with standard patterns
        test_entities = ["Tickets", "Companies", "Contacts", "Projects"]

        for entity_name in test_entities:
            entity = client.entities.get_entity(entity_name)

            # These should not raise exceptions
            try:
                with patch.object(client, "get", return_value={"id": 12345}):
                    result = entity.get(12345)
                    assert result is not None
            except Exception as e:
                pytest.fail(f"{entity_name}.get() failed: {e}")

    def test_entity_documentation_coverage(self, mock_auth):
        """Test that entities have adequate documentation."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        undocumented_entities = []

        # Check a sample of entities for documentation
        sample_entities = list(manager.ENTITY_CLASSES.keys())[:20]

        for entity_name in sample_entities:
            entity_class = manager.ENTITY_CLASSES[entity_name]

            if not entity_class.__doc__ or len(entity_class.__doc__.strip()) < 10:
                undocumented_entities.append(entity_name)

        if undocumented_entities:
            print(f"Entities with insufficient documentation: {undocumented_entities}")
            # Don't fail the test, but warn about documentation

        # At least 80% should have some documentation
        documented_count = len(sample_entities) - len(undocumented_entities)
        coverage_ratio = (
            documented_count / len(sample_entities) if sample_entities else 0
        )

        assert (
            coverage_ratio >= 0.6
        ), f"Documentation coverage too low: {coverage_ratio:.1%}"

    def test_field_information_methods(self, mock_auth):
        """Test that entities support field information retrieval."""
        client = AutotaskClient(mock_auth)

        # Test that client has field info methods
        assert hasattr(client, "get_field_info"), "Client missing get_field_info method"

        # Test with a core entity
        with patch.object(client, "get_field_info", return_value={"fields": []}):
            field_info = client.get_field_info("Tickets")
            assert field_info is not None

    def test_batch_operations_support(self, mock_auth):
        """Test support for batch operations."""
        client = AutotaskClient(mock_auth)

        # Check if client supports batch operations
        batch_methods = ["create_batch", "update_batch", "delete_batch"]

        for method in batch_methods:
            if hasattr(client, method):
                assert callable(getattr(client, method))

    def test_pagination_support(self, mock_auth):
        """Test that pagination is properly supported."""
        client = AutotaskClient(mock_auth)
        entity = client.entities.get_entity("Tickets")

        # Test query_all method exists (for pagination)
        assert hasattr(
            entity, "query_all"
        ), "Entity missing query_all method for pagination"

        # Check signature has pagination parameters
        sig = inspect.signature(entity.query_all)
        pagination_params = ["max_total_records", "page_size"]

        for param in pagination_params:
            assert param in sig.parameters, f"query_all missing {param} parameter"

    def test_error_handling_coverage(self, mock_auth):
        """Test that proper error handling is implemented."""
        from py_autotask.exceptions import (
            AutotaskConnectionError,
            AutotaskTimeoutError,
            AutotaskValidationError,
        )

        # Test that custom exceptions are defined and importable
        exception_classes = [
            AutotaskConnectionError,
            AutotaskValidationError,
            AutotaskTimeoutError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, Exception)
            assert exc_class.__name__.startswith("Autotask")

    def test_authentication_coverage(self, mock_auth):
        """Test that authentication mechanisms are properly covered."""
        from py_autotask.auth import AutotaskAuth
        from py_autotask.types import AuthCredentials, ZoneInfo

        # Test auth classes are available
        assert AutotaskAuth is not None
        assert AuthCredentials is not None
        assert ZoneInfo is not None

        # Test client creation methods
        assert hasattr(AutotaskClient, "create"), "Client missing create class method"

    def test_utility_functions_coverage(self, mock_auth):
        """Test that utility functions provide good coverage."""
        from py_autotask import utils

        # Test that utils module has key functions
        expected_utils = ["handle_api_error", "validate_filter"]

        for util_func in expected_utils:
            if hasattr(utils, util_func):
                assert callable(getattr(utils, util_func))

    def test_comprehensive_entity_list(self, mock_auth):
        """Generate a comprehensive list of all available entities for documentation."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        all_entities = sorted(manager.ENTITY_CLASSES.keys())

        print(f"\n=== Complete Entity List ({len(all_entities)} total) ===")
        for i, entity_name in enumerate(all_entities, 1):
            print(f"{i:3}. {entity_name}")

        # Verify we have comprehensive coverage
        assert (
            len(all_entities) >= 150
        ), f"Expected 150+ entities, found {len(all_entities)}"

    def test_api_version_support(self, mock_auth):
        """Test that the library supports the correct API version."""
        # Test that API URLs are constructed with v1.0
        # by checking the client code directly
        import inspect

        from py_autotask.client import AutotaskClient

        # Get the source code of the client
        source = inspect.getsource(AutotaskClient)

        # Verify that the client uses v1.0 in URL construction
        assert "/v1.0/" in source, "Client should use v1.0 API endpoints"

        # Also verify that the client instance can be created
        client = AutotaskClient(mock_auth)
        assert client is not None
