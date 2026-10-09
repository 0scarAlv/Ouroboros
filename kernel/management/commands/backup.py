from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from kernel.backup import BackupError, create_backup, prune_backups


class Command(BaseCommand):
    help = (
        'Back up the database and the uploaded files into one zip. Safe to run '
        'while the server is up. The database key file is not included: keep '
        'its own copy apart from the backups.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--output', default=None, help='Folder for the zip (default: BACKUP_DIR).')
        parser.add_argument('--keep', type=int, default=0, help='Keep only the newest N backups in the folder.')

    def handle(self, *args, output, keep, **options):
        output = output or settings.BACKUP_DIR
        try:
            path = create_backup(output)
        except BackupError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(self.style.SUCCESS(f'Backup written to {path}'))
        for old in prune_backups(output, keep) if keep else []:
            self.stdout.write(f'Removed old backup {old.name}')
