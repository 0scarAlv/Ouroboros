from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from core.models.audit_model import AuditModel
from core.constants.general import PersonType, PersonRole

class Person(AuditModel):
    person_type = models.CharField(
        max_length=10,
        choices=PersonType.choices,
        default=PersonType.NATURAL,
    )

    first_name = models.CharField(max_length=100,blank=True,default='')
    last_name = models.CharField(max_length=100,blank=True,default='')
    company_name = models.CharField(max_length=200,blank=True,default='')

    dui = models.CharField(max_length=20, blank=True, null=True,unique=True)
    tax_id = models.CharField(max_length=20, blank=True, null=True,unique=True)

    birth_date = models.DateField(blank=True, null=True)

    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=20, blank=True, default='')

    # classification tag 
    roles = ArrayField(
        models.CharField(max_length=20, choices=PersonRole.choices),
        default=list,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    # User is opcional 28-03-2026-oscarlx
    notes = models.TextField(blank=True, default='')
    def __str__(self):
        if self.person_type == PersonType.LEGAL:
            return self.company_name or 'Legal entity'
        return f'{self.first_name} {self.last_name}'.strip() or 'Unnamed person'
    
    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['-created_at']

    