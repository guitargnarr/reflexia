# Reflexia Model Manager Deployment Guide

This guide provides instructions for deploying Reflexia Model Manager in various environments.

## Table of Contents
- [Local Development Environment](#local-development-environment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)

## Local Development Environment

### Prerequisites
- Python 3.8+ installed
- [Ollama](https://ollama.ai/) installed and running
- Git

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/guitargnar/reflexia-model-manager.git
   cd reflexia-model-manager
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Pull a compatible model:
   ```bash
   ollama pull llama3:latest
   ```

5. Run the application:
   ```bash
   ./run.sh interactive  # For interactive mode
   ./run.sh web          # For web UI
   ```

## Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose installed (optional, but recommended)

### Using Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/guitargnar/reflexia-model-manager.git
   cd reflexia-model-manager
   ```

2. Start the service:
   ```bash
   docker-compose up -d
   ```

3. Access the web UI at http://localhost:8001

### Using Docker Only

1. Build the Docker image:
   ```bash
   docker build -t reflexia-model-manager .
   ```

2. Run Ollama container:
   ```bash
   docker run -d --name ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama
   ```

3. Run Reflexia container:
   ```bash
   docker run -d --name reflexia \
     -p 8000:8000 -p 8001:8001 \
     --link ollama \
     -e OLLAMA_HOST=ollama \
     -v ./models:/app/models \
     -v ./cache:/app/cache \
     -v ./vector_db:/app/vector_db \
     -v ./logs:/app/logs \
     reflexia-model-manager
   ```

## Production Deployment

For production environments, we recommend the following additional steps:

1. Set up proper SSL/TLS termination using a reverse proxy like Nginx:
   ```nginx
   server {
       listen 443 ssl;
       server_name reflexia.yourdomain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

2. Set up monitoring using Prometheus and Grafana
3. Implement regular backups of your vector database
4. Configure proper authentication if exposed publicly

## Cloud Deployment

### AWS Deployment

1. Create an EC2 instance with sufficient resources (recommended: at least 8GB RAM, 4 vCPUs)
2. Install Docker and Docker Compose
3. Follow the Docker Compose deployment instructions above
4. Set up an Application Load Balancer with HTTPS support

### Google Cloud Platform

1. Create a VM instance with sufficient resources
2. Install Docker and Docker Compose
3. Follow the Docker Compose deployment instructions above
4. Set up a Cloud Load Balancer with HTTPS support

### Microsoft Azure

1. Create a VM with sufficient resources
2. Install Docker and Docker Compose
3. Follow the Docker Compose deployment instructions above
4. Set up an Application Gateway with HTTPS support

## Environment Variables

Customize your deployment with the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Hostname for the Ollama service | localhost |
| `WEB_UI_PORT` | Port for the web UI | 8001 |
| `PYTHONPATH` | Python module path | /app |
| `LOG_LEVEL` | Logging level | INFO |
| `MAX_MEMORY_PERCENT` | Maximum memory usage threshold | 80 |

## Health Checks

For container orchestration systems, use the following health checks:

- Web UI: `curl -f http://localhost:8001/healthz || exit 1`
- API: `curl -f http://localhost:8000/health || exit 1`