from django.urls import path

from . import views

ObraSocial_patterns = ([

    path(
        '',
        views.obras_sociales,
        name='list'
    ),

    path(
        'crear/',
        views.crear_obra_social,
        name='create'
    ),

    path(
        '<int:pk>/',
        views.ver_obra_social,
        name='detail'
    ),

    path(
        '<int:pk>/editar/',
        views.editar_obra_social,
        name='update'
    ),

    path(
        'desactivar/<int:pk>/',
        views.desactivar_obra_social,
        name='delete'
    ),

    # ==========================
    # PLANES
    # ==========================

    path(
        '<int:obra_social_id>/planes/nuevo/',
        views.crear_plan,
        name='crear_plan'
    ),

    path(
        'planes/<int:pk>/',
        views.detalle_plan,
        name='detalle_plan'
    ),

    path(
        'planes/<int:pk>/editar/',
        views.editar_plan,
        name='editar_plan'
    ),

    path(
        'planes/<int:pk>/desactivar/',
        views.desactivar_plan,
        name='desactivar_plan'
    ),
    
    # ==========================================================
# PRESTACIONES
# ==========================================================

path(
    "<int:obra_social_id>/prestaciones/",
    views.listar_prestaciones,
    name="listar_prestaciones",
),

path(
    "<int:obra_social_id>/prestaciones/nueva/",
    views.crear_prestacion,
    name="crear_prestacion",
),

path(
    "prestaciones/<int:pk>/",
    views.detalle_prestacion,
    name="detalle_prestacion",
),

path(
    "prestaciones/<int:pk>/editar/",
    views.editar_prestacion,
    name="editar_prestacion",
),

path(
    "prestaciones/<int:pk>/desactivar/",
    views.desactivar_prestacion,
    name="desactivar_prestacion",
),

path(
    "<int:pk>/lista-precios/",
    views.lista_precios_particular,
    name="lista_precios_particular"
),
path(
    '<int:pk>/lista-precios/<int:concepto_id>/editar/',
    views.editar_precio_particular,
    name='editar_precio_particular'
),
path(
    '<int:pk>/lista-precios/<int:concepto_id>/ver/',
    views.ver_precio_particular,
    name='ver_precio_particular'
),
path(
    '<int:pk>/lista-precios/importar/',
    views.importar_nomenclador_particular,
    name='importar_nomenclador_particular'
),
], 'obrasocial')