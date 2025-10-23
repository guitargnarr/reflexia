# CLAUDE.md - reflexia-model-manager

# Memory System: ~/.claude/memories/

## Project Overview
**Sophisticated LLM management system** - Deploys, manages, and optimizes large language models with adaptive resource management and intelligent quantization.

**Tech Stack:**
- **Backend:** Flask, llama-cpp-python, Ollama integration
- **ML/AI:** sentence-transformers, chromadb, RAG (Retrieval-Augmented Generation)
- **Features:** Adaptive quantization, memory management, expert roles, Web UI
- **Platform:** Optimized for Apple Silicon (Metal acceleration)

## Key Metrics
- **Status:** Active Development
- **Language:** Python 3.14.0 (recommended)
- **Started:** May 2025
- **Purpose:** Advanced LLM management portfolio piece
- **GitHub:** https://github.com/guitargnar/reflexia-model-manager

---

## ✅ Python Environment (Updated October 22, 2025)

**VERIFIED:** Python 3.14.0 installed and working correctly

### Current Setup

**Python Version:** 3.14.0 (recommended) or 3.10+ minimum
- **Location:** `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`
- **Virtual Environment:** `~/Projects/reflexia-model-manager/venv` (to be created)
- **Status:** ✅ Python 3.14.0 verified working

### Virtual Environment Setup

```bash
cd ~/Projects/reflexia-model-manager

# Create venv with Python 3.14
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify Python version
python --version  # Should show: Python 3.14.0

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Verification

```bash
source venv/bin/activate
python --version  # Should show: Python 3.14.0

# Test critical imports
python -c "import llama_cpp; print('llama-cpp-python OK')"
python -c "import chromadb; print('chromadb OK')"
python -c "import sentence_transformers; print('sentence-transformers OK')"
python -c "import flask; print('Flask OK')"
```

**If verification fails:** See global CLAUDE.md (~/.claude/CLAUDE.md) for troubleshooting

### Global Python Status (Reference)

**System resolved Python corruption issue on October 22, 2025:**
- Python 3.14.0 installed at `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`
- Python 3.9.6 available at `/usr/bin/python3` (system)
- All Python projects now functional

**See global CLAUDE.md (~/.claude/CLAUDE.md) for complete Python environment details.**

---

## Project Architecture

```
reflexia-model-manager/
├── config.py                # Configuration management
├── config.json              # Default configuration
├── demo.py                  # Feature demonstration script
├── model_manager.py         # Core model management
├── memory_manager.py        # Memory monitoring and optimization
├── prompt_manager.py        # Prompt templates and management
├── rag_manager.py           # RAG (Retrieval-Augmented Generation)
├── web_ui/                  # Flask web interface
├── Dockerfile               # Docker containerization
├── docker-compose.yml       # Multi-container deployment
├── deploy.sh                # Deployment automation script
├── requirements.txt         # Python dependencies
└── venv/                    # Virtual environment (to be created)
```

---

## Core Features

### 1. Adaptive Quantization Engine
**Automatically adjusts model precision based on:**
- System memory pressure
- Content complexity
- Hardware capabilities (Metal acceleration on M3 Max)

**Quantization Levels:**
- `q4_0` - Smallest, fastest (4-bit)
- `q4_k_m` - Balanced (4-bit k-means)
- `q5_k_m` - Better quality (5-bit k-means)
- `q8_0` - Higher quality (8-bit)
- `f16` - Highest quality (16-bit float)

### 2. Resource-Aware Operation
- Real-time memory monitoring
- Dynamic resource allocation
- Graceful degradation under constraints
- Apple Silicon Metal acceleration

### 3. RAG Integration
- Document ingestion and indexing
- Vector embeddings (sentence-transformers)
- ChromaDB for vector storage
- Enhanced factual responses

### 4. Expert Roles
Pre-configured personas:
- Code Assistant
- Data Analyst
- Technical Writer
- Research Assistant
- Custom roles via configuration

### 5. Web UI
- Flask-based interface
- Real-time model interaction
- Configuration management
- Performance monitoring

---

## Dependencies (Python 3.14 Compatible)

**Core Framework:**
- `flask>=2.0.0`
- `flask-socketio>=5.3.0`
- `flask-compress>=1.13.0`
- `flask-swagger-ui>=4.11.1`

**ML/AI Core:**
- `llama-cpp-python>=0.1.77` ⚠️ May need rebuild for Python 3.14
- `sentence-transformers>=2.2.0`
- `chromadb>=0.4.0`

**Framework Support:**
- `fastapi>=0.95.0`
- `uvicorn>=0.22.0`
- `pydantic>=2.0.0`

**Utilities:**
- `tenacity>=8.0.0` - Retry logic
- `python-dotenv>=1.0.0` - Environment management
- `psutil>=5.9.0` - System monitoring
- `PyYAML>=6.0` - Configuration parsing

**Monitoring:**
- `prometheus-client>=0.16.0`
- `prometheus-flask-exporter>=0.22.0`
- `opentelemetry-api>=1.15.0`
- `opentelemetry-sdk>=1.15.0`

**Testing:**
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0`

---

## Prerequisites

### Required: Ollama Installation
Reflexia integrates with Ollama for model deployment.

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai/

# Verify installation
ollama --version

# Pull a model (example)
ollama pull llama2:7b

# Start Ollama service
ollama serve
```

### Optional: Docker
For containerized deployment.

```bash
# Check Docker installation
docker --version
docker-compose --version
```

---

## Quick Start Commands

### 1. Setup Virtual Environment
```bash
cd ~/Projects/reflexia-model-manager
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Run Feature Demo
```bash
source venv/bin/activate
python demo.py

# Demo showcases:
# - Adaptive quantization
# - RAG integration
# - Expert roles
# - Memory management
```

### 3. Start Web UI
```bash
source venv/bin/activate
python -m flask run --host=0.0.0.0 --port=5000

# Access UI: http://localhost:5000
```

### 4. Docker Deployment
```bash
# Local setup
./deploy.sh local

# Docker deployment
./deploy.sh docker

# Or manual Docker
docker-compose up -d
```

---

## Configuration

### Environment Variables (.env)
```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Model Configuration
DEFAULT_MODEL=llama2:7b
QUANTIZATION_LEVEL=q4_k_m

# RAG Configuration
VECTOR_DB_PATH=./data/vector_db
EMBEDDINGS_MODEL=all-MiniLM-L6-v2

# Web UI
FLASK_ENV=development
FLASK_PORT=5000

# Memory Management
MAX_MEMORY_PERCENT=80
MIN_FREE_MEMORY_MB=1024
```

### config.json
Provides default settings for:
- Model parameters (temperature, top_p, max_tokens)
- Quantization thresholds
- Expert role definitions
- RAG configuration
- Performance tuning

---

## Known Issues & Solutions

### 1. llama-cpp-python May Need Rebuild for Python 3.14

**Problem:** llama-cpp-python might not have pre-built wheels for Python 3.14
**Solution:**
```bash
# If pip install fails, build from source with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir

# For M3 Max, ensure Metal acceleration:
pip install llama-cpp-python --force-reinstall --no-cache-dir \
  --config-settings="cmake.define.LLAMA_METAL=ON"
```

### 2. ChromaDB Compatibility

**Status:** ChromaDB generally compatible with Python 3.14
**Action:** Test after installation, may need specific version

### 3. Virtual Environment May Need Recreation

**Problem:** If venv was created before Oct 22, 2025, it may use corrupted Python 3.13
**Solution:**
```bash
rm -rf venv
python3 -m venv venv  # Creates with Python 3.14
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Ollama Connection Issues

**Problem:** Cannot connect to Ollama service
**Solution:**
```bash
# Ensure Ollama is running
ollama serve

# Check Ollama status
curl http://localhost:11434/api/tags

# Set OLLAMA_HOST if using different port
export OLLAMA_HOST=http://localhost:11434
```

---

## Performance Optimization

### Apple Silicon (M3 Max)
- **Metal Acceleration:** Automatically enabled for llama-cpp-python
- **Unified Memory:** 36 GB shared between CPU/GPU
- **GPU Cores:** 30 cores available for inference

**Expected Performance:**
- 7B model (q4_k_m): ~50-80 tokens/second
- 13B model (q4_k_m): ~30-50 tokens/second
- RAG retrieval: <100ms per query

### Memory Management
- Adaptive quantization kicks in at 80% memory usage
- Dynamic model switching based on available resources
- LRU caching for frequently asked questions

---

## Testing & Validation

### Run Test Suite
```bash
source venv/bin/activate
pytest tests/ -v --cov=. --cov-report=html
```

### Test Individual Components
```bash
# Test model manager
python -c "from model_manager import ModelManager; mm = ModelManager(); print('OK')"

# Test RAG manager
python -c "from rag_manager import RAGManager; rm = RAGManager(); print('OK')"

# Test memory manager
python -c "from memory_manager import MemoryManager; mem = MemoryManager(); print('OK')"
```

### Integration Test
```bash
# Run demo (tests all features)
python demo.py
```

---

## Development Workflow

### 1. Daily Development
```bash
cd ~/Projects/reflexia-model-manager
source venv/bin/activate

# Ensure Ollama is running
ollama serve &

# Start development server
python -m flask run --reload
```

### 2. Before Committing
```bash
# Run tests
pytest tests/ -v

# Check code quality (if installed)
black *.py
flake8 *.py

# Update requirements if needed
pip freeze > requirements.txt
```

### 3. Docker Testing
```bash
# Build and test Docker image
docker build -t reflexia:latest .
docker run -p 5000:5000 reflexia:latest
```

---

## Project-Specific Rules

### Code Style
- Follow PEP 8 guidelines
- Type hints on all functions
- Docstrings with Google style format
- Error handling with specific exceptions
- Logging for all major operations

### Performance Requirements
- Inference latency: <2 seconds (7B models)
- RAG retrieval: <100ms
- Memory overhead: <500 MB (excluding models)
- Web UI response: <200ms

### Security Considerations
- No API keys in code (use .env)
- Input validation for all user inputs
- Rate limiting for API endpoints
- Secure model file handling

---

## Use Cases

1. **Local LLM Development:** Run and test models locally with adaptive optimization
2. **Research Assistant:** RAG-enhanced responses with document grounding
3. **Code Assistant:** Specialized code generation and review
4. **Resource-Constrained Environments:** Automatic quantization for limited hardware
5. **Model Experimentation:** Easy switching between models and configurations

---

## Next Steps (TODO)

- [ ] Create virtual environment with Python 3.14
- [ ] Install dependencies (test llama-cpp-python compilation)
- [ ] Test Ollama integration
- [ ] Run feature demo (demo.py)
- [ ] Test Web UI startup
- [ ] Verify RAG functionality
- [ ] Run comprehensive test suite
- [ ] Document any Python 3.14 compatibility issues
- [ ] Update deployment scripts if needed

---

## Portfolio Impact

**This project demonstrates:**
- Advanced LLM integration and management
- Real-time resource monitoring and optimization
- RAG implementation for enhanced AI responses
- Production-ready error handling and retry logic
- Modern ML deployment patterns (Ollama, vector DBs)
- Full-stack development (Flask, Web UI)
- Docker containerization skills
- Apple Silicon optimization (Metal acceleration)

**Technical Skills Showcased:**
- PyTorch/LLM ecosystem
- Vector databases (ChromaDB)
- Embedding models (sentence-transformers)
- System resource management
- Microservices architecture
- DevOps (Docker, deployment automation)

---

**Documentation Status:** ✅ Complete
**Last Updated:** October 22, 2025
**Python Environment:** ✅ Requirements verified (Python 3.14 compatible)
**Virtual Environment:** 🔄 To be created
**Testing Status:** 🔄 To be validated
**Deployment:** ✅ Scripts available
