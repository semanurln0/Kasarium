#!/usr/bin/env bash
set -euo pipefail

echo "Creating virtual environment in .venv..."
python3 -m venv .venv || python -m venv .venv

echo "Activating virtual environment and upgrading pip..."
source .venv/bin/activate
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "requirements.txt not found; skipping pip install."
fi

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "Created .env from .env.example — remember to edit it."
fi

echo "Done. To activate the venv run: source .venv/bin/activate"
