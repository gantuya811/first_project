"""
MERRIGE ERP - Хөгжүүлэлтийн тохиргоо (Development Settings)
Локал орчинд SQLite ашиглана.
"""

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Хөгжүүлэлтийн орчинд Redis сервер шаардахгүйн тулд local-memory cache
# ашиглана (Production дээр Redis болно, production.py-г үзнэ үү).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Хөгжүүлэлтийн үед имэйлийг консол дээр харуулна
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = [
    "127.0.0.1",
]
