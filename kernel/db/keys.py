"""
Key files for the encrypted SQLite (SQLCipher) backend.

A key file holds 32 random bytes written as 64 hex characters. SQLCipher
uses it as a raw key, which skips the passphrase derivation that would
otherwise slow down every new connection.
"""
import os
import re
import secrets
from pathlib import Path

KEY_PATTERN = re.compile(r'[0-9a-fA-F]{64}')


class KeyFileError(Exception):
    pass


def create_key_file(path):
    """Write a new random key to `path`. Never overwrites an existing key:
    losing it makes the database unreadable."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL fails if the file exists; 0o600 keeps it private on POSIX.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        handle.write(secrets.token_hex(32))
    return path


def read_key_file(path):
    """Return the hex key stored in `path`, checked so it is safe to put in
    a PRAGMA statement."""
    try:
        key = Path(path).read_text().strip()
    except OSError as error:
        raise KeyFileError(f'Cannot read the database key file {path}: {error}') from None
    if not KEY_PATTERN.fullmatch(key):
        raise KeyFileError(f'The database key file {path} must hold 64 hex characters.')
    return key
