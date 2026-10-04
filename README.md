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

## Requirements

- Python 3.10+
- Optional: Docker + Docker Compose (only for Postgres)

By default the project uses a local SQLite file. Set `DATABASE_URL`
in `.env` to use any other database supported by Django.