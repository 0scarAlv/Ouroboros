from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Serve the application with waitress, a production server that runs '
        'on Windows and Linux. Static files are served by WhiteNoise, so run '
        'collectstatic first.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--host', default='0.0.0.0', help='0.0.0.0 accepts devices on the local network.')
        parser.add_argument('--port', type=int, default=8000)
        parser.add_argument('--threads', type=int, default=8)

    def handle(self, *args, host, port, threads, **options):
        if settings.DEBUG:
            raise CommandError('DEBUG is on: use runserver for development, or the onprem/prod settings.')
        try:
            from waitress import serve
        except ImportError:
            raise CommandError('waitress is not installed: pip install -r requirements/onprem.txt')
        from django.core.wsgi import get_wsgi_application

        self.stdout.write(f'Serving on http://{host}:{port} with {threads} threads')
        serve(get_wsgi_application(), host=host, port=port, threads=threads)
