#!/usr/bin/env python3
"""
Scan for corruption patterns in entity files.
"""
import os
import re

def scan_for_corruption():
    # Pattern to find the same corruption issues we've been seeing
    corruption_patterns = [
        r'from\s*\n\s*from\s+\.\.',  # Split from statements
        r'from\s+\.\.\s*from\s+\.\.',  # Double from statements
        r'datetime\.now\(\)\.isoformat\(\)\s*$',  # Orphaned datetime calls
        r'from\s+\.\.types\s+import\s+QueryFilter[^"\'\n]*$',  # Orphaned QueryFilter imports
        r'datetime\.fromisoformat\(\([^)]+\)\)',  # Double parentheses in datetime calls
        r'def\s+\w+\(\([^)]+\)\):',  # Double parentheses in function defs
    ]

    entity_files = []
    for root, dirs, files in os.walk('py_autotask/entities'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                entity_files.append(os.path.join(root, file))

    corrupted_files = []
    total_issues = 0

    for file_path in entity_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_issues = 0
            for pattern in corruption_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                file_issues += len(matches)
            
            if file_issues > 0:
                corrupted_files.append((file_path, file_issues))
                total_issues += file_issues
        except Exception as e:
            print(f'Error reading {file_path}: {e}')

    print(f'Found corruption in {len(corrupted_files)} files with {total_issues} total issues:')
    for file_path, count in sorted(corrupted_files, key=lambda x: x[1], reverse=True):
        print(f'  {file_path}: {count} issues')
    
    return corrupted_files

if __name__ == '__main__':
    scan_for_corruption()