from django.db import models
from core.models.audit_model import AuditModel
from core.models.person import Person
from core.constants.general import AdressType

class Address(AuditModel):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='addresses',
    )

    address_type = models.CharField(
        max_length=10,
        choices=AdressType.choices,
        default=AdressType.HOME,
    )

    street = models.CharField(max_length=200)
    number = models.CharField(max_length=20, blank=True, default='')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='El Salvador')
    zip_code = models.CharField(max_length=20, blank=True, default='')
    reference = models.CharField(max_length=255, blank=True, default='')

    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.street}, {self.city}, {self.state}'
    
    class Meta:
        verbose_name = 'Dirección'
        verbose_name_plural = 'Direcciones'
        ordering = ["-is_primary", "address_type"]