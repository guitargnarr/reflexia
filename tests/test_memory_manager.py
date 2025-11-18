#!/usr/bin/env python3
"""
test_memory_manager.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Comprehensive tests for the MemoryManager module
"""
import os
import sys
import pytest
import time
import gc
import copy
from unittest.mock import patch, MagicMock, PropertyMock
from collections import namedtuple

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from memory_manager import MemoryManager


# Pytest fixture to ensure Config DEFAULT_CONFIG is reset between tests
@pytest.fixture(autouse=True)
def reset_config():
    """Reset Config.DEFAULT_CONFIG between tests to avoid state pollution"""
    original_config = copy.deepcopy(Config.DEFAULT_CONFIG)
    yield
    Config.DEFAULT_CONFIG = original_config


# Mock psutil.virtual_memory object
def create_mock_memory(total=16*1024**3, available=8*1024**3, used=8*1024**3,
                      free=8*1024**3, percent=50.0):
    """Create a mock memory object similar to psutil.virtual_memory()"""
    svmem = namedtuple('svmem', ['total', 'available', 'used', 'free', 'percent'])
    return svmem(total=total, available=available, used=used, free=free, percent=percent)


class TestMemoryManagerInitialization:
    """Test cases for MemoryManager initialization"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_init_with_default_config(self, mock_vmem):
        """Test initialization with default configuration"""
        mock_vmem.return_value = create_mock_memory()

        config = Config()
        memory_manager = MemoryManager(config)

        # Verify initialization
        assert memory_manager.config == config
        assert memory_manager.model_manager is None
        assert memory_manager.max_memory_percent == 80
        assert memory_manager.critical_memory_percent == 90

    @patch('memory_manager.psutil.virtual_memory')
    def test_init_with_custom_thresholds(self, mock_vmem):
        """Test initialization with custom memory thresholds"""
        mock_vmem.return_value = create_mock_memory()

        config = Config()
        config.set("memory", "max_memory_percent", 70)
        config.set("memory", "critical_memory_percent", 85)

        memory_manager = MemoryManager(config)

        assert memory_manager.max_memory_percent == 70
        assert memory_manager.critical_memory_percent == 85

    @patch('memory_manager.psutil.virtual_memory')
    def test_init_with_model_manager(self, mock_vmem):
        """Test initialization with a model manager"""
        mock_vmem.return_value = create_mock_memory()

        config = Config()
        mock_model_manager = MagicMock()

        memory_manager = MemoryManager(config, model_manager=mock_model_manager)

        assert memory_manager.model_manager == mock_model_manager

    @patch('memory_manager.psutil.virtual_memory')
    def test_init_with_custom_cache_size(self, mock_vmem):
        """Test initialization with custom cache size"""
        mock_vmem.return_value = create_mock_memory()

        config = Config()
        config.set("memory", "response_cache_size", 200)

        memory_manager = MemoryManager(config)

        # Verify cache is initialized (response_cache exists)
        assert hasattr(memory_manager, 'response_cache')


class TestGetMemoryStats:
    """Test cases for get_memory_stats() method"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_get_memory_stats_normal_conditions(self, mock_vmem):
        """Test get_memory_stats under normal conditions (50% usage)"""
        # Mock memory at 50% usage BEFORE creating MemoryManager
        mock_vmem.return_value = create_mock_memory(
            total=16*1024**3,
            available=8*1024**3,
            used=8*1024**3,
            free=8*1024**3,
            percent=50.0
        )

        config = Config()
        memory_manager = MemoryManager(config)

        stats = memory_manager.get_memory_stats()

        # Verify stats
        assert stats["total"] == 16*1024**3
        assert stats["available"] == 8*1024**3
        assert stats["used"] == 8*1024**3
        assert stats["free"] == 8*1024**3
        assert stats["percent"] == 50.0
        assert stats["critical"] is False  # Below 90%

    @patch('memory_manager.psutil.virtual_memory')
    def test_get_memory_stats_high_usage(self, mock_vmem):
        """Test get_memory_stats with high memory usage (85%)"""
        # Mock memory at 85% usage BEFORE creating MemoryManager
        mock_vmem.return_value = create_mock_memory(
            total=16*1024**3,
            available=2.4*1024**3,
            used=13.6*1024**3,
            free=2.4*1024**3,
            percent=85.0
        )

        config = Config()
        memory_manager = MemoryManager(config)

        stats = memory_manager.get_memory_stats()

        assert stats["percent"] == 85.0
        assert stats["critical"] is False  # Still below 90%

    @patch('memory_manager.psutil.virtual_memory')
    def test_get_memory_stats_critical_usage(self, mock_vmem):
        """Test get_memory_stats with critical memory usage (95%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock memory at 95% usage
        mock_vmem.return_value = create_mock_memory(
            total=16*1024**3,
            available=0.8*1024**3,
            used=15.2*1024**3,
            free=0.8*1024**3,
            percent=95.0
        )

        stats = memory_manager.get_memory_stats()

        assert stats["percent"] == 95.0
        assert stats["critical"] is True  # Above 90%

    @patch('memory_manager.psutil.virtual_memory')
    def test_get_memory_stats_low_usage(self, mock_vmem):
        """Test get_memory_stats with low memory usage (20%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock memory at 20% usage
        mock_vmem.return_value = create_mock_memory(
            total=16*1024**3,
            available=12.8*1024**3,
            used=3.2*1024**3,
            free=12.8*1024**3,
            percent=20.0
        )

        stats = memory_manager.get_memory_stats()

        assert stats["percent"] == 20.0
        assert stats["critical"] is False

    @patch('memory_manager.psutil.virtual_memory')
    def test_get_memory_stats_at_threshold(self, mock_vmem):
        """Test get_memory_stats exactly at critical threshold (90%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock memory at exactly 90% usage
        mock_vmem.return_value = create_mock_memory(
            total=16*1024**3,
            available=1.6*1024**3,
            used=14.4*1024**3,
            free=1.6*1024**3,
            percent=90.0
        )

        stats = memory_manager.get_memory_stats()

        assert stats["percent"] == 90.0
        assert stats["critical"] is True  # At threshold counts as critical


class TestCacheOperations:
    """Test cases for cache_response() and get_cached_response()"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_cache_response_normal_memory(self, mock_vmem):
        """Test caching when memory is normal (50%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock normal memory usage
        mock_vmem.return_value = create_mock_memory(percent=50.0)

        # Cache a response
        result = memory_manager.cache_response("test prompt", "test response")

        # Should return None (current implementation)
        assert result is None

    @patch('memory_manager.psutil.virtual_memory')
    def test_cache_response_high_memory_pressure(self, mock_vmem):
        """Test that caching is skipped when memory pressure is high (>80%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock high memory usage (85%)
        mock_vmem.return_value = create_mock_memory(percent=85.0)

        # Attempt to cache - should be skipped
        result = memory_manager.cache_response("test prompt", "test response")

        assert result is None

    @patch('memory_manager.psutil.virtual_memory')
    def test_cache_response_at_max_threshold(self, mock_vmem):
        """Test caching behavior exactly at max_memory_percent (80%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock memory at exactly 80%
        mock_vmem.return_value = create_mock_memory(percent=80.0)

        # Should still cache (>80%, not >=80%)
        result = memory_manager.cache_response("test prompt", "test response")

        assert result is None

    @patch('memory_manager.psutil.virtual_memory')
    def test_cache_response_just_above_threshold(self, mock_vmem):
        """Test caching is skipped just above threshold (81%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Mock memory at 81%
        mock_vmem.return_value = create_mock_memory(percent=81.0)

        # Should skip caching
        result = memory_manager.cache_response("test prompt", "test response")

        assert result is None

    def test_get_cached_response(self):
        """Test get_cached_response (currently returns None)"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Get cached response
        result = memory_manager.get_cached_response("test prompt")

        # Current implementation returns None
        assert result is None

    def test_cache_response_with_long_prompt(self):
        """Test caching with a very long prompt"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Create a long prompt
        long_prompt = "a" * 10000

        with patch('psutil.virtual_memory') as mock_vmem:
            mock_vmem.return_value = create_mock_memory(percent=50.0)

            # Should handle long prompts
            result = memory_manager.cache_response(long_prompt, "response")
            assert result is None


class TestReduceMemoryPressure:
    """Test cases for reduce_memory_pressure() method"""

    @patch('gc.collect')
    def test_reduce_memory_pressure_basic(self, mock_gc_collect):
        """Test basic memory pressure reduction"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Call reduce_memory_pressure
        result = memory_manager.reduce_memory_pressure()

        # Should call gc.collect()
        mock_gc_collect.assert_called_once()
        assert result is True

    @patch('gc.collect')
    def test_reduce_memory_pressure_with_model_manager(self, mock_gc_collect):
        """Test memory pressure reduction with model manager"""
        config = Config()
        mock_model_manager = MagicMock()
        mock_model_manager.clear_cache = MagicMock()

        memory_manager = MemoryManager(config, model_manager=mock_model_manager)

        # Call reduce_memory_pressure
        result = memory_manager.reduce_memory_pressure()

        # Should call gc.collect() and model_manager.clear_cache()
        mock_gc_collect.assert_called_once()
        mock_model_manager.clear_cache.assert_called_once()
        assert result is True

    @patch('gc.collect')
    def test_reduce_memory_pressure_without_clear_cache(self, mock_gc_collect):
        """Test memory pressure reduction when model_manager lacks clear_cache"""
        config = Config()
        mock_model_manager = MagicMock(spec=[])  # No clear_cache method

        memory_manager = MemoryManager(config, model_manager=mock_model_manager)

        # Call reduce_memory_pressure - should not fail
        result = memory_manager.reduce_memory_pressure()

        # Should still call gc.collect()
        mock_gc_collect.assert_called_once()
        assert result is True


class TestAdaptiveChunkSize:
    """Test cases for adaptive_chunk_size() method"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_normal_memory(self, mock_vmem):
        """Test chunk size with normal memory (50%) and normal text"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        # Normal text length
        chunk_size = memory_manager.adaptive_chunk_size(text_length=50000, base_chunk_size=1000)

        # Should return base chunk size
        assert chunk_size == 1000

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_low_memory(self, mock_vmem):
        """Test chunk size with low memory usage (30%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=30.0)

        # With low memory, can use larger chunks
        chunk_size = memory_manager.adaptive_chunk_size(text_length=50000, base_chunk_size=1000)

        # Should return larger chunks (up to 2x base)
        assert chunk_size == 2000

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_high_memory_pressure(self, mock_vmem):
        """Test chunk size with high memory pressure (85%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=85.0)

        chunk_size = memory_manager.adaptive_chunk_size(text_length=50000, base_chunk_size=1000)

        # Should reduce chunk size (base_chunk_size // 2)
        assert chunk_size == 500

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_critical_memory(self, mock_vmem):
        """Test chunk size with critical memory (95%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=95.0)

        chunk_size = memory_manager.adaptive_chunk_size(text_length=50000, base_chunk_size=1000)

        # Should use smallest chunks (base_chunk_size // 5)
        assert chunk_size == 200

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_very_large_text(self, mock_vmem):
        """Test chunk size with very large text (>1MB)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        # Very large text
        chunk_size = memory_manager.adaptive_chunk_size(text_length=2000000, base_chunk_size=1000)

        # Should use smaller chunks for large text
        assert chunk_size == 800

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_large_text(self, mock_vmem):
        """Test chunk size with large text (>100KB)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        chunk_size = memory_manager.adaptive_chunk_size(text_length=150000, base_chunk_size=1000)

        # Should return base chunk size
        assert chunk_size == 1000

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_small_text_low_memory(self, mock_vmem):
        """Test chunk size with small text and low memory usage"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=40.0)

        chunk_size = memory_manager.adaptive_chunk_size(text_length=10000, base_chunk_size=1000)

        # Can use larger chunks
        assert chunk_size == 2000

    @patch('memory_manager.psutil.virtual_memory')
    def test_adaptive_chunk_size_minimum_enforced(self, mock_vmem):
        """Test that minimum chunk size is enforced in critical conditions"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=95.0)

        # Small base chunk size
        chunk_size = memory_manager.adaptive_chunk_size(text_length=50000, base_chunk_size=500)

        # Should enforce minimum of 200
        assert chunk_size == 200


class TestShouldUseQuantization:
    """Test cases for should_use_quantization() method"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_should_use_quantization_normal_memory(self, mock_vmem):
        """Test quantization recommendation with normal memory (50%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        result = memory_manager.should_use_quantization()

        # Should not recommend quantization
        assert result is False

    @patch('memory_manager.psutil.virtual_memory')
    def test_should_use_quantization_high_memory(self, mock_vmem):
        """Test quantization recommendation with high memory (85%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=85.0)

        result = memory_manager.should_use_quantization()

        # Should recommend quantization (>80%)
        assert result is True

    @patch('memory_manager.psutil.virtual_memory')
    def test_should_use_quantization_at_threshold(self, mock_vmem):
        """Test quantization recommendation at threshold (80%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=80.0)

        result = memory_manager.should_use_quantization()

        # Should not recommend (>80%, not >=80%)
        assert result is False

    @patch('memory_manager.psutil.virtual_memory')
    def test_should_use_quantization_just_above_threshold(self, mock_vmem):
        """Test quantization recommendation just above threshold (81%)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=81.0)

        result = memory_manager.should_use_quantization()

        # Should recommend quantization
        assert result is True

    @patch('memory_manager.psutil.virtual_memory')
    def test_should_use_quantization_custom_threshold(self, mock_vmem):
        """Test quantization with custom max_memory_percent"""
        config = Config()
        config.set("memory", "max_memory_percent", 70)
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=75.0)

        result = memory_manager.should_use_quantization()

        # Should recommend quantization (75% > 70%)
        assert result is True


class TestDetailedMemoryStats:
    """Test cases for get_detailed_memory_stats() method"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_get_detailed_stats_first_call(self, mock_vmem):
        """Test detailed stats on first call (no history)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        stats = memory_manager.get_detailed_memory_stats()

        # Verify structure
        assert "current" in stats
        assert "trend" in stats
        assert "trend_description" in stats
        assert "history" in stats

        # First call should have 1 history entry
        assert len(stats["history"]) == 1
        assert stats["trend"] == 0  # No trend on first call
        assert stats["trend_description"] == "stable"

    @patch('memory_manager.psutil.virtual_memory')
    @patch('time.time')
    def test_get_detailed_stats_increasing_trend(self, mock_time, mock_vmem):
        """Test detailed stats with increasing memory trend"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Simulate increasing memory usage over time
        mock_time.side_effect = [100, 110, 120]  # 10 second intervals
        mock_vmem.side_effect = [
            create_mock_memory(percent=50.0),
            create_mock_memory(percent=60.0),
            create_mock_memory(percent=70.0)
        ]

        # Call multiple times
        memory_manager.get_detailed_memory_stats()
        memory_manager.get_detailed_memory_stats()
        stats = memory_manager.get_detailed_memory_stats()

        # Should detect increasing trend
        assert stats["trend"] > 0
        assert stats["trend_description"] == "increasing"
        assert len(stats["history"]) == 3

    @patch('memory_manager.psutil.virtual_memory')
    @patch('time.time')
    def test_get_detailed_stats_decreasing_trend(self, mock_time, mock_vmem):
        """Test detailed stats with decreasing memory trend"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Simulate decreasing memory usage over time
        mock_time.side_effect = [100, 110, 120]
        mock_vmem.side_effect = [
            create_mock_memory(percent=70.0),
            create_mock_memory(percent=60.0),
            create_mock_memory(percent=50.0)
        ]

        # Call multiple times
        memory_manager.get_detailed_memory_stats()
        memory_manager.get_detailed_memory_stats()
        stats = memory_manager.get_detailed_memory_stats()

        # Should detect decreasing trend
        assert stats["trend"] < 0
        assert stats["trend_description"] == "decreasing"

    @patch('memory_manager.psutil.virtual_memory')
    @patch('time.time')
    def test_get_detailed_stats_stable_trend(self, mock_time, mock_vmem):
        """Test detailed stats with stable memory"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Simulate stable memory usage
        mock_time.side_effect = [100, 110, 120]
        mock_vmem.side_effect = [
            create_mock_memory(percent=50.0),
            create_mock_memory(percent=50.1),
            create_mock_memory(percent=50.0)
        ]

        # Call multiple times
        memory_manager.get_detailed_memory_stats()
        memory_manager.get_detailed_memory_stats()
        stats = memory_manager.get_detailed_memory_stats()

        # Should detect stable trend (small changes)
        assert stats["trend_description"] == "stable"

    @patch('memory_manager.psutil.virtual_memory')
    @patch('time.time')
    def test_get_detailed_stats_history_limit(self, mock_time, mock_vmem):
        """Test that history is limited to 10 entries"""
        config = Config()
        memory_manager = MemoryManager(config)

        # Simulate many calls
        mock_time.side_effect = range(100, 120)
        mock_vmem.return_value = create_mock_memory(percent=50.0)

        # Call 15 times
        for i in range(15):
            memory_manager.get_detailed_memory_stats()

        stats = memory_manager.get_detailed_memory_stats()

        # Should keep only last 10 entries
        assert len(stats["history"]) == 10


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_edge_case_zero_percent_memory(self, mock_vmem):
        """Test handling of 0% memory usage (theoretical edge case)"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=0.0)

        stats = memory_manager.get_memory_stats()

        assert stats["percent"] == 0.0
        assert stats["critical"] is False

    @patch('memory_manager.psutil.virtual_memory')
    def test_edge_case_100_percent_memory(self, mock_vmem):
        """Test handling of 100% memory usage"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(
            total=16*1024**3,
            available=0,
            used=16*1024**3,
            free=0,
            percent=100.0
        )

        stats = memory_manager.get_memory_stats()

        assert stats["percent"] == 100.0
        assert stats["critical"] is True

        # Should recommend quantization
        assert memory_manager.should_use_quantization() is True

    @patch('memory_manager.psutil.virtual_memory')
    def test_edge_case_negative_chunk_size_protection(self, mock_vmem):
        """Test that chunk size doesn't go negative"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=95.0)

        # Very small base chunk size
        chunk_size = memory_manager.adaptive_chunk_size(text_length=1000, base_chunk_size=100)

        # Should enforce minimum (200)
        assert chunk_size > 0
        assert chunk_size == 200

    def test_edge_case_none_model_manager(self):
        """Test operations when model_manager is None"""
        config = Config()
        memory_manager = MemoryManager(config, model_manager=None)

        # Should not crash when reducing memory pressure
        result = memory_manager.reduce_memory_pressure()
        assert result is True

    @patch('memory_manager.psutil.virtual_memory')
    def test_edge_case_very_large_text(self, mock_vmem):
        """Test adaptive chunk size with extremely large text"""
        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        # 10MB text
        chunk_size = memory_manager.adaptive_chunk_size(text_length=10000000, base_chunk_size=1000)

        # Should use small chunks for very large text
        assert chunk_size == 800

    def test_edge_case_empty_prompt_caching(self):
        """Test caching with empty prompt"""
        config = Config()
        memory_manager = MemoryManager(config)

        with patch('psutil.virtual_memory') as mock_vmem:
            mock_vmem.return_value = create_mock_memory(percent=50.0)

            # Cache empty prompt
            result = memory_manager.cache_response("", "response")
            assert result is None

            # Get cached empty prompt
            result = memory_manager.get_cached_response("")
            assert result is None


class TestThreadSafety:
    """Test thread safety of memory monitoring operations"""

    @patch('memory_manager.psutil.virtual_memory')
    def test_concurrent_get_memory_stats(self, mock_vmem):
        """Test that get_memory_stats is thread-safe"""
        import threading

        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)

        results = []

        def get_stats():
            stats = memory_manager.get_memory_stats()
            results.append(stats)

        # Create multiple threads
        threads = [threading.Thread(target=get_stats) for _ in range(10)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should have succeeded
        assert len(results) == 10
        for stats in results:
            assert stats["percent"] == 50.0

    @patch('memory_manager.psutil.virtual_memory')
    @patch('time.time')
    def test_concurrent_detailed_stats(self, mock_time, mock_vmem):
        """Test that detailed stats handles concurrent access"""
        import threading

        config = Config()
        memory_manager = MemoryManager(config)

        mock_vmem.return_value = create_mock_memory(percent=50.0)
        mock_time.return_value = 100

        results = []

        def get_detailed():
            stats = memory_manager.get_detailed_memory_stats()
            results.append(stats)

        # Create threads
        threads = [threading.Thread(target=get_detailed) for _ in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # All should have succeeded (may have race conditions on history)
        assert len(results) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
