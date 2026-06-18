import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / '.env', override=True)

# Core
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") #

AUTH_USER_MODEL = 'pci_api.APIUser'

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# installed App
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.admin', # required to manage OAuth2 applications
    'django.contrib.messages',
    'django.contrib.auth',
    'django.contrib.sessions',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'oauth2_provider',
    'drf_spectacular_sidecar',
    'django_apscheduler',

    'pci_api.apps.PciApiConfig',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # required by admin
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # required by admin
    'django.contrib.messages.middleware.MessageMiddleware', # required by admin
    'pci_api.middleware.SecurityHeadersMiddleware', # add security headers to PCI-compliant responses
    'pci_api.middleware.RequestLoggingMiddleware', # Log requests and response (audit middleware)
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ=True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("POSTGRES_DB", os.environ.get("DB_NAME", "")),
        'USER': os.environ.get("POSTGRES_USER", os.environ.get("DB_USER", "")),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", os.environ.get("DB_PASSWORD", "")),
        'HOST': os.environ.get("POSTGRES_HOST", os.environ.get("DB_HOST", "localhost")),
        'PORT': os.environ.get("POSTGRES_PORT", os.environ.get("DB_PORT", "5432")),

        'OPTIONS': {
            'sslmode': 'prefer',
        },
        'CONN_MAX_AGE': 60,
    }
}

if DEBUG:
    print(
        f"[settings] DB target -> "
        f"{DATABASES['default']['USER']}@{DATABASES['default']['HOST']}:"
        f"{DATABASES['default']['PORT']}/{DATABASES['default']['NAME']}"
    )

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [],
    'EXCEPTION_HANDLER': 'pci_api.errors.pci_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ["JWT_SECRET_KEY"],
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# OAuth2 toolkit
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 86400,
    'ROTATE_REFRESH_TOKENS': True,
    'SCOPE': {
        'read': 'Read access to transaction and archive',
        'write': 'Submit new transactions',
    },
    'DEFAULT_SCOPE': ['read', 'write'],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PCI-DSS Secure Transaction API",
    "DESCRIPTION": (
        "REST API demonstrating PCI-DSS card transaction security.\n\n"
        "## How to authenticate\n"
        "1. `POST /api/auth/register/` — create account\n"
        "2. `POST /api/auth/token/` — get access + refresh tokens\n"
        "3. Click **Authorize** (top right), enter `Bearer <access_token>`\n"
        "4. Transaction endpoints are now accessible\n\n"
        "## Security controls\n"
        "- AES-256-GCM encryption at rest (PAN, expiry)\n"
        "- PIN never stored or logged\n"
        "- JWT HS256, 60-min access tokens\n"
        "- Rate limit: 30 req/min per IP\n"
        "- Masked PAN only in responses/logs (`************1111`)\n"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {
        "persistentAuth": True,
        "displayRequestDuration": True,
        "filters": True,
        "deepLinking": True,
    },
    "SERVERS": [{"url": "http://localhost:8000", "description": "Local Server"}],
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Encryption
_hex = os.environ.get("AES_ENCRYPTION_KEY", "")
if len(_hex) != 64:
    raise ValueError(
        "AES_ENCRYPTION_KEY must be a 64-character hex string (32 bytes / AES-256). "
        "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
AES_ENCRYPTION_KEY = bytes.fromhex(_hex)
  
# Api Key
API_KEY = os.environ["API_KEY"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))

ARCHIVE_INTERVAL_SECONDS = int(os.environ.get("ARCHIVE_INTERVAL_SECONDS", "30"))

# Logging
LOG_FILE = os.environ.get("LOG_FILE", "logs/transactions.log")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
os.makedirs(os.path.dirname(BASE_DIR / LOG_FILE), exist_ok=True)

TRANSACTION_LIVE_LOG_FILE = os.environ.get(
    "TRANSACTION_LIVE_LOG_FILE", "logs/transaction_live.log"
)
TRANSACTION_ARCHIVED_LOG_FILE = os.environ.get(
    "TRANSACTION_ARCHIVED_LOG_FILE", "logs/transaction_archived.log"
)

os.makedirs((BASE_DIR / TRANSACTION_LIVE_LOG_FILE).parent, exist_ok=True)
os.makedirs((BASE_DIR / TRANSACTION_ARCHIVED_LOG_FILE).parent, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'pci_json': {
           '()': 'pci_api.logging_formatter.PCIJsonFormatter',
        },
        'transaction_sjon': {
            '()': 'pci_api.logging_formatter.TransactionLogFormatter',
        },
    },
    'handlers': {
        # Rotating file handler
        'transaction_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / LOG_FILE,
            'maxBytes': 10 * 1024 * 1024, # 10 MB per file
            'backupCount': 10,
            'encoding': 'utf-8',
            'formatter': 'pci_json',
        },

        # Console handler for development
        "console": {"class": "logging.StreamHandler", "formatter": "pci_json"},
        "transaction_live_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / TRANSACTION_LIVE_LOG_FILE,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB per file
            "backupCount": 10,
            "encoding": "utf-8",
            "formatter": "transaction_sjon",
        },
        "transaction_archived_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / TRANSACTION_ARCHIVED_LOG_FILE,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB per file
            "backupCount": 10,
            "encoding": "utf-8",
            "formatter": "transaction_sjon",
        },
    },
    'loggers': {
        'pci_audit': {'handlers': ['transaction_file', 'console'], 'level': LOG_LEVEL, 'propagate': False},
        'pci_transaction_live': {'handlers': ['transaction_live_file'], 'level': LOG_LEVEL, 'propagate': False},
        'pci_transaction_archived': {'handlers': ['transaction_archived_file'], 'level': LOG_LEVEL, 'propagate': False},
    },
}

# Security settings
# SECURE_SSL_REDIRECT = False
# SECURE_HSTS_SECONDS = 63072000  # 2 years
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'
# USE_TZ = True

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
SECURE_SSL_REDIRECT = ENVIRONMENT == "production"

if ENVIRONMENT == "production":
    SECURE_HSTS_SECONDS = 63072000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
USE_TZ = True

# STATIC_URL = "/static/"
# STATIC_ROOT = BASE_DIR / "staticfiles"

