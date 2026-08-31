#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
  else
    echo "Python not found. Install Python 3.10+ and retry."
    exit 1
  fi
fi

echo "Creating venv..."
"$PYTHON_BIN" -m venv venv

echo "Installing runtime dependencies..."
./venv/Scripts/python -m pip install --upgrade pip 2>/dev/null || ./venv/bin/python -m pip install --upgrade pip
if [[ -x ./venv/Scripts/python ]]; then
  ./venv/Scripts/python -m pip install -r ./requirements-runtime.txt
else
  ./venv/bin/python -m pip install -r ./requirements-runtime.txt
fi

echo "Done. Copy .env.example to src/.env if needed, then run ./run.sh"
