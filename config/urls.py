from django.contrib import admin
from django.urls import path, include
from kernel.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/", include("apps.authentication.urls")),
    path("attachments/", include("apps.attachments.urls")),
    path("", HomeView.as_view(), name="home"),
    
]