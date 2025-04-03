#!/usr/bin/env python3
"""
initialize_reflexia.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Complete initialization script for Reflexia RAG system
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, desc=None):
    """Run a command and print status"""
    if desc:
        print(f"{desc}...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ " + (desc or "Command completed successfully"))
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {desc or 'Command'} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False, e.stderr

def initialize_system():
    """Initialize the Reflexia RAG system"""
    print("\n=== Reflexia RAG System Initialization ===\n")
    
    # Try to use the new consolidated --initialize flag in main.py
    try:
        print("Running consolidated initialization...")
        run_command(["python", "main.py", "--initialize"], "Initializing system")
        print("\nInitialization through main.py complete!")
    except Exception as e:
        print(f"Error using main.py initialization: {e}")
        print("Falling back to individual fix scripts...")
        
        # Step 1: Fix the web_ui.py file
        run_command(["python", "fix_web_ui_thorough.py"], "Fixing Web UI")
        
        # Step 2: Fix the list_documents function
        run_command(["python", "fix_rag_helper.py"], "Fixing RAG helper")
        
        # Step 3: Add interactive mode
        run_command(["python", "add_interactive_mode.py"], "Adding interactive mode")
        
        # Step 4: Apply RAG fixes
        run_command(["python", "rag_helper.py", "fix"], "Applying RAG fixes")
        
        # Step 5: Check available documents
        run_command(["python", "rag_helper.py", "list"], "Checking documents")
    
    print("\n=== Initialization Complete ===\n")
    print("You can now run either:")
    print("  python main.py --interactive --rag  # For interactive mode with RAG")
    print("  python main.py --web                # For web UI")
    print("  python main.py --diagnose           # To run diagnostics")
    print("  python main.py --test-rag           # To test RAG functionality")
    
    # Ask which mode to start
    while True:
        choice = input("\nStart which mode? (interactive/web/diagnose/test-rag/none): ").strip().lower()
        if choice == "interactive":
            run_command(["python", "main.py", "--interactive", "--rag"], "Starting interactive mode with RAG")
            break
        elif choice == "web":
            run_command(["python", "main.py", "--web"], "Starting web UI")
            break
        elif choice == "diagnose":
            run_command(["python", "main.py", "--diagnose"], "Running diagnostics")
            break
        elif choice == "test-rag":
            run_command(["python", "main.py", "--test-rag"], "Testing RAG")
            break
        elif choice == "none":
            print("Exiting without starting any mode.")
            break
        else:
            print("Invalid choice. Please enter 'interactive', 'web', 'diagnose', 'test-rag', or 'none'.")

if __name__ == "__main__":
    initialize_system()
