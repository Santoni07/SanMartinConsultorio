from django.urls import path
from .views import buscar_y_cargar_estudio,  eliminar_estudio,ver_estudios_paciente

urlpatterns = [
    path('cargar/', buscar_y_cargar_estudio, name='buscar_y_cargar_estudio'),
    path('eliminar/<int:estudio_id>/', eliminar_estudio, name='eliminar_estudio'),
    path('ver/', ver_estudios_paciente, name='ver_estudios'),
]