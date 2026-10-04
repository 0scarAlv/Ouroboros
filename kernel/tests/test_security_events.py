import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse

from apps.authentication.factories import TEST_PASSWORD, UserFactory
from kernel.middleware import SecurityEventMiddleware
from kernel.models import SecurityEvent

pytestmark = pytest.mark.django_db
Kind = SecurityEvent.Kind


def login(client, username, password):
    return client.post(
        reverse('login'),
        {'username': username, 'password': password},
        REMOTE_ADDR='192.168.1.20',
        HTTP_USER_AGENT='Android 14 Chrome',
        HTTP_HX_REQUEST='true',
    )


def kinds():
    return list(SecurityEvent.objects.order_by('created_at').values_list('kind', flat=True))


def test_login_and_logout_are_recorded_with_ip_and_device(client):
    user = UserFactory()
    login(client, user.username, TEST_PASSWORD)
    client.post(reverse('logout'))

    assert kinds() == [Kind.LOGIN, Kind.LOGOUT]
    event = SecurityEvent.objects.get(kind=Kind.LOGIN)
    assert (event.user, event.username, event.ip_address) == (user, user.username, '192.168.1.20')
    assert event.user_agent == 'Android 14 Chrome'


def test_failed_logins_keep_the_attempted_username(client):
    login(client, 'nobody', 'wrong')

    event = SecurityEvent.objects.get()
    assert (event.kind, event.username, event.user) == (Kind.LOGIN_FAILED, 'nobody', None)


def test_lockout_is_recorded(client):
    user = UserFactory()
    for _ in range(5):
        login(client, user.username, 'wrong')

    assert SecurityEvent.objects.filter(kind=Kind.LOCKED_OUT, username=user.username).count() == 1


def test_permission_denied_is_recorded():
    request = RequestFactory().get('/secret/')
    request.user = UserFactory()

    SecurityEventMiddleware(lambda r: None).process_exception(request, PermissionDenied())

    event = SecurityEvent.objects.get()
    assert (event.kind, event.user, event.path) == (Kind.PERMISSION_DENIED, request.user, '/secret/')


def test_events_cannot_be_edited():
    event = SecurityEvent.record(Kind.LOGIN_FAILED, username='x')
    event.username = 'y'

    with pytest.raises(ValueError):
        event.save()


def test_admin_is_read_only(client):
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    SecurityEvent.record(Kind.LOGIN_FAILED, username='x')

    assert client.get(reverse('admin:kernel_securityevent_changelist')).status_code == 200
    assert client.get(reverse('admin:kernel_securityevent_add')).status_code == 403
