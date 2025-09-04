#!/usr/bin/env python3
"""
Fix script to restore query_helpers imports where functions are still used.
"""

import re
from pathlib import Path

def needs_query_helpers(file_path):
    """Check if file uses query helper functions."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for usage of query helper functions
        helper_functions = [
            'build_active_filter', 'build_equality_filter', 'build_in_filter',
            'build_null_filter', 'build_search_filters', 'combine_filters'
        ]
        
        for func in helper_functions:
            if f'{func}(' in content:
                return True, helper_functions
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return False, []

def add_query_helpers_import(file_path):
    """Add query_helpers import to a file if needed."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Find where to insert the import (after other from . imports)
        insert_pos = None
        has_import = False
        
        for i, line in enumerate(lines):
            # Check if import already exists
            if 'from .query_helpers import' in line:
                has_import = True
                break
            
            # Find insertion point after from .base or from . imports
            if line.strip().startswith('from .') and 'base' in line:
                insert_pos = i + 1
        
        if has_import:
            return False  # Already has import
        
        if insert_pos is None:
            # No suitable insertion point found, add after typing imports
            for i, line in enumerate(lines):
                if line.strip().startswith('from typing'):
                    insert_pos = i + 1
                    break
        
        if insert_pos is None:
            print(f"Could not find insertion point for {file_path}")
            return False
        
        # Insert the import
        import_line = "from .query_helpers import (\n    build_active_filter,\n    build_equality_filter,\n    build_in_filter,\n    build_null_filter,\n    build_search_filters,\n    combine_filters,\n)\n"
        lines.insert(insert_pos, import_line)
        
        with open(file_path, 'w') as f:
            f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"Error modifying {file_path}: {e}")
        return False

def main():
    """Process all entity files that need query helpers."""
    entity_dir = Path('py_autotask/entities')
    fixed_files = []
    
    for py_file in entity_dir.glob('*.py'):
        if py_file.name in ['__init__.py', 'query_helpers.py']:
            continue
        
        needs_helpers, functions = needs_query_helpers(py_file)
        
        if needs_helpers:
            if add_query_helpers_import(py_file):
                fixed_files.append(str(py_file))
                print(f"Added query_helpers import to: {py_file}")
    
    print(f"Fixed {len(fixed_files)} files")
    print("Files modified:", fixed_files)

if __name__ == '__main__':
    main()