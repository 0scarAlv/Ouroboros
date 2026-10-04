from django.db import models


class PartyType(models.TextChoices):
    NATURAL = 'natural', 'Persona natural'
    LEGAL = 'legal', 'Persona jurídica'


class PartyRole(models.TextChoices):
    """
    Common roles. The `role` column is free text, so a product can use its
    own TextChoices (e.g. a pharmacist in charge) without migrating this module.
    """
    CLIENT = 'client', 'Cliente'
    SUPPLIER = 'supplier', 'Proveedor'
    EMPLOYEE = 'employee', 'Empleado'
    CONTACT = 'contact', 'Contacto'


class IdentifierKind(models.TextChoices):
    """
    Common identifier kinds. Like roles, `kind` is free text and products
    add their own (licenses, registrations...).
    """
    DUI = 'dui', 'DUI'
    NIT = 'nit', 'NIT'
    NRC = 'nrc', 'NRC'
    PASSPORT = 'passport', 'Pasaporte'


class AddressKind(models.TextChoices):
    HOME = 'home', 'Domicilio'
    WORK = 'work', 'Trabajo'
    BRANCH = 'branch', 'Sucursal'
    BILLING = 'billing', 'Facturación'
    SHIPPING = 'shipping', 'Entrega'
    OTHER = 'other', 'Otro'
