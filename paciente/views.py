from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import  CreateView, UpdateView, DeleteView,TemplateView
from paciente.forms import BusquedaPacienteForm,  PacienteForm
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib import messages
from obrasocial.models import PlanObraSocial
from django.core.serializers.json import DjangoJSONEncoder
import json

from .models import  Paciente
from django.urls import reverse_lazy

# Crud Medicos

class BuscarPacienteView(LoginRequiredMixin,TemplateView):
    template_name = 'paciente/buscar_paciente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BusquedaPacienteForm()
        return context

    def post(self, request, *args, **kwargs):
        form = BusquedaPacienteForm(request.POST)
        if form.is_valid():
            dni = form.cleaned_data['dni']
            try:
                paciente = Paciente.objects.get(dni=dni)
                return self.render_to_response({'paciente_encontrado': paciente})
            except Paciente.DoesNotExist:
                mensaje_error = 'Paciente no encontrado'
                return self.render_to_response({'mensaje_error': mensaje_error})
        else:
            return self.render_to_response({'form': form})

class PacienteUpdateView(LoginRequiredMixin, UpdateView):

    model = Paciente
    form_class = PacienteForm

    template_name_suffix = '_update_form'

    # ==========================================
    # ENVIAR PLANES AL HTML
    # ==========================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        planes_por_obra_social = {}

        planes = PlanObraSocial.objects.select_related(
            "obra_social"
        ).all()

        for plan in planes:

            obra_social_id = str(plan.obra_social_id)

            if obra_social_id not in planes_por_obra_social:
                planes_por_obra_social[obra_social_id] = []

            planes_por_obra_social[obra_social_id].append({
                "id": plan.id,
                "nombre": str(plan),
            })

        context["planes_por_obra_social"] = json.dumps(
            planes_por_obra_social,
            cls=DjangoJSONEncoder
        )

        return context

    # ==========================================
    # REDIRECCIÓN DESPUÉS DE GUARDAR
    # ==========================================

    def get_success_url(self):

        return reverse_lazy(
            'paciente:update',
            args=[self.object.id]
        ) + '?ok'


class PacienteCreateView(LoginRequiredMixin, CreateView):

    model = Paciente
    form_class = PacienteForm

    success_url = reverse_lazy('paciente:buscar')

    # ==========================================
    # ENVIAR PLANES AL HTML
    # ==========================================

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        planes_por_obra_social = {}

        planes = (
            PlanObraSocial.objects
            .filter(activo=True)
            .select_related("obra_social")
            .order_by("obra_social_id", "orden", "codigo", "nombre")
        )

        for plan in planes:

            obra_social_id = str(plan.obra_social_id)

            if obra_social_id not in planes_por_obra_social:
                planes_por_obra_social[obra_social_id] = []

            planes_por_obra_social[obra_social_id].append({
                "id": plan.id,
                "nombre": f"{plan.codigo} - {plan.nombre}",
            })

        context["planes_por_obra_social"] = planes_por_obra_social

        return context

    # ==========================================
    # GUARDAR PACIENTE
    # ==========================================

    def form_valid(self, form):

        messages.success(
            self.request,
            'Paciente creado exitosamente'
        )

        return super().form_valid(form)   


class PacienteDeleteView(LoginRequiredMixin,DeleteView):
    model=Paciente
    success_url = reverse_lazy('IndexAdmin.html')
    
    
 
