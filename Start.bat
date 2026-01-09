@echo off
setlocal enabledelayedexpansion

echo ============================================
echo Tonys Redfin Zillow Image Downloader v1.8.3
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed!
    python --version
    goto :install_packages
)

echo Python is not installed. Installing Python...
echo.

REM Download Python installer
set PYTHON_VERSION=3.12.0
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set INSTALLER=python-installer.exe

echo Downloading Python %PYTHON_VERSION%...
powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'}"

if not exist %INSTALLER% (
    echo Failed to download Python installer.
    echo Please manually install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing Python (this may take a few minutes)...
%INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

REM Wait for installation to complete
timeout /t 10 /nobreak >nul

REM Refresh PATH
call refreshenv >nul 2>&1

REM Delete installer
del %INSTALLER%

REM Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Python installation completed, but Python is not in PATH.
    echo Please restart your computer and run this script again.
    pause
    exit /b 1
)

echo Python installed successfully!
python --version
echo.

:install_packages
echo.
echo ============================================
echo Setup complete starting downloader...
echo ============================================
echo.

REM Run the script
python redfin_gui.py
