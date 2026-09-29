"""
MERRIGE ERP - Бодит орчны тохиргоо (Production Settings)
PostgreSQL болон бүрэн аюулгүй байдлын тохиргоог ашиглана.
"""

from decouple import config

from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# ------------------------------------------------------------------
# Redis Cache (Production)
# ------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,  # noqa: F405 -- base.py-аас "from .base import *"-ээр ирнэ
    }
}

# ------------------------------------------------------------------
# Production Security
# SECURE_SSL_REDIRECT/SESSION_COOKIE_SECURE/CSRF_COOKIE_SECURE-г env-ээр
# унтраах боломжтой (анхдагч утга=True, бодит аюулгүй байдал хэвээр) —
# энэ нь STEP17 (Docker)-т домэйн/SSL сертификат хараахан байхгүй үед
# docker-compose стек дотроо http://localhost-ээр локал шалгах боломж
# олгоно. Бодит production-д (STEP18) domain+SSL сертификат тохируулснаар
# эдгээрийг унтраах шаардлагагүй болно.
# ------------------------------------------------------------------
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
