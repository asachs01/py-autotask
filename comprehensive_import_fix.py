#!/usr/bin/env python3
import re
import os
from pathlib import Path

# Extract all specific error patterns from the CI log to be systematic
error_patterns = [
    (
        r"from \.\.types import ([^,\n]*,\s*)?QueryFilter(?:,\s*([^,\n]*))?\n",
        lambda m: (
            f"from ..types import {((m.group(1) or '') + (m.group(2) or '')).strip(', ')}\n"
            if (m.group(1) or m.group(2))
            else ""
        ),
    ),
    # Remove lines that import from query_helpers
    (r"from \.query_helpers import .*\n", ""),
]


def fix_file_imports(file_path):
    """Fix all unused imports in a file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        original = content

        for pattern, replacement in error_patterns:
            if callable(replacement):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Also remove QueryFilter if it's not used elsewhere in the code
        if "QueryFilter" in content:
            # Check if QueryFilter is used outside of import statements
            content_without_imports = re.sub(r"from.*import.*\n", "", content)
            if "QueryFilter" not in content_without_imports:
                # Remove QueryFilter from import statements
                content = re.sub(
                    r"from \.\.types import ([^,\n]*,\s*)?QueryFilter(?:,\s*([^,\n]*))?\n",
                    lambda m: (
                        f"from ..types import {((m.group(1) or '') + (m.group(2) or '')).strip(', ')}\n"
                        if (m.group(1) or m.group(2))
                        else ""
                    ),
                    content,
                )

        if content != original:
            with open(file_path, "w") as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False


def main():
    """Process all entity files."""
    entity_dir = Path("py_autotask/entities")
    fixed_files = []

    for py_file in entity_dir.glob("*.py"):
        if py_file.name in ["__init__.py", "query_helpers.py"]:
            continue

        if fix_file_imports(py_file):
            fixed_files.append(str(py_file))

    print(f"Fixed {len(fixed_files)} files:")
    for f in fixed_files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
