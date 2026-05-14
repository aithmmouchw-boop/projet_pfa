"""Configuration — MySQL (variables dans .env à la racine du projet)."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = "dev-only-change-me-in-production"

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "appointments",
    "sitepages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# MySQL — socket Unix : définir DB_SOCKET=/chemin/vers/mysql.sock
# Django utilise le socket si HOST est un chemin absolu (voir get_connection_params).
_db_options: dict = {
    "charset": "utf8mb4",
    "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
}

_db_socket = os.environ.get("DB_SOCKET", "").strip()

_db = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": os.environ.get("DB_NAME", "aesculia_db"),
    "USER": os.environ.get("DB_USER", "root"),
    "PASSWORD": os.environ.get("DB_PASSWORD", ""),
    "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "0")),
    "OPTIONS": _db_options,
}

if _db_socket:
    _db["HOST"] = _db_socket
    _db["PORT"] = ""
else:
    _db["HOST"] = os.environ.get("DB_HOST", "127.0.0.1")
    _db["PORT"] = os.environ.get("DB_PORT", "3306")

DATABASES = {"default": _db}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/patient/dashboard/"
LOGOUT_REDIRECT_URL = "/"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@aesculia.local"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
