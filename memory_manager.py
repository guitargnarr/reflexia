#!/usr/bin/env python3
"""
memory_manager.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Memory Manager for Reflexia LLM implementation
Handles memory usage, caching, and resource monitoring
"""
import os
import sys
import time
import psutil
import logging
import gc
from pathlib import Path
from collections import OrderedDict
from functools import lru_cache

logger = logging.getLogger("reflexia-tools.memory")

class MemoryManager:
    """Manager for memory usage and caching"""
    
    def __init__(self, config, model_manager=None):
        """Initialize the memory manager
        
        Args:
            config: Configuration object
            model_manager: ModelManager instance (optional)
        """
        self.config = config
        self.model_manager = model_manager
        
        # Configure memory thresholds
        self.max_memory_percent = config.get("memory", "max_memory_percent", default=80)
        self.critical_memory_percent = config.get("memory", "critical_memory_percent", default=90)
        
        # Initialize response cache
        cache_size = config.get("memory", "response_cache_size", default=100)
        self.response_cache = lru_cache(maxsize=cache_size)(lambda x: x)
        
        logger.info(f"Memory manager initialized (max: {self.max_memory_percent}%, critical: {self.critical_memory_percent}%)")
    
    def get_memory_stats(self):
        """Get current memory usage statistics
        
        Returns:
            dict: Memory usage statistics
        """
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "free": memory.free,
            "percent": memory.percent,
            "critical": memory.percent >= self.critical_memory_percent
        }
    
    def cache_response(self, prompt, response):
        """Cache a response
        
        Args:
            prompt: Prompt string
            response: Response string
            
        Returns:
            None
        """
        # Skip caching if memory pressure is high
        if self.get_memory_stats()["percent"] > self.max_memory_percent:
            return None
        
        # Hash the prompt since it might be long
        prompt_hash = hash(prompt)
        self.response_cache(prompt_hash)
        return None
    
    def get_cached_response(self, prompt):
        """Get a cached response if available
        
        Args:
            prompt: Prompt string
            
        Returns:
            str or None: Cached response or None if not found
        """
        prompt_hash = hash(prompt)
        # This is a simple implementation - in a real system, you'd fetch from cache
        return None  # Currently just a placeholder
    
    def reduce_memory_pressure(self):
        """Attempt to reduce memory pressure
        
        Returns:
            bool: Success status
        """
        logger.info("Reducing memory pressure")
        
        # Run garbage collection
        gc.collect()
        
        # If model_manager was passed, we can call its methods
        if self.model_manager:
            # This would require implementation in model_manager
            if hasattr(self.model_manager, 'clear_cache'):
                self.model_manager.clear_cache()
        
        return True
        
    def adaptive_chunk_size(self, text_length, base_chunk_size=1000):
        """Adaptively determine chunk size based on text length and available memory
        
        Args:
            text_length: Length of text to chunk
            base_chunk_size: Default chunk size
            
        Returns:
            int: Recommended chunk size
        """
        # Check current memory usage
        memory_stats = self.get_memory_stats()
        memory_usage = memory_stats["percent"]
        
        # Base calculation - reduce chunk size when memory pressure is high
        if memory_usage > self.critical_memory_percent:
            # Critical memory pressure - use smallest chunks
            return max(200, base_chunk_size // 5)
        elif memory_usage > self.max_memory_percent:
            # High memory pressure - reduce chunk size
            return max(500, base_chunk_size // 2)
        
        # Adapt based on text length
        if text_length > 1000000:  # Very large text (>1MB)
            return min(base_chunk_size, 800)  # Smaller chunks for very large texts
        elif text_length > 100000:  # Large text
            return base_chunk_size
        
        # For smaller texts, can use larger chunks if memory allows
        if memory_usage < 50:
            return min(2000, base_chunk_size * 2)
            
        return base_chunk_size
        
    def should_use_quantization(self):
        """Determine if model should use more aggressive quantization
        
        Returns:
            bool: True if more aggressive quantization is recommended
        """
        memory_stats = self.get_memory_stats()
        
        # If memory usage is high, recommend more aggressive quantization
        return memory_stats["percent"] > self.max_memory_percent
        
    def get_detailed_memory_stats(self):
        """Get detailed memory statistics including trends
        
        Returns:
            dict: Detailed memory statistics
        """
        current_stats = self.get_memory_stats()
        
        # Calculate memory usage trend (store last few measurements)
        if not hasattr(self, '_memory_history'):
            self._memory_history = []
            
        self._memory_history.append((time.time(), current_stats["percent"]))
        
        # Keep only last 10 measurements
        if len(self._memory_history) > 10:
            self._memory_history.pop(0)
            
        # Calculate trend if we have enough history
        trend = 0
        if len(self._memory_history) >= 2:
            oldest = self._memory_history[0]
            newest = self._memory_history[-1]
            time_diff = newest[0] - oldest[0]
            if time_diff > 0:
                trend = (newest[1] - oldest[1]) / time_diff
        
        return {
            "current": current_stats,
            "trend": trend,
            "trend_description": "increasing" if trend > 0.1 else "decreasing" if trend < -0.1 else "stable",
            "history": self._memory_history
        }
