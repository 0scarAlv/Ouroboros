import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Extends AbstractUser to allow future modifications.
    Uses a UUID primary key like every other model in the project, so any
    generic reference (attachments, audit) can point to a user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
