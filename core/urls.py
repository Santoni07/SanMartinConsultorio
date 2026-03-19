
from django.urls import path


from .views import HomePageView,AdminPageView, ValidarUsuario,MedicoPageView,solicitar_turno,politica_privacidad,terminos_condiciones

app_name="core"

urlpatterns = [
   
    path('', HomePageView.as_view(), name='index'),
    path('IndexAdmin/', AdminPageView.as_view(), name='IndexAdmin'),
    path('validar-usuario/', ValidarUsuario, name='validar_usuario'),
    path('medico/', MedicoPageView.as_view(), name='medico'),
    path('solicitar-turno/', solicitar_turno, name='solicitar_turno'),

    path('politica-privacidad/', politica_privacidad, name='politica_privacidad'),
    path('terminos-condiciones/', terminos_condiciones, name='terminos_condiciones')

     
     
   

 
   
   
   
   
]