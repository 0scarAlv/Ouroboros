"""
Backups of an instance: the SQLite database plus the uploaded files, in a
single zip with a manifest of checksums.

The database is copied with SQLite's online backup API, so a backup can run
while the server is serving requests. An encrypted (SQLCipher) database
stays encrypted inside the zip with the same key; the key file itself is
never included, it is backed up separately. Postgres installs use their
own tools (pg_dump).
"""
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import django
from django.conf import settings
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.utils import timezone

FORMAT_VERSION = 1
MANIFEST = 'manifest.json'
DB_ENTRY = 'db.sqlite3'
MEDIA_PREFIX = 'media/'


class BackupError(Exception):
    pass


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _check_sqlite():
    if connection.vendor != 'sqlite':
        raise BackupError(f'Backups cover SQLite only; use the {connection.vendor} tools for this database.')


def _open_raw(path, key):
    """A plain driver connection to `path`, keyed like the live database."""
    raw = connection.Database.connect(str(path))
    if key:
        raw.execute(f"PRAGMA key = \"x'{key}'\"")
    return raw


def _applied_migrations(raw):
    try:
        rows = raw.execute('SELECT app, name FROM django_migrations').fetchall()
    except connection.Database.DatabaseError as error:
        raise BackupError(f'The database cannot be read: {error}') from None
    return sorted(f'{app}.{name}' for app, name in rows)


def create_backup(output_dir):
    """Write backup-<timestamp>.zip into `output_dir` and return its path."""
    _check_sqlite()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    key = connection.get_connection_params().get('key')
    stamp = timezone.localtime().strftime('%Y%m%d-%H%M%S')
    target = output_dir / f'backup-{stamp}.zip'
    counter = 1
    while target.exists():
        counter += 1
        target = output_dir / f'backup-{stamp}-{counter}.zip'

    with tempfile.TemporaryDirectory() as tmp:
        snapshot = Path(tmp) / DB_ENTRY
        connection.ensure_connection()
        copy = _open_raw(snapshot, key)
        try:
            connection.connection.backup(copy)
            migrations = _applied_migrations(copy)
        finally:
            copy.close()

        files = {DB_ENTRY: _sha256(snapshot)}
        media_root = Path(settings.MEDIA_ROOT)
        media_files = sorted(p for p in media_root.rglob('*') if p.is_file()) if media_root.is_dir() else []
        for path in media_files:
            files[MEDIA_PREFIX + path.relative_to(media_root).as_posix()] = _sha256(path)

        manifest = {
            'format': FORMAT_VERSION,
            'created_at': timezone.now().isoformat(),
            'django': django.get_version(),
            'encrypted': bool(key),
            'migrations': migrations,
            'files': files,
        }
        partial = target.with_suffix('.zip.partial')
        with zipfile.ZipFile(partial, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(MANIFEST, json.dumps(manifest, indent=2))
            archive.write(snapshot, DB_ENTRY)
            for path in media_files:
                archive.write(path, MEDIA_PREFIX + path.relative_to(media_root).as_posix())
        partial.replace(target)
    return target


def prune_backups(output_dir, keep):
    """Delete all but the newest `keep` backups in `output_dir`."""
    backups = sorted(Path(output_dir).glob('backup-*.zip'))
    removed = backups[:-keep] if keep > 0 else []
    for path in removed:
        path.unlink()
    return removed


def _safe_member(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise BackupError(f'Unsafe path in backup: {name}')
    return path


def read_manifest(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        try:
            manifest = json.loads(archive.read(MANIFEST))
        except KeyError:
            raise BackupError(f'{archive_path} is not a backup: no manifest.') from None
    if manifest.get('format') != FORMAT_VERSION:
        raise BackupError(f"Unsupported backup format: {manifest.get('format')}")
    return manifest


def restore_backup(archive_path, *, safety_dir=None):
    """Replace the database and uploaded files with the backup's.

    The backup is checked first (checksums, key, migrations this code
    knows); when `safety_dir` is given, the current data is backed up there
    before anything is replaced. Returns the safety backup path, if any.
    """
    _check_sqlite()
    manifest = read_manifest(archive_path)
    key = connection.get_connection_params().get('key')
    if manifest['encrypted'] != bool(key):
        state = 'encrypted' if manifest['encrypted'] else 'not encrypted'
        raise BackupError(f'The backup is {state} and does not match the configured database.')

    known = {f'{app}.{name}' for app, name in MigrationLoader(None, ignore_no_migrations=True).disk_migrations}
    unknown = sorted(set(manifest['migrations']) - known)
    if unknown:
        raise BackupError(
            'The backup was made by a newer version of the application '
            f'(unknown migrations: {", ".join(unknown[:5])}). Update the application first.'
        )

    db_path = Path(settings.DATABASES['default']['NAME'])
    media_root = Path(settings.MEDIA_ROOT)
    with tempfile.TemporaryDirectory(dir=db_path.parent) as tmp:
        staging = Path(tmp)
        with zipfile.ZipFile(archive_path) as archive:
            for name, checksum in manifest['files'].items():
                target = staging / _safe_member(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name) as source, open(target, 'wb') as dest:
                    shutil.copyfileobj(source, dest)
                if _sha256(target) != checksum:
                    raise BackupError(f'{name} is damaged (checksum mismatch).')

        check = _open_raw(staging / DB_ENTRY, key)
        try:
            _applied_migrations(check)
        finally:
            check.close()

        safety = create_backup(safety_dir) if safety_dir else None

        connection.close()
        for suffix in ('-wal', '-shm', '-journal'):
            Path(f'{db_path}{suffix}').unlink(missing_ok=True)
        (staging / DB_ENTRY).replace(db_path)

        staged_media = staging / 'media'
        if media_root.exists():
            shutil.rmtree(media_root)
        if staged_media.exists():
            shutil.move(staged_media, media_root)
        else:
            media_root.mkdir(parents=True, exist_ok=True)
    return safety
