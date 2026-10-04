from simple_history.models import HistoricalRecords

from kernel.current_user import get_current_user
from .audit_model import AuditModel


def _history_user(instance, request=None, **kwargs):
    return get_current_user()


class TrackedModel(AuditModel):
    """
    Audit level 2: AuditModel plus a full history of every change
    (previous and new values, who and when), stored in a Historical<Model>
    table and reachable through `instance.history`.

    Use it for records that must be traceable; keep high-volume tables
    on BaseModel or AuditModel.
    """

    history = HistoricalRecords(inherit=True, get_user=_history_user)

    class Meta(AuditModel.Meta):
        abstract = True
