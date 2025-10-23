#!/usr/bin/env python3
"""Fix docstring syntax errors in Reflexia files"""

import re
from pathlib import Path

def fix_file(filepath):
    """Fix malformed docstrings in a Python file"""
    content = filepath.read_text()

    # Pattern: closing """ followed by text on next line, then another """
    pattern = r'(""")\n([A-Z][^\n]+)\n(""")'
    replacement = r'\1\n\n\2\n\3'

    fixed_content = re.sub(pattern, replacement, content)

    if fixed_content != content:
        filepath.write_text(fixed_content)
        print(f"✅ Fixed: {filepath.name}")
        return True
    return False

def main():
    project_root = Path(__file__).parent

    # Fix all Python files in root
    fixed_count = 0
    for pyfile in project_root.glob("*.py"):
        if pyfile.name != "fix_docstrings.py":
            if fix_file(pyfile):
                fixed_count += 1

    # Fix all Python files in tests/
    for pyfile in (project_root / "tests").glob("*.py"):
        if fix_file(pyfile):
            fixed_count += 1

    print(f"\n🎯 Total files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
