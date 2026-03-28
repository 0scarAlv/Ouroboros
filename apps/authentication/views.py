from django.contrib.auth import authenticate, login, logout
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
        form = LoginForm(request.POST)

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
        response = render(request, self.form_fragment, {"form": LoginForm()})
        response["HX-Trigger"] = json.dumps({
            "showToast": {
                "message": "Usuario o contraseña incorrectos.",
                "type": "danger"
            }
        })
        return response


class LogoutView(View):
    """Handles user logout"""

    def post(self, request):
        logout(request)
        return redirect("login")