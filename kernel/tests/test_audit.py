from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from kernel.current_user import acting_as, get_current_user
from kernel.middleware import CurrentUserMiddleware
from kernel.tests.models import AuditedNote, TrackedNote

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
            note = AuditedNote.objects.create(title='Ana')
        with acting_as(self.bob):
            note.title = 'Ana López'
            note.save()

        note.refresh_from_db()
        self.assertEqual(note.created_by, self.alice)
        self.assertEqual(note.updated_by, self.bob)

    def test_saving_without_a_user_keeps_previous_audit_fields(self):
        with acting_as(self.alice):
            note = AuditedNote.objects.create(title='Ana')
        note.save()

        note.refresh_from_db()
        self.assertEqual(note.updated_by, self.alice)

    def test_soft_delete_hides_from_default_manager(self):
        with acting_as(self.alice):
            note = AuditedNote.objects.create(title='Ana')
            note.soft_delete()

        self.assertFalse(AuditedNote.objects.filter(pk=note.pk).exists())
        stored = AuditedNote.all_objects.get(pk=note.pk)
        self.assertTrue(stored.is_deleted)
        self.assertEqual(stored.deleted_by, self.alice)
        self.assertEqual(list(AuditedNote.all_objects.deleted()), [stored])

    def test_restore_brings_record_back(self):
        note = AuditedNote.objects.create(title='Ana')
        note.soft_delete(user=self.alice)
        note.restore()

        note.refresh_from_db()
        self.assertTrue(AuditedNote.objects.filter(pk=note.pk).exists())
        self.assertIsNone(note.deleted_by)

    def test_partial_save_also_refreshes_updated_audit_fields(self):
        note = AuditedNote.objects.create(title='Ana')
        before = note.updated_at
        with acting_as(self.bob):
            note.notes = 'changed'
            note.save(update_fields=['notes'])

        note.refresh_from_db()
        self.assertEqual(note.updated_by, self.bob)
        self.assertGreater(note.updated_at, before)


class TrackedModelTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='x')
        self.bob = User.objects.create_user('bob', password='x')

    def test_history_keeps_every_version_and_who_made_it(self):
        with acting_as(self.alice):
            note = TrackedNote.objects.create(title='Ana', code='01234567-8')
        with acting_as(self.bob):
            note.code = '09999999-9'
            note.save()

        newest, oldest = note.history.all()
        self.assertEqual((oldest.history_type, oldest.code, oldest.history_user), ('+', '01234567-8', self.alice))
        self.assertEqual((newest.history_type, newest.code, newest.history_user), ('~', '09999999-9', self.bob))
        delta = newest.diff_against(oldest)
        self.assertEqual([(c.field, c.old, c.new) for c in delta.changes], [('code', '01234567-8', '09999999-9')])

    def test_soft_delete_is_recorded_in_history(self):
        note = TrackedNote.objects.create(title='Ana')
        note.soft_delete(user=self.alice)

        self.assertIsNotNone(note.history.first().deleted_at)

