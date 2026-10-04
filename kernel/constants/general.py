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

# Person type (individual/organization)
class PersonType(models.TextChoices):
    NATURAL = 'natural', 'Natural'
    LEGAL = 'legal', 'Legal'

# Person role quick classification tag
class PersonRole(models.TextChoices):
    CLIENTE = 'client', 'Cliente'
    EMPLOYEE = 'employee', 'Empleado'
    SUPPLIER = 'supplier', 'Proveedor'
    CONTACT = 'contact', 'Contacto'
    OTHER = 'other', 'Otro'

class AdressType(models.TextChoices):
    HOME = 'home', 'Domicilio'
    WORK = 'work', 'Trabajo'
    BREANCH = 'branch', 'Sucursal'
    BILLING = 'billing', 'Facturación'
    OTHER = 'other', 'Otro'

class DocumentType(models.TextChoices):
    DUI              = 'dui',              'DUI'
    NIT              = 'nit',              'NIT'
    CONTRACT         = 'contract',         'Contrato'
    PROOF_OF_ADDRESS = 'proof_of_address', 'Comprobante de domicilio'
    PROFILE_PHOTO    = 'profile_photo',    'Foto de perfil'
    OTHER            = 'other',            'Otro'