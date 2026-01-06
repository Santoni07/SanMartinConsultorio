from django.urls import path
from .views import ServiciosListView,ServiciosCreateView,ServiciosUpdateView,ServiciosDeleteView



Servicios_patterns =([
    path('servicios/',ServiciosListView.as_view(),name="list" ),
    path('create', ServiciosCreateView.as_view(), name="create"),
    path('update/<int:pk>', ServiciosUpdateView.as_view(), name="update"),
    path('delete/<int:pk>', ServiciosDeleteView.as_view(), name="delete"),
    
    
], 'servicios')