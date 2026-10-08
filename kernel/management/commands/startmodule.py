import keyword
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template import Context, Engine

SCAFFOLD_DIR = Path(__file__).resolve().parents[2] / 'scaffold' / 'module'

AUDIT_LEVELS = {
    0: ('BaseModel', 'a UUID primary key and created/updated timestamps'),
    1: ('AuditModel', 'timestamps, who created and changed each record, and soft delete'),
    2: ('TrackedModel', 'everything AuditModel has plus a full change history'),
}


class Command(BaseCommand):
    help = (
        'Create a module in apps/<name>/ with one model and its CRUD views, '
        'URLs, admin, factory and tests, following the project conventions.'
    )

    def add_arguments(self, parser):
        parser.add_argument('name', help='Module (app) name in snake_case, e.g. products.')
        parser.add_argument('--model', help='Model class name, e.g. Product. Defaults to the module name in CamelCase.')
        parser.add_argument(
            '--audit', type=int, choices=sorted(AUDIT_LEVELS), default=1,
            help='0 = BaseModel, 1 = AuditModel (default), 2 = TrackedModel with history.',
        )
        parser.add_argument('--directory', help='Parent folder (default: apps/). Used by the scaffold tests.')
        parser.add_argument('--package', help="Dotted Python package (default: apps.<name>).")

    def handle(self, *args, name, model, audit, directory, package, **options):
        if not re.fullmatch(r'[a-z][a-z0-9_]*', name) or keyword.iskeyword(name):
            raise CommandError(f'"{name}" is not a valid module name: use snake_case, e.g. products.')
        camel_name = ''.join(part.capitalize() for part in name.split('_'))
        model = model or camel_name
        if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', model):
            raise CommandError(f'"{model}" is not a valid model name: use CamelCase, e.g. Product.')

        target = Path(directory or Path(settings.BASE_DIR) / 'apps') / name
        if target.exists():
            raise CommandError(f'{target} already exists.')

        base_class, audit_summary = AUDIT_LEVELS[audit]
        context = Context({
            'app_label': name,
            'package': package or f'apps.{name}',
            'config_class': f'{camel_name}Config',
            'model': model,
            'model_lower': model.lower(),
            'audit': audit,
            'base_class': base_class,
            'audit_summary': audit_summary,
        }, autoescape=False)
        engine = Engine()

        for source in sorted(SCAFFOLD_DIR.rglob('*-tpl')):
            relative = source.relative_to(SCAFFOLD_DIR)
            destination = target / relative.with_name(relative.name.removesuffix('-tpl'))
            destination.parent.mkdir(parents=True, exist_ok=True)
            rendered = engine.from_string(source.read_text(encoding='utf-8')).render(context)
            destination.write_text(rendered, encoding='utf-8')

        package = context['package']
        self.stdout.write(self.style.SUCCESS(f'Module created in {target}'))
        self.stdout.write(
            'Next steps:\n'
            f"  1. Add '{package}' to MODULE_APPS in config/settings/base.py\n"
            f"  2. Add path('{name}/', include('{package}.urls')) to config/urls.py\n"
            f'  3. python manage.py makemigrations {name} && python manage.py migrate\n'
            f'  4. pytest {target}\n'
            f"  5. In the admin, add a menu item with URL name '{name}:{model.lower()}_list'\n"
            f"     and permission '{name} | {model.lower()} | Can view {model.lower()}',\n"
            '     then give the permissions to a group.'
        )
