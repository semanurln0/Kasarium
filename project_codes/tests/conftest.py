"""Pytest configuration: ensure Django settings and apps are initialised for collection.

This avoids collection-time import errors when tests import Django models
before pytest-django is available or configured.
"""
import os
import sys
from pathlib import Path

django_dir = Path(__file__).resolve().parents[2] / "django"
# Add Django directory to path so imports work
# conftest.py is at project_codes/tests/conftest.py; parents[1] -> project_codes
django_dir = Path(__file__).resolve().parents[1] / "django"
if str(django_dir) not in sys.path:
    sys.path.insert(0, str(django_dir))

# Ensure tests use the test settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kasarium.settings.test")
# Ensure testserver is allowed during tests
os.environ.setdefault("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")

# Do not call django.setup() here; let pytest-django handle Django setup and
# database creation so migrations run correctly under pytest.
