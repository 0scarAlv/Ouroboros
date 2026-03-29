from django.contrib import admin
from core.models.menu_item import MenuItem
from core.models.person import Person

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["label", "parent", "order", "is_active"]
    list_filter = ["is_active", "parent"]
    ordering = ["parent", "order"]

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["__str__","person_type","dui","tax_id","email","is_active"]
    list_filter = ["person_type", "is_active"]
    search_fields = ["first_name", "last_name", "company_name", "dui", "tax_id", "email"]
    ordering = ["-created_at"]