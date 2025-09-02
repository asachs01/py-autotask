#!/usr/bin/env python3
"""
Example demonstrating the use of constants and enums in py-autotask.

This example shows how the new constants module eliminates magic numbers
and provides clear, readable code when working with Autotask entities.
"""

from py_autotask.constants import (
    # Task constants
    TaskStatus,
    TaskPriority,
    TaskConstants,
    TaskDependencyType,
    
    # Ticket constants  
    TicketStatus,
    TicketPriority,
    TicketConstants,
    
    # Project constants
    ProjectStatus,
    ProjectType,
    ProjectConstants,
    
    # Contract constants
    ContractStatus,
    ContractType,
    ContractConstants,
    
    # Utility functions
    get_status_name,
    get_priority_description,
    validate_status_filter,
)


def demonstrate_task_constants():
    """Demonstrate task-related constants usage."""
    print("=" * 50)
    print("TASK CONSTANTS DEMONSTRATION")
    print("=" * 50)
    
    # Using enum values instead of magic numbers
    print(f"Task Status - New: {TaskStatus.NEW}")
    print(f"Task Status - In Progress: {TaskStatus.IN_PROGRESS}")
    print(f"Task Status - Complete: {TaskStatus.COMPLETE}")
    print()
    
    print(f"Task Priority - Critical: {TaskPriority.CRITICAL}")
    print(f"Task Priority - High: {TaskPriority.HIGH}")
    print(f"Task Priority - Medium: {TaskPriority.MEDIUM}")
    print(f"Task Priority - Low: {TaskPriority.LOW}")
    print()
    
    # Using status groupings
    print(f"Open Task Statuses: {TaskConstants.OPEN_STATUSES}")
    print(f"Closed Task Statuses: {TaskConstants.CLOSED_STATUSES}")
    print(f"Active Task Statuses: {TaskConstants.ACTIVE_STATUSES}")
    print()
    
    # Using validation constants
    print(f"Min Estimated Hours: {TaskConstants.MIN_ESTIMATED_HOURS}")
    print(f"Max Estimated Hours: {TaskConstants.MAX_ESTIMATED_HOURS}")
    print(f"Min Title Length: {TaskConstants.MIN_TITLE_LENGTH}")
    print(f"Max Title Length: {TaskConstants.MAX_TITLE_LENGTH}")
    print()
    
    # Dependency types
    print(f"Finish-to-Start Dependency: {TaskDependencyType.FINISH_TO_START}")
    print(f"Start-to-Start Dependency: {TaskDependencyType.START_TO_START}")
    print()


def demonstrate_ticket_constants():
    """Demonstrate ticket-related constants usage."""
    print("=" * 50)
    print("TICKET CONSTANTS DEMONSTRATION")
    print("=" * 50)
    
    # Ticket statuses
    print(f"Ticket Status - New: {TicketStatus.NEW}")
    print(f"Ticket Status - Assigned: {TicketStatus.ASSIGNED}")  
    print(f"Ticket Status - In Progress: {TicketStatus.IN_PROGRESS}")
    print(f"Ticket Status - Complete: {TicketStatus.COMPLETE}")
    print()
    
    # Status groupings
    print(f"Open Ticket Statuses: {TicketConstants.OPEN_STATUSES}")
    print(f"Closed Ticket Statuses: {TicketConstants.CLOSED_STATUSES}")
    print(f"Active Ticket Statuses: {TicketConstants.ACTIVE_STATUSES}")
    print(f"Waiting Ticket Statuses: {TicketConstants.WAITING_STATUSES}")
    print()
    
    # SLA mappings
    print("SLA Response Times (hours):")
    for priority, hours in TicketConstants.SLA_RESPONSE_TIMES.items():
        priority_name = get_status_name(TicketPriority, priority)
        print(f"  {priority_name}: {hours} hours")
    print()
    
    print("SLA Resolution Times (hours):")
    for priority, hours in TicketConstants.SLA_RESOLUTION_TIMES.items():
        priority_name = get_status_name(TicketPriority, priority)
        print(f"  {priority_name}: {hours} hours")
    print()


def demonstrate_utility_functions():
    """Demonstrate utility function usage."""
    print("=" * 50)
    print("UTILITY FUNCTIONS DEMONSTRATION")
    print("=" * 50)
    
    # Status name lookup
    print("Status Name Lookups:")
    print(f"  Task Status 2 = {get_status_name(TaskStatus, 2)}")
    print(f"  Task Status 5 = {get_status_name(TaskStatus, 5)}")
    print(f"  Ticket Status 1 = {get_status_name(TicketStatus, 1)}")
    print(f"  Ticket Status 8 = {get_status_name(TicketStatus, 8)}")
    print(f"  Invalid Status 999 = {get_status_name(TaskStatus, 999)}")
    print()
    
    # Priority descriptions
    print("Priority Descriptions:")
    for priority in [1, 2, 3, 4]:
        description = get_priority_description(priority)
        print(f"  Priority {priority}: {description}")
    print(f"  Invalid Priority 999: {get_priority_description(999)}")
    print()
    
    # Status filter validation
    print("Status Filter Validation:")
    try:
        task_open = validate_status_filter(TaskConstants, "open")
        print(f"  Task 'open' filter: {[status.value for status in task_open]}")
        
        task_completed = validate_status_filter(TaskConstants, "completed")
        print(f"  Task 'completed' filter: {[status.value for status in task_completed]}")
        
        ticket_active = validate_status_filter(TicketConstants, "active")
        print(f"  Ticket 'active' filter: {[status.value for status in ticket_active]}")
        
    except ValueError as e:
        print(f"  Validation Error: {e}")
    
    # Test invalid filter
    try:
        validate_status_filter(TaskConstants, "invalid_filter")
    except ValueError as e:
        print(f"  Expected Error: {e}")
    print()


def demonstrate_project_and_contract_constants():
    """Demonstrate project and contract constants."""
    print("=" * 50)
    print("PROJECT & CONTRACT CONSTANTS DEMONSTRATION")
    print("=" * 50)
    
    # Project constants
    print("Project Types:")
    for project_type in ProjectType:
        description = ProjectConstants.TYPE_DESCRIPTIONS.get(project_type, "Unknown")
        print(f"  {project_type.name} ({project_type.value}): {description}")
    print()
    
    print("Project Status Filters:")
    for filter_name, status_list in ProjectConstants.STATUS_FILTERS.items():
        print(f"  {filter_name}: {[status.value for status in status_list]}")
    print()
    
    # Contract constants
    print("Contract Types:")
    for contract_type in ContractType:
        print(f"  {contract_type.name}: {contract_type.value}")
    print()
    
    print("Contract Status Filters:")
    for filter_name, status_list in ContractConstants.STATUS_FILTERS.items():
        print(f"  {filter_name}: {[status.value for status in status_list]}")
    print()


def demonstrate_backwards_compatibility():
    """Demonstrate backwards compatibility with legacy constants."""
    print("=" * 50)
    print("BACKWARDS COMPATIBILITY DEMONSTRATION")
    print("=" * 50)
    
    # Import legacy constants
    from py_autotask.constants import (
        TASK_STATUS_NEW, TASK_STATUS_IN_PROGRESS, TASK_STATUS_COMPLETE,
        TASK_PRIORITY_CRITICAL, TASK_PRIORITY_HIGH, TASK_PRIORITY_MEDIUM, TASK_PRIORITY_LOW
    )
    
    print("Legacy constants still work:")
    print(f"  TASK_STATUS_NEW = {TASK_STATUS_NEW}")
    print(f"  TASK_STATUS_IN_PROGRESS = {TASK_STATUS_IN_PROGRESS}")
    print(f"  TASK_STATUS_COMPLETE = {TASK_STATUS_COMPLETE}")
    print()
    
    print(f"  TASK_PRIORITY_CRITICAL = {TASK_PRIORITY_CRITICAL}")
    print(f"  TASK_PRIORITY_HIGH = {TASK_PRIORITY_HIGH}")
    print(f"  TASK_PRIORITY_MEDIUM = {TASK_PRIORITY_MEDIUM}")
    print(f"  TASK_PRIORITY_LOW = {TASK_PRIORITY_LOW}")
    print()
    
    # Verify they match new constants
    print("Verification - Legacy matches new constants:")
    print(f"  TASK_STATUS_NEW == TaskStatus.NEW: {TASK_STATUS_NEW == TaskStatus.NEW}")
    print(f"  TASK_STATUS_COMPLETE == TaskStatus.COMPLETE: {TASK_STATUS_COMPLETE == TaskStatus.COMPLETE}")
    print(f"  TASK_PRIORITY_CRITICAL == TaskPriority.CRITICAL: {TASK_PRIORITY_CRITICAL == TaskPriority.CRITICAL}")
    print()


def demonstrate_code_improvements():
    """Show before/after code examples."""
    print("=" * 50)
    print("CODE IMPROVEMENT EXAMPLES")
    print("=" * 50)
    
    print("BEFORE (with magic numbers):")
    print("  # Hard to understand what status 2 means")
    print("  task_data = {'status': 2, 'priority': 1}")
    print("  if task['status'] == 5:")
    print("      print('Task completed')")
    print()
    
    print("AFTER (with constants):")
    print("  # Clear and self-documenting")
    print("  task_data = {")
    print("      'status': TaskStatus.IN_PROGRESS,")
    print("      'priority': TaskPriority.CRITICAL")
    print("  }")
    print("  if task['status'] == TaskStatus.COMPLETE:")
    print("      print('Task completed')")
    print()
    
    print("Status filtering improvements:")
    print("BEFORE:")
    print("  # Magic numbers are unclear")
    print("  open_statuses = [1, 2, 3]")
    print("  filters.append(QueryFilter('status', 'in', open_statuses))")
    print()
    
    print("AFTER:")
    print("  # Self-documenting and reusable")
    print("  open_statuses = TaskConstants.OPEN_STATUSES") 
    print("  filters.append(QueryFilter('status', 'in', open_statuses))")
    print("  # Or even better:")
    print("  status_ids = validate_status_filter(TaskConstants, 'open')")
    print("  filters.append(QueryFilter('status', 'in', status_ids))")
    print()


if __name__ == "__main__":
    print("py-autotask Constants and Enums Usage Examples")
    print("=" * 60)
    print()
    
    demonstrate_task_constants()
    print()
    
    demonstrate_ticket_constants()
    print()
    
    demonstrate_utility_functions()
    print()
    
    demonstrate_project_and_contract_constants()
    print()
    
    demonstrate_backwards_compatibility()
    print()
    
    demonstrate_code_improvements()
    print()
    
    print("=" * 60)
    print("All constants and enums are working correctly!")
    print("Magic numbers have been eliminated from the SDK!")
    print("=" * 60)