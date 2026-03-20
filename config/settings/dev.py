from .base import *

# Development-specific settings
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Enable Django debug toolbar and other dev tools in the future
INSTALLED_APPS += []

# Show emails in console instead of sending them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'