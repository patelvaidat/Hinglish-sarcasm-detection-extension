#!/bin/bash

# Startup script for the Sarcasm Detection Backend
set -e

echo "=========================================="
echo "Sarcasm Detection API - Startup"
echo "=========================================="
echo ""

# Determine project root and backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv311"

echo "Project root: $PROJECT_ROOT"
echo "Backend directory: $SCRIPT_DIR"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "WARNING: Virtual environment not found at $VENV_PATH"
    echo "Please create it with: python3.11 -m venv venv311"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Check if model exists
if [ ! -d "$SCRIPT_DIR/saved_model" ]; then
    echo "WARNING: saved_model directory not found!"
    echo "Please place your trained model in: $SCRIPT_DIR/saved_model/"
    echo "Required files:"
    echo "  - config.json"
    echo "  - model.safetensors (or pytorch_model.bin)"
    echo "  - tokenizer.json"
    echo "  - tokenizer_config.json"
    echo ""
    echo "You can download a test model with: python download_test_model.py"
    exit 1
fi

# Create necessary directories
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/reports"
mkdir -p "$SCRIPT_DIR/data"

# Check port availability
PORT=8000
if command -v lsof >/dev/null 2>&1; then
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "WARNING: Port $PORT is already in use!"
        echo "Please stop the existing process or use a different port"
        exit 1
    fi
fi

# Set model path
export MODEL_PATH="$SCRIPT_DIR/saved_model"

# Start the server
echo ""
echo "=========================================="
echo "Starting API server on port $PORT..."
echo "=========================================="
echo ""
echo "API will be available at: http://localhost:$PORT"
echo "API documentation: http://localhost:$PORT/docs"
echo "Model path: $MODEL_PATH"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$SCRIPT_DIR"
uvicorn main:app --host 0.0.0.0 --port $PORT --reload
