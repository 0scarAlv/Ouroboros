import pytest
from django.urls import reverse

from apps.authentication.factories import AdminFactory, UserFactory
from kernel.models import SecurityEvent

from .models import PlainNote, TrackedNote

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


