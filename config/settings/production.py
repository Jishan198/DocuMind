from .base import *
from decouple import config

DEBUG = False

# Allows defining trusted origins for CSRF in environment (e.g. for AWS IP or Domain)
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost,http://127.0.0.1').split(',')
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')

# Only set these to True if accessing via HTTPS
CSRF_COOKIE_SECURE = config('SECURE_COOKIES', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SECURE_COOKIES', default=False, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')