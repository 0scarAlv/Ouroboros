from .home import HomeView
from .crud import (
    CrudCreateView,
    CrudDeleteView,
    CrudDetailView,
    CrudHistoryView,
    CrudListView,
    CrudUpdateView,
)

__all__ = [
    'HomeView',
    'CrudListView',
    'CrudDetailView',
    'CrudCreateView',
    'CrudUpdateView',
    'CrudDeleteView',
    'CrudHistoryView',
]
