"""
Django settings for personal_finance project.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

env = os.environ.get("ENV", "development")
load_dotenv(BASE_DIR / f".env.{env}")

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    # Local apps
    "finance",
    "users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:5174,http://127.0.0.1:5175"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "utils.renderers.UnifiedJSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "config.pagination.ElementPlusPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "utils.exception_handler.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "Personal Finance API",
    "DESCRIPTION": "个人财务 API 文档",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_MINUTES", default=60, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_DAYS", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =========================================================================
# Logging
# =========================================================================
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = config("LOG_LEVEL", default="INFO" if not DEBUG else "DEBUG")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "[{asctime}] {levelname:7s} {name:30s} "
                "{funcName}:{lineno:4d} | {message}"
            ),
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{asctime}] {levelname:7s} {name:20s} | {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "simple",
        },
        "file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
        "file_error": {
            "level": "WARNING",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 90,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
        "file_sql": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": LOG_DIR / "sql.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Django internals — always INFO to suppress verbose autoreload spam
        "django": {
            "handlers": ["console", "file", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # SQL queries (DEBUG only, separate file)
        "django.db.backends": {
            "handlers": ["file_sql"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        # DRF
        "rest_framework": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # Local apps
        "finance": {
            "handlers": ["console", "file", "file_error"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "users": {
            "handlers": ["console", "file", "file_error"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "utils": {
            "handlers": ["console", "file", "file_error"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
    # Root logger — catches anything not covered above
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
}
