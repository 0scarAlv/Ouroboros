"""
The module scaffold is the reference module: generate one module per audit
level, make its migrations and run its own tests in a separate process, so
a broken template fails the suite.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

LEVELS = {'basic_items': 0, 'audited_items': 1, 'tracked_items': 2}

SETTINGS = '''\
from config.settings.dev import *  # noqa: F401,F403

INSTALLED_APPS = INSTALLED_APPS + {apps!r}
ROOT_URLCONF = 'scaffold_urls'
DATABASES = {{'default': {{'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}}}
'''

URLS = '''\
from django.urls import include, path

from config.urls import urlpatterns as project_urlpatterns

urlpatterns = [{routes}, *project_urlpatterns]
'''


def _run(args, cwd, env):
    result = subprocess.run(
        [sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


@pytest.mark.slow
def test_generated_modules_pass_their_own_tests(tmp_path):
    for name, audit in LEVELS.items():
        call_command('startmodule', name, audit=audit, directory=tmp_path, package=name, stdout=open(os.devnull, 'w'))

    (tmp_path / 'scaffold_settings.py').write_text(SETTINGS.format(apps=list(LEVELS)))
    routes = ', '.join(f"path('{name}/', include('{name}.urls'))" for name in LEVELS)
    (tmp_path / 'scaffold_urls.py').write_text(URLS.format(routes=routes))

    base_dir = Path(settings.BASE_DIR)
    env = {
        **os.environ,
        'PYTHONPATH': os.pathsep.join([str(tmp_path), str(base_dir)]),
        'DJANGO_SETTINGS_MODULE': 'scaffold_settings',
    }
    _run([str(base_dir / 'manage.py'), 'makemigrations', *LEVELS], cwd=tmp_path, env=env)
    result = _run(
        ['-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--rootdir', str(tmp_path),
         '-o', 'addopts=', '--ds=scaffold_settings', *(str(tmp_path / name) for name in LEVELS)],
        cwd=tmp_path, env=env,
    )
    # 6 tests at level 0 and 1, 7 at level 2 (history).
    assert '19 passed' in result.stdout, result.stdout


def test_generated_module_uses_the_requested_audit_level(tmp_path):
    call_command('startmodule', 'products', model='Product', audit=2, directory=tmp_path,
                 stdout=open(os.devnull, 'w'))

    module = tmp_path / 'products'
    assert 'class Product(TrackedModel)' in (module / 'models.py').read_text()
    assert "name = 'apps.products'" in (module / 'apps.py').read_text()
    assert 'product_history' in (module / 'urls.py').read_text()
    assert not list(module.rglob('*-tpl'))


def test_existing_folders_are_never_overwritten(tmp_path):
    (tmp_path / 'products').mkdir()

    with pytest.raises(CommandError, match='already exists'):
        call_command('startmodule', 'products', directory=tmp_path)


@pytest.mark.parametrize('name', ['Products', 'class', '9lives', 'my-module'])
def test_invalid_module_names_are_rejected(tmp_path, name):
    with pytest.raises(CommandError, match='not a valid module name'):
        call_command('startmodule', name, directory=tmp_path)
