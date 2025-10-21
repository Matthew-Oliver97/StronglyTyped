#!/bin/bash

# This script automates the setup and execution of the P2P typing game.
# It ensures a clean environment by recreating the virtual environment on each run.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# The name of the virtual environment directory.
VENV_DIR="wormhole_venv"
# The Python script to run.
GAME_SCRIPT="typing_game.py"
# The path to the Homebrew Python interpreter (for Apple Silicon Macs).
# If you have an Intel Mac, change this to /usr/local/bin/python3
PYTHON_CMD="/opt/homebrew/bin/python3"


# --- Script Logic ---

# 1. Check if the Homebrew Python command exists.
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "Error: Homebrew Python not found at '$PYTHON_CMD'"
    echo "Please make sure Homebrew is installed and you've run 'brew install python3'."
    exit 1
fi

# 2. Force a clean slate by removing the old virtual environment if it exists.
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment for a clean start..."
    rm -rf "$VENV_DIR"
fi

# 3. Create a new virtual environment.
echo "Creating a fresh Python virtual environment..."
"$PYTHON_CMD" -m venv "$VENV_DIR"

# --- Use Explicit Paths to Virtual Environment Executables ---
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# 4. Install the required package into the new environment.
# Since we create a fresh venv every time, we always need to install.
echo "Installing 'paho-mqtt' package..."
"$VENV_PIP" install paho-mqtt

# 5. Run the game using the explicit path to the venv's Python interpreter.
echo "Starting the typing game..."
"$VENV_PYTHON" "$GAME_SCRIPT"

# 6. No 'deactivate' is needed because we didn't 'source' the 'activate' script.
echo "Game has ended."

