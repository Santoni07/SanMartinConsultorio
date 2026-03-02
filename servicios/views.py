from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView,CreateView,DeleteView,UpdateView

from servicios.forms import ServiciosForm
from django.contrib import messages

from .models import Servicios

# Create your views here.
@login_required
class ServiciosListView(ListView):
    model = Servicios
    template_name = 'servicios/servicios.html'
    context_object_name = 'servicios'

@login_required
class ServiciosDetailView(DeleteView):
    pass 

@login_required
class ServiciosCreateView(CreateView):
    model = Servicios
    form_class = ServiciosForm
    success_url = reverse_lazy('servicios:list')

    def form_valid(self, form):
        # Guarda los datos si el formulario es válido
        messages.success(self.request, 'Servicio creado exitosamente.')

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

@login_required
class ServiciosUpdateView(UpdateView):
    model=Servicios
    fields = ["nombre","descripcion","imagen"]
    success_url = reverse_lazy('servicios:list')
    template_name_suffix = '_update_form'
    def get_success_url(self):
      return reverse_lazy('servicios:update', args=[self.object.id]) + '?ok'
@login_required
class ServiciosDeleteView(DeleteView):
    model=Servicios
    success_url = reverse_lazy('servicios:list')
