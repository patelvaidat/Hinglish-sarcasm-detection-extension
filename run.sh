#!/bin/bash

# Master setup and run script for Sarcasm Detection System

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv311"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     SARCASM DETECTION SYSTEM - SETUP & RUN SCRIPT         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print status
status() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python version
echo ""
echo "Checking Python version..."
PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
status "Python $PYTHON_VERSION found"

# Step 1: Create virtual environment if needed
echo ""
echo "Setting up virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating new virtual environment at $VENV_PATH..."
    python3.11 -m venv "$VENV_PATH"
    status "Virtual environment created"
else
    status "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"
status "Virtual environment activated"

# Step 2: Install dependencies
echo ""
echo "Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --upgrade pip --quiet
    pip install -r "$BACKEND_DIR/requirements.txt" --quiet
    status "Dependencies installed"
else
    status "Dependencies already installed"
fi

# Step 3: Check for model
echo ""
echo "Checking for trained model..."
if [ ! -d "$BACKEND_DIR/saved_model" ] || [ -z "$(ls -A "$BACKEND_DIR/saved_model")" ]; then
    warning "No model found in $BACKEND_DIR/saved_model/"
    echo ""
    echo "Download a test model? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Downloading test model..."
        cd "$BACKEND_DIR"
        python download_test_model.py
        cd "$PROJECT_ROOT"
        status "Test model downloaded"
    else
        echo ""
        error "Model is required to run the backend. Please place model files in $BACKEND_DIR/saved_model/"
    fi
else
    status "Model found at $BACKEND_DIR/saved_model/"
fi

# Step 4: Create required directories
echo ""
echo "Creating required directories..."
mkdir -p "$BACKEND_DIR/logs"
mkdir -p "$BACKEND_DIR/reports"
mkdir -p "$BACKEND_DIR/data"
status "Directories ready"

# Step 5: Check port availability
echo ""
echo "Checking port 8000 availability..."
PORT=8000
if command -v lsof >/dev/null 2>&1; then
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        error "Port $PORT is already in use. Please stop the process using this port."
    fi
fi
status "Port 8000 is available"

# Step 6: Set environment
echo ""
echo "Setting up environment variables..."
export MODEL_PATH="$BACKEND_DIR/saved_model"
status "MODEL_PATH=$MODEL_PATH"

# Step 7: Start backend
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              STARTING BACKEND SERVER                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Starting Uvicorn server..."
echo "  Host: 0.0.0.0"
echo "  Port: 8000"
echo "  Model: $MODEL_PATH"
echo ""
echo "Access the API at:"
echo "  • http://localhost:8000"
echo "  • http://localhost:8000/docs (interactive docs)"
echo "  • http://localhost:8000/health (health check)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$BACKEND_DIR"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
