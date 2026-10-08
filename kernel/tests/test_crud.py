import json
import re

import pytest
from django.urls import reverse

from apps.authentication.factories import AdminFactory, UserFactory
from kernel.models import SecurityEvent

from .models import AuditedNote, PlainNote, TrackedNote

pytestmark = [pytest.mark.django_db, pytest.mark.urls('kernel.tests.urls')]

ALL_PERMS = [
    f'kernel_tests.{action}_trackednote' for action in ('view', 'add', 'change', 'delete')
]


@pytest.fixture
def editor(client):
    user = UserFactory(permissions=ALL_PERMS)
    client.force_login(user)
    return user


@pytest.fixture
def note():
    return TrackedNote.objects.create(title='Primera', code='A1')


def test_anonymous_users_are_sent_to_login(client):
    response = client.get(reverse('kernel_tests:trackednote_list'))

    assert response.status_code == 302
    assert response.url.startswith('/auth/login/')


def test_users_without_the_permission_get_403_and_it_is_logged(client, note):
    client.force_login(UserFactory(permissions=['kernel_tests.view_trackednote']))

    response = client.get(reverse('kernel_tests:trackednote_update', args=[note.pk]))

    assert response.status_code == 403
    assert SecurityEvent.objects.filter(kind=SecurityEvent.Kind.PERMISSION_DENIED).exists()


def test_list_shows_records_and_only_permitted_actions(client, note):
    client.force_login(UserFactory(permissions=['kernel_tests.view_trackednote']))

    response = client.get(reverse('kernel_tests:trackednote_list'))

    assert response.status_code == 200
    assert 'Primera' in response.content.decode()
    assert response.context['crud']['can_add'] is False
    assert response.context['crud']['can_change'] is False
    assert reverse('kernel_tests:trackednote_update', args=[note.pk]) not in response.content.decode()


def test_actions_without_a_route_are_not_offered(client):
    client.force_login(AdminFactory())

    response = client.get(reverse('kernel_tests:auditednote_list'))

    assert response.status_code == 200
    assert set(response.context['crud']['urls']) == {'list'}
    assert response.context['crud']['can_add'] is False


def test_search_filters_and_htmx_gets_only_the_table(client, editor):
    TrackedNote.objects.create(title='Aspirina', code='X')
    TrackedNote.objects.create(title='Ibuprofeno', code='Y')

    response = client.get(
        reverse('kernel_tests:trackednote_list'), {'q': 'aspi'}, HTTP_HX_REQUEST='true',
    )

    body = response.content.decode()
    assert 'Aspirina' in body
    assert 'Ibuprofeno' not in body
    assert '<html' not in body


def test_list_is_paginated(client, editor):
    for n in range(3):
        TrackedNote.objects.create(title=f'Nota {n}')

    response = client.get(reverse('kernel_tests:trackednote_list'), {'page': 2})

    assert response.context['page_obj'].number == 2
    assert len(response.context['object_list']) == 1


def test_create_saves_the_record_with_its_author(client, editor):
    response = client.post(
        reverse('kernel_tests:trackednote_create'), {'title': 'Nueva', 'code': 'N1'}, follow=True,
    )

    created = TrackedNote.objects.get(title='Nueva')
    assert created.created_by == editor
    assert 'Registro «Nueva» creado.' in [str(m) for m in response.context['messages']]


def test_invalid_form_is_shown_again_with_errors(client, editor):
    response = client.post(reverse('kernel_tests:trackednote_create'), {'title': ''})

    assert response.status_code == 200
    assert response.context['form'].errors['title'] == ['FIELD_REQUIRED']
    assert 'Este campo es obligatorio.' in response.content.decode()


def test_update_changes_the_record(client, editor, note):
    client.post(
        reverse('kernel_tests:trackednote_update', args=[note.pk]), {'title': 'Editada', 'code': 'A1'},
    )

    note.refresh_from_db()
    assert note.title == 'Editada'
    assert note.updated_by == editor


def test_delete_asks_first_and_then_soft_deletes(client, editor, note):
    url = reverse('kernel_tests:trackednote_delete', args=[note.pk])

    assert client.get(url).status_code == 200
    assert TrackedNote.objects.filter(pk=note.pk).exists()

    client.post(url)

    assert not TrackedNote.objects.filter(pk=note.pk).exists()
    assert TrackedNote.all_objects.get(pk=note.pk).deleted_by == editor


def test_records_without_audit_are_deleted_for_real(client):
    note = PlainNote.objects.create(title='Temporal')
    client.force_login(UserFactory(permissions=['kernel_tests.delete_plainnote']))

    client.post(reverse('kernel_tests:plainnote_delete', args=[note.pk]))

    assert not PlainNote.objects.filter(pk=note.pk).exists()


def test_deleted_records_are_not_found(client, editor, note):
    note.soft_delete()

    response = client.get(reverse('kernel_tests:trackednote_detail', args=[note.pk]))

    assert response.status_code == 404


def test_detail_shows_own_fields(client, editor, note):
    response = client.get(reverse('kernel_tests:trackednote_detail', args=[note.pk]))

    assert response.context['detail_fields'] == ['title', 'code']
    assert 'A1' in response.content.decode()


def test_history_lists_changes_with_who_made_them(client, editor, note):
    client.post(
        reverse('kernel_tests:trackednote_update', args=[note.pk]), {'title': 'Cambiada', 'code': 'A1'},
    )

    response = client.get(reverse('kernel_tests:trackednote_history', args=[note.pk]))

    latest, first = response.context['entries']
    assert latest['record'].history_user == editor
    assert [(c['old'], c['new']) for c in latest['changes']] == [('Primera', 'Cambiada')]
    assert first['record'].history_type == '+'


# -- List page: one toolbar acting on the selected row, panel above the table --

HX = {'HTTP_HX_REQUEST': 'true'}


def _toolbar_actions(body):
    return set(re.findall(r'data-crud-action="(\w+)"', body))


def test_list_has_one_toolbar_and_no_per_row_buttons(client, editor, note):
    response = client.get(reverse('kernel_tests:trackednote_list'))

    body = response.content.decode()
    assert _toolbar_actions(body) == {'create', 'update', 'delete', 'history'}
    assert 'id="crud-panel-body"' in body
    # Each row carries its action URLs as data, never as buttons or links.
    tbody = body.split('<tbody>')[1].split('</tbody>')[0]
    assert f'data-update-url="{reverse("kernel_tests:trackednote_update", args=[note.pk])}"' in tbody
    assert f'data-delete-url="{reverse("kernel_tests:trackednote_delete", args=[note.pk])}"' in tbody
    assert '<a ' not in tbody and '<button' not in tbody


def test_toolbar_only_offers_permitted_actions(client, note):
    client.force_login(UserFactory(permissions=['kernel_tests.view_trackednote']))

    body = client.get(reverse('kernel_tests:trackednote_list')).content.decode()

    # Without change permission, Ver replaces Modificar.
    assert _toolbar_actions(body) == {'history', 'detail'}
    assert 'data-update-url' not in body
    assert 'data-delete-url' not in body
    assert 'data-crud-default="detail"' in body


def test_list_without_other_routes_offers_no_actions(client):
    record = AuditedNote.objects.create(title='Sola')
    client.force_login(AdminFactory())

    body = client.get(reverse('kernel_tests:auditednote_list')).content.decode()

    assert _toolbar_actions(body) == set()
    assert f'data-pk="{record.pk}"' in body
    assert 'data-crud-default=""' in body


@pytest.mark.parametrize('route', ['create', 'update', 'delete', 'history', 'detail'])
def test_htmx_requests_get_the_panel_partial(client, editor, note, route):
    args = [] if route == 'create' else [note.pk]
    url = reverse(f'kernel_tests:trackednote_{route}', args=args)

    panel = client.get(url, **HX).content.decode()
    page = client.get(url).content.decode()

    assert '<html' not in panel
    assert 'class="panel' in panel
    assert 'data-crud-close' in panel
    # The full page wraps the same partial and works without htmx.
    assert '<html' in page
    assert 'class="panel' in page
    assert 'data-crud-close' not in page
    assert 'hx-post' not in page
    if route in ('create', 'update', 'delete'):
        assert f'hx-post="{url}"' in panel


def test_htmx_create_answers_204_with_a_toast_and_no_message(client, editor):
    response = client.post(
        reverse('kernel_tests:trackednote_create'), {'title': '<b>Nueva</b>', 'code': 'N1'}, **HX,
    )

    created = TrackedNote.objects.get(code='N1')
    assert response.status_code == 204
    header = response['HX-Trigger']
    assert header.isascii()
    trigger = json.loads(header)
    assert trigger['showToast'] == {'message': 'Registro «<b>Nueva</b>» creado.', 'type': 'success'}
    assert trigger['crudChanged'] == {'action': 'create', 'pk': str(created.pk)}
    # The toast replaces the flash message: nothing is left for the next page.
    assert list(client.get(reverse('kernel_tests:trackednote_list')).context['messages']) == []


def test_htmx_invalid_form_is_shown_again_in_the_panel(client, editor):
    url = reverse('kernel_tests:trackednote_create')

    response = client.post(url, {'title': ''}, **HX)

    body = response.content.decode()
    assert response.status_code == 200
    assert 'HX-Trigger' not in response
    assert '<html' not in body
    assert 'Este campo es obligatorio.' in body
    assert f'hx-post="{url}"' in body


def test_htmx_update_answers_204(client, editor, note):
    response = client.post(
        reverse('kernel_tests:trackednote_update', args=[note.pk]), {'title': 'Editada', 'code': 'A1'}, **HX,
    )

    note.refresh_from_db()
    assert response.status_code == 204
    assert note.title == 'Editada'
    assert json.loads(response['HX-Trigger'])['crudChanged'] == {'action': 'update', 'pk': str(note.pk)}


def test_htmx_delete_answers_204_with_the_deleted_pk(client):
    note = PlainNote.objects.create(title='Temporal')
    pk = note.pk
    client.force_login(UserFactory(permissions=['kernel_tests.delete_plainnote']))

    response = client.post(reverse('kernel_tests:plainnote_delete', args=[pk]), **HX)

    assert response.status_code == 204
    trigger = json.loads(response['HX-Trigger'])
    assert trigger['crudChanged'] == {'action': 'delete', 'pk': str(pk)}
    assert trigger['showToast']['type'] == 'success'
    assert not PlainNote.objects.filter(pk=pk).exists()


def test_delete_confirmation_says_whether_the_record_is_kept(client, editor, note):
    tracked = client.get(reverse('kernel_tests:trackednote_delete', args=[note.pk]), **HX)
    plain_note = PlainNote.objects.create(title='Temporal')
    client.force_login(AdminFactory())
    plain = client.get(reverse('kernel_tests:plainnote_delete', args=[plain_note.pk]), **HX)

    assert 'dejará de aparecer en los listados' in tracked.content.decode()
    assert 'se borrará definitivamente' in plain.content.decode()


def test_out_of_range_page_shows_the_last_one(client, editor):
    for n in range(3):
        TrackedNote.objects.create(title=f'Nota {n}')

    response = client.get(reverse('kernel_tests:trackednote_list'), {'page': 9}, **HX)

    assert response.status_code == 200
    assert response.context['page_obj'].number == 2


def test_toolbar_buttons_carry_what_the_cancel_toggle_needs(client, editor):
    body = client.get(reverse('kernel_tests:trackednote_list')).content.decode()

    buttons = re.findall(r'<(?:a|button) [^>]*data-crud-action="[^"]*"[^>]*>', body)
    assert len(buttons) == 4
    for button in buttons:
        # crud.js swaps the label/icon to "Cancelar" and restores them from these.
        assert 'aria-controls="crud-panel"' in button
        assert 'aria-expanded="false"' in button
        assert re.search(r'data-label="\w+"', button)
        assert re.search(r'data-icon="\w+"', button)
    labels = dict(re.findall(r'data-label="(\w+)" data-icon="\w+" data-crud-action="(\w+)"', body))
    assert labels == {'Nuevo': 'create', 'Modificar': 'update', 'Eliminar': 'delete', 'Historial': 'history'}
    assert body.count('data-crud-label>') == 4 and body.count('data-crud-icon>') == 4


def test_panel_forms_keep_their_own_cancel_button(client, editor, note):
    for route, args in (('create', []), ('update', [note.pk]), ('delete', [note.pk])):
        body = client.get(reverse(f'kernel_tests:trackednote_{route}', args=args), **HX).content.decode()
        assert re.search(r'<button type="button" class="btn btn-tool btn-sm" data-crud-close[^>]*>Cancelar</button>', body)
