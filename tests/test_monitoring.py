#!/usr/bin/env python3
"""
Unit tests for the monitoring module
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitoring import (
    REQUESTS, MODEL_INFERENCE_LATENCY, track_memory_usage, 
    track_request, track_inference_latency, track_connection
)

class TestMonitoring(unittest.TestCase):
    """Test cases for monitoring module"""
    
    @patch('monitoring.REQUESTS.labels')
    def test_track_request(self, mock_labels):
        """Test request tracking"""
        # Setup
        mock_counter = MagicMock()
        mock_labels.return_value = mock_counter
        
        # Exercise
        track_request(method="GET", endpoint="/api/test", status=200)
        
        # Verify
        mock_labels.assert_called_once_with(method="GET", endpoint="/api/test", status=200)
        mock_counter.inc.assert_called_once()
    
    @patch('monitoring.MODEL_INFERENCE_LATENCY.labels')
    def test_track_inference_latency(self, mock_labels):
        """Test inference latency tracking"""
        # Setup
        mock_histogram = MagicMock()
        mock_labels.return_value = mock_histogram
        
        # Exercise
        track_inference_latency(model="reflexia-r1", quantization="q4_0", latency=0.5)
        
        # Verify
        mock_labels.assert_called_once_with(model="reflexia-r1", quantization="q4_0")
        mock_histogram.observe.assert_called_once_with(0.5)
    
    @patch('monitoring.ACTIVE_CONNECTIONS')
    def test_track_connection(self, mock_connections):
        """Test connection tracking"""
        # Exercise - Connection established
        track_connection(connected=True)
        
        # Verify
        mock_connections.inc.assert_called_once()
        mock_connections.reset_mock()
        
        # Exercise - Connection closed
        track_connection(connected=False)
        
        # Verify
        mock_connections.dec.assert_called_once()
    
    @patch('monitoring.MEMORY_USAGE')
    @patch('monitoring.MEMORY_USAGE_PERCENT')
    def test_track_memory_usage(self, mock_percent, mock_usage):
        """Test memory usage tracking"""
        # Setup
        memory_manager = MagicMock()
        memory_manager.get_memory_stats.return_value = {
            'total': 16 * 1024 * 1024 * 1024,  # 16GB
            'used': 8 * 1024 * 1024 * 1024,    # 8GB
            'free': 8 * 1024 * 1024 * 1024,    # 8GB
            'percent': 50.0,
            'critical': False
        }
        
        # Exercise
        track_memory_usage(memory_manager, interval=1)
        
        # Wait for the first update
        import time
        time.sleep(0.1)
        
        # Verify
        memory_manager.get_memory_stats.assert_called()
        mock_usage.set.assert_called_with(8 * 1024 * 1024 * 1024)
        mock_percent.set.assert_called_with(50.0)

if __name__ == '__main__':
    unittest.main()