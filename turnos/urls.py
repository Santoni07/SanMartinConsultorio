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
    path('crear-sobreturno/', views.crear_sobreturno, name='crear_sobreturno'),
    path('eliminar-sobreturno/<int:sobreturno_id>/', views.eliminar_sobreturno, name='eliminar_sobreturno'),
      path(
        'buscar-turnos-dni/',
        views.buscar_turnos_por_dni,
        name='buscar_turnos_por_dni'
    ),
    path('agenda-rapida/', views.agenda_rapida, name='agenda_rapida'),
    path('cargar-agenda-medico/', views.cargar_agenda_medico, name='cargar_agenda_medico'),
    path('agenda-mensual/', views.agenda_mensual_medico, name='agenda_mensual_medico'),
    path('seleccionar-medico-consulta/', views.seleccionar_medico_consulta, name='seleccionar_medico_consulta'),
    path('excepcion/', views.crear_excepcion, name='crear_excepcion'),
    path('excepciones/', views.lista_excepciones, name='lista_excepciones'),
    path('excepciones-detalle/', views.excepciones_detalle, name='excepciones_detalle'),
    path('disponibilidad-consulta/', views.ver_disponibilidad_consulta, name='disponibilidad_consulta'),
    path("mis-turnos-medico/", views.mis_turnos_medico, name="mis_turnos_medico"),
]
