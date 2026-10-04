from django.db import models

from kernel.models import AuditModel, TrackedModel


class AuditedNote(AuditModel):
    title = models.CharField(max_length=100)
    notes = models.TextField(blank=True, default='')


class TrackedNote(TrackedModel):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, default='')
