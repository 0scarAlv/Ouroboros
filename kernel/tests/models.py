from django.db import models

from kernel.models import AuditModel, BaseModel, TrackedModel


class AuditedNote(AuditModel):
    title = models.CharField(max_length=100)
    notes = models.TextField(blank=True, default='')


class TrackedNote(TrackedModel):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return self.title


class PlainNote(BaseModel):
    title = models.CharField(max_length=100)
