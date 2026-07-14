from django.utils import timezone
from core.utils import mostrar_exito
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
import json

from decimal import Decimal
from caja.views import obtener_caja_abierta

from honorarios.models import (
    LiquidacionMedica,
    PagoLiquidacionMedica
)

from honorarios.forms import (
    PagoLiquidacionForm
)

from caja.models import (
    MovimientoCaja,
    DetalleMedioPago,
    MedioPago
)

from core.utils import (
    obtener_centro_activo
)
from django.contrib import messages

from django.db import transaction


from .models import LiquidacionMedica

from core.utils import obtener_centro_activo,mostrar_error
# Create your views here.
from django.db.models import Sum
from medicos.models import Medico
from caja.models import MovimientoCaja,  DetalleMovimientoCaja
from django.contrib.auth.decorators import login_required


@login_required
def honorarios_medicos(request):

    medico_id = request.GET.get("medico")

    medicos = Medico.objects.all().order_by(
        "apellido",
        "nombre"
    )

    detalles = DetalleMovimientoCaja.objects.none()

    resumen = {}

    if medico_id:

        detalles = DetalleMovimientoCaja.objects.filter(

            movimiento__turno__medico_id=medico_id,

            movimiento__tipo="INGRESO",

            movimiento__estado="ACTIVO",

            estado="PENDIENTE",

            liquidacion__isnull=True,

        ).select_related(

            "movimiento",

            "movimiento__paciente",

            "movimiento__turno",

        )

        resumen = detalles.aggregate(

            total_bruto=Sum("importe"),

            total_iva=Sum("importe_iva"),

            total_consultorio=Sum("importe_consultorio"),

            total_honorarios=Sum("importe_medico"),

        )

        resumen["total_retenciones"] = 0

    return render(

        request,

        "honorarios/honorarios_medicos.html",

        {

            "medicos": medicos,

            "detalles": detalles,

            "resumen": resumen,

            "medico_id": medico_id,

        },

    )

@login_required
@transaction.atomic
def generar_liquidacion(request, medico_id):

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    detalles = DetalleMovimientoCaja.objects.filter(

        movimiento__turno__medico=medico,

        movimiento__centro_medico=centro_medico,

        movimiento__tipo="INGRESO",

        movimiento__estado="ACTIVO",

        estado="PENDIENTE",

        liquidacion__isnull=True,

    )

    if not detalles.exists():

        messages.warning(
            request,
            "No existen prestaciones pendientes para liquidar."
        )

        return redirect(
            "honorarios_medicos"
        )

    resumen = detalles.aggregate(

        total_bruto=Sum(
            "importe"
        ),

        total_iva=Sum(
            "importe_iva"
        ),

        total_consultorio=Sum(
            "importe_consultorio"
        ),

        total_honorarios=Sum(
            "importe_medico"
        ),

    )

    liquidacion = LiquidacionMedica.objects.create(

        medico=medico,

        centro_medico=centro_medico,

        cantidad_prestaciones=detalles.count(),

        total_bruto=(
            resumen["total_bruto"] or 0
        ),

        total_iva=(
            resumen["total_iva"] or 0
        ),

        total_retenciones=0,

        total_consultorio=(
            resumen["total_consultorio"] or 0
        ),

        total_honorarios=(
            resumen["total_honorarios"] or 0
        ),

        generado_por=request.user,

    )

    detalles.update(

        estado="LIQUIDADO",

        liquidacion=liquidacion,

    )

    messages.success(

        request,

        (
            f"Liquidación generada correctamente. "
            f"Total honorarios: "
            f"${liquidacion.total_honorarios}"
        ),

    )

    return redirect(
        "honorarios_medicos"
    )
    
@login_required
def previsualizar_liquidacion(request, medico_id):

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    detalles = DetalleMovimientoCaja.objects.filter(

        movimiento__turno__medico=medico,

        movimiento__centro_medico=centro_medico,

        movimiento__tipo="INGRESO",

        movimiento__estado="ACTIVO",

        estado="PENDIENTE",

        liquidacion__isnull=True,

    ).select_related(

        "movimiento",

        "movimiento__paciente",

    )

    if not detalles.exists():

        messages.warning(
            request,
            "No existen prestaciones pendientes."
        )

        return redirect(
            "honorarios_medicos"
        )

    resumen = detalles.aggregate(

        total_bruto=Sum("importe"),

        total_iva=Sum("importe_iva"),

        total_consultorio=Sum("importe_consultorio"),

        total_honorarios=Sum("importe_medico"),

    )

    resumen["total_retenciones"] = 0

    return render(

        request,

        "honorarios/previsualizar_liquidacion.html",

        {

            "medico": medico,

            "detalles": detalles,

            "resumen": resumen,

        }

    )




from django.utils import timezone
from core.utils import mostrar_exito
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
import json

from decimal import Decimal
from caja.views import obtener_caja_abierta

from honorarios.models import (
    LiquidacionMedica,
    PagoLiquidacionMedica
)

from honorarios.forms import (
    PagoLiquidacionForm
)

from caja.models import (
    MovimientoCaja,
    DetalleMedioPago,
    MedioPago
)

from core.utils import (
    obtener_centro_activo
)
from django.contrib import messages

from django.db import transaction


from .models import LiquidacionMedica

from core.utils import obtener_centro_activo,mostrar_error
# Create your views here.
from django.db.models import Sum
from medicos.models import Medico
from caja.models import MovimientoCaja,  DetalleMovimientoCaja
from django.contrib.auth.decorators import login_required


@login_required
def honorarios_medicos(request):

    medico_id = request.GET.get("medico")

    medicos = Medico.objects.all().order_by(
        "apellido",
        "nombre"
    )

    detalles = DetalleMovimientoCaja.objects.none()

    resumen = {}

    if medico_id:

        detalles = DetalleMovimientoCaja.objects.filter(

            movimiento__turno__medico_id=medico_id,

            movimiento__tipo="INGRESO",

            movimiento__estado="ACTIVO",

            estado="PENDIENTE",

            liquidacion__isnull=True,

        ).select_related(

            "movimiento",

            "movimiento__paciente",

            "movimiento__turno",

        )

        resumen = detalles.aggregate(

            total_bruto=Sum("importe"),

            total_iva=Sum("importe_iva"),

            total_consultorio=Sum("importe_consultorio"),

            total_honorarios=Sum("importe_medico"),

        )

        resumen["total_retenciones"] = 0

    return render(

        request,

        "honorarios/honorarios_medicos.html",

        {

            "medicos": medicos,

            "detalles": detalles,

            "resumen": resumen,

            "medico_id": medico_id,

        },

    )

@login_required
@transaction.atomic
def generar_liquidacion(request, medico_id):
    
    if request.method != "POST":
        return redirect("honorarios_medicos")

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    detalles = DetalleMovimientoCaja.objects.filter(

        movimiento__turno__medico=medico,

        movimiento__centro_medico=centro_medico,

        movimiento__tipo="INGRESO",

        movimiento__estado="ACTIVO",

        estado="PENDIENTE",

        liquidacion__isnull=True,

    )

    if not detalles.exists():

        messages.warning(
            request,
            "No existen prestaciones pendientes para liquidar."
        )

        return redirect(
            "honorarios_medicos"
        )

    resumen = detalles.aggregate(

        total_bruto=Sum(
            "importe"
        ),

        total_iva=Sum(
            "importe_iva"
        ),

        total_consultorio=Sum(
            "importe_consultorio"
        ),

        total_honorarios=Sum(
            "importe_medico"
        ),

    )

    liquidacion = LiquidacionMedica.objects.create(

        medico=medico,

        centro_medico=centro_medico,

        cantidad_prestaciones=detalles.count(),

        total_bruto=(
            resumen["total_bruto"] or 0
        ),

        total_iva=(
            resumen["total_iva"] or 0
        ),

        total_retenciones=0,

        total_consultorio=(
            resumen["total_consultorio"] or 0
        ),

        total_honorarios=(
            resumen["total_honorarios"] or 0
        ),

        generado_por=request.user,

    )

    detalles.update(

        estado="LIQUIDADO",

        liquidacion=liquidacion,

    )

    messages.success(

        request,

        (
            f"Liquidación generada correctamente. "
            f"Total honorarios: "
            f"${liquidacion.total_honorarios}"
        ),

    )

    return redirect(
        "honorarios_medicos"
    )
    
@login_required
def previsualizar_liquidacion(request, medico_id):

    centro_medico = obtener_centro_activo(request)

    medico = get_object_or_404(
        Medico,
        pk=medico_id
    )

    detalles = DetalleMovimientoCaja.objects.filter(

        movimiento__turno__medico=medico,

        movimiento__centro_medico=centro_medico,

        movimiento__tipo="INGRESO",

        movimiento__estado="ACTIVO",

        estado="PENDIENTE",

        liquidacion__isnull=True,

    ).select_related(

        "movimiento",

        "movimiento__paciente",

    )

    if not detalles.exists():

        messages.warning(
            request,
            "No existen prestaciones pendientes."
        )

        return redirect(
            "honorarios_medicos"
        )

    resumen = detalles.aggregate(

        total_bruto=Sum("importe"),

        total_iva=Sum("importe_iva"),

        total_consultorio=Sum("importe_consultorio"),

        total_honorarios=Sum("importe_medico"),

    )

    resumen["total_retenciones"] = 0

    return render(

        request,

        "honorarios/previsualizar_liquidacion.html",

        {

            "medico": medico,

            "detalles": detalles,

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