#PLANES

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from obrasocial.models import ObraSocial
from ..forms import ObraSocialForm,PlanObraSocialForm
from ..models import ObraSocial,PlanObraSocial


@login_required
def listar_planes(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        activa=True
    )

    planes = obra_social.planes.order_by(
        "orden",
        "codigo",
    )

    context = {

        "obra_social": obra_social,

        "planes": planes,

    }

    return render(
        request,
        "obrasocial/planes/lista.html",
        context,
    )
@login_required
def crear_plan(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        activa=True
    )

    if request.method == "POST":

        form = PlanObraSocialForm(
            request.POST,
            obra_social=obra_social
        )

        if form.is_valid():

            plan = form.save(
                commit=False
            )

            plan.obra_social = obra_social

            plan.save()

            messages.success(
                request,
                "El plan fue creado correctamente."
            )

            return redirect(
                "obrasocial:listar_planes",
                obra_social.pk
            )

    else:

        form = PlanObraSocialForm(
            obra_social=obra_social
        )

    context = {

        "obra_social": obra_social,

        "form": form,

        "titulo": "Nuevo Plan",

    }

    return render(
        request,
        "obrasocial/planes/form.html",
        context,
    )
@login_required
def editar_plan(request, pk):

    plan = get_object_or_404(
        PlanObraSocial,
        pk=pk
    )

    if request.method == "POST":

        form = PlanObraSocialForm(
            request.POST,
            instance=plan,
            obra_social=plan.obra_social
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Plan actualizado correctamente."
            )

            return redirect(
                "obrasocial:listar_planes",
                plan.obra_social.pk
            )

    else:

        form = PlanObraSocialForm(
            instance=plan,
            obra_social=plan.obra_social
        )

    return render(
        request,
        "obrasocial/planes/form.html",
        {

            "obra_social": plan.obra_social,

            "form": form,

            "titulo": "Editar Plan",

            "plan": plan,

        },
    )
@login_required
def desactivar_plan(request, pk):

    plan = get_object_or_404(
        PlanObraSocial,
        pk=pk
    )

    plan.activo = False

    plan.save(
        update_fields=["activo"]
    )

    messages.success(
        request,
        "Plan desactivado correctamente."
    )

    return redirect(
        "obrasocial:listar_planes",
        plan.obra_social.pk
    )

@login_required
def detalle_plan(request, pk):

    plan = get_object_or_404(
        PlanObraSocial,
        pk=pk
    )

    context = {
        "plan": plan,
        "obra_social": plan.obra_social,
        "cantidad_prestaciones": 0,
    }

    return render(
        request,
        "obrasocial/planes/detalle.html",
        context
    )