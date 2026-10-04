from django.conf import settings
from django.core.exceptions import PermissionDenied

from kernel.current_user import acting_as
from kernel.models import SecurityEvent


class CurrentUserMiddleware:
    """
    Exposes request.user to the audit layer for the whole request.
    Must run after AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with acting_as(request.user):
            return self.get_response(request)


class SecurityEventMiddleware:
    """Records every PermissionDenied raised by a view as a security event."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            SecurityEvent.record(SecurityEvent.Kind.PERMISSION_DENIED, request)
        return None


class SecurityHeadersMiddleware:
    """
    Adds the Content-Security-Policy and Permissions-Policy headers from the
    CONTENT_SECURITY_POLICY and PERMISSIONS_POLICY settings, unless the view
    already set them.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.headers = {
            'Content-Security-Policy': getattr(settings, 'CONTENT_SECURITY_POLICY', ''),
            'Permissions-Policy': getattr(settings, 'PERMISSIONS_POLICY', ''),
        }

    def __call__(self, request):
        response = self.get_response(request)
        for header, value in self.headers.items():
            if value:
                response.headers.setdefault(header, value)
        return response
