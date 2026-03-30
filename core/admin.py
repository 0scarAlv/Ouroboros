from django.contrib import admin
from core.models.menu_item import MenuItem
from core.models.person import Person
from core.models.address import Address
from core.models.document import Document

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

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["__str__", "person", "address_type", "city", "state", "is_primary"]
    list_filter = ["address_type", "is_primary", "state"]
    search_fields = ["street", "city", "state", "person__first_name", "person__company_name"]
    ordering = ["-is_primary", "address_type"]

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ["__str__", "person", "document_type", "filename", "is_active"]
    list_filter   = ["document_type", "is_active"]
    search_fields = ["filename", "person__first_name", "person__company_name"]
    ordering      = ["-created_at"]