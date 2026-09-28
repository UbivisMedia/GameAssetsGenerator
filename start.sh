#!/usr/bin/env bash
set -e

# Navigate to script directory
cd "$(dirname "$0")"

echo "========================================================"
echo "  Starting GameAssetGenerator Studio"
echo "========================================================"
echo ""

# Detect Python interpreter
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Neither 'python3' nor 'python' was found in PATH!"
    echo "Please install Python 3.10+ (e.g. sudo apt install python3 python3-pip)."
    exit 1
fi

# Activate virtual environment if present
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
fi

echo "Starting with $PYTHON_CMD..."
exec "$PYTHON_CMD" main.py "$@"
