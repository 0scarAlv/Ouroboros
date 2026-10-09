from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from kernel.backup import BackupError, read_manifest, restore_backup


class Command(BaseCommand):
    help = (
        'Replace the database and the uploaded files with a backup made by the '
        'backup command, then apply any newer migrations. Stop the server first. '
        'The current data is backed up to BACKUP_DIR before it is replaced.'
    )

    def add_arguments(self, parser):
        parser.add_argument('archive', help='Path to a backup-*.zip file.')
        parser.add_argument('--no-input', action='store_false', dest='interactive', help='Do not ask for confirmation.')

    def handle(self, *args, archive, interactive, **options):
        try:
            manifest = read_manifest(archive)
        except (BackupError, OSError) as error:
            raise CommandError(str(error)) from None
        files = len(manifest['files']) - 1
        self.stdout.write(f"Backup from {manifest['created_at']}: database and {files} uploaded files.")
        if interactive:
            answer = input('This replaces ALL current data. Type "restaurar" to continue: ')
            if answer.strip() != 'restaurar':
                raise CommandError('Restore cancelled.')
        try:
            safety = restore_backup(archive, safety_dir=settings.BACKUP_DIR)
        except BackupError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(f'Previous data saved to {safety}')
        call_command('migrate', interactive=False, verbosity=0)
        self.stdout.write(self.style.SUCCESS('Restore complete. Start the server again.'))
