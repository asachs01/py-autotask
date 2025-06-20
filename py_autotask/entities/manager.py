"""
Entity manager for organizing and accessing different Autotask entities.

This module provides the EntityManager class that creates and manages
entity instances, providing both direct access and dynamic entity creation.
"""

import logging
from typing import TYPE_CHECKING, Dict, Any

from .base import BaseEntity
from .tickets import TicketsEntity
from .companies import CompaniesEntity
from .contacts import ContactsEntity
from .projects import ProjectsEntity
from .resources import ResourcesEntity
from .contracts import ContractsEntity

if TYPE_CHECKING:
    from ..client import AutotaskClient

logger = logging.getLogger(__name__)


class EntityManager:
    """
    Manager for all entity operations.
    
    Provides access to entity-specific handlers and can dynamically
    create handlers for entities not explicitly defined.
    """
    
    # Mapping of entity names to their specific handler classes
    ENTITY_CLASSES = {
        "Tickets": TicketsEntity,
        "Companies": CompaniesEntity,
        "Contacts": ContactsEntity,
        "Projects": ProjectsEntity,
        "Resources": ResourcesEntity,
        "Contracts": ContractsEntity,
    }
    
    def __init__(self, client: "AutotaskClient") -> None:
        """
        Initialize the entity manager.
        
        Args:
            client: The AutotaskClient instance
        """
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.EntityManager")
        self._entity_cache: Dict[str, BaseEntity] = {}
        
    def get_entity(self, entity_name: str) -> BaseEntity:
        """
        Get an entity handler, creating it if necessary.
        
        Args:
            entity_name: Name of the entity (e.g., 'Tickets', 'Companies')
            
        Returns:
            Entity handler instance
        """
        if entity_name not in self._entity_cache:
            # Check if we have a specific class for this entity
            entity_class = self.ENTITY_CLASSES.get(entity_name, BaseEntity)
            self._entity_cache[entity_name] = entity_class(self.client, entity_name)
            self.logger.debug(f"Created {entity_class.__name__} for {entity_name}")
            
        return self._entity_cache[entity_name]
    
    def __getattr__(self, name: str) -> BaseEntity:
        """
        Dynamically access entities as attributes.
        
        This allows for accessing entities like:
        manager.tickets, manager.companies, etc.
        
        Args:
            name: Entity name in lowercase
            
        Returns:
            Entity handler instance
        """
        # Convert attribute name to proper entity name
        entity_name = name.capitalize()
        
        # Handle special cases for entity naming
        if entity_name == "Companies":
            entity_name = "Companies"
        elif entity_name == "Tickets":
            entity_name = "Tickets"
        # Add more special cases as needed
        
        return self.get_entity(entity_name)
    
    # Direct properties for common entities (for better IDE support)
    @property
    def tickets(self) -> TicketsEntity:
        """Access to Tickets entity operations."""
        return self.get_entity("Tickets")
    
    @property
    def companies(self) -> CompaniesEntity:
        """Access to Companies entity operations."""
        return self.get_entity("Companies")
    
    @property
    def contacts(self) -> ContactsEntity:
        """Access to Contacts entity operations."""
        return self.get_entity("Contacts")
    
    @property
    def projects(self) -> ProjectsEntity:
        """Access to Projects entity operations."""
        return self.get_entity("Projects")
    
    @property
    def resources(self) -> ResourcesEntity:
        """Access to Resources entity operations."""
        return self.get_entity("Resources")
    
    @property
    def contracts(self) -> ContractsEntity:
        """Access to Contracts entity operations."""
        return self.get_entity("Contracts")
    
    def list_available_entities(self) -> list:
        """
        List all available entity types.
        
        Returns:
            List of entity names that have specific handlers
        """
        return list(self.ENTITY_CLASSES.keys()) 