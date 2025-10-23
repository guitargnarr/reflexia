#!/usr/bin/env python3
"""
test_recovery.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Unit tests for the recovery module
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from recovery import CircuitBreaker, HealthMonitor, protect_model_manager

class TestCircuitBreaker(unittest.TestCase):
    """Test cases for circuit breaker implementation"""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state"""
        cb = CircuitBreaker("test")
        self.assertEqual(cb.state, CircuitBreaker.CLOSED)
        self.assertEqual(cb.failure_count, 0)
    
    def test_circuit_breaker_open_after_failures(self):
        """Test circuit breaker opens after failures"""
        cb = CircuitBreaker("test", failure_threshold=3)
        
        # First two failures
        for _ in range(2):
            result = cb.execute(lambda: None)
            self.assertTrue(result.success)
            cb.record_failure()
        
        # Circuit still closed
        self.assertEqual(cb.state, CircuitBreaker.CLOSED)
        
        # Third failure - should open circuit
        result = cb.execute(lambda: None)
        self.assertTrue(result.success)
        cb.record_failure()
        
        # Circuit now open
        self.assertEqual(cb.state, CircuitBreaker.OPEN)
        
        # Function should not be executed when circuit is open
        function_mock = MagicMock()
        result = cb.execute(function_mock)
        function_mock.assert_not_called()
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Circuit is open")
    
    @patch('recovery.time.time')
    def test_circuit_breaker_half_open_after_timeout(self, mock_time):
        """Test circuit breaker transitions to half-open after timeout"""
        # Setup
        mock_time.return_value = 100  # Initial time
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=30)
        
        # Open the circuit
        cb.execute(lambda: None)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitBreaker.OPEN)
        
        # Advance time to recovery_timeout + 1
        mock_time.return_value = 131
        
        # Should now be half-open
        function_mock = MagicMock(return_value="success")
        result = cb.execute(function_mock)
        self.assertEqual(cb.state, CircuitBreaker.HALF_OPEN)
        function_mock.assert_called_once()
        self.assertTrue(result.success)
        self.assertEqual(result.result, "success")
    
    def test_circuit_breaker_reset_after_success(self):
        """Test circuit breaker resets after successful execution in half-open state"""
        cb = CircuitBreaker("test", failure_threshold=1)
        
        # Open the circuit
        cb.execute(lambda: None)
        cb.record_failure()
        self.assertEqual(cb.state, CircuitBreaker.OPEN)
        
        # Manually set to half-open
        cb.state = CircuitBreaker.HALF_OPEN
        
        # Successful execution should reset the circuit
        function_mock = MagicMock(return_value="success")
        result = cb.execute(function_mock)
        self.assertEqual(cb.state, CircuitBreaker.CLOSED)
        self.assertEqual(cb.failure_count, 0)
        self.assertTrue(result.success)

class TestHealthMonitor(unittest.TestCase):
    """Test cases for health monitor implementation"""
    
    @patch('recovery.threading.Thread')
    def test_health_monitor_initialization(self, mock_thread):
        """Test health monitor initialization"""
        # Setup
        model_manager = MagicMock()
        memory_manager = MagicMock()
        
        # Exercise
        monitor = HealthMonitor(model_manager=model_manager, memory_manager=memory_manager)
        
        # Verify
        self.assertEqual(monitor.model_manager, model_manager)
        self.assertEqual(monitor.memory_manager, memory_manager)
        self.assertFalse(monitor.is_monitoring)
    
    @patch('recovery.threading.Thread')
    def test_start_monitoring(self, mock_thread):
        """Test start monitoring"""
        # Setup
        model_manager = MagicMock()
        memory_manager = MagicMock()
        monitor = HealthMonitor(model_manager=model_manager, memory_manager=memory_manager)
        
        # Exercise
        monitor.start_monitoring(interval=5)
        
        # Verify
        self.assertTrue(monitor.is_monitoring)
        mock_thread.assert_called_once()
        mock_thread.return_value.daemon = True
        mock_thread.return_value.start.assert_called_once()
    
    def test_check_health(self):
        """Test health check"""
        # Setup
        model_manager = MagicMock()
        model_manager.is_healthy.return_value = True
        
        memory_manager = MagicMock()
        memory_manager.get_memory_stats.return_value = {
            'critical': False,
            'percent': 50.0
        }
        
        monitor = HealthMonitor(model_manager=model_manager, memory_manager=memory_manager)
        
        # Exercise
        health_status = monitor.check_health()
        
        # Verify
        self.assertTrue(health_status['healthy'])
        self.assertEqual(health_status['services']['model'], True)
        self.assertEqual(health_status['services']['memory'], True)
        
        # Test with unhealthy model
        model_manager.is_healthy.return_value = False
        health_status = monitor.check_health()
        self.assertFalse(health_status['healthy'])
        self.assertEqual(health_status['services']['model'], False)

class TestProtectModelManager(unittest.TestCase):
    """Test cases for model manager protection with circuit breaker"""
    
    def test_protect_model_manager(self):
        """Test protecting model manager with circuit breaker"""
        # Setup
        model_manager = MagicMock()
        model_manager.generate_response.return_value = "Sample response"
        
        # Exercise
        protected_manager = protect_model_manager(model_manager)
        
        # Verify - method calls should be forwarded to the original manager
        response = protected_manager.generate_response("Test prompt")
        self.assertEqual(response, "Sample response")
        model_manager.generate_response.assert_called_once_with("Test prompt")
    
    def test_protected_manager_handles_exceptions(self):
        """Test protected manager handles exceptions correctly"""
        # Setup
        model_manager = MagicMock()
        model_manager.generate_response.side_effect = Exception("Test error")
        
        # Exercise
        protected_manager = protect_model_manager(model_manager)
        
        # Verify - first call should raise the exception
        with self.assertRaises(Exception):
            protected_manager.generate_response("Test prompt")
        
        # Verify - circuit should be open after threshold failures
        for _ in range(5):  # Should exceed default threshold
            try:
                protected_manager.generate_response("Test prompt")
            except:
                pass
        
        # Next call should return fallback value without calling the original
        model_manager.generate_response.reset_mock()
        response = protected_manager.generate_response("Test prompt")
        self.assertIn("Error", response)
        self.assertIn("circuit open", response.lower())
        model_manager.generate_response.assert_not_called()

if __name__ == '__main__':
    unittest.main()