"""Test settings: use SQLite in-memory so tests run without PostgreSQL."""
from .base import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

WORK_HOURS_ENFORCEMENT = False
