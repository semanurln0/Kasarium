"""Top-level pytest configuration to prepare Django before tests import models.

This file sets environment variables and adjusts sys.path so pytest-django
can import the Django settings module and initialise the app registry
before test modules import Django models at import time.
"""
import os
import sys
from pathlib import Path

# Ensure pytest-django sees the test settings module early
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasarium.settings.test")
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")

# Add the Django project directory to sys.path so `import kasarium` works
workspace_root = Path(__file__).resolve().parent
django_dir = workspace_root / "project_codes" / "django"
if str(django_dir) not in sys.path:
    sys.path.insert(0, str(django_dir))

# IMPORTANT: Do NOT call `django.setup()` here. Let pytest-django manage
# Django initialization and test database creation. Calling setup() too
# early can cause the test DB lifecycle to be bypassed and lead to
# "no such table" OperationalError during tests.
