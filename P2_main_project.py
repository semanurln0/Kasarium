"""Required packages (core):
    - Django>=4.2,<5.0
    - gunicorn>=21.2
    - whitenoise>=6.6
    - python-dotenv>=1.0
    - psycopg2-binary>=2.9

Optional packages (for testing):
    - pytest
    - pytest-django>=4.12
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path

# Define required packages for main project
REQUIREMENTS_CORE = [
    "Django>=4.2,<5.0",
    "gunicorn>=21.2",
    "whitenoise>=6.6",
    "python-dotenv>=1.0",
    "psycopg2-binary>=2.9",
]

# Map pip package names to import names used by Python.
IMPORT_NAME_MAP = {
    "Django": "django",
    "python-dotenv": "dotenv",
    "psycopg2-binary": "psycopg2",
}


def check_and_install_requirements():
    """Check if all required packages are installed. Install missing ones."""
    import importlib.util

    missing = []
    for req in REQUIREMENTS_CORE:
        # Extract package name (before version specifier)
        pkg_name = req.split(">")[0].split("<")[0].split("=")[0].strip()
        import_name = IMPORT_NAME_MAP.get(pkg_name, pkg_name.replace("-", "_"))

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

    from project_codes.scripts.main.run import main

    main()
