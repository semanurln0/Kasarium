"""Main project runner for Kasarium.

Handles:
- Database setup and migrations
- Django development server startup
- Environment validation
"""
from __future__ import annotations

import sys
import os
import subprocess
import argparse
import time
import webbrowser
from pathlib import Path


def get_workspace_root() -> Path:
    """Get workspace root directory."""
    # Try common-case fixed parent traversal first
    p = Path(__file__).resolve()
    try:
        candidate = p.parents[4]
        manage_py = candidate / "project_codes" / "django" / "manage.py"
        if manage_py.exists():
            return candidate
    except IndexError:
        pass

    # Fallback: walk parents and find the directory that contains project_codes/django/manage.py
    for parent in (p,) + tuple(p.parents):
        manage_py = parent / "project_codes" / "django" / "manage.py"
        if manage_py.exists():
            return parent

    # Last resort: use current working directory
    return Path.cwd()


def setup_django_env():
    """Set up Django environment variables and paths."""
    workspace_root = get_workspace_root()
    django_dir = workspace_root / "project_codes" / "django"
    
    # Add django dir to sys.path so manage.py can be found
    if str(django_dir) not in sys.path:
        sys.path.insert(0, str(django_dir))
    
    # Set Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasarium.settings.dev")


def run_migrations():
    """Run Django migrations."""
    workspace_root = get_workspace_root()
    manage_py = workspace_root / "project_codes" / "django" / "manage.py"
    
    print("Running migrations...")
    result = subprocess.run(
        [sys.executable, str(manage_py), "migrate", "--settings=kasarium.settings.dev"],
        cwd=str(workspace_root / "project_codes" / "django"),
        capture_output=False,
    )
    
    if result.returncode != 0:
        print("Error running migrations")
        return False
    return True


def start_server(port: int = 8000):
    """Start Django development server."""
    workspace_root = get_workspace_root()
    manage_py = workspace_root / "project_codes" / "django" / "manage.py"
    
    print(f"Starting server on port {port}...")
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open(f"http://127.0.0.1:{port}")
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start server
        subprocess.run(
            [sys.executable, str(manage_py), "runserver", f"127.0.0.1:{port}", 
             "--settings=kasarium.settings.dev"],
            cwd=str(workspace_root / "project_codes" / "django"),
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Kasarium project runner")
    parser.add_argument(
        "--setup-db",
        action="store_true",
        help="Run migrations before starting server"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate environment and exit (dry-run)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run server on (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Set up Django environment
    setup_django_env()

    # If user requested a dry-run check, validate environment and exit
    if args.check:
        try:
            import django as _django  # type: ignore
            workspace_root = get_workspace_root()
            manage_py = workspace_root / "project_codes" / "django" / "manage.py"
            if not manage_py.exists():
                print(f"manage.py not found at: {manage_py}")
                sys.exit(2)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Environment check failed: {exc}")
            sys.exit(2)

        print("Environment check passed")
        sys.exit(0)
    
    # Run migrations if requested
    if args.setup_db:
        if not run_migrations():
            sys.exit(1)
    
    # Start server
    start_server(args.port)


if __name__ == "__main__":
    main()
