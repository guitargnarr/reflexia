# Reflexia Model Manager

<div align="center">
  <img src="web_ui/static/logo.svg" alt="Reflexia Logo" width="150" height="150">
  <p><em>A sophisticated system for deploying, managing, and optimizing large language models with adaptive resource management and intelligent quantization.</em></p>
</div>

<div align="center">
  <a href="#-overview">Overview</a> •
  <a href="#%EF%B8%8F-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</div>

---

## 🔍 Overview

Reflexia Model Manager provides a comprehensive solution for running large language models efficiently on consumer-grade hardware. It automatically adapts model precision based on system conditions and content complexity, ensuring optimal performance and resource utilization.

**Key Differentiators:**

- 🧠 **Adaptive Quantization Engine**: Automatically adjusts model precision based on content complexity and system resources
- 🔄 **Resource-Aware Operation**: Monitors memory usage and adjusts operation in real-time
- 📚 **RAG Integration**: Enhances responses with information from your documents
- 🌐 **Web UI**: Built-in interface for easy interaction
- 👨‍💻 **Expert Roles**: Pre-configured specialized personas for different tasks

## ⚙️ Features

### Model Management
- Integration with Ollama for model deployment and operation
- Support for various model architectures and sizes
- Simplified API for model interaction and management
- RAG integration for improved factual responses

### Adaptive Quantization
- Dynamic precision adjustment based on:
  - System memory pressure
  - Content complexity 
  - Hardware capabilities
- Support for multiple quantization levels:
  - q4_0 (smallest, fastest)
  - q4_k_m, q5_k_m (balanced)
  - q8_0 (higher quality)
  - f16 (highest quality)

### Performance Optimization
- LRU caching of responses for frequently asked questions
- Metal acceleration for Apple Silicon
- Memory monitoring and management
- Content complexity analysis for optimal resource allocation

### Reliability Engineering
- Retry logic with exponential backoff for inference calls
- Comprehensive error handling and reporting
- Graceful degradation under resource constraints

## 🚀 Installation

### Prerequisites

- [Ollama](https://ollama.ai/) installed and running
- Python 3.8+
- MacOS recommended (for Metal acceleration)

### Quick Installation

Use our deployment script for the easiest setup:

```bash
# Clone the repository
git clone https://github.com/guitargnar/reflexia-model-manager.git
cd reflexia-model-manager

# Make the deployment script executable
chmod +x deploy.sh

# Setup local environment
./deploy.sh local

# Or deploy with Docker
./deploy.sh docker
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/guitargnar/reflexia-model-manager.git
cd reflexia-model-manager

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull a compatible model
ollama pull llama3:latest
```

### Docker Installation

```bash
# Clone the repository
git clone https://github.com/guitargnar/reflexia-model-manager.git
cd reflexia-model-manager

# Start with Docker Compose
docker-compose up -d
```

### Pip Installation

```bash
# Install from PyPI (once published)
pip install reflexia-model-manager

# Or install from the local repository
pip install -e .
```

## 📋 Usage

### Quick Start

The easiest way to get started is using the run script:

```bash
# Make the script executable
chmod +x run.sh

# Start interactive mode
./run.sh interactive

# Start web UI
./run.sh web

# Start with RAG enabled
./run.sh rag

# Run benchmarks
./run.sh benchmark

# Run examples
./run.sh examples
```

### Basic API Usage

```python
from reflexia import Config, ModelManager

# Initialize configuration
config = Config()
config.set("model", "name", "llama3:latest")
config.set("model", "quantization", "q4_0")
config.set("model", "context_length", 4096)

# Create model manager
model = ModelManager(config)

# Generate response
response = model.generate_response(
    prompt="Explain quantum computing in simple terms",
    temperature=0.7,
    top_p=0.9
)

print(response)
```

### Command-line Interface

```bash
python main.py --interactive  # Interactive mode
python main.py --web          # Start web UI
python main.py --rag          # Enable RAG
python main.py --benchmark    # Run benchmarks
```

## 📊 How It Works

### Content Complexity Analysis

The system automatically analyzes input text to determine appropriate quantization levels:

<div align="center">
  <table>
    <tr>
      <th>Factor</th>
      <th>Description</th>
      <th>Impact</th>
    </tr>
    <tr>
      <td>Text Length</td>
      <td>Longer texts require more context maintenance</td>
      <td>Higher precision for longer texts</td>
    </tr>
    <tr>
      <td>Technical Terms</td>
      <td>Domain-specific vocabulary detection</td>
      <td>More resources for technical content</td>
    </tr>
    <tr>
      <td>Special Characters</td>
      <td>Code, formulas, and structured text</td>
      <td>Higher precision for code/math</td>
    </tr>
  </table>
</div>

### Adaptive Quantization Flow

```
Input → Content Analysis → Memory Pressure Check → Quantization Selection → Inference → Response
       ↑                    ↑                      ↓
       └── Length           └── System            q4_0 (fastest)
           Technical Terms     Resources          q4_k_m
           Special Chars       Current Usage      q5_k_m
                                                  q8_0
                                                  f16 (highest quality)
```

## 📚 Documentation

- [Usage Guide](docs/usage.md): Detailed usage instructions
- [API Reference](docs/api.md): Full API documentation with architecture diagram
- [Deployment Guide](docs/deployment.md): Deployment instructions for various environments
- [Troubleshooting Guide](docs/troubleshooting.md): Solutions to common issues
- [Examples](examples/): Example code for common use cases
  - [Basic Inference](examples/basic_inference.py)
  - [RAG](examples/rag_example.py)
  - [Web UI](examples/web_ui_example.py)
  - [Adaptive Quantization](examples/adaptive_quantization.py)

## 🔧 MLOps Features

- **Resource Monitoring**: Tracks memory usage and adapts model configuration accordingly
- **Progressive Enhancement**: Can automatically increase quality when resources permit
- **Reliable Operation**: Implements proper retry logic and error handling
- **Performance Metrics**: Collects and reports inference performance data

## 🤝 Contributing

Contributions are welcome! Please check out our [contributing guidelines](CONTRIBUTING.md) to get started.

## 📄 License and Intellectual Property Notice

Reflexia Model Manager is proprietary software with significant protections:

### Usage Rights
- **Personal Use**: Permitted for individual, non-commercial learning and experimentation
- **Commercial Use**: Requires a paid commercial license
- **Distribution**: Not permitted without written authorization

### Legal Protections
- **Copyright**: © 2025 Matthew D. Scott. All rights reserved
- **Proprietary Technology**: The adaptive quantization system and resource management technology are proprietary
- **Confidentiality**: Code, algorithms, and implementation details are confidential information
- **Digital Watermarking**: Outputs contain digital watermarks to identify unauthorized use
- **License Verification**: Built-in license verification prevents unauthorized commercial use
- **Code Obfuscation**: Key algorithms are only available in the commercial version

### Trademark Notice
"Reflexia" and the Reflexia logo are proprietary identifiers of this project and cannot be used without permission.

See the [LICENSE](LICENSE) and [NOTICE](NOTICE) files for complete terms.

For licensing inquiries, partnerships, or permitted use questions: matthewdscott7@gmail.com

## 🙏 Acknowledgements

- The [Ollama](https://ollama.ai/) project for making local LLM deployment easy
- The open source AI community for their excellent models
- All open-source contributors who make projects like this possible
