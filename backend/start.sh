#!/bin/bash

# Startup script for the Sarcasm Detection Backend

echo "=========================================="
echo "Sarcasm Detection API - Startup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "? Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "? Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "Checking dependencies..."
pip list | grep fastapi > /dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if model exists
if [ ! -d "saved_model" ]; then
    echo "??  Warning: saved_model directory not found!"
    echo "Please place your trained MuRIL model in the saved_model/ directory"
    echo "Required files:"
    echo "  - config.json"
    echo "  - pytorch_model.bin"
    echo "  - tokenizer files"
    exit 1
fi

# Create necessary directories
mkdir -p logs
mkdir -p reports
mkdir -p data

# Check port availability
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "??  Port $PORT is already in use!"
    echo "Please stop the existing process or use a different port"
    exit 1
fi

# Start the server
echo ""
echo "=========================================="
echo "Starting API server on port $PORT..."
echo "=========================================="
echo ""
echo "API will be available at: http://localhost:$PORT"
echo "API documentation: http://localhost:$PORT/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port $PORT --reload
