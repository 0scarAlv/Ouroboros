"""
Generic CRUD views for kernel models.

A module subclasses them, sets `model` (and `form_class` for create and
update) and wires them with the URL names `<app_label>:<model_name>_<action>`,
where action is list, detail, create, update, delete or history. The list
route is required (forms and deletes return to it); the others are optional
and the templates only offer the ones that exist. Every view
requires the matching Django model permission (view, add, change, delete):
anonymous users are sent to the login page and signed-in users without the
permission get a 403, which is recorded as a security event.

Templates live in templates/crud/ and can be overridden per model by adding
templates/<app_label>/<model_name>_<suffix>.html.
"""
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from kernel.models import AuditModel

ACTIONS = ('list', 'detail', 'create', 'update', 'delete', 'history')

# Any value accepted by a `<uuid:pk>` route; only used to test that a route exists.
_SAMPLE_PK = str(uuid.UUID(int=0))

# Fields every kernel model has; left out of the default detail view.
AUDIT_FIELDS = {
    'id', 'created_at', 'updated_at',
    'created_by', 'updated_by', 'deleted_at', 'deleted_by',
}


class CrudMixin(PermissionRequiredMixin):
    """Permission check, URL names and shared template context."""

    permission_action = None
    template_suffix = None

    def get_permission_required(self):
        opts = self.model._meta
        return [f'{opts.app_label}.{self.permission_action}_{opts.model_name}']

    def url_name(self, action):
        opts = self.model._meta
        return f'{opts.app_label}:{opts.model_name}_{action}'

    def get_template_names(self):
        opts = self.model._meta
        return [
            f'{opts.app_label}/{opts.model_name}_{self.template_suffix}.html',
            f'crud/{self.template_suffix}.html',
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opts = self.model._meta
        user = self.request.user
        urls = {}
        for action in ACTIONS:
            try:
                args = [] if action in ('list', 'create') else [_SAMPLE_PK]
                reverse(self.url_name(action), args=args)
            except NoReverseMatch:
                continue
            urls[action] = self.url_name(action)
        context['crud'] = {
            'verbose_name': opts.verbose_name,
            'verbose_name_plural': opts.verbose_name_plural,
            'urls': urls,
            'can_add': 'create' in urls and user.has_perm(f'{opts.app_label}.add_{opts.model_name}'),
            'can_change': 'update' in urls and user.has_perm(f'{opts.app_label}.change_{opts.model_name}'),
            'can_delete': 'delete' in urls and user.has_perm(f'{opts.app_label}.delete_{opts.model_name}'),
            'has_history': 'history' in urls and hasattr(self.model, 'history'),
        }
        return context


class CrudListView(CrudMixin, ListView):
    """
    Paginated list with a text search over `search_fields`.
    `list_display` names the columns. htmx requests (search, paging) get only
    the table back.
    """

    permission_action = 'view'
    template_suffix = 'list'
    partial_template_name = 'crud/_list_table.html'
    paginate_by = 25
    search_fields = ()
    list_display = ('__str__',)

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f'{field}__icontains': query})
            queryset = queryset.filter(condition)
        return queryset

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return [self.partial_template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_display'] = self.list_display
        context['query'] = self.request.GET.get('q', '')
        context['searchable'] = bool(self.search_fields)
        return context


class CrudDetailView(CrudMixin, DetailView):
    """Read-only view of a record. `detail_fields` defaults to every own field."""

    permission_action = 'view'
    template_suffix = 'detail'
    detail_fields = None

    def get_detail_fields(self):
        if self.detail_fields is not None:
            return self.detail_fields
        return [
            field.name for field in self.model._meta.concrete_fields
            if field.name not in AUDIT_FIELDS
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detail_fields'] = self.get_detail_fields()
        return context


class CrudFormMixin(CrudMixin):
    template_suffix = 'form'
    success_message = ''
    title = ''
    submit_label = 'Guardar'

    def get_success_url(self):
        return reverse(self.url_name('list'))

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message.format(object=self.object))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse(self.url_name('list'))
        context['title'] = self.title.format(verbose_name=self.model._meta.verbose_name)
        context['submit_label'] = self.submit_label
        return context


class CrudCreateView(CrudFormMixin, CreateView):
    permission_action = 'add'
    success_message = 'Registro «{object}» creado.'
    title = 'Nuevo {verbose_name}'
    submit_label = 'Crear'


class CrudUpdateView(CrudFormMixin, UpdateView):
    permission_action = 'change'
    success_message = 'Registro «{object}» actualizado.'
    title = 'Editar {verbose_name}'
    submit_label = 'Guardar cambios'


class CrudDeleteView(CrudMixin, DetailView):
    """
    Asks for confirmation on GET and deletes on POST. AuditModel records are
    soft-deleted (they stay in the database); other models are deleted.
    """

    permission_action = 'delete'
    template_suffix = 'confirm_delete'
    success_message = 'Registro «{object}» eliminado.'

    def get_success_url(self):
        return reverse(self.url_name('list'))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if isinstance(self.object, AuditModel):
            self.object.soft_delete(request.user)
        else:
            self.object.delete()
        messages.success(request, self.success_message.format(object=self.object))
        return HttpResponseRedirect(self.get_success_url())


class CrudHistoryView(CrudMixin, DetailView):
    """Change history of a TrackedModel record, newest first, with field diffs."""

    permission_action = 'view'
    template_suffix = 'history'

    def get(self, request, *args, **kwargs):
        if not hasattr(self.model, 'history'):
            raise ImproperlyConfigured(f'{self.model.__name__} has no history; use TrackedModel.')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = list(self.object.history.select_related('history_user'))
        entries = []
        for record, previous in zip(records, records[1:] + [None]):
            changes = []
            if previous is not None:
                delta = record.diff_against(previous)
                changes = [
                    {
                        'field': self.model._meta.get_field(change.field).verbose_name,
                        'old': change.old,
                        'new': change.new,
                    }
                    for change in delta.changes
                    if change.field not in AUDIT_FIELDS - {'deleted_at'}
                ]
            entries.append({'record': record, 'changes': changes})
        context['entries'] = entries
        return context
