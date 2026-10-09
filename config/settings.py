import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 1. INITIALISATION DE ENVIROUNEMENT
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-hotel-pms-super-secret-key-change-in-production-2026!'),
)

# Read .env file if present
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

# ==============================================================================
# CONFIGURATION POUR ACCÈS DISTANT (RENDER & CLOUDFLARE)
# ==============================================================================

# Lecture dynamique via env
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    'gestion-hoteliere-2jms.onrender.com',
    'consulting-moms-specifications-fill.trycloudflare.com',
    '.trycloudflare.com',
])

# Autoriser les formulaires POST (connexion, admin, etc.)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://*.onrender.com',
    'https://gestion-hoteliere-2jms.onrender.com',
    'https://consulting-moms-specifications-fill.trycloudflare.com',
    'https://*.trycloudflare.com',
])

# Gestion du Proxy HTTPS / Headers SSL
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Configuration des cookies de session pour les requêtes distantes
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# ==============================================================================

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # Local apps (Hotel PMS Modules)
    'accounts.apps.AccountsConfig',
    'dashboard.apps.DashboardConfig',
    'rooms.apps.RoomsConfig',
    'guests.apps.GuestsConfig',
    'reservations.apps.ReservationsConfig',
    'reception.apps.ReceptionConfig',
    'housekeeping.apps.HousekeepingConfig',
    'maintenance.apps.MaintenanceConfig',
    'restaurant.apps.RestaurantConfig',
    'kitchen.apps.KitchenConfig',
    'inventory.apps.InventoryConfig',
    'procurement.apps.ProcurementConfig',
    'cashier.apps.CashierConfig',
    'finance.apps.FinanceConfig',
    'hr.apps.HrConfig',
    'commercial.apps.CommercialConfig',
    'reports.apps.ReportsConfig',
    'notifications.apps.NotificationsConfig',
    'audit.apps.AuditConfig',
    'common.apps.CommonConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',  # Traçabilité intégrale
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'common.context_processors.hotel_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# DATABASE CONFIGURATION (CORRIGÉE POUR RENDER ET DÉVELOPPEMENT LOCAL)
# ==============================================================================

if env('DATABASE_URL', default=None):
    # En production (Render / Heroku) via la variable DATABASE_URL
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
    DATABASES['default']['CONN_MAX_AGE'] = 600
else:
    # En local (developpement)
    DATABASES = {
        'default': {
            'ENGINE': env('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': env('DB_NAME', default='hotel_pms_db'),
            'USER': env('DB_USER', default='postgres'),
            'PASSWORD': env('DB_PASSWORD', default='postgres'),
            'HOST': env('DB_HOST', default='127.0.0.1'),
            'PORT': env('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 600,
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = env('HOTEL_TIMEZONE', default='UTC')
USE_I18N = True
USE_TZ = True

# Currency Configuration
HOTEL_CURRENCY = env('HOTEL_CURRENCY', default='FCFA')
HOTEL_NAME = env('HOTEL_NAME', default='Hôtel Prestige & Spa')

# Static & Media Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}