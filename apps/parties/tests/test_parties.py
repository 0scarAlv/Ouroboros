from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from apps.parties.constants import IdentifierKind, PartyRole, PartyType
from apps.parties.models import Address, Party, PartyIdentifier
from kernel.current_user import acting_as

User = get_user_model()


class PartyTests(TestCase):
    def test_display_name_depends_on_party_type(self):
        person = Party(first_name='Ana', last_name='López')
        company = Party(party_type=PartyType.LEGAL, legal_name='Droguería X, S.A. de C.V.')
        branded = Party(party_type=PartyType.LEGAL, legal_name='Droguería X, S.A. de C.V.', trade_name='Droguería X')

        self.assertEqual(str(person), 'Ana López')
        self.assertEqual(str(company), 'Droguería X, S.A. de C.V.')
        self.assertEqual(str(branded), 'Droguería X')

    def test_required_name_depends_on_party_type(self):
        with self.assertRaises(ValidationError):
            Party(party_type=PartyType.LEGAL).full_clean()
        with self.assertRaises(ValidationError):
            Party(party_type=PartyType.NATURAL).full_clean()

    def test_email_can_be_shared(self):
        Party.objects.create(first_name='Ana', email='compras@x.com')
        Party.objects.create(first_name='Luis', email='compras@x.com')

    def test_can_be_linked_to_a_user(self):
        user = User.objects.create_user('ana', password='x')
        party = Party.objects.create(first_name='Ana', user=user)

        self.assertEqual(user.party, party)

    def test_changes_are_kept_in_history(self):
        alice = User.objects.create_user('alice', password='x')
        with acting_as(alice):
            party = Party.objects.create(first_name='Ana')
            party.phone = '2222-2222'
            party.save()

        self.assertEqual(party.history.count(), 2)
        self.assertEqual(party.history.first().history_user, alice)


class PartyRoleTests(TestCase):
    def setUp(self):
        self.party = Party.objects.create(party_type=PartyType.LEGAL, legal_name='Droguería X')

    def test_roles_are_filterable_and_unique(self):
        self.party.add_role(PartyRole.SUPPLIER)
        self.party.add_role(PartyRole.SUPPLIER)

        self.assertTrue(self.party.has_role(PartyRole.SUPPLIER))
        self.assertFalse(self.party.has_role(PartyRole.CLIENT))
        self.assertEqual(list(Party.objects.filter(roles__role=PartyRole.SUPPLIER)), [self.party])
        with self.assertRaises(IntegrityError):
            self.party.roles.create(role=PartyRole.SUPPLIER)

    def test_products_can_use_their_own_roles(self):
        self.party.add_role('pharmacist_in_charge')

        self.assertTrue(self.party.has_role('pharmacist_in_charge'))

    def test_role_can_be_given_again_after_soft_delete(self):
        self.party.add_role(PartyRole.CLIENT).soft_delete()

        self.assertFalse(self.party.has_role(PartyRole.CLIENT))
        self.party.add_role(PartyRole.CLIENT)
        self.assertTrue(self.party.has_role(PartyRole.CLIENT))


class PartyIdentifierTests(TestCase):
    def setUp(self):
        self.ana = Party.objects.create(first_name='Ana')
        self.luis = Party.objects.create(first_name='Luis')

    def test_values_are_normalized_and_default_to_the_configured_country(self):
        identifier = self.ana.identifiers.create(kind=' DUI ', value=' 01234567-8 ')

        self.assertEqual((identifier.kind, identifier.value, identifier.country), ('dui', '01234567-8', 'SV'))
        self.assertEqual(self.ana.get_identifier(IdentifierKind.DUI), '01234567-8')
        self.assertIsNone(self.ana.get_identifier(IdentifierKind.NIT))

    @override_settings(PARTIES_DEFAULT_COUNTRY='GT')
    def test_default_country_comes_from_settings(self):
        identifier = self.ana.identifiers.create(kind='passport', value='X1')

        self.assertEqual(identifier.country, 'GT')

    def test_value_is_unique_per_kind_and_country(self):
        self.ana.identifiers.create(kind=IdentifierKind.DUI, value='01234567-8')
        self.luis.identifiers.create(kind=IdentifierKind.PASSPORT, value='01234567-8')
        self.luis.identifiers.create(kind=IdentifierKind.DUI, value='01234567-8', country='GT')

        with self.assertRaises(IntegrityError):
            self.luis.identifiers.create(kind=IdentifierKind.DUI, value='01234567-8')

    def test_value_is_free_again_after_soft_delete(self):
        self.ana.identifiers.create(kind=IdentifierKind.DUI, value='01234567-8').soft_delete()

        self.luis.identifiers.create(kind=IdentifierKind.DUI, value='01234567-8')
        self.assertEqual(PartyIdentifier.all_objects.filter(value='01234567-8').count(), 2)


class AddressTests(TestCase):
    def test_only_one_primary_address_per_party(self):
        party = Party.objects.create(first_name='Ana')
        Address.objects.create(party=party, line1='Calle 1', city='San Salvador', is_primary=True)
        Address.objects.create(party=party, line1='Calle 2', city='Santa Tecla')

        with self.assertRaises(IntegrityError), transaction.atomic():
            Address.objects.create(party=party, line1='Calle 3', city='Soyapango', is_primary=True)

        self.assertEqual(party.addresses.first().line1, 'Calle 1')
