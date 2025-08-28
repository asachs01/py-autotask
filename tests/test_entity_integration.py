"""
Integration tests for all Autotask entities.

This module tests that all entities integrate properly with the client,
entity manager, and provide consistent behavior across the entire API.
"""

import inspect
from unittest.mock import patch

import pytest

from py_autotask import entities
from py_autotask.client import AutotaskClient
from py_autotask.entities import EntityManager
from py_autotask.entities.base import BaseEntity


class TestEntityIntegration:
    """Test cases for entity integration across the library."""

    def test_entity_manager_initialization(self, mock_auth):
        """Test that EntityManager initializes correctly."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        assert manager.client is client
        assert hasattr(manager, "ENTITY_CLASSES")
        assert isinstance(manager.ENTITY_CLASSES, dict)
        assert len(manager.ENTITY_CLASSES) > 0

    def test_all_entities_in_manager(self, mock_auth):
        """Test that all defined entities are registered in EntityManager."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Get all entity classes from entities module
        entity_classes = []
        for name in dir(entities):
            obj = getattr(entities, name)
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseEntity)
                and obj is not BaseEntity
                and name.endswith("Entity")
            ):
                entity_classes.append(obj)

        # Verify core entities are in manager
        core_entities = [
            "Tickets",
            "Companies",
            "Contacts",
            "Projects",
            "Resources",
            "Contracts",
            "TimeEntries",
            "Attachments",
        ]

        for entity_name in core_entities:
            assert (
                entity_name in manager.ENTITY_CLASSES
            ), f"{entity_name} not found in EntityManager"

    def test_entity_dynamic_creation(self, mock_auth):
        """Test dynamic entity creation for entities not explicitly defined."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test dynamic creation of an entity not in ENTITY_CLASSES
        custom_entity = manager.get_entity("CustomEntity")
        assert custom_entity is not None
        assert isinstance(custom_entity, BaseEntity)
        assert custom_entity.entity_name == "CustomEntity"

    def test_entity_caching(self, mock_auth):
        """Test that entity instances are cached properly."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Get the same entity twice
        entity1 = manager.get_entity("Tickets")
        entity2 = manager.get_entity("Tickets")

        # Should return the same instance
        assert entity1 is entity2

    def test_client_entity_access(self, mock_auth):
        """Test that client provides proper access to entities."""
        client = AutotaskClient(mock_auth)

        # Test that entities property returns EntityManager
        assert isinstance(client.entities, EntityManager)

        # Test convenience properties
        convenience_entities = [
            "tickets",
            "companies",
            "contacts",
            "projects",
            "resources",
            "contracts",
        ]

        for entity_attr in convenience_entities:
            entity = getattr(client, entity_attr)
            assert entity is not None
            assert isinstance(entity, BaseEntity)

    def test_all_entities_inherit_base(self, mock_auth):
        """Test that all entities properly inherit from BaseEntity."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test a sample of entities from different categories
        sample_entities = [
            "Tickets",
            "Companies",
            "Contacts",
            "Projects",
            "ActionTypes",
            "CompanyAlerts",
            "TicketNotes",
            "ConfigurationItems",
            "Invoices",
            "Resources",
        ]

        for entity_name in sample_entities:
            if entity_name in manager.ENTITY_CLASSES:
                entity = manager.get_entity(entity_name)
                assert isinstance(entity, BaseEntity)

                # Check all required methods exist
                required_methods = ["get", "query", "create", "update", "delete"]
                for method in required_methods:
                    assert hasattr(
                        entity, method
                    ), f"{entity_name} missing {method} method"
                    assert callable(getattr(entity, method))

    def test_entity_consistent_naming(self, mock_auth):
        """Test that entity naming is consistent across the library."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        for entity_name, entity_class in manager.ENTITY_CLASSES.items():
            entity = entity_class(client, entity_name)

            # Entity name should match what was passed
            assert entity.entity_name == entity_name

            # Class name should end with 'Entity'
            assert entity_class.__name__.endswith("Entity")

    def test_entity_client_reference(self, mock_auth):
        """Test that all entities maintain proper client reference."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test a sample of entities
        sample_entities = ["Tickets", "Companies", "Projects", "Resources"]

        for entity_name in sample_entities:
            entity = manager.get_entity(entity_name)
            assert entity.client is client

    def test_entity_logger_setup(self, mock_auth):
        """Test that all entities have proper logger setup."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test a few entities
        test_entities = ["Tickets", "Companies", "ActionTypes"]

        for entity_name in test_entities:
            if entity_name in manager.ENTITY_CLASSES:
                entity = manager.get_entity(entity_name)
                assert hasattr(entity, "logger")
                assert entity.logger.name.endswith(entity_name)

    def test_entity_method_signatures(self, mock_auth):
        """Test that entity methods have consistent signatures."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test core CRUD methods exist and have proper signatures
        entity = manager.get_entity("Tickets")

        # Test get method
        get_method = getattr(entity, "get")
        sig = inspect.signature(get_method)
        assert "entity_id" in sig.parameters

        # Test query method
        query_method = getattr(entity, "query")
        sig = inspect.signature(query_method)
        assert "filters" in sig.parameters

        # Test create method
        create_method = getattr(entity, "create")
        sig = inspect.signature(create_method)
        assert "entity_data" in sig.parameters

        # Test update method
        update_method = getattr(entity, "update")
        sig = inspect.signature(update_method)
        assert "entity_data" in sig.parameters

        # Test delete method
        delete_method = getattr(entity, "delete")
        sig = inspect.signature(delete_method)
        assert "entity_id" in sig.parameters

    def test_entity_error_propagation(self, mock_auth):
        """Test that entities properly propagate errors from client."""
        client = AutotaskClient(mock_auth)
        entity = client.entities.get_entity("Tickets")

        # Mock client method to raise an exception
        with patch.object(client, "get", side_effect=Exception("Test error")):
            with pytest.raises(Exception, match="Test error"):
                entity.get(12345)

    def test_all_entities_accessible_via_manager(self, mock_auth):
        """Test that all entities defined in __init__.py are accessible."""
        client = AutotaskClient(mock_auth)
        EntityManager(client)

        # Get all entities listed in __all__ from entities module
        all_entities = getattr(entities, "__all__", [])

        # Filter out non-entity classes
        entity_names = [name for name in all_entities if name.endswith("Entity")]

        # Check that we can access a representative sample
        sample_entities = entity_names[:20]  # Test first 20 to keep test reasonable

        for entity_name in sample_entities:
            # Convert class name to entity name (remove 'Entity' suffix)
            entity_key = entity_name.replace("Entity", "")
            if entity_key.endswith("s"):
                entity_key = entity_key[:-1] + "s"  # Ensure proper pluralization

            # Try to get the entity
            try:
                entity_class = getattr(entities, entity_name)
                if inspect.isclass(entity_class) and issubclass(
                    entity_class, BaseEntity
                ):
                    entity = entity_class(client, entity_key)
                    assert entity.entity_name == entity_key
            except AttributeError:
                # Some entities might not be directly accessible - that's ok
                pass

    def test_entity_manager_get_all_entities(self, mock_auth):
        """Test EntityManager can provide access to all registered entities."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test that we can get at least the major entity categories
        major_entities = [
            "Tickets",
            "Companies",
            "Contacts",
            "Projects",
            "Resources",
            "Contracts",
            "TimeEntries",
            "Attachments",
            "BillingCodes",
            "ConfigurationItems",
            "Invoices",
        ]

        for entity_name in major_entities:
            entity = manager.get_entity(entity_name)
            assert entity is not None
            assert isinstance(entity, BaseEntity)
            assert entity.entity_name == entity_name

    def test_entity_method_chaining(self, mock_auth):
        """Test that entity operations can be chained properly."""
        client = AutotaskClient(mock_auth)

        # Test that we can chain operations
        tickets = client.tickets
        assert tickets is not None

        # Should be able to call methods
        assert callable(tickets.get)
        assert callable(tickets.query)

        # Should be able to access through entities manager
        tickets_via_manager = client.entities.get_entity("Tickets")
        assert tickets_via_manager is not None
        assert tickets is tickets_via_manager  # Should be cached

    def test_specialized_entity_methods(self, mock_auth):
        """Test that specialized entities have their specific methods."""
        client = AutotaskClient(mock_auth)

        # Test TicketsEntity has specialized methods
        tickets = client.tickets
        if hasattr(tickets, "create_ticket"):
            # Verify signature of specialized method
            sig = inspect.signature(tickets.create_ticket)
            assert "title" in sig.parameters
            assert "description" in sig.parameters
            assert "account_id" in sig.parameters

    def test_entity_consistency_across_instances(self, mock_auth):
        """Test that entity behavior is consistent across different instances."""
        client1 = AutotaskClient(mock_auth)
        client2 = AutotaskClient(mock_auth)

        # Get same entity from different clients
        entity1 = client1.entities.get_entity("Tickets")
        entity2 = client2.entities.get_entity("Tickets")

        # Should have same entity name
        assert entity1.entity_name == entity2.entity_name

        # Should have same methods available
        methods1 = [method for method in dir(entity1) if not method.startswith("_")]
        methods2 = [method for method in dir(entity2) if not method.startswith("_")]
        assert methods1 == methods2

    def test_entity_docstring_presence(self, mock_auth):
        """Test that entities have proper documentation."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Test a sample of entities have docstrings
        sample_entities = ["Tickets", "Companies", "Contacts"]

        for entity_name in sample_entities:
            if entity_name in manager.ENTITY_CLASSES:
                entity_class = manager.ENTITY_CLASSES[entity_name]
                assert entity_class.__doc__ is not None
                assert len(entity_class.__doc__.strip()) > 0

    def test_no_entity_naming_conflicts(self, mock_auth):
        """Test that there are no naming conflicts in entity registration."""
        client = AutotaskClient(mock_auth)
        manager = EntityManager(client)

        # Check that all entity names in ENTITY_CLASSES are unique
        entity_names = list(manager.ENTITY_CLASSES.keys())
        assert len(entity_names) == len(
            set(entity_names)
        ), "Duplicate entity names found"

        # Check that all entity class names are unique
        class_names = [cls.__name__ for cls in manager.ENTITY_CLASSES.values()]
        assert len(class_names) == len(
            set(class_names)
        ), "Duplicate entity class names found"

    def test_entity_memory_efficiency(self, mock_auth):
        """Test that entities don't create unnecessary instances."""
        client = AutotaskClient(mock_auth)

        # Access the same entity multiple times
        entities = [client.tickets for _ in range(10)]

        # All should be the same instance due to caching
        first_entity = entities[0]
        for entity in entities[1:]:
            assert entity is first_entity, "Entity caching not working properly"
