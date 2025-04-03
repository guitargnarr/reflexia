#!/usr/bin/env python3
"""
example_usage.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Example usage of reflexia Local LLM Tools
"""

import os
import sys
import time
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
from config import Config
from model_manager import ModelManager
from memory_manager import MemoryManager
from prompt_manager import PromptManager
from utils import monitor_resources

def example_basic_interaction():
    """Example of basic interaction with the model"""
    print("\n=== Basic Interaction Example ===\n")
    
    # Create components
    config = Config()
    model = ModelManager(config)
    
    # Basic interaction
    prompts = [
        "What are the key principles of quantum physics?",
        "Write a haiku about artificial intelligence",
        "Explain the concept of recursion in programming"
    ]
    
    print("Generating responses to example prompts:\n")
    for prompt in prompts:
        print(f"Prompt: {prompt}")
        
        start_time = time.time()
        response = model.generate_response(prompt)
        elapsed = time.time() - start_time
        
        print(f"Response: {response}")
        print(f"Generated in {elapsed:.2f} seconds\n")
    
    print("Basic interaction example completed")

def example_caching():
    """Example of response caching"""
    print("\n=== Caching Example ===\n")
    
    # Create components
    config = Config()
    model = ModelManager(config)
    memory = MemoryManager(config)
    
    # Example prompt
    prompt = "Explain the theory of relativity in simple terms"
    
    print(f"First request (no cache) for: {prompt}")
    
    # First request (no cache)
    start_time = time.time()
    response = model.generate_response(prompt)
    first_time = time.time() - start_time
    
    print(f"Response: {response[:100]}...")
    print(f"Generated in {first_time:.2f} seconds")
    
    # Cache the response
    memory.cache_response(prompt, response)
    
    print("\nSecond request (cached):")
    
    # Second request (from cache)
    start_time = time.time()
    cached_response = memory.get_cached_response(prompt)
    second_time = time.time() - start_time
    
    print(f"Response: {cached_response[:100]}...")
    print(f"Retrieved in {second_time:.2f} seconds")
    
    # Compare times
    speedup = first_time / max(second_time, 0.001)  # Avoid division by zero
    print(f"\nCaching speedup: {speedup:.2f}x faster")
    
    print("\nCaching example completed")

def example_template_usage():
    """Example of using prompt templates"""
    print("\n=== Template Usage Example ===\n")
    
    # Create components
    config = Config()
    model = ModelManager(config)
    prompts = PromptManager(config)
    
    # Create a custom template
    custom_template = """You are a technical expert specializing in {topic}. 
    
User: {user_input}

Expert:"""
    
    prompts.add_template("technical", custom_template)
    
    # Create a custom system prompt
    prompts.set_system_prompt("Answer with detailed explanations and examples.")
    
    # Format a prompt using different templates
    user_question = "How do I optimize a deep learning model?"
    
    templates = ["default", "technical", "code"]
    
    for template_name in templates:
        if template_name == "technical":
            # Format with custom parameter for technical template
            formatted = custom_template.format(
                topic="machine learning",
                user_input=user_question
            )
        else:
            # Use standard formatting
            formatted = prompts.format_prompt(user_question, template_name)
        
        print(f"Template: {template_name}")
        print(f"Formatted Prompt: {formatted}")
        print("-" * 40)
    
    # Generate a response using a template
    print("\nGenerating response using 'code' template...")
    response = model.generate_response(
        prompts.format_prompt("Create a function to calculate Fibonacci numbers", "code")
    )
    
    print(f"Response: {response}")
    
    print("\nTemplate usage example completed")

def example_resource_monitoring():
    """Example of resource monitoring"""
    print("\n=== Resource Monitoring Example ===\n")
    
    # Create components
    config = Config()
    model = ModelManager(config)
    
    # Monitor baseline
    print("Baseline resource usage:")
    baseline = monitor_resources()
    print(f"CPU: {baseline['cpu_percent']}%")
    print(f"Memory: {baseline['memory']['percent']}% ({baseline['memory']['used_gb']:.2f} GB)")
    
    # Run a demanding prompt
    print("\nRunning a demanding prompt...")
    prompt = """Write a detailed essay on the history of artificial intelligence, 
    including major milestones, key figures, and the evolution of machine learning techniques 
    from the 1950s to the present day."""
    
    response = model.generate_response(prompt)
    
    # Monitor after generation
    print("\nResource usage after generation:")
    after = monitor_resources()
    print(f"CPU: {after['cpu_percent']}%")
    print(f"Memory: {after['memory']['percent']}% ({after['memory']['used_gb']:.2f} GB)")
    
    # Compare
    print("\nResource impact:")
    print(f"CPU impact: {after['cpu_percent'] - baseline['cpu_percent']:.1f}% increase")
    print(f"Memory impact: {after['memory']['percent'] - baseline['memory']['percent']:.1f}% increase")
    
    print("\nResource monitoring example completed")

def main():
    """Main function to run examples"""
    print("reflexia Local LLM Tools - Usage Examples")
    
    # Create output directory for example results
    examples_dir = Path("examples/results")
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    # Run examples
    try:
        example_basic_interaction()
        example_caching()
        example_template_usage()
        example_resource_monitoring()
        
        print("\nAll examples completed successfully!")
    except Exception as e:
        print(f"\nError running examples: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())