# Ouroboros

Reusable enterprise core built with Django 5.2 LTS + DRF.

## Getting Started
```bash
git clone git@github.com:0scarAlv/Ouroboros.git
cd Ouroboros

python -m venv .venv
source .venv/bin/activate

pip install -r requirements/base.txt

cp .env.example .env
# fill in your values

docker compose up -d

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Requirements

- Python 3.10+
- Docker + Docker Compose