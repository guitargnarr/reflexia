# Reflexia Model Manager Architecture

This document provides an overview of the Reflexia Model Manager architecture, explaining how the different components interact.

## System Architecture

Reflexia is designed as a modular system with several key components that work together:

```
                  ┌───────────────┐
                  │     Client    │
                  │  Applications │
                  └───────┬───────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│               Reflexia Web UI               │
│  ┌─────────────┐  ┌─────────┐  ┌─────────┐  │
│  │  REST API   │  │ Web UI  │  │ Swagger │  │
│  └──────┬──────┘  └────┬────┘  └────┬────┘  │
└─────────┼───────────────┼───────────┼───────┘
          │               │           │
┌─────────▼───────────────▼───────────▼───────┐
│             Core Component Layer            │
│                                             │
│  ┌─────────────┐  ┌─────────┐  ┌─────────┐  │
│  │    Model    │  │ Memory  │  │ Prompt  │  │
│  │   Manager   │◄─┤ Manager │  │ Manager │  │
│  └──────┬──────┘  └─────────┘  └─────────┘  │
│         │                                    │
│         │        ┌─────────┐  ┌─────────┐   │
│         └───────►│   RAG   │  │Recovery │   │
│                  │ Manager │  │ System  │   │
│                  └────┬────┘  └─────────┘   │
└──────────────────────┼──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│             Service Integrations             │
│  ┌─────────────┐  ┌─────────┐  ┌─────────┐  │
│  │   Ollama    │  │ Vector  │  │Prometheus│ │
│  │   Models    │  │   DB    │  │ Metrics  │ │
│  └─────────────┘  └─────────┘  └─────────┘  │
└─────────────────────────────────────────────┘
```

## Component Descriptions

### User Interface Layer

- **REST API**: Provides programmatic access to all Reflexia functionality
- **Web UI**: Browser-based interface for human interaction
- **Swagger UI**: Interactive API documentation and testing interface

### Core Component Layer

- **Model Manager**: Core component responsible for LLM inference with adaptive quantization
- **Memory Manager**: Monitors system resources and manages memory allocation
- **Prompt Manager**: Handles prompt templates and system prompts
- **RAG Manager**: Implements retrieval-augmented generation for enhanced responses
- **Recovery System**: Implements circuit breakers and health monitoring for fault tolerance

### Service Integrations

- **Ollama Models**: Integration with local LLM models via Ollama
- **Vector DB**: Storage for document embeddings (ChromaDB)
- **Prometheus Metrics**: Performance and health monitoring

## Data Flow

1. **User Request**: Initiated through Web UI or API
2. **Input Processing**: Prompt formatting and preprocessing
3. **Resource Evaluation**: Memory and complexity assessment
4. **Adaptive Quantization**: Dynamic model precision adjustment
5. **RAG Enhancement** (optional): Document retrieval and context enrichment
6. **Inference**: Model generation with the selected configuration
7. **Response Delivery**: Formatted response returned to client

## Key Subsystems

### Adaptive Quantization Engine

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Content     │     │   Memory      │     │ Available     │
│  Complexity   │     │   Pressure    │     │ Hardware      │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Decision Engine                          │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────┐   │
│  │Content Analysis│  │Resource Monitor│  │Quality Map │   │
│  └───────────────┘  └───────────────┘  └────────────┘   │
└─────────────────────────────┬─────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│               Quantization Selection                     │
│                                                         │
│   q4_0  ←  q4_k_m  ←  q5_k_m  ←  q8_0  ←  f16          │
│ (fastest)                               (highest quality)│
└─────────────────────────────────────────────────────────┘
```

### RAG System Architecture

```
┌───────────────┐
│   Document    │
│    Upload     │
└───────┬───────┘
        │
        ▼
┌───────────────┐     ┌───────────────┐
│   Text        │     │  Embedding    │
│  Extraction   │────►│   Model       │
└───────────────┘     └───────┬───────┘
                              │
                              ▼
                     ┌───────────────┐
                     │   Vector      │
                     │   Database    │
                     └───────┬───────┘
                             │
        ┌───────────────┐    │
        │    User       │    │
        │    Query      │    │
        └───────┬───────┘    │
                │            │
                ▼            ▼
        ┌───────────────────────┐
        │     Similarity        │
        │      Search           │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │    Context            │
        │   Augmentation        │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │      LLM              │
        │    Inference          │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │    Enhanced           │
        │    Response           │
        └───────────────────────┘
```

## Deployment Architecture

Reflexia supports multiple deployment options:

### Local Development

```
┌───────────────┐
│   Developer   │
│   Machine     │
│               │
│  ┌─────────┐  │
│  │Reflexia │  │
│  │  Code   │  │
│  └────┬────┘  │
│       │       │
│  ┌────▼────┐  │
│  │ Ollama  │  │
│  │ Runtime │  │
│  └─────────┘  │
└───────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────────────┐
│             Docker Host                 │
│                                         │
│  ┌─────────────┐      ┌─────────────┐   │
│  │  Reflexia   │      │   Ollama    │   │
│  │  Container  │◄────►│  Container  │   │
│  └──────┬──────┘      └──────┬──────┘   │
│         │                    │          │
│         │      ┌─────────────▼────┐     │
│         │      │  Docker Volumes  │     │
│         └─────►│   for Models &   │     │
│                │     Data         │     │
│                └──────────────────┘     │
└─────────────────────────────────────────┘
```

### Kubernetes Deployment

```
┌───────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                    │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Reflexia   │  │   Ollama    │  │ Prometheus  │   │
│  │   Pods      │  │    Pods     │  │    Pods     │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                 │         │
│  ┌──────▼────────────────▼─────────────────▼──────┐  │
│  │                 Services                       │  │
│  └──────┬────────────────┬─────────────────┬──────┘  │
│         │                │                 │         │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  │
│  │ Persistent  │  │  ConfigMaps │  │   Ingress   │  │
│  │  Volumes    │  │  & Secrets  │  │ Controllers │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└───────────────────────────────────────────────────────┘
```

## Technology Stack

- **Backend**: Python with Flask for web services
- **LLM Runtime**: Ollama for local model deployment
- **Vector Database**: ChromaDB for document embeddings
- **Embeddings**: Sentence-Transformers for text embeddings
- **Web Interface**: HTML, CSS, JavaScript with Socket.IO for real-time updates
- **Containerization**: Docker and Kubernetes for deployment
- **Monitoring**: Prometheus for metrics collection, Grafana for visualization