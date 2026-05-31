from django.urls import path
from . import views

app_name = "gerencia"

urlpatterns = [

    path(
        'dashboard/',
        views.dashboard_gerencia,
        name='dashboard'
    ),

    path(
        'operaciones/',
        views.operaciones_gerencia,
        name='operaciones'
    ),

    path(
        'pacientes/',
        views.pacientes_gerencia,
        name='pacientes'
    ),

    path(
        'medicos/',
        views.medicos_gerencia,
        name='medicos'
    ),

    path(
        'sedes/',
        views.sedes_gerencia,
        name='sedes'
    ),
]