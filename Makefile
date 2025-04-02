.PHONY: help install dev test lint clean docker docker-gpu rename check-branding fix-branding

# Variables
PYTHON = python3
PIP = $(PYTHON) -m pip
TEST = pytest
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Default target
help:
	@echo "Reflexia Model Manager"
	@echo "-----------------------"
	@echo "Available commands:"
	@echo "  make install       Install dependencies"
	@echo "  make dev           Start development server"
	@echo "  make web           Start web UI"
	@echo "  make rag           Start interactive mode with RAG"
	@echo "  make test          Run tests"
	@echo "  make lint          Run linters"
	@echo "  make clean         Clean temporary files"
	@echo "  make docker        Build and start Docker containers"
	@echo "  make docker-gpu    Build and start Docker containers with GPU support"
	@echo "  make rename        Rename project directory to Reflexia Model Manager"
	@echo "  make check-branding Check for remaining DeepSeek references"
	@echo "  make fix-branding   Fix any remaining DeepSeek references"

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# Start development server (interactive mode)
dev:
	./run.sh interactive

# Start web UI
web:
	./run.sh web

# Start interactive mode with RAG
rag:
	./run.sh rag

# Run tests
test:
	$(TEST) tests/

# Run linters
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Clean temporary files
clean:
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf */*/__pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Docker commands
docker:
	./deploy.sh docker

# Docker with GPU support
docker-gpu:
	./deploy.sh docker-gpu

# Rename project directory
rename:
	./rename_project_dir.sh
	
# Check for DeepSeek references
check-branding:
	./scripts/ensure_rebranding.py

# Fix DeepSeek references
fix-branding:
	./scripts/ensure_rebranding.py --fix