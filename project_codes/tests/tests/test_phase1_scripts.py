from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# This file is at project_codes/tests/tests/test_phase1_scripts.py
# parents[3] gets to workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
PYTHON = sys.executable


def test_run_phase1_script_executes():
    result = subprocess.run(
        [PYTHON, str(WORKSPACE_ROOT / "P1_database_check.py")],
        capture_output=True,
        text=True,
        cwd=WORKSPACE_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_merge_products_script_executes():
    result = subprocess.run(
        [PYTHON, str(WORKSPACE_ROOT / "project_codes" / "scripts" / "data" / "merge_products_expiration.py")],
        capture_output=True,
        text=True,
        cwd=WORKSPACE_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr
