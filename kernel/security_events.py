"""
Signal receivers that write authentication events to SecurityEvent.
Connected in KernelConfig.ready().
"""
from axes.signals import user_locked_out
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from kernel.models import SecurityEvent


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    SecurityEvent.record(SecurityEvent.Kind.LOGIN, request, user=user)


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    SecurityEvent.record(SecurityEvent.Kind.LOGOUT, request, user=user)


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    username = credentials.get(get_user_model().USERNAME_FIELD, '')
    SecurityEvent.record(SecurityEvent.Kind.LOGIN_FAILED, request, username=username)


@receiver(user_locked_out)
def log_locked_out(sender, request, username, ip_address, **kwargs):
    SecurityEvent.record(SecurityEvent.Kind.LOCKED_OUT, request, username=username or '')
