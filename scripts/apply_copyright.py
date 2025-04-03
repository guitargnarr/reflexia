#!/usr/bin/env python3
"""
Script to apply copyright headers to all source files in the project.
"""
import os
import sys
from pathlib import Path

# Define the header for Python files
PYTHON_HEADER = '''#!/usr/bin/env python3
"""
{filename} - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""

'''

# Define the header for JavaScript/CSS files
JS_HEADER = '''/**
 * {filename} - Part of Reflexia Model Manager
 * 
 * Copyright (c) 2025 Matthew D. Scott
 * All rights reserved.
 * 
 * This source code is licensed under the Reflexia Model Manager License
 * found in the LICENSE file in the root directory of this source tree.
 * 
 * Unauthorized use, reproduction, or distribution is prohibited.
 */

'''

# Define file types to process
PYTHON_EXTENSIONS = ['.py']
JS_EXTENSIONS = ['.js', '.css']
HTML_EXTENSIONS = ['.html']

# Directories to ignore
IGNORE_DIRS = [
    '.git',
    '__pycache__',
    'venv',
    '.venv',
    'node_modules',
    'logs',
    'models',
    'cache',
    'vector_db',
    'uploads',
    'temp'
]

def should_ignore(path):
    """Check if path should be ignored"""
    for ignore_dir in IGNORE_DIRS:
        if ignore_dir in path.parts:
            return True
    return False

def apply_header_to_file(file_path, header_template):
    """Apply header to a single file"""
    filename = os.path.basename(file_path)
    header = header_template.format(filename=filename)
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check if file already has a copyright header
    if "Copyright (c)" in content[:500]:
        print(f"Skipping {file_path} - already has copyright header")
        return
    
    # For Python files, handle shebang line properly
    if file_path.suffix in PYTHON_EXTENSIONS and content.startswith('#!/'):
        lines = content.split('\n')
        shebang = lines[0]
        rest = '\n'.join(lines[1:])
        new_content = shebang + '\n"""' + header.split('"""')[1] + rest
    else:
        new_content = header + content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Applied header to {file_path}")

def apply_headers(directory):
    """Apply headers to all source files in directory"""
    directory = Path(directory)
    
    # Count files processed
    count = 0
    
    # Traverse all files recursively
    for root, dirs, files in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        root_path = Path(root)
        if should_ignore(root_path):
            continue
            
        for file in files:
            file_path = root_path / file
            
            # Apply appropriate header based on file extension
            if file_path.suffix in PYTHON_EXTENSIONS:
                apply_header_to_file(file_path, PYTHON_HEADER)
                count += 1
            elif file_path.suffix in JS_EXTENSIONS:
                apply_header_to_file(file_path, JS_HEADER)
                count += 1
    
    print(f"\nApplied headers to {count} files")

if __name__ == "__main__":
    # Use current directory or directory specified in command line
    directory = os.getcwd()
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    print(f"Applying copyright headers to files in {directory}")
    apply_headers(directory)