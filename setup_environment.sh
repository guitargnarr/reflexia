#!/bin/bash
# Reflexia Model Manager - Environment Setup Script
# Creates virtual environment and installs all dependencies

set -e  # Exit on error

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$PROJECT_DIR/reflexia-venv"

echo "🔧 Reflexia Model Manager - Environment Setup"
echo "=============================================="
echo ""

# Step 1: Deactivate any existing virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Deactivating current virtual environment: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

# Step 2: Create virtual environment
if [[ -d "$VENV_DIR" ]]; then
    echo "📁 Virtual environment already exists at: $VENV_DIR"
    echo "   Use it with: source reflexia-venv/bin/activate"
else
    echo "📦 Creating virtual environment..."
    /usr/bin/python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created: $VENV_DIR"
fi

# Step 3: Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"

# Step 4: Upgrade pip
echo ""
echo "⬆️  Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel --quiet
echo "✅ Package managers upgraded"

# Step 5: Install dependencies
echo ""
echo "📚 Installing dependencies from requirements.txt..."
if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
    pip install -r "$PROJECT_DIR/requirements.txt" --quiet
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, installing minimal testing dependencies..."
    pip install pytest pytest-cov pytest-mock --quiet
    echo "✅ Testing dependencies installed"
fi

# Step 6: Verify installation
echo ""
echo "🧪 Verifying pytest installation..."
pytest --version
echo ""

# Step 7: Show next steps
echo "=============================================="
echo "✅ Environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate the environment:"
echo "      source reflexia-venv/bin/activate"
echo ""
echo "   2. Run tests:"
echo "      pytest tests/ -v"
echo ""
echo "   3. Run tests with coverage:"
echo "      pytest tests/ --cov=. --cov-report=html"
echo ""
echo "   4. Deactivate when done:"
echo "      deactivate"
echo "=============================================="
