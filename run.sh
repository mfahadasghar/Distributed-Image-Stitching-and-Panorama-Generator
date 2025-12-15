#!/bin/bash

# Distributed Image Stitching and Panorama Generator
# Startup script

echo "========================================"
echo "  Image Stitching & Panorama Generator  "
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
echo "Setting up directories..."
mkdir -p uploads outputs

# Run the application
echo ""
echo "Starting server..."
echo "========================================"
python app.py
