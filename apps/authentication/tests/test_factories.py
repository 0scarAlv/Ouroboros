import pytest

from apps.authentication.factories import TEST_PASSWORD, AdminFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_user_factory_creates_a_user_that_can_log_in(client):
    user = UserFactory()

    assert client.login(username=user.username, password=TEST_PASSWORD)


def test_user_factory_grants_permissions():
    user = UserFactory(permissions=['parties.view_party'])

    assert user.has_perm('parties.view_party')
    assert not user.has_perm('parties.change_party')


def test_admin_factory_creates_a_superuser():
    assert AdminFactory().is_superuser
