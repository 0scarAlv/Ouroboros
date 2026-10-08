from django.contrib import admin
from kernel.models import MenuItem, SecurityEvent

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
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
