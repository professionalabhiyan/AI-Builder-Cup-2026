import os
from pathlib import Path

# BASE_DIR points to backend/; we can reference the root project directory via BASE_DIR.parent
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_PROJECT_DIR = BASE_DIR.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'aeroguard-factorymind-enterprise-secret-2026-x99')
DEBUG = False  # Set to False for production deployment on Cloud Run
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <-- Added for efficient static file serving on Cloud Run
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aeroguard_backend.urls'
AUTH_USER_MODEL = 'core.User'
CORS_ALLOW_ALL_ORIGINS = True

# Point Django to Angular's compiled build directory for templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            ROOT_PROJECT_DIR / 'frontend' / 'dist' / 'aeroguard-factorymind-dashboard',
        ],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'aeroguard_factorymind.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'aeroguard-high-concurrency-cache',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

# Point Django to Angular's compiled static assets
STATICFILES_DIRS = [
    ROOT_PROJECT_DIR / 'frontend' / 'dist' / 'aeroguard-factorymind-dashboard',
]

# Where collectstatic will output bundled static files for WhiteNoise
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'