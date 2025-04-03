#!/usr/bin/env python3
"""
test_model_manager.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Tests for the ModelManager module
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from model_manager import ModelManager

class TestModelManager:
    """Test cases for the ModelManager class"""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        config = Config()
        config.set("model", "name", "llama3:latest")
        config.set("model", "quantization", "q4_0")
        config.set("model", "context_length", 4096)
        return config
    
    @patch('subprocess.run')
    def test_init(self, mock_run, config):
        """Test ModelManager initialization"""
        # Mock subprocess.run for _check_model_availability
        mock_process = MagicMock()
        mock_process.stdout = "llama3:latest\n"
        mock_run.return_value = mock_process
        
        # Create model manager
        model_manager = ModelManager(config)
        
        # Verify initialization
        assert model_manager.model_name == "llama3:latest"
        assert model_manager.quantization == "q4_0"
        assert model_manager.context_length == 4096
        
        # Verify subprocess was called
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_estimate_content_complexity(self, mock_run, config):
        """Test content complexity estimation"""
        # Mock subprocess.run for _check_model_availability
        mock_process = MagicMock()
        mock_process.stdout = "llama3:latest\n"
        mock_run.return_value = mock_process
        
        # Create model manager
        model_manager = ModelManager(config)
        
        # Test with simple text
        simple_text = "Hello, how are you?"
        simple_complexity = model_manager.estimate_content_complexity(simple_text)
        assert 0 <= simple_complexity <= 1
        
        # Test with complex text
        complex_text = """
        def calculate_tensor_gradient(tensor, function):
            '''Calculate the gradient of a function with respect to a tensor'''
            x = tensor.requires_grad_(True)
            y = function(x)
            y.backward()
            return x.grad
        """
        complex_complexity = model_manager.estimate_content_complexity(complex_text)
        assert 0 <= complex_complexity <= 1
        
        # Complex text should be more complex than simple text
        assert complex_complexity > simple_complexity