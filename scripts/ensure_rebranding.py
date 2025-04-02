#!/usr/bin/env python3
"""
Script to ensure all DeepSeek references are properly renamed to Reflexia across the codebase.
This script scans all relevant files and reports any remaining occurrences of DeepSeek.
"""
import os
import re
import sys
from pathlib import Path
import argparse
import fnmatch

# ANSI color codes for highlighting
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color

# Search patterns - case insensitive
PATTERNS = [
    'deepseek', 
    'deep seek',
    'DeepSeek',
    'Deep Seek',
    'DEEPSEEK',
    'DEEP SEEK'
]

# File extensions to check
FILE_EXTENSIONS = [
    '.py', '.js', '.html', '.css', '.md', '.json', '.yaml', '.yml', 
    '.txt', '.sh', '.bash', '.dockerfile', '.makefile', '.toml'
]

# Directories to exclude
EXCLUDE_DIRS = [
    '.git', '__pycache__', 'venv', '.venv', 'node_modules', 'logs/legacy_deepseek_logs',
    'logs', 'models', 'cache', 'vector_db', 'uploads', 'temp'
]

# Files to exclude
EXCLUDE_FILES = [
    'scripts/ensure_rebranding.py',  # This file
    'CHANGELOG.md',  # May contain historical references
    '*.bak',  # Backup files
    '*.log',  # Log files
    '*.log.*',  # Log rotation files
]

def should_check_file(file_path):
    """Determine if a file should be checked based on exclusion rules"""
    # Check if file extension is in the list to check
    if not any(file_path.endswith(ext) for ext in FILE_EXTENSIONS):
        return False
    
    # Check if file matches any exclude pattern
    rel_path = os.path.relpath(file_path)
    for pattern in EXCLUDE_FILES:
        if fnmatch.fnmatch(rel_path, pattern):
            return False
    
    return True

def find_deepseek_references(file_path):
    """Find DeepSeek references in a file"""
    references = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
            # Search for each pattern
            for pattern in PATTERNS:
                # Case insensitive search
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    # Get line number and context
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Get the line containing the match
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.start())
                    if line_end == -1:  # Handle last line
                        line_end = len(content)
                        
                    line_content = content[line_start:line_end]
                    
                    # Highlight the match in the line
                    match_in_line = match.group()
                    highlighted_line = line_content.replace(
                        match_in_line, 
                        f"{RED}{match_in_line}{NC}"
                    )
                    
                    references.append((line_num, match.group(), highlighted_line))
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return references

def scan_directory(directory, recursive=True):
    """Scan directory for DeepSeek references"""
    directory_path = Path(directory)
    total_files = 0
    files_with_references = 0
    total_references = 0
    
    print(f"{BLUE}Scanning directory: {directory_path.absolute()}{NC}")
    
    # Walk through the directory
    for root, dirs, files in os.walk(directory_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if should_check_file(file_path):
                total_files += 1
                
                # Find references
                references = find_deepseek_references(file_path)
                
                if references:
                    files_with_references += 1
                    total_references += len(references)
                    
                    # Print file path with references
                    print(f"\n{YELLOW}Found {len(references)} references in {file_path}:{NC}")
                    
                    # Print each reference
                    for line_num, match, highlighted_line in references:
                        print(f"  Line {line_num}: {highlighted_line}")
        
        # Stop recursion if not recursive
        if not recursive:
            break
    
    # Print summary
    print(f"\n{BLUE}Scan Complete{NC}")
    print(f"Files checked: {total_files}")
    print(f"Files with DeepSeek references: {files_with_references}")
    print(f"Total references found: {total_references}")
    
    if total_references == 0:
        print(f"{GREEN}✓ All files have been properly rebranded to Reflexia!{NC}")
    else:
        print(f"{RED}✗ Found {total_references} remaining DeepSeek references that need to be updated to Reflexia.{NC}")
    
    return total_references

def fix_deepseek_references(file_path, dry_run=True):
    """Fix DeepSeek references in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Create a copy of the original content
        new_content = content
        
        # Replacement mapping
        replacements = {
            'deepseek': 'reflexia',
            'Deepseek': 'Reflexia',
            'DeepSeek': 'Reflexia',
            'DEEPSEEK': 'REFLEXIA',
            'deep seek': 'reflexia',
            'Deep Seek': 'Reflexia',
            'DEEP SEEK': 'REFLEXIA'
        }
        
        # Apply replacements
        for old, new in replacements.items():
            new_content = re.sub(re.escape(old), new, new_content, flags=re.IGNORECASE)
        
        # Check if content was modified
        if new_content != content:
            if dry_run:
                print(f"{YELLOW}Would fix references in: {file_path}{NC}")
                return True
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"{GREEN}Fixed references in: {file_path}{NC}")
                return True
        
        return False
    
    except Exception as e:
        print(f"{RED}Error fixing {file_path}: {e}{NC}")
        return False

def fix_all_references(directory, recursive=True, dry_run=True):
    """Fix all DeepSeek references in directory"""
    directory_path = Path(directory)
    total_files_fixed = 0
    
    print(f"{BLUE}{'Analyzing' if dry_run else 'Fixing'} references in: {directory_path.absolute()}{NC}")
    
    # Walk through the directory
    for root, dirs, files in os.walk(directory_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if should_check_file(file_path):
                # Fix references
                if fix_deepseek_references(file_path, dry_run):
                    total_files_fixed += 1
        
        # Stop recursion if not recursive
        if not recursive:
            break
    
    # Print summary
    print(f"\n{BLUE}Operation Complete{NC}")
    if dry_run:
        print(f"Would fix references in {total_files_fixed} files")
    else:
        print(f"Fixed references in {total_files_fixed} files")
    
    return total_files_fixed

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Find and optionally fix DeepSeek references in codebase"
    )
    parser.add_argument(
        "--fix", action="store_true", 
        help="Fix DeepSeek references (default: scan only)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", 
        help="Show what would be fixed without making changes"
    )
    parser.add_argument(
        "--directory", type=str, default=".", 
        help="Directory to scan (default: current directory)"
    )
    parser.add_argument(
        "--no-recursive", action="store_true", 
        help="Don't scan subdirectories"
    )
    
    args = parser.parse_args()
    
    # Set working directory
    os.chdir(args.directory)
    
    # Determine action
    if args.fix:
        fix_all_references(".", not args.no_recursive, args.dry_run)
    else:
        num_references = scan_directory(".", not args.no_recursive)
        # Return non-zero exit code if references found
        if num_references > 0:
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())