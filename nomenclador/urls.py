from django.urls import path
from . import views

urlpatterns = [

    path(
        '',
        views.lista_nomenclador,
        name='lista_nomenclador'
    ),

    path(
        'nuevo/',
        views.nuevo_nomenclador,
        name='nuevo_nomenclador'
    ),

    path(
        'editar/<int:pk>/',
        views.editar_nomenclador,
        name='editar_nomenclador'
    ),

    path(
        'eliminar/<int:pk>/',
        views.eliminar_nomenclador,
        name='eliminar_nomenclador'
    ),

]