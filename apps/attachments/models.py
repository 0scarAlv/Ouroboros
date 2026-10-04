import hashlib
import mimetypes
import uuid
from pathlib import PurePath

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible

from kernel.models import AuditModel

DEFAULT_ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'webp', 'docx', 'xlsx', 'csv', 'txt']
DEFAULT_MAX_SIZE = 10 * 1024 * 1024


def allowed_extensions():
    return getattr(settings, 'ATTACHMENTS_ALLOWED_EXTENSIONS', DEFAULT_ALLOWED_EXTENSIONS)


def max_size():
    return getattr(settings, 'ATTACHMENTS_MAX_SIZE', DEFAULT_MAX_SIZE)


def extension_of(filename):
    return PurePath(filename).suffix.lstrip('.').lower()


def attachment_upload_path(instance, filename):
    """
    attachments/YYYY/MM/<uuid>.<ext>: the original name (which may hold
    personal data) is kept only in the database, never in the file path.
    """
    now = timezone.now()
    return f'attachments/{now:%Y}/{now:%m}/{instance.pk}.{extension_of(filename)}'


@deconstructible
class UploadValidator:
    """Rejects files whose extension is not allowed or that are too big."""

    def __call__(self, file):
        extension = extension_of(file.name)
        if extension not in allowed_extensions():
            raise ValidationError(
                'Tipo de archivo no permitido (.%(ext)s). Permitidos: %(allowed)s.',
                params={'ext': extension, 'allowed': ', '.join(allowed_extensions())},
                code='invalid_extension',
            )
        if file.size > max_size():
            raise ValidationError(
                'El archivo supera el tamaño máximo de %(max)s MB.',
                params={'max': max_size() // (1024 * 1024)},
                code='file_too_large',
            )


class Attachment(AuditModel):
    """
    A file attached to any record. Files are immutable: replacing a document
    means adding a new attachment and soft-deleting the old one, so earlier
    versions stay available. Soft-deleted files are only removed from disk by
    the `purge_attachments` command.

    Never expose files through MEDIA_URL; serve them with the download view,
    which checks permissions.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

    kind = models.CharField(
        max_length=30,
        blank=True,
        default='',
        db_index=True,
        help_text='Clasificación definida por el producto (contrato, factura, receta...).',
    )
    description = models.CharField(max_length=255, blank=True, default='')

    file = models.FileField(upload_to=attachment_upload_path, validators=[UploadValidator()])
    original_name = models.CharField(max_length=255, editable=False)
    mime_type = models.CharField(max_length=100, editable=False)
    size = models.PositiveBigIntegerField(editable=False)
    sha256 = models.CharField(
        max_length=64,
        editable=False,
        db_index=True,
        help_text='Huella del contenido para comprobar que el archivo no fue alterado.',
    )

    class Meta(AuditModel.Meta):
        verbose_name = 'Archivo adjunto'
        verbose_name_plural = 'Archivos adjuntos'
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return self.original_name

    def save(self, *args, **kwargs):
        if self._state.adding:
            self._fill_file_metadata()
        elif self._file_changed():
            raise ValidationError('Un archivo adjunto no se puede reemplazar; agrega uno nuevo.')
        super().save(*args, **kwargs)

    def _fill_file_metadata(self):
        self.original_name = PurePath(self.file.name).name
        self.mime_type = mimetypes.guess_type(self.original_name)[0] or 'application/octet-stream'
        self.size = self.file.size
        self.sha256 = compute_sha256(self.file)

    def _file_changed(self):
        stored = type(self).all_objects.filter(pk=self.pk).values_list('file', flat=True).first()
        return stored is not None and stored != self.file.name

    def verify_integrity(self):
        """True if the stored file still matches the checksum taken on upload."""
        with self.file.open('rb'):
            return compute_sha256(self.file) == self.sha256

    @classmethod
    def attach(cls, obj, file, kind='', description=''):
        """Validate `file` and attach it to `obj`."""
        attachment = cls(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            file=file,
            kind=kind,
            description=description,
        )
        attachment.full_clean()
        attachment.save()
        return attachment


def compute_sha256(file):
    digest = hashlib.sha256()
    file.seek(0)
    for chunk in file.chunks():
        digest.update(chunk)
    file.seek(0)
    return digest.hexdigest()


class HasAttachments(models.Model):
    """
    Adds `record.attachments` to a model. Hard-deleting the record also
    deletes its attachment rows (files stay on disk until purged).
    """
    attachments = GenericRelation(Attachment)

    class Meta:
        abstract = True
