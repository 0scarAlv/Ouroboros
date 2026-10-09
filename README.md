# Ouroboros

Reusable enterprise base built with Django 5.2 LTS.

## Getting Started
```bash
git clone git@github.com:0scarAlv/Ouroboros.git
cd Ouroboros

python -m venv .venv
source .venv/bin/activate

pip install -r requirements/dev.txt
# or requirements/postgres.txt to run on Postgres

cp .env.example .env
# fill in your values

# Optional: local Postgres (then set DATABASE_URL in .env)
# docker compose up -d

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## New modules

```bash
python manage.py startmodule products --model Product --audit 1
```

Creates `apps/products/` with a model, CRUD views, URLs, admin, factory
and tests (audit level 0 = timestamps, 1 = who + soft delete, 2 = full
history). Conventions are in `CLAUDE.md`.

## Tests

Tests run with pytest (`manage.py test` misses pytest-style tests):

```bash
pytest                         # whole suite
pytest apps/parties            # one module
pytest --cov                   # with coverage report
```

Write new tests as plain pytest functions and build test data with the
factory_boy factories in each app's `factories.py` (Spanish fake data
via Faker). Uploaded files go to a temporary folder (see `conftest.py`).

## Settings profiles

| Profile | Use |
|---|---|
| `config.settings.dev` | Development (`manage.py` default) |
| `config.settings.prod` | Server with a domain and HTTPS (`wsgi`/`asgi` default) |
| `config.settings.onprem` | The client's own PC serving its local network, offline-capable |

On-premise run (Windows or Linux, no Docker):

```bash
pip install -r requirements/onprem.txt
set DJANGO_SETTINGS_MODULE=config.settings.onprem   # export on Linux
python manage.py setup_instance   # folders, key, migrate, static, first admin
python manage.py serve            # waitress on 0.0.0.0:8000
```

`setup_instance` is safe to run again after an update. Backups:

```bash
python manage.py backup --keep 30          # zip in BACKUP_DIR: database + uploads
python manage.py restore <backup.zip>      # stop the server first
```

A backup can run while the server is up. Restore checks the zip, saves the
current data as a new backup, replaces it and applies newer migrations.

The database, uploads and logs live under `DATA_DIR`. The profile uses
plain HTTP; waitress has no TLS, so HTTPS needs a proxy in front (e.g.
Caddy with a local certificate) and `USE_HTTPS=True`.

To encrypt the database file at rest (SQLCipher), install
`requirements/sqlcipher.txt` and point `DATABASE_URL` at the database and
its key file:

```bash
DATABASE_URL=sqlcipher:////absolute/path/data/db.sqlite3?key_file=/absolute/path/data/db.key
```

`setup_instance` creates the key file when the URL names one that does not
exist yet. Without it the database cannot be opened, so keep a copy apart
from the backups (which never include it).

## Requirements

- Python 3.10+
- Optional: Docker + Docker Compose (only for Postgres)

By default the project uses a local SQLite file. Set `DATABASE_URL`
in `.env` to use any other database supported by Django.