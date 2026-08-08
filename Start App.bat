@echo off
setlocal enabledelayedexpansion
title Skyline - Weather AI App
cd /d "%~dp0"

echo ======================================================
echo   Skyline - AI Weather Assistant
echo   Startup script (Windows) (Was made by Oleh Datsyk)
echo ======================================================
echo.

REM ------------------------------------------------------------------
REM 1. Verify Python is installed
REM ------------------------------------------------------------------
echo [1/6] Checking for Python...
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found on this computer.
    echo.
    echo Please install Python 3.10 or newer from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: On the first installer screen, check the box that
    echo says "Add python.exe to PATH" before clicking Install.
    echo.
    echo See INSTRUCTION.md, section 1, for full details.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   Found: %%v
echo.

REM ------------------------------------------------------------------
REM 2. Create a virtual environment if it doesn't exist yet
REM ------------------------------------------------------------------
echo [2/6] Checking for virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo   No virtual environment found - creating one now...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to create the virtual environment.
        echo See INSTRUCTION.md, section 7, and the Troubleshooting section.
        echo.
        pause
        exit /b 1
    )
    echo   Virtual environment created.
) else (
    echo   Virtual environment already exists.
)
echo.

REM ------------------------------------------------------------------
REM 3. Activate the virtual environment
REM ------------------------------------------------------------------
echo [3/6] Activating virtual environment...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo.
    echo [ERROR] Could not activate the virtual environment.
    echo See INSTRUCTION.md, Troubleshooting section.
    echo.
    pause
    exit /b 1
)
echo   Activated.
echo.

REM ------------------------------------------------------------------
REM 4. Install missing dependencies
REM ------------------------------------------------------------------
echo [4/6] Checking dependencies (this may take a minute the first time)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies from requirements.txt.
    echo Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo   Dependencies OK.
echo.

REM ------------------------------------------------------------------
REM 5. Verify the .env file exists
REM ------------------------------------------------------------------
echo [5/6] Checking configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo   No .env file found - creating one from .env.example...
        copy /y ".env.example" ".env" >nul
        echo.
        echo [ACTION REQUIRED] A new .env file was created for you.
        echo Open it in VS Code and fill in your real API keys before
        echo continuing. See INSTRUCTION.md, section 10-11, for help.
        echo.
        pause
        exit /b 1
    ) else (
        echo.
        echo [ERROR] No .env or .env.example file found.
        echo Cannot continue without configuration. See INSTRUCTION.md.
        echo.
        pause
        exit /b 1
    )
) else (
    echo   .env file found.
    findstr /C:"your_openweathermap_api_key_here" ".env" >nul
    if not errorlevel 1 (
        echo.
        echo [WARNING] .env still contains a placeholder WEATHER_API_KEY.
        echo The app will start, but weather lookups will fail until you
        echo add a real key. See INSTRUCTION.md, section 11.2.
        echo.
    )
)
echo.

REM ------------------------------------------------------------------
REM 6. Launch the application
REM ------------------------------------------------------------------
echo [6/6] Starting Skyline...
echo.
echo   Once the server starts, open this address in your browser:
echo   http://127.0.0.1:1020
echo.
echo   Press CTRL+C in this window to stop the app.
echo ============================================
echo.

python app.py

REM If app.py exits (crash or Ctrl+C), keep the window open so the
REM user can read any error output before it disappears.
echo.
echo ============================================
echo The application has stopped.
echo If this was unexpected, scroll up to read any error messages,
echo or check the Troubleshooting section of INSTRUCTION.md.
echo ============================================
pause
