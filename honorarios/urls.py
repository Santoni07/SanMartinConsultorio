from django.urls import path
from . import views

urlpatterns = [

    path(
        '',
        views.honorarios_medicos,
        name='honorarios_medicos'
    ),
     path(
    'generar/<int:medico_id>/',
    views.generar_liquidacion,
    name='generar_liquidacion'
),
path(
    'previsualizar/<int:medico_id>/',
    views.previsualizar_liquidacion,
    name='previsualizar_liquidacion'
),


 path(
    'pendientes/',
    views.liquidaciones_pendientes,
    name='liquidaciones_pendientes'
), 

path(
    'pagar/<int:liquidacion_id>/',
    views.registrar_pago_liquidacion,
    name='registrar_pago_liquidacion'
),
]