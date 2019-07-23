"""Django settings for d1_schema_scan.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "e^!1&&+7y(=y*$c+c7ofq=5(-z773tp1y$6+h)bvck&eknfa-0"

DEBUG = True

ALLOWED_HOSTS = ["gmn.test.dataone.org", "127.0.0.1", "0.0.0.0", "192.168.1.121"]

INSTALLED_APPS = [
    "d1_schema_scan.app",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
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

ROOT_URLCONF = "d1_schema_scan.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "app/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "d1_schema_scan.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "d1_schema_scan", "db.sqlite3"),
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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/schema_org_static/"

ASGI_APPLICATION = "d1_schema_scan.routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    }
}

MAX_LOG_LINES = 2000

REDIS_HOST = "localhost"
REDIS_PORT = "6379"
REDIS_DB = 0

LOG_LEVEL = "DEBUG"
LOG_FILE_PATH = os.path.join(BASE_DIR, "d1_schema_scan.log")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)-8s %(name)s %(module)s "
            "%(process)d %(thread)d %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        # Write logs to a rotating set of files, much like logrotate.
        "rotating_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE_PATH,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
        # Write logs to stdout. Useful when running via ./manage.py runserver.
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": LOG_LEVEL,
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # The "catch all" logger is at the root of the tree, denoted by ''.
        "": {"handlers": ["rotating_file"], "level": LOG_LEVEL, "propagate": True}
    },
}

PY_BIN_PATH = "/var/local/dataone/schema_org_scan/venv/bin/python"
D1_CHECK_SITE_PATH = "/var/local/dataone/schema_org_scan/venv/bin/d1-check-site"
