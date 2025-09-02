"""
Constants and enums for the py-autotask SDK.

This module provides comprehensive constants for all Autotask entities,
replacing magic numbers throughout the SDK with readable, well-documented constants.

The constants are organized into categories:
- API Configuration Constants
- Common Status and Priority Constants  
- Entity-specific Constants (Tasks, Tickets, Projects, etc.)

All constants are aligned with the Autotask API documentation and provide
clear mapping between human-readable names and API values.
"""

from enum import IntEnum
from typing import Dict, List


# =============================================================================
# API Configuration Constants
# =============================================================================

class APILimits:
    """API limits and configuration constants."""
    
    MAX_QUERY_RESULTS = 500
    MAX_BATCH_SIZE = 200
    MAX_CONCURRENT_REQUESTS = 10
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2


class FieldLengths:
    """Maximum field lengths for entity fields."""
    
    TITLE_MAX = 255
    DESCRIPTION_MAX = 8000
    NAME_MAX = 100
    EMAIL_MAX = 254
    PHONE_MAX = 25
    ADDRESS_LINE_MAX = 128
    CITY_MAX = 50
    STATE_MAX = 25
    ZIP_CODE_MAX = 10
    COUNTRY_MAX = 100


# =============================================================================
# Common Priority Levels
# =============================================================================

class Priority(IntEnum):
    """Common priority levels used across multiple entities."""
    
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class PriorityMap:
    """Mapping priority names to descriptions."""
    
    DESCRIPTIONS = {
        Priority.CRITICAL: "Critical - Immediate attention required",
        Priority.HIGH: "High - Urgent resolution needed",
        Priority.MEDIUM: "Medium - Normal priority",
        Priority.LOW: "Low - Can be handled when time permits"
    }


# =============================================================================
# Task Constants
# =============================================================================

class TaskStatus(IntEnum):
    """Task status codes used in the Autotask API."""
    
    NEW = 1
    IN_PROGRESS = 2
    WAITING = 3
    CANCELLED = 4
    COMPLETE = 5


class TaskPriority(IntEnum):
    """Task priority levels."""
    
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskDependencyType:
    """Task dependency relationship types."""
    
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


class TaskConstants:
    """Consolidated task-related constants."""
    
    # Status mappings for common queries
    OPEN_STATUSES = [TaskStatus.NEW, TaskStatus.IN_PROGRESS, TaskStatus.WAITING]
    CLOSED_STATUSES = [TaskStatus.COMPLETE, TaskStatus.CANCELLED]
    ACTIVE_STATUSES = [TaskStatus.IN_PROGRESS]
    
    # Status filters for API queries
    STATUS_FILTERS = {
        "open": OPEN_STATUSES,
        "closed": CLOSED_STATUSES,
        "active": ACTIVE_STATUSES,
        "completed": [TaskStatus.COMPLETE],
        "in_progress": [TaskStatus.IN_PROGRESS],
        "waiting": [TaskStatus.WAITING],
        "new": [TaskStatus.NEW],
        "cancelled": [TaskStatus.CANCELLED]
    }
    
    # Validation limits
    MIN_ESTIMATED_HOURS = 0.01
    MAX_ESTIMATED_HOURS = 9999.99
    MIN_PERCENT_COMPLETE = 0
    MAX_PERCENT_COMPLETE = 100
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = FieldLengths.TITLE_MAX


# =============================================================================
# Ticket Constants  
# =============================================================================

class TicketStatus(IntEnum):
    """Ticket status codes used in the Autotask API."""
    
    NEW = 1
    ASSIGNED = 2
    IN_PROGRESS = 3
    WAITING_CUSTOMER = 4
    WAITING_MATERIALS = 5
    WAITING_VENDOR = 6
    ON_HOLD = 7
    COMPLETE = 8
    CANCELLED = 9
    ESCALATED = 10


class TicketType(IntEnum):
    """Ticket type categories."""
    
    INCIDENT = 1
    PROBLEM = 2
    CHANGE_REQUEST = 3
    SERVICE_REQUEST = 4
    MAINTENANCE = 5


class TicketPriority(IntEnum):
    """Ticket priority levels."""
    
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TicketConstants:
    """Consolidated ticket-related constants."""
    
    # Status groupings
    OPEN_STATUSES = [
        TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS,
        TicketStatus.WAITING_CUSTOMER, TicketStatus.WAITING_MATERIALS,
        TicketStatus.WAITING_VENDOR, TicketStatus.ON_HOLD, TicketStatus.ESCALATED
    ]
    CLOSED_STATUSES = [TicketStatus.COMPLETE, TicketStatus.CANCELLED]
    WAITING_STATUSES = [
        TicketStatus.WAITING_CUSTOMER, TicketStatus.WAITING_MATERIALS,
        TicketStatus.WAITING_VENDOR, TicketStatus.ON_HOLD
    ]
    ACTIVE_STATUSES = [TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]
    
    # Status filters for common queries
    STATUS_FILTERS = {
        "open": OPEN_STATUSES,
        "closed": CLOSED_STATUSES,
        "active": ACTIVE_STATUSES,
        "waiting": WAITING_STATUSES,
        "new": [TicketStatus.NEW],
        "in_progress": [TicketStatus.IN_PROGRESS],
        "complete": [TicketStatus.COMPLETE],
        "cancelled": [TicketStatus.CANCELLED]
    }
    
    # SLA response time mappings (hours)
    SLA_RESPONSE_TIMES = {
        TicketPriority.CRITICAL: 1,
        TicketPriority.HIGH: 4,
        TicketPriority.MEDIUM: 8,
        TicketPriority.LOW: 24
    }
    
    # SLA resolution time mappings (hours)
    SLA_RESOLUTION_TIMES = {
        TicketPriority.CRITICAL: 4,
        TicketPriority.HIGH: 24,
        TicketPriority.MEDIUM: 72,
        TicketPriority.LOW: 168
    }


# =============================================================================
# Project Constants
# =============================================================================

class ProjectStatus(IntEnum):
    """Project status codes."""
    
    NEW = 1
    IN_PROGRESS = 2
    ON_HOLD = 3
    CANCELLED = 4
    COMPLETE = 5


class ProjectType(IntEnum):
    """Project type categories."""
    
    FIXED_PRICE = 1
    TIME_AND_MATERIALS = 2
    RETAINER = 3
    RECURRING_SERVICE = 4
    MILESTONE = 5


class ProjectConstants:
    """Consolidated project-related constants."""
    
    # Status groupings
    ACTIVE_STATUSES = [ProjectStatus.IN_PROGRESS]
    OPEN_STATUSES = [ProjectStatus.NEW, ProjectStatus.IN_PROGRESS]
    CLOSED_STATUSES = [ProjectStatus.COMPLETE, ProjectStatus.CANCELLED]
    
    # Status filters
    STATUS_FILTERS = {
        "active": ACTIVE_STATUSES,
        "open": OPEN_STATUSES,
        "closed": CLOSED_STATUSES,
        "new": [ProjectStatus.NEW],
        "in_progress": [ProjectStatus.IN_PROGRESS],
        "on_hold": [ProjectStatus.ON_HOLD],
        "complete": [ProjectStatus.COMPLETE],
        "cancelled": [ProjectStatus.CANCELLED]
    }
    
    # Type descriptions
    TYPE_DESCRIPTIONS = {
        ProjectType.FIXED_PRICE: "Fixed Price Project",
        ProjectType.TIME_AND_MATERIALS: "Time and Materials Project",
        ProjectType.RETAINER: "Retainer-based Project", 
        ProjectType.RECURRING_SERVICE: "Recurring Service Project",
        ProjectType.MILESTONE: "Milestone-based Project"
    }


# =============================================================================
# Contract Constants
# =============================================================================

class ContractStatus(IntEnum):
    """Contract status codes."""
    
    DRAFT = 1
    ACTIVE = 2
    ON_HOLD = 3
    EXPIRED = 4
    CANCELLED = 5
    COMPLETE = 6


class ContractType(IntEnum):
    """Contract type categories."""
    
    RECURRING_SERVICE = 1
    BLOCK_HOURS = 2
    TIME_AND_MATERIALS = 3
    FIXED_PRICE = 4
    MAINTENANCE = 5


class ContractBillingType(IntEnum):
    """Contract billing frequency types."""
    
    MONTHLY = 1
    QUARTERLY = 2
    SEMI_ANNUALLY = 3
    ANNUALLY = 4
    ONE_TIME = 5


class ContractConstants:
    """Consolidated contract-related constants."""
    
    # Status groupings
    ACTIVE_STATUSES = [ContractStatus.ACTIVE]
    INACTIVE_STATUSES = [
        ContractStatus.DRAFT, ContractStatus.ON_HOLD, 
        ContractStatus.EXPIRED, ContractStatus.CANCELLED, ContractStatus.COMPLETE
    ]
    
    # Status filters
    STATUS_FILTERS = {
        "active": ACTIVE_STATUSES,
        "inactive": INACTIVE_STATUSES,
        "draft": [ContractStatus.DRAFT],
        "on_hold": [ContractStatus.ON_HOLD],
        "expired": [ContractStatus.EXPIRED],
        "cancelled": [ContractStatus.CANCELLED],
        "complete": [ContractStatus.COMPLETE]
    }


# =============================================================================
# Resource Constants
# =============================================================================

class ResourceStatus(IntEnum):
    """Resource/employee status codes."""
    
    ACTIVE = 1
    INACTIVE = 2
    TERMINATED = 3
    ON_LEAVE = 4


class ResourceType(IntEnum):
    """Resource type categories."""
    
    EMPLOYEE = 1
    CONTRACTOR = 2
    CONSULTANT = 3
    VENDOR = 4


class ResourceConstants:
    """Consolidated resource-related constants."""
    
    # Status filters
    STATUS_FILTERS = {
        "active": [ResourceStatus.ACTIVE],
        "inactive": [ResourceStatus.INACTIVE, ResourceStatus.TERMINATED],
        "available": [ResourceStatus.ACTIVE],
        "unavailable": [ResourceStatus.INACTIVE, ResourceStatus.TERMINATED, ResourceStatus.ON_LEAVE]
    }


# =============================================================================
# Account/Company Constants
# =============================================================================

class AccountStatus(IntEnum):
    """Account status codes."""
    
    ACTIVE = 1
    INACTIVE = 2
    PROSPECT = 3
    FORMER_CLIENT = 4


class AccountType(IntEnum):
    """Account type categories."""
    
    CUSTOMER = 1
    PROSPECT = 2
    PARTNER = 3
    VENDOR = 4
    LEAD = 5


# =============================================================================
# Expense Report Constants  
# =============================================================================

class ExpenseReportStatus(IntEnum):
    """Expense report status codes."""
    
    DRAFT = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4
    PAID = 5


class ExpenseReportConstants:
    """Consolidated expense report constants."""
    
    # Status filters
    STATUS_FILTERS = {
        "draft": [ExpenseReportStatus.DRAFT],
        "pending": [ExpenseReportStatus.SUBMITTED],
        "approved": [ExpenseReportStatus.APPROVED], 
        "rejected": [ExpenseReportStatus.REJECTED],
        "paid": [ExpenseReportStatus.PAID]
    }


# =============================================================================
# Time Entry Constants
# =============================================================================

class TimeEntryType(IntEnum):
    """Time entry type categories."""
    
    REGULAR = 1
    OVERTIME = 2
    DOUBLE_TIME = 3
    HOLIDAY = 4
    PTO = 5
    SICK = 6
    TRAINING = 7


class TimeEntryStatus(IntEnum):
    """Time entry status codes."""
    
    DRAFT = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4
    INVOICED = 5


# =============================================================================
# Opportunity Constants
# =============================================================================

class OpportunityStatus(IntEnum):
    """Opportunity status codes."""
    
    OPEN = 1
    WON = 2
    LOST = 3
    CANCELLED = 4


class OpportunityStage(IntEnum):
    """Opportunity sales stage."""
    
    LEAD = 1
    QUALIFIED = 2
    PROPOSAL = 3
    NEGOTIATION = 4
    CLOSING = 5


# =============================================================================
# Quote Constants
# =============================================================================

class QuoteStatus(IntEnum):
    """Quote status codes."""
    
    DRAFT = 1
    PENDING = 2
    ACCEPTED = 3
    REJECTED = 4
    EXPIRED = 5


# =============================================================================
# Invoice Constants
# =============================================================================

class InvoiceStatus(IntEnum):
    """Invoice status codes."""
    
    DRAFT = 1
    SENT = 2
    PAID = 3
    OVERDUE = 4
    CANCELLED = 5


# =============================================================================
# Utility Functions
# =============================================================================

def get_status_name(status_class, status_value: int) -> str:
    """
    Get the name of a status from its numeric value.
    
    Args:
        status_class: The status enum class (e.g., TaskStatus, TicketStatus)
        status_value: The numeric status value
        
    Returns:
        String name of the status, or "UNKNOWN" if not found
    """
    try:
        return status_class(status_value).name
    except ValueError:
        return "UNKNOWN"


def get_priority_description(priority_value: int) -> str:
    """
    Get a description for a priority level.
    
    Args:
        priority_value: The numeric priority value
        
    Returns:
        String description of the priority level
    """
    return PriorityMap.DESCRIPTIONS.get(priority_value, f"Unknown Priority ({priority_value})")


def validate_status_filter(entity_constants, filter_name: str) -> List[int]:
    """
    Validate and return status IDs for a given filter name.
    
    Args:
        entity_constants: The constants class for the entity (e.g., TaskConstants)
        filter_name: Name of the status filter
        
    Returns:
        List of status IDs for the filter
        
    Raises:
        ValueError: If filter_name is not valid for the entity
    """
    if not hasattr(entity_constants, 'STATUS_FILTERS'):
        raise ValueError(f"Entity constants class {entity_constants.__name__} does not support status filters")
    
    status_filters = entity_constants.STATUS_FILTERS
    if filter_name.lower() not in status_filters:
        valid_filters = list(status_filters.keys())
        raise ValueError(f"Invalid status filter '{filter_name}'. Valid options: {valid_filters}")
    
    return status_filters[filter_name.lower()]


# =============================================================================
# Legacy Compatibility Mappings
# =============================================================================

# For backwards compatibility, provide old-style constants
# These will be deprecated in a future version

# Task status (legacy)
TASK_STATUS_NEW = TaskStatus.NEW
TASK_STATUS_IN_PROGRESS = TaskStatus.IN_PROGRESS  
TASK_STATUS_WAITING = TaskStatus.WAITING
TASK_STATUS_CANCELLED = TaskStatus.CANCELLED
TASK_STATUS_COMPLETE = TaskStatus.COMPLETE

# Task priority (legacy)
TASK_PRIORITY_CRITICAL = TaskPriority.CRITICAL
TASK_PRIORITY_HIGH = TaskPriority.HIGH
TASK_PRIORITY_MEDIUM = TaskPriority.MEDIUM
TASK_PRIORITY_LOW = TaskPriority.LOW

# Ticket status (legacy)
TICKET_STATUS_NEW = TicketStatus.NEW
TICKET_STATUS_ASSIGNED = TicketStatus.ASSIGNED
TICKET_STATUS_IN_PROGRESS = TicketStatus.IN_PROGRESS
TICKET_STATUS_COMPLETE = TicketStatus.COMPLETE

# Project status (legacy)
PROJECT_STATUS_NEW = ProjectStatus.NEW
PROJECT_STATUS_IN_PROGRESS = ProjectStatus.IN_PROGRESS
PROJECT_STATUS_COMPLETE = ProjectStatus.COMPLETE

# Contract status (legacy)  
CONTRACT_STATUS_ACTIVE = ContractStatus.ACTIVE
CONTRACT_STATUS_EXPIRED = ContractStatus.EXPIRED


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # API Configuration
    'APILimits',
    'FieldLengths',
    
    # Common Enums
    'Priority',
    'PriorityMap',
    
    # Task Constants
    'TaskStatus',
    'TaskPriority', 
    'TaskDependencyType',
    'TaskConstants',
    
    # Ticket Constants
    'TicketStatus',
    'TicketType',
    'TicketPriority',
    'TicketConstants',
    
    # Project Constants
    'ProjectStatus',
    'ProjectType', 
    'ProjectConstants',
    
    # Contract Constants
    'ContractStatus',
    'ContractType',
    'ContractBillingType',
    'ContractConstants',
    
    # Resource Constants
    'ResourceStatus',
    'ResourceType',
    'ResourceConstants',
    
    # Account Constants
    'AccountStatus',
    'AccountType',
    
    # Expense Report Constants
    'ExpenseReportStatus',
    'ExpenseReportConstants',
    
    # Time Entry Constants
    'TimeEntryType',
    'TimeEntryStatus',
    
    # Opportunity Constants
    'OpportunityStatus',
    'OpportunityStage',
    
    # Quote Constants
    'QuoteStatus',
    
    # Invoice Constants
    'InvoiceStatus',
    
    # Utility Functions
    'get_status_name',
    'get_priority_description',
    'validate_status_filter',
]