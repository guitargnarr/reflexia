# Reflexia Model Manager Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using Reflexia Model Manager.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Problems](#performance-problems)
- [Web UI Issues](#web-ui-issues)
- [RAG Issues](#rag-issues)
- [Docker Issues](#docker-issues)
- [Logs and Debugging](#logs-and-debugging)

## Installation Issues

### Missing Dependencies

**Problem**: Error messages about missing Python packages.

**Solution**:
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# If that doesn't work, try with --force-reinstall
pip install --force-reinstall -r requirements.txt
```

### Ollama Not Found

**Problem**: "Ollama not found" or similar error messages.

**Solution**:
1. Install Ollama from [https://ollama.ai/](https://ollama.ai/)
2. Make sure Ollama is running:
   ```bash
   ollama serve
   ```
3. Check if the required model is pulled:
   ```bash
   ollama list
   # If not present, pull it:
   ollama pull llama3:latest
   ```

## Runtime Errors

### Out of Memory Errors

**Problem**: Application crashes with out of memory errors.

**Solution**:
1. Use a lower quantization setting in config.json:
   ```json
   "model": {
     "quantization": "q4_0"  # Use the most memory-efficient setting
   }
   ```
2. Reduce the context length:
   ```json
   "model": {
     "context_length": 2048  # Lower from the default 4096
   }
   ```
3. Enable adaptive quantization:
   ```json
   "memory": {
     "adaptive_quantization": true
   }
   ```

### Permission Errors

**Problem**: File permission errors when reading or writing files.

**Solution**:
1. Check the ownership of the directories:
   ```bash
   ls -la logs/ vector_db/ models/ cache/
   ```
2. Fix permissions:
   ```bash
   chmod -R 755 logs/ vector_db/ models/ cache/
   ```

## Performance Problems

### Slow Inference

**Problem**: Model responses take too long to generate.

**Solution**:
1. Check if Metal acceleration is enabled on Mac:
   ```json
   "resources": {
     "metal_optimized": true
   }
   ```
2. Use a lighter model quantization if speed is more important than quality:
   ```bash
   # In interactive mode
   system:set_quantization q4_0
   ```
3. Reduce batch size in config.json:
   ```json
   "model": {
     "batch_size": 4  # Lower from default
   }
   ```

### High Memory Usage

**Problem**: Application uses too much memory during operation.

**Solution**:
1. Lower the maximum memory percentage threshold:
   ```json
   "memory": {
     "max_memory_percent": 70  # Lower from default 80
   }
   ```
2. Reduce cache size:
   ```json
   "memory": {
     "cache_size": 64,  # Lower from default
     "lru_cache_size": 32  # Lower from default
   }
   ```

## Web UI Issues

### Web UI Doesn't Start

**Problem**: Web UI fails to start or is not accessible.

**Solution**:
1. Check if the port is already in use:
   ```bash
   lsof -i :8001
   ```
2. Try a different port in config.json:
   ```json
   "web_ui": {
     "port": 8002
   }
   ```
   Or via environment variable:
   ```bash
   export WEB_UI_PORT=8002
   ```
3. Make sure Flask and Socket.IO are installed:
   ```bash
   pip install flask flask-socketio
   ```

### Socket Connection Issues

**Problem**: Web UI loads but real-time updates don't work.

**Solution**:
1. Check browser console for errors
2. Try disabling CORS in config.json:
   ```json
   "web_ui": {
     "cors_enabled": false
   }
   ```
3. Update Socket.IO client library in web_ui/static/

## RAG Issues

### Document Loading Failures

**Problem**: Documents fail to load into the RAG system.

**Solution**:
1. Check if ChromaDB is installed:
   ```bash
   pip install chromadb sentence-transformers
   ```
2. Make sure the vector_db directory exists and is writable
3. Try a different document format (PDF may work when DOCX fails)

### Poor RAG Responses

**Problem**: RAG responses don't seem to use document knowledge.

**Solution**:
1. Increase the chunk overlap in config.json:
   ```json
   "rag": {
     "chunk_overlap": 300  # Higher overlap can capture more context
   }
   ```
2. Increase top_k for more document matches:
   ```json
   "rag": {
     "similarity_top_k": 5  # More documents to consider
   }
   ```

## Docker Issues

### Container Fails to Start

**Problem**: Docker container exits immediately after starting.

**Solution**:
1. Check the container logs:
   ```bash
   docker logs reflexia
   ```
2. Make sure volumes are mounted correctly in docker-compose.yml
3. Verify the Ollama container is running and accessible:
   ```bash
   docker ps | grep ollama
   ```

### GPU Not Detected

**Problem**: GPU acceleration not working in Docker.

**Solution**:
1. Make sure NVIDIA Container Toolkit is installed
2. Confirm GPU drivers are up to date
3. Use the docker-gpu deployment method:
   ```bash
   ./deploy.sh docker-gpu
   ```

## Logs and Debugging

### Enabling Debug Logs

To get more detailed logs for troubleshooting:

1. In code:
   ```python
   import logging
   logging.getLogger("reflexia-tools").setLevel(logging.DEBUG)
   ```

2. Via environment variable:
   ```bash
   export LOG_LEVEL=DEBUG
   ```

3. In .env file:
   ```
   LOG_LEVEL=DEBUG
   ```

### Checking Logs

Log files are stored in the logs/ directory. To view recent errors:

```bash
tail -f logs/reflexia-tools-*.log
```

### Monitoring Memory Usage

To monitor memory usage in real-time:

```bash
# In interactive mode
status
memory
```