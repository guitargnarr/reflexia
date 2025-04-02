#!/bin/bash
# Script to rename the project directory from "Deekseek Model" to "Reflexia Model Manager"
# and clean up legacy reflexia references

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

set -e  # Exit on any error

echo -e "${BLUE}===== Reflexia Model Manager - Project Directory Renaming =====${NC}"
echo -e "${YELLOW}This script will rename the project directory and clean up legacy references${NC}"
echo -e "${YELLOW}Current directory: $(pwd)${NC}"

# Get the parent directory
PARENT_DIR=$(dirname "$(pwd)")
CURRENT_DIR=$(basename "$(pwd)")
NEW_DIR="Reflexia Model Manager"

if [ "$CURRENT_DIR" != "Deekseek Model" ]; then
    echo -e "${RED}Error: Current directory is '$CURRENT_DIR', not 'Deekseek Model'${NC}"
    echo -e "${RED}Please run this script from the 'Deekseek Model' directory${NC}"
    exit 1
fi

# Check if target directory already exists
if [ -d "$PARENT_DIR/$NEW_DIR" ]; then
    echo -e "${RED}Error: Target directory '$NEW_DIR' already exists${NC}"
    echo -e "${RED}Please remove or rename it first${NC}"
    exit 1
fi

# Step 1: Clean up log files
echo -e "\n${BLUE}Step 1: Cleaning up legacy log files...${NC}"
if [ -d "logs" ]; then
    # Create a backup of old logs
    echo -e "${YELLOW}Creating backup of legacy logs...${NC}"
    mkdir -p logs/legacy_reflexia_logs
    
    # Move reflexia log files to backup directory
    find logs -name "reflexia-tools-*.log*" -type f -exec mv {} logs/legacy_reflexia_logs/ \;
    
    echo -e "${GREEN}Legacy log files moved to logs/legacy_reflexia_logs/${NC}"
else
    echo -e "${YELLOW}No logs directory found. Skipping log cleanup.${NC}"
fi

# Step 2: Rename project directory
echo -e "\n${BLUE}Step 2: Renaming directory...${NC}"
echo -e "${YELLOW}Will rename from '$CURRENT_DIR' to '$NEW_DIR'${NC}"

# Move to parent directory
pushd "$PARENT_DIR" > /dev/null

# Rename the directory
mv "Deekseek Model" "$NEW_DIR"
echo -e "${GREEN}Directory successfully renamed to '$NEW_DIR'${NC}"

# Move back to the renamed directory
popd > /dev/null
cd "$PARENT_DIR/$NEW_DIR"

# Step 3: Create symlink for backward compatibility
echo -e "\n${BLUE}Step 3: Creating backward compatibility symlink (optional)${NC}"
read -p "Create symlink for backward compatibility? (y/n): " create_symlink

if [[ "$create_symlink" =~ ^[Yy]$ ]]; then
    pushd "$PARENT_DIR" > /dev/null
    ln -s "$NEW_DIR" "Deekseek Model"
    echo -e "${GREEN}Symlink created: 'Deekseek Model' -> '$NEW_DIR'${NC}"
    popd > /dev/null
else
    echo -e "${YELLOW}Skipping symlink creation${NC}"
fi

# Step 4: Final steps and instructions
echo -e "\n${BLUE}Step 4: Creating .env file for environment configuration${NC}"
if [ ! -f ".env" ]; then
    cat > .env << EOL
# Reflexia Model Manager Environment Configuration

# Web UI Settings
WEB_UI_HOST=127.0.0.1
WEB_UI_PORT=8000

# Security Settings
ENABLE_AUTH=false
API_KEY=

# Resource Settings
MAX_MEMORY_PERCENT=80
ENABLE_ADAPTIVE_QUANTIZATION=true

# Monitoring Settings
ENABLE_METRICS=true
METRICS_PORT=9090

# Advanced Settings
ENABLE_RECOVERY=true
LOG_LEVEL=INFO
EOL
    echo -e "${GREEN}.env file created with default configuration${NC}"
else
    echo -e "${YELLOW}.env file already exists. Skipping creation.${NC}"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
.env
vector_db/
logs/*.log
logs/*.log.*
cache/
models/
temp/
uploads/

# OS specific
.DS_Store
Thumbs.db
EOL
    echo -e "${GREEN}.gitignore file created${NC}"
else
    echo -e "${YELLOW}.gitignore file already exists. Skipping creation.${NC}"
fi

# Final message
echo -e "\n${GREEN}✅ Project renamed successfully!${NC}"
echo -e "${GREEN}New path: $PARENT_DIR/$NEW_DIR${NC}"
echo -e "\n${YELLOW}To use the web UI:${NC}"
echo -e "${GREEN}python main.py --web --rag${NC}"
echo -e "\n${YELLOW}To use interactive mode:${NC}"
echo -e "${GREEN}python main.py --interactive --rag${NC}"
echo -e "\n${YELLOW}To verify the installation:${NC}"
echo -e "${GREEN}python -c \"from utils import check_dependencies; check_dependencies()\"${NC}"