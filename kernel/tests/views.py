from kernel.utils.forms import BaseModelForm
from kernel.views import (
    CrudCreateView,
    CrudDeleteView,
    CrudDetailView,
    CrudHistoryView,
    CrudListView,
    CrudUpdateView,
)

from .models import AuditedNote, PlainNote, TrackedNote


class TrackedNoteForm(BaseModelForm):
    class Meta:
        model = TrackedNote
        fields = ['title', 'code']


class TrackedNoteViewMixin:
    model = TrackedNote
    form_class = TrackedNoteForm


class TrackedNoteList(TrackedNoteViewMixin, CrudListView):
    search_fields = ['title', 'code']
    list_display = ['title', 'code']
    paginate_by = 2


class TrackedNoteDetail(TrackedNoteViewMixin, CrudDetailView):
    pass


class TrackedNoteCreate(TrackedNoteViewMixin, CrudCreateView):
    pass


class TrackedNoteUpdate(TrackedNoteViewMixin, CrudUpdateView):
    pass


class TrackedNoteDelete(TrackedNoteViewMixin, CrudDeleteView):
    pass


class TrackedNoteHistory(TrackedNoteViewMixin, CrudHistoryView):
    pass


class AuditedNoteList(CrudListView):
    """Only a list route: the other actions must not be offered."""
    model = AuditedNote


class PlainNoteList(CrudListView):
    model = PlainNote


class PlainNoteDelete(CrudDeleteView):
    model = PlainNote
