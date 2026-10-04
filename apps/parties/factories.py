import factory

from .constants import AddressKind, IdentifierKind, PartyType
from .models import Address, Party, PartyIdentifier, PartyRole


class PartyFactory(factory.django.DjangoModelFactory):
    """A natural person. Use LegalPartyFactory for companies."""

    class Meta:
        model = Party

    party_type = PartyType.NATURAL
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    phone = factory.Faker('numerify', text='7###-####')


class LegalPartyFactory(PartyFactory):
    party_type = PartyType.LEGAL
    first_name = ''
    last_name = ''
    legal_name = factory.Faker('company')
    trade_name = ''


class PartyRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartyRole

    party = factory.SubFactory(PartyFactory)
    role = 'client'


class PartyIdentifierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PartyIdentifier

    party = factory.SubFactory(PartyFactory)
    kind = IdentifierKind.DUI
    value = factory.Sequence(lambda n: f'{n:08d}-{n % 10}')


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    party = factory.SubFactory(PartyFactory)
    kind = AddressKind.HOME
    line1 = factory.Faker('street_address')
    city = factory.Faker('city')
    region = factory.Faker('state')
