from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from apps.authentication.forms import LoginForm

class LoginView(View):
    """Handles user login via html templates"""
    template_name = "authentication/login.html"

    def get(self, request):
        """Remder login form. Redirect if alredy authenticated"""
        if request.user.is_authenticated:
            return redirect("/admin/")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})
    
    def post(self, request):
        """Process login form submission."""
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/admin/")
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    """Handles user logout"""
    
    def post(self, request):
        logout(request)
        return redirect("login")