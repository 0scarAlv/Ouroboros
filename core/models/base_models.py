import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model for all models in the project.
    Provides UUID primary key, and creation/update timestamps.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']