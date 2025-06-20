"""
Entity management for Autotask API.

This package provides entity-specific operations and managers for
interacting with different Autotask entities like Tickets, Companies, etc.
"""

from .manager import EntityManager
from .base import BaseEntity
from .tickets import TicketsEntity
from .companies import CompaniesEntity
from .contacts import ContactsEntity
from .projects import ProjectsEntity
from .resources import ResourcesEntity
from .contracts import ContractsEntity

__all__ = [
    "EntityManager", 
    "BaseEntity",
    "TicketsEntity",
    "CompaniesEntity", 
    "ContactsEntity",
    "ProjectsEntity",
    "ResourcesEntity",
    "ContractsEntity",
] 