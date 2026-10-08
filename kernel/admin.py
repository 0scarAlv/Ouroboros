from django import forms
from django.contrib import admin

from kernel.constants.icons import ICON_SET
from kernel.models import MenuItem, SecurityEvent


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = "__all__"
        help_texts = {
            "icon": "Material Symbols name from kernel/constants/icons.py (e.g. inventory_2). Leave empty for none.",
        }

    def clean_icon(self):
        # The vendored font is a subset: an unknown name would render as plain text.
        icon = self.cleaned_data["icon"].strip()
        if icon and icon not in ICON_SET:
            raise forms.ValidationError(
                f"«{icon}» is not in the vendored icon set (kernel/constants/icons.py)."
            )
        return icon


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    form = MenuItemForm
    list_display = ["label", "parent", "url_name", "permission", "order", "is_active"]
    list_filter = ["is_active", "parent"]
    ordering = ["parent", "order"]
    autocomplete_fields = ["parent"]
    search_fields = ["label", "url_name"]


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Read-only: the log can be searched but never edited or deleted."""
    list_display = ["created_at", "kind", "username", "ip_address", "path"]
    list_filter = ["kind"]
    search_fields = ["username", "ip_address", "path"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
