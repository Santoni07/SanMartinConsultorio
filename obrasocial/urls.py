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

], 'obrasocial')