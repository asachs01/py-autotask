#!/usr/bin/env python3
"""
Complete corruption fix for all entity files.
"""
import os
import re

def fix_all_corruption():
    """Fix all corruption patterns in all entity files."""
    
    # Get all entity files
    entity_files = []
    for root, dirs, files in os.walk('py_autotask/entities'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                entity_files.append(os.path.join(root, file))
    
    files_fixed = []
    total_fixes = 0
    
    for file_path in entity_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_this_file = 0
            
            # Fix 1: Split from statements like "from\nfrom ..types import QueryFilter_something"
            # This handles cases where import lines got corrupted
            pattern = r'from\s*\n\s*from\s+\.\.types\s+import\s+QueryFilter[^"\'\n]*'
            if re.search(pattern, content, re.MULTILINE):
                # Remove these corrupted import lines entirely
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                fixes_this_file += len(re.findall(pattern, original_content, re.MULTILINE))
            
            # Fix 2: Double from statements like "from ..from ..types import"
            pattern = r'from\s+\.\.\s*from\s+\.\.types\s+import\s+QueryFilter[^"\'\n]*'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                fixes_this_file += len(re.findall(pattern, original_content, re.MULTILINE))
            
            # Fix 3: Orphaned datetime.now().isoformat() calls
            pattern = r'^\s*datetime\.now\(\)\.isoformat\(\)\s*$'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                fixes_this_file += len(re.findall(pattern, original_content, re.MULTILINE))
            
            # Fix 4: Orphaned QueryFilter imports in the middle of code
            pattern = r'^\s*from\s+\.\.types\s+import\s+QueryFilter[^"\'\n]*$'
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                fixes_this_file += len(re.findall(pattern, original_content, re.MULTILINE))
            
            # Fix 5: Double parentheses in datetime.fromisoformat calls
            pattern = r'datetime\.fromisoformat\(\(([^)]+)\)\)'
            def fix_datetime(match):
                return f'datetime.fromisoformat({match.group(1)})'
            content = re.sub(pattern, fix_datetime, content)
            fixes_this_file += len(re.findall(pattern, original_content))
            
            # Fix 6: Double parentheses in function definitions
            pattern = r'def\s+(\w+)\(\(([^)]+)\)\):'
            def fix_function_def(match):
                return f'def {match.group(1)}({match.group(2)}):'
            content = re.sub(pattern, fix_function_def, content)
            fixes_this_file += len(re.findall(pattern, original_content))
            
            # Fix 7: Clean up multiple blank lines
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            
            # Fix 8: Remove any remaining orphaned lines with just "from" or partial imports
            content = re.sub(r'^\s*from\s*$', '', content, flags=re.MULTILINE)
            
            # Fix 9: Fix any malformed function parameters that got mangled
            # Look for patterns like "from_department_id: int," that should be parameters
            pattern = r'from\s*\n\s*from\s+\.\.types\s+import\s+QueryFilter([_\w]*)'
            def fix_parameter(match):
                param_name = match.group(1)
                if param_name.startswith('_'):
                    return param_name.lstrip('_') + ': int,'
                return ''
            content = re.sub(pattern, fix_parameter, content, flags=re.MULTILINE)
            
            # Only write if we made changes
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_fixed.append(file_path)
                total_fixes += fixes_this_file
                print(f'Fixed {fixes_this_file} issues in {file_path}')
                
        except Exception as e:
            print(f'Error processing {file_path}: {e}')
    
    print(f'\nSummary: Fixed {total_fixes} issues across {len(files_fixed)} files')
    return files_fixed, total_fixes

if __name__ == '__main__':
    fix_all_corruption()