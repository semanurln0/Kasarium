<#
Simple PowerShell script to create a virtual environment and install requirements.
Usage (PowerShell):
  ./scripts/setup_environment.ps1
#>

$ErrorActionPreference = 'Stop'

Write-Host "Creating virtual environment in .venv..."
python -m venv .venv

if (-not (Test-Path -Path ".venv/Scripts/Activate.ps1")) {
    Write-Host "Virtualenv creation may have failed. Check Python installation."
    exit 1
}

Write-Host "Activating virtual environment and upgrading pip..."
. .venv/Scripts/Activate.ps1
python -m pip install --upgrade pip

if (Test-Path -Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
} else {
    Write-Host "requirements.txt not found; skipping pip install."
}

if (-not (Test-Path -Path ".env") -and (Test-Path -Path ".env.example")) {
    Copy-Item -Path ".env.example" -Destination ".env"
    Write-Host "Created .env from .env.example — remember to edit it."
}

Write-Host "Done. To activate the venv in this session run: . .venv/Scripts/Activate.ps1"
