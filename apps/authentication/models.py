from django.contrib.auth.models import AbstractUser
from django.db import models

class User (AbstractUser):
    """
    Custom user model. extends AbstractUser to allow future modifications.
    """
    pass