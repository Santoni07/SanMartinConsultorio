from django.urls import path
from .views import BuscarPacienteView,PacienteUpdateView,PacienteDeleteView,PacienteCreateView






Paciente_patterns = ([
    path('',BuscarPacienteView.as_view(), name='buscar'),
    path('update/<int:pk>/', PacienteUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', PacienteDeleteView.as_view(), name='delete'),
    path('create/', PacienteCreateView.as_view(), name='create'),
    
   
    
], 'paciente')