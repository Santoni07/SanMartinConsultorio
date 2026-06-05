from django.urls import path
from . import views

urlpatterns = [
    path('', views.caja_home, name='caja_home'),
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('registrar-cobro/', views.registrar_cobro, name='registrar_cobro'),
    path('registrar-movimiento/', views.registrar_movimiento, name='registrar_movimiento'),
    path('anular/<int:movimiento_id>/', views.anular_movimiento, name='anular_movimiento'),
    path('cerrar/', views.cerrar_caja, name='cerrar_caja'),
]