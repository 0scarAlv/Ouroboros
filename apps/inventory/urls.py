from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('categories/',            views.CategoryListView.as_view(),   name='category-list'),
    path('categories/new/',        views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<uuid:pk>/edit/',   views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<uuid:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),
    path('categories/form/', views.CategoryFormPanelView.as_view(), name='category-form-panel'),
]