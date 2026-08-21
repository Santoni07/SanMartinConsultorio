from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
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
    obras_sociales_pendientes = DetalleMovimientoCaja.objects.none()

    # ==========================================
    # RESUMEN INICIAL
    # ==========================================

    resumen = {
        "total_particulares": Decimal("0.00"),
        "total_coseguros": Decimal("0.00"),
        "total_os_pendiente": Decimal("0.00"),
        "total_honorarios_os_pendiente": Decimal("0.00"),
        "total_disponible": Decimal("0.00"),
    }

    # ==========================================
    # SI SE SELECCIONÓ MÉDICO
    # ==========================================

    if medico_id:

        # ==========================================
        # BASE COMÚN
        # ==========================================

        base = DetalleMovimientoCaja.objects.filter(
            movimiento__turno__medico_id=medico_id,
            movimiento__centro_medico=centro_medico,
            movimiento__tipo="INGRESO",
            movimiento__estado="ACTIVO",
            estado="PENDIENTE",
        ).select_related(
            "movimiento",
            "movimiento__paciente",
            "movimiento__turno",
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
        # OBRAS SOCIALES PENDIENTES DE COBRO
        # ==========================================

        obras_sociales_pendientes = base.filter(
            prestacion_obra_social__isnull=False,
            obra_social_cobrada=False,
            honorario_os_liquidado=False,
        )

        # IMPORTANTE:
        # Inicializamos los acumuladores ANTES del for.

        total_os_pendiente = Decimal("0.00")
        total_honorarios_os_pendiente = Decimal("0.00")

        # ==========================================
        # CALCULAR CADA PRESTACIÓN OS
        # ==========================================

        for detalle in obras_sociales_pendientes:

            # --------------------------------------
            # SALDO QUE DEBE PAGAR LA OBRA SOCIAL
            # --------------------------------------

            saldo_os = (
                detalle.importe
                - detalle.importe_coseguro
            )

            if saldo_os < 0:
                saldo_os = Decimal("0.00")

            # Atributo temporal para mostrar en HTML
            detalle.saldo_os_calculado = saldo_os

            total_os_pendiente += saldo_os

            # --------------------------------------
            # HONORARIO MÉDICO PENDIENTE DE LA OS
            # --------------------------------------

            honorario_os = (
                detalle.importe_medico
                - detalle.importe_coseguro
            )

            if honorario_os < 0:
                honorario_os = Decimal("0.00")

            # Atributo temporal para mostrar en HTML
            detalle.honorario_os_calculado = honorario_os

            total_honorarios_os_pendiente += honorario_os

        # ==========================================
        # RESUMEN FINAL
        # ==========================================

        resumen = {
            "total_particulares":
                total_particulares,

            "total_coseguros":
                total_coseguros,

            "total_os_pendiente":
                total_os_pendiente,

            "total_honorarios_os_pendiente":
                total_honorarios_os_pendiente,

            "total_disponible":
                total_particulares + total_coseguros,
        }

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "honorarios/honorarios_medicos.html",
        {
            "medicos": medicos,
            "particulares": particulares,
            "coseguros": coseguros,
            "obras_sociales_pendientes":
                obras_sociales_pendientes,
            "resumen": resumen,
            "medico_id": medico_id,
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
    # TOTAL A LIQUIDAR
    # ==========================================

    total_honorarios = (
        total_particulares
        + total_coseguros
    )

    # ==========================================
    # VALIDAR
    # ==========================================

    if total_honorarios <= 0:

        messages.warning(
            request,
            "No existen honorarios disponibles para liquidar."
        )

        return redirect(
            "honorarios_medicos"
        )

    # ==========================================
    # RESUMEN
    # ==========================================

    resumen = {
        "total_particulares": total_particulares,
        "total_coseguros": total_coseguros,
        "total_honorarios": total_honorarios,
        "cantidad_particulares": particulares.count(),
        "cantidad_coseguros": coseguros.count(),
    }

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "honorarios/previsualizar_liquidacion.html",
        {
            "medico": medico,
            "particulares": particulares,
            "coseguros": coseguros,
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
    # VALIDAR QUE HAYA ALGO PARA LIQUIDAR
    # ==========================================

    if not particulares and not coseguros:

        messages.warning(
            request,
            "No existen honorarios disponibles para liquidar."
        )

        return redirect(
            "honorarios_medicos"
        )

    # ==========================================
    # TOTALES
    # ==========================================

    total_particulares = sum(
        (
            detalle.importe_medico
            for detalle in particulares
        ),
        Decimal("0.00")
    )

    total_coseguros = sum(
        (
            detalle.importe_coseguro
            for detalle in coseguros
        ),
        Decimal("0.00")
    )

    total_honorarios = (
        total_particulares
        + total_coseguros
    )

    # ==========================================
    # DATOS FINANCIEROS DE PARTICULARES
    # ==========================================
    #
    # Los valores de OS no entran todavía
    # porque la Obra Social no fue cobrada.
    #
    # El coseguro solamente forma parte del
    # honorario que estamos pagando ahora.
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
        # NO cambiamos:
        #
        # detalle.estado
        # detalle.liquidacion
        # detalle.obra_social_cobrada
        # detalle.honorario_os_liquidado
        #
        # La prestación OS debe continuar
        # pendiente hasta que la OS pague.
        # --------------------------------------

        detalle.coseguro_liquidado = True

        detalle.save(
            update_fields=[
                "coseguro_liquidado",
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