
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)

from paciente.forms import (
    BusquedaPacienteForm,
    PacienteForm,
    PacienteUpdateForm,
)
from paciente.models import Paciente
from obrasocial.models import PlanObraSocial


# ==========================================================
# OBTENER PLANES AGRUPADOS POR OBRA SOCIAL
# ==========================================================

def obtener_planes_por_obra_social(paciente=None):

    planes_por_obra_social = {}

    # Mostrar únicamente los planes activos.
    filtros = Q(activo=True)

    # En edición, conservar también el plan actual,
    # aunque haya sido desactivado.
    if (
        paciente is not None
        and paciente.pk
        and paciente.plan_obra_social_id
    ):
        filtros |= Q(pk=paciente.plan_obra_social_id)

    planes = (
        PlanObraSocial.objects
        .filter(filtros)
        .order_by(
            "obra_social_id",
            "orden",
            "codigo",
            "nombre",
        )
    )

    for plan in planes:

        obra_social_id = str(plan.obra_social_id)

        if obra_social_id not in planes_por_obra_social:
            planes_por_obra_social[obra_social_id] = []

        planes_por_obra_social[obra_social_id].append({
            "id": plan.id,
            "nombre": str(plan),
        })

    return planes_por_obra_social


# ==========================================================
# BUSCAR PACIENTE
# ==========================================================

class BuscarPacienteView(LoginRequiredMixin, TemplateView):

    template_name = "paciente/buscar_paciente.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["form"] = BusquedaPacienteForm()

        return context

    def post(self, request, *args, **kwargs):

        form = BusquedaPacienteForm(request.POST)

        if form.is_valid():

            dni = form.cleaned_data["dni"]

            try:

                paciente = Paciente.objects.get(dni=dni)

                return self.render_to_response({
                    "paciente_encontrado": paciente,
                })

            except Paciente.DoesNotExist:

                return self.render_to_response({
                    "mensaje_error": "Paciente no encontrado",
                })

        return self.render_to_response({
            "form": form,
        })


# ==========================================================
# ACTUALIZAR PACIENTE
# ==========================================================

class PacienteUpdateView(LoginRequiredMixin, UpdateView):

    model = Paciente

    # Conservamos el formulario específico de main.
    form_class = PacienteUpdateForm

    template_name_suffix = "_update_form"

    # ------------------------------------------------------
    # ENVIAR PLANES AL HTML
    # ------------------------------------------------------

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["planes_por_obra_social"] = (
            obtener_planes_por_obra_social(
                paciente=self.object
            )
        )

        return context

    # ------------------------------------------------------
    # REDIRECCIÓN DESPUÉS DE GUARDAR
    # ------------------------------------------------------

    def get_success_url(self):

        return (
            reverse_lazy(
                "paciente:update",
                args=[self.object.id],
            )
            + "?ok"
        )


# ==========================================================
# CREAR PACIENTE
# ==========================================================

class PacienteCreateView(LoginRequiredMixin, CreateView):

    model = Paciente

    form_class = PacienteForm

    success_url = reverse_lazy("paciente:buscar")

    # ------------------------------------------------------
    # ENVIAR PLANES AL HTML
    # ------------------------------------------------------

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["planes_por_obra_social"] = (
            obtener_planes_por_obra_social()
        )

        return context

    # ------------------------------------------------------
    # GUARDAR PACIENTE
    # ------------------------------------------------------

    def form_valid(self, form):

        messages.success(
            self.request,
            "Paciente creado exitosamente",
        )

        return super().form_valid(form)


# ==========================================================
# ELIMINAR PACIENTE
# ==========================================================

class PacienteDeleteView(LoginRequiredMixin, DeleteView):

    model = Paciente

    # Conservamos la redirección original de ambas ramas.
    success_url = reverse_lazy("IndexAdmin.html")
