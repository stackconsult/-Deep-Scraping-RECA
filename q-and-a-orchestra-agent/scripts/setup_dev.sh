#!/bin/bash
set -e

# setup_dev.sh (Safeguarded)
# Automates the setup of the development environment.

echo "🚀 Starting Development Environment Setup..."

# Change to the directory where the script is located to ensure relative paths work
cd "$(dirname "$0")/.." || exit

# 1. Check/Install Git LFS
if ! command -v git-lfs &> /dev/null; then
    echo "📦 Git LFS not found."
    if command -v brew &> /dev/null; then
         echo "🍺 Attempting to install via Homebrew..."
         # Try installing without sudo first
         if brew install git-lfs; then
             echo "✅ Git LFS installed via Homebrew."
         else
             echo "❌ Homebrew install failed (likely permissions). "
             echo "👉 Please run: 'brew install git-lfs' manually in your terminal, then re-run this script."
             exit 1
         fi
    else
        echo "❌ Homebrew not found. Please install Git LFS manually: https://git-lfs.github.com/"
        exit 1
    fi
else
    echo "✅ Git LFS is already installed."
fi

echo "🔧 Initializing Git LFS..."
git lfs install

# 2. Install Python Dependencies
echo "🐍 Installing Python dependencies..."
# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python."
    exit 1
fi

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found!"
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
else
    echo "⚠️ requirements-dev.txt not found!"
fi

# 3. Setup Pre-commit Hooks
echo "🪝 Setting up Pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
else
    echo "⚠️ 'pre-commit' command not found. Ensure it was installed in the previous step."
    # Attempt to install it explicitly if missing
    pip install pre-commit
    pre-commit install
fi

echo "✅ Environment setup complete! Please restart VS Code to apply extension recommendations."
