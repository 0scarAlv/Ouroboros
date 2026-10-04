import json

import pytest
from django.urls import reverse

from apps.authentication.factories import TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

HTMX = {'HTTP_HX_REQUEST': 'true'}


def attempt(client, username, password, ip='10.0.0.1'):
    return client.post(
        reverse('login'),
        {'username': username, 'password': password},
        REMOTE_ADDR=ip,
        **HTMX,
    )


def toast(response):
    return json.loads(response['HX-Trigger'])['showToast']['message']


def test_valid_credentials_log_in(client):
    user = UserFactory()

    response = attempt(client, user.username, TEST_PASSWORD)

    assert response['HX-Redirect'] == '/'
    assert client.session['_auth_user_id'] == str(user.pk)


def test_wrong_password_shows_an_error(client):
    user = UserFactory()

    response = attempt(client, user.username, 'wrong')

    assert 'incorrectos' in toast(response)
    assert '_auth_user_id' not in client.session


def test_account_locks_after_five_failures_from_any_ip(client):
    user = UserFactory()
    for n in range(5):
        attempt(client, user.username, 'wrong', ip=f'10.0.0.{n}')

    response = attempt(client, user.username, TEST_PASSWORD, ip='10.0.0.99')

    assert 'bloqueada' in toast(response)
    assert '_auth_user_id' not in client.session


def test_lockout_only_affects_that_username(client):
    victim, colleague = UserFactory(), UserFactory()
    for _ in range(5):
        attempt(client, victim.username, 'wrong')

    response = attempt(client, colleague.username, TEST_PASSWORD)

    assert response['HX-Redirect'] == '/'


def test_successful_login_resets_the_failure_count(client):
    user = UserFactory()
    for _ in range(4):
        attempt(client, user.username, 'wrong')
    attempt(client, user.username, TEST_PASSWORD)
    client.logout()
    for _ in range(4):
        attempt(client, user.username, 'wrong')

    response = attempt(client, user.username, TEST_PASSWORD)

    assert response['HX-Redirect'] == '/'


def test_lockout_without_htmx_returns_429(client):
    user = UserFactory()
    for _ in range(5):
        attempt(client, user.username, 'wrong')

    response = client.post(reverse('login'), {'username': user.username, 'password': TEST_PASSWORD})

    assert response.status_code == 429
