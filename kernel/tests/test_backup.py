"""
setup_instance, backup and restore run end to end in a separate process on
an on-premise instance under a temporary DATA_DIR, with plain and encrypted
SQLite.
"""
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.slow

COUNT_USERS = (
    'import django; django.setup(); '
    'from django.contrib.auth import get_user_model; '
    'print(get_user_model().objects.count())'
)
ADD_USER = (
    'import django; django.setup(); '
    'from django.contrib.auth import get_user_model; '
    "get_user_model().objects.create_user('intruso', password='x')"
)


def instance(tmp_path, encrypted):
    env = {
        **os.environ,
        'DJANGO_SETTINGS_MODULE': 'config.settings.onprem',
        'SECRET_KEY': 'test',
        'ALLOWED_HOSTS': 'localhost',
        'DATA_DIR': str(tmp_path),
        'DJANGO_SUPERUSER_USERNAME': 'admin',
        'DJANGO_SUPERUSER_EMAIL': 'admin@example.com',
        'DJANGO_SUPERUSER_PASSWORD': 'una-clave-larga-1',
    }
    env.pop('DATABASE_URL', None)
    if encrypted:
        env['DATABASE_URL'] = f'sqlcipher:///{tmp_path}/db.sqlite3?key_file={tmp_path}/db.key'

    def run(*args, code=None, check=True):
        command = [sys.executable, '-c', code] if code else [sys.executable, 'manage.py', *args]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        if not check:
            return result
        assert result.returncode == 0, result.stderr
        return result.stdout

    return run


@pytest.mark.parametrize('encrypted', [False, True], ids=['sqlite', 'sqlcipher'])
def test_setup_backup_and_restore_round_trip(tmp_path, encrypted):
    if encrypted:
        pytest.importorskip('sqlcipher3')
    run = instance(tmp_path, encrypted)

    run('setup_instance', '--no-input')
    assert run(code=COUNT_USERS).strip() == '1'
    assert (tmp_path / 'db.key').exists() is encrypted
    run('setup_instance', '--no-input')  # a second run changes nothing

    upload = tmp_path / 'media' / 'attachments' / 'nota.txt'
    upload.parent.mkdir(parents=True)
    upload.write_text('original')

    run('backup')
    backups = sorted((tmp_path / 'backups').glob('backup-*.zip'))
    assert len(backups) == 1
    with zipfile.ZipFile(backups[0]) as archive:
        assert {'manifest.json', 'db.sqlite3', 'media/attachments/nota.txt'} <= set(archive.namelist())
        assert archive.read('db.sqlite3').startswith(b'SQLite format 3') is not encrypted

    run(code=ADD_USER)
    upload.write_text('cambiado')
    (upload.parent / 'nuevo.txt').write_text('nuevo')

    run('restore', str(backups[0]), '--no-input')

    assert run(code=COUNT_USERS).strip() == '1'
    assert upload.read_text() == 'original'
    assert not (upload.parent / 'nuevo.txt').exists()
    # The data replaced by the restore was backed up first.
    assert len(list((tmp_path / 'backups').glob('backup-*.zip'))) == 2


def test_restore_rejects_a_damaged_backup(tmp_path):
    run = instance(tmp_path, encrypted=False)
    run('setup_instance', '--no-input')
    run('backup')
    good = next((tmp_path / 'backups').glob('backup-*.zip'))

    damaged = tmp_path / 'damaged.zip'
    with zipfile.ZipFile(good) as source, zipfile.ZipFile(damaged, 'w') as target:
        for item in source.infolist():
            data = source.read(item)
            target.writestr(item, data + b'x' if item.filename == 'db.sqlite3' else data)

    run(code=ADD_USER)

    result = run('restore', str(damaged), '--no-input', check=False)
    assert result.returncode != 0
    assert 'damaged' in result.stderr
    assert run(code=COUNT_USERS).strip() == '2'  # current data untouched


def test_backup_keeps_only_the_newest(tmp_path):
    run = instance(tmp_path, encrypted=False)
    run('setup_instance', '--no-input')
    for _ in range(3):
        run('backup', '--keep', '2')
    assert len(list((tmp_path / 'backups').glob('backup-*.zip'))) == 2
