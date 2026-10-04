from datetime import timedelta

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.attachments.models import Attachment

ROOT = 'attachments'


class Command(BaseCommand):
    help = (
        'Permanently remove attachments soft-deleted more than --older-than days ago '
        '(row and file). With --orphans, also remove stored files no attachment refers to.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--older-than', type=int, default=30, metavar='DAYS')
        parser.add_argument('--orphans', action='store_true')
        parser.add_argument('--dry-run', action='store_true', help='Only list what would be removed.')

    def handle(self, *args, older_than, orphans, dry_run, **options):
        cutoff = timezone.now() - timedelta(days=older_than)
        expired = Attachment.all_objects.filter(deleted_at__lt=cutoff)

        files = 0
        for attachment in expired:
            self.stdout.write(f'attachment {attachment.pk} {attachment.file.name}')
            if not dry_run:
                attachment.file.delete(save=False)
                attachment.delete()
            files += 1

        if orphans:
            known = set(Attachment.all_objects.values_list('file', flat=True))
            for name in self._stored_files(ROOT):
                if name not in known:
                    self.stdout.write(f'orphan {name}')
                    if not dry_run:
                        default_storage.delete(name)
                    files += 1

        verb = 'Would remove' if dry_run else 'Removed'
        self.stdout.write(self.style.SUCCESS(f'{verb} {files} file(s).'))

    def _stored_files(self, folder):
        if not default_storage.exists(folder):
            return
        directories, files = default_storage.listdir(folder)
        for name in files:
            yield f'{folder}/{name}'
        for directory in directories:
            yield from self._stored_files(f'{folder}/{directory}')
