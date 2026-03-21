from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View

class LoginView(View):
    """Handles user login via html templates"""
    template_name = "authentication/login.html"

    def get(self, request):
        """Remder login form. Redirect if alredy authenticated"""
        if request.user.is_authenticated:
            return redirect("/admin/")
        return render(request, self.template_name)
    
    def post(self, request):
        """Process login form submission."""
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request,user)
            return redirect("/admin/")
        return render(request, self.template_name, {"error": "Invalid credentials"})
    
class LogoutView(View):
    """Handles user logout"""
    
    def post(self, request):
        logout(request)
        return redirect("login")