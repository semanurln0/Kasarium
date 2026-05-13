import os
from .base import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    import re
    _m = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", DATABASE_URL)
    if _m:
        DATABASES["default"].update({  # noqa: F405
            "ENGINE": "django.db.backends.postgresql",
            "USER": _m.group(1),
            "PASSWORD": _m.group(2),
            "HOST": _m.group(3),
            "PORT": _m.group(4) or "5432",
            "NAME": _m.group(5),
        })

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
