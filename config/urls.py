from django.contrib import admin
from django.urls import path, include
from core.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/", include("apps.authentication.urls")),
    path('inventory/', include('apps.inventory.urls')),
    path("", HomeView.as_view(), name="home"),
    
]