from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from especialidades.forms import EspecialidadesForm









from .models import Especialidades
from django.urls import reverse_lazy
from django.contrib import messages

# Crud Especialidades
class EspecialidadesListView(ListView):
    model = Especialidades
    template_name = 'especialidades/especialidades.html' 
    context_object_name = 'especialidades'

class EspecialidadesDetailView(DeleteView):
     model=Especialidades
  

class EspecialidadesCreateView(CreateView):   
    model = Especialidades
    form_class= EspecialidadesForm
    
    
    
    success_url = reverse_lazy('especialidades:list')
   
    def form_valid(self, form):
        # Guarda los datos si el formulario es válido
        messages.success(self.request, 'Especialidad creado exitosamente.')

        # Verifica si se cargó una imagen en el formulario y muestra el nombre por consola
        if 'imagen' in form.cleaned_data:
            imagen = form.cleaned_data['imagen']
            print(f'Imagen cargada exitosamente: {imagen}')
        else:
            messages.warning(self.request, 'No se cargó ninguna imagen.')

        return super().form_valid(form)

    def form_invalid(self, form):
        # Maneja el caso en que el formulario no es válido
        messages.error(self.request, 'Hubo un error en el formulario.')
        return super().form_invalid(form)

class EspecialidadesUpdateView(UpdateView):
    model=Especialidades
    success_url = reverse_lazy('especialidades:list')
    fields= ["descripcion", "img" ]
    template_name_suffix = '_update_form' 
    def get_success_url(self):
      return reverse_lazy('especialidades:update', args=[self.object.id]) + '?ok'

class EspecialidadesDeleteView(DeleteView):
    model=Especialidades
    success_url = reverse_lazy('especialidades:list')
    

