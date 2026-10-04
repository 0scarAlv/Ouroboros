import pytest
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.authentication.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_new_passwords_are_hashed_with_argon2():
    user = UserFactory()

    assert user.password.startswith('argon2$')


def test_passwords_need_at_least_ten_characters():
    with pytest.raises(ValidationError):
        validate_password('Xk3!pq9z')
    validate_password('Xk3!pq9zLm')


def test_session_lasts_a_fixed_eight_hour_shift():
    assert settings.SESSION_COOKIE_AGE == 8 * 60 * 60
    assert settings.SESSION_SAVE_EVERY_REQUEST is False


def test_pages_send_security_headers(client):
    response = client.get('/auth/login/')

    csp = response['Content-Security-Policy']
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert 'camera=(self)' in response['Permissions-Policy']
    assert response['X-Frame-Options'] == 'DENY'
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert response['Referrer-Policy'] == 'same-origin'


def test_pages_load_no_external_resources(client):
    client.force_login(UserFactory())
    html = client.get('/').content.decode()

    assert 'https://' not in html and 'http://' not in html


def test_htmx_sends_the_csrf_token(client):
    client.force_login(UserFactory())
    html = client.get('/').content.decode()

    assert 'hx-headers=\'{"X-CSRFToken": "' in html
