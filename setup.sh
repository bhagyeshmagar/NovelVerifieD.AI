#!/bin/bash
# ================================================================================
# NovelVerified.AI - Setup Script
# Team StrawHats - KDSH 2026 Track A
# ================================================================================
#
# This script sets up the project and runs the verification pipeline.
# Prerequisites: Python 3.10+, pip, Node.js 18+, npm, Ollama
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# ================================================================================

set -e  # Exit on error

echo "============================================================"
echo "NovelVerified.AI - Setup Script"
echo "============================================================"

# Check Python version
echo ""
echo "[1/5] Checking Python version..."
python3 --version || { echo "ERROR: Python 3 not found. Please install Python 3.10+"; exit 1; }

# Create virtual environment if not exists
echo ""
echo "[2/5] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  Created .venv"
else
    echo "  .venv already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
echo ""
echo "[3/5] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
echo ""
echo "[4/5] Installing frontend dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
    echo "  Frontend dependencies installed"
else
    echo "  WARNING: frontend directory not found"
fi

# Check Ollama
echo ""
echo "[5/5] Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "  Ollama found: $(ollama --version)"
    
    # Check if a model is available
    if ollama list | grep -q "mistral\|llama\|phi"; then
        echo "  LLM model found"
    else
        echo "  WARNING: No LLM model found. Install one with:"
        echo "    ollama pull mistral:7b-instruct-q4_0"
    fi
else
    echo "  WARNING: Ollama not found. Install from https://ollama.ai"
    echo "  After installing, run: ollama pull mistral:7b-instruct-q4_0"
fi

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "To run the verification pipeline:"
echo "  source .venv/bin/activate"
echo "  python run_all.py --local --clean"
echo ""
echo "To run the dashboard:"
echo "  Terminal 1: python flask_api/app.py"
echo "  Terminal 2: cd frontend && npm run dev"
echo "  Open: http://localhost:5173"
echo ""
