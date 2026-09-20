from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404,redirect
from django.utils import timezone
from django.contrib import messages
from django.db import transaction

from ..models import (
    ObraSocial,
    DetalleMasterObraSocial,
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
            "prestaciones_observadas",
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
            "gestionar_prestacion_observada",
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
    # VALIDACIONES
    # ======================================================

    if detalle.estado != "DEBITO_PARCIAL":

        messages.error(
            request,
            "Esta prestación no corresponde a un débito parcial."
        )

        return redirect(
            "gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    if detalle.importe_reconocido is None:

        messages.error(
            request,
            "La prestación no tiene un importe reconocido."
        )

        return redirect(
            "gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    if detalle.importe_reconocido < 0:

        messages.error(
            request,
            "El importe reconocido no puede ser negativo."
        )

        return redirect(
            "gestionar_prestacion_observada",
            detalle_id=detalle.id
        )

    if detalle.importe_reconocido > detalle.importe_presentado:

        messages.error(
            request,
            "El importe reconocido no puede superar el importe presentado."
        )

        return redirect(
            "gestionar_prestacion_observada",
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