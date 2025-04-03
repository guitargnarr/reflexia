#!/usr/bin/env python3
"""
Model Manager for Reflexia LLM implementation
Handles model loading, inference, and interaction with Ollama

Copyright (c) 2025 Matthew D. Scott. All Rights Reserved.
This file contains proprietary and confidential information.
Unauthorized copying, use, distribution, or modification is strictly prohibited.
Core adaptive quantization technology is patent-pending.
"""

import os
import json
import logging
import subprocess
import tempfile
import time
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("reflexia-tools.model")

class ModelManager:
    """Manager for the Reflexia model through Ollama"""
    
    def __init__(self, config):
        """Initialize the model manager"""
        from utils import get_env_var
        
        self.config = config
        # Use environment variables if available, otherwise fallback to config
        self.model_name = get_env_var("DEFAULT_MODEL", 
                                      config.get("model", "name", default="llama3:latest"))
        self.quantization = get_env_var("DEFAULT_QUANTIZATION", 
                                        config.get("model", "quantization", default="q4_0"))
        self.context_length = int(get_env_var("CONTEXT_LENGTH", 
                                            config.get("model", "context_length", default=4096)))
        self.batch_size = int(get_env_var("BATCH_SIZE", 
                                         config.get("model", "batch_size", default=8)))
        
        # Set up LRU cache size
        self.cache_size = config.get("memory", "lru_cache_size", default=64)
        
        # Ensure Ollama is using Metal acceleration
        if config.get("resources", "metal_optimized", default=True):
            os.environ["OLLAMA_METAL"] = "1"
        
        logger.info(f"Model manager initialized for {self.model_name}")
        
        # Check if model is available
        self._check_model_availability()
    
    def _check_model_availability(self):
        """Check if the model is available in Ollama"""
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if self.model_name in result.stdout:
                logger.info(f"Model {self.model_name} is available")
            else:
                logger.warning(f"Model {self.model_name} not found in Ollama")
                print(f"Warning: Model {self.model_name} not found in Ollama")
                print(f"You may need to pull it with: ollama pull {self.model_name}")
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            print(f"Error: Failed to check model availability: {e}")
            print("Please ensure Ollama is installed and running")
    
    def load_model(self):
        """Load the model into memory"""
        logger.info(f"Loading model {self.model_name}")
        
        try:
            # Run a simple inference to load the model
            self.generate_response("Hello", system_prompt="Test")
            logger.info(f"Model {self.model_name} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            print(f"Error: Failed to load model: {e}")
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_response(self, prompt, system_prompt=None, temperature=0.7, top_p=0.9):
        """Generate a response from the model with retry capability"""
        logger.debug(f"Generating response for prompt: {prompt[:50]}...")
        
        try:
            # Prepare command
            cmd = ["ollama", "run", self.model_name, "--format", "json"]
            
            # Prepare input data
            input_data = {
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "top_p": top_p,
                "context_length": self.context_length,
            }
            
            if system_prompt:
                input_data["system"] = system_prompt
            
            # Create a temporary file for input
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(input_data, f)
                input_file = f.name
            
            # Run ollama with input from file
            result = subprocess.run(
                cmd,
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse response
            try:
                response_data = json.loads(result.stdout)
                response = response_data.get('response', '')
                
                # Log metrics if available
                if 'eval_count' in response_data:
                    logger.debug(f"Eval count: {response_data['eval_count']}, " 
                                f"Eval duration: {response_data.get('eval_duration', 0)}")
                
                return response
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw output
                logger.warning("Failed to parse JSON response, returning raw output")
                return result.stdout
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error calling model: {e}")
            logger.error(f"Error output: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating response: {e}")
            raise
        finally:
            # Clean up temp file
            if 'input_file' in locals():
                try:
                    os.unlink(input_file)
                except:
                    pass
    
    @lru_cache(maxsize=None)  # Size will be set in __init__
    def cached_response(self, prompt, system_prompt=None, temperature=0.7, top_p=0.9):
        """Cached version of generate_response"""
        # Convert None to empty string for consistent caching
        system = system_prompt or ""
        return self.generate_response(prompt, system_prompt=system, temperature=temperature, top_p=top_p)
    
    def set_cache_size(self, size):
        """Update the LRU cache size"""
        # We need to recreate the cache with the new size
        self.cached_response.cache_clear()
        
        # Create a new cached function with updated size
        self.cached_response = lru_cache(maxsize=size)(self.generate_response)
        self.cache_size = size
        
        logger.info(f"Cache size updated to {size}")
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cached_response.cache_clear()
        logger.info("Response cache cleared")
    
    def create_embedding(self, text):
        """Create an embedding for the given text"""
        # This is a placeholder for embedding functionality
        # Ollama currently doesn't directly support embeddings via CLI
        # This would need to be implemented with a different library
        logger.warning("Embedding functionality not yet implemented")
        raise NotImplementedError("Embedding creation not implemented")
    
    # Add a new method to handle dynamic quantization
    def set_quantization(self, quantization_type):
        """Change the quantization method
        
        Args:
            quantization_type: Type of quantization to use
            
        Returns:
            bool: Success status
        """
        valid_quantizations = ["q4_0", "q4_k_m", "q5_k_m", "q8_0", "f16"]
        
        if quantization_type not in valid_quantizations:
            logger.error(f"Invalid quantization type: {quantization_type}")
            print(f"Invalid quantization type: {quantization_type}")
            print(f"Valid types: {', '.join(valid_quantizations)}")
            return False
        
        # Check if this requires changing the model
        if quantization_type != self.quantization:
            logger.info(f"Changing quantization from {self.quantization} to {quantization_type}")
            self.quantization = quantization_type
            
            # Create a new model name with the quantization parameter
            model_parts = self.model_name.split(':')
            base_model = model_parts[0]
            new_model_name = f"{base_model}:{self.quantization}"
            
            # Check if the model with this quantization exists
            try:
                result = subprocess.run(
                    ["ollama", "list"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                if new_model_name in result.stdout:
                    # Model with this quantization exists
                    self.model_name = new_model_name
                    logger.info(f"Using existing model with quantization: {new_model_name}")
                    return True
                else:
                    # Need to pull the model with this quantization
                    logger.info(f"Pulling model with quantization: {new_model_name}")
                    print(f"Pulling model with {quantization_type} quantization (this may take a while)...")
                    
                    # Run pull in a separate process
                    result = subprocess.run(
                        ["ollama", "pull", new_model_name],
                        check=True
                    )
                    
                    self.model_name = new_model_name
                    return True
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Error changing quantization: {e}")
                print(f"Error: Failed to change quantization: {e}")
                return False
        
        # Already using this quantization
        return True

    def adaptive_quantization(self, memory_manager):
        """Adaptively change quantization based on memory pressure
        
        Args:
            memory_manager: MemoryManager instance to monitor memory
            
        Returns:
            bool: True if quantization was changed
        """
        memory_stats = memory_manager.get_memory_stats()
        memory_percent = memory_stats.get("percent", 0)
        
        # Define thresholds for different quantization levels
        high_threshold = self.config.get("memory", "high_memory_threshold", default=85)
        
        # Current quantization level
        current_level = self.quantization
        
        # Check memory pressure and adjust quantization
        if memory_percent > high_threshold:
            # High memory pressure - use lower precision
            if current_level == "f16":
                return self.set_quantization("q8_0")
            elif current_level == "q8_0":
                return self.set_quantization("q5_k_m")
            elif current_level == "q5_k_m":
                return self.set_quantization("q4_k_m")
            elif current_level == "q4_k_m":
                return self.set_quantization("q4_0")
        elif memory_percent < 50 and current_level != "q8_0" and current_level != "f16":
            # Low memory pressure - can use higher precision if desired
            # This is optional and can be based on user preference
            return False  # Don't automatically increase quality, let user decide
        
        # No change needed
        return False

    def adaptive_quantization(self, memory_manager=None, content_complexity=None):
        """Adaptively change quantization based on memory pressure and content complexity
        
        Args:
            memory_manager: MemoryManager instance to monitor memory (optional)
            content_complexity: Estimated complexity of the content (0-1, optional)
            
        Returns:
            bool: True if quantization was changed
        """
        # Default quantization levels from lowest to highest quality
        quant_levels = ["q4_0", "q4_k_m", "q5_k_m", "q8_0", "f16"]
        
        # Get current level index
        current_index = quant_levels.index(self.quantization) if self.quantization in quant_levels else 0
        target_index = current_index
        
        # FACTOR 1: Memory pressure - prioritize memory efficiency under pressure
        if memory_manager:
            memory_stats = memory_manager.get_memory_stats()
            memory_percent = memory_stats.get("percent", 0)
            
            # Define thresholds for different memory pressure levels
            critical_threshold = self.config.get("memory", "critical_memory_threshold", default=90)
            high_threshold = self.config.get("memory", "high_memory_threshold", default=85)
            medium_threshold = self.config.get("memory", "medium_memory_threshold", default=75)
            low_threshold = self.config.get("memory", "low_memory_threshold", default=60)
            
            # Adjust based on memory pressure
            if memory_percent > critical_threshold:
                # Critical pressure - use lowest quality
                target_index = 0
                logger.warning(f"Critical memory pressure ({memory_percent}%), forcing lowest quantization")
            elif memory_percent > high_threshold:
                # High pressure - move down by up to 2 levels
                target_index = max(0, current_index - 2)
                logger.info(f"High memory pressure ({memory_percent}%), decreasing quantization by up to 2 levels")
            elif memory_percent > medium_threshold:
                # Medium pressure - move down by 1 level if not already at lowest
                target_index = max(0, current_index - 1)
                logger.info(f"Medium memory pressure ({memory_percent}%), decreasing quantization by 1 level")
            elif memory_percent < low_threshold and current_index < len(quant_levels) - 1:
                # Low pressure - consider moving up if user has enabled auto-quality improvement
                if self.config.get("model", "auto_improve_quality", default=False):
                    target_index = min(len(quant_levels) - 1, current_index + 1)
                    logger.info(f"Low memory pressure ({memory_percent}%), increasing quantization")
        
        # FACTOR 2: Content complexity - use higher quality for complex content
        if content_complexity is not None:
            # Adjust target based on complexity (0-1)
            complexity_adjustment = int(content_complexity * 2)  # 0-2 level adjustment
            
            # Only adjust up for complexity if memory permits
            if memory_manager and memory_manager.get_memory_stats().get("percent", 0) < 70:
                complexity_target = min(len(quant_levels) - 1, current_index + complexity_adjustment)
                # Take the higher of the memory-based target and complexity-based target
                target_index = max(target_index, complexity_target)
                logger.info(f"Content complexity {content_complexity}, adjusting quantization")
        
        # Apply change if needed
        if target_index != current_index:
            target_quant = quant_levels[target_index]
            logger.info(f"Changing quantization from {self.quantization} to {target_quant}")
            return self.set_quantization(target_quant)
        
        return False

    def estimate_content_complexity(self, text):
        """Estimate content complexity to guide quantization level
        
        Args:
            text: Text content to analyze
            
        Returns:
            float: Complexity score (0-1), higher means more complex
        """
        # Simple heuristic complexity estimation
        
        # 1. Length factor (longer texts tend to be more complex)
        length = len(text)
        length_factor = min(1.0, length / 10000)  # Cap at 10,000 chars
        
        # 2. Technical term factor
        technical_terms = [
            "algorithm", "function", "variable", "module", "tensor", 
            "derivative", "integral", "matrix", "vector", "quantum",
            "regression", "neural network", "transformer", "attention",
            "parameter", "coefficient", "theorem", "equation"
        ]
        
        term_count = sum(1 for term in technical_terms if term.lower() in text.lower())
        term_factor = min(1.0, term_count / 10)  # Cap at 10 terms
        
        # 3. Special characters factor (code, math, etc.)
        special_chars = sum(1 for char in text if char in "{}[]()<>+-*/\\=^;:")
        special_factor = min(1.0, special_chars / 100)  # Cap at 100 special chars
        
        # Calculate weighted score
        complexity = 0.4 * length_factor + 0.4 * term_factor + 0.2 * special_factor
        
        logger.debug(f"Content complexity: {complexity:.2f} (length: {length_factor:.2f}, terms: {term_factor:.2f}, special: {special_factor:.2f})")
        return complexity