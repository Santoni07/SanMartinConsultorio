from django.urls import path
from . import views

app_name = 'turnos'

urlpatterns = [
    path('seleccionar_paciente/', views.seleccionar_paciente, name='seleccionar_paciente'),
    path('seleccionar_medico/', views.seleccionar_medico, name='seleccionar_medico'),
    path('ver_disponibilidad/', views.ver_disponibilidad, name='ver_disponibilidad'),
    path('reservar_turno/', views.reservar_turno, name='reservar_turno'),
    path('eliminar_turno/<int:turno_id>/', views.eliminar_turno, name='eliminar_turno'),
]
