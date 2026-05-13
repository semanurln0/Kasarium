import sys
import subprocess


def test_run_check_exits_zero():
    """Run `run.py --check` to validate environment checks (dry-run).

    This test expects that the script performs environment validation and
    exits with code 0 when requirements (notably Django) are importable.
    """
    proc = subprocess.run([sys.executable, "P2_main_project.py", "--check"], capture_output=True, text=True)
    # Print outputs to help debugging when test fails
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0
