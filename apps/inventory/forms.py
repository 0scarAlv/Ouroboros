from django import forms
from .models import Category
from core.utils.forms import BaseModelForm, TextInput, Textarea


class CategoryForm(BaseModelForm):
    name = forms.CharField(
        label='Nombre',
        widget=TextInput(attrs={'placeholder': 'Ej. Electrónica'})
    )
    slug = forms.SlugField(
        label='Slug',
        widget=TextInput(attrs={'placeholder': 'ej. electronica'})
    )
    description = forms.CharField(
        label='Descripción',
        required=False,
        widget=Textarea(attrs={'placeholder': 'Opcional'})
    )

    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']