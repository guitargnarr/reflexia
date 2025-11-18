#!/usr/bin/env python3
"""
rag_example.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

RAG (Retrieval-Augmented Generation) example using Reflexia Model Manager
"""

import os
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from model_manager import ModelManager
from rag_manager import RAGManager

def main():
    """Run a RAG example"""
    print("Reflexia Model Manager - RAG Example")
    print("-" * 50)
    
    # Initialize configuration
    config = Config()
    config.set("model", "name", "llama3:latest")
    config.set("model", "quantization", "q4_0")
    config.set("model", "context_length", 4096)
    
    # Create model and RAG managers
    print("Initializing managers...")
    model = ModelManager(config)
    rag = RAGManager(config, model)
    
    if not rag.is_available():
        print("Error: RAG is not available. Please install the required packages:")
        print("  pip install chromadb sentence-transformers")
        return
    
    # Check if a document was provided as an argument
    if len(sys.argv) > 1:
        document_path = sys.argv[1]
        print(f"Loading document: {document_path}")
        
        # Load the document
        success = rag.load_file(document_path)
        if not success:
            print(f"Error: Failed to load document {document_path}")
            return
            
        print("Document loaded successfully!")
    else:
        print("No document provided. Skipping document loading.")
        print("Pass a document path as an argument to load it:")
        print("  python rag_example.py path/to/document.pdf")
    
    # Interactive query loop
    print("\nEnter queries to get RAG-enhanced responses (type 'exit' to quit):")
    while True:
        query = input("\nQuery: ")
        if query.lower() in ['exit', 'quit']:
            break
            
        print("\nGenerating response...")
        result = rag.generate_rag_response(
            query_text=query,
            system_prompt="You are a helpful assistant that provides accurate information based on the provided context."
        )
        
        # Display response
        print("\nResponse:")
        print("-" * 50)
        print(result["response"])
        print("-" * 50)
        
        # Display sources if available
        if "sources" in result and result["sources"]:
            print("\nSources:")
            for source in result["sources"]:
                print(f"- {source}")
                
        # Show if context was used
        context_used = result.get("context_used", False)
        print(f"\nContext used: {context_used}")

if __name__ == "__main__":
    main()