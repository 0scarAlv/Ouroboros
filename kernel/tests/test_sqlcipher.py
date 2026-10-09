import sqlite3
import stat
import sys

import dj_database_url
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import ConnectionHandler

from kernel.db.keys import KeyFileError, create_key_file, read_key_file

pytest.importorskip('sqlcipher3')


@pytest.fixture(autouse=True)
def standalone_connections(django_db_blocker):
    # These tests open their own files, never the test database.
    with django_db_blocker.unblock():
        yield


def wrapper(url):
    # ConnectionHandler fills the settings Django adds to every database.
    return ConnectionHandler({'default': dj_database_url.parse(url)})['default']


def connect(db_path, key_path):
    return wrapper(f'sqlcipher:///{db_path}?key_file={key_path}')


def write_rows(db_path, key_path):
    connection = connect(db_path, key_path)
    with connection.cursor() as cursor:
        cursor.execute('CREATE TABLE note (id integer primary key, body text)')
        cursor.execute('INSERT INTO note (body) VALUES (%s)', ['secreto'])
    connection.commit()
    connection.close()


def test_url_selects_the_backend_and_keeps_the_key_file(tmp_path):
    config = dj_database_url.parse(f'sqlcipher:///{tmp_path}/db.sqlite3?key_file={tmp_path}/db.key')
    assert config['ENGINE'] == 'kernel.db.backends.sqlcipher'
    assert config['OPTIONS'] == {'key_file': f'{tmp_path}/db.key'}


def test_data_round_trips_with_the_key(tmp_path):
    db, key = tmp_path / 'db.sqlite3', create_key_file(tmp_path / 'db.key')
    write_rows(db, key)

    connection = connect(db, key)
    with connection.cursor() as cursor:
        cursor.execute('SELECT body FROM note WHERE id = %(id)s', {'id': 1})
        assert cursor.fetchone() == ('secreto',)
    connection.close()


def test_file_is_unreadable_without_the_key(tmp_path):
    db, key = tmp_path / 'db.sqlite3', create_key_file(tmp_path / 'db.key')
    write_rows(db, key)

    raw = db.read_bytes()
    assert not raw.startswith(b'SQLite format 3')
    assert b'secreto' not in raw
    with pytest.raises(sqlite3.DatabaseError):
        sqlite3.connect(db).execute('SELECT * FROM note')


def test_wrong_key_is_reported_on_connect(tmp_path):
    db = tmp_path / 'db.sqlite3'
    write_rows(db, create_key_file(tmp_path / 'db.key'))

    connection = connect(db, create_key_file(tmp_path / 'other.key'))
    with pytest.raises(ImproperlyConfigured, match='wrong key'):
        connection.ensure_connection()


def test_missing_key_file_option_is_reported(tmp_path):
    connection = wrapper(f'sqlcipher:///{tmp_path}/db.sqlite3')
    with pytest.raises(ImproperlyConfigured, match='key_file'):
        connection.ensure_connection()


def test_key_file_is_never_overwritten(tmp_path):
    key = create_key_file(tmp_path / 'db.key')
    original = key.read_text()
    with pytest.raises(FileExistsError):
        create_key_file(key)
    assert key.read_text() == original


@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX permissions')
def test_key_file_is_private(tmp_path):
    key = create_key_file(tmp_path / 'db.key')
    assert stat.S_IMODE(key.stat().st_mode) == 0o600


@pytest.mark.parametrize('content', ['', 'not-hex', 'ab' * 31, "x' ; DROP TABLE note; --"])
def test_malformed_key_is_rejected(tmp_path, content):
    key = tmp_path / 'db.key'
    key.write_text(content)
    with pytest.raises(KeyFileError):
        read_key_file(key)
