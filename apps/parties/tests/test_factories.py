import pytest

from apps.parties.factories import (
    AddressFactory,
    LegalPartyFactory,
    PartyFactory,
    PartyIdentifierFactory,
    PartyRoleFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('factory_class', [
    PartyFactory,
    LegalPartyFactory,
    PartyRoleFactory,
    PartyIdentifierFactory,
    AddressFactory,
])
def test_factories_build_valid_records(factory_class):
    record = factory_class()

    record.full_clean()


def test_identifier_values_do_not_collide():
    PartyIdentifierFactory.create_batch(20)
