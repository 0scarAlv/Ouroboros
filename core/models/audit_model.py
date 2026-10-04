from django.conf import settings
from django.db import models
from django.utils import timezone

from core.current_user import get_current_user
from .base_models import BaseModel


class AuditQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class ActiveManager(models.Manager.from_queryset(AuditQuerySet)):
    """Default manager: hides soft-deleted records."""

    def get_queryset(self):
        return super().get_queryset().active()


class AuditModel(BaseModel):
    """
    Audit level 1: BaseModel plus who created, last updated and soft-deleted
    each record. The acting user is taken from the current request (see
    CurrentUserMiddleware) or from an `acting_as()` block.

    `objects` only returns active records; `all_objects` includes the
    soft-deleted ones. `delete()` is still a real delete.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_updated',
    )
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_deleted',
    )

    objects = ActiveManager()
    all_objects = AuditQuerySet.as_manager()

    class Meta(BaseModel.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user is not None:
            if self._state.adding and self.created_by_id is None:
                self.created_by = user
            self.updated_by = user
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = {*kwargs['update_fields'], 'updated_at', 'updated_by'}
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """Mark the record as deleted without removing it from the database."""
        self.deleted_at = timezone.now()
        self.deleted_by = user or get_current_user()
        self.save(update_fields=['deleted_at', 'deleted_by'])

    def restore(self):
        """Undo a soft delete."""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['deleted_at', 'deleted_by'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None
