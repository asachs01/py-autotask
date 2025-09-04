#!/usr/bin/env python3
"""Fix broken imports in entity files."""

import os
import re
from pathlib import Path

def fix_broken_file(file_path):
    """Fix a file with broken imports."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix patterns like "from\nfrom ..types import QueryFilter typing import..."
    # These got mangled when trying to add QueryFilter
    
    # Pattern 1: Fix "from\nfrom ..types import QueryFilter typing import"
    content = re.sub(
        r'from\nfrom \.\.types import QueryFilter typing import (.+)',
        r'from typing import \1\nfrom ..types import QueryFilter',
        content
    )
    
    # Pattern 2: Fix "from\nfrom ..types import QueryFilter .base import"
    content = re.sub(
        r'from\nfrom \.\.types import QueryFilter \.base import (.+)',
        r'from .base import \1\nfrom ..types import QueryFilter',
        content
    )
    
    # Pattern 3: Fix any other similar patterns
    content = re.sub(
        r'from\nfrom \.\.types import QueryFilter ([.\w]+) import (.+)',
        r'from \1 import \2\nfrom ..types import QueryFilter',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path.name}")

def main():
    """Fix all broken files."""
    entities_dir = Path('/home/asachs/Documents/wyre/projects/py-autotask/trees/fix-query-patterns/py_autotask/entities')
    
    # Files that failed to format
    broken_files = [
        'company_alerts.py',
        'company_attachments.py',
        'company_categories.py',
        'company_note_attachments.py',
        'company_notes.py',
        'company_teams.py',
        'company_to_dos.py',
        'company_site_configurations.py',
        'configuration_item_attachments.py',
        'configuration_item_billing_product_associations.py',
        'configuration_item_categories.py',
        'configuration_item_category_udf_associations.py',
        'configuration_item_note_attachments.py',
        'configuration_item_dns_records.py',
        'configuration_item_notes.py',
        'configuration_item_related_items.py',
        'configuration_item_ssl_subject_alternative_name.py',
        'resource_attachments.py',
        'resource_role_departments.py',
        'resource_role_queues.py',
        'resource_service_desk_roles.py',
        'user_defined_field_list_items.py',
    ]
    
    print("Fixing broken imports...")
    print("=" * 60)
    
    for filename in broken_files:
        file_path = entities_dir / filename
        if file_path.exists():
            fix_broken_file(file_path)
    
    print("\nRunning Black formatter...")
    os.system('cd /home/asachs/Documents/wyre/projects/py-autotask/trees/fix-query-patterns && black py_autotask/entities/')
    
    print("\nDone!")

if __name__ == "__main__":
    main()