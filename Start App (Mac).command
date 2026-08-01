#!/bin/bash
# ---------------------------------------------------------------------------
# Skyline - AI Weather Assistant
# Startup script (macOS)
#
# Double-click this file in Finder to run it. If macOS refuses to open it
# the first time, see INSTRUCTION.md / the Troubleshooting section for how
# to allow it (Right-click -> Open, then confirm).
# ---------------------------------------------------------------------------

# Always run from the folder this script lives in, no matter where it was
# double-clicked from.
cd "$(dirname "$0")"

# Keep the Terminal window open even if something below fails, so the user
# can read the error instead of the window vanishing instantly.
trap 'echo; echo "============================================"; \
      echo "The application has stopped."; \
      echo "If this was unexpected, scroll up to read any error messages,"; \
      echo "or check the Troubleshooting section of INSTRUCTION.md."; \
      echo "============================================"; \
      read -n 1 -s -r -p "Press any key to close this window..."; echo' EXIT

echo "============================================"
echo "  Skyline - AI Weather Assistant"
echo "  Startup script (macOS)"
echo "============================================"
echo

# ---------------------------------------------------------------------------
# 1. Verify Python is installed
# ---------------------------------------------------------------------------
echo "[1/6] Checking for Python..."
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo
    echo "[ERROR] Python was not found on this computer."
    echo
    echo "Please install Python 3.10 or newer from:"
    echo "  https://www.python.org/downloads/"
    echo
    echo "See INSTRUCTION.md, section 1, for full details."
    echo
    exit 1
fi
echo "  Found: $($PYTHON_BIN --version)"
echo

# ---------------------------------------------------------------------------
# 2. Create a virtual environment if it doesn't exist yet
# ---------------------------------------------------------------------------
echo "[2/6] Checking for virtual environment..."
if [ ! -f "venv/bin/activate" ]; then
    echo "  No virtual environment found - creating one now..."
    "$PYTHON_BIN" -m venv venv
    if [ $? -ne 0 ]; then
        echo
        echo "[ERROR] Failed to create the virtual environment."
        echo "See INSTRUCTION.md, section 7, and the Troubleshooting section."
        echo
        exit 1
    fi
    echo "  Virtual environment created."
else
    echo "  Virtual environment already exists."
fi
echo

# ---------------------------------------------------------------------------
# 3. Activate the virtual environment
# ---------------------------------------------------------------------------
echo "[3/6] Activating virtual environment..."
# shellcheck disable=SC1091
source "venv/bin/activate"
if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Could not activate the virtual environment."
    echo "See INSTRUCTION.md, Troubleshooting section."
    echo
    exit 1
fi
echo "  Activated."
echo

# ---------------------------------------------------------------------------
# 4. Install missing dependencies
# ---------------------------------------------------------------------------
echo "[4/6] Checking dependencies (this may take a minute the first time)..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Failed to install dependencies from requirements.txt."
    echo "Check your internet connection and try again."
    echo
    exit 1
fi
echo "  Dependencies OK."
echo

# ---------------------------------------------------------------------------
# 5. Verify the .env file exists
# ---------------------------------------------------------------------------
echo "[5/6] Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "  No .env file found - creating one from .env.example..."
        cp ".env.example" ".env"
        echo
        echo "[ACTION REQUIRED] A new .env file was created for you."
        echo "Open it in VS Code and fill in your real API keys before"
        echo "continuing. See INSTRUCTION.md, section 10-11, for help."
        echo
        exit 1
    else
        echo
        echo "[ERROR] No .env or .env.example file found."
        echo "Cannot continue without configuration. See INSTRUCTION.md."
        echo
        exit 1
    fi
else
    echo "  .env file found."
    if grep -q "your_openweathermap_api_key_here" ".env" 2>/dev/null; then
        echo
        echo "[WARNING] .env still contains a placeholder WEATHER_API_KEY."
        echo "The app will start, but weather lookups will fail until you"
        echo "add a real key. See INSTRUCTION.md, section 11.2."
        echo
    fi
fi
echo

# ---------------------------------------------------------------------------
# 6. Launch the application
# ---------------------------------------------------------------------------
echo "[6/6] Starting Skyline..."
echo
echo "  Once the server starts, open this address in your browser:"
echo "  http://127.0.0.1:5000"
echo
echo "  Press CTRL+C in this window to stop the app."
echo "============================================"
echo

python app.py
