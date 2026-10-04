from django.contrib import admin
from kernel.models.menu_item import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["label", "parent", "order", "is_active"]
    list_filter = ["is_active", "parent"]
    ordering = ["parent", "order"]
