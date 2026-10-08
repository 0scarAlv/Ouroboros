"""Project URLs plus CRUD routes for the kernel test models."""
from django.urls import include, path

from config.urls import urlpatterns as project_urlpatterns

from . import views

crud_patterns = ([
    path('tracked/', views.TrackedNoteList.as_view(), name='trackednote_list'),
    path('tracked/new/', views.TrackedNoteCreate.as_view(), name='trackednote_create'),
    path('tracked/<uuid:pk>/', views.TrackedNoteDetail.as_view(), name='trackednote_detail'),
    path('tracked/<uuid:pk>/edit/', views.TrackedNoteUpdate.as_view(), name='trackednote_update'),
    path('tracked/<uuid:pk>/delete/', views.TrackedNoteDelete.as_view(), name='trackednote_delete'),
    path('tracked/<uuid:pk>/history/', views.TrackedNoteHistory.as_view(), name='trackednote_history'),
    path('audited/', views.AuditedNoteList.as_view(), name='auditednote_list'),
    path('plain/', views.PlainNoteList.as_view(), name='plainnote_list'),
    path('plain/<uuid:pk>/delete/', views.PlainNoteDelete.as_view(), name='plainnote_delete'),
], 'kernel_tests')

urlpatterns = [path('notes/', include(crud_patterns)), *project_urlpatterns]
