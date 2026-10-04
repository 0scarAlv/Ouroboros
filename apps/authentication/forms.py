from django import forms
from django.contrib.auth import authenticate
from kernel.utils.forms import BaseForm, TextInput, PasswordInput

class LoginForm(BaseForm):
    """Autentication form."""

    username = forms.CharField(
        label="Usuario",
        widget=TextInput(attrs={"placeholder": "Ingresa tu usuario"})
    )

    password = forms.CharField(
        label="Contraseña",
        widget=PasswordInput(attrs={"placeholder": "Ingresa tu contraseña"})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        
        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError("INVALID_CREDENTIALS")

        return cleaned_data

    def get_user(self):
        """Returns the authenticated user after successful validation."""
        return getattr(self, "user", None)
    
    