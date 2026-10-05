from decimal import Decimal
import json
from obrasocial.models import ObraSocial
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.urls import reverse
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from obrasocial.models import (
    DetalleMasterObraSocial
)
from django.utils import timezone
from django.db.models import Count, Case, When, F, IntegerField
from caja.models import (
    MovimientoCaja,
    DetalleMovimientoCaja,
    DetalleMedioPago,
    MedioPago,
)
from caja.views import obtener_caja_abierta

from core.utils import (
    obtener_centro_activo,
    mostrar_error,
    mostrar_exito,
)

from medicos.models import Medico

from honorarios.models import (
    LiquidacionMedica,
    DetalleLiquidacionMedica,
    PagoLiquidacionMedica,
)

from honorarios.forms import (
    PagoLiquidacionForm,
    FiltroHistorialLiquidacionesForm,
)


@login_required
def honorarios_medicos(request):

    medico_id = request.GET.get("medico")
    centro_medico = obtener_centro_activo(request)

    medicos = Medico.objects.all().order_by(
        "apellido",
        "nombre"
    )

    # ==========================================
    # QUERYSETS VACÍOS
    # ==========================================

    particulares = DetalleMovimientoCaja.objects.none()
    coseguros = DetalleMovimientoCaja.objects.none()
    copagos = DetalleMovimientoCaja.objects.none()

    obras_sociales_pendientes = DetalleMovimientoCaja.objects.none()
    obras_sociales_cobradas = DetalleMovimientoCaja.objects.none()

    # ==========================================
    # RESUMEN INICIAL
    # ==========================================

    resumen = {

        "total_particulares":
            Decimal("0.00"),

        "total_coseguros":
            Decimal("0.00"),

        "total_copagos":
            Decimal("0.00"),

        # OS todavía no cobradas
        "total_os_pendiente":
            Decimal("0.00"),

        "total_honorarios_os_pendiente":
            Decimal("0.00"),

        # OS ya cobradas
        "total_os_cobrado":
            Decimal("0.00"),

        "total_honorarios_os_disponible":
            Decimal("0.00"),

        # Disponible directo
        "total_disponible_directo":
            Decimal("0.00"),

        # Total disponible para liquidar
        "total_disponible":
            Decimal("0.00"),
    }

    # ==========================================
    # SI SE SELECCIONÓ MÉDICO
    # ==========================================

    if medico_id:

        # ==========================================
        # BASE COMÚN
        # ==========================================

        base = (
            DetalleMovimientoCaja.objects
            .filter(
                movimiento__turno__medico_id=medico_id,
                movimiento__centro_medico=centro_medico,
                movimiento__tipo="INGRESO",
                movimiento__estado="ACTIVO",
                estado="PENDIENTE",
            )
            .select_related(
                "movimiento",
                "movimiento__centro_medico",
                "movimiento__paciente",
                "movimiento__turno",
                "movimiento__turno__medico",
                "prestacion_obra_social",
                "prestacion_obra_social__obra_social",
                "prestacion_obra_social__plan",
            )
        )

        # ==========================================
        # PARTICULARES
        # ==========================================

        particulares = base.filter(
            concepto_facturacion__isnull=False,
            prestacion_obra_social__isnull=True,
            liquidacion__isnull=True,
        )

        total_particulares = (
            particulares.aggregate(
                total=Sum("importe_medico")
            )["total"]
            or Decimal("0.00")
        )

        # ==========================================
        # COSEGUROS COBRADOS
        # PENDIENTES DE LIQUIDAR
        # ==========================================

        coseguros = base.filter(
            prestacion_obra_social__isnull=False,
            coseguro_cobrado=True,
            coseguro_liquidado=False,
            importe_coseguro__gt=0,
        )

        total_coseguros = (
            coseguros.aggregate(
                total=Sum("importe_coseguro")
            )["total"]
            or Decimal("0.00")
        )

        # ==========================================
        # COPAGOS COBRADOS
        # PENDIENTES DE LIQUIDAR
        # ==========================================
        #
        # El copago va directamente al médico.
        #
        # NO se descuenta:
        #
        # - del importe que debe pagar la OS
        # - del honorario correspondiente a la OS
        #
        # Tiene su propio circuito de liquidación.
        # ==========================================

        copagos = base.filter(
            prestacion_obra_social__isnull=False,
            copago_cobrado=True,
            copago_liquidado=False,
            importe_copago__gt=0,
        )

        total_copagos = (
            copagos.aggregate(
                total=Sum("importe_copago")
            )["total"]
            or Decimal("0.00")
        )

        # ==========================================
        # OBRAS SOCIALES PENDIENTES DE COBRO
        # ==========================================
        #
        # Incluye prestaciones todavía no cobradas
        # por la Obra Social.
        #
        # IMPORTANTE:
        #
        # Una prestación RECHAZADA en el Master
        # no debe aparecer como saldo pendiente
        # normal de cobro ni como honorario médico
        # pendiente de OS.
        #
        # Los rechazos se gestionan desde:
        # Débitos / Rechazos.
        # ==========================================

        obras_sociales_pendientes = (
            base
            .filter(
                prestacion_obra_social__isnull=False,
                obra_social_cobrada=False,
                honorario_os_liquidado=False,
            )
            .exclude(
                detalles_master_obra_social__estado="RECHAZADO"
            )
            .distinct()
        )

        total_os_pendiente = Decimal("0.00")
        total_honorarios_os_pendiente = Decimal("0.00")

        # ==========================================
        # CALCULAR PRESTACIONES OS PENDIENTES
        # ==========================================

        for detalle in obras_sociales_pendientes:

            # --------------------------------------
            # SALDO QUE DEBE PAGAR LA OBRA SOCIAL
            # --------------------------------------
            #
            # COSEGURO:
            # se descuenta del importe OS.
            #
            # COPAGO:
            # NO se descuenta.
            # --------------------------------------

            saldo_os = (
                (detalle.importe or Decimal("0.00"))
                -
                (detalle.importe_coseguro or Decimal("0.00"))
            )

            if saldo_os < Decimal("0.00"):
                saldo_os = Decimal("0.00")

            detalle.saldo_os_calculado = saldo_os

            total_os_pendiente += saldo_os

            # --------------------------------------
            # HONORARIO MÉDICO CORRESPONDIENTE
            # A LA PARTE DE LA OBRA SOCIAL
            # --------------------------------------
            #
            # Acá todavía NO usamos el snapshot.
            #
            # Esta prestación todavía está pendiente
            # de cobro y mostramos el honorario
            # originalmente esperado.
            #
            # El coseguro forma parte del honorario
            # original, por eso se descuenta.
            #
            # El copago es adicional y NO se
            # descuenta.
            # --------------------------------------

            honorario_os = (
                (detalle.importe_medico or Decimal("0.00"))
                -
                (detalle.importe_coseguro or Decimal("0.00"))
            )

            if honorario_os < Decimal("0.00"):
                honorario_os = Decimal("0.00")

            detalle.honorario_os_calculado = honorario_os

            total_honorarios_os_pendiente += honorario_os

               # ==========================================
        # OBRAS SOCIALES YA COBRADAS
        # PENDIENTES DE LIQUIDAR AL MÉDICO
        # ==========================================
        #
        # SISTEMA NUEVO:
        #
        # La fuente de verdad es:
        #
        # DetalleMasterObraSocial
        #
        # Cada cobro de Master puede generar un crédito
        # independiente de honorarios.
        #
        # Ejemplo:
        #
        # Master original:
        #     $153.800 -> liquidado
        #
        # Refacturación:
        #     $15.750 -> pendiente
        #
        # Por eso NO debemos filtrar por:
        #
        # detalle_movimiento.honorario_os_liquidado
        #
        # ya que ese booleano pertenece al movimiento
        # completo y no a cada evento de cobro.
        # ==========================================

        detalles_master_cobrados = list(

            DetalleMasterObraSocial.objects

            .filter(

                master__estado="COBRADO",

                detalle_movimiento__movimiento__turno__medico_id=medico_id,

                detalle_movimiento__movimiento__centro_medico=centro_medico,

                detalle_movimiento__movimiento__tipo="INGRESO",

                detalle_movimiento__movimiento__estado="ACTIVO",

                detalle_movimiento__estado="PENDIENTE",

                detalle_movimiento__prestacion_obra_social__isnull=False,

                honorario_medico_liquidado=False,

                honorario_medico_reconocido__isnull=False,

                honorario_medico_reconocido__gt=0,
            )

            .select_related(

                "master",

                "master__obra_social",

                "detalle_movimiento",

                "detalle_movimiento__movimiento",

                "detalle_movimiento__movimiento__centro_medico",

                "detalle_movimiento__movimiento__paciente",

                "detalle_movimiento__movimiento__turno",

                "detalle_movimiento__movimiento__turno__medico",

                "detalle_movimiento__prestacion_obra_social",

                "detalle_movimiento__prestacion_obra_social__obra_social",

                "detalle_movimiento__prestacion_obra_social__plan",

                "detalle_origen",
            )

            .order_by(

                "master__obra_social__nombre",

                "detalle_movimiento__fecha_prestacion",

                "id",
            )
        )

        # ==========================================
        # PREPARAR DATOS PARA EL TEMPLATE ACTUAL
        # ==========================================
        #
        # El template actualmente espera objetos
        # DetalleMovimientoCaja.
        #
        # Para no modificar todavía el HTML,
        # agregamos atributos temporales.
        # ==========================================

        obras_sociales_cobradas = []

        total_os_cobrado = Decimal("0.00")

        total_honorarios_os_disponible = Decimal("0.00")

        for item_master in detalles_master_cobrados:

            detalle = item_master.detalle_movimiento

            # --------------------------------------
            # IMPORTE COBRADO EN ESTE MASTER
            # --------------------------------------

            importe_os = (
                item_master.importe_reconocido
                or Decimal("0.00")
            )

            # --------------------------------------
            # HONORARIO GENERADO POR ESTE MASTER
            # --------------------------------------

            honorario_os = (
                item_master.honorario_medico_reconocido
                or Decimal("0.00")
            )

            # --------------------------------------
            # ATRIBUTOS TEMPORALES PARA TEMPLATE
            # --------------------------------------

            detalle.importe_os_cobrado_calculado = (
                importe_os
            )

            detalle.honorario_os_calculado = (
                honorario_os
            )

            detalle.detalle_master_honorario = (
                item_master
            )

            obras_sociales_cobradas.append(
                detalle
            )

            total_os_cobrado += importe_os

            total_honorarios_os_disponible += (
                honorario_os
            )

        # ==========================================
        # COMPATIBILIDAD HISTÓRICA
        # ==========================================
        #
        # Conservamos prestaciones anteriores al
        # nuevo sistema que todavía puedan tener
        # honorarios pendientes.
        #
        # Excluimos movimientos que ya poseen
        # DetalleMaster con snapshot de honorario,
        # porque esos ya son administrados arriba.
        # ==========================================

        historicos_os_cobrados = (

            base

            .filter(

                prestacion_obra_social__isnull=False,

                obra_social_cobrada=True,

                honorario_os_liquidado=False,
            )

            .exclude(

                detalles_master_obra_social__master__estado="COBRADO",

                detalles_master_obra_social__honorario_medico_reconocido__isnull=False,
            )

            .distinct()
        )

        for detalle in historicos_os_cobrados:

            # --------------------------------------
            # IMPORTE OS HISTÓRICO
            # --------------------------------------

            if detalle.importe_reconocido_obra_social is not None:

                importe_os = (
                    detalle.importe_reconocido_obra_social
                )

            else:

                importe_os = (
                    (detalle.importe or Decimal("0.00"))
                    -
                    (detalle.importe_coseguro or Decimal("0.00"))
                )

                if importe_os < Decimal("0.00"):
                    importe_os = Decimal("0.00")

            # --------------------------------------
            # HONORARIO OS HISTÓRICO
            # --------------------------------------

            if detalle.honorario_reconocido_obra_social is not None:

                honorario_os = (
                    detalle.honorario_reconocido_obra_social
                )

            else:

                honorario_os = (
                    (detalle.importe_medico or Decimal("0.00"))
                    -
                    (detalle.importe_coseguro or Decimal("0.00"))
                )

                if honorario_os < Decimal("0.00"):
                    honorario_os = Decimal("0.00")

            detalle.importe_os_cobrado_calculado = (
                importe_os
            )

            detalle.honorario_os_calculado = (
                honorario_os
            )

            detalle.detalle_master_honorario = None

            obras_sociales_cobradas.append(
                detalle
            )

            total_os_cobrado += importe_os

            total_honorarios_os_disponible += (
                honorario_os
            )
        # ==========================================
        # TOTAL DIRECTO DISPONIBLE
        # ==========================================
        #
        # Dinero que ya está disponible para
        # pagar directamente al médico:
        #
        # - Particulares
        # - Coseguros cobrados
        # - Copagos cobrados
        #
        # Las OS cobradas se muestran por separado.
        # ==========================================

        total_disponible_directo = (
            total_particulares
            + total_coseguros
            + total_copagos
        )

        # ==========================================
        # RESUMEN FINAL
        # ==========================================

        resumen = {

            # --------------------------------------
            # PARTICULAR
            # --------------------------------------

            "total_particulares":
                total_particulares,

            # --------------------------------------
            # COSEGURO
            # --------------------------------------

            "total_coseguros":
                total_coseguros,

            # --------------------------------------
            # COPAGO
            # --------------------------------------

            "total_copagos":
                total_copagos,

            # --------------------------------------
            # OS PENDIENTES DE COBRO
            # --------------------------------------

            "total_os_pendiente":
                total_os_pendiente,

            "total_honorarios_os_pendiente":
                total_honorarios_os_pendiente,

            # --------------------------------------
            # OS COBRADAS
            # --------------------------------------

            "total_os_cobrado":
                total_os_cobrado,

            "total_honorarios_os_disponible":
                total_honorarios_os_disponible,

            # --------------------------------------
            # DISPONIBLE DIRECTO
            # Particular + Coseguro + Copago
            # --------------------------------------

            "total_disponible_directo":
                total_disponible_directo,

            # --------------------------------------
            # TOTAL GENERAL DISPONIBLE
            # --------------------------------------

            "total_disponible":
                (
                    total_disponible_directo
                    + total_honorarios_os_disponible
                ),
        }

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "honorarios/honorarios_medicos.html",
        {
            "medicos":
                medicos,

            "particulares":
                particulares,

            "coseguros":
                coseguros,

            "copagos":
                copagos,

            "obras_sociales_pendientes":
                obras_sociales_pendientes,

            "obras_sociales_cobradas":
                obras_sociales_cobradas,

            "resumen":
                resumen,

            "medico_id":
                medico_id,
        },
    )


@login_required
def previsualizar_liquidacion(request, medico_id):

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    # ==========================================
    # BASE COMÚN
    # ==========================================

    base = DetalleMovimientoCaja.objects.filter(
        movimiento__turno__medico=medico,
        movimiento__centro_medico=centro_medico,
        movimiento__tipo="INGRESO",
        movimiento__estado="ACTIVO",
        estado="PENDIENTE",
    ).select_related(
        "movimiento",
        "movimiento__paciente",
        "movimiento__turno",
        "concepto_facturacion",
        "prestacion_obra_social",
        "prestacion_obra_social__obra_social",
    )

    # ==========================================
    # PARTICULARES
    # ==========================================

    particulares = base.filter(
        concepto_facturacion__isnull=False,
        prestacion_obra_social__isnull=True,
        liquidacion__isnull=True,
    )

    # ==========================================
    # COSEGUROS COBRADOS
    # ==========================================

    coseguros = base.filter(
        prestacion_obra_social__isnull=False,
        coseguro_cobrado=True,
        coseguro_liquidado=False,
        importe_coseguro__gt=0,
    )

    # ==========================================
    # COPAGOS COBRADOS
    # ==========================================
    #
    # El copago:
    # - ya fue cobrado al paciente
    # - corresponde directamente al médico
    # - no modifica el saldo de la Obra Social
    # ==========================================

    copagos = base.filter(
        prestacion_obra_social__isnull=False,
        copago_cobrado=True,
        copago_liquidado=False,
        importe_copago__gt=0,
    )

    # ==========================================
    # TOTAL PARTICULARES
    # ==========================================

    total_particulares = (
        particulares.aggregate(
            total=Sum("importe_medico")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # TOTAL COSEGUROS
    # ==========================================

    total_coseguros = (
        coseguros.aggregate(
            total=Sum("importe_coseguro")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # TOTAL COPAGOS
    # ==========================================

    total_copagos = (
        copagos.aggregate(
            total=Sum("importe_copago")
        )["total"]
        or Decimal("0.00")
    )

    # ==========================================
    # TOTAL A LIQUIDAR
    # ==========================================

    total_honorarios = (
        total_particulares
        + total_coseguros
        + total_copagos
    )

    # ==========================================
    # VALIDAR
    # ==========================================

    if total_honorarios <= 0:

        messages.warning(
            request,
            "No existen honorarios disponibles para liquidar."
        )
        url = reverse("honorarios_medicos")

        return redirect(
            f"{url}?medico={medico.id}"
        )

        

    # ==========================================
    # RESUMEN
    # ==========================================

    resumen = {

        "total_particulares":
            total_particulares,

        "total_coseguros":
            total_coseguros,

        "total_copagos":
            total_copagos,

        "total_honorarios":
            total_honorarios,

        "cantidad_particulares":
            particulares.count(),

        "cantidad_coseguros":
            coseguros.count(),

        "cantidad_copagos":
            copagos.count(),
    }

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "honorarios/previsualizar_liquidacion.html",
        {
            "medico": medico,

            "particulares":
                particulares,

            "coseguros":
                coseguros,

            "copagos":
                copagos,

            "resumen":
                resumen,
        }
    )  

@login_required
def previsualizar_liquidacion_os(request, medico_id):

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    # ======================================================
    # NUEVO SISTEMA
    # HONORARIOS GENERADOS POR DETALLE DE MASTER
    # ======================================================
    #
    # Cada cobro de una OS genera su propio crédito de
    # honorarios.
    #
    # Una misma prestación puede aparecer más de una vez:
    #
    # Master original       -> honorario $X
    # Refacturación         -> honorario $Y
    #
    # Cada uno se liquida independientemente.
    # ======================================================

    detalles_master = list(
        DetalleMasterObraSocial.objects
        .filter(
            master__estado="COBRADO",

            detalle_movimiento__movimiento__turno__medico=medico,
            detalle_movimiento__movimiento__centro_medico=centro_medico,

            detalle_movimiento__movimiento__tipo="INGRESO",
            detalle_movimiento__movimiento__estado="ACTIVO",

            detalle_movimiento__estado="PENDIENTE",
            detalle_movimiento__prestacion_obra_social__isnull=False,

            honorario_medico_liquidado=False,
            honorario_medico_reconocido__isnull=False,
            honorario_medico_reconocido__gt=0,
        )
        .select_related(
            "master",
            "master__obra_social",

            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__centro_medico",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",
            "detalle_movimiento__movimiento__turno__medico",

            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__obra_social",
            "detalle_movimiento__prestacion_obra_social__plan",

            "detalle_origen",
        )
        .order_by(
            "master__obra_social__nombre",
            "detalle_movimiento__fecha_prestacion",
            "id",
        )
    )

    # ======================================================
    # PREPARAR DATOS PARA EL TEMPLATE
    # ======================================================

    prestaciones_os = []

    total_importe_os = Decimal("0.00")
    total_honorarios_os = Decimal("0.00")

    for item_master in detalles_master:

        detalle = item_master.detalle_movimiento

        importe_os = (
            item_master.importe_reconocido
            or Decimal("0.00")
        )

        honorario_os = (
            item_master.honorario_medico_reconocido
            or Decimal("0.00")
        )

        # --------------------------------------------------
        # ATRIBUTOS TEMPORALES
        # --------------------------------------------------
        #
        # Esto permite conservar el template actual sin
        # tener que modificarlo ahora.
        # --------------------------------------------------

        detalle.importe_os_calculado = importe_os
        detalle.honorario_os_calculado = honorario_os

        # Guardamos referencia temporal al detalle Master.
        detalle.detalle_master_liquidacion = item_master

        prestaciones_os.append(detalle)

        total_importe_os += importe_os
        total_honorarios_os += honorario_os

    # ======================================================
    # COMPATIBILIDAD HISTÓRICA
    # ======================================================
    #
    # Buscamos prestaciones del sistema anterior que:
    #
    # - fueron cobradas
    # - todavía no fueron liquidadas
    # - NO poseen un DetalleMaster nuevo con snapshot de
    #   honorario pendiente
    #
    # Esto permite conservar registros históricos que
    # todavía puedan quedar pendientes.
    # ======================================================

    historicos = (
        DetalleMovimientoCaja.objects
        .filter(
            movimiento__turno__medico=medico,
            movimiento__centro_medico=centro_medico,
            movimiento__tipo="INGRESO",
            movimiento__estado="ACTIVO",
            estado="PENDIENTE",
            prestacion_obra_social__isnull=False,
            obra_social_cobrada=True,
            honorario_os_liquidado=False,
        )
        .exclude(
            detalles_master_obra_social__master__estado="COBRADO",
            detalles_master_obra_social__honorario_medico_reconocido__isnull=False,
        )
        .select_related(
            "movimiento",
            "movimiento__centro_medico",
            "movimiento__paciente",
            "movimiento__turno",
            "movimiento__turno__medico",
            "prestacion_obra_social",
            "prestacion_obra_social__obra_social",
            "prestacion_obra_social__plan",
        )
        .distinct()
        .order_by(
            "prestacion_obra_social__obra_social__nombre",
            "fecha_prestacion",
            "id",
        )
    )

    for detalle in historicos:

        if detalle.importe_reconocido_obra_social is not None:

            importe_os = (
                detalle.importe_reconocido_obra_social
            )

        else:

            importe_os = (
                (detalle.importe or Decimal("0.00"))
                -
                (detalle.importe_coseguro or Decimal("0.00"))
            )

            if importe_os < Decimal("0.00"):
                importe_os = Decimal("0.00")

        if detalle.honorario_reconocido_obra_social is not None:

            honorario_os = (
                detalle.honorario_reconocido_obra_social
            )

        else:

            honorario_os = (
                (detalle.importe_medico or Decimal("0.00"))
                -
                (detalle.importe_coseguro or Decimal("0.00"))
            )

            if honorario_os < Decimal("0.00"):
                honorario_os = Decimal("0.00")

        detalle.importe_os_calculado = importe_os
        detalle.honorario_os_calculado = honorario_os

        # Histórico = no tiene detalle Master asociado
        # para esta liquidación.
        detalle.detalle_master_liquidacion = None

        prestaciones_os.append(detalle)

        total_importe_os += importe_os
        total_honorarios_os += honorario_os

    # ======================================================
    # VALIDAR
    # ======================================================

    if not prestaciones_os:

        messages.warning(
            request,
            "No existen honorarios de Obras Sociales "
            "cobradas disponibles para liquidar."
        )

        return redirect(
            f"{reverse('honorarios_medicos')}?medico={medico.id}"
        )

    # ======================================================
    # RESUMEN
    # ======================================================

    resumen = {
        "cantidad": len(prestaciones_os),
        "total_importe_os": total_importe_os,
        "total_honorarios_os": total_honorarios_os,
    }

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "honorarios/previsualizar_liquidacion_os.html",
        {
            "medico": medico,
            "prestaciones_os": prestaciones_os,
            "resumen": resumen,
        }
    )



@login_required
@transaction.atomic
def registrar_pago_liquidacion(
    request,
    liquidacion_id
    ):


    centro_medico = obtener_centro_activo(request)

    liquidacion = get_object_or_404(
        LiquidacionMedica,
        pk=liquidacion_id
    )

    caja = obtener_caja_abierta(
        centro_medico
    )
    medios_pago = MedioPago.objects.filter(
        activo=True
    ).order_by("nombre")

    if not caja:
        mostrar_error(

            request,

            titulo="Caja cerrada",

            mensaje="No existe una caja abierta.",

            detalles=[
                "Debe abrir una caja antes de registrar un pago."
            ],

        )

        return redirect(
            "liquidaciones_pendientes"
        )

        

    if request.method == 'POST':

        form = PagoLiquidacionForm(
            request.POST
        )

        if form.is_valid():
            
            # =====================================
            # MEDIOS DE PAGO
            # =====================================

            medios_pago_json = request.POST.get(
                "medios_pago_json"
            )

            if not medios_pago_json:

                messages.error(
                    request,
                    "Debe agregar al menos un medio de pago."
                )

                return render(
                    request,
                    "honorarios/registrar_pago_liquidacion.html",
                    {
                        "form": form,
                        "liquidacion": liquidacion,
                       "medios_pago": medios_pago,
                    },
                )

            try:

                medios_pago = json.loads(
                    medios_pago_json
                )

            except json.JSONDecodeError:

                messages.error(
                    request,
                    "Error al procesar los medios de pago."
                )

                return render(
                    request,
                    "honorarios/registrar_pago_liquidacion.html",
                    {
                        "form": form,
                        "liquidacion": liquidacion,
                        "medios_pago": MedioPago.objects.filter(
                            activo=True
                        ).order_by("nombre"),
                    },
                )

            importe = form.cleaned_data[
                'importe'
            ]

            if importe <= 0:

                mostrar_error(

                    request,

                    titulo="Importe inválido",

                    mensaje="El importe debe ser mayor a cero.",

                )

                return redirect(
                    'registrar_pago_liquidacion',
                    liquidacion.id
                )

            if importe > liquidacion.saldo_pendiente:
                mostrar_error(

                    request,

                    titulo="Importe inválido",

                    mensaje="El importe supera el saldo pendiente.",

                    detalles=[
                        f"Saldo pendiente: ${liquidacion.saldo_pendiente}"
                    ],

                )

               

                return redirect(
                    'registrar_pago_liquidacion',
                    liquidacion.id
                )

            movimiento = MovimientoCaja.objects.create(

                caja=caja,

                centro_medico=centro_medico,

                tipo='EGRESO',

                importe=importe,

                concepto=(
                    f'Pago Honorarios Médicos - '
                    f'{liquidacion.medico}'
                ),

                observacion=form.cleaned_data[
                    'observacion'
                ],

                estado='ACTIVO',

                creado_por=request.user,
            )

            # =====================================
            # GUARDAR MEDIOS DE PAGO
            # =====================================

            for item in medios_pago:

                medio = MedioPago.objects.get(
                    pk=item["medio"]
                )

                DetalleMedioPago.objects.create(

                    movimiento=movimiento,

                    medio_pago=medio,

                    importe=Decimal(
                        str(item["importe"])
                    )

                )
            PagoLiquidacionMedica.objects.create(

                liquidacion=liquidacion,

                movimiento_caja=movimiento,

                importe=importe,

                registrado_por=request.user
            )

            liquidacion.total_pagado += importe

            liquidacion.cantidad_pagos += 1

            if liquidacion.saldo_pendiente <= 0:

                liquidacion.estado = 'PAGADA'

                liquidacion.fecha_pago = timezone.now()

                liquidacion.pagado_por = request.user

            elif liquidacion.total_pagado > 0:

                liquidacion.estado = 'PARCIAL'

            else:

                liquidacion.estado = 'PENDIENTE'

            liquidacion.save()

            mostrar_exito(

            request,

            titulo="Pago registrado",

            mensaje="El pago de la liquidación fue registrado correctamente.",

            icono="bi-wallet2",

            detalles=[

                f"Médico: {liquidacion.medico}",

                f"Importe pagado: ${importe}",

                f"Saldo pendiente: ${liquidacion.saldo_pendiente}",

                f"Estado: {liquidacion.get_estado_display()}",

            ],

        )

        return redirect(
            "liquidaciones_pendientes"
        )

    else:

        form = PagoLiquidacionForm()

    return render(
        request,
        'honorarios/registrar_pago_liquidacion.html',
        {
            'form': form,
            'liquidacion': liquidacion,
            "medios_pago": medios_pago,
        }
    )



@login_required
@transaction.atomic
def generar_liquidacion(request, medico_id):

    # ==========================================
    # SOLO POST
    # ==========================================

    if request.method != "POST":
        return redirect(
            "previsualizar_liquidacion",
            medico_id=medico_id
        )

    # ==========================================
    # CENTRO Y MÉDICO
    # ==========================================

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    # ==========================================
    # BASE COMÚN
    # ==========================================

    base = DetalleMovimientoCaja.objects.filter(
        movimiento__turno__medico=medico,
        movimiento__centro_medico=centro_medico,
        movimiento__tipo="INGRESO",
        movimiento__estado="ACTIVO",
        estado="PENDIENTE",
    ).select_related(
        "movimiento",
        "movimiento__paciente",
        "movimiento__turno",
        "concepto_facturacion",
        "prestacion_obra_social",
        "prestacion_obra_social__obra_social",
    )

    # ==========================================
    # PARTICULARES PENDIENTES
    # ==========================================

    particulares = list(
        base.filter(
            concepto_facturacion__isnull=False,
            prestacion_obra_social__isnull=True,
            liquidacion__isnull=True,
        )
    )

    # ==========================================
    # COSEGUROS COBRADOS PENDIENTES
    # ==========================================

    coseguros = list(
        base.filter(
            prestacion_obra_social__isnull=False,
            coseguro_cobrado=True,
            coseguro_liquidado=False,
            importe_coseguro__gt=0,
        )
    )

    # ==========================================
    # COPAGOS COBRADOS PENDIENTES
    # ==========================================

    copagos = list(
        base.filter(
            prestacion_obra_social__isnull=False,
            copago_cobrado=True,
            copago_liquidado=False,
            importe_copago__gt=0,
        )
    )

    # ==========================================
    # VALIDAR QUE HAYA ALGO PARA LIQUIDAR
    # ==========================================

    if (
        not particulares
        and not coseguros
        and not copagos
    ):

        messages.warning(
            request,
            "No existen honorarios disponibles para liquidar."
        )

        return redirect(
            "honorarios_medicos"
        )

    # ==========================================
    # TOTAL PARTICULARES
    # ==========================================

    total_particulares = sum(
        (
            detalle.importe_medico
            for detalle in particulares
        ),
        Decimal("0.00")
    )

    # ==========================================
    # TOTAL COSEGUROS
    # ==========================================

    total_coseguros = sum(
        (
            detalle.importe_coseguro
            for detalle in coseguros
        ),
        Decimal("0.00")
    )

    # ==========================================
    # TOTAL COPAGOS
    # ==========================================

    total_copagos = sum(
        (
            detalle.importe_copago
            for detalle in copagos
        ),
        Decimal("0.00")
    )

    # ==========================================
    # TOTAL HONORARIOS
    # ==========================================

    total_honorarios = (
        total_particulares
        + total_coseguros
        + total_copagos
    )

    # ==========================================
    # DATOS FINANCIEROS DE PARTICULARES
    # ==========================================
    #
    # Solamente los particulares forman parte
    # de estos totales financieros.
    #
    # Los valores de OS todavía no entran porque
    # la Obra Social no fue cobrada.
    #
    # Coseguros y copagos solamente forman parte
    # del honorario que liquidamos ahora.
    # ==========================================

    total_bruto = sum(
        (
            detalle.importe
            for detalle in particulares
        ),
        Decimal("0.00")
    )

    total_iva = sum(
        (
            detalle.importe_iva
            for detalle in particulares
        ),
        Decimal("0.00")
    )

    total_consultorio = sum(
        (
            detalle.importe_consultorio
            for detalle in particulares
        ),
        Decimal("0.00")
    )

    total_retenciones = Decimal("0.00")

    # ==========================================
    # CREAR LIQUIDACIÓN
    # ==========================================

    liquidacion = LiquidacionMedica.objects.create(

        medico=medico,

        centro_medico=centro_medico,

        cantidad_prestaciones=(
            len(particulares)
            + len(coseguros)
            + len(copagos)
        ),

        total_bruto=total_bruto,

        total_iva=total_iva,

        total_consultorio=total_consultorio,

        total_honorarios=total_honorarios,

        total_retenciones=total_retenciones,

        estado="PENDIENTE",

        generado_por=request.user,

        creado_por=request.user,
    )

    # ==========================================
    # CREAR ITEMS PARTICULARES
    # ==========================================

    for detalle in particulares:

        DetalleLiquidacionMedica.objects.create(

            liquidacion=liquidacion,

            detalle_movimiento=detalle,

            tipo="PARTICULAR",

            importe=detalle.importe_medico,
        )

        # --------------------------------------
        # PARTICULAR QUEDA TOTALMENTE LIQUIDADO
        # --------------------------------------

        detalle.liquidacion = liquidacion

        detalle.estado = "LIQUIDADO"

        detalle.save(
            update_fields=[
                "liquidacion",
                "estado",
            ]
        )

    # ==========================================
    # CREAR ITEMS COSEGUROS
    # ==========================================

    for detalle in coseguros:

        DetalleLiquidacionMedica.objects.create(

            liquidacion=liquidacion,

            detalle_movimiento=detalle,

            tipo="COSEGURO",

            importe=detalle.importe_coseguro,
        )

        # --------------------------------------
        # SOLO LIQUIDAMOS EL COSEGURO
        # --------------------------------------
        #
        # NO modificamos:
        #
        # detalle.estado
        # detalle.liquidacion
        # detalle.obra_social_cobrada
        # detalle.honorario_os_liquidado
        #
        # La prestación sigue pendiente de OS.
        # --------------------------------------

        detalle.coseguro_liquidado = True

        detalle.save(
            update_fields=[
                "coseguro_liquidado",
            ]
        )

    # ==========================================
    # CREAR ITEMS COPAGOS
    # ==========================================

    for detalle in copagos:

        DetalleLiquidacionMedica.objects.create(

            liquidacion=liquidacion,

            detalle_movimiento=detalle,

            tipo="COPAGO",

            importe=detalle.importe_copago,
        )

        # --------------------------------------
        # SOLO LIQUIDAMOS EL COPAGO
        # --------------------------------------
        #
        # El copago pertenece directamente
        # al médico.
        #
        # NO modificamos:
        #
        # detalle.estado
        # detalle.liquidacion
        # detalle.obra_social_cobrada
        # detalle.honorario_os_liquidado
        #
        # La prestación continúa pendiente
        # hasta que pague la Obra Social.
        # --------------------------------------

        detalle.copago_liquidado = True

        detalle.save(
            update_fields=[
                "copago_liquidado",
            ]
        )

    # ==========================================
    # MENSAJE
    # ==========================================

    messages.success(
        request,
        (
            f"Liquidación #{liquidacion.id} generada correctamente. "
            f"Total: ${total_honorarios:,.2f}"
        )
    )

    # ==========================================
    # IR AL DETALLE
    # ==========================================

    return redirect(
        "detalle_liquidacion_medica",
        liquidacion_id=liquidacion.id
    )

@login_required
@transaction.atomic
def generar_liquidacion_os(request, medico_id):

    # ======================================================
    # SOLO POST
    # ======================================================

    if request.method != "POST":

        return redirect(
            "previsualizar_liquidacion_os",
            medico_id=medico_id
        )

    # ======================================================
    # CENTRO Y MÉDICO
    # ======================================================

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    # ======================================================
    # NUEVO SISTEMA
    # DETALLES MASTER COBRADOS PENDIENTES DE LIQUIDAR
    # ======================================================

    detalles_master = list(
        DetalleMasterObraSocial.objects
        .select_for_update()
        .filter(
            master__estado="COBRADO",

            detalle_movimiento__movimiento__turno__medico=medico,
            detalle_movimiento__movimiento__centro_medico=centro_medico,

            detalle_movimiento__movimiento__tipo="INGRESO",
            detalle_movimiento__movimiento__estado="ACTIVO",

            detalle_movimiento__estado="PENDIENTE",
            detalle_movimiento__prestacion_obra_social__isnull=False,

            honorario_medico_liquidado=False,
            honorario_medico_reconocido__isnull=False,
            honorario_medico_reconocido__gt=0,
        )
        .select_related(
            "master",
            "master__obra_social",

            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__movimiento__turno",

            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__obra_social",
            "detalle_movimiento__prestacion_obra_social__plan",

            "detalle_origen",
        )
    )

    # ======================================================
    # COMPATIBILIDAD HISTÓRICA
    # ======================================================

    historicos = list(
        DetalleMovimientoCaja.objects
        .select_for_update()
        .filter(
            movimiento__turno__medico=medico,
            movimiento__centro_medico=centro_medico,
            movimiento__tipo="INGRESO",
            movimiento__estado="ACTIVO",
            estado="PENDIENTE",

            prestacion_obra_social__isnull=False,

            obra_social_cobrada=True,
            honorario_os_liquidado=False,
        )
        .exclude(
            detalles_master_obra_social__master__estado="COBRADO",
            detalles_master_obra_social__honorario_medico_reconocido__isnull=False,
        )
        .select_related(
            "movimiento",
            "movimiento__paciente",
            "movimiento__turno",

            "prestacion_obra_social",
            "prestacion_obra_social__obra_social",
            "prestacion_obra_social__plan",
        )
        .distinct()
    )

    # ======================================================
    # VALIDAR
    # ======================================================

    if not detalles_master and not historicos:

        messages.warning(
            request,
            "No existen honorarios de Obras Sociales "
            "cobradas disponibles para liquidar."
        )

        return redirect(
            "previsualizar_liquidacion_os",
            medico_id=medico.id
        )

    # ======================================================
    # ITEMS DE LIQUIDACIÓN
    # ======================================================

    items_liquidacion = []

    total_honorarios_os = Decimal("0.00")
    total_bruto = Decimal("0.00")

    # ======================================================
    # NUEVO SISTEMA
    # ======================================================

    for item_master in detalles_master:

        detalle = item_master.detalle_movimiento

        importe_os = (
            item_master.importe_reconocido
            or Decimal("0.00")
        )

        honorario_os = (
            item_master.honorario_medico_reconocido
            or Decimal("0.00")
        )

        if honorario_os <= Decimal("0.00"):
            continue

        items_liquidacion.append(
            {
                "detalle": detalle,
                "detalle_master": item_master,
                "importe_os": importe_os,
                "honorario": honorario_os,
                "historico": False,
            }
        )

        total_bruto += importe_os
        total_honorarios_os += honorario_os

    # ======================================================
    # HISTÓRICOS
    # ======================================================

    for detalle in historicos:

        if detalle.importe_reconocido_obra_social is not None:

            importe_os = (
                detalle.importe_reconocido_obra_social
            )

        else:

            importe_os = (
                (detalle.importe or Decimal("0.00"))
                -
                (detalle.importe_coseguro or Decimal("0.00"))
            )

            if importe_os < Decimal("0.00"):
                importe_os = Decimal("0.00")

        if detalle.honorario_reconocido_obra_social is not None:

            honorario_os = (
                detalle.honorario_reconocido_obra_social
            )

        else:

            honorario_os = (
                (detalle.importe_medico or Decimal("0.00"))
                -
                (detalle.importe_coseguro or Decimal("0.00"))
            )

            if honorario_os < Decimal("0.00"):
                honorario_os = Decimal("0.00")

        if honorario_os <= Decimal("0.00"):
            continue

        items_liquidacion.append(
            {
                "detalle": detalle,
                "detalle_master": None,
                "importe_os": importe_os,
                "honorario": honorario_os,
                "historico": True,
            }
        )

        total_bruto += importe_os
        total_honorarios_os += honorario_os

    # ======================================================
    # VALIDAR TOTAL
    # ======================================================

    if (
        not items_liquidacion
        or total_honorarios_os <= Decimal("0.00")
    ):

        messages.warning(
            request,
            "Las prestaciones cobradas no poseen "
            "honorarios de Obra Social para liquidar."
        )

        return redirect(
            "previsualizar_liquidacion_os",
            medico_id=medico.id
        )

    # ======================================================
    # IVA / CONSULTORIO / RETENCIONES
    # ======================================================

    total_iva = Decimal("0.00")
    total_consultorio = Decimal("0.00")
    total_retenciones = Decimal("0.00")

    # ======================================================
    # CREAR LIQUIDACIÓN
    # ======================================================

    liquidacion = LiquidacionMedica.objects.create(
        medico=medico,
        centro_medico=centro_medico,

        cantidad_prestaciones=len(items_liquidacion),

        total_bruto=total_bruto,
        total_iva=total_iva,
        total_consultorio=total_consultorio,

        total_honorarios=total_honorarios_os,
        total_retenciones=total_retenciones,

        estado="PENDIENTE",

        generado_por=request.user,
        creado_por=request.user,
    )

    # ======================================================
    # CREAR DETALLES
    # ======================================================

    for item in items_liquidacion:

        detalle = item["detalle"]
        detalle_master = item["detalle_master"]
        honorario_os = item["honorario"]
        historico = item["historico"]

        # ==================================================
        # DETALLE LIQUIDACIÓN
        # ==================================================

        DetalleLiquidacionMedica.objects.create(
            liquidacion=liquidacion,
            detalle_movimiento=detalle,

            # ----------------------------------------------
            # NUEVO SISTEMA
            # ----------------------------------------------
            #
            # Para históricos queda NULL.
            # Para Masters nuevos sabemos exactamente qué
            # evento de cobro generó este honorario.
            # ----------------------------------------------

            detalle_master_obra_social=detalle_master,

            tipo="OBRA_SOCIAL",
            importe=honorario_os,
        )

        # ==================================================
        # NUEVO SISTEMA
        # ==================================================

        if detalle_master is not None:

            detalle_master.honorario_medico_liquidado = True

            detalle_master.fecha_liquidacion_honorario = (
                timezone.now()
            )

            detalle_master.save(
                update_fields=[
                    "honorario_medico_liquidado",
                    "fecha_liquidacion_honorario",
                ]
            )

        # ==================================================
        # HISTÓRICO
        # ==================================================

        else:

            detalle.honorario_os_liquidado = True

            detalle.save(
                update_fields=[
                    "honorario_os_liquidado",
                ]
            )

    # ======================================================
    # COMPATIBILIDAD DEL MOVIMIENTO
    # ======================================================
    #
    # Para los registros nuevos NO usamos
    # honorario_os_liquidado para decidir si futuras
    # refacturaciones pueden generar otro honorario.
    #
    # Pero podemos dejarlo en True cuando TODOS los créditos
    # de honorarios actualmente existentes de esa prestación
    # ya están liquidados.
    #
    # Esto mantiene coherencia con otras pantallas antiguas.
    # ======================================================

    movimientos_procesados = {
        item["detalle"].id
        for item in items_liquidacion
        if item["detalle_master"] is not None
    }

    for detalle_id in movimientos_procesados:

        quedan_creditos = (
            DetalleMasterObraSocial.objects
            .filter(
                detalle_movimiento_id=detalle_id,
                master__estado="COBRADO",
                honorario_medico_liquidado=False,
                honorario_medico_reconocido__gt=0,
            )
            .exists()
        )

        if not quedan_creditos:

            DetalleMovimientoCaja.objects.filter(
                pk=detalle_id
            ).update(
                honorario_os_liquidado=True
            )

    # ======================================================
    # MENSAJE
    # ======================================================

    messages.success(
        request,
        (
            "Liquidación de Obra Social generada "
            "correctamente. "
            f"Total honorarios: "
            f"${total_honorarios_os:,.2f}"
        )
    )

    # ======================================================
    # REDIRECT
    # ======================================================

    return redirect(
    "detalle_liquidacion_medica",
    liquidacion_id=liquidacion.id
)



@login_required
def liquidaciones_pendientes(request):

    centro_medico = obtener_centro_activo(request)

    liquidaciones = LiquidacionMedica.objects.filter(
        centro_medico=centro_medico
    ).exclude(
        estado='PAGADA'
    ).select_related(
        'medico'
    )

    return render(
        request,
        'honorarios/liquidaciones_pendientes.html',
        {
            'liquidaciones': liquidaciones
        }
    )

@login_required
@transaction.atomic
def registrar_pago_liquidacion(
    request,
    liquidacion_id
):

    # ==========================================
    # CENTRO MÉDICO ACTIVO
    # ==========================================

    centro_medico = obtener_centro_activo(request)

    # ==========================================
    # LIQUIDACIÓN
    # ==========================================
    #
    # La liquidación debe pertenecer
    # obligatoriamente a la sede activa.
    # ==========================================

    liquidacion = get_object_or_404(
        LiquidacionMedica,
        pk=liquidacion_id,
        centro_medico=centro_medico,
    )

    # ==========================================
    # CAJA ABIERTA
    # ==========================================

    caja = obtener_caja_abierta(
        centro_medico
    )

    # ==========================================
    # MEDIOS DE PAGO
    # ==========================================

    medios_pago = (
        MedioPago.objects
        .filter(activo=True)
        .order_by("nombre")
    )

    # ==========================================
    # VALIDAR CAJA ABIERTA
    # ==========================================

    if not caja:

        mostrar_error(
            request,
            titulo="Caja cerrada",
            mensaje="No existe una caja abierta.",
            detalles=[
                "Debe abrir una caja antes de registrar un pago."
            ],
        )

        return redirect(
            "liquidaciones_pendientes"
        )

    # ==========================================
    # POST
    # ==========================================

    if request.method == "POST":

        form = PagoLiquidacionForm(
            request.POST
        )

        if form.is_valid():

            # ==================================
            # MEDIOS DE PAGO
            # ==================================

            medios_pago_json = request.POST.get(
                "medios_pago_json"
            )

            if not medios_pago_json:

                messages.error(
                    request,
                    "Debe agregar al menos un medio de pago."
                )

                return render(
                    request,
                    "honorarios/registrar_pago_liquidacion.html",
                    {
                        "form": form,
                        "liquidacion": liquidacion,
                        "medios_pago": medios_pago,
                    },
                )

            try:

                medios_pago_seleccionados = json.loads(
                    medios_pago_json
                )

            except json.JSONDecodeError:

                messages.error(
                    request,
                    "Error al procesar los medios de pago."
                )

                return render(
                    request,
                    "honorarios/registrar_pago_liquidacion.html",
                    {
                        "form": form,
                        "liquidacion": liquidacion,
                        "medios_pago": medios_pago,
                    },
                )

            # ==================================
            # IMPORTE DEL PAGO
            # ==================================

            importe = form.cleaned_data[
                "importe"
            ]

            if importe <= 0:

                mostrar_error(
                    request,
                    titulo="Importe inválido",
                    mensaje="El importe debe ser mayor a cero.",
                )

                return redirect(
                    "registrar_pago_liquidacion",
                    liquidacion.id
                )

            # ==================================
            # VALIDAR SALDO
            # ==================================

            if importe > liquidacion.saldo_pendiente:

                mostrar_error(
                    request,
                    titulo="Importe inválido",
                    mensaje="El importe supera el saldo pendiente.",
                    detalles=[
                        f"Saldo pendiente: ${liquidacion.saldo_pendiente}"
                    ],
                )

                return redirect(
                    "registrar_pago_liquidacion",
                    liquidacion.id
                )

            # ==================================
            # CREAR EGRESO EN CAJA
            # ==================================

            movimiento = MovimientoCaja.objects.create(

                caja=caja,

                centro_medico=centro_medico,

                tipo="EGRESO",

                importe=importe,

                concepto=(
                    f"Pago Honorarios Médicos - "
                    f"{liquidacion.medico}"
                ),

                observacion=form.cleaned_data[
                    "observacion"
                ],

                estado="ACTIVO",

                creado_por=request.user,
            )

            # ==================================
            # GUARDAR MEDIOS DE PAGO
            # ==================================

            for item in medios_pago_seleccionados:

                medio = MedioPago.objects.get(
                    pk=item["medio"],
                    activo=True,
                )

                DetalleMedioPago.objects.create(

                    movimiento=movimiento,

                    medio_pago=medio,

                    importe=Decimal(
                        str(item["importe"])
                    ),
                )

            # ==================================
            # REGISTRAR PAGO DE LIQUIDACIÓN
            # ==================================

            PagoLiquidacionMedica.objects.create(

                liquidacion=liquidacion,

                movimiento_caja=movimiento,

                importe=importe,

                registrado_por=request.user,
            )

            # ==================================
            # ACTUALIZAR LIQUIDACIÓN
            # ==================================

            liquidacion.total_pagado += importe

            liquidacion.cantidad_pagos += 1

            # ==================================
            # ESTADO DE LA LIQUIDACIÓN
            # ==================================

            if liquidacion.saldo_pendiente <= 0:

                liquidacion.estado = "PAGADA"

                liquidacion.fecha_pago = timezone.now()

                liquidacion.pagado_por = request.user

            elif liquidacion.total_pagado > 0:

                liquidacion.estado = "PARCIAL"

                liquidacion.fecha_pago = None

                liquidacion.pagado_por = None

            else:

                liquidacion.estado = "PENDIENTE"

                liquidacion.fecha_pago = None

                liquidacion.pagado_por = None

            liquidacion.save()

            # ==================================
            # MENSAJE
            # ==================================

            mostrar_exito(
                request,
                titulo="Pago registrado",
                mensaje=(
                    "El pago de la liquidación "
                    "fue registrado correctamente."
                ),
                icono="bi-wallet2",
                detalles=[
                    f"Médico: {liquidacion.medico}",
                    f"Importe pagado: ${importe}",
                    (
                        f"Saldo pendiente: "
                        f"${liquidacion.saldo_pendiente}"
                    ),
                    (
                        f"Estado: "
                        f"{liquidacion.get_estado_display()}"
                    ),
                ],
            )

            return redirect(
                "liquidaciones_pendientes"
            )

    else:

        form = PagoLiquidacionForm()

    # ==========================================
    # TEMPLATE
    # ==========================================

    return render(
        request,
        "honorarios/registrar_pago_liquidacion.html",
        {
            "form": form,
            "liquidacion": liquidacion,
            "medios_pago": medios_pago,
        }
    )


@login_required
def historial_liquidaciones_medicas(request):

    liquidaciones = (
    LiquidacionMedica.objects
    .select_related(
        "medico",
        "centro_medico",
        "generado_por",
        "pagado_por",
    )
    .annotate(
        cantidad_items_nuevos=Count(
            "items",
            distinct=True
        ),
        cantidad_detalles_anteriores=Count(
            "detalles",
            distinct=True
        ),
    )
    .annotate(
        cantidad_conceptos=Case(
            When(
                cantidad_items_nuevos__gt=0,
                then=F("cantidad_items_nuevos")
            ),
            default=F("cantidad_detalles_anteriores"),
            output_field=IntegerField(),
        )
    )
    .order_by("-fecha")
)

    form = FiltroHistorialLiquidacionesForm(
        request.GET or None
    )

    if form.is_valid():

        desde = form.cleaned_data.get(
            "desde"
        )

        hasta = form.cleaned_data.get(
            "hasta"
        )

        medico = form.cleaned_data.get(
            "medico"
        )

        centro = form.cleaned_data.get(
            "centro_medico"
        )

        estado = form.cleaned_data.get(
            "estado"
        )

        if desde:

            liquidaciones = liquidaciones.filter(
                fecha__date__gte=desde
            )

        if hasta:

            liquidaciones = liquidaciones.filter(
                fecha__date__lte=hasta
            )

        if medico:

            liquidaciones = liquidaciones.filter(
                medico=medico
            )

        if centro:

            liquidaciones = liquidaciones.filter(
                centro_medico=centro
            )

        if estado:

            liquidaciones = liquidaciones.filter(
                estado=estado
            )

    return render(
        request,
        "honorarios/historial_liquidaciones.html",
        {
            "form": form,
            "liquidaciones": liquidaciones,
        },
    )


@login_required
def detalle_liquidacion_medica(
    request,
    liquidacion_id
):

    # ==========================================
    # LIQUIDACIÓN
    # ==========================================

    liquidacion = get_object_or_404(
        LiquidacionMedica,
        pk=liquidacion_id
    )

    # ==========================================
    # ITEMS NUEVOS
    # ==========================================
    #
    # Sistema actual:
    #
    # DetalleLiquidacionMedica
    #   - PARTICULAR
    #   - COSEGURO
    #   - OBRA SOCIAL (futuro)
    #
    # ==========================================

    items_nuevos = list(
        DetalleLiquidacionMedica.objects
        .filter(
            liquidacion=liquidacion
        )
        .select_related(
            "detalle_movimiento",
            "detalle_movimiento__movimiento",
            "detalle_movimiento__movimiento__paciente",
            "detalle_movimiento__prestacion_obra_social",
            "detalle_movimiento__prestacion_obra_social__obra_social",
            "detalle_movimiento__concepto_facturacion",
        )
        .order_by(
            "detalle_movimiento__fecha_prestacion",
            "id"
        )
    )

    # ==========================================
    # DETERMINAR SISTEMA
    # ==========================================

    usa_sistema_nuevo = bool(items_nuevos)

    # ==========================================
    # SISTEMA NUEVO
    # ==========================================

    if usa_sistema_nuevo:

        items = items_nuevos

        total_particulares = sum(
            (
                item.importe
                for item in items
                if item.tipo == "PARTICULAR"
            ),
            Decimal("0.00")
        )

        total_coseguros = sum(
            (
                item.importe
                for item in items
                if item.tipo == "COSEGURO"
            ),
            Decimal("0.00")
        )

        cantidad_conceptos = len(items)

    # ==========================================
    # SISTEMA HISTÓRICO
    # ==========================================

    else:

        items = list(
            liquidacion.detalles
            .select_related(
                "movimiento",
                "movimiento__paciente",
                "concepto_facturacion",
                "prestacion_obra_social",
            )
            .order_by(
                "fecha_prestacion",
                "id"
            )
        )

        # En las liquidaciones históricas no
        # necesitamos reconstruir PARTICULAR /
        # COSEGURO.
        #
        # Conservamos los totales originales
        # de la liquidación.

        total_particulares = Decimal("0.00")
        total_coseguros = Decimal("0.00")

        cantidad_conceptos = len(items)

    # ==========================================
    # PAGOS
    # ==========================================

    pagos = (
        PagoLiquidacionMedica.objects
        .filter(
            liquidacion=liquidacion
        )
        .select_related(
            "movimiento_caja",
            "registrado_por"
        )
        .prefetch_related(
            "movimiento_caja__detalles_medios_pago",
            "movimiento_caja__detalles_medios_pago__medio_pago",
        )
        .order_by("-fecha")
    )

    # ==========================================
    # CONTEXTO
    # ==========================================

    return render(
        request,
        "honorarios/detalle_liquidacion_medica.html",
        {
            "liquidacion": liquidacion,

            "items": items,
            "pagos": pagos,

            "usa_sistema_nuevo": usa_sistema_nuevo,
            "cantidad_conceptos": cantidad_conceptos,

            "total_particulares": total_particulares,
            "total_coseguros": total_coseguros,
        },
    )
    

@login_required
def generar_liquidacion_obra_social(request):

    # ==========================================
    # CENTRO ACTIVO
    # ==========================================

    centro_medico = obtener_centro_activo(request)

    # ==========================================
    # DATOS DEL FILTRO
    # ==========================================

    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")
    obra_social_id = request.GET.get("obra_social")
    medico_id = request.GET.get("medico")

    # ==========================================
    # LISTAS PARA LOS SELECTORES
    # ==========================================

    obras_sociales = (
        ObraSocial.objects
        .filter(activa=True)
        .order_by("nombre")
    )

    medicos = (
        Medico.objects
        .all()
        .order_by("apellido", "nombre")
    )

    # ==========================================
    # RESULTADOS
    # ==========================================

    prestaciones = DetalleMovimientoCaja.objects.none()

    filtros_aplicados = False

    # ==========================================
    # BUSCAR
    # ==========================================

    if (
        desde
        and hasta
        and obra_social_id
        and medico_id
    ):

        filtros_aplicados = True

        prestaciones = (
            DetalleMovimientoCaja.objects
            .filter(

                # ----------------------------------
                # CENTRO
                # ----------------------------------

                movimiento__centro_medico=centro_medico,

                # ----------------------------------
                # MOVIMIENTO VÁLIDO
                # ----------------------------------

                movimiento__tipo="INGRESO",
                movimiento__estado="ACTIVO",

                # ----------------------------------
                # MÉDICO
                # ----------------------------------

                movimiento__turno__medico_id=medico_id,

                # ----------------------------------
                # OBRA SOCIAL
                # ----------------------------------

                prestacion_obra_social__isnull=False,

                prestacion_obra_social__obra_social_id=obra_social_id,

                # ----------------------------------
                # FECHAS
                # ----------------------------------

                fecha_prestacion__range=(
                    desde,
                    hasta
                ),

                # ----------------------------------
                # TODAVÍA NO COBRADA DE LA OS
                # ----------------------------------

                obra_social_cobrada=False,

                # ----------------------------------
                # HONORARIO OS TODAVÍA NO LIQUIDADO
                # ----------------------------------

                honorario_os_liquidado=False,
            )
            .select_related(
                "movimiento",
                "movimiento__paciente",
                "movimiento__turno",

                "prestacion_obra_social",
                "prestacion_obra_social__obra_social",

                # Necesario para código y descripción
                "prestacion_obra_social__nomenclador",
            )
            .order_by(
                "fecha_prestacion",
                "movimiento__paciente__apellido",
                "id",
            )
        )

    # ==========================================
    # CALCULAR HONORARIO OS PENDIENTE
    # ==========================================
    #
    # IMPORTANTE:
    #
    # importe_medico contiene el honorario total
    # correspondiente a la prestación.
    #
    # Si el coseguro ya fue liquidado anteriormente,
    # debemos descontarlo para no volver a pagarlo.
    #
    # Ejemplo:
    #
    # Honorario médico original:     $179.550
    # Coseguro ya liquidado:          $10.000
    # Honorario pendiente por OS:    $169.550
    #
    # ==========================================

    for detalle in prestaciones:

        honorario_pendiente = (
            detalle.importe_medico
            or Decimal("0.00")
        )

        # --------------------------------------
        # DESCONTAR COSEGURO YA LIQUIDADO
        # --------------------------------------

        if detalle.coseguro_liquidado:

            honorario_pendiente -= (
                detalle.importe_coseguro
                or Decimal("0.00")
            )

        # --------------------------------------
        # EVITAR VALORES NEGATIVOS
        # --------------------------------------

        if honorario_pendiente < Decimal("0.00"):

            honorario_pendiente = Decimal("0.00")

        # --------------------------------------
        # ATRIBUTO TEMPORAL PARA EL HTML
        # --------------------------------------

        detalle.honorario_os_pendiente = (
            honorario_pendiente
        )

    # ==========================================
    # TOTALES PARA PREVISUALIZACIÓN
    # ==========================================

    cantidad_prestaciones = prestaciones.count()

    # ------------------------------------------
    # TOTAL COBRADO A LA OBRA SOCIAL
    # ------------------------------------------

    total_obra_social = sum(
        (
            detalle.importe
            or Decimal("0.00")
            for detalle in prestaciones
        ),
        Decimal("0.00")
    )

    # ------------------------------------------
    # TOTAL HONORARIOS PENDIENTES
    # ------------------------------------------
    #
    # Usamos honorario_os_pendiente y NO
    # importe_medico, porque puede existir
    # un coseguro previamente liquidado.
    # ------------------------------------------

    total_honorarios = sum(
        (
            detalle.honorario_os_pendiente
            for detalle in prestaciones
        ),
        Decimal("0.00")
    )

    # ==========================================
    # CONTEXTO
    # ==========================================

    context = {

        "centro_medico": centro_medico,

        # --------------------------------------
        # SELECTORES
        # --------------------------------------

        "obras_sociales": obras_sociales,
        "medicos": medicos,

        # --------------------------------------
        # RESULTADOS
        # --------------------------------------

        "prestaciones": prestaciones,

        "filtros_aplicados": filtros_aplicados,

        # --------------------------------------
        # TOTALES
        # --------------------------------------

        "cantidad_prestaciones": cantidad_prestaciones,
        "total_obra_social": total_obra_social,
        "total_honorarios": total_honorarios,

        # --------------------------------------
        # MANTENER FILTROS SELECCIONADOS
        # --------------------------------------

        "desde": desde,
        "hasta": hasta,
        "obra_social_id": obra_social_id,
        "medico_id": medico_id,
    }

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "honorarios/generar_liquidacion_os.html",
        context,
    )
    
@login_required
@transaction.atomic
def confirmar_liquidacion_obra_social(request):

    # ==========================================
    # SOLO POST
    # ==========================================

    if request.method != "POST":
        return redirect(
            "generar_liquidacion_obra_social"
        )

    # ==========================================
    # CENTRO ACTIVO
    # ==========================================

    centro_medico = obtener_centro_activo(request)

    # ==========================================
    # DATOS RECIBIDOS
    # ==========================================

    detalle_ids = request.POST.getlist(
        "prestaciones"
    )

    obra_social_id = request.POST.get(
        "obra_social"
    )

    medico_id = request.POST.get(
        "medico"
    )

    desde = request.POST.get(
        "desde"
    )

    hasta = request.POST.get(
        "hasta"
    )

    # ==========================================
    # VALIDACIONES BÁSICAS
    # ==========================================

    if not detalle_ids:

        messages.warning(
            request,
            "Debe seleccionar al menos una prestación."
        )

        return redirect(
            "generar_liquidacion_obra_social"
        )

    if not obra_social_id or not medico_id:

        messages.error(
            request,
            "No se pudo identificar la obra social o el médico."
        )

        return redirect(
            "generar_liquidacion_obra_social"
        )

    # ==========================================
    # OBTENER MÉDICO Y OBRA SOCIAL
    # ==========================================

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    # ==========================================
    # VOLVER A CONSULTAR LAS PRESTACIONES
    # ==========================================
    #
    # MUY IMPORTANTE:
    # No confiamos solamente en los IDs enviados
    # por el navegador.
    #
    # Volvemos a comprobar:
    #
    # - sede
    # - médico
    # - obra social
    # - movimiento activo
    # - todavía no cobrada OS
    # - honorario OS todavía no liquidado
    #
    # ==========================================

    prestaciones = list(
        DetalleMovimientoCaja.objects
        .select_for_update()
        .filter(
            id__in=detalle_ids,

            movimiento__centro_medico=centro_medico,
            movimiento__tipo="INGRESO",
            movimiento__estado="ACTIVO",

            movimiento__turno__medico=medico,

            prestacion_obra_social__isnull=False,
            prestacion_obra_social__obra_social=obra_social,

            obra_social_cobrada=False,
            honorario_os_liquidado=False,
        )
        .select_related(
            "movimiento",
            "movimiento__paciente",
            "movimiento__turno",
            "prestacion_obra_social",
            "prestacion_obra_social__obra_social",
            "prestacion_obra_social__nomenclador",
        )
        .order_by(
            "fecha_prestacion",
            "id"
        )
    )

    # ==========================================
    # VALIDAR RESULTADOS
    # ==========================================

    if not prestaciones:

        messages.warning(
            request,
            "Las prestaciones seleccionadas ya no están disponibles para liquidar."
        )

        return redirect(
            "generar_liquidacion_obra_social"
        )

    # ==========================================
    # SEGURIDAD: TODOS LOS IDS DEBEN SER VÁLIDOS
    # ==========================================

    ids_validos = {
        str(detalle.id)
        for detalle in prestaciones
    }

    ids_solicitados = {
        str(detalle_id)
        for detalle_id in detalle_ids
    }

    if ids_validos != ids_solicitados:

        messages.error(
            request,
            (
                "Una o más prestaciones seleccionadas ya no están "
                "disponibles. No se generó la liquidación."
            )
        )

        transaction.set_rollback(True)

        return redirect(
            "generar_liquidacion_obra_social"
        )

    # ==========================================
    # TOTALES
    # ==========================================

    total_bruto = Decimal("0.00")
    total_iva = Decimal("0.00")
    total_consultorio = Decimal("0.00")
    total_honorarios = Decimal("0.00")
    total_retenciones = Decimal("0.00")

    honorarios_por_detalle = {}

    # ==========================================
    # CALCULAR CADA PRESTACIÓN
    # ==========================================

    for detalle in prestaciones:

        total_bruto += (
            detalle.importe
            or Decimal("0.00")
        )

        total_iva += (
            detalle.importe_iva
            or Decimal("0.00")
        )

        total_consultorio += (
            detalle.importe_consultorio
            or Decimal("0.00")
        )

        # --------------------------------------
        # HONORARIO ORIGINAL
        # --------------------------------------

        honorario_os = (
            detalle.importe_medico
            or Decimal("0.00")
        )

        # --------------------------------------
        # DESCONTAR COSEGURO YA LIQUIDADO
        # --------------------------------------
        #
        # Ejemplo:
        #
        # Honorario total:       179.550
        # Coseguro ya liquidado:  10.000
        #
        # Honorario OS:          169.550
        #
        # --------------------------------------

        if detalle.coseguro_liquidado:

            honorario_os -= (
                detalle.importe_coseguro
                or Decimal("0.00")
            )

        # Nunca permitir honorario negativo

        if honorario_os < 0:
            honorario_os = Decimal("0.00")

        honorarios_por_detalle[
            detalle.id
        ] = honorario_os

        total_honorarios += honorario_os

    # ==========================================
    # CREAR LIQUIDACIÓN
    # ==========================================

    liquidacion = LiquidacionMedica.objects.create(

        medico=medico,
        centro_medico=centro_medico,

        cantidad_prestaciones=len(
            prestaciones
        ),

        total_bruto=total_bruto,
        total_iva=total_iva,
        total_retenciones=total_retenciones,
        total_consultorio=total_consultorio,

        total_honorarios=total_honorarios,

        estado="PENDIENTE",

        generado_por=request.user,
        creado_por=request.user,

        observacion=(
            f"Liquidación Obra Social: "
            f"{obra_social.nombre}"
        ),
    )

    # ==========================================
    # CREAR ITEMS DE LIQUIDACIÓN
    # ==========================================

    for detalle in prestaciones:

        honorario_os = (
            honorarios_por_detalle[
                detalle.id
            ]
        )

        DetalleLiquidacionMedica.objects.create(

            liquidacion=liquidacion,

            detalle_movimiento=detalle,

            tipo="OBRA_SOCIAL",

            importe=honorario_os,
        )

        # ======================================
        # MARCAR PARTE OS COMO LIQUIDADA
        # ======================================

        detalle.obra_social_cobrada = True
        detalle.honorario_os_liquidado = True

        detalle.save(
            update_fields=[
                "obra_social_cobrada",
                "honorario_os_liquidado",
            ]
        )

    # ==========================================
    # MENSAJE
    # ==========================================

    messages.success(
        request,
        (
            f"Liquidación #{liquidacion.id} generada correctamente "
            f"para {obra_social.nombre}. "
            f"{len(prestaciones)} prestaciones. "
            f"Honorarios: ${total_honorarios:,.2f}"
        )
    )

    # ==========================================
    # IR AL DETALLE
    # ==========================================

    return redirect(
        "detalle_liquidacion_medica",
        liquidacion_id=liquidacion.id
    )