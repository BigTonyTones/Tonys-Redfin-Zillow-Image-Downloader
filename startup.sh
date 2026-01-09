#!/bin/bash

echo "============================================"
echo "Tonys Redfin Zillow Image Downloader v1.8.3"
echo "============================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed!"
    echo "Please install Python 3 from https://www.python.org/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed!"
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

echo "Checking dependencies..."
echo ""

# The Python script will handle dependency installation with user permission
# Just run the GUI
echo "============================================"
echo "Setup complete - starting downloader..."
echo "============================================"
echo ""

# Run the script
python3 redfin_gui.py
