import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / '.env')

# Core
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

AUTH_USER_MODEL = 'pci_api.APIUser'

# installed App
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular_sidecar',
    'pci_api',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'pci_api.middleware.SecurityHeadersMiddleware',
    'pci_api.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ=True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASSWORD"),
        'HOST': os.environ.get("DB_HOST", "localhost"),
        'PORT': os.environ.get("DB_PORT", "5432"),

        'OPTIONS': {
            'sslmode': 'prefer',
        },
        'CONN_MAX_AGE': 60,
    }
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
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
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
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
        "- PIN never stored (PCI-DSS Req 3.2.1)\n"
        "- JWT HS256, 60-min access tokens\n"
        "- Rate limit: 30 req/min per IP\n"
        "- Masked PAN only in responses/logs (`************1111`)\n"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
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
            'context_processors': [],
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

# Logging
LOG_FILE = os.environ.get("LOG_FILE", "logs/transactions.log")
os.makedirs(os.path.dirname(BASE_DIR / LOG_FILE), exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'pci_json': {
           '()': 'pci_api.logging_formatter.PCIJsonFormatter',
        },
    },
    'handlers': {
        # Roating file handler
        'transaction_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / LOG_FILE,
            'maxBytes': 10 * 1024 * 1024, # 10 MB per file
            'backupCount': 10,
            'encoding': 'utf-8',
            'formatter': 'pci_json',
        },

        # Console handler for development
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'pci_json',
        },
    },
    'loggers': {
        'pci_audit': {
            'handlers': ['transaction_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
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

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

