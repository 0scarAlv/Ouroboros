from django.db import models


class TimestampMixin(models.Model):
    """
    Mixin that adds created_at and updated_at fields to any model.
    Use this when you need timestamps but not the full BaseModel.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True