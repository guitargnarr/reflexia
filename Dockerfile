# Multi-stage build for Reflexia Model Manager
# Stage 1: Builder - install dependencies and prepare application
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Only copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with pip
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - copy only what's needed for production
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Set up the Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Create necessary directories and set permissions
RUN mkdir -p models cache logs vector_db uploads output temp && \
    chmod 755 run.sh

# Set environment variables
ENV WEB_UI_HOST=0.0.0.0
ENV WEB_UI_PORT=8000
ENV METRICS_PORT=9090
ENV ENABLE_METRICS=true
ENV ENABLE_RECOVERY=true
ENV OLLAMA_HOST=localhost:11434

# Expose ports
# - 8000: Web UI
# - 9090: Prometheus metrics
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Add volume mounts for persistence
VOLUME ["/app/vector_db", "/app/logs", "/app/models", "/app/uploads"]

# Set default command
ENTRYPOINT ["./run.sh"]
CMD ["web"]

# Metadata
LABEL org.opencontainers.image.title="Reflexia Model Manager"
LABEL org.opencontainers.image.description="A system for deploying, managing and optimizing large language models with adaptive resource management"
LABEL org.opencontainers.image.vendor="Reflexia"
LABEL org.opencontainers.image.url="https://github.com/guitargnar/reflexia-model-manager"
LABEL org.opencontainers.image.documentation="https://github.com/guitargnar/reflexia-model-manager/blob/main/README.md"
LABEL org.opencontainers.image.licenses="MIT"