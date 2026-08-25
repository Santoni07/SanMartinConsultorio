from django.contrib import messages
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
from caja.models import DetalleMovimientoCaja
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
    
    
@login_required
def master_obra_social_lista(request, obra_social_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if request.user.username.lower() != "cintia":
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
            "-anio",
            "-mes"
        )
    )

    return render(
        request,
        "obrasocial/master/lista.html",
        {
            "obra_social": obra_social,
            "masters": masters,
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

    if request.user.username.lower() != "cintia":
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

        detalles_ids = request.POST.getlist("prestaciones")

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
        # VERIFICAR QUE NO EXISTA EL MASTER
        # ==================================================

        if MasterObraSocial.objects.filter(
            obra_social=obra_social,
            mes=mes,
            anio=anio
        ).exists():

            messages.error(
                request,
                "Ya existe un Master para esta Obra Social "
                "en el período seleccionado."
            )

            return redirect(
                "obrasocial:master_obra_social_lista",
                obra_social_id=obra_social.id
            )

        # ==================================================
        # TRANSACCIÓN
        # ==================================================

        try:

            with transaction.atomic():

                # ==========================================
                # VOLVER A CONSULTAR LAS PRESTACIONES
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

                        detalle_master_obra_social__isnull=True,
                    )
                )

                # ==========================================
                # VALIDAR QUE TODOS SIGAN DISPONIBLES
                # ==========================================

                if detalles.count() != len(set(detalles_ids)):

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
                # CREAR DETALLES
                # ==========================================

                DetalleMasterObraSocial.objects.bulk_create(

                    [
                        DetalleMasterObraSocial(
                            master=master,
                            detalle_movimiento=detalle,
                            estado="PENDIENTE"
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

                    detalle_master_obra_social__isnull=True,
                )
                .select_related(
                    "movimiento",
                    "movimiento__centro_medico",
                    "movimiento__paciente",
                    "movimiento__turno",
                    "prestacion_obra_social",
                    "prestacion_obra_social__plan",
                )
                .order_by(
                    "movimiento__centro_medico__nombre",
                    "fecha_prestacion",
                    "id"
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

    if request.user.username.lower() != "cintia":
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
    # IMPORTANTE:
    # comprobamos también que pertenezca a esta OS
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

    for item in detalles:

        detalle = item.detalle_movimiento
        importe = detalle.importe or Decimal("0.00")

        total_master += importe

        centro = detalle.movimiento.centro_medico

        # Usamos el nombre para presentación.
        # Más adelante, si queremos, podemos trabajar por ID.
        nombre_centro = centro.nombre.lower()

        if "agua de oro" in nombre_centro:

            total_agua_de_oro += importe
            cantidad_agua_de_oro += 1

        else:

            total_casa_central += importe
            cantidad_casa_central += 1

    # ======================================================
    # CONTEXTO
    # ======================================================

    return render(
        request,
        "obrasocial/master/detalle.html",
        {
            "obra_social": obra_social,
            "master": master,
            "detalles": detalles,

            "total_master": total_master,

            "total_casa_central": total_casa_central,
            "total_agua_de_oro": total_agua_de_oro,

            "cantidad_casa_central": cantidad_casa_central,
            "cantidad_agua_de_oro": cantidad_agua_de_oro,
        }
    )
    
@login_required
def master_obra_social_presentar(request, obra_social_id, master_id):

    # ======================================================
    # ACCESO EXCLUSIVO CINTIA
    # ======================================================

    if request.user.username.lower() != "cintia":
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
            request.POST.get("numero_presentacion", "")
            .strip()
        )

        numero_factura = (
            request.POST.get("numero_factura", "")
            .strip()
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

            # ==============================================
            # ACTUALIZAR MASTER
            # ==============================================

            master.fecha_presentacion = fecha_presentacion

            master.numero_presentacion = numero_presentacion

            master.numero_factura = numero_factura

            master.estado = "PRESENTADO"

            master.save(
                update_fields=[
                    "fecha_presentacion",
                    "numero_presentacion",
                    "numero_factura",
                    "estado",
                    "fecha_modificacion",
                ]
            )

            messages.success(
                request,
                "El Master fue marcado como PRESENTADO correctamente."
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

    if request.user.username.lower() != "cintia":
        raise PermissionDenied(
            "No tiene permisos para registrar pagos de Masters."
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
            "Solamente se puede registrar el pago "
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
    # POST
    # ======================================================

    if request.method == "POST":

        fecha_cobro = request.POST.get("fecha_cobro")

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
                # RECORRER PRESTACIONES
                # ==========================================

                for item in detalles:

                    estado = request.POST.get(
                        f"estado_{item.id}"
                    )

                    importe_reconocido = request.POST.get(
                        f"importe_{item.id}",
                        ""
                    )

                    # ======================================
                    # VALIDAR ESTADO
                    # ======================================

                    if estado not in [
                        "PAGADO",
                        "DEBITADO",
                        "RECHAZADO"
                    ]:

                        raise ValueError(
                            "Debe indicar el resultado de "
                            "todas las prestaciones."
                        )

                    # ======================================
                    # IMPORTE RECONOCIDO
                    # ======================================

                    if importe_reconocido:

                        importe_reconocido = (
                            importe_reconocido
                            .replace(".", "")
                            .replace(",", ".")
                        )

                        importe_reconocido = Decimal(
                            importe_reconocido
                        )

                    else:

                        importe_reconocido = Decimal("0.00")

                    if importe_reconocido < 0:

                        raise ValueError(
                            "El importe reconocido no puede "
                            "ser negativo."
                        )

                    # ======================================
                    # ACTUALIZAR DETALLE MASTER
                    # ======================================

                    item.estado = estado

                    item.importe_reconocido = (
                        importe_reconocido
                    )

                    item.fecha_resolucion = fecha_cobro

                    item.save(
                        update_fields=[
                            "estado",
                            "importe_reconocido",
                            "fecha_resolucion",
                        ]
                    )

                    # ======================================
                    # DETALLE MOVIMIENTO CAJA
                    # ======================================

                    detalle = item.detalle_movimiento

                    if estado == "PAGADO":

                        detalle.obra_social_cobrada = True

                        detalle.fecha_cobro_obra_social = (
                            fecha_cobro
                        )

                    else:

                        detalle.obra_social_cobrada = False

                        detalle.fecha_cobro_obra_social = None

                    detalle.save(
                        update_fields=[
                            "obra_social_cobrada",
                            "fecha_cobro_obra_social",
                        ]
                    )

                # ==========================================
                # MASTER COBRADO / RESUELTO
                # ==========================================

                master_bloqueado.estado = "COBRADO"
                master_bloqueado.fecha_cobro = fecha_cobro

                master_bloqueado.save(
                    update_fields=[
                        "estado",
                        "fecha_cobro",
                        "fecha_modificacion",
                    ]
                )

        except (ValueError, InvalidOperation) as e:

            messages.error(
                request,
                str(e)
            )

            return redirect(
                "obrasocial:master_obra_social_registrar_pago",
                obra_social_id=obra_social.id,
                master_id=master.id
            )

        messages.success(
            request,
            "El pago del Master fue registrado correctamente."
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
            "hoy": date.today(),
        }
    )