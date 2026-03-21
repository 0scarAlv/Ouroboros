from django.db import models
class TimestampMixin(models.Model):
    """
    Mixin that adds created_at and update_at fields to any model.
    use this yout need timestamps but not the full BaseModel.
    """

    created_at = models.D