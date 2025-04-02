#!/bin/bash
# Reflexia Model Manager deployment script

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display help message
show_help() {
    echo -e "${BLUE}Reflexia Model Manager Deployment Script${NC}"
    echo "Usage: ./deploy.sh [OPTION]"
    echo "Options:"
    echo "  local         Setup local development environment"
    echo "  docker        Deploy using Docker"
    echo "  docker-gpu    Deploy using Docker with GPU support"
    echo "  update        Update existing installation"
    echo "  help          Display this help message"
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
        exit 1
    fi
    
    if ! command -v pip &> /dev/null; then
        echo -e "${RED}pip is not installed. Please install pip.${NC}"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}git is not installed. Please install git.${NC}"
        exit 1
    fi
    
    if [[ "$1" == "docker" || "$1" == "docker-gpu" ]]; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Docker is not installed. Please install Docker.${NC}"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${YELLOW}Warning: docker-compose is not installed. Proceeding with docker only.${NC}"
        fi
    fi
    
    echo -e "${GREEN}All required dependencies are installed.${NC}"
}

# Function to setup local environment
setup_local() {
    echo -e "${BLUE}Setting up local development environment...${NC}"
    
    # Create and activate virtual environment
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo -e "${YELLOW}Ollama is not installed. Please install Ollama from https://ollama.ai/${NC}"
        echo -e "${YELLOW}After installing Ollama, pull the required model with: ollama pull llama3:latest${NC}"
    else
        echo "Checking for required models..."
        MODELS=$(ollama list)
        if [[ ! $MODELS == *"llama3:latest"* ]]; then
            echo "Pulling llama3:latest model..."
            ollama pull llama3:latest
        fi
    fi
    
    echo -e "${GREEN}Local environment setup complete!${NC}"
    echo -e "To start the application:"
    echo -e "  - Interactive mode: ${BLUE}./run.sh interactive${NC}"
    echo -e "  - Web UI: ${BLUE}./run.sh web${NC}"
}

# Function to deploy using Docker
deploy_docker() {
    echo -e "${BLUE}Deploying with Docker...${NC}"
    
    # Check if we need GPU support
    if [[ "$1" == "gpu" ]]; then
        echo "Enabling GPU support..."
        # Create a temporary docker-compose file with GPU support
        sed 's/# deploy:/deploy:/g; s/#   resources:/  resources:/g; s/#     reservations:/    reservations:/g; s/#       devices:/      devices:/g; s/#         - driver: nvidia/        - driver: nvidia/g; s/#           count: all/          count: all/g; s/#           capabilities: \[gpu\]/          capabilities: [gpu]/g' docker-compose.yml > docker-compose.gpu.yml
        COMPOSE_FILE="docker-compose.gpu.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    # Start the containers
    if command -v docker-compose &> /dev/null; then
        echo "Starting services with docker-compose..."
        docker-compose -f $COMPOSE_FILE up -d
    else
        echo "docker-compose not found, using docker commands..."
        
        # Create a network
        docker network create reflexia-network || true
        
        # Start Ollama container
        echo "Starting Ollama container..."
        docker run -d --name ollama \
            --network reflexia-network \
            -p 11434:11434 \
            -v ollama_data:/root/.ollama \
            ollama/ollama
        
        # Start Reflexia container
        echo "Starting Reflexia container..."
        docker run -d --name reflexia \
            --network reflexia-network \
            -p 8000:8000 -p 8001:8001 \
            -e OLLAMA_HOST=ollama \
            -v ./models:/app/models \
            -v ./cache:/app/cache \
            -v ./vector_db:/app/vector_db \
            -v ./logs:/app/logs \
            -v ./uploads:/app/uploads \
            -v ./output:/app/output \
            reflexia-model-manager
    fi
    
    # Cleanup temporary file
    if [[ "$1" == "gpu" && -f "docker-compose.gpu.yml" ]]; then
        rm docker-compose.gpu.yml
    fi
    
    echo -e "${GREEN}Deployment complete!${NC}"
    echo -e "Web UI available at: ${BLUE}http://localhost:8001${NC}"
    echo -e "API available at: ${BLUE}http://localhost:8000${NC}"
}

# Function to update existing installation
update_installation() {
    echo -e "${BLUE}Updating Reflexia Model Manager...${NC}"
    
    # Pull latest changes
    git pull
    
    # Check if we're in a virtual environment
    if [[ -d ".venv" && -f ".venv/bin/activate" ]]; then
        echo "Updating local environment..."
        source .venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Check if we're using Docker
    if command -v docker &> /dev/null && [ -f "docker-compose.yml" ]; then
        echo "Updating Docker deployment..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
    fi
    
    echo -e "${GREEN}Update complete!${NC}"
}

# Main script execution
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    "local")
        check_dependencies "local"
        setup_local
        ;;
    "docker")
        check_dependencies "docker"
        deploy_docker
        ;;
    "docker-gpu")
        check_dependencies "docker-gpu"
        deploy_docker "gpu"
        ;;
    "update")
        update_installation
        ;;
    "help"|*)
        show_help
        ;;
esac