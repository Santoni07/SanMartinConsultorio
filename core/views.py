
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate
from servicios.models import Servicios
from medicos.models import Medico
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from especialidades.models import Especialidades
from obrasocial.models import ObraSocial

import os
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages



from especialidades.views import *
from django.contrib.auth.views import LoginView

print("🚀 CORE VIEWS CARGADO")


    
class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    def dispatch(self, request, *args, **kwargs):
        print("🔥 Estoy usando CustomLoginView")
        return super().dispatch(request, *args, **kwargs)
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

    def form_valid(self, form):
        print("✅ FORM VALID - Usuario autenticado:", form.get_user())
        return super().form_valid(form)

    def form_invalid(self, form):
        print("❌ FORM INVALID:", form.errors)
        return super().form_invalid(form)
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")

        print("🔎 Intentando login con:", username)

        user = authenticate(request, username=username, password=password)

        print("🔎 Resultado authenticate:", user)

        return super().post(request, *args, **kwargs)
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



class MedicoPageView(LoginRequiredMixin,TemplateView):
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

def solicitar_turno(request):
    especialidades = Especialidades.objects.all()
    obras_sociales = ObraSocial.objects.all()

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        dni = request.POST.get("dni")
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        telefono = request.POST.get("telefono")
        email = request.POST.get("email")
        tipo_pago = request.POST.get("tipo_pago")
        obra_social_id = request.POST.get("obra_social")
        especialidad_id = request.POST.get("especialidad")
        preferencia = request.POST.get("preferencia_horaria")

        # Obtener nombres reales en vez de IDs
        especialidad = Especialidades.objects.filter(id=especialidad_id).first()
        obra_social = ObraSocial.objects.filter(id=obra_social_id).first()

        contenido = f"""
NUEVA SOLICITUD DE TURNO

Nombre: {nombre}
DNI: {dni}
Fecha Nacimiento: {fecha_nacimiento}
Teléfono: {telefono}
Email: {email}
Tipo de Atención: {tipo_pago}
Obra Social: {obra_social.nombre if obra_social else "Particular"}
Especialidad: {especialidad.nombre if especialidad else ""}
Preferencia Horaria: {preferencia}

Fecha de solicitud: {datetime.now()}
"""

        carpeta = os.path.join(settings.BASE_DIR, "emails_prueba")

        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        nombre_archivo = f"turno_{dni}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        ruta_archivo = os.path.join(carpeta, nombre_archivo)

        with open(ruta_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)

        messages.success(request, "Solicitud enviada correctamente ✅")

        return redirect("core:solicitar_turno")

    return render(request, 'core/solicitar_turno.html', {
        'especialidades': especialidades,
        'obras_sociales': obras_sociales,
    })