from django.db import models
from core.models.audit_model import AuditModel
from core.models.person import Person
from core.constants.general import DocumentType



def document_upload_path(instance, filename):
    """
    Create filepath in server 
    """
    #technical debt for future file server integration
    return f'documents/person_{instance.person.pk}/{filename}' 


class Document(AuditModel):
    """
    Documents is a upload files or img(bill,identity document,etc.....)
    """
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='documents',
    )

    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
    )

    # File
    file     = models.FileField(upload_to=document_upload_path)
    filename = models.CharField(max_length=255, blank=True, default='')

    notes     = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            self.filename = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_document_type_display()} — {self.person}'

    class Meta:
        verbose_name        = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering            = ['-created_at']