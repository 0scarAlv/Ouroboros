from django.apps import AppConfig


class AttachmentsTestsConfig(AppConfig):
    """Test-only app with a model that uses HasAttachments."""
    name = 'apps.attachments.tests'
    label = 'attachments_tests'
