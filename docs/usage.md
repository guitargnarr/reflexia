# Reflexia Model Manager Usage Guide

This guide provides detailed instructions on how to use Reflexia Model Manager for various tasks.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Interactive Mode](#interactive-mode)
- [Web UI](#web-ui)
- [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
- [Expert Roles](#expert-roles)
- [Batch Processing](#batch-processing)
- [Fine-tuning](#fine-tuning)
- [Advanced Configuration](#advanced-configuration)

## Installation

Before using Reflexia Model Manager, you need to install it and its dependencies:

```bash
# Clone the repository
git clone https://github.com/guitargnarr/reflexia-model-manager.git
cd reflexia-model-manager

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

Additionally, you need to have [Ollama](https://ollama.ai/) installed and running:

```bash
# Check if Ollama is running
ollama list

# Pull a compatible model
ollama pull llama3:latest
```

## Basic Usage

Here's a simple example of how to use Reflexia Model Manager in your Python code:

```python
from reflexia import Config, ModelManager

# Initialize configuration
config = Config()
config.set("model", "name", "llama3:latest")
config.set("model", "quantization", "q4_0")
config.set("model", "context_length", 4096)

# Create model manager
model = ModelManager(config)

# Generate a response
response = model.generate_response(
    prompt="Explain quantum computing in simple terms",
    temperature=0.7,
    top_p=0.9
)

print(response)
```

## Interactive Mode

You can run Reflexia Model Manager in interactive mode using the command-line interface:

```bash
python main.py --interactive
```

This will start an interactive session where you can chat with the model.

### Interactive Mode Commands

In interactive mode, you can use the following commands:

- `exit` or `quit`: Exit the application
- `help`: Show help message
- `benchmark`: Run benchmarking tests
- `system:X`: Set system prompt to X
- `clear`: Clear the screen
- `status`: Show current system status
- `memory`: Show memory usage details
- `list`: List available documents in the knowledge base
- `info`: Show information about the current model

## Web UI

Reflexia Model Manager includes a web-based user interface:

```bash
python main.py --web
```

This will start a web server at http://127.0.0.1:8000 by default. You can interact with the model through your web browser.

### Web UI Features

- Chat interface with streaming responses
- Expert role selection
- System prompt customization
- Document upload for RAG
- Memory usage monitoring
- Response time tracking

## RAG (Retrieval-Augmented Generation)

RAG enhances responses by retrieving relevant information from documents:

```bash
# Enable RAG in interactive mode
python main.py --interactive --rag
```

### Adding Documents to RAG

In interactive mode, use the `load:` command:

```
> load:path/to/document.pdf
```

In Python code:

```python
from reflexia import Config, ModelManager, RAGManager

config = Config()
model_manager = ModelManager(config)
rag_manager = RAGManager(config, model_manager)

# Load a document
rag_manager.load_file("path/to/document.pdf")

# Generate a RAG-enhanced response
result = rag_manager.generate_rag_response(
    query_text="What is the main point of the document?",
    system_prompt="Provide a concise summary based on the context."
)

print(result["response"])
print("\nSources:")
for source in result["sources"]:
    print(f"- {source}")
```

## Expert Roles

Reflexia Model Manager includes a variety of expert roles for specialized tasks:

```python
from reflexia import Config, ModelManager, PromptManager

config = Config()
model_manager = ModelManager(config)
prompt_manager = PromptManager(config)

# List available expert roles
roles = prompt_manager.get_expert_roles()
print(f"Available roles: {list(roles.keys())}")

# Get system prompt for a specific role
system_prompt = prompt_manager.get_system_prompt(role="software_engineer")

# Generate a response using an expert role
response = model_manager.generate_response(
    prompt="How do I implement a binary search tree?",
    system_prompt=system_prompt
)

print(response)
```

## Batch Processing

For processing multiple prompts at once:

```bash
python main.py --batch inputs.txt outputs.json
```

The input file should contain one prompt per line. The output will be a JSON file with responses.

## Fine-tuning

You can fine-tune the model with your own data:

```bash
python main.py --finetune path/to/dataset.json
```

The dataset should be in JSONL format with "prompt" and "response" fields.

## Advanced Configuration

Reflexia Model Manager is highly configurable. You can modify settings through the `config.json` file or programmatically:

```python
from reflexia import Config

config = Config()

# Model settings
config.set("model", "name", "llama3:latest")
config.set("model", "quantization", "q4_k_m")  # Better quality, more memory
config.set("model", "context_length", 8192)
config.set("model", "auto_improve_quality", True)

# Memory settings
config.set("memory", "max_memory_percent", 75)
config.set("memory", "critical_memory_threshold", 85)
config.set("memory", "lru_cache_size", 128)

# RAG settings
config.set("rag", "chunk_size", 1200)
config.set("rag", "chunk_overlap", 250)
config.set("rag", "similarity_top_k", 5)
config.set("rag", "embedding_model", "all-MiniLM-L6-v2")

# Save configuration
config.save_config()
```

### Memory Optimization

Reflexia Model Manager automatically adapts resource usage based on:

1. Available system memory
2. Content complexity
3. Hardware capabilities

For optimal performance on resource-constrained systems, use:

```python
config.set("model", "quantization", "q4_0")  # Smallest, fastest
config.set("memory", "max_memory_percent", 60)
```

For highest quality on powerful systems:

```python
config.set("model", "quantization", "q8_0")  # Higher quality, more memory
config.set("model", "auto_improve_quality", True)
```