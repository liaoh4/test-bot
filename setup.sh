#!/usr/bin/env bash
set -e

# ── System dependencies ────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "Homebrew not found. Install it from https://brew.sh and re-run this script."
  exit 1
fi

for pkg in ffmpeg ngrok; do
  if ! command -v "$pkg" &>/dev/null; then
    echo "Installing $pkg..."
    brew install "$pkg"
  else
    echo "$pkg already installed, skipping."
  fi
done

# ── Python version check ───────────────────────────────────────────────────────
PYTHON=$(command -v python3.11 || command -v python3)
PY_VERSION=$("$PYTHON" -c "import sys; print(sys.version_info[:2])")
if [[ "$PY_VERSION" < "(3, 11)" ]]; then
  echo "Python 3.11+ required. Found: $($PYTHON --version)"
  exit 1
fi

# ── Virtual environment ────────────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt

# ── Environment file ───────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo ".env created from .env.example — fill in your API keys before running."
else
  echo ".env already exists, skipping."
fi

echo ""
echo "Setup complete. Activate the environment with:"
echo "  source .venv/bin/activate"
echo "Then run with:"
echo "  python main.py"
