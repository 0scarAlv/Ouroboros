from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from kernel.models import SecurityEvent

from .models import Attachment
from .permissions import can_view

# Types the browser may display instead of downloading. Never add HTML or
# SVG: they can run scripts in the application's origin.
INLINE_MIME_TYPES = {'application/pdf', 'image/jpeg', 'image/png', 'image/webp'}


@login_required
def download(request, pk):
    """
    The only way to read an attachment: checks permissions on every request.
    Add ?inline=1 to preview PDFs and images in the browser.
    """
    attachment = get_object_or_404(Attachment, pk=pk)
    if not can_view(request.user, attachment):
        raise PermissionDenied
    try:
        file = attachment.file.open('rb')
    except FileNotFoundError:
        raise Http404('El archivo ya no existe en el almacenamiento.')

    inline = request.GET.get('inline') == '1' and attachment.mime_type in INLINE_MIME_TYPES
    SecurityEvent.record(
        SecurityEvent.Kind.FILE_DOWNLOAD,
        request,
        attachment=str(attachment.pk),
        name=attachment.original_name,
        owner=f'{attachment.content_type.app_label}.{attachment.content_type.model}:{attachment.object_id}',
        inline=inline,
    )
    response = FileResponse(
        file,
        as_attachment=not inline,
        filename=attachment.original_name,
        content_type=attachment.mime_type,
    )
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
