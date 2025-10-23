#!/usr/bin/env python3
"""
monitoring.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""

Monitoring module for Reflexia Model Manager
Handles Prometheus metrics and monitoring infrastructure
"""
import time
import logging
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
from functools import wraps

logger = logging.getLogger("reflexia-tools.monitoring")

# Create metrics
REQUESTS = Counter(
    'reflexia_http_requests_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'reflexia_http_request_duration_seconds', 
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

MODEL_INFERENCE_LATENCY = Histogram(
    'reflexia_model_inference_duration_seconds', 
    'Model inference latency in seconds',
    ['model', 'quantization']
)

MEMORY_USAGE = Gauge(
    'reflexia_memory_usage_bytes', 
    'Current memory usage in bytes'
)

MEMORY_PERCENT = Gauge(
    'reflexia_memory_usage_percent', 
    'Current memory usage as percentage'
)

CPU_PERCENT = Gauge(
    'reflexia_cpu_usage_percent', 
    'Current CPU usage as percentage'
)

RAG_QUERIES = Counter(
    'reflexia_rag_queries_total', 
    'Total number of RAG queries'
)

RAG_DOCUMENT_COUNT = Gauge(
    'reflexia_rag_document_count', 
    'Number of documents in RAG system'
)

ACTIVE_CONNECTIONS = Gauge(
    'reflexia_active_connections', 
    'Number of active WebSocket connections'
)

def instrument_flask_app(app):
    """Add Prometheus Flask exporter to the Flask app
    
    Args:
        app: Flask application
    """
    try:
        from prometheus_flask_exporter import PrometheusMetrics
        metrics = PrometheusMetrics(app)
        
        # Add default metrics
        metrics.info('reflexia_app_info', 'Application info', 
                     version='1.0.0', service='reflexia-model-manager')
                     
        logger.info("Prometheus Flask metrics initialized")
        return metrics
    except ImportError:
        logger.warning("prometheus_flask_exporter not installed, skipping Flask instrumentation")
        return None

def start_metrics_server(port=9090):
    """Start a dedicated Prometheus metrics server
    
    Args:
        port: Port to expose metrics on (default: 9090)
    """
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus metrics server: {e}")

def track_memory_usage(memory_manager, interval=15):
    """Background task to track memory usage metrics
    
    Args:
        memory_manager: MemoryManager instance to monitor
        interval: Polling interval in seconds (default: 15)
    """
    import threading
    
    def update_metrics():
        while True:
            try:
                # Get memory stats
                stats = memory_manager.get_memory_stats()
                
                # Update gauges
                MEMORY_USAGE.set(stats.get("used", 0))
                MEMORY_PERCENT.set(stats.get("percent", 0))
                
                # Get CPU stats
                import psutil
                CPU_PERCENT.set(psutil.cpu_percent())
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error updating memory metrics: {e}")
                time.sleep(interval)
    
    thread = threading.Thread(target=update_metrics, daemon=True)
    thread.start()
    logger.info(f"Memory metrics tracking started with {interval}s interval")
    
def track_model_inference(func):
    """Decorator to track model inference latency
    
    Args:
        func: Function to track (should be model_manager.generate_response)
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Get model info
        model = getattr(self, 'model_name', 'unknown')
        quantization = getattr(self, 'quantization', 'unknown')
        
        # Measure time
        start_time = time.time()
        try:
            # Call original function
            result = func(self, *args, **kwargs)
            return result
        finally:
            # Record latency
            latency = time.time() - start_time
            MODEL_INFERENCE_LATENCY.labels(
                model=model,
                quantization=quantization
            ).observe(latency)
    
    return wrapper

def track_rag_document_count(rag_manager):
    """Update RAG document count metric
    
    Args:
        rag_manager: RAGManager instance
    """
    try:
        doc_count = len(rag_manager.list_documents())
        RAG_DOCUMENT_COUNT.set(doc_count)
    except Exception as e:
        logger.error(f"Error updating RAG document count: {e}")

def track_connection(connected=True):
    """Track active WebSocket connections
    
    Args:
        connected: True if connection established, False if disconnected
    """
    if connected:
        ACTIVE_CONNECTIONS.inc()
    else:
        ACTIVE_CONNECTIONS.dec()