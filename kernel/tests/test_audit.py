from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from kernel.constants.general import PersonRole
from kernel.current_user import acting_as, get_current_user
from kernel.middleware import CurrentUserMiddleware
from kernel.models import Person, PersonRoleAssignment

User = get_user_model()


class CurrentUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='x')

    def test_no_user_outside_a_request(self):
        self.assertIsNone(get_current_user())

    def test_anonymous_user_counts_as_none(self):
        with acting_as(AnonymousUser()):
            self.assertIsNone(get_current_user())

    def test_middleware_exposes_request_user_only_during_the_request(self):
        seen = []

        def view(request):
            seen.append(get_current_user())
            return HttpResponse()

        request = RequestFactory().get('/')
        request.user = self.user
        CurrentUserMiddleware(view)(request)

        self.assertEqual(seen, [self.user])
        self.assertIsNone(get_current_user())


class AuditModelTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.bob = User.objects.create_user('bob', password='x')

    def test_create_and_update_record_the_acting_user(self):
        with acting_as(self.alice):
            person = Person.objects.create(first_name='Ana')
        with acting_as(self.bob):
            person.last_name = 'López'
            person.save()

        person.refresh_from_db()
        self.assertEqual(person.created_by, self.alice)
        self.assertEqual(person.updated_by, self.bob)

    def test_saving_without_a_user_keeps_previous_audit_fields(self):
        with acting_as(self.alice):
            person = Person.objects.create(first_name='Ana')
        person.save()

        person.refresh_from_db()
        self.assertEqual(person.updated_by, self.alice)

    def test_soft_delete_hides_from_default_manager(self):
        with acting_as(self.alice):
            person = Person.objects.create(first_name='Ana')
            person.soft_delete()

        self.assertFalse(Person.objects.filter(pk=person.pk).exists())
        stored = Person.all_objects.get(pk=person.pk)
        self.assertTrue(stored.is_deleted)
        self.assertEqual(stored.deleted_by, self.alice)
        self.assertEqual(list(Person.all_objects.deleted()), [stored])

    def test_restore_brings_record_back(self):
        person = Person.objects.create(first_name='Ana')
        person.soft_delete(user=self.alice)
        person.restore()

        person.refresh_from_db()
        self.assertTrue(Person.objects.filter(pk=person.pk).exists())
        self.assertIsNone(person.deleted_by)

    def test_partial_save_also_refreshes_updated_audit_fields(self):
        person = Person.objects.create(first_name='Ana')
        before = person.updated_at
        with acting_as(self.bob):
            person.notes = 'changed'
            person.save(update_fields=['notes'])

        person.refresh_from_db()
        self.assertEqual(person.updated_by, self.bob)
        self.assertGreater(person.updated_at, before)


class TrackedModelTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.bob = User.objects.create_user('bob', password='x')

    def test_history_keeps_every_version_and_who_made_it(self):
        with acting_as(self.alice):
            person = Person.objects.create(first_name='Ana', dui='01234567-8')
        with acting_as(self.bob):
            person.dui = '09999999-9'
            person.save()

        newest, oldest = person.history.all()
        self.assertEqual((oldest.history_type, oldest.dui, oldest.history_user), ('+', '01234567-8', self.alice))
        self.assertEqual((newest.history_type, newest.dui, newest.history_user), ('~', '09999999-9', self.bob))
        delta = newest.diff_against(oldest)
        self.assertEqual([(c.field, c.old, c.new) for c in delta.changes], [('dui', '01234567-8', '09999999-9')])

    def test_soft_delete_is_recorded_in_history(self):
        person = Person.objects.create(first_name='Ana')
        person.soft_delete(user=self.alice)

        self.assertIsNotNone(person.history.first().deleted_at)


class PersonRoleTests(TestCase):
    def test_roles_are_filterable_and_unique(self):
        person = Person.objects.create(company_name='Droguería X', person_type='legal')
        PersonRoleAssignment.objects.create(person=person, role=PersonRole.SUPPLIER)

        self.assertTrue(person.has_role(PersonRole.SUPPLIER))
        self.assertFalse(person.has_role(PersonRole.CLIENTE))
        self.assertEqual(list(Person.objects.filter(role_assignments__role=PersonRole.SUPPLIER)), [person])
        with self.assertRaises(IntegrityError):
            PersonRoleAssignment.objects.create(person=person, role=PersonRole.SUPPLIER)
