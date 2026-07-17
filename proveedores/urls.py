from django.urls import path
from . import views

app_name = "proveedores"

urlpatterns = [

    path(
        "pendientes/",
        views.proveedores_pendientes,
        name="proveedores_pendientes",
    ),

    path(
        "previsualizar/",
        views.previsualizar_liquidacion_proveedor,
        name="previsualizar_liquidacion_proveedor",
    ),
    
    path(
    "generar/",
    views.generar_liquidacion_proveedor,
    name="generar_liquidacion_proveedor",
),
    path(
    "liquidaciones/",
    views.liquidaciones_pendientes_proveedor,
    name="liquidaciones_pendientes_proveedor",
),
    path(
    "registrar-pago/<int:liquidacion_id>/",
    views.registrar_pago_liquidacion_proveedor,
    name="registrar_pago_liquidacion_proveedor",
),
    path(
    "historial/",
    views.historial_liquidaciones_proveedor,
    name="historial_liquidaciones_proveedor",
),
    path(
    "detalle/<int:liquidacion_id>/",
    views.detalle_liquidacion_proveedor,
    name="detalle_liquidacion_proveedor",
),

]
