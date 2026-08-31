#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ -x ./venv/Scripts/python ]]; then
  PY=./venv/Scripts/python
elif [[ -x ./venv/bin/python ]]; then
  PY=./venv/bin/python
else
  echo "venv not found. Run ./setup.sh or setup.bat first."
  exit 1
fi

mkdir -p ./staticfiles/logs
PYTHONPATH=. "$PY" src/main.py
