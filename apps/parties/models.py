from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from kernel.models import AuditModel, TrackedModel
from .constants import AddressKind, PartyType


def default_country():
    """ISO 3166-1 alpha-2 code used when none is given (PARTIES_DEFAULT_COUNTRY)."""
    return getattr(settings, 'PARTIES_DEFAULT_COUNTRY', 'SV')


class Party(TrackedModel):
    """
    Any person or organization the system deals with: clients, suppliers,
    employees, contacts... What a party *is* for the business is given by
    its roles; role-specific data belongs in the product's own tables
    (e.g. a Supplier model with a OneToOne to Party).
    """
    party_type = models.CharField(
        max_length=10,
        choices=PartyType.choices,
        default=PartyType.NATURAL,
    )

    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    legal_name = models.CharField(max_length=200, blank=True, default='')
    trade_name = models.CharField(max_length=200, blank=True, default='')

    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='party',
        help_text='Cuenta de acceso, si esta persona usa el sistema.',
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')

    class Meta(TrackedModel.Meta):
        verbose_name = 'Persona o empresa'
        verbose_name_plural = 'Personas y empresas'

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        if self.party_type == PartyType.LEGAL:
            return self.trade_name or self.legal_name or 'Empresa sin nombre'
        return f'{self.first_name} {self.last_name}'.strip() or 'Persona sin nombre'

    def clean(self):
        if self.party_type == PartyType.LEGAL and not self.legal_name:
            raise ValidationError({'legal_name': 'Una persona jurídica necesita razón social.'})
        if self.party_type == PartyType.NATURAL and not self.first_name:
            raise ValidationError({'first_name': 'Una persona natural necesita nombre.'})

    def has_role(self, role):
        return self.roles.filter(role=role).exists()

    def add_role(self, role):
        return self.roles.get_or_create(role=role)[0]

    def get_identifier(self, kind):
        """Value of the party's identifier of the given kind, or None."""
        identifier = self.identifiers.filter(kind=kind).first()
        return identifier.value if identifier else None


class PartyRole(TrackedModel):
    """
    What a party is for the business (client, supplier...). A party can hold
    several roles. Free text so products can add roles without migrations:
    Party.objects.filter(roles__role='supplier')
    """
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='roles')
    role = models.CharField(max_length=30, db_index=True)

    class Meta(TrackedModel.Meta):
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        constraints = [
            models.UniqueConstraint(
                fields=['party', 'role'],
                condition=Q(deleted_at__isnull=True),
                name='unique_active_party_role',
            ),
        ]

    def __str__(self):
        return f'{self.party} — {self.role}'


class PartyIdentifier(TrackedModel):
    """
    Official identifier of a party (DUI, NIT, passport, license...). Stored
    as rows so each product and country adds its own kinds. A value is
    unique per kind and country among active records.
    """
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='identifiers')
    kind = models.CharField(max_length=30)
    value = models.CharField(max_length=50)
    country = models.CharField(max_length=2, default=default_country)

    class Meta(TrackedModel.Meta):
        verbose_name = 'Identificador'
        verbose_name_plural = 'Identificadores'
        constraints = [
            models.UniqueConstraint(
                fields=['kind', 'value', 'country'],
                condition=Q(deleted_at__isnull=True),
                name='unique_active_party_identifier',
            ),
        ]

    def __str__(self):
        return f'{self.kind.upper()} {self.value}'

    def save(self, *args, **kwargs):
        self.kind = self.kind.strip().lower()
        self.value = self.value.strip().upper()
        self.country = self.country.strip().upper()
        super().save(*args, **kwargs)


class Address(AuditModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='addresses')
    kind = models.CharField(max_length=10, choices=AddressKind.choices, default=AddressKind.HOME)

    line1 = models.CharField('dirección', max_length=200)
    line2 = models.CharField('complemento', max_length=200, blank=True, default='')
    city = models.CharField('municipio o ciudad', max_length=100)
    region = models.CharField('departamento o estado', max_length=100, blank=True, default='')
    country = models.CharField('país', max_length=2, default=default_country)
    postal_code = models.CharField(max_length=20, blank=True, default='')
    reference = models.CharField('punto de referencia', max_length=255, blank=True, default='')

    is_primary = models.BooleanField(default=False)

    class Meta(AuditModel.Meta):
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
        ordering = ['-is_primary', 'kind']
        constraints = [
            models.UniqueConstraint(
                fields=['party'],
                condition=Q(is_primary=True, deleted_at__isnull=True),
                name='one_primary_address_per_party',
            ),
        ]

    def __str__(self):
        return ', '.join(part for part in (self.line1, self.city, self.region) if part)
