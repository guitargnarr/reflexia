#!/usr/bin/env python3
"""
fix_rag_emergency.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Emergency fix for indentation error in rag_manager.py and rag_manager references in main.py
"""
import os
import shutil
import re
from pathlib import Path
import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fix_rag_emergency")

def fix_rag_emergency():
    """Fix critical indentation error in rag_manager.py and references in main.py"""
    print("Applying emergency fix to reflexia Model...")
    
    # Step 1: Fix rag_manager.py indentation
    fixed_indentation = fix_rag_indentation()
    
    # Step 2: Fix main.py references to rag_manager without self
    fixed_references = fix_rag_references()
    
    return fixed_indentation and fixed_references

def fix_rag_indentation():
    """Fix indentation issues in rag_manager.py"""
    print("Fixing indentation in rag_manager.py...")
    
    # Path to file
    file_path = Path("rag_manager.py")
    
    # Create a backup if it doesn't already exist
    backup_path = Path("rag_manager.py.emergency_bak")
    if not backup_path.exists() and file_path.exists():
        shutil.copy(file_path, backup_path)
        print(f"✅ Created backup at {backup_path}")
    
    try:
        # Read the file content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Use regex to find the problematic docstring and fix it
        pattern = r'def query\(self, query_text: str, collection_name: str = "documents", .*?\n\s*n_results: int = None, filter_criteria: Dict = None\) -> List\[Dict\]:\s*\n"""Query the vector database"""'
        replacement = r'def query(self, query_text: str, collection_name: str = "documents", \n             n_results: int = None, filter_criteria: Dict = None) -> List[Dict]:\n        """Query the vector database"""'
        
        # Apply the replacement
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the fixed content back
        if new_content != content:
            with open(file_path, "w") as f:
                f.write(new_content)
            print("✅ Fixed indentation in query method using regex")
        else:
            print("⚠️ No changes needed or regex didn't match")
            
            # Alternative direct line-by-line approach
            with open(file_path, "r") as f:
                lines = f.readlines()
            
            # Find the problematic query method
            query_line_idx = None
            for i, line in enumerate(lines):
                if "def query(self, query_text: str, collection_name: str =" in line:
                    query_line_idx = i
                    break
            
            if query_line_idx is None:
                print("❌ Could not find the query method")
                return False
            
            # Find the docstring line
            docstring_line_idx = None
            for i in range(query_line_idx + 1, min(query_line_idx + 5, len(lines))):
                if '"""Query the vector database"""' in lines[i]:
                    docstring_line_idx = i
                    break
            
            if docstring_line_idx is None:
                print("❌ Could not find the docstring")
                return False
            
            # Get indentation of the method signature
            method_indent = len(lines[query_line_idx]) - len(lines[query_line_idx].lstrip())
            # Body indentation should be method indent + 4 spaces
            body_indent = " " * (method_indent + 4)
            
            # Fix the docstring indentation
            current_docstring = lines[docstring_line_idx].strip()
            lines[docstring_line_idx] = body_indent + current_docstring + "\n"
            
            # Write the fixed content back
            with open(file_path, "w") as f:
                f.writelines(lines)
            
            print("✅ Fixed indentation in query method using line-by-line approach")
        
        # Verify the fix worked
        with open(file_path, "r") as f:
            verification = f.read()
            docstring_pos = verification.find('"""Query the vector database"""')
            prev_newline = verification.rfind('\n', 0, docstring_pos)
            space_count = docstring_pos - prev_newline - 1
            if space_count >= 4:
                print(f"✅ Verification passed: docstring has {space_count} spaces of indentation (expected >=4)")
                return True
            else:
                print(f"⚠️ Verification failed: docstring has {space_count} spaces of indentation (expected >=4)")
                return False
        
    except Exception as e:
        print(f"❌ Error fixing indentation: {e}")
        return False

def fix_rag_references():
    """Fix references to rag_manager without self prefix in main.py"""
    print("Fixing rag_manager references in main.py...")
    
    # Path to file
    file_path = Path("main.py")
    
    # Create a backup if it doesn't already exist
    backup_path = Path("main.py.rag_ref_bak")
    if not backup_path.exists() and file_path.exists():
        shutil.copy(file_path, backup_path)
        print(f"✅ Created backup at {backup_path}")
    
    try:
        # Read the file content
        with open(file_path, "r") as f:
            content = f.read()
        
        # Use regex to find and fix references to rag_manager without self prefix
        # Add self. prefix to rag_manager references not already prefixed
        pattern = r'(?<!\bself\.)(?<![-_a-zA-Z0-9])rag_manager\b(?!\.py)'
        replacement = r'self.rag_manager'
        
        # Apply the replacement
        new_content = re.sub(pattern, replacement, content)
        
        # Write the fixed content back
        if new_content != content:
            with open(file_path, "w") as f:
                f.write(new_content)
            print("✅ Fixed rag_manager references in main.py")
            return True
        else:
            print("✅ No rag_manager reference issues found in main.py")
            return True
        
    except Exception as e:
        print(f"❌ Error fixing rag_manager references: {e}")
        return False

def clean_redundant_files():
    """Clean up redundant fix scripts and backups"""
    print("Cleaning up redundant files...")
    
    # Files to keep
    essential_files = [
        "main.py", "rag_manager.py", "web_ui.py", "utils.py", "model_manager.py",
        "memory_manager.py", "prompt_manager.py", "run_reflexia.py", "README.md",
        "config.json", "requirements.txt", "fix_rag_emergency.py", "config.py",
        "rag_helper.py", "initialize_reflexia.py", "fix_port_conflict.py"
    ]
    
    # Directories to keep
    essential_dirs = [
        ".venv", "logs", "models", "cache", "vector_db", "web_ui", "vector_db_backup_final",
        "output", "uploads", "datasets"
    ]
    
    # Files to delete (specific fix scripts that are no longer needed)
    redundant_files = [
        "fix_rag_final.py", "fix_rag_consistency.py", "fix_rag_loader.py", 
        "fix_rag.py", "fix_rag_all.py", "fix_rag_complete.py",
        "fix_web_ui_final.py", "fix_web_ui_thorough.py", "fix_web_ui_thoroughly.py",
        "fix_web_ui_complete.py", "fix_web_ui_syntax.py", "fix_web_ui.py",
        "fix_rag_helper.py", "fix_rag_manager_direct.py", "fix_web_ui_direct.py",
        "create_fresh_main.py", "add_command_handler.py", "add_interactive_mode.py",
        "clean_main.py", "reset_main.py", "fix_interactive.py", "enhanced_interactive.py",
        "rag_debug.py", "rag_debug_fixed.py", "fix_all_indentation.py", "fix_host.py",
        "enhance_web_ui.py", "rag_manager_fix.py", "load_doc.py", "web_ui_excerpt.txt"
    ]
    
    deleted_count = 0
    
    # Clean up backup files except the most recent backup
    print("Cleaning up redundant backup files...")
    backup_files = []
    # Find all backup files
    for file in Path(".").glob("*.bak"):
        backup_files.append(file)
    for file in Path(".").glob("*.old"):
        backup_files.append(file)
    for file in Path(".").glob("*.orig"):
        backup_files.append(file)
    for file in Path(".").glob("*_backup"):
        backup_files.append(file)
    for file in Path(".").glob("*.original"):
        backup_files.append(file)
    for file in Path(".").glob("*.emergency_bak"):
        backup_files.append(file)
    
    # Keep only the most recent backup for each file
    kept_backups = set()
    for file in backup_files:
        base_name = file.stem.split(".")[0]  # Get the original file name
        
        # Skip if we already kept a backup for this file
        if base_name in kept_backups:
            try:
                file.unlink()
                print(f"✅ Deleted redundant backup: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete backup {file}: {e}")
        else:
            kept_backups.add(base_name)
            print(f"✅ Kept recent backup: {file}")
    
    # Delete redundant fix scripts
    for filename in redundant_files:
        file_path = Path(filename)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Deleted {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {filename}: {e}")
    
    print(f"✅ Cleaned up {deleted_count} redundant files")
    return True

if __name__ == "__main__":
    success = fix_rag_emergency()
    if success:
        print("Fix succeeded - now cleaning up redundant files...")
        clean_redundant_files()
    else:
        print("Fix failed") 
