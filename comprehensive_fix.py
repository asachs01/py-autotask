#!/usr/bin/env python3
"""
Comprehensive script to fix all syntax errors from the corrupted import fixing process.
"""

import re
import os
from pathlib import Path

def comprehensive_fix(file_path):
    """Apply comprehensive fixes to corrupted files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix broken function definitions
        content = re.sub(r'def (\w+)_from_category\(\(', r'def \1_from_category(', content)
        content = re.sub(r'def (\w+)_from\(', r'def \1_from_category(', content)
        
        # Fix broken datetime patterns with extra parentheses
        content = re.sub(r'datetime\.fromisoformat\(\(\s*([^)]+)\s*\)\s*', r'datetime.fromisoformat(\1)', content)
        
        # Fix broken dictionary keys
        content = re.sub(r'"from\n": from category,', '"from_resource": from_resource_id,', content)
        
        # Fix broken docstring lines
        content = re.sub(r'Remove category assignment from\n a company\.', 'Remove category assignment from a company.', content)
        content = re.sub(r'Remove a UDF association from\n a configuration item category\.', 'Remove a UDF association from a configuration item category.', content)
        
        # Fix broken multiline function calls - look for patterns where parentheses are broken across lines
        content = re.sub(r'(\w+\.fromisoformat)\(\(\s*\n\s*([^)]+)\s*\)\s*\n', r'\1(\2)', content)
        
        # Save if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {file_path}")
            return True
        else:
            print(f"No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all files."""
    
    entities_dir = Path("py_autotask/entities")
    
    files_to_fix = [
        "company_teams.py",
        "configuration_item_billing_product_associations.py", 
        "company_categories.py",
        "configuration_item_attachments.py",
        "configuration_item_category_udf_associations.py",
        "configuration_item_note_attachments.py",
        "configuration_item_ssl_subject_alternative_name.py",
        "resource_attachments.py",
        "company_notes.py",
        "resource_role_departments.py",
        "user_defined_field_list_items.py",
        "company_to_dos.py",
        "resource_service_desk_roles.py",
        "configuration_item_notes.py"
    ]
    
    fixed_count = 0
    
    for file_name in files_to_fix:
        file_path = entities_dir / file_name
        if file_path.exists():
            if comprehensive_fix(file_path):
                fixed_count += 1
        else:
            print(f"Warning: {file_path} not found")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()