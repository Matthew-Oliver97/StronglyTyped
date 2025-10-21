#!/bin/bash

# This script automates the setup and execution of the typing game for macOS and Linux.
# It intelligently finds the Python command, creates a clean virtual environment,
# installs dependencies, and runs the game.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
VENV_DIR="game_venv"
GAME_SCRIPT="typing_game.py"
PYTHON_CMD=""

# --- Platform Detection and Python Command Discovery ---
echo "Detecting platform and finding Python 3..."

# Check if running on macOS
if [[ "$(uname)" == "Darwin" ]]; then
    # On macOS, prioritize Homebrew's Python
    if command -v brew &> /dev/null; then
        # Check for Apple Silicon path first
        if [ -x "/opt/homebrew/bin/python3" ]; then
            PYTHON_CMD="/opt/homebrew/bin/python3"
        # Check for Intel path
        elif [ -x "/usr/local/bin/python3" ]; then
            PYTHON_CMD="/usr/local/bin/python3"
        fi
    fi
fi

# If no specific path was found (or not on macOS), fall back to the default python3
if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "Error: python3 command not found."
        echo "Please install Python 3 and make sure it is in your system's PATH."
        exit 1
    fi
fi

echo "Using Python interpreter at: $($PYTHON_CMD -c 'import sys; print(sys.executable)')"

# --- Script Logic ---

# 1. Force a clean slate by removing the old virtual environment if it exists.
if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment for a clean start..."
    rm -rf "$VENV_DIR"
fi

# 2. Create a new virtual environment.
echo "Creating a fresh Python virtual environment..."
"$PYTHON_CMD" -m venv "$VENV_DIR"

# --- Use Explicit Paths to Virtual Environment Executables ---
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# 3. Install the required package into the new environment.
echo "Installing 'paho-mqtt' package..."
"$VENV_PIP" install paho-mqtt

# 4. Run the game using the explicit path to the venv's Python interpreter.
echo "Starting Terminal Velocity..."
"$VENV_PYTHON" "$GAME_SCRIPT"

echo "Game has ended."

