from django.db import models
from django.contrib.auth.models import Group
from kernel.models.audit_model import AuditModel

class MenuItem(AuditModel):
    """
    Represents a sidebar item, acting as a section header
    if it has no parent or a child item if it does,
    with visibility based on Django groups.
    """

    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True, default="")
    url_name = models.CharField(max_length=200 , blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="menu_items",
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Menu Item"
        verbose_name_plural = "menu Items"
    
    def __str__(self):
        return self.label
    
    def is_accessible_by(self, user):
        """
        Returns True if the user is authenticated and either
        the item has no groups or the user belongs to one of them.
        """
        if not user.is_authenticated:
            return False
        if not self.groups.exists():
            return True
        return self.groups.filter(user=user).exists()