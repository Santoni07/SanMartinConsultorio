from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from obrasocial.models import ObraSocial
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

 
class ObraSocialListView(LoginRequiredMixin,ListView):
      model = ObraSocial
      template_name = 'obraSocial/obrasocial.html' 
      context_object_name = 'obras_sociales' 
    
 
class ObraSocialUpdateView(LoginRequiredMixin,UpdateView):
    model=ObraSocial
    fields = [ 'nombre']
    success_url = reverse_lazy('obrasocial:list')
    template_name_suffix = '_update_form'
    def get_success_url(self):
      return reverse_lazy('obrasocial:update', args=[self.object.id]) + '?ok'

class ObraSocialDeleteView(LoginRequiredMixin,DeleteView):
    model=ObraSocial
    success_url = reverse_lazy('obrasocial:list')
    
    
class ObraSocialCreateView(LoginRequiredMixin,CreateView):
    model=ObraSocial
    fields=['nombre']
    success_url = reverse_lazy('obrasocial:list')
   

    def form_valid(self, form):
        messages.success(self.request, 'Paciente creado exitosamente')
        return super().form_valid(form)
    
        