from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import ObraSocialForm,PlanObraSocialForm
from ..models import ObraSocial,PlanObraSocial
from django.db.models import Q
from caja.models import ConceptoFacturacion
from nomenclador.models import NomencladorGeneral
# ==========================================================
# LISTADO
# ==========================================================

@login_required
def obras_sociales(request):

    buscar = request.GET.get("buscar", "")

    obras_sociales = ObraSocial.objects.all()

    if buscar:

        obras_sociales = obras_sociales.filter(
            nombre__icontains=buscar
        )

    obras_sociales = obras_sociales.order_by("nombre")

    return render(

        request,

        "obraSocial/obrasocial.html",

        {

            "obras_sociales": obras_sociales,

            "buscar": buscar,

        }

    )


# ==========================================================
# CREAR
# ==========================================================

@login_required
def crear_obra_social(request):

    if request.method == "POST":

        form = ObraSocialForm(request.POST)

        if form.is_valid():

            obra_social = form.save()

            messages.success(

                request,

                f"La obra social '{obra_social.nombre}' fue creada correctamente."

            )

            return redirect("obrasocial:list")

    else:

        form = ObraSocialForm()

    return render(

        request,

        "obraSocial/obrasocial_form.html",

        {

            "form": form,

            "titulo": "Nueva Obra Social",

            "boton": "Guardar"

        }

    )


# ==========================================================
# EDITAR
# ==========================================================
@login_required
def editar_obra_social(request, pk):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk
    )

    if request.method == "POST":

        form = ObraSocialForm(
            request.POST,
            instance=obra_social
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Obra Social actualizada correctamente."
            )

            return redirect(
                "obrasocial:update",
                pk=obra_social.pk
            )

    else:

        form = ObraSocialForm(
            instance=obra_social
        )

    planes = PlanObraSocial.objects.filter(
        obra_social=obra_social
    ).order_by("nombre")

    return render(

        request,

        "obrasocial/obrasocial_form.html",

        {

            "form": form,

            "obra_social": obra_social,

            "planes": planes,

            "titulo": "Editar Obra Social",

            "boton": "Guardar Cambios",

        }

    )
# ==========================================================
# DESACTIVAR
# ==========================================================

@login_required
def desactivar_obra_social(request, pk):

    obra_social = get_object_or_404(

        ObraSocial,

        pk=pk

    )

    obra_social.activa = False

    obra_social.save()

    messages.warning(

        request,

        f"La obra social '{obra_social.nombre}' fue desactivada."

    )

    return redirect(

        "obrasocial:list"

    )
    
    
    
@login_required
def ver_obra_social(request, pk):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk
    )
    planes = obra_social.planes.order_by(
        "orden",
        "codigo"
    )

    if request.method == "POST":

        form = ObraSocialForm(
            request.POST,
            instance=obra_social
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Obra Social actualizada correctamente."
            )

            return redirect(
                "obrasocial:detail",
                pk=obra_social.pk
            )

    else:

        form = ObraSocialForm(
            instance=obra_social
        )

   

    context = {

        "obra_social": obra_social,
        "form": form,
        
        "planes": planes,

    }

    return render(
        request,
        "obrasocial/obrasocial_detail.html",
        context
    )

@login_required
def lista_precios_particular(request, pk):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk,
        es_particular=True
    )

    buscar = request.GET.get("buscar", "")

    # Últimos conceptos creados primero
    conceptos = (
        ConceptoFacturacion.objects
        .select_related("nomenclador")
        .order_by("-id")
    )

    if buscar:

        conceptos = conceptos.filter(
            Q(nomenclador__codigo__icontains=buscar) |
            Q(nomenclador__descripcion__icontains=buscar)
        )

    context = {

        "obra_social": obra_social,

        "conceptos": conceptos,

        "buscar": buscar,

        "total": conceptos.count(),

        "activos": conceptos.filter(
            activo=True
        ).count(),

        "inactivos": conceptos.filter(
            activo=False
        ).count(),

    }

    return render(
        request,
        "obrasocial/particular/lista_precios.html",
        context
    )


from ..forms import ConceptoFacturacionParticularForm    

@login_required
def editar_precio_particular(request, pk, concepto_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk,
        es_particular=True
    )

    concepto = get_object_or_404(
        ConceptoFacturacion.objects.select_related("nomenclador"),
        pk=concepto_id
    )

    if request.method == "POST":

        form = ConceptoFacturacionParticularForm(
            request.POST,
            instance=concepto
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "La prestación se actualizó correctamente."
            )

            return redirect(
                "obrasocial:lista_precios_particular",
                pk=obra_social.pk
            )

    else:

        form = ConceptoFacturacionParticularForm(
            instance=concepto
        )

    context = {
        "obra_social": obra_social,
        "concepto": concepto,
        "form": form,
    }

    return render(
        request,
        "obrasocial/particular/editar_precio.html",
        context
    )
    
@login_required
def ver_precio_particular(request, pk, concepto_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk,
        es_particular=True
    )

    concepto = get_object_or_404(
        ConceptoFacturacion.objects.select_related(
            "nomenclador",
            "proveedor"
        ),
        pk=concepto_id
    )

    context = {
        "obra_social": obra_social,
        "concepto": concepto,
    }

    return render(
        request,
        "obrasocial/particular/ver_precio.html",
        context
    )
    
@login_required
def importar_nomenclador_particular(request, pk):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk,
        es_particular=True
    )

    # =========================================================
    # IMPORTAR PRESTACIONES SELECCIONADAS
    # =========================================================

    if request.method == "POST":

        ids_seleccionados = request.POST.getlist("nomencladores")

        if not ids_seleccionados:

            messages.warning(
                request,
                "Debe seleccionar al menos una prestación."
            )

            return redirect(
                "obrasocial:importar_nomenclador_particular",
                pk=obra_social.pk
            )

        nomencladores_seleccionados = (
            NomencladorGeneral.objects
            .filter(
                id__in=ids_seleccionados,
                activo=True
            )
        )

        importados = 0

        for nomenclador in nomencladores_seleccionados:

            concepto, creado = ConceptoFacturacion.objects.get_or_create(
                nomenclador=nomenclador,
                defaults={
                    "importe_particular": 0,
                    "porcentaje_iva": 0,
                    "porcentaje_medico": 0,
                    "porcentaje_consultorio": 0,
                    "tipo_calculo": "PORCENTAJE",
                    "honorario_fijo_medico": 0,
                    "tipo_concepto": "CONSULTA",
                    "importe_proveedor": 0,
                    "activo": True,
                }
            )

            if creado:
                importados += 1

        if importados > 0:

            messages.success(
                request,
                f"Se importaron correctamente {importados} prestación/es."
            )

        else:

            messages.info(
                request,
                "Las prestaciones seleccionadas ya estaban incorporadas."
            )

        return redirect(
            "obrasocial:lista_precios_particular",
            pk=obra_social.pk
        )


    # =========================================================
    # MOSTRAR NOMENCLADORES DISPONIBLES
    # =========================================================

    buscar = request.GET.get("buscar", "").strip()

    nomencladores = (
        NomencladorGeneral.objects
        .filter(
            activo=True,
            particular__isnull=True
        )
        .order_by("codigo")
    )

    if buscar:

        nomencladores = nomencladores.filter(
            Q(codigo__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    context = {

        "obra_social": obra_social,

        "nomencladores": nomencladores,

        "buscar": buscar,

        "total_disponibles": nomencladores.count(),

    }

    return render(
        request,
        "obrasocial/particular/importar_nomenclador.html",
        context
    )