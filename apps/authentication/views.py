from django.conf import settings
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from apps.authentication.forms import LoginForm
import json

class LoginView(View):
    """Handles user login via html templates"""
    template_name = "authentication/login.html"
    form_fragment = "authentication/_login_form.html"

    def get(self, request):
        """Render login form. Redirect if already authenticated."""
        if request.user.is_authenticated:
            return redirect("home")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Process login form submission via HTMX."""
        form = LoginForm(request.POST, request=request)

        if form.is_valid():
            login(request, form.get_user())
            response = HttpResponse(status=200)
            response["HX-Redirect"] = "/"
            return response

        has_field_errors = any(
            field != "__all__" for field in form.errors
        )
        if has_field_errors:
            return render(request, self.form_fragment, {"form": form})

        # Credentials failed — return a clean form + fire toast
        return login_form_with_toast(request, "Usuario o contraseña incorrectos.")


def login_form_with_toast(request, message, status=200):
    """Clean login form fragment plus an error toast (HTMX)."""
    response = render(request, LoginView.form_fragment, {"form": LoginForm()}, status=status)
    response["HX-Trigger"] = json.dumps({
        "showToast": {"message": message, "type": "danger"}
    })
    return response


def locked_out(request, credentials, *args, **kwargs):
    """
    Response for a locked account (django-axes AXES_LOCKOUT_CALLABLE).
    HTMX only swaps 2xx responses, so the login form gets a 200 with a toast.
    """
    minutes = int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)
    message = (
        "Cuenta bloqueada por demasiados intentos fallidos. "
        f"Intenta de nuevo en {minutes} minutos o contacta al administrador."
    )
    if request.headers.get("HX-Request"):
        return login_form_with_toast(request, message)
    return HttpResponse(message, status=429, content_type="text/plain; charset=utf-8")


class LogoutView(View):
    """Handles user logout"""

    def post(self, request):
        logout(request)
        return redirect("login")