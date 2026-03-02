from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from medicos.forms import MedicosForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


from .models import  Medico
from django.urls import reverse_lazy

# Crud Medicos

class MedicoListView(LoginRequiredMixin,ListView):
    model = Medico
    template_name = 'medicos/medicos.html' 
    context_object_name = 'medicos' 

class MedicoDetailView(LoginRequiredMixin,DeleteView):
     model=Medico

class MedicoCreateView(LoginRequiredMixin,CreateView):   
       model = Medico
       form_class = MedicosForm
       success_url = reverse_lazy('medicos:list')
    

       def form_valid(self, form):
        messages.success(self.request, 'Médico creado exitosamente.')

        # Verifica si se cargó una imagen en el formulario y muestra el nombre por consola
        if 'img' in form.cleaned_data:
            imagen = form.cleaned_data['img']
            print(f'Imagen cargada exitosamente: {imagen}')
        else:
            messages.warning(self.request, 'No se cargó ninguna imagen.')

        return super().form_valid(form)

       def form_invalid(self, form):
        messages.error(self.request, 'Hubo un error en el formulario.')
        return super().form_invalid(form)


class MedicoUpdateView(LoginRequiredMixin,UpdateView):
    model=Medico
    fields = [ 'email', 'telefono', 'img', 'especialidad']
    success_url = reverse_lazy('medicos:list')
    template_name_suffix = '_update_form'
    def get_success_url(self):
      return reverse_lazy('medicos:update', args=[self.object.id]) + '?ok'

class MedicoDeleteView(LoginRequiredMixin,DeleteView):
    model=Medico
    success_url = reverse_lazy('medicos:list')
    

