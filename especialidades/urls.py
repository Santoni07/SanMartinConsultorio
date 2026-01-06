from django.urls import path
from .views import EspecialidadesCreateView,EspecialidadesListView,EspecialidadesDeleteView,EspecialidadesUpdateView
Especialidades_patterns = ([
    # Path especialidades
    path('especialidades/', EspecialidadesListView.as_view(), name='list'),
    path('create/', EspecialidadesCreateView.as_view(), name='create'),
    path('delete/<int:pk>/', EspecialidadesDeleteView.as_view(), name='delete'),
    path('update/<int:pk>/', EspecialidadesUpdateView.as_view(), name='update'),
    
    
   
   
],'especialidades')