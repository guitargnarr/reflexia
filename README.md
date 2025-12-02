# Reflexia Model Manager

<div align="center">
  <img src="web_ui/static/logo.svg" alt="Reflexia Logo" width="120" height="120">
  <p><em>Adaptive LLM management with intelligent quantization for consumer hardware.</em></p>
</div>

---

## Overview

Reflexia automatically adapts model precision based on system resources and content complexity, enabling efficient LLM inference on consumer-grade hardware.

**Key Features:**
- **Adaptive Quantization**: Dynamic precision adjustment (q4_0 to f16)
- **Resource-Aware**: Real-time memory monitoring and optimization
- **RAG Integration**: Document-enhanced responses
- **Web UI**: Built-in browser interface
- **Expert Roles**: Pre-configured personas for different tasks

## Installation

**Prerequisites:** [Ollama](https://ollama.ai/), Python 3.8+, MacOS recommended

### Quick Start

```bash
git clone https://github.com/guitargnarr/reflexia.git
cd reflexia
chmod +x deploy.sh
./deploy.sh local
```

### Manual Setup

```bash
git clone https://github.com/guitargnarr/reflexia.git
cd reflexia
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3:latest
```

### Docker

```bash
git clone https://github.com/guitargnarr/reflexia.git
cd reflexia
docker-compose up -d
```

## Usage

```bash
./run.sh interactive  # Interactive mode
./run.sh web          # Web UI at localhost:5000
./run.sh rag          # RAG-enabled mode
```

### Python API

```python
from reflexia import Config, ModelManager

config = Config()
config.set("model", "name", "llama3:latest")
model = ModelManager(config)

response = model.generate_response(
    prompt="Explain quantum computing",
    temperature=0.7
)
```

## Documentation

- [Usage Guide](docs/usage.md)
- [API Reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

Proprietary software. Personal use permitted; commercial use requires license.

Copyright 2025 Matthew D. Scott. See [LICENSE](LICENSE) for terms.

Contact: matthewdscott7@gmail.com
