"""
On-premise install: the client's own PC acts as the server for devices on
its local network (desktop browsers and phones over Wi-Fi), possibly with
no internet access. Runs on Windows or Linux without Docker:

    python manage.py serve --settings=config.settings.onprem

Everything the install writes lives under DATA_DIR (database, uploads,
logs), so backing up that folder backs up the instance.
"""
from .base import *

DEBUG = False

DATA_DIR = Path(config('DATA_DIR', default=str(BASE_DIR / 'data')))

DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default=f"sqlite:///{DATA_DIR / 'db.sqlite3'}")
    )
}
MEDIA_ROOT = config('MEDIA_ROOT', default=str(DATA_DIR / 'media'))
LOG_DIR = Path(config('LOG_DIR', default=str(DATA_DIR / 'logs')))

# Plain HTTP by default: there is no certificate on a local network.
# Set USE_HTTPS=True once a TLS proxy (e.g. Caddy with a local certificate)
# sits in front of the server; waitress itself does not speak HTTPS.
USE_HTTPS = config('USE_HTTPS', default=False, cast=bool)
if USE_HTTPS:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=60 * 60 * 24 * 30, cast=int)
else:
    # Deploy checks that only make sense over HTTPS.
    SILENCED_SYSTEM_CHECKS += ['security.W004', 'security.W008', 'security.W012', 'security.W016']

LOG_DIR.mkdir(parents=True, exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {'format': '{asctime} {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'app.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'encoding': 'utf-8',
            'formatter': 'standard',
        },
        'console': {'class': 'logging.StreamHandler', 'formatter': 'standard'},
    },
    'root': {'handlers': ['file', 'console'], 'level': 'INFO'},
    'loggers': {
        'django.request': {'level': 'WARNING'},
        'waitress': {'level': 'INFO'},
    },
}
