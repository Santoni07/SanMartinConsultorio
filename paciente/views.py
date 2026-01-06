from django.shortcuts import render
from django.views.generic import  CreateView, UpdateView, DeleteView,TemplateView
from paciente.forms import BusquedaPacienteForm


from django.contrib import messages


from .models import  Paciente
from django.urls import reverse_lazy

# Crud Medicos
class BuscarPacienteView(TemplateView):
    template_name = 'paciente/buscar_paciente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BusquedaPacienteForm()
        return context

    def post(self, request, *args, **kwargs):
        form = BusquedaPacienteForm(request.POST)
        if form.is_valid():
            dni = form.cleaned_data['dni']
            try:
                paciente = Paciente.objects.get(dni=dni)
                return self.render_to_response({'paciente_encontrado': paciente})
            except Paciente.DoesNotExist:
                mensaje_error = 'Paciente no encontrado'
                return self.render_to_response({'mensaje_error': mensaje_error})
        else:
            return self.render_to_response({'form': form})
      
class PacienteUpdateView(UpdateView):
    model=Paciente
    fields = [ 'telefono','email',  'direccion', 'observaciones', 'obrasocial']
    success_url = reverse_lazy('IndexAdmin.html')
    template_name_suffix = '_update_form'
    def get_success_url(self):
      return reverse_lazy('paciente:update', args=[self.object.id]) + '?ok'

class PacienteDeleteView(DeleteView):
    model=Paciente
    success_url = reverse_lazy('IndexAdmin.html')
    
    
    
class PacienteCreateView(CreateView):
    model=Paciente
    fields=['dni','nombre','apellido','edad','fecha_nacimiento','telefono','email','direccion','observaciones','obrasocial']
    success_url = reverse_lazy('paciente:buscar')
   

    def form_valid(self, form):
        messages.success(self.request, 'Paciente creado exitosamente')
        return super().form_valid(form)
    
        
        

       


