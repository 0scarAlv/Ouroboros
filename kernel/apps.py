from django.apps import AppConfig


class KernelConfig(AppConfig):
    name = 'kernel'
    verbose_name = 'Kernel'

    def ready(self):
        from kernel import security_events  # noqa: F401  (connects signal receivers)
