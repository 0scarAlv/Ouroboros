import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.test import RequestFactory

from apps.authentication.factories import UserFactory
from kernel.context_processors import sidebar_menu
from kernel.models import MenuItem

pytestmark = pytest.mark.django_db


def _menu_for(user):
    request = RequestFactory().get('/')
    request.user = user
    return sidebar_menu(request)['sidebar_menu']


def _labels(menu):
    return {entry['item'].label: [c.label for c in entry['children']] for entry in menu}


@pytest.fixture
def view_group_perm():
    return Permission.objects.get(codename='view_group')


def test_item_without_permission_is_visible_to_any_signed_in_user():
    MenuItem.objects.create(label='Home', url_name='home')

    assert _labels(_menu_for(UserFactory())) == {'Home': []}


def test_item_is_hidden_from_users_without_its_permission(view_group_perm):
    MenuItem.objects.create(label='Groups', url_name='home', permission=view_group_perm)

    assert _menu_for(UserFactory()) == []


def test_permission_granted_through_a_group_shows_the_item(view_group_perm):
    MenuItem.objects.create(label='Groups', url_name='home', permission=view_group_perm)
    group = Group.objects.create(name='Supervisors')
    group.permissions.add(view_group_perm)
    user = UserFactory()
    user.groups.add(group)

    assert _labels(_menu_for(user)) == {'Groups': []}


def test_section_without_visible_children_is_hidden(view_group_perm):
    section = MenuItem.objects.create(label='Admin')
    MenuItem.objects.create(label='Groups', url_name='home', parent=section,
                            permission=view_group_perm)

    assert _menu_for(UserFactory()) == []


def test_inactive_children_are_left_out():
    section = MenuItem.objects.create(label='Catalog')
    MenuItem.objects.create(label='Active', url_name='home', parent=section)
    MenuItem.objects.create(label='Old', url_name='home', parent=section, is_active=False)

    assert _labels(_menu_for(UserFactory())) == {'Catalog': ['Active']}


def test_anonymous_users_get_no_menu():
    MenuItem.objects.create(label='Home', url_name='home')

    assert _menu_for(AnonymousUser()) == []
