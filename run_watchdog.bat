@echo off
REM GPU Watchdog Batch Script
REM This script runs the GPU temperature watchdog using the virtual environment

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Run the GPU watchdog
".venv\Scripts\python.exe" gpu_watchdog.py %*

REM If the program exits, pause to show any error messages
if errorlevel 1 (
    echo.
    echo Program exited with error code %errorlevel%
    pause
)