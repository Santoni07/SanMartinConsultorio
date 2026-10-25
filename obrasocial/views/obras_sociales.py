from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from ..forms import ObraSocialForm,PlanObraSocialForm
from ..models import ObraSocial,PlanObraSocial,MasterObraSocial,DetalleMasterObraSocial
from django.db.models import Q
from datetime import date
from django.db import transaction
from decimal import Decimal,InvalidOperation
from caja.models import ConceptoFacturacion
from nomenclador.models import NomencladorGeneral
from caja.models import DetalleMovimientoCaja, DetalleMedioPago, MedioPago
from django.views.decorators.http import require_POST

# ======================================================
# PERMISOS - GESTIÓN DE OBRAS SOCIALES
# ======================================================

def usuario_autorizado_obras_sociales(user):
    return (
        user.is_authenticated
        and user.username.lower() in {"cintia", "cintia2"}
    )

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

        "obrasocial/obrasocial.html",

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

        "obrasocial/obrasocial_form.html",

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
@require_POST
def desactivar_obra_social(request, pk):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=pk
    )

    obra_social.activa = False
    obra_social.save(update_fields=["activa"])

    messages.warning(
        request,
        f"La obra social '{obra_social.nombre}' fue desactivada."
    )

    return redirect("obrasocial:list")


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


def calcular_importe_obra_social(detalle):

    # ======================================================
    # IMPORTE ORIGINAL DE LA PRESTACIÓN
    # ======================================================

    importe = (
        detalle.importe
        or Decimal("0.00")
    )

    # ======================================================
    # COSEGURO
    # ======================================================
    #
    # Solamente se descuenta si efectivamente
    # fue cobrado al paciente.
    #
    # El COPAGO NO interviene.
    # ======================================================

    coseguro = Decimal("0.00")

    if detalle.coseguro_cobrado:

        coseguro = (
            detalle.importe_coseguro
            or Decimal("0.00")
        )

    # ======================================================
    # IMPORTE A COBRAR A LA OBRA SOCIAL
    # ======================================================

    importe_os = importe - coseguro

    if importe_os < Decimal("0.00"):
        importe_os = Decimal("0.00")

    return importe_os


@login_required
def master_obra_social_lista(request, obra_social_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para acceder al Master de Obra Social."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    # ======================================================
    # FILTROS
    # ======================================================

    mes = request.GET.get("mes")
    anio = request.GET.get("anio")

    buscando = False

    # ======================================================
    # MASTERS DE ESTA OBRA SOCIAL
    # ======================================================

    masters = (
        MasterObraSocial.objects
        .filter(
            obra_social=obra_social
        )
        .select_related(
            "obra_social",
            "creado_por"
        )
        .order_by(
            "-fecha_creacion"
        )
    )

    # ======================================================
    # BÚSQUEDA POR MES / AÑO
    # ======================================================

    if mes and anio:

        try:

            mes = int(mes)
            anio = int(anio)

            if 1 <= mes <= 12:

                masters = masters.filter(
                    mes=mes,
                    anio=anio
                )

                buscando = True

            else:

                mes = None
                anio = None

        except (TypeError, ValueError):

            mes = None
            anio = None

    # ======================================================
    # SIN BÚSQUEDA
    # MOSTRAR SOLAMENTE LOS ÚLTIMOS 5
    # ======================================================

    if not buscando:

        masters = masters[:5]

    # ======================================================
    # TEMPLATE
    # ======================================================

    return render(
        request,
        "obrasocial/master/lista.html",
        {
            "obra_social": obra_social,
            "masters": masters,

            "mes_seleccionado": mes,
            "anio_seleccionado": anio,

            "buscando": buscando,
        }
    )
# ==========================================================
# MASTER DE OBRA SOCIAL
# NUEVO MASTER
# ==========================================================

@login_required
def master_obra_social_nuevo(request, obra_social_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para generar Masters."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    hoy = date.today()

    prestaciones = None

    # ======================================================
    # POST - GENERAR MASTER
    # ======================================================

    if request.method == "POST":

        mes = request.POST.get("mes")
        anio = request.POST.get("anio")

        detalles_ids = request.POST.getlist(
            "prestaciones"
        )

        # ==================================================
        # VALIDAR PERÍODO
        # ==================================================

        try:
            mes = int(mes)
            anio = int(anio)

        except (TypeError, ValueError):

            messages.error(
                request,
                "El período seleccionado no es válido."
            )

            return redirect(
                "obrasocial:master_obra_social_nuevo",
                obra_social_id=obra_social.id
            )

        if mes < 1 or mes > 12:

            messages.error(
                request,
                "El mes seleccionado no es válido."
            )

            return redirect(
                "obrasocial:master_obra_social_nuevo",
                obra_social_id=obra_social.id
            )

        # ==================================================
        # DEBE HABER PRESTACIONES SELECCIONADAS
        # ==================================================

        if not detalles_ids:

            messages.warning(
                request,
                "Debe seleccionar al menos una prestación."
            )

            return redirect(
                f"{request.path}?mes={mes}&anio={anio}"
            )


        # ==================================================
        # TRANSACCIÓN
        # ==================================================

        try:

            with transaction.atomic():

                # ==========================================
                # VOLVER A CONSULTAR LAS PRESTACIONES
                # ==========================================
                #
                # IMPORTANTE:
                #
                # Desde que DetalleMasterObraSocial usa
                # ForeignKey hacia DetalleMovimientoCaja,
                # el related_name es:
                #
                # detalles_master_obra_social
                #
                # Por eso utilizamos:
                #
                # detalles_master_obra_social__isnull=True
                #
                # Esto impide incorporar accidentalmente
                # como "nueva" una prestación que ya estuvo
                # incluida en algún Master.
                # ==========================================

                detalles = (
                    DetalleMovimientoCaja.objects
                    .select_for_update()
                    .filter(

                        id__in=detalles_ids,

                        prestacion_obra_social__obra_social=obra_social,

                        fecha_prestacion__year=anio,
                        fecha_prestacion__month=mes,

                        movimiento__tipo="INGRESO",
                        movimiento__estado="ACTIVO",

                        estado="PENDIENTE",

                        obra_social_cobrada=False,

                        detalles_master_obra_social__isnull=True,
                    )
                )

                # ==========================================
                # VALIDAR QUE TODOS SIGAN DISPONIBLES
                # ==========================================

                if detalles.count() != len(
                    set(detalles_ids)
                ):

                    messages.error(
                        request,
                        "Una o más prestaciones seleccionadas "
                        "ya no están disponibles."
                    )

                    return redirect(
                        f"{request.path}?mes={mes}&anio={anio}"
                    )

                # ==========================================
                # CREAR CABECERA MASTER
                # ==========================================

                master = MasterObraSocial.objects.create(

                    obra_social=obra_social,

                    mes=mes,

                    anio=anio,

                    estado="BORRADOR",

                    creado_por=request.user
                )

                # ==========================================
                # CREAR DETALLES DEL MASTER
                # ==========================================
                #
                # IMPORTANTE:
                #
                # NO modificamos detalle.importe.
                #
                # Ese campo conserva siempre el valor
                # original de la prestación.
                #
                # El importe que debe pagar la OS será:
                #
                # importe prestación
                # -
                # coseguro cobrado
                #
                # El COPAGO NO se descuenta.
                #
                # El importe OS se calcula mediante:
                #
                # calcular_importe_obra_social(detalle)
                #
                # ==========================================

                DetalleMasterObraSocial.objects.bulk_create(

                    [

                        DetalleMasterObraSocial(

                            master=master,

                            detalle_movimiento=detalle,

                            estado="PENDIENTE",

                            # ==================================
                            # CONGELAR IMPORTE PRESENTADO
                            # ==================================
                            #
                            # Representa exactamente el importe
                            # presentado a la Obra Social.
                            #
                            # Prestación
                            # -
                            # coseguro cobrado
                            #
                            # El copago NO se descuenta.
                            # ==================================

                            importe_presentado=(
                                calcular_importe_obra_social(
                                    detalle
                                )
                            ),

                            # Todavía no existe resolución
                            # de la Obra Social.

                            importe_reconocido=None,

                            importe_debitado=Decimal("0.00"),

                            refacturable=False,

                            estado_refacturacion="NO_APLICA",

                        )

                        for detalle in detalles

                    ]

                )

        except Exception as e:

            messages.error(
                request,
                f"No se pudo generar el Master: {e}"
            )

            return redirect(
                f"{request.path}?mes={mes}&anio={anio}"
            )

        # ==================================================
        # MASTER GENERADO
        # ==================================================

        messages.success(
            request,
            "El Master fue generado correctamente."
        )

        return redirect(
            "obrasocial:master_obra_social_lista",
            obra_social_id=obra_social.id
        )

    # ======================================================
    # GET - BUSCAR PRESTACIONES
    # ======================================================

    mes = request.GET.get("mes")
    anio = request.GET.get("anio")

    if mes and anio:

        try:

            mes = int(mes)
            anio = int(anio)

        except (TypeError, ValueError):

            messages.error(
                request,
                "El período seleccionado no es válido."
            )

            mes = None
            anio = None

        if mes and anio:

            # ==================================================
            # MASTER EXISTENTE
            # ==================================================

            master_existente = (
                MasterObraSocial.objects
                .filter(
                    obra_social=obra_social,
                    mes=mes,
                    anio=anio
                )
                .first()
            )

            if master_existente:

                messages.warning(
                    request,
                    "Ya existe un Master para esta Obra Social "
                    "en el período seleccionado."
                )

            # ==================================================
            # PRESTACIONES DISPONIBLES
            # ==================================================
            #
            # Solamente mostramos prestaciones:
            #
            # - De esta Obra Social
            # - Del período seleccionado
            # - Con movimiento activo
            # - Pendientes
            # - No cobradas por OS
            # - Que nunca hayan sido incorporadas a un Master
            #
            # La futura REFACTURACIÓN tendrá un circuito
            # separado y NO pasará por este filtro.
            # ==================================================

            prestaciones = (

                DetalleMovimientoCaja.objects

                .filter(

                    prestacion_obra_social__obra_social=obra_social,

                    fecha_prestacion__year=anio,
                    fecha_prestacion__month=mes,

                    movimiento__tipo="INGRESO",
                    movimiento__estado="ACTIVO",

                    estado="PENDIENTE",

                    obra_social_cobrada=False,

                    detalles_master_obra_social__isnull=True,
                )

                .select_related(

                    "movimiento",

                    "movimiento__centro_medico",

                    "movimiento__paciente",

                    "movimiento__turno",

                    "movimiento__turno__medico",

                    "prestacion_obra_social",

                    "prestacion_obra_social__plan",
                )

                .order_by(

                    "movimiento__centro_medico__nombre",

                    "fecha_prestacion",

                    "id"
                )
            )

            # ==================================================
            # CALCULAR IMPORTE REAL A PRESENTAR A LA OS
            # ==================================================

            for detalle in prestaciones:

                detalle.importe_os_calculado = (
                    calcular_importe_obra_social(
                        detalle
                    )
                )

    # ======================================================
    # TEMPLATE
    # ======================================================

    return render(
        request,
        "obrasocial/master/nuevo.html",
        {
            "obra_social": obra_social,

            "prestaciones": prestaciones,

            "mes": mes or hoy.month,

            "anio": anio or hoy.year,
        }
    )


@login_required
def master_obra_social_detalle(request, obra_social_id, master_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para acceder al Master."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    # ======================================================
    # MASTER
    # ======================================================

    master = get_object_or_404(
        MasterObraSocial,
        pk=master_id,
        obra_social=obra_social
    )

    # ======================================================
    # DETALLES
    # ======================================================

    detalles = (
        master.detalles
        .select_related(
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__centro_medico",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__plan",
        )
        .order_by(
            "detalle_movimiento__movimiento__centro_medico__nombre",
            "detalle_movimiento__fecha_prestacion",
            "id"
        )
    )

    # ======================================================
    # ESTADO DE LIQUIDACIÓN / AUDITORÍA
    # ======================================================
    #
    # Consideramos cargada la liquidación cuando ya no
    # existen prestaciones pendientes de auditoría.
    # ======================================================

    liquidacion_cargada = (
        detalles.exists()
        and not detalles.filter(
            estado="PENDIENTE"
        ).exists()
    )

    # ======================================================
    # TOTALES PRESENTADOS
    # ======================================================

    total_master = Decimal("0.00")

    total_casa_central = Decimal("0.00")
    total_agua_de_oro = Decimal("0.00")

    cantidad_casa_central = 0
    cantidad_agua_de_oro = 0

    # ======================================================
    # TOTALES DE RESOLUCIÓN DE LA OBRA SOCIAL
    # ======================================================

    total_reconocido = Decimal("0.00")
    total_diferencia = Decimal("0.00")

    cantidad_pagadas = 0
    cantidad_debitadas = 0
    cantidad_rechazadas = 0

    # ======================================================
    # RECORRER PRESTACIONES
    # ======================================================

    for item in detalles:

        detalle = item.detalle_movimiento

        # --------------------------------------------------
        # IMPORTE ORIGINAL
        # --------------------------------------------------

        importe_original = (
            detalle.importe
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # COSEGURO COBRADO
        # --------------------------------------------------

        coseguro = Decimal("0.00")

        if detalle.coseguro_cobrado:
            coseguro = (
                detalle.importe_coseguro
                or Decimal("0.00")
            )

        # --------------------------------------------------
        # IMPORTE PRESENTADO A LA OBRA SOCIAL
        # --------------------------------------------------

        importe_os = (
                item.importe_presentado
                or Decimal("0.00")
            )

        # --------------------------------------------------
        # VARIABLES PARA EL HTML
        # --------------------------------------------------

        detalle.importe_original_master = importe_original
        detalle.coseguro_master = coseguro
        detalle.importe_os_calculado = importe_os

        # --------------------------------------------------
        # TOTAL PRESENTADO
        # --------------------------------------------------

        total_master += importe_os

        # --------------------------------------------------
        # TOTAL POR SEDE
        # --------------------------------------------------

        centro = detalle.movimiento.centro_medico
        nombre_centro = centro.nombre.lower()

        if "agua de oro" in nombre_centro:

            total_agua_de_oro += importe_os
            cantidad_agua_de_oro += 1

        else:

            total_casa_central += importe_os
            cantidad_casa_central += 1

        # ==================================================
        # RESULTADO INFORMADO POR LA OBRA SOCIAL
        # ==================================================

        estado_resultado = item.estado

        importe_reconocido = (
            item.importe_reconocido
            or Decimal("0.00")
        )

        # Dejamos estos valores disponibles para el template
        item.importe_presentado_calculado = importe_os
        item.importe_reconocido_calculado = importe_reconocido

        # --------------------------------------------------
        # DIFERENCIA
        # --------------------------------------------------

        diferencia = (
            importe_os
            - importe_reconocido
        )

        if diferencia < Decimal("0.00"):
            diferencia = Decimal("0.00")

        item.diferencia_calculada = diferencia

        # --------------------------------------------------
        # TOTALES RECONOCIDOS
        # --------------------------------------------------

        total_reconocido += importe_reconocido
        total_diferencia += diferencia

        # --------------------------------------------------
        # CONTADORES
        # --------------------------------------------------

        if estado_resultado == "ACEPTADO":

            cantidad_pagadas += 1

        elif estado_resultado == "DEBITO_PARCIAL":

            cantidad_debitadas += 1

        elif estado_resultado == "RECHAZADO":

            cantidad_rechazadas += 1
    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "obrasocial/master/detalle.html",
        {
            "obra_social": obra_social,
            "master": master,
            "detalles": detalles,

            "liquidacion_cargada": liquidacion_cargada,

            # PRESENTADO
            "total_master": total_master,

            # RECONOCIDO
            "total_reconocido": total_reconocido,

            # DIFERENCIA
            "total_diferencia": total_diferencia,

            # SEDES
            "total_casa_central": total_casa_central,
            "total_agua_de_oro": total_agua_de_oro,

            "cantidad_casa_central":
                cantidad_casa_central,

            "cantidad_agua_de_oro":
                cantidad_agua_de_oro,

            # RESULTADOS
            "cantidad_pagadas":
                cantidad_pagadas,

            "cantidad_debitadas":
                cantidad_debitadas,

            "cantidad_rechazadas":
                cantidad_rechazadas,
        }
    )


@login_required
def master_obra_social_presentar(request, obra_social_id, master_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para presentar Masters."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    # ======================================================
    # MASTER
    # ======================================================

    master = get_object_or_404(
        MasterObraSocial,
        pk=master_id,
        obra_social=obra_social
    )

    # ======================================================
    # SOLO SE PUEDE PRESENTAR UN BORRADOR
    # ======================================================

    if master.estado != "BORRADOR":

        messages.warning(
            request,
            "Este Master ya no se encuentra en estado Borrador."
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    # ======================================================
    # DEBE TENER PRESTACIONES
    # ======================================================

    if not master.detalles.exists():

        messages.error(
            request,
            "No se puede presentar un Master sin prestaciones."
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        fecha_presentacion = request.POST.get(
            "fecha_presentacion"
        )

        numero_presentacion = (
            request.POST.get(
                "numero_presentacion",
                ""
            ).strip()
        )

        numero_factura = (
            request.POST.get(
                "numero_factura",
                ""
            ).strip()
        )

        # ==================================================
        # VALIDAR FECHA
        # ==================================================

        if not fecha_presentacion:

            messages.error(
                request,
                "Debe indicar la fecha de presentación."
            )

        else:

            try:

                with transaction.atomic():

                    # ======================================
                    # BLOQUEAR MASTER
                    # ======================================

                    master_bloqueado = (
                        MasterObraSocial.objects
                        .select_for_update()
                        .get(
                            pk=master.id,
                            estado="BORRADOR",
                        )
                    )

                    # ======================================
                    # ACTUALIZAR MASTER
                    # ======================================

                    master_bloqueado.fecha_presentacion = (
                        fecha_presentacion
                    )

                    master_bloqueado.numero_presentacion = (
                        numero_presentacion
                    )

                    master_bloqueado.numero_factura = (
                        numero_factura
                    )

                    master_bloqueado.estado = "PRESENTADO"

                    master_bloqueado.save(
                        update_fields=[
                            "fecha_presentacion",
                            "numero_presentacion",
                            "numero_factura",
                            "estado",
                            "fecha_modificacion",
                        ]
                    )

                    # ======================================
                    # SI ES REFACTURACIÓN
                    # ======================================
                    #
                    # No tocamos:
                    #
                    # - MovimientoCaja
                    # - coseguro
                    # - copago
                    # - importe original
                    # - honorarios
                    #
                    # Solamente actualizamos la trazabilidad
                    # del detalle original.
                    # ======================================

                    if master_bloqueado.tipo == "REFACTURACION":

                        detalles_refacturados = (
                            DetalleMasterObraSocial.objects
                            .select_for_update()
                            .select_related(
                                "detalle_origen"
                            )
                            .filter(
                                master=master_bloqueado,
                                detalle_origen__isnull=False,
                            )
                        )

                        for nuevo_detalle in detalles_refacturados:

                            origen = (
                                nuevo_detalle.detalle_origen
                            )

                            origen.estado_refacturacion = (
                                "PRESENTADA"
                            )

                            origen.fecha_refacturacion = (
                                fecha_presentacion
                            )

                            origen.fecha_ultima_gestion = (
                                timezone.now()
                            )

                            origen.resuelto_por = (
                                request.user
                            )

                            origen.observacion_refacturacion = (
                                f"Refacturación presentada en "
                                f"Master #{master_bloqueado.id}. "
                                f"Fecha de presentación: "
                                f"{fecha_presentacion}. "
                                f"Usuario: "
                                f"{request.user.get_username()}."
                            )

                            origen.save(
                                update_fields=[
                                    "estado_refacturacion",
                                    "fecha_refacturacion",
                                    "fecha_ultima_gestion",
                                    "resuelto_por",
                                    "observacion_refacturacion",
                                ]
                            )

            except MasterObraSocial.DoesNotExist:

                messages.error(
                    request,
                    "El Master ya fue presentado "
                    "o cambió de estado."
                )

                return redirect(
                    "obrasocial:master_obra_social_detalle",
                    obra_social_id=obra_social.id,
                    master_id=master.id
                )

            # ==============================================
            # MENSAJE
            # ==============================================

            if master.tipo == "REFACTURACION":

                messages.success(
                    request,
                    "El Master de refacturación fue "
                    "marcado como PRESENTADO correctamente."
                )

            else:

                messages.success(
                    request,
                    "El Master fue marcado como "
                    "PRESENTADO correctamente."
                )

            return redirect(
                "obrasocial:master_obra_social_detalle",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

    # ======================================================
    # TEMPLATE
    # ======================================================

    return render(
        request,
        "obrasocial/master/presentar.html",
        {
            "obra_social": obra_social,
            "master": master,
            "hoy": date.today(),
        }
    )
# ==========================================================
# MASTER DE OBRA SOCIAL
# REGISTRAR PAGO
# ==========================================================
@login_required
def master_obra_social_registrar_pago(
    request,
    obra_social_id,
    master_id
):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para registrar cobros de Masters."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    # ======================================================
    # MASTER
    # ======================================================

    master = get_object_or_404(
        MasterObraSocial,
        pk=master_id,
        obra_social=obra_social
    )

    # ======================================================
    # SOLO MASTER PRESENTADO
    # ======================================================

    if master.estado != "PRESENTADO":

        messages.warning(
            request,
            "Solamente se puede registrar el cobro "
            "de un Master presentado."
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    # ======================================================
    # DETALLES DEL MASTER
    # ======================================================

    detalles = (
        master.detalles
        .select_related(
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__centro_medico",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__plan",
            "detalle_origen",
        )
        .order_by(
            "detalle_movimiento__fecha_prestacion",
            "id"
        )
    )

    # ======================================================
    # VERIFICAR QUE EXISTA LIQUIDACIÓN
    # ======================================================

    estados_validos = [
        "ACEPTADO",
        "DEBITO_PARCIAL",
        "RECHAZADO",
    ]

    if not detalles.exists():

        messages.warning(
            request,
            "El Master no contiene prestaciones."
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    for item in detalles:

        if item.estado not in estados_validos:

            messages.warning(
                request,
                "Debe cargar completamente la liquidación "
                "de la Obra Social antes de registrar el cobro."
            )

            return redirect(
                "obrasocial:master_obra_social_detalle",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

    # ======================================================
    # PREPARAR DATOS PARA MOSTRAR
    # ======================================================

    total_presentado = Decimal("0.00")
    total_reconocido = Decimal("0.00")
    total_debitado = Decimal("0.00")

    cantidad_aceptadas = 0
    cantidad_debitadas = 0
    cantidad_rechazadas = 0

    # ======================================================
    # RECORRER RESULTADOS
    # ======================================================

    for item in detalles:

        importe_presentado = (
            item.importe_presentado
            or Decimal("0.00")
        )

        importe_reconocido = (
            item.importe_reconocido
            or Decimal("0.00")
        )

        importe_debitado = (
            item.importe_debitado
            or Decimal("0.00")
        )

        item.importe_presentado_calculado = (
            importe_presentado
        )

        item.importe_reconocido_calculado = (
            importe_reconocido
        )

        item.diferencia_calculada = (
            importe_debitado
        )

        total_presentado += importe_presentado
        total_reconocido += importe_reconocido
        total_debitado += importe_debitado

        if item.estado == "ACEPTADO":
            cantidad_aceptadas += 1

        elif item.estado == "DEBITO_PARCIAL":
            cantidad_debitadas += 1

        elif item.estado == "RECHAZADO":
            cantidad_rechazadas += 1

    # ======================================================
    # POST - CONFIRMAR COBRO
    # ======================================================

    if request.method == "POST":

        fecha_cobro = request.POST.get(
            "fecha_cobro"
        )

        # ==================================================
        # VALIDAR FECHA
        # ==================================================

        if not fecha_cobro:

            messages.error(
                request,
                "Debe indicar la fecha de cobro."
            )

            return redirect(
                "obrasocial:master_obra_social_registrar_pago",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

        try:

            with transaction.atomic():

                # ==========================================
                # BLOQUEAR MASTER
                # ==========================================

                master_bloqueado = (
                    MasterObraSocial.objects
                    .select_for_update()
                    .get(
                        pk=master.id,
                        estado="PRESENTADO"
                    )
                )

                # ==========================================
                # DETALLES BLOQUEADOS
                # ==========================================

                detalles_bloqueados = (
                    DetalleMasterObraSocial.objects
                    .select_for_update()
                    .select_related(
                        "detalle_movimiento",
                        "detalle_movimiento__prestacion_obra_social",
                        "detalle_origen",
                    )
                    .filter(
                        master=master_bloqueado
                    )
                )

                # ==========================================
                # PROCESAR COBRO
                # ==========================================

                for item in detalles_bloqueados:

                    detalle = item.detalle_movimiento

                    importe_reconocido = (
                        item.importe_reconocido
                        or Decimal("0.00")
                    )

                    honorario_os = Decimal("0.00")
                    importe_consultorio = Decimal("0.00")

                    # ======================================
                    # ACEPTADO / DÉBITO PARCIAL
                    # ======================================

                    if (
                        item.estado in [
                            "ACEPTADO",
                            "DEBITO_PARCIAL",
                        ]
                        and importe_reconocido > Decimal("0.00")
                    ):

                        prestacion = (
                            detalle.prestacion_obra_social
                        )

                        if prestacion is None:
                            raise ValueError(
                                "La prestación no posee configuración "
                                "de Obra Social."
                            )

                        # ==================================
                        # COSEGURO
                        # ==================================

                        coseguro = (
                            detalle.importe_coseguro
                            or Decimal("0.00")
                        )

                        # ==================================
                        # RECONOCIMIENTOS ANTERIORES
                        # ==================================

                        detalles_anteriores = (
                            DetalleMasterObraSocial.objects
                            .filter(
                                detalle_movimiento=detalle,
                                master__estado="COBRADO",
                            )
                            .exclude(
                                pk=item.pk
                            )
                        )

                        importe_os_reconocido_anterior = (
                            Decimal("0.00")
                        )

                        honorario_os_generado_anterior = (
                            Decimal("0.00")
                        )

                        consultorio_generado_anterior = (
                            Decimal("0.00")
                        )

                        for anterior in detalles_anteriores:

                            importe_os_reconocido_anterior += (
                                anterior.importe_reconocido
                                or Decimal("0.00")
                            )

                            honorario_os_generado_anterior += (
                                anterior.honorario_medico_reconocido
                                or Decimal("0.00")
                            )

                            consultorio_generado_anterior += (
                                anterior.importe_consultorio_reconocido
                                or Decimal("0.00")
                            )

                        # ==================================
                        # TOTAL OS RECONOCIDO ACUMULADO
                        # ==================================

                        importe_os_reconocido_acumulado = (
                            importe_os_reconocido_anterior
                            + importe_reconocido
                        )

                        # ==================================
                        # TOTAL ECONÓMICO RECUPERADO
                        # ==================================
                        #
                        # El coseguro forma parte del valor
                        # económico de la prestación.
                        #
                        # Se agrega una sola vez al acumulado.
                        # ==================================

                        importe_total_recuperado = (
                            importe_os_reconocido_acumulado
                            + coseguro
                        )

                        # ==================================
                        # IVA
                        # ==================================

                        porcentaje_iva = (
                            prestacion.porcentaje_iva
                            or Decimal("0.00")
                        )

                        importe_iva_total = (
                            importe_total_recuperado
                            * porcentaje_iva
                            / Decimal("100")
                        )

                        # ==================================
                        # PROVEEDOR
                        # ==================================

                        importe_proveedor = (
                            prestacion.importe_proveedor
                            or Decimal("0.00")
                        )

                        # ==================================
                        # BASE DISTRIBUIBLE ACUMULADA
                        # ==================================

                        base_distribuible_total = (
                            importe_total_recuperado
                            - importe_iva_total
                            - importe_proveedor
                        )

                        if (
                            base_distribuible_total
                            < Decimal("0.00")
                        ):
                            base_distribuible_total = (
                                Decimal("0.00")
                            )

                        # ==================================
                        # PORCENTAJE CONSULTORIO
                        # ==================================

                        porcentaje_consultorio = (
                            prestacion.porcentaje_consultorio
                            or Decimal("0.00")
                        )

                        # ==================================
                        # HONORARIO MÉDICO TOTAL ACUMULADO
                        # ==================================

                        if (
                            prestacion.tipo_calculo
                            == "FIJO_MEDICO"
                        ):

                            honorario_total_acumulado = (
                                prestacion.honorario_fijo_medico
                                or Decimal("0.00")
                            )

                        else:

                            porcentaje_medico = (
                                prestacion.porcentaje_medico
                                or Decimal("0.00")
                            )

                            honorario_total_acumulado = (
                                base_distribuible_total
                                * porcentaje_medico
                                / Decimal("100")
                            )

                        # ==================================
                        # CONSULTORIO TOTAL ACUMULADO
                        # ==================================
                        #
                        # Utilizamos el porcentaje de
                        # consultorio configurado en la
                        # PrestacionPlan.
                        # ==================================

                        consultorio_total_acumulado = (
                            base_distribuible_total
                            * porcentaje_consultorio
                            / Decimal("100")
                        )

                        # ==================================
                        # COMPONENTE MÉDICO DE OBRA SOCIAL
                        # ==================================
                        #
                        # El coseguro ya tiene su propio
                        # circuito de liquidación médica.
                        # Por eso se descuenta del honorario
                        # médico de OS.
                        # ==================================

                        honorario_os_acumulado = (
                            honorario_total_acumulado
                            - coseguro
                        )

                        if (
                            honorario_os_acumulado
                            < Decimal("0.00")
                        ):
                            honorario_os_acumulado = (
                                Decimal("0.00")
                            )

                        # ==================================
                        # HONORARIO MÉDICO DE ESTA COBRANZA
                        # ==================================

                        honorario_os = (
                            honorario_os_acumulado
                            - honorario_os_generado_anterior
                        )

                        if honorario_os < Decimal("0.00"):
                            honorario_os = Decimal("0.00")

                        # ==================================
                        # CONSULTORIO DE ESTA COBRANZA
                        # ==================================
                        #
                        # Igual que con el médico:
                        #
                        # total acumulado que corresponde
                        # menos lo ya generado anteriormente.
                        #
                        # Esto permite recuperar débitos sin
                        # duplicar el 30% del consultorio.
                        # ==================================

                        importe_consultorio = (
                            consultorio_total_acumulado
                            - consultorio_generado_anterior
                        )

                        if (
                            importe_consultorio
                            < Decimal("0.00")
                        ):
                            importe_consultorio = (
                                Decimal("0.00")
                            )

                        # ==================================
                        # SNAPSHOT DEL DETALLE DEL MASTER
                        # MÉDICO + CONSULTORIO
                        # ==================================

                        item.honorario_medico_reconocido = (
                            honorario_os
                        )

                        item.honorario_medico_liquidado = False

                        item.fecha_liquidacion_honorario = None

                        item.importe_consultorio_reconocido = (
                            importe_consultorio
                        )

                        item.consultorio_ingresado_caja = False

                        item.fecha_ingreso_consultorio = None

                        item.movimiento_ingreso_consultorio = None

                        item.save(
                            update_fields=[
                                "honorario_medico_reconocido",
                                "honorario_medico_liquidado",
                                "fecha_liquidacion_honorario",
                                "importe_consultorio_reconocido",
                                "consultorio_ingresado_caja",
                                "fecha_ingreso_consultorio",
                                "movimiento_ingreso_consultorio",
                            ]
                        )

                        # ==================================
                        # COMPATIBILIDAD SISTEMA ACTUAL
                        # ==================================

                        detalle.obra_social_cobrada = True

                        detalle.fecha_cobro_obra_social = (
                            fecha_cobro
                        )

                        detalle.importe_reconocido_obra_social = (
                            importe_reconocido
                        )

                        detalle.honorario_reconocido_obra_social = (
                            honorario_os
                        )

                    # ======================================
                    # RECHAZADO / RECONOCIDO EN CERO
                    # ======================================

                    else:

                        # ==================================
                        # ESTE MASTER NO GENERA HONORARIO
                        # NI CRÉDITO PARA EL CONSULTORIO
                        # ==================================

                        item.honorario_medico_reconocido = (
                            Decimal("0.00")
                        )

                        item.honorario_medico_liquidado = False

                        item.fecha_liquidacion_honorario = None

                        item.importe_consultorio_reconocido = (
                            Decimal("0.00")
                        )

                        item.consultorio_ingresado_caja = False

                        item.fecha_ingreso_consultorio = None

                        item.movimiento_ingreso_consultorio = None

                        item.save(
                            update_fields=[
                                "honorario_medico_reconocido",
                                "honorario_medico_liquidado",
                                "fecha_liquidacion_honorario",
                                "importe_consultorio_reconocido",
                                "consultorio_ingresado_caja",
                                "fecha_ingreso_consultorio",
                                "movimiento_ingreso_consultorio",
                            ]
                        )

                        # ==================================
                        # ¿HUBO ALGÚN COBRO ANTERIOR?
                        # ==================================

                        cobro_anterior = (
                            DetalleMasterObraSocial.objects
                            .filter(
                                detalle_movimiento=detalle,
                                master__estado="COBRADO",
                                importe_reconocido__gt=0,
                            )
                            .exclude(
                                pk=item.pk
                            )
                            .order_by(
                                "-master__fecha_cobro",
                                "-id"
                            )
                            .first()
                        )

                        if cobro_anterior:

                            # ==============================
                            # CONSERVAR MOVIMIENTO COBRADO
                            # ==============================

                            detalle.obra_social_cobrada = True

                            if (
                                detalle.fecha_cobro_obra_social
                                is None
                            ):
                                detalle.fecha_cobro_obra_social = (
                                    cobro_anterior.master.fecha_cobro
                                )

                            # ==============================
                            # COMPATIBILIDAD
                            # ==============================

                            detalle.importe_reconocido_obra_social = (
                                cobro_anterior.importe_reconocido
                                or Decimal("0.00")
                            )

                            detalle.honorario_reconocido_obra_social = (
                                cobro_anterior.honorario_medico_reconocido
                                or Decimal("0.00")
                            )

                        else:

                            # ==============================
                            # NUNCA HUBO COBRO
                            # ==============================

                            detalle.obra_social_cobrada = False

                            detalle.fecha_cobro_obra_social = None

                            detalle.importe_reconocido_obra_social = (
                                Decimal("0.00")
                            )

                            detalle.honorario_reconocido_obra_social = (
                                Decimal("0.00")
                            )

                    # ======================================
                    # GUARDAR DETALLE MOVIMIENTO
                    # ======================================

                    detalle.save(
                        update_fields=[
                            "obra_social_cobrada",
                            "fecha_cobro_obra_social",
                            "importe_reconocido_obra_social",
                            "honorario_reconocido_obra_social",
                        ]
                    )

                # ==========================================
                # MASTER COBRADO
                # ==========================================

                master_bloqueado.estado = "COBRADO"

                master_bloqueado.fecha_cobro = (
                    fecha_cobro
                )

                master_bloqueado.save(
                    update_fields=[
                        "estado",
                        "fecha_cobro",
                        "fecha_modificacion",
                    ]
                )

        except MasterObraSocial.DoesNotExist:

            messages.error(
                request,
                "El Master ya fue procesado "
                "o cambió de estado."
            )

            return redirect(
                "obrasocial:master_obra_social_detalle",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

        # ==================================================
        # OK
        # ==================================================

        messages.success(
            request,
            (
                "El cobro del Master fue registrado "
                f"correctamente por "
                f"${total_reconocido:,.2f}."
            )
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    # ======================================================
    # GET
    # ======================================================

    return render(
        request,
        "obrasocial/master/registrar_pago.html",
        {
            "obra_social": obra_social,
            "master": master,
            "detalles": detalles,

            "total_presentado": total_presentado,
            "total_reconocido": total_reconocido,
            "total_debitado": total_debitado,

            "cantidad_pagadas": cantidad_aceptadas,

            "cantidad_aceptadas": cantidad_aceptadas,
            "cantidad_debitadas": cantidad_debitadas,
            "cantidad_rechazadas": cantidad_rechazadas,

            "hoy": date.today(),
        }
    )

# ==========================================================
# MASTER DE OBRA SOCIAL
# CARGAR LIQUIDACIÓN / AUDITORÍA DE LA OBRA SOCIAL
# ==========================================================

@login_required
def master_obra_social_cargar_liquidacion(
    request,
    obra_social_id,
    master_id
):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):

        raise PermissionDenied(
            "No tiene permisos para cargar liquidaciones "
            "de Obras Sociales."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    # ======================================================
    # MASTER
    # ======================================================

    master = get_object_or_404(
        MasterObraSocial,
        pk=master_id,
        obra_social=obra_social
    )

    # ======================================================
    # SOLAMENTE MASTER PRESENTADO
    # ======================================================

    if master.estado != "PRESENTADO":

        messages.warning(
            request,
            "Solamente se puede cargar la liquidación "
            "de un Master presentado."
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    # ======================================================
    # DETALLES
    # ======================================================

    detalles = (
        master.detalles
        .select_related(
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__centro_medico",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__plan",
        )
        .order_by(
            "detalle_movimiento__fecha_prestacion",
            "id"
        )
    )




    # ======================================================
    # TOTAL PRESENTADO
    # ======================================================

    total_presentado = sum(
        (
            item.importe_presentado
            or Decimal("0.00")
        )
        for item in detalles
    )

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        fecha_resolucion = request.POST.get(
            "fecha_resolucion"
        )

        # ==================================================
        # VALIDAR FECHA
        # ==================================================

        if not fecha_resolucion:

            messages.error(
                request,
                "Debe indicar la fecha de liquidación "
                "o resolución de la Obra Social."
            )

            return redirect(
                "obrasocial:master_obra_social_cargar_liquidacion",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

        try:

            with transaction.atomic():

                # ==========================================
                # BLOQUEAR MASTER
                # ==========================================

                master_bloqueado = (
                    MasterObraSocial.objects
                    .select_for_update()
                    .get(
                        pk=master.id,
                        estado="PRESENTADO"
                    )
                )

                # ==========================================
                # RECORRER PRESTACIONES
                # ==========================================

                for item in detalles:

                    # ======================================
                    # RESULTADO DE AUDITORÍA
                    # ======================================

                    estado = request.POST.get(
                        f"estado_{item.id}"
                    )

                    if estado not in [
                        "ACEPTADO",
                        "DEBITO_PARCIAL",
                        "RECHAZADO",
                    ]:

                        raise ValueError(
                            "Debe indicar el resultado de "
                            "todas las prestaciones."
                        )

                    # ======================================
                    # IMPORTE PRESENTADO
                    # ======================================

                    importe_presentado = (
                        item.importe_presentado
                        or Decimal("0.00")
                    )

                    # ======================================
                    # IMPORTE RECONOCIDO
                    # ======================================

                    importe_reconocido_texto = (
                        request.POST.get(
                            f"importe_{item.id}",
                            ""
                        )
                        .strip()
                    )

                    if importe_reconocido_texto:

                        importe_reconocido = Decimal(
                            importe_reconocido_texto.replace(
                                ",",
                                "."
                            )
                        )

                    else:

                        importe_reconocido = Decimal("0.00")

                    # ======================================
                    # VALIDACIONES GENERALES
                    # ======================================

                    if importe_reconocido < Decimal("0.00"):

                        raise ValueError(
                            "El importe reconocido no puede "
                            "ser negativo."
                        )

                    if importe_reconocido > importe_presentado:

                        raise ValueError(
                            "El importe reconocido no puede "
                            "ser mayor al importe presentado."
                        )

                    # ======================================
                    # ACEPTADO
                    # ======================================

                    if estado == "ACEPTADO":

                        importe_reconocido = (
                            importe_presentado
                        )

                        importe_debitado = Decimal("0.00")

                    # ======================================
                    # RECHAZADO
                    # ======================================

                    elif estado == "RECHAZADO":

                        importe_reconocido = Decimal("0.00")

                        importe_debitado = (
                            importe_presentado
                        )

                    # ======================================
                    # DÉBITO PARCIAL
                    # ======================================

                    else:

                        if (
                            importe_reconocido
                            <= Decimal("0.00")
                            or importe_reconocido
                            >= importe_presentado
                        ):

                            raise ValueError(
                                "En un débito parcial, el importe "
                                "reconocido debe ser mayor a $0 "
                                "y menor al importe presentado."
                            )

                        importe_debitado = (
                            importe_presentado
                            - importe_reconocido
                        )

                    # ======================================
                    # MOTIVO NORMALIZADO
                    # DÉBITO / RECHAZO
                    # ======================================

                    motivo_observacion = (
                        request.POST.get(
                            f"motivo_observacion_{item.id}",
                            ""
                        )
                        .strip()
                    )

                    detalle_observacion = (
                        request.POST.get(
                            f"detalle_observacion_{item.id}",
                            ""
                        )
                        .strip()
                    )

                    # ======================================
                    # ACEPTADO
                    # No necesita motivo
                    # ======================================

                    if estado == "ACEPTADO":

                        motivo_observacion = ""
                        detalle_observacion = ""

                    # ======================================
                    # DÉBITO / RECHAZO
                    # El motivo es obligatorio
                    # ======================================

                    else:

                        motivos_validos = dict(
                            DetalleMasterObraSocial.MOTIVOS_OBSERVACION
                        )

                        if not motivo_observacion:

                            raise ValueError(
                                "Debe seleccionar el motivo de todos "
                                "los débitos y rechazos."
                            )

                        if motivo_observacion not in motivos_validos:

                            raise ValueError(
                                "El motivo seleccionado no es válido."
                            )

                        # Si selecciona OTRO necesitamos explicación.

                        if (
                            motivo_observacion == "OTRO"
                            and not detalle_observacion
                        ):

                            raise ValueError(
                                "Debe indicar una explicación cuando "
                                "selecciona 'Otro motivo'."
                            )

                    # ======================================
                    # REFACTURABLE
                    # ======================================

                    refacturable = (
                        request.POST.get(
                            f"refacturable_{item.id}"
                        )
                        == "1"
                    )

                    # Una prestación aceptada no necesita
                    # refacturación.

                    if estado == "ACEPTADO":

                        refacturable = False
                        estado_refacturacion = "NO_APLICA"

                    elif refacturable:

                        estado_refacturacion = "PENDIENTE"

                    else:

                        estado_refacturacion = "NO_APLICA"

                    # ======================================
                    # GUARDAR RESULTADO
                    # ======================================

                    item.estado = estado

                    item.importe_reconocido = (
                        importe_reconocido
                    )

                    item.importe_debitado = (
                        importe_debitado
                    )

                    item.motivo_observacion = (
                        motivo_observacion
                    )

                    item.detalle_observacion = (
                        detalle_observacion
                    )

                    # Conservamos motivo_debito por compatibilidad
                    # con registros históricos.
                    item.motivo_debito = (
                        detalle_observacion
                    )

                    item.refacturable = (
                        refacturable
                    )

                    item.estado_refacturacion = (
                        estado_refacturacion
                    )

                    item.fecha_resolucion = (
                        fecha_resolucion
                    )

                    item.save(
                        update_fields=[
                            "estado",
                            "importe_reconocido",
                            "importe_debitado",
                            "motivo_debito",
                            "refacturable",
                            "estado_refacturacion",
                            "motivo_observacion",
                            "detalle_observacion",
                            "motivo_debito",
                            "fecha_resolucion",
                        ]
                    )

                # ==========================================
                # IMPORTANTE
                # ==========================================
                #
                # NO marcamos todavía:
                #
                # master.estado = COBRADO
                #
                # NO modificamos:
                #
                # detalle.obra_social_cobrada
                #
                # Esta pantalla solamente registra
                # la respuesta / auditoría de la OS.
                # ==========================================

                master_bloqueado.save(
                    update_fields=[
                        "fecha_modificacion"
                    ]
                )

        except (
            ValueError,
            InvalidOperation
        ) as e:

            messages.error(
                request,
                str(e)
            )

            return redirect(
                "obrasocial:master_obra_social_cargar_liquidacion",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

        # ==================================================
        # OK
        # ==================================================

        messages.success(
            request,
            "La liquidación de la Obra Social fue "
            "registrada correctamente."
        )

        return redirect(
            "obrasocial:master_obra_social_detalle",
            obra_social_id=obra_social.id,
            master_id=master.id
        )

    # ======================================================
    # GET
    # ======================================================

    return render(
        request,
        "obrasocial/master/cargar_liquidacion.html",
        {
            "obra_social": obra_social,
            "master": master,
            "detalles": detalles,
            "total_presentado": total_presentado,
            "hoy": date.today(),
        }
    )




@login_required
def master_obra_social_imprimir(request, obra_social_id, master_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para imprimir el Master."
        )

    # ======================================================
    # OBRA SOCIAL
    # ======================================================

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False
    )

    # ======================================================
    # MASTER
    # ======================================================

    master = get_object_or_404(
        MasterObraSocial,
        pk=master_id,
        obra_social=obra_social
    )

    # ======================================================
    # DETALLES
    # ======================================================

    detalles = (
        master.detalles
        .select_related(
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__centro_medico",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__plan",
        )
        .order_by(
            "detalle_movimiento__movimiento__centro_medico__nombre",
            "detalle_movimiento__fecha_prestacion",
            "id"
        )
    )

    # ======================================================
    # TOTALES
    # ======================================================

    total_master = Decimal("0.00")

    total_casa_central = Decimal("0.00")
    total_agua_de_oro = Decimal("0.00")

    cantidad_casa_central = 0
    cantidad_agua_de_oro = 0

    # ======================================================
    # RECORRER DETALLES
    # ======================================================

    for item in detalles:

        detalle = item.detalle_movimiento

        # --------------------------------------------------
        # IMPORTE ORIGINAL
        # --------------------------------------------------

        importe_original = (
            detalle.importe
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # COSEGURO COBRADO
        # --------------------------------------------------

        coseguro = Decimal("0.00")

        if detalle.coseguro_cobrado:

            coseguro = (
                detalle.importe_coseguro
                or Decimal("0.00")
            )

        # --------------------------------------------------
        # IMPORTE REAL A PRESENTAR A LA OBRA SOCIAL
        # --------------------------------------------------
        #
        # Prestación - coseguro cobrado
        #
        # El copago NO se descuenta.
        # --------------------------------------------------

        importe_os = calcular_importe_obra_social(
            detalle
        )

        # --------------------------------------------------
        # VARIABLES PARA imprimir.html
        # --------------------------------------------------

        detalle.importe_original_master = importe_original

        detalle.coseguro_master = coseguro

        detalle.importe_os_calculado = importe_os

        # --------------------------------------------------
        # TOTAL GENERAL
        # --------------------------------------------------

        total_master += importe_os

        # --------------------------------------------------
        # TOTAL POR SEDE
        # --------------------------------------------------

        centro = detalle.movimiento.centro_medico

        nombre_centro = centro.nombre.lower()

        if "agua de oro" in nombre_centro:

            total_agua_de_oro += importe_os

            cantidad_agua_de_oro += 1

        else:

            total_casa_central += importe_os

            cantidad_casa_central += 1

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "obrasocial/master/imprimir.html",
        {
            "obra_social": obra_social,
            "master": master,
            "detalles": detalles,

            "total_master": total_master,

            "total_casa_central": total_casa_central,
            "total_agua_de_oro": total_agua_de_oro,

            "cantidad_casa_central":
                cantidad_casa_central,

            "cantidad_agua_de_oro":
                cantidad_agua_de_oro,
        }
    )

from core.models import CentroMedico
from core.models import CentroMedico


@login_required
def ingresos_consultorio_os(request):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para acceder a los ingresos "
            "del consultorio por Obras Sociales."
        )

    # ======================================================
    # CENTRO MÉDICO ACTUAL
    # ======================================================

    centro_id = request.session.get("centro_id")

    if not centro_id:
        messages.warning(
            request,
            "Debe seleccionar una sede."
        )
        return redirect("home")

    centro_medico = get_object_or_404(
        CentroMedico,
        pk=centro_id
    )

     # ======================================================
    # CAJAS ABIERTAS DE HOY - SEDE ACTIVA
    # ======================================================

    hoy = timezone.localdate()

    cajas_abiertas = list(
        CajaDiaria.objects.filter(
            centro_medico=centro_medico,
            fecha=hoy,
            estado="ABIERTA",
        ).order_by("turno")
    )

    cantidad_cajas_abiertas = len(cajas_abiertas)


    # ======================================================
    # MEDIOS DE PAGO ACTIVOS
    # ======================================================

    medios_pago = MedioPago.objects.filter(
        activo=True
    ).order_by("nombre")

    # ======================================================
    # DETALLES PENDIENTES DE ESTA SEDE
    # ======================================================

    pendientes = (
        DetalleMasterObraSocial.objects
        .filter(
            master__estado="COBRADO",

            # Siempre respetamos la sede activa
            detalle_movimiento__movimiento__centro_medico=centro_medico,

            importe_consultorio_reconocido__isnull=False,
            importe_consultorio_reconocido__gt=0,

            consultorio_ingresado_caja=False,
        )
        .select_related(
            "master",
            "master__obra_social",

            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",

            "detalle_movimiento__prestacion_obra_social",
            "detalle_origen",
        )
        .order_by(
            "master__fecha_cobro",
            "master_id",
            "id",
        )
    )

    # ======================================================
    # AGRUPAR PENDIENTES POR MASTER
    # ======================================================

    masters_dict = {}

    for item in pendientes:

        master = item.master

        if master.id not in masters_dict:

            masters_dict[master.id] = {
                "master": master,
                "prestaciones": [],
                "cantidad": 0,
                "total_consultorio": Decimal("0.00"),
            }

        masters_dict[master.id]["prestaciones"].append(
            item
        )

        masters_dict[master.id]["cantidad"] += 1

        masters_dict[master.id]["total_consultorio"] += (
            item.importe_consultorio_reconocido
            or Decimal("0.00")
        )

    masters_pendientes = list(
        masters_dict.values()
    )

    # ======================================================
    # TOTAL GENERAL PENDIENTE
    # ======================================================

    total_pendiente = sum(
        (
            grupo["total_consultorio"]
            for grupo in masters_pendientes
        ),
        Decimal("0.00")
    )

    # ======================================================
    # FILTROS DEL HISTORIAL
    # ======================================================

    hoy = timezone.localdate()

    try:
        mes_historial = int(
            request.GET.get("mes", hoy.month)
        )
    except (TypeError, ValueError):
        mes_historial = hoy.month

    try:
        anio_historial = int(
            request.GET.get("anio", hoy.year)
        )
    except (TypeError, ValueError):
        anio_historial = hoy.year

    # Validaciones simples
    if mes_historial < 1 or mes_historial > 12:
        mes_historial = hoy.month

    if anio_historial < 2000 or anio_historial > 2100:
        anio_historial = hoy.year

    # ======================================================
    # HISTORIAL DE INGRESOS DEL CONSULTORIO
    #
    # Importante:
    # filtramos por FECHA REAL DE INGRESO A CAJA,
    # no por el período del Master.
    # ======================================================

    historial = (
        DetalleMasterObraSocial.objects
        .filter(
            consultorio_ingresado_caja=True,

            movimiento_ingreso_consultorio__isnull=False,

            detalle_movimiento__movimiento__centro_medico=centro_medico,

            fecha_ingreso_consultorio__year=anio_historial,
            fecha_ingreso_consultorio__month=mes_historial,
        )
        .select_related(
            "master",
            "master__obra_social",

            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_movimiento__prestacion_obra_social",

            "movimiento_ingreso_consultorio",
            "movimiento_ingreso_consultorio__creado_por",
        )
        .prefetch_related(
            "movimiento_ingreso_consultorio__detalles_medios_pago",
            "movimiento_ingreso_consultorio__detalles_medios_pago__medio_pago",
        )
        .order_by(
            "-fecha_ingreso_consultorio",
            "-master_id",
            "-id",
        )
    )

    # ======================================================
    # AGRUPAR HISTORIAL POR MOVIMIENTO DE CAJA
    #
    # Esto es importante porque un mismo ingreso puede
    # contener varias prestaciones del mismo Master.
    # ======================================================

    historial_dict = {}

    for item in historial:

        movimiento = item.movimiento_ingreso_consultorio

        if not movimiento:
            continue

        movimiento_id = movimiento.id

        if movimiento_id not in historial_dict:

            # ----------------------------------------------
            # MEDIOS DE PAGO DEL MOVIMIENTO
            # ----------------------------------------------

            detalles_medios = list(
                movimiento.detalles_medios_pago.all()
            )

            medios = []

            for detalle_medio in detalles_medios:

                medios.append({
                    "nombre": detalle_medio.medio_pago.nombre,
                    "importe": detalle_medio.importe,
                })

            historial_dict[movimiento_id] = {

                "movimiento": movimiento,

                "master": item.master,

                "obra_social": item.master.obra_social,

                "fecha_ingreso": item.fecha_ingreso_consultorio,

                "prestaciones": [],

                "cantidad": 0,

                "total_consultorio": Decimal("0.00"),

                "medios_pago": medios,
            }

        # ----------------------------------------------
        # PRESTACIÓN
        # ----------------------------------------------

        historial_dict[movimiento_id][
            "prestaciones"
        ].append(item)

        historial_dict[movimiento_id][
            "cantidad"
        ] += 1

        historial_dict[movimiento_id][
            "total_consultorio"
        ] += (
            item.importe_consultorio_reconocido
            or Decimal("0.00")
        )

    historial_ingresos = list(
        historial_dict.values()
    )

    # ======================================================
    # RESUMEN DEL HISTORIAL
    # ======================================================

    total_ingresado_historial = sum(
        (
            grupo["total_consultorio"]
            for grupo in historial_ingresos
        ),
        Decimal("0.00")
    )

    cantidad_ingresos_historial = len(
        historial_ingresos
    )

    cantidad_prestaciones_historial = sum(
        grupo["cantidad"]
        for grupo in historial_ingresos
    )

    # ======================================================
    # CANTIDAD DE MASTERS DIFERENTES
    # ======================================================

    masters_historial_ids = {
        grupo["master"].id
        for grupo in historial_ingresos
    }

    cantidad_masters_historial = len(
        masters_historial_ids
    )

    # ======================================================
    # RESUMEN POR MEDIO DE PAGO
    # ======================================================

    resumen_medios_dict = {}

    for grupo in historial_ingresos:

        for medio in grupo["medios_pago"]:

            nombre = medio["nombre"]
            importe = medio["importe"] or Decimal("0.00")

            if nombre not in resumen_medios_dict:
                resumen_medios_dict[nombre] = Decimal("0.00")

            resumen_medios_dict[nombre] += importe

    resumen_medios_pago = [
        {
            "nombre": nombre,
            "importe": importe,
        }
        for nombre, importe
        in sorted(resumen_medios_dict.items())
    ]

    # ======================================================
    # AÑOS DISPONIBLES PARA EL SELECT
    # ======================================================

    anios_disponibles = list(
        range(
            hoy.year,
            max(2024, hoy.year - 5) - 1,
            -1
        )
    )

    # Si estamos consultando manualmente un año que no está
    # dentro del rango, también lo agregamos.
    if anio_historial not in anios_disponibles:
        anios_disponibles.append(anio_historial)
        anios_disponibles.sort(reverse=True)

    # ======================================================
    # MESES
    # ======================================================

    meses = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "obrasocial/consultorio/ingresos_pendientes.html",
        {
            # SEDE
            "centro_medico": centro_medico,

            # PENDIENTES
            "masters_pendientes": masters_pendientes,
            "total_pendiente": total_pendiente,

            # PARA EL MODAL DE INGRESO
            "medios_pago": medios_pago,

            # CAJAS ABIERTAS DE HOY
            "cajas_abiertas": cajas_abiertas,
            "cantidad_cajas_abiertas": cantidad_cajas_abiertas,

            # HISTORIAL
            "historial_ingresos": historial_ingresos,
            "total_ingresado_historial": total_ingresado_historial,
            "cantidad_ingresos_historial": cantidad_ingresos_historial,
            "cantidad_masters_historial": cantidad_masters_historial,
            "cantidad_prestaciones_historial": cantidad_prestaciones_historial,

            # RESUMEN MEDIOS DE PAGO
            "resumen_medios_pago": resumen_medios_pago,

            # FILTROS
            "mes_historial": mes_historial,
            "anio_historial": anio_historial,
            "meses": meses,
            "anios_disponibles": anios_disponibles,
        }
    )


from caja.models import CajaDiaria, MovimientoCaja


@login_required
@transaction.atomic
def ingresar_master_consultorio_caja(request, master_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para registrar ingresos "
            "del consultorio por Obras Sociales."
        )

    # ======================================================
    # SOLO POST
    # ======================================================

    if request.method != "POST":
        return redirect(
            "obrasocial:ingresos_consultorio_os"
        )

    # ======================================================
    # CENTRO MÉDICO ACTIVO
    # ======================================================

    centro_id = request.session.get("centro_id")

    if not centro_id:
        messages.error(
            request,
            "Debe seleccionar una sede."
        )
        return redirect(
            "obrasocial:ingresos_consultorio_os"
        )

    centro_medico = get_object_or_404(
        CentroMedico,
        pk=centro_id
    )

    # ======================================================
    # MASTER COBRADO
    # ======================================================

    master = get_object_or_404(
        MasterObraSocial.objects.select_related(
            "obra_social"
        ),
        pk=master_id,
        estado="COBRADO",
    )

    # ======================================================
    # MEDIO DE PAGO
    # ======================================================

    medio_pago_id = request.POST.get("medio_pago")

    if not medio_pago_id:
        messages.error(
            request,
            "Debe seleccionar un medio de pago."
        )
        return redirect(
            "obrasocial:ingresos_consultorio_os"
        )

    medio_pago = get_object_or_404(
        MedioPago,
        pk=medio_pago_id,
        activo=True,
    )

    # ======================================================
    # CAJAS ABIERTAS DE LA SEDE Y FECHA ACTUAL
    # ======================================================

    hoy = timezone.localdate()

    cajas_abiertas = list(
        CajaDiaria.objects
        .select_for_update()
        .filter(
            centro_medico=centro_medico,
            fecha=hoy,
            estado="ABIERTA",
        )
        .order_by("turno")
    )

    # ======================================================
    # SIN CAJAS ABIERTAS
    # ======================================================

    if not cajas_abiertas:
        messages.error(
            request,
            f"No existe una caja abierta hoy en "
            f"{centro_medico.nombre}. "
            f"Debe abrir una caja antes de registrar "
            f"el ingreso."
        )
        return redirect(
            "obrasocial:ingresos_consultorio_os"
        )

    # ======================================================
    # UNA SOLA CAJA ABIERTA
    # ======================================================

    if len(cajas_abiertas) == 1:
        caja = cajas_abiertas[0]

    # ======================================================
    # DOS CAJAS ABIERTAS
    # ======================================================

    else:
        caja_id = request.POST.get("caja_id")

        if not caja_id:
            messages.error(
                request,
                "Hay dos cajas abiertas para hoy. "
                "Debe seleccionar la caja de mañana "
                "o tarde antes de registrar el ingreso."
            )
            return redirect(
                "obrasocial:ingresos_consultorio_os"
            )

        caja = next(
            (
                c for c in cajas_abiertas
                if str(c.pk) == str(caja_id)
            ),
            None
        )

        if caja is None:
            messages.error(
                request,
                "La caja seleccionada no es válida "
                "o ya no se encuentra abierta."
            )
            return redirect(
                "obrasocial:ingresos_consultorio_os"
            )

    # ======================================================
    # PRESTACIONES PENDIENTES DEL MASTER
    # ======================================================

    detalles = list(
        DetalleMasterObraSocial.objects
        .select_for_update()
        .filter(
            master=master,
            detalle_movimiento__movimiento__centro_medico=centro_medico,
            importe_consultorio_reconocido__isnull=False,
            importe_consultorio_reconocido__gt=0,
            consultorio_ingresado_caja=False,
        )
        .select_related(
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
        )
    )

    # ======================================================
    # VALIDAR PENDIENTES
    # ======================================================

    if not detalles:
        messages.warning(
            request,
            f"El Master #{master.id} no tiene importes "
            f"del consultorio pendientes de ingresar "
            f"para {centro_medico.nombre}. "
            f"Es posible que ya hayan sido ingresados."
        )
        return redirect(
            "obrasocial:ingresos_consultorio_os"
        )

    # ======================================================
    # CALCULAR TOTAL EN EL SERVIDOR
    # ======================================================

    total_consultorio = sum(
        (
            detalle.importe_consultorio_reconocido
            or Decimal("0.00")
            for detalle in detalles
        ),
        Decimal("0.00")
    )

    if total_consultorio <= Decimal("0.00"):
        messages.error(
            request,
            "El importe a ingresar debe ser mayor a cero."
        )
        return redirect(
            "obrasocial:ingresos_consultorio_os"
        )

    # ======================================================
    # CREAR MOVIMIENTO DE CAJA
    # ======================================================

    movimiento = MovimientoCaja.objects.create(
        caja=caja,
        centro_medico=centro_medico,
        tipo="INGRESO",
        importe=total_consultorio,
        concepto=(
            f"Ingreso Consultorio Obra Social - "
            f"{master.obra_social.nombre} - "
            f"Master #{master.id}"
        ),
        observacion=(
            f"Ingreso correspondiente al consultorio por "
            f"Master #{master.id} - "
            f"{master.obra_social.nombre} - "
            f"Período {master.mes:02d}/{master.anio}. "
            f"Sede: {centro_medico.nombre}. "
            f"Turno: {caja.get_turno_display()}. "
            f"Prestaciones: {len(detalles)}. "
            f"Medio de pago: {medio_pago.nombre}."
        ),
        estado="ACTIVO",
        creado_por=request.user,
    )

    # ======================================================
    # REGISTRAR MEDIO DE PAGO
    # ======================================================

    DetalleMedioPago.objects.create(
        movimiento=movimiento,
        medio_pago=medio_pago,
        importe=total_consultorio,
        observacion=(
            f"Cobro Obra Social - "
            f"{master.obra_social.nombre} - "
            f"Master #{master.id}"
        ),
        orden=1,
    )

    # ======================================================
    # MARCAR PRESTACIONES COMO INGRESADAS
    # ======================================================

    ahora = timezone.now()

    DetalleMasterObraSocial.objects.filter(
        pk__in=[
            detalle.pk
            for detalle in detalles
        ]
    ).update(
        consultorio_ingresado_caja=True,
        fecha_ingreso_consultorio=ahora,
        movimiento_ingreso_consultorio=movimiento,
    )

    # ======================================================
    # MENSAJE DE ÉXITO
    # ======================================================

    messages.success(
        request,
        (
            f"Ingreso registrado correctamente. "
            f"Master #{master.id} - "
            f"{master.obra_social.nombre} - "
            f"{centro_medico.nombre} - "
            f"Turno {caja.get_turno_display()} - "
            f"{len(detalles)} prestación/es - "
            f"${total_consultorio:,.2f} - "
            f"{medio_pago.nombre}."
        )
    )

    return redirect(
        "obrasocial:ingresos_consultorio_os"
    )





@login_required
def historial_ingresos_consultorio_os(request):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if not usuario_autorizado_obras_sociales(request.user):
        raise PermissionDenied(
            "No tiene permisos para acceder al historial "
            "de ingresos del consultorio."
        )

    # ======================================================
    # CENTRO MÉDICO ACTUAL
    # ======================================================

    centro_id = request.session.get("centro_id")

    if not centro_id:
        messages.warning(
            request,
            "Debe seleccionar una sede."
        )
        return redirect("home")

    centro_medico = get_object_or_404(
        CentroMedico,
        pk=centro_id
    )

    # ======================================================
    # FILTROS MES / AÑO
    # ======================================================

    hoy = timezone.localdate()

    try:
        mes = int(
            request.GET.get("mes", hoy.month)
        )
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(
            request.GET.get("anio", hoy.year)
        )
    except (TypeError, ValueError):
        anio = hoy.year

    if mes < 1 or mes > 12:
        mes = hoy.month

    if anio < 2000 or anio > 2100:
        anio = hoy.year

    # ======================================================
    # HISTORIAL
    #
    # Se filtra por la fecha REAL en que el dinero
    # fue ingresado a Caja.
    # ======================================================

    historial = (
        DetalleMasterObraSocial.objects
        .filter(
            consultorio_ingresado_caja=True,

            movimiento_ingreso_consultorio__isnull=False,

            detalle_movimiento__movimiento__centro_medico=centro_medico,

            fecha_ingreso_consultorio__year=anio,
            fecha_ingreso_consultorio__month=mes,
        )
        .select_related(
            "master",
            "master__obra_social",

            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_movimiento__prestacion_obra_social",

            "movimiento_ingreso_consultorio",
            "movimiento_ingreso_consultorio__creado_por",
        )
        .prefetch_related(
            "movimiento_ingreso_consultorio__detalles_medios_pago",
            "movimiento_ingreso_consultorio__detalles_medios_pago__medio_pago",
        )
        .order_by(
            "-fecha_ingreso_consultorio",
            "-master_id",
            "-id",
        )
    )

    # ======================================================
    # AGRUPAR POR MOVIMIENTO DE CAJA
    # ======================================================

    historial_dict = {}

    for item in historial:

        movimiento = item.movimiento_ingreso_consultorio

        if not movimiento:
            continue

        movimiento_id = movimiento.id

        if movimiento_id not in historial_dict:

            detalles_medios = list(
                movimiento.detalles_medios_pago.all()
            )

            medios = []

            for detalle_medio in detalles_medios:

                medios.append({
                    "nombre": detalle_medio.medio_pago.nombre,
                    "importe": detalle_medio.importe,
                })

            historial_dict[movimiento_id] = {

                "movimiento": movimiento,

                "master": item.master,

                "obra_social": item.master.obra_social,

                "fecha_ingreso": item.fecha_ingreso_consultorio,

                "prestaciones": [],

                "cantidad": 0,

                "total_consultorio": Decimal("0.00"),

                "medios_pago": medios,
            }

        historial_dict[movimiento_id][
            "prestaciones"
        ].append(item)

        historial_dict[movimiento_id][
            "cantidad"
        ] += 1

        historial_dict[movimiento_id][
            "total_consultorio"
        ] += (
            item.importe_consultorio_reconocido
            or Decimal("0.00")
        )

    historial_ingresos = list(
        historial_dict.values()
    )

    # ======================================================
    # TOTALES
    # ======================================================

    total_ingresado = sum(
        (
            grupo["total_consultorio"]
            for grupo in historial_ingresos
        ),
        Decimal("0.00")
    )

    cantidad_ingresos = len(
        historial_ingresos
    )

    cantidad_prestaciones = sum(
        grupo["cantidad"]
        for grupo in historial_ingresos
    )

    masters_ids = {
        grupo["master"].id
        for grupo in historial_ingresos
    }

    cantidad_masters = len(
        masters_ids
    )

    # ======================================================
    # RESUMEN MEDIOS DE PAGO
    # ======================================================

    resumen_medios_dict = {}

    for grupo in historial_ingresos:

        for medio in grupo["medios_pago"]:

            nombre = medio["nombre"]

            importe = (
                medio["importe"]
                or Decimal("0.00")
            )

            if nombre not in resumen_medios_dict:
                resumen_medios_dict[nombre] = Decimal("0.00")

            resumen_medios_dict[nombre] += importe

    resumen_medios_pago = [
        {
            "nombre": nombre,
            "importe": importe,
        }
        for nombre, importe
        in sorted(resumen_medios_dict.items())
    ]

    # ======================================================
    # MESES
    # ======================================================

    meses = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    # ======================================================
    # AÑOS
    # ======================================================

    anios_disponibles = list(
        range(
            hoy.year,
            max(2024, hoy.year - 5) - 1,
            -1
        )
    )

    if anio not in anios_disponibles:

        anios_disponibles.append(anio)

        anios_disponibles.sort(
            reverse=True
        )

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "obrasocial/consultorio/historial_ingresos.html",
        {
            "centro_medico": centro_medico,

            "historial_ingresos": historial_ingresos,

            "total_ingresado": total_ingresado,

            "cantidad_ingresos": cantidad_ingresos,

            "cantidad_masters": cantidad_masters,

            "cantidad_prestaciones": cantidad_prestaciones,

            "resumen_medios_pago": resumen_medios_pago,

            "mes": mes,
            "anio": anio,

            "meses": meses,

            "anios_disponibles": anios_disponibles,
        }
    )