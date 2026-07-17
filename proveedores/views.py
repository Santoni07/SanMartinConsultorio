from decimal import Decimal
import json



from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db import transaction

from django.utils import timezone

from caja.models import (
    MovimientoCaja,
    MedioPago,
    DetalleMedioPago,
    DetalleMovimientoCaja,
)



from core.utils import (
    mostrar_error,
    mostrar_exito,
    obtener_centro_activo,
)

from .forms import PagoLiquidacionProveedorForm

from .models import (
    Proveedor,
    LiquidacionProveedor,
    PagoLiquidacionProveedor,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from caja.models import DetalleMovimientoCaja
from caja.models import CajaDiaria

def obtener_centro_activo(request):

    centro_id = request.session.get("centro_id")

    if not centro_id:
        return None

    from core.models import CentroMedico

    try:
        return CentroMedico.objects.get(pk=centro_id)
    except CentroMedico.DoesNotExist:
        return None


def obtener_caja_abierta(centro_medico):

    return CajaDiaria.objects.filter(
        centro_medico=centro_medico,
        estado="ABIERTA",
    ).first()

@login_required
def proveedores_pendientes(request):

    proveedor_id = request.GET.get("proveedor")

    proveedores = (
        Proveedor.objects
        .filter(activo=True)
        .order_by("nombre")
    )

    detalles = DetalleMovimientoCaja.objects.none()

    proveedor = None

    total = Decimal("0.00")

    if proveedor_id:

        proveedor = Proveedor.objects.get(
            pk=proveedor_id
        )

        detalles = (

            DetalleMovimientoCaja.objects

            .filter(

                proveedor=proveedor,

                importe_proveedor__gt=0,

                liquidacion_proveedor__isnull=True,

            )

            .select_related(

                "movimiento",

                "movimiento__paciente",

                "concepto_facturacion",

            )

            .order_by(

                "fecha_prestacion",

                "id",

            )

        )

        total = (

            detalles.aggregate(

                total=Sum("importe_proveedor")

            )["total"]

            or Decimal("0.00")

        )

    return render(

        request,

        "proveedores/proveedores_pendientes.html",

        {

            "proveedores": proveedores,

            "proveedor": proveedor,

            "detalles": detalles,

            "total": total,

        },

    )
    
@login_required
def previsualizar_liquidacion_proveedor(request):

    proveedor_id = request.GET.get("proveedor")

    proveedor = get_object_or_404(
        Proveedor,
        pk=proveedor_id
    )

    detalles = (

        DetalleMovimientoCaja.objects

        .filter(

            proveedor=proveedor,

            importe_proveedor__gt=0,

            liquidacion_proveedor__isnull=True,

        )

        .select_related(

            "movimiento",
            "movimiento__paciente",
            "concepto_facturacion",

        )

        .order_by(

            "fecha_prestacion",
            "id",

        )

    )

    total = (

        detalles.aggregate(

            total=Sum("importe_proveedor")

        )["total"]

        or Decimal("0.00")

    )

    context = {

        "proveedor": proveedor,

        "detalles": detalles,

        "total": total,

    }

    return render(

        request,

        "proveedores/previsualizar_liquidacion.html",

        context,

    )
    
@login_required
@transaction.atomic
def generar_liquidacion_proveedor(request):

    if request.method != "POST":

        return redirect(
            "proveedores:proveedores_pendientes"
        )

    proveedor = get_object_or_404(

        Proveedor,

        pk=request.POST.get("proveedor")

    )

    detalles = (

        DetalleMovimientoCaja.objects

        .filter(

    proveedor=proveedor,

    importe_proveedor__gt=0,

    liquidacion_proveedor__isnull=True,

)

    )

    if not detalles.exists():

        messages.error(

            request,

            "No existen prestaciones pendientes."

        )

        return redirect(

            "proveedores:proveedores_pendientes"

        )

    total = (

        detalles.aggregate(

            total=Sum("importe_proveedor")

        )["total"]

        or Decimal("0.00")

    )

    liquidacion = LiquidacionProveedor.objects.create(

        proveedor=proveedor,

        total=total,

        generado_por=request.user,

    )

    detalles.update(

        liquidacion_proveedor=liquidacion

    )

    messages.success(

        request,

        "La liquidación fue generada correctamente."

    )

    return redirect(

        "proveedores:proveedores_pendientes"

    )
    
@login_required
def liquidaciones_pendientes_proveedor(request):

    liquidaciones = (

        LiquidacionProveedor.objects

        .select_related(
            "proveedor"
        )

        .exclude(
            estado="PAGADA"
        )

        .order_by(
            "-fecha_generacion"
        )

    )

    return render(

        request,

        "proveedores/liquidaciones_pendientes.html",

        {

            "liquidaciones": liquidaciones,

        },

    )
    
@login_required
@transaction.atomic
def registrar_pago_liquidacion_proveedor(
    request,
    liquidacion_id
):

    centro_medico = obtener_centro_activo(request)

    liquidacion = get_object_or_404(
        LiquidacionProveedor,
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
            "proveedores:liquidaciones_pendientes_proveedor"
        )

    if request.method == "POST":

        form = PagoLiquidacionProveedorForm(
            request.POST
        )

        if form.is_valid():

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
                    "proveedores/registrar_pago_liquidacion_proveedor.html",
                    {
                        "form": form,
                        "liquidacion": liquidacion,
                        "medios_pago": medios_pago,
                    }
                )

            medios = json.loads(
                medios_pago_json
            )

            importe = form.cleaned_data["importe"]

            if importe <= 0:

                mostrar_error(
                    request,
                    titulo="Importe inválido",
                    mensaje="El importe debe ser mayor a cero."
                )

                return redirect(
                    "proveedores:registrar_pago_liquidacion_proveedor",
                    liquidacion.id
                )

            if importe > liquidacion.saldo_pendiente:

                mostrar_error(
                    request,
                    titulo="Importe inválido",
                    mensaje="El importe supera el saldo pendiente."
                )

                return redirect(
                    "proveedores:registrar_pago_liquidacion_proveedor",
                    liquidacion.id
                )

            movimiento = MovimientoCaja.objects.create(

                caja=caja,

                centro_medico=centro_medico,

                tipo="EGRESO",

                importe=importe,

                concepto=(
                    f"Pago Proveedor - "
                     f"{liquidacion.proveedor.nombre}"
                ),

                observacion=form.cleaned_data[
                    "observacion"
                ],

                estado="ACTIVO",

                creado_por=request.user,

            )

            for item in medios:

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

            PagoLiquidacionProveedor.objects.create(

                liquidacion=liquidacion,

                movimiento_caja=movimiento,

                importe=importe,

                registrado_por=request.user,

            )

            liquidacion.total_pagado += importe

            liquidacion.cantidad_pagos += 1

            if liquidacion.saldo_pendiente <= 0:

                liquidacion.estado = "PAGADA"

                liquidacion.fecha_pago = timezone.now()

                liquidacion.pagado_por = request.user

            elif liquidacion.total_pagado > 0:

                liquidacion.estado = "PARCIAL"

            else:

                liquidacion.estado = "PENDIENTE"

            liquidacion.save()

            mostrar_exito(

                request,

                titulo="Pago registrado",

                mensaje="El pago del proveedor fue registrado correctamente.",

                icono="bi-wallet2",

                detalles=[

                    f"Proveedor: {liquidacion.proveedor}",

                    f"Importe pagado: ${importe}",

                    f"Saldo pendiente: ${liquidacion.saldo_pendiente}",

                    f"Estado: {liquidacion.get_estado_display()}",

                ]

            )

            return redirect(
                "proveedores:liquidaciones_pendientes_proveedor"
            )

    else:

        form = PagoLiquidacionProveedorForm()

    return render(

        request,

        "proveedores/registrar_pago_liquidacion_proveedor.html",

        {

            "form": form,

            "liquidacion": liquidacion,

            "medios_pago": medios_pago,

        }

    )
    
@login_required
def historial_liquidaciones_proveedor(request):

    proveedor_id = request.GET.get("proveedor")
    estado = request.GET.get("estado")

    liquidaciones = (
        LiquidacionProveedor.objects
        .select_related("proveedor")
        .order_by("-fecha_generacion")
    )

    if proveedor_id:
        liquidaciones = liquidaciones.filter(
            proveedor_id=proveedor_id
        )

    if estado:
        liquidaciones = liquidaciones.filter(
            estado=estado
        )

    proveedores = Proveedor.objects.filter(
        activo=True
    ).order_by("nombre")

    return render(
        request,
        "proveedores/historial_liquidaciones.html",
        {
            "liquidaciones": liquidaciones,
            "proveedores": proveedores,
            "proveedor_id": proveedor_id,
            "estado": estado,
        },
    )
    
@login_required
def detalle_liquidacion_proveedor(
    request,
    liquidacion_id
):

    liquidacion = get_object_or_404(
        LiquidacionProveedor,
        pk=liquidacion_id
    )

    detalles = (
        liquidacion.detalles
        .select_related(
            "movimiento",
            "movimiento__paciente"
        )
        .order_by(
            "fecha_prestacion"
        )
    )

    pagos = (

        PagoLiquidacionProveedor.objects

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

        .order_by(
            "-fecha"
        )

    )

    return render(

        request,

        "proveedores/detalle_liquidacion.html",

        {

            "liquidacion": liquidacion,

            "detalles": detalles,

            "pagos": pagos,

        },

    )