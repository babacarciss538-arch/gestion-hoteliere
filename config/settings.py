# ==============================================================================
# CONFIGURATION POUR ACCÈS DISTANT (RENDER & CLOUDFLARE)
# ==============================================================================

# Lecture dynamique depuis la variable d'environnement ALLOWED_HOSTS si présente,
# sinon fallback sur Render, Cloudflare et localhost.
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    'gestion-hoteliere-2jms.onrender.com',
    '.trycloudflare.com',
])

# Autoriser les formulaires POST pour Render et Cloudflare
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://*.onrender.com',
    'https://gestion-hoteliere-2jms.onrender.com',
    'https://*.trycloudflare.com',
])

# Gestion des proxys HTTPS (Render & Cloudflare)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies sécurisés en HTTPS
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Support des fichiers statiques avec WhiteNoise sur Render
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir les fichiers CSS/JS
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.AuditMiddleware',
]