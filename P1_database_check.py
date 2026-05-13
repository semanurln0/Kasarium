"""Phase 1 runner (database / data pipeline check).

Usage:
    python P1_database_check.py

This runner automatically checks if required packages are installed.
If missing, it installs them before proceeding.

Required packages:
    - pandas>=2.1
    - openpyxl>=3.1
    - python-dateutil>=2.9
    - Django>=4.2,<5.0
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path

# Define required packages for Phase 1
REQUIREMENTS = [
    "pandas>=2.1",
    "openpyxl>=3.1",
    "python-dateutil>=2.9",
    "Django>=4.2,<5.0",
]


def check_and_install_requirements():
    """Check if all required packages are installed. Install missing ones."""
    import importlib.util

    missing = []
    for req in REQUIREMENTS:
        # Extract package name (before version specifier)
        pkg_name = req.split(">")[0].split("<")[0].split("=")[0].strip()
        # Convert hyphens to underscores for import (e.g., python-dateutil -> dateutil)
        import_name = pkg_name.replace("-", "_")

        if importlib.util.find_spec(import_name) is None:
            missing.append(req)

    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing,
            stdout=subprocess.DEVNULL,
        )
        print("Dependencies installed successfully.")
    else:
        print("All required packages are installed.")


if __name__ == "__main__":
    # Check and install requirements first
    check_and_install_requirements()

    # Add workspace root to path so project_codes can be imported
    workspace_root = Path(__file__).resolve().parent
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))

    from project_codes.scripts.data.run_phase1 import main

    main()
