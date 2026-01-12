# Reflexia Model Manager

Adaptive LLM management system with intelligent quantization for consumer hardware.

## Overview

Reflexia automatically adapts model precision based on system resources and content complexity, enabling efficient LLM inference without manual tuning. Built for Apple Silicon with Metal acceleration.

**Key Features:**

- **Adaptive Quantization** - Dynamic precision adjustment (q4_0 to f16) based on memory pressure and content complexity
- **Resource-Aware** - Real-time memory monitoring with automatic optimization
- **RAG Integration** - Document-enhanced responses via ChromaDB vector storage
- **Web UI** - Built-in browser interface for interaction
- **Expert Roles** - Pre-configured personas (Code Assistant, Data Analyst, Technical Writer)
- **Circuit Breakers** - Fault-tolerant operation with automatic recovery

## Installation

**Prerequisites:** [Ollama](https://ollama.ai/), Python 3.8+, macOS recommended

### Quick Start

```bash
git clone https://github.com/guitargnarr/reflexia.git
cd reflexia
chmod +x deploy.sh && ./deploy.sh local
```

### Manual Setup

```bash
git clone https://github.com/guitargnarr/reflexia.git
cd reflexia
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3:latest
```

### Docker

```bash
git clone https://github.com/guitargnarr/reflexia.git
cd reflexia && docker-compose up -d
```

## Usage

### Run Modes

```bash
./run.sh interactive  # Interactive CLI
./run.sh web          # Web UI (localhost:5000)
./run.sh rag          # RAG-enabled mode
./run.sh benchmark    # Performance benchmarks
```

### Python API

```python
from reflexia import Config, ModelManager

config = Config()
config.set("model", "name", "llama3:latest")
config.set("model", "quantization", "q4_0")

model = ModelManager(config)
response = model.generate_response(
    prompt="Explain quantum computing",
    temperature=0.7
)
```

### CLI

```bash
python main.py --interactive
python main.py --web
python main.py --rag
```

## How It Works

### Adaptive Quantization

The system analyzes content complexity and available resources to select optimal precision:

| Factor | Impact |
|--------|--------|
| Text Length | Longer texts get higher precision |
| Technical Terms | Domain vocabulary triggers more resources |
| Code/Math | Special characters increase precision |
| Memory Pressure | Low memory forces lower quantization |

**Quantization Levels:** q4_0 (fastest) → q4_k_m → q5_k_m → q8_0 → f16 (highest quality)

### Architecture

```
Client → Web UI/API → Model Manager → Ollama
                    ↓
              Memory Manager (resource monitoring)
                    ↓
              RAG Manager (document retrieval)
                    ↓
              Recovery System (circuit breakers)
```

## Project Structure

```
reflexia/
├── model_manager.py    # Core LLM interface
├── memory_manager.py   # Resource monitoring
├── rag_manager.py      # Document retrieval
├── recovery.py         # Circuit breakers
├── monitoring.py       # Prometheus metrics
├── web_ui.py           # Flask interface
├── config.py           # Configuration
├── docs/               # Detailed documentation
├── examples/           # Usage examples
└── tests/              # Test suite
```

## Documentation

- [Usage Guide](docs/usage.md) - Detailed instructions
- [API Reference](docs/api.md) - Full API documentation
- [Architecture](docs/architecture.md) - System design
- [Deployment](docs/deployment.md) - Production setup
- [Troubleshooting](docs/troubleshooting.md) - Common issues

## Requirements

- Python 3.8+
- Ollama runtime
- macOS (recommended for Metal acceleration)
- 8GB+ RAM recommended

## License

Proprietary software. Personal/educational use permitted; commercial use requires license.

Copyright 2025 Matthew D. Scott. All rights reserved.

See [LICENSE](LICENSE) for full terms. Contact: matthewdscott7@gmail.com
