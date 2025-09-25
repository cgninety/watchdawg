@echo off
REM Setup script for GPU Watchdog
REM This script creates a virtual environment and installs dependencies

echo Setting up GPU Watchdog...
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install psutil nvidia-ml-py3

if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

REM Create default configuration if it doesn't exist
if not exist "gpu_watchdog_config.json" (
    echo Creating default configuration...
    ".venv\Scripts\python.exe" gpu_watchdog.py --create-config
)

echo.
echo Setup complete! You can now run the watchdog with run_watchdog.bat
echo.
echo Configuration file: gpu_watchdog_config.json
echo Main script: gpu_watchdog.py
echo.
pause