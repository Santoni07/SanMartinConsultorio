from django.urls import path
from . import views

urlpatterns = [
     path('buscar/', views.buscar_paciente_consulta, name='buscar_paciente_consulta'),
    path('consulta/cargar/<int:paciente_id>/', views.cargar_consulta_paciente, name='cargar_consulta_paciente'),
    path('historia/<int:paciente_id>/', views.ver_historia_clinica, name='ver_historia_clinica'),
    path('buscar-por-dni/', views.buscar_historia_por_dni, name='buscar_historia_por_dni'),

]