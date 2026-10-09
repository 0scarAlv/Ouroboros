"""
SQLite encrypted at rest with SQLCipher, for on-premise installs where the
database file sits on a client PC.

It is Django's SQLite backend on top of the sqlcipher3 driver; only the
connection is keyed. Select it with

    DATABASE_URL=sqlcipher:////absolute/path/db.sqlite3?key_file=/absolute/path/db.key

and install requirements/sqlcipher.txt. The key file is created by
kernel.db.keys.create_key_file; protecting it (file permissions, DPAPI on
Windows) is the installer's job.
"""
import datetime
import decimal
from collections.abc import Mapping
from itertools import tee

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3 import base as sqlite_base
from django.db.backends.sqlite3._functions import register as register_functions
from django.utils.asyncio import async_unsafe
from django.utils.dateparse import parse_date, parse_datetime, parse_time

from kernel.db.keys import KeyFileError, read_key_file

try:
    from sqlcipher3 import dbapi2 as Database
except ImportError as error:
    raise ImproperlyConfigured(
        'The sqlcipher backend needs sqlcipher3: pip install -r requirements/sqlcipher.txt'
    ) from error

# The same type conversions Django registers on the standard sqlite3 module.
Database.register_converter('bool', b'1'.__eq__)
Database.register_converter('date', sqlite_base.decoder(parse_date))
Database.register_converter('time', sqlite_base.decoder(parse_time))
Database.register_converter('datetime', sqlite_base.decoder(parse_datetime))
Database.register_converter('timestamp', sqlite_base.decoder(parse_datetime))
Database.register_adapter(decimal.Decimal, str)
Database.register_adapter(datetime.date, sqlite_base.adapt_date)
Database.register_adapter(datetime.datetime, sqlite_base.adapt_datetime)


class SQLCipherCursorWrapper(Database.Cursor):
    """Django's SQLiteCursorWrapper, rebased on the sqlcipher3 cursor (the
    driver only accepts its own cursor classes)."""

    convert_query = sqlite_base.SQLiteCursorWrapper.convert_query

    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        param_names = list(params) if isinstance(params, Mapping) else None
        return super().execute(self.convert_query(query, param_names=param_names), params)

    def executemany(self, query, param_list):
        peekable, param_list = tee(iter(param_list))
        if (params := next(peekable, None)) and isinstance(params, Mapping):
            param_names = list(params)
        else:
            param_names = None
        return super().executemany(self.convert_query(query, param_names=param_names), param_list)


class DatabaseWrapper(sqlite_base.DatabaseWrapper):
    vendor = 'sqlite'
    display_name = 'SQLite (SQLCipher)'
    Database = Database

    def get_connection_params(self):
        params = super().get_connection_params()
        key_file = params.pop('key_file', None)
        if not key_file:
            raise ImproperlyConfigured(
                'The sqlcipher backend needs a key file: add ?key_file=/path/to/db.key to DATABASE_URL.'
            )
        try:
            params['key'] = read_key_file(key_file)
        except KeyFileError as error:
            raise ImproperlyConfigured(str(error)) from None
        return params

    @async_unsafe
    def get_new_connection(self, conn_params):
        conn_params = dict(conn_params)
        key = conn_params.pop('key')
        conn = Database.connect(**conn_params)
        # The key must be set before anything touches the file. It is a
        # checked hex string, so formatting it into the PRAGMA is safe.
        conn.execute(f"PRAGMA key = \"x'{key}'\"")
        try:
            conn.execute('SELECT count(*) FROM sqlite_master').fetchone()
        except Database.DatabaseError:
            conn.close()
            raise ImproperlyConfigured(
                f"Cannot open {conn_params.get('database')}: wrong key, or not a SQLCipher database."
            ) from None
        register_functions(conn)
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA legacy_alter_table = OFF')
        for init_command in self.init_commands:
            if init_command := init_command.strip():
                conn.execute(init_command)
        return conn

    def create_cursor(self, name=None):
        return self.connection.cursor(factory=SQLCipherCursorWrapper)
