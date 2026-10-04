from django.conf import settings
from django.db import models

from .base_models import BaseModel


class SecurityEvent(BaseModel):
    """
    Append-only log of security-relevant events (logins, failures,
    lockouts, denied access, file downloads) for audits. Records cannot be
    edited once written.
    """

    class Kind(models.TextChoices):
        LOGIN = 'login', 'Inicio de sesión'
        LOGOUT = 'logout', 'Cierre de sesión'
        LOGIN_FAILED = 'login_failed', 'Intento fallido'
        LOCKED_OUT = 'locked_out', 'Cuenta bloqueada'
        PERMISSION_DENIED = 'permission_denied', 'Acceso denegado'
        FILE_DOWNLOAD = 'file_download', 'Descarga de archivo'

    kind = models.CharField(max_length=30, choices=Kind.choices, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    # Kept as text: failed logins may use names that match no user, and the
    # name must survive if the user is deleted.
    username = models.CharField(max_length=150, blank=True, default='', db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    path = models.CharField(max_length=500, blank=True, default='')
    detail = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = 'Evento de seguridad'
        verbose_name_plural = 'Eventos de seguridad'
        indexes = [models.Index(fields=['created_at'])]

    def __str__(self):
        return f'{self.get_kind_display()} — {self.username or "anónimo"}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Security events are append-only.')
        super().save(*args, **kwargs)

    @classmethod
    def record(cls, kind, request=None, user=None, username='', **detail):
        """Write an event, taking user, IP, user agent and path from the request."""
        if user is None and request is not None:
            user = getattr(request, 'user', None)
        if user is not None and not user.is_authenticated:
            user = None
        event = cls(
            kind=kind,
            user=user,
            username=username or (user.get_username() if user else ''),
            detail=detail,
        )
        if request is not None:
            event.ip_address = request.META.get('REMOTE_ADDR') or None
            event.user_agent = request.headers.get('User-Agent', '')[:255]
            event.path = request.path[:500]
        event.save()
        return event
