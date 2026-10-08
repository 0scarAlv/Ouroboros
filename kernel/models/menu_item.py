from django.db import models
from django.contrib.auth.models import Permission
from kernel.models.audit_model import AuditModel

class MenuItem(AuditModel):
    """
    Represents a sidebar item, acting as a section header
    if it has no parent or a child item if it does.

    The menu is configured per install from the admin. Visibility follows
    Django permissions: an item with a permission is shown only to users
    who have it (usually through a group); an item without one is shown to
    every signed-in user.
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
    
    permission = models.ForeignKey(
        Permission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="menu_items",
        help_text="Leave empty to show the item to every signed-in user.",
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
        the item has no permission or the user has it.
        """
        if not user.is_authenticated:
            return False
        if self.permission is None:
            return True
        perm = self.permission
        return user.has_perm(f"{perm.content_type.app_label}.{perm.codename}")