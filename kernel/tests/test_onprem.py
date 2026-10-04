import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

ROOT = Path(__file__).resolve().parents[2]

PRINT_SETTINGS = """
import json, django
django.setup()
from django.conf import settings as s
print(json.dumps({
    'debug': s.DEBUG,
    'db': str(s.DATABASES['default']['NAME']),
    'media': str(s.MEDIA_ROOT),
    'log': str(s.LOGGING['handlers']['file']['filename']),
    'secure_cookies': s.SESSION_COOKIE_SECURE,
    'ssl_redirect': s.SECURE_SSL_REDIRECT,
}))
"""


def load_onprem(tmp_path, **env):
    result = subprocess.run(
        [sys.executable, '-c', PRINT_SETTINGS],
        cwd=ROOT,
        env={
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'config.settings.onprem',
            'SECRET_KEY': 'test',
            'ALLOWED_HOSTS': 'localhost',
            'DATA_DIR': str(tmp_path),
            **env,
        },
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_onprem_keeps_all_instance_data_under_data_dir(tmp_path):
    loaded = load_onprem(tmp_path)

    assert loaded['debug'] is False
    assert loaded['db'] == str(tmp_path / 'db.sqlite3')
    assert loaded['media'] == str(tmp_path / 'media')
    assert loaded['log'] == str(tmp_path / 'logs' / 'app.log')
    assert (tmp_path / 'logs').is_dir()


def test_onprem_uses_plain_http_unless_https_is_enabled(tmp_path):
    assert load_onprem(tmp_path)['secure_cookies'] is False

    https = load_onprem(tmp_path, USE_HTTPS='True')
    assert https['secure_cookies'] is True
    assert https['ssl_redirect'] is True


def test_serve_refuses_to_run_with_debug(settings):
    settings.DEBUG = True

    with pytest.raises(CommandError):
        call_command('serve')


def test_serve_starts_waitress(settings, monkeypatch):
    settings.DEBUG = False
    calls = []
    monkeypatch.setattr('waitress.serve', lambda app, **kwargs: calls.append(kwargs))

    call_command('serve', '--port', '9000', stdout=open(os.devnull, 'w'))

    assert calls == [{'host': '0.0.0.0', 'port': 9000, 'threads': 8}]
