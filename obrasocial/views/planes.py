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


@login_required
def crear_plan(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    # Una obra social que no usa planes
    # no puede crear planes.
    if not obra_social.usa_planes:

        messages.warning(
            request,
            "Esta obra social no utiliza planes."
        )

        return redirect(
            "obrasocial:detail",
            pk=obra_social.id
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
                f"El plan {plan.nombre} fue creado correctamente."
            )

            return redirect(
                "obrasocial:detail",
                pk=obra_social.id
            )

    else:

        form = PlanObraSocialForm(
            obra_social=obra_social
        )

    context = {
        "obra_social": obra_social,
        "form": form,
    }

    return render(
        request,
        "obrasocial/planes/crear.html",
        context
    )



@login_required
def editar_plan(request, pk):

    plan = get_object_or_404(
        PlanObraSocial.objects.select_related("obra_social"),
        pk=pk
    )

    obra_social = plan.obra_social

    if request.method == "POST":

        form = PlanObraSocialForm(
            request.POST,
            instance=plan,
            obra_social=obra_social
        )

        if form.is_valid():

            plan = form.save()

            messages.success(
                request,
                f"El plan {plan.nombre} fue modificado correctamente."
            )

            return redirect(
                "obrasocial:detail",
                pk=obra_social.id
            )

    else:

        form = PlanObraSocialForm(
            instance=plan,
            obra_social=obra_social
        )

    context = {
        "obra_social": obra_social,
        "plan": plan,
        "form": form,
    }

    return render(
        request,
        "obrasocial/planes/editar.html",
        context
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