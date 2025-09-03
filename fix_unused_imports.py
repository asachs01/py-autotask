#!/usr/bin/env python3
"""
Script to remove unused query_helpers imports from entity files.
"""

import os
import re
from pathlib import Path


def fix_unused_imports(file_path):
    """Remove unused query_helpers imports from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Remove the query_helpers import line entirely
    # Pattern matches: from .query_helpers import (...) across multiple lines
    content = re.sub(
        r"from \.query_helpers import \([^)]*\)\n",
        "",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Also handle single line imports
    content = re.sub(
        r"from \.query_helpers import [^\n]*\n", "", content, flags=re.MULTILINE
    )

    # Remove unused QueryFilter imports from ..types import (but keep others)
    # First, check if QueryFilter is actually used in the file
    if "QueryFilter" in content and not re.search(
        r"\bQueryFilter\b(?!.*import)", content
    ):
        # Remove QueryFilter from import lines
        content = re.sub(
            r"from \.\.types import ([^,\n]*,\s*)?QueryFilter(?:,\s*([^,\n]*))?\n",
            lambda m: (
                f"from ..types import {m.group(1) or ''}{m.group(2) or ''}".rstrip(", ")
                + "\n"
                if m.group(1) or m.group(2)
                else ""
            ),
            content,
        )

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    """Main function to process all entity files."""
    entity_dir = Path("py_autotask/entities")
    files_modified = 0

    for py_file in entity_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            if fix_unused_imports(py_file):
                print(f"Fixed imports in: {py_file}")
                files_modified += 1
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

    print(f"Modified {files_modified} files")


if __name__ == "__main__":
    main()
