from .base import *

# Development-specific settings
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Enable Django debug toolbar and other dev tools in the future
INSTALLED_APPS += []

# Show emails in console instead of sending them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# No collectstatic needed while developing: static files are served
# straight from each app's static/ folder.
STATIC_ROOT = None
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
STORAGES = {
    **STORAGES,
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
