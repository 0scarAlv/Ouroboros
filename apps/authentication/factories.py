import factory
from django.contrib.auth.models import Permission

from .models import User

TEST_PASSWORD = 'test-password'


class UserFactory(factory.django.DjangoModelFactory):
    """User with a known password (TEST_PASSWORD), for login in tests."""

    class Meta:
        model = User
        django_get_or_create = ['username']
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda user: f'{user.username}@example.com')
    password = factory.django.Password(TEST_PASSWORD)

    @factory.post_generation
    def permissions(user, create, extracted, **kwargs):
        """UserFactory(permissions=['parties.view_party', ...])"""
        if not create or not extracted:
            return
        for perm in extracted:
            app_label, codename = perm.split('.')
            user.user_permissions.add(
                Permission.objects.get(content_type__app_label=app_label, codename=codename)
            )


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True
