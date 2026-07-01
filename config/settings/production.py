from .base import *

DEBUG = False

STATIC_ROOT = BASE_DIR / 'staticfiles'

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_ALLOWED_ORIGINS = [
    'https://estacionamiento.albertoknow.com',
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'https://estacionamiento.albertoknow.com',
    'https://estacionamiento-api.albertoknow.com',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
