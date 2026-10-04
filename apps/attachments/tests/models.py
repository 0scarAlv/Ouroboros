from django.db import models

from apps.attachments.models import HasAttachments
from kernel.models import AuditModel


class Contract(HasAttachments, AuditModel):
    title = models.CharField(max_length=100)
