#!/usr/bin/env python3
"""
test_config.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Tests for the Config module
"""
import os
import sys
import pytest
import tempfile
import json
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

class TestConfig:
    """Test cases for the Config class"""
    
    def test_default_config(self):
        """Test that default config is loaded correctly"""
        config = Config()
        assert config.get("model", "name") == "llama3:latest"
        assert config.get("model", "quantization") == "q4_0"
        assert config.get("model", "context_length") == 4096
    
    def test_get_with_default(self):
        """Test the get method with a default value"""
        config = Config()
        # Test getting an existing value
        assert config.get("model", "name") == "llama3:latest"
        # Test getting a non-existing value with default
        assert config.get("non_existing", "key", default="default_value") == "default_value"
    
    def test_set_and_get(self):
        """Test setting and getting a config value"""
        config = Config()
        # Set a new value
        config.set("test_section", "test_key", "test_value")
        # Get the value back
        assert config.get("test_section", "test_key") == "test_value"
    
    def test_load_and_save_config(self):
        """Test loading and saving configuration"""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            test_config = {
                "test_section": {
                    "test_key": "test_value"
                }
            }
            temp_file.write(json.dumps(test_config).encode('utf-8'))
            temp_path = temp_file.name
        
        try:
            # Load the config
            config = Config(temp_path)
            # Check if value is loaded correctly
            assert config.get("test_section", "test_key") == "test_value"
            
            # Modify the config
            config.set("test_section", "new_key", "new_value")
            config.save_config()
            
            # Load the config again to verify it was saved
            config2 = Config(temp_path)
            assert config2.get("test_section", "new_key") == "new_value"
        finally:
            # Clean up the temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)