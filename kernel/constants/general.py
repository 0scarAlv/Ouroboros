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

# Human-readable Spanish translations for form error codes.
ERROR_MESSAGES = {
    "FIELD_REQUIRED":       "Este campo es obligatorio.",
    "FIELD_INVALID":        "El valor ingresado no es válido.",
    "FIELD_TOO_LONG":       "El valor ingresado es demasiado largo.",
    "FIELD_TOO_SHORT":      "El valor ingresado es demasiado corto.",
    "FIELD_TOO_LARGE":      "El valor ingresado es demasiado grande.",
    "FIELD_TOO_SMALL":      "El valor ingresado es demasiado pequeño.",
    "FIELD_INVALID_CHOICE": "La opción seleccionada no es válida.",
    "FIELD_NOT_UNIQUE":     "Este valor ya existe, debe ser único.",
    "INVALID_CREDENTIALS":  "Usuario o contraseña incorrectos.",
}
