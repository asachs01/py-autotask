#!/usr/bin/env python3
import re
import sys

# Fix contracts.py
with open('py_autotask/entities/contracts.py', 'r') as f:
    content = f.read()

# Remove unused Union import
content = re.sub(r'from typing import Any, Dict, List, Optional, Union', 
                'from typing import Any, Dict, List, Optional', content)

# Fix unused variable assignments
content = re.sub(r'(\s+)updated_contract = self\.update\(', r'\1self.update(', content)

# Fix bare except clauses
content = re.sub(r'(\s+)except:\n', r'\1except Exception:\n', content)

# Fix unused variable 'e'
content = re.sub(r'except Exception as e:\n(\s+)# Log error if needed\n(\s+)pass', 
                r'except Exception:\n\1# Log error if needed\n\2pass', content)

with open('py_autotask/entities/contracts.py', 'w') as f:
    f.write(content)

print("Fixed contracts.py")

# Fix projects.py
with open('py_autotask/entities/projects.py', 'r') as f:
    content = f.read()

# Fix bare except clauses
content = re.sub(r'(\s+)except:\n', r'\1except Exception:\n', content)

# Fix unused variables
content = re.sub(r'(\s+)activity_data = {[^}]+}\n', '', content)
content = re.sub(r'(\s+)phase_data = {[^}]+}\n', '', content)
content = re.sub(r'(\s+)dep_filters = \[', r'\1# dep_filters = [', content)

# Fix undefined 'i' - looks like a typo, should be iteration variable
content = re.sub(r'for i in range\(len\(tasks\)\)', r'for idx in range(len(tasks))', content)
content = re.sub(r'tasks\[i\]', r'tasks[idx]', content)

# Fix unused 'e' variable
content = re.sub(r'except Exception as e:\n(\s+)pass', r'except Exception:\n\1pass', content)

with open('py_autotask/entities/projects.py', 'w') as f:
    f.write(content)

print("Fixed projects.py")

# Fix resources.py
with open('py_autotask/entities/resources.py', 'r') as f:
    content = f.read()

# Fix unused variable 'deadline'
content = re.sub(r'(\s+)deadline = datetime\.now\(\)[^\n]+\n', '', content)

# Fix ambiguous variable name 'l' - change to 'level'
content = re.sub(r'\bl\b(?=\s*in\s+range)', 'level', content)
content = re.sub(r'\[l\]', '[level]', content)

# Fix unused 'e' variable
content = re.sub(r'except Exception as e:\n(\s+)pass', r'except Exception:\n\1pass', content)

with open('py_autotask/entities/resources.py', 'w') as f:
    f.write(content)

print("Fixed resources.py")

# Fix test_resources_enhanced.py
with open('tests/test_resources_enhanced.py', 'r') as f:
    content = f.read()

# Remove unused imports
content = re.sub(r'import json\n', '', content)
content = re.sub(r'from unittest\.mock import MagicMock, Mock, patch\n', 
                'from unittest.mock import Mock, patch\n', content)
content = re.sub(r'from py_autotask\.types import QueryFilter, QueryRequest\n',
                'from py_autotask.types import QueryRequest\n', content)

# Fix unused variables
content = re.sub(r'(\s+)mock_util = [^\n]+\n', '', content)
content = re.sub(r'(\s+)mock_entries = [^\n]+\n', '', content)

with open('tests/test_resources_enhanced.py', 'w') as f:
    f.write(content)

print("Fixed test_resources_enhanced.py")
