from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404,redirect
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from decimal import Decimal



from ..models import (
    ObraSocial,
    DetalleMasterObraSocial,
    MasterObraSocial,
)


@login_required
def prestaciones_observadas(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    estado = request.GET.get("estado", "")
    periodo = request.GET.get("periodo", "")

    detalles = (
        DetalleMasterObraSocial.objects
        .filter(
            master__obra_social=obra_social,
            estado__in=[
                "DEBITO_PARCIAL",
                "RECHAZADO",
            ],
        )
        .select_related(
            "master",
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_origen",
            "resuelto_por",
        )
        .order_by(
            "-master__anio",
            "-master__mes",
            "detalle_movimiento__fecha_prestacion",
        )
    )

    if estado in [
        "DEBITO_PARCIAL",
        "RECHAZADO",
    ]:
        detalles = detalles.filter(
            estado=estado
        )

    if periodo:
        try:
            anio, mes = periodo.split("-")

            detalles = detalles.filter(
                master__anio=int(anio),
                master__mes=int(mes),
            )

        except (ValueError, TypeError):
            pass

    total_rechazados = detalles.filter(
        estado="RECHAZADO"
    ).count()

    total_debitos = detalles.filter(
        estado="DEBITO_PARCIAL"
    ).count()

    total_refacturar = detalles.filter(
        estado_refacturacion="PENDIENTE"
    ).count()

    total_cancelados = (
        DetalleMasterObraSocial.objects
        .filter(
            master__obra_social=obra_social,
            estado_refacturacion="CANCELADA",
        )
        .count()
    )

    return render(
        request,
            "obrasocial/master/prestaciones_observadas.html",
        {
            "obra_social": obra_social,
            "detalles": detalles,
            "estado_filtro": estado,
            "periodo_filtro": periodo,
            "total_rechazados": total_rechazados,
            "total_debitos": total_debitos,
            "total_refacturar": total_refacturar,
            "total_cancelados": total_cancelados,
        }
    )
    
@login_required
def gestionar_prestacion_observada(request, detalle_id):

    detalle = get_object_or_404(
        DetalleMasterObraSocial.objects.select_related(
            "master",
            "master__obra_social",
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "detalle_origen",
            "resuelto_por",
        ),
        pk=detalle_id,
    )

    # Solo permitimos gestionar prestaciones observadas
    if detalle.estado not in [
        "DEBITO_PARCIAL",
        "RECHAZADO",
    ]:
        messages.warning(
            request,
            "Esta prestación no tiene un débito ni un rechazo pendiente de gestión."
        )

        return redirect(
            "obrasocial:prestaciones_observadas",
            obra_social_id=detalle.master.obra_social_id
        )

    return render(
        request,
        "obrasocial/master/gestionar_prestacion_observada.html",
        {
            "detalle": detalle,
            "obra_social": detalle.master.obra_social,
            "master": detalle.master,
        }
    )
    

@login_required
@transaction.atomic
def marcar_para_refacturar(request, detalle_id):

    # ======================================================
    # SOLO POST
    # ======================================================

    if request.method != "POST":
        messages.warning(
            request,
            "La acción de refacturación debe realizarse desde el formulario."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle_id
        )

    # ======================================================
    # BLOQUEAR REGISTRO
    # ======================================================

    detalle = get_object_or_404(
        DetalleMasterObraSocial.objects
        .select_for_update()
        .select_related(
            "master",
            "master__obra_social",
            "detalle_movimiento",
            "detalle_origen",
        ),
        pk=detalle_id,
    )

    # ======================================================
    # VALIDAR ESTADO DE AUDITORÍA
    # ======================================================

    if detalle.estado not in [
        "DEBITO_PARCIAL",
        "RECHAZADO",
    ]:

        messages.warning(
            request,
            "Esta prestación no posee un débito o rechazo "
            "que pueda enviarse a refacturación."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    # ======================================================
    # EVITAR PRESTACIONES YA RESUELTAS
    # ======================================================

    if detalle.estado_refacturacion in [
        "PRESENTADA",
        "ACEPTADA",
        "CANCELADA",
    ]:

        messages.warning(
            request,
            "Esta prestación ya fue gestionada y no puede "
            "marcarse nuevamente para refacturación."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    # ======================================================
    # CALCULAR IMPORTE A REFACTURAR
    # ======================================================

    importe_presentado = (
        detalle.importe_presentado
        or Decimal("0.00")
    )

    importe_reconocido = (
        detalle.importe_reconocido
        or Decimal("0.00")
    )

    importe_debitado = (
        detalle.importe_debitado
        or Decimal("0.00")
    )

    # ------------------------------------------------------
    # DÉBITO PARCIAL
    # ------------------------------------------------------
    #
    # Solo se vuelve a presentar la diferencia debitada.
    #
    # Ejemplo:
    #
    # presentado   275.000
    # reconocido   250.000
    # débito        25.000
    #
    # refacturar    25.000
    # ------------------------------------------------------

    if detalle.estado == "DEBITO_PARCIAL":

        importe_refacturar = importe_debitado

        # Compatibilidad por si algún registro histórico
        # no tuviera correctamente guardado el débito.

        if importe_refacturar <= Decimal("0.00"):

            importe_refacturar = (
                importe_presentado
                - importe_reconocido
            )

    # ------------------------------------------------------
    # RECHAZO TOTAL
    # ------------------------------------------------------
    #
    # Se vuelve a presentar todo el importe rechazado.
    # ------------------------------------------------------

    else:

        importe_refacturar = importe_debitado

        if importe_refacturar <= Decimal("0.00"):
            importe_refacturar = importe_presentado

    # ======================================================
    # VALIDAR IMPORTE
    # ======================================================

    if importe_refacturar <= Decimal("0.00"):

        messages.error(
            request,
            "No existe un importe válido para refacturar."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    # ======================================================
    # MARCAR PARA REFACTURACIÓN
    # ======================================================
    #
    # IMPORTANTE:
    #
    # Acá NO:
    #
    # - creamos MovimientoCaja
    # - cobramos nuevamente coseguro
    # - cobramos nuevamente copago
    # - modificamos la prestación original
    # - creamos todavía otro Master
    #
    # Solamente dejamos esta observación preparada para
    # entrar posteriormente al Master de refacturación.
    # ======================================================

    detalle.refacturable = True
    detalle.estado_refacturacion = "PENDIENTE"

    detalle.fecha_refacturacion = None

    detalle.fecha_ultima_gestion = timezone.now()

    detalle.resuelto_por = request.user

    # Guardamos una observación legible para auditoría.
    # El importe real continúa siendo importe_debitado,
    # que es un Decimal y sirve para los cálculos.

    detalle.observacion_refacturacion = (
        f"Marcada para refacturación por "
        f"{request.user.get_username()}. "
        f"Importe pendiente de refacturar: "
        f"${importe_refacturar:.2f}"
    )

    detalle.save(
        update_fields=[
            "refacturable",
            "estado_refacturacion",
            "fecha_refacturacion",
            "fecha_ultima_gestion",
            "resuelto_por",
            "observacion_refacturacion",
        ]
    )

    # ======================================================
    # MENSAJE
    # ======================================================

    messages.success(
        request,
        (
            "La prestación fue enviada a la bandeja de "
            "refacturación. "
            f"Importe a refacturar: ${importe_refacturar:,.2f}"
        )
    )

    # ======================================================
    # VOLVER
    # ======================================================

    return redirect(
        "obrasocial:gestionar_prestacion_observada",
        detalle_id=detalle.id
    )

@login_required
def pendientes_refacturacion(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    detalles = (
        DetalleMasterObraSocial.objects
        .filter(
            master__obra_social=obra_social,
            refacturable=True,
            estado_refacturacion="PENDIENTE",
        )
        .select_related(
            "master",
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",
            "resuelto_por",
        )
        .order_by(
            "master__anio",
            "master__mes",
            "detalle_movimiento__fecha_prestacion",
            "id",
        )
    )

    # ======================================================
    # CALCULAR IMPORTE PENDIENTE DE REFACTURACIÓN
    # ======================================================

    total_refacturar = Decimal("0.00")

    for detalle in detalles:

        if detalle.estado == "DEBITO_PARCIAL":

            importe_refacturar = (
                detalle.importe_debitado
                or Decimal("0.00")
            )

            # Compatibilidad con registros históricos
            if importe_refacturar <= Decimal("0.00"):

                importe_refacturar = (
                    (detalle.importe_presentado or Decimal("0.00"))
                    -
                    (detalle.importe_reconocido or Decimal("0.00"))
                )

        elif detalle.estado == "RECHAZADO":

            importe_refacturar = (
                detalle.importe_debitado
                or Decimal("0.00")
            )

            if importe_refacturar <= Decimal("0.00"):

                importe_refacturar = (
                    detalle.importe_presentado
                    or Decimal("0.00")
                )

        else:

            importe_refacturar = Decimal("0.00")

        if importe_refacturar < Decimal("0.00"):
            importe_refacturar = Decimal("0.00")

        detalle.importe_refacturar_calculado = importe_refacturar

        total_refacturar += importe_refacturar

    return render(
        request,
        "obrasocial/master/pendientes_refacturacion.html",
        {
            "obra_social": obra_social,
            "detalles": detalles,
            "total_refacturar": total_refacturar,
        }
    )

@login_required
@transaction.atomic
def aceptar_importe_reconocido(request, detalle_id):

    # ======================================================
    # SOLO POST
    # ======================================================

    if request.method != "POST":
        messages.error(
            request,
            "La operación solicitada no es válida."
        )
        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle_id
        )
       

    # ======================================================
    # BLOQUEAMOS EL REGISTRO DURANTE LA OPERACIÓN
    # ======================================================

    detalle = get_object_or_404(
        DetalleMasterObraSocial.objects
        .select_for_update()
        .select_related(
            "master",
            "master__obra_social",
            "detalle_movimiento",
        ),
        pk=detalle_id,
    )
    # ======================================================
    # EVITAR PROCESAR DOS VECES LA MISMA PRESTACIÓN
    # ======================================================

    if detalle.estado_refacturacion == "CANCELADA":

        messages.warning(
            request,
            "Esta prestación ya fue resuelta anteriormente."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )
    # ======================================================
    # VALIDACIONES
    # ======================================================

    if detalle.estado != "DEBITO_PARCIAL":

        messages.error(
            request,
            "Esta prestación no corresponde a un débito parcial."
        )

        return redirect(
        "obrasocial:gestionar_prestacion_observada",
        detalle_id=detalle_id
    )

    if detalle.importe_reconocido is None:

        messages.error(
            request,
            "La prestación no tiene un importe reconocido."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    if detalle.importe_reconocido < 0:

        messages.error(
            request,
            "El importe reconocido no puede ser negativo."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    if detalle.importe_reconocido > detalle.importe_presentado:

        messages.error(
            request,
            "El importe reconocido no puede superar el importe presentado."
        )

        return redirect(
            "obrasocial:gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    # ======================================================
    # RECALCULAMOS EL DÉBITO
    # ======================================================

    importe_debitado = (
        detalle.importe_presentado
        - detalle.importe_reconocido
    )

    # ======================================================
    # CERRAMOS LA REFACTURACIÓN
    #
    # Significa:
    # "Acepto lo que pagó/reconoció la OS y no voy
    # a reclamar nuevamente la diferencia."
    # ======================================================

    detalle.importe_debitado = importe_debitado

    detalle.refacturable = False

    detalle.estado_refacturacion = "CANCELADA"

    detalle.fecha_resolucion = timezone.localdate()

    detalle.fecha_ultima_gestion = timezone.now()

    detalle.resuelto_por = request.user

    # Conservamos estado DEBITO_PARCIAL porque es el
    # resultado histórico de la auditoría.
    detalle.save(
        update_fields=[
            "importe_debitado",
            "refacturable",
            "estado_refacturacion",
            "fecha_resolucion",
            "fecha_ultima_gestion",
            "resuelto_por",
        ]
    )

    # ======================================================
    # MENSAJE
    # ======================================================

    messages.success(
        request,
        (
            "Importe reconocido aceptado correctamente. "
            f"Reconocido: ${detalle.importe_reconocido:,.2f} - "
            f"Débito definitivo: ${detalle.importe_debitado:,.2f}."
        )
    )

    return redirect(
        "obrasocial:prestaciones_observadas",
        obra_social_id=detalle.master.obra_social_id
    ) 
    
@login_required
@transaction.atomic
def generar_master_refacturacion(request, obra_social_id):

    # ======================================================
    # ACCESO
    # ======================================================

    if request.user.username.lower() != "cintia":
        raise PermissionDenied(
            "No tiene permisos para generar Masters de refacturación."
        )

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id,
        es_particular=False,
    )

    # ======================================================
    # SOLO POST
    # ======================================================

    if request.method != "POST":

        messages.warning(
            request,
            "Debe seleccionar las prestaciones desde "
            "la bandeja de refacturación."
        )

        return redirect(
            "obrasocial:pendientes_refacturacion",
            obra_social_id=obra_social.id,
        )

    # ======================================================
    # DETALLES SELECCIONADOS
    # ======================================================

    ids_seleccionados = request.POST.getlist("detalles")

    if not ids_seleccionados:

        messages.warning(
            request,
            "Debe seleccionar al menos una prestación."
        )

        return redirect(
            "obrasocial:pendientes_refacturacion",
            obra_social_id=obra_social.id,
        )

    # ======================================================
    # BLOQUEAR ORIGINALES
    # ======================================================

    detalles_origen = list(
        DetalleMasterObraSocial.objects
        .select_for_update()
        .select_related(
            "master",
            "master__obra_social",
            "detalle_movimiento",
        )
        .filter(
            id__in=ids_seleccionados,
            master__obra_social=obra_social,
            refacturable=True,
            estado_refacturacion="PENDIENTE",
        )
        .order_by("id")
    )

    # ======================================================
    # SEGURIDAD
    # ======================================================

    if len(detalles_origen) != len(set(ids_seleccionados)):

        messages.error(
            request,
            "Una o más prestaciones seleccionadas ya no están "
            "disponibles para refacturación."
        )

        return redirect(
            "obrasocial:pendientes_refacturacion",
            obra_social_id=obra_social.id,
        )

    # ======================================================
    # CALCULAR IMPORTES
    # ======================================================

    detalles_preparados = []

    total_refacturacion = Decimal("0.00")

    for origen in detalles_origen:

        presentado = (
            origen.importe_presentado
            or Decimal("0.00")
        )

        reconocido = (
            origen.importe_reconocido
            or Decimal("0.00")
        )

        debitado = (
            origen.importe_debitado
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # DÉBITO PARCIAL
        # --------------------------------------------------

        if origen.estado == "DEBITO_PARCIAL":

            importe_refacturar = debitado

            if importe_refacturar <= Decimal("0.00"):

                importe_refacturar = (
                    presentado - reconocido
                )

        # --------------------------------------------------
        # RECHAZO TOTAL
        # --------------------------------------------------

        elif origen.estado == "RECHAZADO":

            importe_refacturar = debitado

            if importe_refacturar <= Decimal("0.00"):
                importe_refacturar = presentado

        else:

            messages.error(
                request,
                (
                    f"El detalle #{origen.id} no corresponde "
                    "a un débito o rechazo."
                )
            )

            return redirect(
                "obrasocial:pendientes_refacturacion",
                obra_social_id=obra_social.id,
            )

        if importe_refacturar <= Decimal("0.00"):

            messages.error(
                request,
                (
                    f"El detalle #{origen.id} no posee "
                    "importe pendiente para refacturar."
                )
            )

            return redirect(
                "obrasocial:pendientes_refacturacion",
                obra_social_id=obra_social.id,
            )

        detalles_preparados.append(
            (
                origen,
                importe_refacturar,
            )
        )

        total_refacturacion += importe_refacturar

    # ======================================================
    # PERÍODO DEL NUEVO MASTER
    # ======================================================
    #
    # La refacturación pertenece al período actual de
    # presentación, no al período original de la prestación.
    #
    # El período original continúa disponible mediante:
    #
    # nuevo_detalle.detalle_origen.master
    # ======================================================

    hoy = timezone.localdate()

    mes = hoy.month
    anio = hoy.year

    # ======================================================
    # CREAR MASTER
    # ======================================================
    #
    # IMPORTANTE:
    #
    # Acá usamos los campos que ya posee MasterObraSocial.
    #
    # Si tu modelo exige algún otro campo obligatorio,
    # Django nos lo va a indicar en el check/prueba y
    # lo incorporamos.
    # ======================================================

    nuevo_master = MasterObraSocial.objects.create(
        obra_social=obra_social,
        mes=mes,
        anio=anio,
        tipo="REFACTURACION",
        estado="BORRADOR",
        creado_por=request.user,
        observaciones=(
            "Master generado automáticamente desde "
            "Gestión de Débitos y Rechazos."
        ),
    )

    # ======================================================
    # CREAR DETALLES DE REFACTURACIÓN
    # ======================================================

    cantidad_creada = 0

    for origen, importe_refacturar in detalles_preparados:

        # --------------------------------------------------
        # NUEVO DETALLE
        # --------------------------------------------------
        #
        # Utilizamos el MISMO DetalleMovimientoCaja.
        #
        # NO creamos otro movimiento.
        # --------------------------------------------------

        DetalleMasterObraSocial.objects.create(

            master=nuevo_master,

            detalle_movimiento=(
                origen.detalle_movimiento
            ),

            # ----------------------------------------------
            # NUEVA PRESENTACIÓN
            # ----------------------------------------------

            estado="PENDIENTE",

            importe_presentado=(
                importe_refacturar
            ),

            importe_reconocido=None,

            importe_debitado=Decimal("0.00"),

            # ----------------------------------------------
            # TODAVÍA NO SABEMOS SI ESTA NUEVA
            # PRESENTACIÓN SERÁ DEBITADA
            # ----------------------------------------------

            motivo_debito="",

            motivo_observacion="",

            detalle_observacion="",

            # ----------------------------------------------
            # ESTA ES UNA REFACTURACIÓN
            # ----------------------------------------------

            detalle_origen=origen,

            refacturable=False,

            estado_refacturacion="NO_APLICA",

            fecha_refacturacion=None,

            observacion_refacturacion=(
                f"Refacturación del detalle "
                f"original #{origen.id}."
            ),

            # ----------------------------------------------
            # HONORARIOS
            # ----------------------------------------------
            #
            # Todavía no existe honorario porque la OS
            # todavía no reconoció esta presentación.
            # ----------------------------------------------

            honorario_medico_reconocido=None,

            honorario_medico_liquidado=False,

            fecha_liquidacion_honorario=None,
        )

        # ==================================================
        # ACTUALIZAR ORIGINAL
        # ==================================================

        origen.estado_refacturacion = "PRESENTADA"

        origen.fecha_refacturacion = hoy

        origen.fecha_ultima_gestion = timezone.now()

        origen.resuelto_por = request.user

        origen.observacion_refacturacion = (
            f"Refacturación incorporada al Master "
            f"#{nuevo_master.id} por "
            f"{request.user.get_username()}. "
            f"Importe refacturado: "
            f"${importe_refacturar:.2f}"
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

        cantidad_creada += 1

    # ======================================================
    # MENSAJE
    # ======================================================

    messages.success(
        request,
        (
            f"Se generó el Master de refacturación "
            f"#{nuevo_master.id} con "
            f"{cantidad_creada} prestación/es por "
            f"${total_refacturacion:,.2f}."
        )
    )

    # ======================================================
    # IR AL MASTER
    # ======================================================

    return redirect(
        "obrasocial:master_obra_social_detalle",
        obra_social_id=obra_social.id,
        master_id=nuevo_master.id,
    )