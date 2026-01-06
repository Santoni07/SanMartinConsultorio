
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf.urls.static import static
from django.conf import settings
from especialidades.urls import Especialidades_patterns
from medicos.urls import Medico_patterns
from servicios.urls import Servicios_patterns
from paciente.urls import Paciente_patterns
from obrasocial.urls import ObraSocial_patterns
from agendas.urls import Agenda_patterns








urlpatterns = [
    path('admin/', admin.site.urls),
    
# url core
      path('', include('core.urls')),

     
# path del Auth
     path('accounts/', include('django.contrib.auth.urls')),
     path('accounts/', include('registration.urls')),

# path del especialidades
   path('especialidades/', include(Especialidades_patterns)),
   
#path medicos
     path('medicos/', include(Medico_patterns)),
     
# path servicios
    path('servicios/', include(Servicios_patterns)),
    
# path Pacientes
    path('pacientes/', include(Paciente_patterns)),
    
# path ObraSocial
    path('obrasocial/', include(ObraSocial_patterns)),
    
# path agenda
    path('agenda/', include(Agenda_patterns)),
# path turnos
   path('turnos/', include('turnos.urls')),
   
# path estudios
   path('estudios/', include('estudios.urls')),
   
# path historial
   path('historial/', include('historial.urls')),

]




if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    