

from django.urls import path
from .views import AgendaCreateView, AgendaDeleteView, AgendaListView, AgendaUpdateView













Agenda_patterns = ([
    path('', AgendaListView.as_view(), name='agenda_list'),  # Lista de agendas
    path('create/', AgendaCreateView.as_view(), name='agenda_create'),  # Crear agenda
    path('update/<int:pk>/', AgendaUpdateView.as_view(), name='agenda_update'),  # Actualizar agenda
    path('delete/<int:pk>/', AgendaDeleteView.as_view(), name='agenda_delete'),  # Eliminar agenda
  
  
    
], 'agenda')