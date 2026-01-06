
from django.urls import path


from .views import HomePageView,AdminPageView, ValidarUsuario,MedicoPageView

app_name="core"

urlpatterns = [
   
    path('', HomePageView.as_view(), name='index'),
     path('IndexAdmin/', AdminPageView.as_view(), name='IndexAdmin'),
      path('validar-usuario/', ValidarUsuario, name='validar_usuario'),
    path('medico/', MedicoPageView.as_view(), name='medico')
     
     
   

 
   
   
   
   
]