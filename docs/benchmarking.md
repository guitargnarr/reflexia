# Reflexia Performance Benchmarking Guide

This guide explains how to benchmark and optimize the performance of your Reflexia Model Manager deployment.

## Benchmarking Tools

Reflexia includes built-in benchmarking capabilities that allow you to measure:

1. **Inference Latency**: Time to generate responses
2. **Memory Usage**: RAM consumption under various loads
3. **Throughput**: Requests per second the system can handle
4. **RAG Performance**: Document retrieval and processing time

## Running Basic Benchmarks

### Command-line Benchmark

The simplest way to run benchmarks is using the built-in benchmark command:

```bash
python main.py --benchmark
```

This will run a standard set of benchmark tests and output the results.

### Targeted Benchmarks

For more specific benchmarks, use the `benchmark.py` script with options:

```bash
# Benchmark inference with different quantization levels
python benchmark.py --test inference --quantization q4_0,q5_k_m,f16

# Benchmark RAG with varying document counts
python benchmark.py --test rag --documents 10,100,1000

# Benchmark memory usage with different content complexity
python benchmark.py --test memory --complexity low,medium,high

# Benchmark throughput with concurrent requests
python benchmark.py --test throughput --concurrency 1,5,10,20
```

## Prometheus Metrics

For continuous performance monitoring, Reflexia exports Prometheus metrics.

### Viewing Metrics

Access the metrics endpoint at:
```
http://localhost:9090/metrics
```

Key metrics include:

1. **Request Counts**:
   ```
   reflexia_http_requests_total{method="GET", endpoint="/api/documents", status="200"}
   ```

2. **Inference Latency**:
   ```
   reflexia_model_inference_duration_seconds_count{model="reflexia-r1", quantization="q4_0"}
   reflexia_model_inference_duration_seconds_sum{model="reflexia-r1", quantization="q4_0"}
   reflexia_model_inference_duration_seconds_bucket{model="reflexia-r1", quantization="q4_0", le="0.1"}
   ```

3. **Memory Usage**:
   ```
   reflexia_memory_usage_bytes
   reflexia_memory_usage_percent
   ```

4. **RAG Performance**:
   ```
   reflexia_rag_retrieval_duration_seconds
   reflexia_rag_document_count
   ```

### Grafana Dashboard

A pre-configured Grafana dashboard is available in `kubernetes/grafana-dashboard.json` that visualizes these metrics.

## Performance Factors

Several factors influence Reflexia's performance:

### Hardware Factors

1. **CPU**: More cores and higher clock speeds improve performance
   - Recommendation: 4+ cores for moderate usage, 8+ cores for heavy usage

2. **RAM**: More RAM allows for larger models and document caches
   - Recommendation: 16GB minimum, 32GB+ recommended

3. **GPU**: Accelerates computation (when supported)
   - Recommendation: 8GB+ VRAM for optimal performance
   
4. **Storage**: SSD speeds affect document loading and model initialization
   - Recommendation: NVMe SSD for best performance

### Software Factors

1. **Quantization Level**: Lower precision (e.g., q4_0) is faster but less accurate
   - Trade-off: Speed vs. Quality

2. **Context Length**: Shorter context windows require less memory
   - Trade-off: Memory Usage vs. Context Awareness

3. **RAG Configuration**: More documents increase quality but slow retrieval
   - Trade-off: Knowledge Breadth vs. Speed

4. **Model Size**: Smaller models are faster but less capable
   - Trade-off: Speed vs. Capability

## Optimizing Performance

### Quick Wins

1. **Enable Adaptive Quantization**:
   ```
   ENABLE_ADAPTIVE_QUANTIZATION=true
   ```

2. **Tune Memory Limits**:
   ```
   MAX_MEMORY_PERCENT=80
   ```

3. **Enable Response Caching**:
   ```
   ENABLE_RESPONSE_CACHE=true
   RESPONSE_CACHE_SIZE=1000
   ```

4. **Optimize Document Chunking**:
   - Smaller chunks (256-512 tokens) for faster retrieval
   - Larger chunks (512-1024 tokens) for better context

### Advanced Optimizations

1. **Fine-tune RAG Retrieval Parameters**:
   ```python
   # In config.py
   config.set("rag", "similarity_top_k", 3)  # Number of documents to retrieve
   config.set("rag", "chunk_size", 512)      # Document chunk size in tokens
   config.set("rag", "chunk_overlap", 50)    # Overlap between chunks in tokens
   ```

2. **Adjust Thread Pool Size**:
   ```python
   # In config.py
   config.set("performance", "thread_pool_size", 4)
   ```

3. **Implement Request Batching**:
   ```python
   # Example batching in client code
   responses = model_manager.batch_generate([
       "What is quantum computing?",
       "Explain machine learning",
       "How does a transformer model work?"
   ])
   ```

4. **Optimize Vector Database**:
   ```python
   # Configure vector database parameters
   config.set("vector_db", "embedding_dim", 384)    # Smaller embedding dimension 
   config.set("vector_db", "distance_metric", "ip") # Inner product is faster than cosine
   ```

## Benchmarking Results Interpretation

### Inference Latency

| Quantization | Model Size | Avg. Latency | 95th Percentile | Max Latency |
|--------------|------------|--------------|-----------------|-------------|
| q4_0         | 7B         | 150ms/token  | 200ms/token     | 250ms/token |
| q5_k_m       | 7B         | 180ms/token  | 240ms/token     | 300ms/token |
| f16          | 7B         | 300ms/token  | 400ms/token     | 500ms/token |

### Memory Usage

| Quantization | Model Size | Base Memory | Peak Memory |
|--------------|------------|-------------|-------------|
| q4_0         | 7B         | ~4GB        | ~6GB        |
| q5_k_m       | 7B         | ~5GB        | ~7GB        |
| f16          | 7B         | ~10GB       | ~14GB       |

### Throughput

| Deployment | Concurrent Users | Requests/sec |
|------------|------------------|--------------|
| Single CPU | 1                | ~2           |
| Single CPU | 5                | ~1           |
| GPU        | 1                | ~8           |
| GPU        | 5                | ~6           |

### RAG Performance

| Document Count | Chunk Size | Retrieval Time | Total Response Time |
|----------------|------------|----------------|---------------------|
| 100            | 512        | ~100ms         | Base + ~150ms       |
| 1,000          | 512        | ~250ms         | Base + ~300ms       |
| 10,000         | 512        | ~500ms         | Base + ~600ms       |

## Load Testing

For thorough performance analysis, use the included load testing script:

```bash
python load_test.py --workers 10 --duration 300 --ramp-up 60
```

This will simulate multiple concurrent users and generate a comprehensive report on system performance under load.

## Common Performance Issues

1. **Memory Leaks**: 
   - Symptom: Gradually increasing memory usage
   - Solution: Check for reference cycles or missed cleanup

2. **Slow Document Retrieval**:
   - Symptom: High RAG latency
   - Solution: Optimize chunk size, reduce number of retrieved documents

3. **CPU Bottlenecks**:
   - Symptom: High CPU usage, slow responses
   - Solution: Consider GPU acceleration or more efficient quantization

4. **I/O Bottlenecks**:
   - Symptom: Disk activity during inference
   - Solution: Increase RAM to keep models fully in memory

## Reporting Performance Issues

When reporting performance issues, please include:

1. Hardware specifications
2. Reflexia configuration
3. Benchmark results
4. Specific use case details
5. Prometheus metrics (if available)

This information will help diagnose and resolve performance problems efficiently.