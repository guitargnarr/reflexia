#!/usr/bin/env python3
"""
config.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Configuration module for Reflexia LLM implementation
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("reflexia-tools.config")

class Config:
    """Configuration handler for Reflexia Tools"""
    
    # Default configuration values optimized for M3 Max with 36GB RAM
    DEFAULT_CONFIG = {
        "model": {
            "name": "llama3:latest",
            "quantization": "q4_0",
            "context_length": 4096,
            "metal_enabled": True,
            "batch_size": 8
        },
        "memory": {
            "cache_size": 128,
            "max_memory_percent": 80,
            "lru_cache_size": 64
        },
        "prompt": {
            "default_system_prompt": "You are a helpful AI assistant.",
            "templates": {
                "default": "{system}\n\nUser: {user_input}\nAssistant:",
                "code": "You are an expert programmer. {system}\n\nUser: {user_input}\nWrite code to solve this problem:\nAssistant:",
                "creative": "You are a creative assistant. {system}\n\nUser: {user_input}\nAssistant:"
            }
        },
        "fine_tuning": {
            "method": "lora",
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "epochs": 3,
            "learning_rate": 2e-4,
            "batch_size": 4,
            "max_steps": 1000,
            "save_steps": 200
        },
        "resources": {
            "threads": 8,
            "metal_optimized": True
        },
        "paths": {
            "models_dir": "models",
            "cache_dir": "cache",
            "datasets_dir": "datasets",
            "output_dir": "output",
            "logs_dir": "logs"
        }
    }
    
    def __init__(self, config_path=None):
        """Initialize the configuration"""
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load config from file if provided
        if config_path:
            self.config_path = Path(config_path)
            self.load_config()
        else:
            # Look for config.json in current directory
            default_path = Path("config.json")
            if default_path.exists():
                self.config_path = default_path
                self.load_config()
            else:
                logger.info("No config file found, using default configuration")
                self.config_path = default_path
                self.save_config()  # Create default config file
        
        # Create directories defined in paths
        self._create_directories()
        
        logger.info("Configuration initialized")
    
    def get(self, section, key=None, default=None):
        """Get a configuration value"""
        if section not in self.config:
            return default
        
        if key is None:
            return self.config[section]
        
        if key not in self.config[section]:
            return default
            
        return self.config[section][key]
    
    def set(self, section, key, value):
        """Set a configuration value"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        return True
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return False
                
            with open(self.config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Update the configuration
            for section, values in loaded_config.items():
                if section not in self.config:
                    self.config[section] = {}
                    
                if isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
                    
            logger.info(f"Configuration loaded from {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def _create_directories(self):
        """Create directories defined in paths configuration"""
        for dir_name, dir_path in self.config["paths"].items():
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")