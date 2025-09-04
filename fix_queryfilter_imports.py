#!/usr/bin/env python3
"""Fix QueryFilter import issues across all entity files."""

import os
import re
from pathlib import Path

def needs_queryfilter(content):
    """Check if file uses QueryFilter."""
    # Look for QueryFilter usage patterns
    patterns = [
        r'QueryFilter\s*\(',  # QueryFilter constructor
        r'filters:\s*List\[QueryFilter\]',  # Type hints
        r'filter:\s*QueryFilter',  # Type hints
        r'QueryFilter\[',  # Generic type
        r'QueryFilter\.',  # QueryFilter class methods
    ]
    return any(re.search(pattern, content) for pattern in patterns)

def has_queryfilter_import(content):
    """Check if file already imports QueryFilter."""
    return bool(re.search(r'from \.\.types import .*\bQueryFilter\b', content))

def add_queryfilter_import(content):
    """Add QueryFilter to existing types import or create new import."""
    # Check if there's already a types import
    types_import_match = re.search(r'^(from \.\.types import )(.+)$', content, re.MULTILINE)
    
    if types_import_match:
        # Add QueryFilter to existing import
        existing_imports = types_import_match.group(2)
        if 'QueryFilter' not in existing_imports:
            # Parse the imports and add QueryFilter in the right position
            imports = [imp.strip() for imp in existing_imports.split(',')]
            imports.append('QueryFilter')
            imports.sort()
            new_import_line = f"{types_import_match.group(1)}{', '.join(imports)}"
            content = content.replace(types_import_match.group(0), new_import_line)
    else:
        # Add new import line after other imports
        # Find the last import statement
        import_lines = re.findall(r'^(from|import) .+$', content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            # Add the new import after the last import
            content = content.replace(
                last_import,
                f"{last_import}\nfrom ..types import QueryFilter"
            )
        else:
            # No imports found, add at the beginning after docstring
            lines = content.split('\n')
            insert_pos = 0
            in_docstring = False
            for i, line in enumerate(lines):
                if line.strip().startswith('"""'):
                    if not in_docstring:
                        in_docstring = True
                    else:
                        insert_pos = i + 1
                        break
            lines.insert(insert_pos + 1, 'from ..types import QueryFilter')
            lines.insert(insert_pos + 1, '')
            content = '\n'.join(lines)
    
    return content

def remove_unused_queryfilter_import(content):
    """Remove QueryFilter from imports if not used."""
    if not needs_queryfilter(content) and has_queryfilter_import(content):
        # Remove QueryFilter from the import
        types_import_match = re.search(r'^(from \.\.types import )(.+)$', content, re.MULTILINE)
        if types_import_match:
            imports = [imp.strip() for imp in types_import_match.group(2).split(',')]
            imports = [imp for imp in imports if 'QueryFilter' not in imp]
            if imports:
                new_import_line = f"{types_import_match.group(1)}{', '.join(imports)}"
                content = content.replace(types_import_match.group(0), new_import_line)
            else:
                # Remove the entire import line if QueryFilter was the only import
                content = re.sub(r'^from \.\.types import QueryFilter\n', '', content, flags=re.MULTILINE)
    return content

def fix_file(file_path):
    """Fix QueryFilter imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Check if file needs QueryFilter
    if needs_queryfilter(content):
        if not has_queryfilter_import(content):
            print(f"  Adding QueryFilter import to {file_path.name}")
            content = add_queryfilter_import(content)
    else:
        # Remove unused QueryFilter import
        if has_queryfilter_import(content):
            print(f"  Removing unused QueryFilter import from {file_path.name}")
            content = remove_unused_queryfilter_import(content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix QueryFilter imports in all entity files."""
    entities_dir = Path('/home/asachs/Documents/wyre/projects/py-autotask/trees/fix-query-patterns/py_autotask/entities')
    
    # Files reported with F821 errors (undefined QueryFilter)
    files_needing_import = [
        'additional_invoice_field_values.py',
        'appointment_collections.py',
        'article_attachments.py',
        'article_configuration_item_category_associations.py',
        'article_contacts.py',
        'article_notes.py',
        'article_sections.py',
        'article_tags.py',
        'article_ticket_associations.py',
        'article_to_document_associations.py',
        'billing_codes.py',
        'billing_invoice_templates.py',
        'billing_item_approval_levels.py',
        'billing_milestones.py',
        'business_divisions.py',
        'business_locations.py',
        'business_subdivisions.py',
        'calendar_reminders.py',
        'check_list_items.py',
        'classification_icons.py',
        'client_portal_users.py',
        'company_locations.py',
        'company_teams.py',
        'configuration_items.py',
        'contact_webhooks.py',
        'contract_adjustments.py',
        'contract_billing_rules.py',
        'contract_rates.py',
        'contract_service_adjustments.py',
        'contracts.py',
        'cost_centers.py',
        'countries.py',
        'currencies.py',
        'departments.py',
        'document_attachments.py',
        'expense_categories.py',
        'expense_codes.py',
        'expense_items.py',
        'filtering_fields.py',
        'group_contracts.py',
        'holidays.py',
        'installed_products.py',
        'internal_location_with_business_hours.py',
        'invoice_line_items.py',
        'note_attachments.py',
        'notes.py',
        'opportunity_attachments.py',
        'payment_methods.py',
        'project_attachments.py',
        'project_charges.py',
        'project_costs.py',
        'purchase_order_items.py',
        'quote_attachments.py',
        'quote_locations.py',
        'resource_skill_levels.py',
        'resource_skills.py',
        'resource_time_off_balances.py',
        'resource_time_off_policies.py',
        'risk_assessment_results.py',
        'sales_order_attachments.py',
        'service_call_task_resources.py',
        'service_call_tickets.py',
        'service_level_agreement_results.py',
        'shipping_addresses.py',
        'shipping_types.py',
        'skill_categories.py',
        'surveys.py',
        'task_attachments.py',
        'task_predecessors.py',
        'tax_categories.py',
        'tax_codes.py',
        'tax_details.py',
        'tax_rates.py',
        'tax_regions.py',
        'ticket_webhooks.py',
        'time_entry_attachments.py',
        'user_defined_field_definitions.py',
        'user_defined_field_list_items.py',
        'user_defined_fields.py',
        'webhooks.py',
        'work_type_modifiers.py',
        'workflow_actions.py',
    ]
    
    # Files reported with F401 errors (unused QueryFilter import)  
    files_with_unused_import = [
        'action_types.py',
    ]
    
    print("Fixing QueryFilter import issues...")
    print("=" * 60)
    
    fixed_count = 0
    
    # Process all entity files
    for file_path in entities_dir.glob('*.py'):
        if file_path.name == '__init__.py' or file_path.name == 'base.py':
            continue
            
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    print("\nRunning Black formatter...")
    os.system('cd /home/asachs/Documents/wyre/projects/py-autotask/trees/fix-query-patterns && black py_autotask/entities/')
    
    print("\nDone!")

if __name__ == "__main__":
    main()