#!/usr/bin/env python3
"""
Script to fix corrupted import statements and syntax errors in the entities directory.
These were caused during the automatic import fixing process.
"""

import re
import os
from pathlib import Path

def fix_corrupted_imports(file_path):
    """Fix corrupted import statements and other syntax errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix orphaned imports scattered through the code
        content = re.sub(r'^from \.\.types import QueryFilter(?:\w+)*\n?', '', content, flags=re.MULTILINE)
        
        # Fix corrupted function parameters
        content = re.sub(r'from\nfrom \.\.types import QueryFilter[^\n]*', 'from_department_id: int,', content)
        
        # Fix corrupted docstring and comments
        content = re.sub(r'from\nfrom \.\.types import QueryFilter ([^"\n]+)', r'\1', content)
        content = re.sub(r'from \.\.types import QueryFilter ([^"\n]+)', r'\1', content)
        
        # Fix orphaned datetime.now().isoformat() statements
        content = re.sub(r'^\s+datetime\.now\(\)\.isoformat\(\)\s*\n?', '', content, flags=re.MULTILINE)
        
        # Fix corrupted f-strings and comments
        content = re.sub(r'(\s+)from\nfrom \.\.types import QueryFilter([^"]*?")', r'\1\2', content)
        
        # Fix corrupted dictionary values
        content = re.sub(r'"from\nfrom \.\.types import QueryFilter_department_id:', '"from_department_id":', content)
        content = re.sub(r'"from\nfrom \.\.types import QueryFilter_department": from\nfrom \.\.types import QueryFilter_department_id,', '"from_department": from_department_id,', content)
        
        # Remove duplicate imports at the top
        lines = content.split('\n')
        seen_imports = set()
        fixed_lines = []
        import_section = True
        
        for line in lines:
            if import_section:
                if line.strip() == '' or line.startswith('"""') or line.startswith('from ') or line.startswith('import '):
                    if line.startswith('from ..types import QueryFilter') or line.startswith('import '):
                        if line not in seen_imports:
                            seen_imports.add(line)
                            fixed_lines.append(line)
                        # Skip duplicate imports
                    else:
                        fixed_lines.append(line)
                else:
                    import_section = False
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Additional cleanup for specific patterns
        content = re.sub(r'from \.\.types import QueryFilter a company\.', 'for a company.', content)
        content = re.sub(r'from \.\.types import QueryFilter any existing primary team', 'any existing primary team', content)
        
        # Fix broken function definitions
        content = re.sub(r'def (\w+)_from\n', r'def \1_from_category(', content)
        content = re.sub(r'def (\w+)_from$', r'def \1_from_category(', content, flags=re.MULTILINE)
        
        # Fix broken datetime.from patterns  
        content = re.sub(r'datetime\.from\n', 'datetime.fromisoformat(', content)
        content = re.sub(r'datetime\.from$', 'datetime.fromisoformat(', content, flags=re.MULTILINE)
        
        # Fix broken multiline strings
        content = re.sub(r'(\s+)"([^"]*) from\n', r'\1"\2 from category', content)
        content = re.sub(r'"Consider redistributing resources from\n', '"Consider redistributing resources from other roles"', content)
        
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
    """Fix all corrupted files in the entities directory."""
    
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
            if fix_corrupted_imports(file_path):
                fixed_count += 1
        else:
            print(f"Warning: {file_path} not found")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()