from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html

from .models import Attachment

READONLY_FIELDS = ['download_link', 'original_name', 'mime_type', 'size', 'sha256', 'created_by', 'created_at']


def download_link(attachment):
    if not attachment.pk or attachment._state.adding:
        return '—'
    url = reverse('attachments:download', args=[attachment.pk])
    return format_html('<a href="{}">{}</a>', url, attachment.original_name)


download_link.short_description = 'Archivo'


class AttachmentInline(GenericTabularInline):
    """Add to any ModelAdmin whose model uses HasAttachments."""
    model = Attachment
    extra = 0
    fields = ['file', 'kind', 'description', 'download_link', 'size', 'created_by', 'created_at']
    readonly_fields = READONLY_FIELDS

    def download_link(self, obj):
        return download_link(obj)

    def has_change_permission(self, request, obj=None):
        # Existing files cannot be replaced, only added.
        return False


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'kind', 'content_type', 'size', 'created_by', 'created_at', 'is_deleted']
    list_filter = ['kind', 'content_type', ('deleted_at', admin.EmptyFieldListFilter)]
    search_fields = ['original_name', 'description', 'sha256']
    readonly_fields = READONLY_FIELDS + ['content_type', 'object_id', 'file', 'deleted_at', 'deleted_by']
    fields = ['download_link', 'kind', 'description', 'content_type', 'object_id',
              'original_name', 'mime_type', 'size', 'sha256', 'created_by', 'created_at', 'deleted_at', 'deleted_by']
    actions = ['restore_selected']

    def download_link(self, obj):
        return download_link(obj)

    def get_queryset(self, request):
        return Attachment.all_objects.all()

    def has_add_permission(self, request):
        # Attachments are added from the record they belong to.
        return False

    def delete_model(self, request, obj):
        obj.soft_delete(user=request.user)

    def delete_queryset(self, request, queryset):
        for attachment in queryset:
            attachment.soft_delete(user=request.user)

    @admin.display(boolean=True, description='Eliminado')
    def is_deleted(self, obj):
        return obj.is_deleted

    @admin.action(description='Restaurar adjuntos eliminados')
    def restore_selected(self, request, queryset):
        for attachment in queryset.deleted():
            attachment.restore()
