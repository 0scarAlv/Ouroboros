import uuid
from django.db import models
from django.contrib.auth import get_user_model
from .base_models import BaseModel

class AuditModel(BaseModel):
    """
    Abstract model that extends BaseModel whith full audit trail.
    Tracks who create, update, and soft-deleted each record or log
    """
    
    created_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s %(class)s_created',
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s %(class)s_updated',
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    deletd_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s %(class)s_deleted',
    )

    class Meta:
        abstract = True

