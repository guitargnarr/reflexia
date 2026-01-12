#!/usr/bin/env python3
"""
recovery.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Recovery mechanisms for Reflexia Model Manager
Implements error recovery, circuit breakers, and auto-healing capabilities
"""
import time
import logging
import threading
from functools import wraps

logger = logging.getLogger("reflexia-tools.recovery")


class CircuitBreaker:
    """Circuit breaker pattern implementation to prevent cascading failures.

    The circuit breaker has three states:
    - CLOSED: All calls go through (normal operation)
    - OPEN: All calls fail fast (after too many failures)
    - HALF-OPEN: Next call is allowed through to test system health
    """

    # Circuit breaker states
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half-open'

    def __init__(self, name, failure_threshold=5, recovery_timeout=30,
                 failure_count_timeout=60):
        """Initialize the circuit breaker.

        Args:
            name: Name/identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery (half-open)
            failure_count_timeout: Seconds before resetting failure count
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count_timeout = failure_count_timeout

        # State management
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.open_time = 0

        logger.info(f"Circuit breaker '{name}' initialized")

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        current_time = time.time()

        # Reset failure count if enough time has passed since last failure
        if current_time - self.last_failure_time > self.failure_count_timeout:
            self.failure_count = 0

        self.failure_count += 1
        self.last_failure_time = current_time

        # Open circuit if threshold reached
        if self.state == self.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            self.open_time = current_time
            logger.warning(f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures")

    def record_success(self):
        """Record a success and potentially close the circuit."""
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            self.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' CLOSED after successful test")

    def allow_request(self):
        """Check if request should be allowed through.

        Returns:
            bool: True if request should be allowed, False otherwise
        """
        current_time = time.time()

        # Check if circuit is open
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if current_time - self.open_time > self.recovery_timeout:
                self.state = self.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}' entering HALF-OPEN state for testing")
                return True
            return False

        # Always allow if closed or half-open
        return True


def circuit_breaker(breaker):
    """Decorator to apply circuit breaker pattern to a function.

    Args:
        breaker: CircuitBreaker instance to use

    Returns:
        Decorated function with circuit breaker protection
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not breaker.allow_request():
                logger.warning(f"Circuit breaker '{breaker.name}' prevented call to {func.__name__}")
                raise Exception(f"Service unavailable: circuit breaker '{breaker.name}' open")

            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception:
                breaker.record_failure()
                raise
        return wrapper
    return decorator


class HealthMonitor:
    """Monitors the health of system components and takes recovery actions."""

    def __init__(self, model_manager=None, memory_manager=None, rag_manager=None):
        """Initialize the health monitor.

        Args:
            model_manager: ModelManager instance to monitor
            memory_manager: MemoryManager instance to monitor
            rag_manager: RAGManager instance to monitor
        """
        self.model_manager = model_manager
        self.memory_manager = memory_manager
        self.rag_manager = rag_manager

        # Health status of components
        self.component_health = {
            "model": True,
            "memory": True,
            "rag": True if rag_manager else False
        }

        # Circuit breakers for components
        self.circuit_breakers = {
            "model": CircuitBreaker("model", failure_threshold=3),
            "rag": CircuitBreaker("rag", failure_threshold=3)
        }

        logger.info("Health monitor initialized")

    def start_monitoring(self, interval=30):
        """Start background health monitoring.

        Args:
            interval: Check interval in seconds
        """
        thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        thread.start()
        logger.info(f"Health monitoring started with {interval}s interval")

    def _monitor_loop(self, interval):
        """Background monitoring loop."""
        while True:
            try:
                self.check_health()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                time.sleep(interval)

    def check_health(self):
        """Check health of all components and attempt recovery if needed."""
        # Check model health with a simple ping
        if self.model_manager:
            try:
                # Simple prompt to check if model is responsive
                self.model_manager.generate_response("Hello", max_tokens=5)
                self.component_health["model"] = True
            except Exception as e:
                logger.error(f"Model health check failed: {e}")
                self.component_health["model"] = False
                self._attempt_model_recovery()

        # Check memory pressure
        if self.memory_manager:
            try:
                stats = self.memory_manager.get_memory_stats()
                memory_percent = stats.get("percent", 0)

                # If memory usage is critically high, take action
                if memory_percent > 90:
                    logger.warning(f"Critical memory pressure: {memory_percent}%")
                    self.component_health["memory"] = False
                    self._attempt_memory_recovery()
                else:
                    self.component_health["memory"] = True
            except Exception as e:
                logger.error(f"Memory health check failed: {e}")
                self.component_health["memory"] = False

        # Check RAG health if available
        if self.rag_manager:
            try:
                # Check if we can list documents
                self.rag_manager.list_documents()
                self.component_health["rag"] = True
            except Exception as e:
                logger.error(f"RAG health check failed: {e}")
                self.component_health["rag"] = False
                self._attempt_rag_recovery()

    def _attempt_model_recovery(self):
        """Attempt to recover model functionality."""
        logger.info("Attempting model recovery...")

        try:
            # Strategy 1: Try to reload the model
            if hasattr(self.model_manager, "load_model"):
                logger.info("Reloading model...")
                self.model_manager.load_model()

            # Strategy 2: Try switching to a lighter quantization
            if hasattr(self.model_manager, "adaptive_quantization") and self.memory_manager:
                logger.info("Switching to lighter quantization...")
                self.model_manager.adaptive_quantization(self.memory_manager)

            logger.info("Model recovery attempted")
        except Exception as e:
            logger.error(f"Model recovery failed: {e}")

    def _attempt_memory_recovery(self):
        """Attempt to recover from memory pressure."""
        logger.info("Attempting memory recovery...")

        try:
            # Strategy 1: Clear caches
            if hasattr(self.model_manager, "clear_cache"):
                logger.info("Clearing model cache...")
                self.model_manager.clear_cache()

            # Strategy 2: Reduce memory pressure
            if hasattr(self.memory_manager, "reduce_memory_pressure"):
                logger.info("Reducing memory pressure...")
                self.memory_manager.reduce_memory_pressure()

            # Strategy 3: Switch to lighter model quantization
            if hasattr(self.model_manager, "adaptive_quantization"):
                logger.info("Switching to lighter quantization...")
                self.model_manager.adaptive_quantization(self.memory_manager, force_reduction=True)

            logger.info("Memory recovery attempted")
        except Exception as e:
            logger.error(f"Memory recovery failed: {e}")

    def _attempt_rag_recovery(self):
        """Attempt to recover RAG functionality."""
        logger.info("Attempting RAG recovery...")

        try:
            # Strategy 1: Reinitialize the vector store
            if hasattr(self.rag_manager, "reinitialize_vector_store"):
                logger.info("Reinitializing vector store...")
                self.rag_manager.reinitialize_vector_store()

            # Strategy 2: Reconnect to the database
            if hasattr(self.rag_manager, "reconnect"):
                logger.info("Reconnecting to RAG database...")
                self.rag_manager.reconnect()

            logger.info("RAG recovery attempted")
        except Exception as e:
            logger.error(f"RAG recovery failed: {e}")


def protect_model_manager(model_manager):
    """Apply circuit breakers to critical model manager methods.

    Args:
        model_manager: ModelManager instance to protect

    Returns:
        Protected ModelManager instance
    """
    breaker = CircuitBreaker("model_inference", failure_threshold=3)

    # Protect generate_response method
    original_generate = model_manager.generate_response
    model_manager.generate_response = circuit_breaker(breaker)(original_generate)

    logger.info("Model manager protected with circuit breaker")

    return model_manager


def protect_rag_manager(rag_manager):
    """Apply circuit breakers to critical RAG manager methods.

    Args:
        rag_manager: RAGManager instance to protect

    Returns:
        Protected RAGManager instance or None
    """
    if not rag_manager:
        return None

    breaker = CircuitBreaker("rag_query", failure_threshold=3)

    # Protect generate_rag_response method if it exists
    if hasattr(rag_manager, "generate_rag_response"):
        original_generate = rag_manager.generate_rag_response
        rag_manager.generate_rag_response = circuit_breaker(breaker)(original_generate)

    logger.info("RAG manager protected with circuit breaker")

    return rag_manager
