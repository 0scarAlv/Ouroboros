# Ouroboros

Reusable enterprise core built with Django 5.2 LTS.

## Getting Started
```bash
git clone git@github.com:0scarAlv/Ouroboros.git
cd Ouroboros

python -m venv .venv
source .venv/bin/activate

pip install -r requirements/base.txt
# or requirements/postgres.txt to run on Postgres

cp .env.example .env
# fill in your values

# Optional: local Postgres (then set DATABASE_URL in .env)
# docker compose up -d

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Requirements

- Python 3.10+
- Optional: Docker + Docker Compose (only for Postgres)

By default the project uses a local SQLite file. Set `DATABASE_URL`
in `.env` to use any other database supported by Django.