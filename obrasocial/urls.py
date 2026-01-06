from django.urls import path

from .views import ObraSocialDeleteView,ObraSocialUpdateView,ObraSocialListView,ObraSocialCreateView



ObraSocial_patterns = ([
    path('',ObraSocialListView.as_view(), name='list'),
    path('create/', ObraSocialCreateView.as_view(), name='create'),
    path('update/<int:pk>/', ObraSocialUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', ObraSocialDeleteView.as_view(), name='delete'),
  
    
], 'obrasocial')