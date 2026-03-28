from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from apps.authentication.forms import LoginForm
import json

class LoginView(View):
    """Handles user login via html templates"""
    template_name = "authentication/login.html"

    def get(self, request):
        """Remder login form. Redirect if alredy authenticated"""
        if request.user.is_authenticated:
            return redirect("home")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request):
        """Process login form submission."""
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            response = HttpResponse(status=200)
            response["HX-Redirect"] = "/"
            return response
        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps({
            "showToast": {
                "message": "Usuario o contraseña incorrecto",
                "type": "danger"
            }
        })
        return response


class LogoutView(View):
    """Handles user logout"""
    
    def post(self, request):
        logout(request)
        return redirect("login")