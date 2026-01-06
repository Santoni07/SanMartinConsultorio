from django.urls import path

from .views import MedicoListView,MedicoCreateView,MedicoDeleteView,MedicoUpdateView



Medico_patterns = ([
    path('medicos/',MedicoListView.as_view(), name='list'),
    path('create/', MedicoCreateView.as_view(), name='create'),
    path('delete/<int:pk>/', MedicoDeleteView.as_view(), name='delete'),
    path('update/<int:pk>/', MedicoUpdateView.as_view(), name='update'),
    
], 'medicos')