from django.apps import AppConfig


class KernelTestsConfig(AppConfig):
    """Test-only app holding concrete models to exercise the abstract kernel models."""
    name = 'kernel.tests'
    label = 'kernel_tests'
