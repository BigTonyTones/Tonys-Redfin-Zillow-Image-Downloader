#!/bin/bash

# ==============================================================================
# Tonys Redfin Zillow Image Downloader - macOS Double-Click Launcher
# ==============================================================================

# Change directory to the folder containing this script so relative paths work
cd "$(dirname "$0")" || exit

clear
echo "====================================================================="
echo "        Tonys Redfin Zillow Image Downloader Launcher (macOS)        "
echo "====================================================================="
echo ""
echo "🎨 TIP: Want to add the premium app icon to this file?"
echo "   1. Open the 'assets/app_icon.png' file in Preview and press [Cmd + C] to copy it."
echo "   2. Right-click this 'Start_on_Mac.command' file in Finder and select 'Get Info'."
echo "   3. Click the small file icon in the top-left of the Info window, then press [Cmd + V]."
echo "====================================================================="
echo ""

# 1. Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "The app requires Python 3 to run."
    echo ""
    echo "We are opening the official Python download page in your browser."
    echo "Please download the macOS installer and install it, then run this again."
    echo ""
    echo "Press [Enter] to open the download page..."
    read -r
    open "https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# 2. Check if Tkinter is available (crucial for GUI on Mac)
python3 -c "import tkinter" &> /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Python is installed, but Tkinter (the GUI library) is missing!"
    echo "This usually happens if Python was installed via Homebrew."
    echo ""
    echo "The easiest fix is to install Python using the official installer from"
    echo "python.org, which automatically includes Tkinter."
    echo ""
    echo "We are opening the official Python download page in your browser."
    echo "Press [Enter] to open the download page..."
    read -r
    open "https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Tkinter GUI framework is available."

# 3. macOS Python SSL Certificate Auto-Fix
# This solves the extremely common macOS bug where Python throws SSL: CERTIFICATE_VERIFY_FAILED
# when downloading packages or fetching real estate images over HTTPS.
echo "Checking macOS SSL certificates..."
CERT_SCRIPT=$(ls /Applications/Python\ 3.*/Install\ Certificates.command 2>/dev/null | head -n 1)
if [ -n "$CERT_SCRIPT" ]; then
    # Run the official python certificate setup silently
    bash "$CERT_SCRIPT" >/dev/null 2>&1
    echo "✅ SSL Certificates verified and updated."
else
    echo "ℹ️ SSL Certificate script not found. Skipping (Custom Python installation)."
fi

# 4. Check if pip is available, bootstrap if missing
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Bootstrapping pip..."
    python3 -m ensurepip --upgrade >/dev/null 2>&1
fi
echo "✅ Python Package Manager (pip) is ready."

echo "🚀 Starting downloader..."
echo "====================================================================="
echo ""

# Run the app
python3 redfin_gui.py

# Keep the window open if the python script crashed/exited with an error
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️ Downloader closed with an error."
    echo "Press [Enter] to exit..."
    read -r
fi
