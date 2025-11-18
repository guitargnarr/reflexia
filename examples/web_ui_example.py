#!/usr/bin/env python3
"""
web_ui_example.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Web UI example using Reflexia Model Manager
"""

import os
import sys
import time

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from model_manager import ModelManager
from memory_manager import MemoryManager
from prompt_manager import PromptManager
from rag_manager import RAGManager
from web_ui import WebUI

def main():
    """Run a Web UI example"""
    print("Reflexia Model Manager - Web UI Example")
    print("-" * 50)
    
    # Initialize configuration
    config = Config()
    
    # Configure model
    config.set("model", "name", "reflexia-r1")
    config.set("model", "quantization", "q4_0")
    config.set("model", "context_length", 4096)
    
    # Configure web UI
    config.set("web_ui", "host", "127.0.0.1")
    config.set("web_ui", "port", 8000)
    
    # Create components
    print("Initializing components...")
    model_manager = ModelManager(config)
    memory_manager = MemoryManager(config, model_manager)
    prompt_manager = PromptManager(config)
    
    # Initialize RAG if possible
    try:
        import chromadb
        import sentence_transformers
        rag_manager = RAGManager(config, model_manager)
        print("RAG support enabled")
    except ImportError:
        print("Note: RAG support is not available. Install with: pip install chromadb sentence-transformers")
        rag_manager = None
    
    # Create Web UI
    try:
        # Try to import Flask and SocketIO
        import flask
        import flask_socketio
        
        web_ui = WebUI(
            config=config,
            model_manager=model_manager,
            memory_manager=memory_manager,
            prompt_manager=prompt_manager,
            rag_manager=rag_manager
        )
        
        # Start the Web UI
        print("\nStarting Web UI...")
        host = config.get("web_ui", "host", default="127.0.0.1")
        port = config.get("web_ui", "port", default=8000)
        
        print(f"Web UI will be available at: http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Start the UI in a separate thread
        web_ui.start(threaded=True)
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping Web UI...")
            
    except ImportError as e:
        print(f"Error: Web UI support is not available - {e}")
        print("Install with: pip install flask flask-socketio")
        return

if __name__ == "__main__":
    main()