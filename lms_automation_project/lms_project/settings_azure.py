from .settings import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Azure App Service hostname
ALLOWED_HOSTS = [
    os.getenv('WEBSITE_HOSTNAME', 'localhost'),
    '.azurewebsites.net',
    '127.0.0.1',
]

# CSRF trusted origins for Azure
CSRF_TRUSTED_ORIGINS = [
    f"https://{os.getenv('WEBSITE_HOSTNAME', 'localhost')}",
    'https://*.azurewebsites.net',
]

# WhiteNoise for static files (no need for separate static file server)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# MongoDB from environment variable (for Azure Cosmos DB or MongoDB Atlas)
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session configuration
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Logging for Azure
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
