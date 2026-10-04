from django.db import models
from kernel.models.base_models import BaseModel
from kernel.models.tracked_model import TrackedModel
from kernel.constants.general import PersonType, PersonRole

class Person(TrackedModel):
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

    is_active = models.BooleanField(default=True)

    # User is opcional 28-03-2026-oscarlx
    notes = models.TextField(blank=True, default='')
    def has_role(self, role):
        return self.role_assignments.filter(role=role).exists()

    def __str__(self):
        if self.person_type == PersonType.LEGAL:
            return self.company_name or 'Legal entity'
        return f'{self.first_name} {self.last_name}'.strip() or 'Unnamed person'
    
    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['-created_at']


class PersonRoleAssignment(BaseModel):
    """
    Quick classification tag (client, supplier, employee...). A person can
    hold several roles. Stored as rows instead of an array column so it works
    on every database and stays filterable:
    Person.objects.filter(role_assignments__role=PersonRole.SUPPLIER)
    """
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='role_assignments',
    )
    role = models.CharField(max_length=20, choices=PersonRole.choices)

    class Meta:
        verbose_name = 'Rol de persona'
        verbose_name_plural = 'Roles de persona'
        constraints = [
            models.UniqueConstraint(fields=['person', 'role'], name='unique_person_role'),
        ]

    def __str__(self):
        return f'{self.person} — {self.get_role_display()}'
