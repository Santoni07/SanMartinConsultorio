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
    "<int:pk>/",
    views.ver_obra_social,
    name="detail",
),

    path(
        'desactivar/<int:pk>/',
        views.desactivar_obra_social,
        name='delete'
    ),
    
    path(
    "<int:obra_social_id>/planes/nuevo/",
    views.crear_plan,
    name="crear_plan"
),

path(
    "planes/<int:pk>/",
    views.detalle_plan,
    name="detalle_plan"
),

path(
    "planes/<int:pk>/editar/",
    views.editar_plan,
    name="editar_plan"
),

path(
    "planes/<int:pk>/desactivar/",
    views.desactivar_plan,
    name="desactivar_plan"
),

], 'obrasocial')