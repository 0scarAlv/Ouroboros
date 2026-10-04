import factory
import pytest

# Test data in Spanish (Latin America): names, addresses, phones.
factory.Faker._DEFAULT_LOCALE = 'es_MX'


@pytest.fixture(autouse=True)
def _isolated_media_root(settings, tmp_path):
    """Uploaded files go to a temporary folder, never to the real MEDIA_ROOT."""
    settings.MEDIA_ROOT = tmp_path / 'media'
