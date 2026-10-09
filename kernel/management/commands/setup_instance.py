from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from kernel.db.keys import create_key_file


class Command(BaseCommand):
    help = (
        'Prepare a new instance, or bring an existing one up to date: create '
        'its folders and database key, migrate, collect static files and '
        'create the first administrator. Safe to run again.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input', action='store_false', dest='interactive',
            help='Read the administrator from DJANGO_SUPERUSER_USERNAME, _EMAIL and _PASSWORD.',
        )

    def handle(self, *args, interactive, **options):
        for folder in (settings.MEDIA_ROOT, settings.BACKUP_DIR, getattr(settings, 'LOG_DIR', None)):
            if folder:
                Path(folder).mkdir(parents=True, exist_ok=True)

        key_file = settings.DATABASES['default'].get('OPTIONS', {}).get('key_file')
        if key_file and not Path(key_file).exists():
            Path(settings.DATABASES['default']['NAME']).parent.mkdir(parents=True, exist_ok=True)
            create_key_file(key_file)
            self.stdout.write(self.style.WARNING(
                f'Created the database key {key_file}. Copy it somewhere safe and apart '
                'from the backups: without it the database cannot be opened.'
            ))
        elif connection.vendor == 'sqlite':
            Path(settings.DATABASES['default']['NAME']).parent.mkdir(parents=True, exist_ok=True)

        call_command('migrate', interactive=False, verbosity=1 if options['verbosity'] else 0)
        if settings.STATIC_ROOT:
            call_command('collectstatic', interactive=False, verbosity=0)
            self.stdout.write('Static files collected.')

        if get_user_model().objects.filter(is_superuser=True).exists():
            self.stdout.write('An administrator already exists.')
        else:
            self.stdout.write('Create the first administrator:')
            call_command('createsuperuser', interactive=interactive)
        self.stdout.write(self.style.SUCCESS('Instance ready.'))
