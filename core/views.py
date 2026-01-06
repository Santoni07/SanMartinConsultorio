
from django.shortcuts import redirect
from django.views.generic.base import TemplateView

from servicios.models import Servicios
from medicos.models import Medico

from django.urls import reverse


from especialidades.views import *
from django.contrib.auth.views import LoginView




    
class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        print("🟢 Usuario logueado:", user.username)
        print("🟢 ¿Staff?:", user.is_staff)
        print("🟢 ¿Superuser?:", user.is_superuser)

        # Verificamos si tiene perfil médico
        if hasattr(user, 'medico'):
            print("🟢 Usuario es médico:", user.medico)
        else:
            print("🔴 Usuario NO es médico.")

        if user.is_superuser or user.is_staff:
            print("🔁 Redirigiendo a IndexAdmin")
            return reverse('core:IndexAdmin')

        elif hasattr(user, 'medico'):
            print("🔁 Redirigiendo a /medico/")
            return reverse('core:medico')

        print("🔁 Redirigiendo a index general")
        return reverse('core:index')

class HomePageView(TemplateView):
    template_name = 'core/index.html'
   
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['especialidades'] = Especialidades.objects.all()  # Obtén todas las especialidades
        context['medicos'] = Medico.objects.all()  # Obtén todos los médicos
        context['especialidades_count'] = Especialidades.objects.count()
        context['medicos_count'] = Medico.objects.count()
    
        context['Servicios'] = Servicios.objects.all()
        return context

class AdminPageView(TemplateView):
    template_name = 'core/indexAdmin.html'

class MedicoPageView(TemplateView):
    template_name = 'core/IndexMedico.html'
    

def ValidarUsuario(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/IndexAdmin/')
        elif hasattr(request.user, 'medico'):
            return redirect('/medico/')
        else:
            return redirect('/')
    return redirect('login')
