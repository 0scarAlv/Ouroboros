from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from django.urls import reverse_lazy
from .forms import CategoryForm
from .services import CategoryService
from django.shortcuts import redirect,render
from django.views import View



class CategoryListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return CategoryService.get_all()

class CategoryFormPanelView(LoginRequiredMixin, View):
    def get(self, request):
        form = CategoryForm()
        return render(request, 'inventory/_category_form.html', {'form': form})

class CategoryCreateView(LoginRequiredMixin, CreateView):
    template_name = 'inventory/category_form.html'
    form_class = CategoryForm

    def form_valid(self, form):
        CategoryService.create(form.cleaned_data, self.request.user)
        if self.request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = str(reverse_lazy('inventory:category-list'))
            response['HX-Trigger'] = '{"showToast": {"message": "Categoría creada correctamente", "type": "success"}}'
            return response
        return redirect('inventory:category-list')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'inventory/category_form.html'
    form_class = CategoryForm

    def get_object(self):
        return CategoryService.get_by_id(self.kwargs['pk'])

    def form_valid(self, form):
        CategoryService.update(self.get_object(), form.cleaned_data, self.request.user)
        response = HttpResponse()
        response['HX-Redirect'] = reverse_lazy('inventory:category-list')
        response['HX-Trigger'] = '{"showToast": {"message": "Categoría actualizada correctamente", "type": "success"}}'
        return response

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'inventory/category_confirm_delete.html'

    def get_object(self):
        return CategoryService.get_by_id(self.kwargs['pk'])

    def form_valid(self, form):
        CategoryService.create(form.cleaned_data, self.request.user)
        if self.request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = str(reverse_lazy('inventory:category-list'))
            response['HX-Trigger'] = '{"showToast": {"message": "Categoría creada correctamente", "type": "success"}}'
            return response
        return redirect('inventory:category-list')