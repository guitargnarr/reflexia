#!/usr/bin/env python3
"""
rag_helper.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Reflexia RAG Helper: Easy start, stop and document management for RAG
"""
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

def fix_rag():
    """Apply all RAG fixes in correct sequence"""
    print("Applying RAG fixes for Apple Silicon...")
    
    # 1. Fix the RAG manager
    try:
        # Run rag_manager_fix.py
        subprocess.run(["python", "rag_manager_fix.py"], check=True)
        
        # Run fix_rag_final.py to rebuild vector DB
        subprocess.run(["python", "fix_rag_final.py"], check=True)
        
        print("\n✅ RAG system ready! You can now run the model with RAG enabled.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error applying fixes: {e}")
        return False

def start_rag(interactive=True, web=False):
    """Start Reflexia model with RAG enabled"""
    try:
        cmd = ["python", "main.py"]
        
        if interactive:
            cmd.append("--interactive")
            cmd.append("--rag")
            print("Starting Reflexia in interactive mode with RAG...")
        
        if web:
            cmd.append("--web")
            print("Starting Reflexia web UI with RAG...")
        
        # Run the command
        process = subprocess.Popen(cmd)
        print(f"Reflexia RAG running (PID: {process.pid})")
        print("Press Ctrl+C to stop")
        
        # Return the process so it can be terminated later
        return process
    except Exception as e:
        print(f"❌ Error starting Reflexia: {e}")
        return None

def add_document(filepath):
    """Add a document to the RAG database"""
    try:
        if not Path(filepath).exists():
            print(f"❌ Document not found: {filepath}")
            return False
            
        # Copy file to project directory
        dest_path = Path(filepath).name
        shutil.copy(filepath, dest_path)
        print(f"✅ Document copied to project directory: {dest_path}")
        
        # Rebuild the database
        subprocess.run(["python", "fix_rag_final.py"], check=True)
        print(f"✅ Document added to RAG database: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error adding document: {e}")
        return False

def list_documents():
    """List documents in the RAG database"""
    try:
        import chromadb
        client = chromadb.PersistentClient(path="vector_db")
        
        # Get collection names (compatible with v0.6.0+)
        collections = client.list_collections()
        
        if not collections:
            print("❌ No collections found in the database")
            return False
        
        total_docs = 0
        for coll in collections:
            try:
                # Get the collection by name
                collection = client.get_collection(coll.name)
                
                # Get all documents and metadata from collection
                try:
                    results = collection.get(include=["documents", "metadatas", "embeddings"])
                    doc_count = len(results.get("ids", []))
                    
                    print(f"\nCollection '{coll.name}': {doc_count} documents")
                    
                    # Show document sources
                    for i, metadata in enumerate(results.get("metadatas", [])):
                        if metadata and "source" in metadata:
                            source = metadata["source"]
                            print(f"  {i+1}. {source}")
                        else:
                            print(f"  {i+1}. [Document without source]")
                        total_docs += 1
                        
                except Exception as e:
                    print(f"  Error retrieving documents: {e}")
                    
            except Exception as e:
                print(f"  Error accessing collection {coll.name}: {e}")
        
        if total_docs == 0:
            print("❌ No documents found in any collection")
        else:
            print(f"\n✅ Found {total_docs} total documents in {len(collections)} collections")
        return True
        
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        return False

def start_interactive():
    """Start Reflexia with interactive RAG mode only (no web dependencies)"""
    try:
        print("Starting Reflexia in interactive RAG mode...")
        
        # Start the interactive mode with RAG enabled
        cmd = ["python", "main.py", "--interactive", "--rag"]
        process = subprocess.Popen(cmd)
        
        print(f"✅ Interactive mode started (PID: {process.pid})")
        print("Type 'exit' to quit, or press Ctrl+C")
        
        return process
    except Exception as e:
        print(f"❌ Error starting interactive mode: {e}")
        return None

def start_web_ui():
    """Start Reflexia with Web UI and RAG enabled"""
    try:
        print("Starting Web UI with RAG enabled...")
        
        # First ensure the web UI files are properly set up
        subprocess.run(["python", "fix_web_ui.py"], check=True)
        
        # Start the web server with RAG enabled
        cmd = ["python", "main.py", "--web", "--rag"]
        process = subprocess.Popen(cmd)
        
        print(f"✅ Web UI started (PID: {process.pid})")
        print("💻 Access at: http://127.0.0.1:8000/")
        print("Press Ctrl+C to stop")
        
        return process
    except Exception as e:
        print(f"❌ Error starting Web UI: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Reflexia RAG Helper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Fix RAG system")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start Reflexia with RAG")
    start_parser.add_argument("--web", action="store_true", help="Start web UI instead of interactive mode")
    start_parser.add_argument("--no-interactive", action="store_true", help="Don't use interactive mode")
    
    # Add document command
    add_parser = subparsers.add_parser("add", help="Add document to RAG database")
    add_parser.add_argument("filepath", help="Path to document file")
    
    # List documents command
    list_parser = subparsers.add_parser("list", help="List documents in RAG database")
    
    # Web command
    web_parser = subparsers.add_parser("web", help="Start Reflexia with Web UI and RAG")
    
    args = parser.parse_args()
    
    if args.command == "fix":
        fix_rag()
    elif args.command == "start":
        interactive = not args.no_interactive
        start_rag(interactive=interactive, web=args.web)
    elif args.command == "add":
        add_document(args.filepath)
    elif args.command == "list":
        list_documents()
    elif args.command == "web":
        start_web_ui()
    elif args.command == "interactive":
        start_interactive()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()