"""
MERRIGE ERP - Суурь тохиргоо (Base Settings)
Энэ файл dev болон prod хоёрын аль алинд нь нийтлэг тохиргоог агуулна.
"""

from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

# ------------------------------------------------------------------
# Замууд
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ------------------------------------------------------------------
# Аюулгүй байдлын үндсэн тохиргоо
# ------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ------------------------------------------------------------------
# Application definition
# ------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.shared",
    "apps.accounts",
    "apps.products",
    "apps.inventory",
    "apps.orders",
    "apps.payments",
    "apps.profits",
    "apps.commissions",
    "apps.reports",
    "apps.notifications",
    "apps.audit",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------------
# Нууц үгийн баталгаажуулалт
# ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "apps.shared.password_validators.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "apps.shared.password_validators.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "apps.shared.password_validators.CommonPasswordValidator",
    },
    {
        "NAME": "apps.shared.password_validators.NumericPasswordValidator",
    },
]

# ------------------------------------------------------------------
# Хэл, цаг бүс (100% Монгол хэл)
# ------------------------------------------------------------------
LANGUAGE_CODE = "mn"
TIME_ZONE = "Asia/Ulaanbaatar"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Static / Media файлууд
# ------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Excel экспорт болон архивын замууд
EXPORTS_ROOT = BASE_DIR / "exports"
ARCHIVES_ROOT = BASE_DIR / "archives"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# Django REST Framework
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        "apps.accounts.permissions.IsPasswordChanged",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.shared.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.shared.exception_handler.merrige_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "120/minute",
        "login": "5/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MERRIGE ERP API",
    "DESCRIPTION": "Борлуулагчийн сүлжээ, бараа, захиалга, агуулах, төлбөр, "
    "ашиг хуваарилалт, шимтгэл, тайлан удирдлагын нэгдсэн систем.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ------------------------------------------------------------------
# Redis Ready (Cache)
# Cache backend-ийг орчноор нь (Development/Production) тусад нь
# тохируулна (SQLite/PostgreSQL-тэй ижил зарчим) — доор development.py,
# production.py-г үзнэ үү.
# ------------------------------------------------------------------
REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/0")

# ------------------------------------------------------------------
# Celery Ready
# ------------------------------------------------------------------
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = config(
    "CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/2"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ------------------------------------------------------------------
# Имэйл (Мэдэгдэлд ашиглана)
# ------------------------------------------------------------------
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default="MERRIGE ERP <no-reply@merrige.mn>"
)

# ------------------------------------------------------------------
# Session / Login
# ------------------------------------------------------------------
LOGIN_URL = "/nevtreh/"
SESSION_COOKIE_AGE = 60 * 60 * 12  # 12 цаг

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "merrige_erp.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
