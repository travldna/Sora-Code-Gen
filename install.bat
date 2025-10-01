@echo off
title Sora Invite Script Installer

echo ========================================
echo  Sora Invite Code Script - Installer
echo ========================================
echo.

REM Step 1: Check for Python
echo [1/4] Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in your system's PATH.
    echo Please install Python from https://www.python.org/ and try again.
    echo.
    pause
    exit /b
)
echo Python found.
echo.

REM Step 2: Create Virtual Environment
echo [2/4] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b
    )
    echo Virtual environment 'venv' created successfully.
) else (
    echo Virtual environment 'venv' already exists.
)
echo.

REM Step 3: Activate venv and Install Requests
echo [3/4] Activating virtual environment and installing 'requests' library...
call venv\Scripts\activate.bat
pip install requests
if %errorlevel% neq 0 (
    echo ERROR: Failed to install the 'requests' library.
    pause
    exit /b
)
echo 'requests' library installed successfully.
echo.

REM Step 4: Final Instructions
echo [4/4] Installation complete!
echo ========================================
echo  NEXT STEPS:
echo ========================================
echo.
echo 1. Open the 'auth.txt' file and paste your Sora authentication token.
echo 2. Open the 'config.txt' file and paste your OAI-Device-Id and User-Agent.
echo 3. (Optional) Edit 'params.txt' to change script settings like thread count.
echo    (See README.md for detailed instructions on how to get these).
echo 4. Double-click 'run.bat' to start the script.
echo.
echo Press any key to close this window...
pause >nul