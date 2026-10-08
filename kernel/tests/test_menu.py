import re

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.test import RequestFactory
from django.urls import reverse

from apps.authentication.factories import AdminFactory, UserFactory
from kernel.admin import MenuItemForm
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


@pytest.mark.urls('kernel.tests.urls')
def test_sidebar_marks_the_current_section_on_every_page_of_its_crud(client):
    section = MenuItem.objects.create(label='Catalog', icon='category')
    MenuItem.objects.create(label='Notes', url_name='kernel_tests:trackednote_list', parent=section)
    MenuItem.objects.create(label='Plain', url_name='kernel_tests:plainnote_list', parent=section)
    client.force_login(AdminFactory())

    body = client.get(reverse('kernel_tests:trackednote_create')).content.decode()

    assert body.count('aria-current="page"') == 1
    assert re.search(r'aria-current="page">\s*<span class="sidebar__label">Notes<', body)
    assert 'aria-expanded="true"' in body  # its section is open


def test_sidebar_leaves_out_unknown_icons_and_broken_routes(client):
    MenuItem.objects.create(label='Listado', icon='list', url_name='no_such_route')
    client.force_login(UserFactory())

    response = client.get(reverse('home'))

    body = response.content.decode()
    assert response.status_code == 200
    assert '>list<' not in body
    assert re.search(r'<a href="#" class="sidebar__link"', body)


def test_admin_rejects_icons_missing_from_the_vendored_font():
    form = MenuItemForm(data={'label': 'Listado', 'icon': 'list', 'order': 0, 'is_active': True})
    valid = MenuItemForm(data={'label': 'Listado', 'icon': 'inventory_2', 'order': 0, 'is_active': True})

    assert 'icon' in form.errors
    assert valid.is_valid(), valid.errors
