import sys
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'simple_history',
    'axes',
]

LOCAL_APPS = [
    'kernel',
    "apps.authentication",
]

# Optional modules: keep only the ones the product uses.
MODULE_APPS = [
    "apps.parties",
    "apps.attachments",
]
LOGIN_URL = '/auth/login/'

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + MODULE_APPS

# Concrete models used only by the tests of the kernel and modules.
TESTING = sys.argv[1:2] == ['test'] or 'pytest' in sys.modules
if TESTING:
    INSTALLED_APPS += ['kernel.tests', 'apps.attachments.tests']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'kernel.middleware.SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'kernel.middleware.CurrentUserMiddleware',
    'kernel.middleware.SecurityEventMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Must stay last: turns locked-out logins into the lockout response.
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'kernel.context_processors.sidebar_menu',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# One URL selects the engine, so each product picks what suits its client:
# sqlite:///path/db.sqlite3, postgres://user:pass@host:5432/name, ...
# Defaults to a local SQLite file for development.
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': config('PASSWORD_MIN_LENGTH', default=10, cast=int)},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    # Must stay first: rejects logins for locked-out accounts.
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Failed-login lockout (django-axes). Locks the username, wherever the
# attempts come from: on a shared LAN many devices may share one IP.
AXES_FAILURE_LIMIT = config('LOGIN_FAILURE_LIMIT', default=5, cast=int)
AXES_COOLOFF_TIME = timedelta(minutes=config('LOGIN_LOCKOUT_MINUTES', default=15, cast=int))
AXES_LOCKOUT_PARAMETERS = ['username']
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = 'apps.authentication.views.locked_out'
# axes.W006 recommends adding the IP to the lockout key; locking by username
# alone is deliberate (see above).
SILENCED_SYSTEM_CHECKS = ['axes.W006']

# Security headers (every profile). All assets are served locally, so
# the browser may only load code and styles from this server.
# 'unsafe-eval': Alpine.js evaluates x-* expressions at runtime.
# 'unsafe-inline' styles: templates and Bootstrap's JS set inline styles.
CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
# Camera allowed for this site only (barcode scanning, needs HTTPS).
PERMISSIONS_POLICY = "camera=(self), microphone=(), geolocation=(), payment=(), usb=()"
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Argon2 (OWASP recommendation) for new passwords; existing hashes are
# upgraded on the user's next login.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# Sessions last a fixed work shift from login, whether or not the user is
# active (the expiry is not extended on each request).
SESSION_COOKIE_AGE = config('SESSION_HOURS', default=8, cast=int) * 60 * 60
SESSION_SAVE_EVERY_REQUEST = False

# Internationalization
LANGUAGE_CODE = config('LANGUAGE_CODE', default='es')
# Datetimes are stored in UTC (USE_TZ); this is only the display zone.
TIME_ZONE = config('TIME_ZONE', default='America/El_Salvador')
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "kernel" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded files. They are never served by URL: attachments go through
# their permission-checked download view.
MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR / 'media'))
MEDIA_URL = '/media/'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "authentication.User"