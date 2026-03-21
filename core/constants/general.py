from django.db import models

#Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

#Date format
DATE_FORMAT = '%B %d, %Y'
DATETIME_FORMAT = '%B %d, %Y %H:%M'

#Status choices
class Status(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inctive'
    DELETED = 'deleted', 'Deleted'

    