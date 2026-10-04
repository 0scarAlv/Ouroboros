from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Address, Party, PartyIdentifier, PartyRole


class PartyRoleInline(admin.TabularInline):
    model = PartyRole
    extra = 0


class PartyIdentifierInline(admin.TabularInline):
    model = PartyIdentifier
    extra = 0


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


@admin.register(Party)
class PartyAdmin(SimpleHistoryAdmin):
    inlines = [PartyRoleInline, PartyIdentifierInline, AddressInline]
    list_display = ['__str__', 'party_type', 'email', 'phone', 'is_active']
    list_filter = ['party_type', 'is_active', 'roles__role']
    search_fields = ['first_name', 'last_name', 'legal_name', 'trade_name', 'email', 'identifiers__value']
