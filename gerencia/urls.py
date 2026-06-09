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
    
    path(
    'facturacion/casa-central/',
    views.facturacion_sede,
    {'centro_id': 1},
    name='facturacion_casa_central'
    ),

    path(
        'facturacion/agua-de-oro/',
        views.facturacion_sede,
        {'centro_id': 2},
        name='facturacion_agua_oro'
    ),
    path('facturacion/', views.facturacion, name='facturacion'),
    path(
    'facturacion/caja/<int:caja_id>/',
    views.detalle_caja,
    name='detalle_caja'
),
]