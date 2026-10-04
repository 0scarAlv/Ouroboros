import hashlib
import shutil
import tempfile
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.attachments.models import Attachment
from apps.attachments.tests.models import Contract
from kernel.current_user import acting_as

User = get_user_model()
PDF = b'%PDF-1.4 fake content'


def upload(name='Contrato Ana López.pdf', content=PDF):
    return SimpleUploadedFile(name, content)


class MediaRootMixin:
    """Stores uploads in a temporary folder removed after each test class."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)


class AttachmentTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.contract = Contract.objects.create(title='Contrato 1')
        self.alice = User.objects.create_user('alice', password='x')

    def test_attach_records_metadata_checksum_and_author(self):
        with acting_as(self.alice):
            attachment = Attachment.attach(self.contract, upload(), kind='contract')

        self.assertEqual(attachment.content_object, self.contract)
        self.assertEqual(attachment.original_name, 'Contrato Ana López.pdf')
        self.assertEqual(attachment.mime_type, 'application/pdf')
        self.assertEqual(attachment.size, len(PDF))
        self.assertEqual(attachment.sha256, hashlib.sha256(PDF).hexdigest())
        self.assertEqual(attachment.created_by, self.alice)
        self.assertEqual(list(self.contract.attachments.all()), [attachment])

    def test_stored_path_hides_the_original_name(self):
        attachment = Attachment.attach(self.contract, upload())

        now = timezone.now()
        self.assertEqual(attachment.file.name, f'attachments/{now:%Y}/{now:%m}/{attachment.pk}.pdf')

    def test_rejects_disallowed_extensions(self):
        for name in ['script.html', 'logo.svg', 'tool.exe']:
            with self.subTest(name=name), self.assertRaises(ValidationError):
                Attachment.attach(self.contract, upload(name))
        self.assertFalse(Attachment.all_objects.exists())

    @override_settings(ATTACHMENTS_MAX_SIZE=10)
    def test_rejects_files_over_the_size_limit(self):
        with self.assertRaises(ValidationError):
            Attachment.attach(self.contract, upload())

    @override_settings(ATTACHMENTS_ALLOWED_EXTENSIONS=['dwg'])
    def test_allowed_extensions_come_from_settings(self):
        Attachment.attach(self.contract, upload('plano.dwg'))
        with self.assertRaises(ValidationError):
            Attachment.attach(self.contract, upload())

    def test_file_cannot_be_replaced(self):
        attachment = Attachment.attach(self.contract, upload())
        attachment.description = 'firmado'
        attachment.save()

        attachment.file.save('other.pdf', ContentFile(b'other'), save=False)
        with self.assertRaises(ValidationError):
            attachment.save()

    def test_verify_integrity_detects_tampering(self):
        attachment = Attachment.attach(self.contract, upload())
        self.assertTrue(attachment.verify_integrity())

        with open(attachment.file.path, 'wb') as stored:
            stored.write(b'%PDF-1.4 altered')
        self.assertFalse(attachment.verify_integrity())

    def test_soft_delete_hides_the_attachment_but_keeps_the_file(self):
        attachment = Attachment.attach(self.contract, upload())
        attachment.soft_delete(user=self.alice)

        self.assertFalse(self.contract.attachments.exists())
        self.assertTrue(default_storage.exists(attachment.file.name))


class PurgeTests(MediaRootMixin, TestCase):
    def setUp(self):
        self.contract = Contract.objects.create(title='Contrato 1')

    def purge(self, *args):
        call_command('purge_attachments', *args, stdout=StringIO())

    def test_removes_only_attachments_deleted_before_the_cutoff(self):
        old = Attachment.attach(self.contract, upload())
        recent = Attachment.attach(self.contract, upload())
        active = Attachment.attach(self.contract, upload())
        old.soft_delete()
        recent.soft_delete()
        Attachment.all_objects.filter(pk=old.pk).update(deleted_at=timezone.now() - timedelta(days=31))

        self.purge('--older-than', '30')

        self.assertEqual(set(Attachment.all_objects.values_list('pk', flat=True)), {recent.pk, active.pk})
        self.assertFalse(default_storage.exists(old.file.name))
        self.assertTrue(default_storage.exists(recent.file.name))

    def test_dry_run_removes_nothing(self):
        attachment = Attachment.attach(self.contract, upload())
        attachment.soft_delete()

        self.purge('--older-than', '0', '--dry-run')

        self.assertTrue(Attachment.all_objects.filter(pk=attachment.pk).exists())
        self.assertTrue(default_storage.exists(attachment.file.name))

    def test_orphans_removes_files_without_an_attachment(self):
        kept = Attachment.attach(self.contract, upload())
        orphan = Attachment.attach(self.contract, upload())
        Attachment.all_objects.filter(pk=orphan.pk).delete()

        self.purge('--orphans')

        self.assertTrue(default_storage.exists(kept.file.name))
        self.assertFalse(default_storage.exists(orphan.file.name))


class DownloadTests(MediaRootMixin, TestCase):
    def setUp(self):
        contract = Contract.objects.create(title='Contrato 1')
        self.attachment = Attachment.attach(contract, upload())
        self.url = reverse('attachments:download', args=[self.attachment.pk])
        self.user = User.objects.create_user('ana', password='x')

    def grant(self, *codenames):
        self.user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))

    def test_anonymous_users_are_sent_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_needs_permission_on_attachments_and_on_the_owner_record(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

        self.grant('view_attachment')
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_allowed_user_downloads_with_the_original_name(self):
        self.grant('view_attachment', 'view_contract')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), PDF)
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('Contrato%20Ana%20L%C3%B3pez.pdf', response['Content-Disposition'])
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_inline_preview_only_for_safe_types(self):
        self.grant('view_attachment', 'view_contract')
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'inline': '1'})
        self.assertIn('inline;', response['Content-Disposition'])

        text = Attachment.attach(self.attachment.content_object, upload('notas.txt', b'hola'))
        response = self.client.get(reverse('attachments:download', args=[text.pk]), {'inline': '1'})
        self.assertIn('attachment;', response['Content-Disposition'])

    def test_soft_deleted_attachments_are_not_served(self):
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        self.attachment.soft_delete()

        self.assertEqual(self.client.get(self.url).status_code, 404)


class DownloadLogTests(MediaRootMixin, TestCase):
    def test_downloads_and_denials_are_recorded(self):
        from kernel.models import SecurityEvent

        attachment = Attachment.attach(Contract.objects.create(title='C'), upload())
        url = reverse('attachments:download', args=[attachment.pk])
        user = User.objects.create_user('ana', password='x')
        self.client.force_login(user)

        self.client.get(url)
        user.user_permissions.add(*Permission.objects.filter(codename__in=['view_attachment', 'view_contract']))
        self.client.get(url)

        denied = SecurityEvent.objects.get(kind=SecurityEvent.Kind.PERMISSION_DENIED)
        download = SecurityEvent.objects.get(kind=SecurityEvent.Kind.FILE_DOWNLOAD)
        self.assertEqual(denied.path, url)
        self.assertEqual(download.detail['attachment'], str(attachment.pk))
        self.assertEqual(download.detail['name'], 'Contrato Ana López.pdf')
