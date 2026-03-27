from django.urls import path
from . import views

app_name = 'turnos'

urlpatterns = [
    path('seleccionar_paciente/', views.seleccionar_paciente, name='seleccionar_paciente'),
    path('seleccionar_medico/', views.seleccionar_medico, name='seleccionar_medico'),
    path('ver_disponibilidad/', views.ver_disponibilidad, name='ver_disponibilidad'),
    path('reservar_turno/', views.reservar_turno, name='reservar_turno'),
    path('turno/<int:turno_id>/ausente/', views.marcar_ausente, name='marcar_ausente'),
    path('eliminar_turno/<int:turno_id>/', views.eliminar_turno, name='eliminar_turno'),
      path(
        'buscar-turnos-dni/',
        views.buscar_turnos_por_dni,
        name='buscar_turnos_por_dni'
    ),
    path('agenda-rapida/', views.agenda_rapida, name='agenda_rapida'),
    path('cargar-agenda-medico/', views.cargar_agenda_medico, name='cargar_agenda_medico'),
    path('agenda-mensual/', views.agenda_mensual_medico, name='agenda_mensual_medico'),
    path("mis-turnos-medico/", views.mis_turnos_medico, name="mis_turnos_medico"),
]
