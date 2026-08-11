from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from ..models import (
    ObraSocial,
    PrestacionPlan
)


@login_required
def listar_prestaciones(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    plan = None

    plan_id = request.GET.get("plan")

    prestaciones = PrestacionPlan.objects.filter(
        obra_social=obra_social
    )

    if plan_id:

        plan = get_object_or_404(
            PlanObraSocial,
            pk=plan_id,
            obra_social=obra_social
        )

        prestaciones = prestaciones.filter(
            plan=plan
        )

    else:

        prestaciones = prestaciones.filter(
            plan__isnull=True
        )

    buscar = request.GET.get("buscar", "")

    if buscar:

        prestaciones = prestaciones.filter(
            nomenclador__codigo__icontains=buscar
        ) | prestaciones.filter(
            nomenclador__descripcion__icontains=buscar
        )

    context = {

        "obra_social": obra_social,
        "plan": plan,
        "prestaciones": prestaciones.order_by(
            "nomenclador__codigo"
        ),
        "buscar": buscar,

        "total": prestaciones.count(),

        "activas": prestaciones.filter(
            estado="ACTIVA"
        ).count(),

        "inactivas": prestaciones.filter(
            estado="INACTIVA"
        ).count(),

    }

    return render(
        request,
        "obrasocial/prestaciones/lista.html",
        context
    )


@login_required
def crear_prestacion(request, obra_social_id):
    return HttpResponse("Crear Prestación")


@login_required
def detalle_prestacion(request, pk):
    return HttpResponse("Detalle Prestación")


@login_required
def editar_prestacion(request, pk):
    return HttpResponse("Editar Prestación")


@login_required
def desactivar_prestacion(request, pk):
    return HttpResponse("Desactivar Prestación")