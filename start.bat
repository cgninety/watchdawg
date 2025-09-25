@echo off
title WatchDAWG - GPU Temperature Monitor
color 0B
echo.
echo =========================================================================
echo                            WATCHDAWG
echo                    GPU Temperature Watchdog for Crypto Mining
echo                        Protects your GPU from overheating!
echo =========================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if this is first run
if not exist "gpu_watchdog_config.json" goto FIRST_SETUP
if not exist ".venv" goto FIRST_SETUP
goto MAIN_MENU

:FIRST_SETUP
echo.
echo [FIRST TIME SETUP]
echo This appears to be your first time running WatchDAWG.
echo Let me set everything up for you...
echo.
pause

echo [1/4] Creating Python virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python is installed and in your PATH
    pause
    exit /b 1
)
echo [OK] Virtual environment created successfully!
echo.

echo [2/4] Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install psutil nvidia-ml-py3
if errorlevel 1 (
    echo ERROR: Failed to install required packages
    pause
    exit /b 1
)
echo [OK] Packages installed successfully!
echo.

echo [3/4] Creating default configuration...
".venv\Scripts\python.exe" gpu_watchdog.py --create-config
echo [OK] Configuration file created!
echo.

echo [4/4] Testing GPU temperature reading...
".venv\Scripts\python.exe" gpu_watchdog.py --dry-run
echo.

echo =========================================================================
echo [OK] SETUP COMPLETE!
echo.
echo Your WatchDAWG is now ready to protect your GPU!
echo Configuration file: gpu_watchdog_config.json
echo.
pause

:MAIN_MENU
cls
echo.
echo =========================================================================
echo                            WATCHDAWG
echo                              MAIN MENU
echo =========================================================================

REM Show current status
echo [CURRENT STATUS]
".venv\Scripts\python.exe" gpu_watchdog.py --dry-run
echo.

REM Show current configuration
echo [CURRENT SETTINGS]
for /f "tokens=2 delims=:" %%a in ('findstr "temp_threshold" gpu_watchdog_config.json') do (
    set temp_setting=%%a
)
for /f "tokens=2 delims=:" %%a in ('findstr "grace_period" gpu_watchdog_config.json') do (
    set grace_setting=%%a
)
echo Temperature Threshold: %temp_setting%C
echo Grace Period: %grace_setting% seconds
echo.

echo ================================================================================
echo.
echo What would you like to do?
echo.
echo [1] Start WatchDAWG (Monitor and protect GPU)
echo [2] Test Mode (Show what would happen, but don't kill processes)
echo [3] Check current GPU temperature
echo [4] Edit temperature threshold
echo [5] View log file
echo [6] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto START_WATCHDOG
if "%choice%"=="2" goto TEST_MODE
if "%choice%"=="3" goto CHECK_TEMP
if "%choice%"=="4" goto EDIT_THRESHOLD
if "%choice%"=="5" goto VIEW_LOG
if "%choice%"=="6" goto EXIT

echo Invalid choice. Please try again.
pause
goto MAIN_MENU

:START_WATCHDOG
cls
echo.
echo =========================================================================
echo                              STARTING WATCHDOG
echo =========================================================================
echo.
echo [!] IMPORTANT INSTRUCTIONS:
echo.
echo 1. Make sure your T-Rex mining software is already running
echo 2. WatchDAWG will monitor GPU temperature every 10 seconds  
echo 3. If temperature exceeds the threshold, it will:
echo    - Send graceful shutdown signal to T-Rex
echo    - Wait 15 seconds for T-Rex to close properly
echo    - Force close if T-Rex doesn't respond
echo 4. Press Ctrl+C to stop the watchdog
echo.
echo =========================================================================
echo Starting WatchDAWG in 5 seconds...
timeout /t 5 >nul
echo.

".venv\Scripts\python.exe" gpu_watchdog.py
echo.
echo WatchDAWG has stopped.
pause
goto MAIN_MENU

:TEST_MODE
cls
echo.
echo =========================================================================
echo                                 TEST MODE
echo =========================================================================
echo.
echo This will show you what WatchDAWG would do without actually killing processes.
echo Setting threshold to 50C to trigger the test...
echo.
pause

".venv\Scripts\python.exe" gpu_watchdog.py --test-mode --temp-threshold 50
echo.
pause
goto MAIN_MENU

:CHECK_TEMP
cls
echo.
echo =========================================================================
echo                           CURRENT GPU STATUS
echo =========================================================================
echo.

".venv\Scripts\python.exe" gpu_watchdog.py --dry-run
echo.
pause
goto MAIN_MENU

:EDIT_THRESHOLD
cls
echo.
echo =========================================================================
echo                        EDIT TEMPERATURE THRESHOLD
echo =========================================================================
echo.
echo Current temperature threshold: %temp_setting%C
echo.
echo Recommended settings:
echo - 70C - Very conservative (safest for GPU)
echo - 75C - Conservative (good for expensive GPUs)
echo - 80C - Moderate (balanced protection)
echo - 85C - Standard (most common setting)
echo - 90C - High (only with excellent cooling)
echo.
set /p new_temp="Enter new temperature threshold (70-90): "

if %new_temp% LSS 60 (
    echo Temperature too low! Minimum is 60C.
    pause
    goto EDIT_THRESHOLD
)
if %new_temp% GTR 95 (
    echo Temperature too high! Maximum is 95C.
    pause
    goto EDIT_THRESHOLD
)

REM Update the config file (simple replacement)
powershell -Command "(Get-Content gpu_watchdog_config.json) -replace '\"temp_threshold\": [0-9.]+', '\"temp_threshold\": %new_temp%.0' | Set-Content gpu_watchdog_config.json"

echo.
echo [OK] Temperature threshold updated to %new_temp%C
echo.
pause
goto MAIN_MENU

:VIEW_LOG
cls
echo.
echo =========================================================================
echo                               LOG FILE
echo =========================================================================
echo.

if exist "gpu_watchdog.log" (
    echo [Last 30 lines of gpu_watchdog.log]
    echo.
    powershell -Command "Get-Content gpu_watchdog.log | Select-Object -Last 30"
) else (
    echo No log file found yet. The log will be created when you start the watchdog.
)

echo.
pause
goto MAIN_MENU

:EXIT
echo.
echo Thank you for using WatchDAWG!
echo Your GPU will thank you too!
echo.
pause
exit

REM Error handling
:ERROR
echo.
echo An error occurred. Please check:
echo 1. Python is installed and in PATH
echo 2. You have an NVIDIA GPU with drivers installed
echo 3. You have internet connection (for initial setup)
echo.
pause
exit /b 1