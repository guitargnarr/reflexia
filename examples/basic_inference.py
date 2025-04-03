#!/usr/bin/env python3
"""
basic_inference.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Basic inference example using Reflexia Model Manager
"""

import os
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from model_manager import ModelManager

def main():
    """Run a basic inference example"""
    print("Reflexia Model Manager - Basic Inference Example")
    print("-" * 50)
    
    # Initialize configuration
    config = Config()
    config.set("model", "name", "llama3:latest")
    config.set("model", "quantization", "q4_0")
    config.set("model", "context_length", 4096)
    
    # Create model manager
    print("Initializing model manager...")
    model = ModelManager(config)
    
    # Generate a response
    prompt = "Explain quantum computing in simple terms"
    print(f"\nPrompt: {prompt}")
    print("\nGenerating response...")
    
    response = model.generate_response(
        prompt=prompt,
        temperature=0.7,
        top_p=0.9
    )
    
    print("\nResponse:")
    print("-" * 50)
    print(response)
    print("-" * 50)

if __name__ == "__main__":
    main()