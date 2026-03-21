from django.db import models
from django.utils import timezone


class SoftDeleteMixin(models.Model):
    """
    Mixin that adds soft delete functionality to any model.
    Records are never deleted from the database, only marked as deleted.
    """
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, deleted_by=None, *args, **kwargs):
        """Mark record as deleted instead of removing it from the database."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        """Return True if the record has been soft-deleted."""
        return self.deleted_at is not None