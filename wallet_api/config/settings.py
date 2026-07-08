from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)




# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", False) == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost, 127.0.0.1").split(",")

AUTH_USER_MODEL = "wallet.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
     "django_apscheduler",

    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'drf_spectacular_sidecar',

    'wallet.apps.WalletConfig',
    'loans.apps.LoansConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("POSTGRES_DB", "wallet_db"),
        'USER': os.environ.get("POSTGRES_USER", "wallet_user"),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", ""),
        'HOST': os.environ.get("POSTGRES_HOST", "localhost"),
        'PORT': os.environ.get("POSTGRES_PORT", "5432"),
        'OPTIONS': {'sslmode': 'prefer'},
        'CONN_MAX_AGE': 60
    }
}

if DEBUG:
    _db = DATABASES["default"]
    print(f"[settings] DB -> {_db['USER']}@{_db['HOST']}:{_db['PORT']}/{_db['NAME']}")


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    #"EXCEPTION_HANDLER": "wallet.utils.custom_exception_handler",
}

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ["DJANGO_SECRET_KEY"],
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE":   "Wallet API",
    "DESCRIPTION": (
        "A digital wallet system with KYC, funding, withdrawals, "
        "intra-wallet transfers, and a loan service.\n\n"
        "## Authentication\n"
        "1. `POST /api/auth/register/` — create account (auto-creates wallet)\n"
        "2. `POST /api/auth/login/` — get JWT tokens\n"
        "3. Click **Authorize**, enter `Bearer <access_token>`\n"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST":         "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST":              "SIDECAR",

    # map each model's status choices to a clearly named enum
    "ENUM_NAME_OVERRIDES": {
        "TransactionStatusEnum": "wallet.models.TransactionStatus",
        "TransactionTypeEnum": "wallet.models.TransactionType",
        "LoanStatusEnum": "loans.models.LoanStatus",
        "RepaymentStatusEnum": "loans.models.RepaymentStatus",
    },

    "OPERATION_ID_MAP": {
        ("GET", "/api/loans/{id}"): "loans_detail_retrieve",
    },
}

_hex = os.environ.get("AES_ENCRYPTION_KEY", "")
if len(_hex) != 64:
    raise ValueError(
        "AES_ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes / AES-256). "
        "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
AES_ENCRYPTION_KEY = bytes.fromhex(_hex)
 
DEFAULT_INTEREST_RATE = float(os.environ.get("DEFAULT_INTEREST_RATE", "5.0"))
# MAX_LOAN_AMOUNT = float(os.environ.get("MAX_LOAN_AMOUNT", "1000000.00"))
# MIN_LOAN_AMOUNT = float(os.environ.get("MIN_LOAN_AMOUNT", "5000.00"))

EMAIL_HOST = os.environ.get("EMAIL_HOST", "sandbox.smtp.mailtrap.io")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "2525"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@walletapi.dev")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
os.makedirs(BASE_DIR / "logs", exist_ok=True)

LOG_ARCHIVE_AFTER_SECONDS = int(os.environ.get("LOG_ARCHIVE_AFTER_SECONDS", "30"))
LOG_ARCHIVE_INTERVAL_SECONDS = int(os.environ.get("LOG_ARCHIVE_INTERVAL_SECONDS", "30"))

TRANSACTION_LIVE_LOG_FILE = os.environ.get(
    "TRANSACTION_LIVE_LOG_FILE", "logs/transactions_live.log"
)

TRANSACTION_ARCHIVED_LOG_FILE = os.environ.get(
    "TRANSACTION_ARCHIVED_LOG_FILE", "logs/transactions_archived.log"
)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "json": {
            "()": "wallet.logging_formatter.WalletJsonFormatter",
        },
        "txn_json": {
            "()": "wallet.logging_formatter.WalletTransactionLogFormatter",
        },
    },

    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/wallet.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
            "formatter": "json",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "txn_live_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / TRANSACTION_LIVE_LOG_FILE,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
            "formatter": "json",
        },
        "txn_archived_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / TRANSACTION_ARCHIVED_LOG_FILE,
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
            "formatter": "txn_json",
        },
    },

    "loggers": {
        "wallet_audit": {
            "handlers": ["file", "console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "wallet_txn_live": {
            "handlers": ["txn_live_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "wallet_txn_archived": {
            "handlers": ["txn_archived_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True


