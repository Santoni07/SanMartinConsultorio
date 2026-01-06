from django.forms import DateInput
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


from medicos.models import Medico
from .models import Agendas
from django.urls import reverse_lazy

class AgendaListView(ListView):
    model = Agendas
    template_name = 'agendas/agenda_list.html'  # La plantilla para mostrar la lista de agendas
    context_object_name = 'agendas'  # El nombre del objeto de contexto en la plantilla
   
class AgendaCreateView(CreateView):
    model = Agendas
    template_name = 'agendas/agenda_form.html'
    fields = '__all__'
    success_url = reverse_lazy('agenda:agenda_list')

    # Agregar widgets personalizados al formulario
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['dia'].widget = DateInput(attrs={'type': 'date'})
        return form

class AgendaUpdateView(UpdateView):
    model = Agendas
    template_name = 'agendas/agenda_form.html'
    fields = '__all__'
    success_url = reverse_lazy('agenda:agenda_list')

    # Agregar widgets personalizados al formulario
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['dia'].widget = DateInput(attrs={'type': 'date'})
        return form # URL a la que se redirige después de la actualización

class AgendaDeleteView(DeleteView):
    model = Agendas
    template_name = 'agendas/agenda_confirm_delete.html'  # La plantilla para la confirmación de eliminación
    success_url = reverse_lazy('agenda:agenda_list')  # URL a la que se redirige después de la eliminación