from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from .models import CajaDiaria, MovimientoCaja, HistorialMovimientoCaja
from .forms import (
    AperturaCajaForm,
    MovimientoCajaForm,
    CobroConsultaForm,
    AnularMovimientoCajaForm,
    CerrarCajaForm,
)
from core.models import CentroMedico, PerfilUsuario


def obtener_centro_activo(request):
    centro = getattr(request, 'centro_activo', None)

    if centro:
        return centro

    centro_id = request.session.get('centro_id')

    if centro_id:
        centro = CentroMedico.objects.filter(
            id=centro_id,
            activo=True
        ).first()

        if centro:
            return centro

    if request.user.is_authenticated:
        perfil = PerfilUsuario.objects.filter(
            user=request.user,
            activo=True
        ).first()

        if perfil and perfil.centro_principal:
            request.session['centro_id'] = perfil.centro_principal.id
            return perfil.centro_principal

    return CentroMedico.objects.filter(activo=True).first()


def obtener_caja_abierta(centro_medico):
    return CajaDiaria.objects.filter(
        centro_medico=centro_medico,
        fecha=timezone.localdate(),
        estado='ABIERTA'
    ).order_by('turno').first()


@login_required
def caja_home(request):
    centro_medico = obtener_centro_activo(request)

    if not centro_medico:
        messages.error(request, 'No hay una sede activa seleccionada.')
        return redirect('core:index')

    caja = obtener_caja_abierta(centro_medico)

    cajas = CajaDiaria.objects.filter(
        centro_medico=centro_medico
    ).order_by('-fecha')[:10]

    if caja:
        movimientos = MovimientoCaja.objects.filter(
            caja=caja,
            centro_medico=centro_medico
        ).order_by('-fecha_creacion')
    else:
        movimientos = MovimientoCaja.objects.none()

    return render(request, 'caja/caja_home.html', {
        'centro_medico': centro_medico,
        'caja': caja,
        'cajas': cajas,
        'movimientos': movimientos,
    })


@login_required
@transaction.atomic
def abrir_caja(request):

    centro_medico = obtener_centro_activo(request)

    if not centro_medico:
        messages.error(
            request,
            'No hay una sede activa seleccionada.'
        )
        return redirect('caja_home')

    if request.method == 'POST':

        form = AperturaCajaForm(request.POST)

        if form.is_valid():

            turno = form.cleaned_data['turno']

            caja_existente = CajaDiaria.objects.filter(
                centro_medico=centro_medico,
                fecha=timezone.localdate(),
                turno=turno
            ).first()

            if caja_existente:

                estado = (
                    'abierta'
                    if caja_existente.estado == 'ABIERTA'
                    else 'cerrada'
                )

                messages.warning(
                    request,
                    f'La caja del turno '
                    f'{caja_existente.get_turno_display()} '
                    f'ya fue creada hoy y actualmente se encuentra {estado}.'
                )

                return redirect('caja_home')

            caja = form.save(commit=False)

            caja.centro_medico = centro_medico
            caja.fecha = timezone.localdate()
            caja.abierta_por = request.user
            caja.estado = 'ABIERTA'

            caja.save()

            HistorialMovimientoCaja.objects.create(
                caja=caja,
                accion='APERTURA_CAJA',
                usuario=request.user,
                centro_medico=centro_medico,
                descripcion=(
                    f'Apertura de caja '
                    f'{caja.get_turno_display()} '
                    f'en {centro_medico.nombre}'
                ),
                datos_nuevos={
                    'fecha': str(caja.fecha),
                    'turno': caja.get_turno_display(),
                    'saldo_inicial': str(caja.saldo_inicial),
                    'observacion_apertura': caja.observacion_apertura,
                    'usuario': request.user.username,
                }
            )

            messages.success(
                request,
                f'Caja del turno '
                f'{caja.get_turno_display()} '
                f'abierta correctamente.'
            )

            return redirect('caja_home')

    else:

        form = AperturaCajaForm()

    return render(
        request,
        'caja/abrir_caja.html',
        {
            'form': form,
            'centro_medico': centro_medico,
        }
    )


@login_required
@transaction.atomic
def registrar_movimiento(request):
    centro_medico = obtener_centro_activo(request)

    if not centro_medico:
        messages.error(request, 'No hay una sede activa seleccionada.')
        return redirect('core:index')

    caja = obtener_caja_abierta(centro_medico)

    if not caja:
        messages.error(request, 'Primero debe abrir la caja de esta sede.')
        return redirect('abrir_caja')

    if request.method == 'POST':
        form = MovimientoCajaForm(request.POST)

        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.caja = caja
            movimiento.centro_medico = centro_medico
            movimiento.creado_por = request.user
            movimiento.estado = 'ACTIVO'
            movimiento.save()

            HistorialMovimientoCaja.objects.create(
                caja=caja,
                movimiento=movimiento,
                accion='CREADO',
                usuario=request.user,
                centro_medico=centro_medico,
                descripcion=f'{movimiento.tipo} registrado por {request.user}.',
                datos_nuevos={
                    'tipo': movimiento.tipo,
                    'medio_pago': movimiento.medio_pago.nombre,
                    'importe': str(movimiento.importe),
                    'concepto': movimiento.concepto,
                    'observacion': movimiento.observacion,
                }
            )

            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('caja_home')
    else:
        form = MovimientoCajaForm()

    return render(request, 'caja/registrar_movimiento.html', {
        'form': form,
        'caja': caja,
        'centro_medico': centro_medico,
    })


@login_required
@transaction.atomic
def registrar_cobro(request):
    centro_medico = obtener_centro_activo(request)

    if not centro_medico:
        messages.error(request, 'No hay una sede activa seleccionada.')
        return redirect('caja_home')

    caja = obtener_caja_abierta(centro_medico)

    if not caja:
        messages.error(request, 'Primero debe abrir la caja de esta sede.')
        return redirect('abrir_caja')

    if request.method == 'POST':
        form = CobroConsultaForm(
            request.POST,
            centro_medico=centro_medico
        )

        if form.is_valid():
            turno = form.cleaned_data['turno']

            movimiento = form.save(commit=False)

            movimiento.caja = caja
            movimiento.centro_medico = centro_medico
            movimiento.turno = turno
            movimiento.paciente = turno.paciente
            movimiento.tipo = 'INGRESO'
            movimiento.creado_por = request.user
            movimiento.estado = 'ACTIVO'

            # =====================================
            # CONCEPTO AUTOMÁTICO
            # =====================================

            movimiento.concepto = (
                movimiento.concepto_facturacion.nombre
            )

            # =====================================
            # CÁLCULOS ECONÓMICOS
            # =====================================

            movimiento.importe_bruto = movimiento.importe

            movimiento.importe_iva = (
                movimiento.importe *
                movimiento.concepto_facturacion.porcentaje_iva
            ) / 100

            movimiento.importe_neto = (
                movimiento.importe_bruto
                - movimiento.importe_iva
                - movimiento.retencion_monto
            )

            movimiento.importe_medico = (
                movimiento.importe_neto *
                movimiento.concepto_facturacion.porcentaje_medico
            ) / 100

            movimiento.importe_consultorio = (
                movimiento.importe_neto *
                movimiento.concepto_facturacion.porcentaje_consultorio
            ) / 100

            movimiento.save()

            HistorialMovimientoCaja.objects.create(
                caja=caja,
                movimiento=movimiento,
                accion='CREADO',
                usuario=request.user,
                centro_medico=centro_medico,
                descripcion=f'Cobro asociado al turno #{turno.id}.',
                datos_nuevos={
                    'turno_id': turno.id,
                    'paciente': str(turno.paciente),
                    'medico': str(turno.medico),
                    'fecha_turno': str(turno.fecha),
                    'hora_turno': str(turno.hora),
                    'tipo': movimiento.tipo,
                    'medio_pago': movimiento.medio_pago.nombre,
                    'importe': str(movimiento.importe),
                    'concepto': movimiento.concepto,
                    'observacion': movimiento.observacion,
                    'concepto_facturacion':
                        movimiento.concepto_facturacion.nombre,

                    'importe_bruto':
                        str(movimiento.importe_bruto),

                    'importe_iva':
                        str(movimiento.importe_iva),

                    'retencion':
                        str(movimiento.retencion_monto),

                    'importe_neto':
                        str(movimiento.importe_neto),

                    'importe_medico':
                        str(movimiento.importe_medico),

                    'importe_consultorio':
                        str(movimiento.importe_consultorio),
                                    }
            )

            messages.success(request, 'Cobro asociado al turno correctamente.')
            return redirect('caja_home')
    else:
        form = CobroConsultaForm(
            centro_medico=centro_medico
        )

    return render(request, 'caja/registrar_cobro.html', {
        'form': form,
        'caja': caja,
        'centro_medico': centro_medico,
    })

@login_required
@transaction.atomic
def anular_movimiento(request, movimiento_id):
    centro_medico = obtener_centro_activo(request)

    movimiento = get_object_or_404(
        MovimientoCaja,
        id=movimiento_id,
        centro_medico=centro_medico,
        estado='ACTIVO'
    )

    if movimiento.caja.estado == 'CERRADA':
        messages.error(request, 'No se puede anular un movimiento de una caja cerrada.')
        return redirect('caja_home')

    if request.method == 'POST':
        form = AnularMovimientoCajaForm(request.POST)

        if form.is_valid():
            motivo = form.cleaned_data['motivo_anulacion']

            datos_anteriores = {
                'estado': movimiento.estado,
                'importe': str(movimiento.importe),
                'tipo': movimiento.tipo,
                'medio_pago': movimiento.medio_pago.nombre,
                'concepto': movimiento.concepto,
            }

            movimiento.anular(
                usuario=request.user,
                motivo=motivo
            )

            HistorialMovimientoCaja.objects.create(
                caja=movimiento.caja,
                movimiento=movimiento,
                accion='ANULADO',
                usuario=request.user,
                centro_medico=centro_medico,
                descripcion=f'Movimiento anulado. Motivo: {motivo}',
                datos_anteriores=datos_anteriores,
                datos_nuevos={
                    'estado': movimiento.estado,
                    'anulado_por': request.user.username,
                    'motivo_anulacion': motivo,
                }
            )

            messages.success(request, 'Movimiento anulado correctamente.')
            return redirect('caja_home')
    else:
        form = AnularMovimientoCajaForm()

    return render(request, 'caja/anular_movimiento.html', {
        'form': form,
        'movimiento': movimiento,
        'centro_medico': centro_medico,
    })


@login_required
@transaction.atomic
def cerrar_caja(request):
    centro_medico = obtener_centro_activo(request)

    if not centro_medico:
        messages.error(request, 'No hay una sede activa seleccionada.')
        return redirect('caja_home')

    caja = obtener_caja_abierta(centro_medico)

    if not caja:
        messages.error(request, 'No hay caja abierta para cerrar.')
        return redirect('caja_home')

    movimientos = MovimientoCaja.objects.filter(
        caja=caja,
        centro_medico=centro_medico,
        estado='ACTIVO'
    ).select_related(
        'medio_pago',
        'paciente',
        'turno',
        'creado_por'
    ).order_by('fecha_creacion')

    resumen_medios = movimientos.values(
        'medio_pago__nombre',
        'tipo'
    ).annotate(
        total=Sum('importe')
    ).order_by('medio_pago__nombre', 'tipo')

    total_ingresos = movimientos.filter(
        tipo='INGRESO'
    ).aggregate(
        total=Sum('importe')
    )['total'] or 0

    total_egresos = movimientos.filter(
        tipo='EGRESO'
    ).aggregate(
        total=Sum('importe')
    )['total'] or 0

    saldo_final = caja.saldo_inicial + total_ingresos - total_egresos

    if request.method == 'POST':
        form = CerrarCajaForm(request.POST, instance=caja)

        if form.is_valid():
            caja = form.save(commit=False)
            caja.estado = 'CERRADA'
            caja.cerrada_por = request.user
            caja.fecha_cierre = timezone.now()
            caja.save()

            HistorialMovimientoCaja.objects.create(
                caja=caja,
                accion='CIERRE_CAJA',
                usuario=request.user,
                centro_medico=centro_medico,
                descripcion=(
                    f'Cierre de caja {caja.get_turno_display()} '
                    f'de {centro_medico.nombre}.'
                ),
                datos_nuevos={
                    'fecha': str(caja.fecha),
                    'turno': caja.get_turno_display(),
                    'saldo_inicial': str(caja.saldo_inicial),
                    'total_ingresos': str(total_ingresos),
                    'total_egresos': str(total_egresos),
                    'saldo_final': str(saldo_final),
                    'observacion_cierre': caja.observacion_cierre,
                    'cerrada_por': request.user.username,
                }
            )

            messages.success(
                request,
                f'Caja del turno {caja.get_turno_display()} cerrada correctamente.'
            )
            return redirect('caja_home')
    else:
        form = CerrarCajaForm(instance=caja)

    efectivo_rendir = movimientos.filter(
        tipo='INGRESO',
        medio_pago__nombre='Efectivo'
    ).aggregate(
        total=Sum('importe')
    )['total'] or 0

    efectivo_egresos = movimientos.filter(
        tipo='EGRESO',
        medio_pago__nombre='Efectivo'
    ).aggregate(
        total=Sum('importe')
    )['total'] or 0

    efectivo_rendir = (
        caja.saldo_inicial +
        efectivo_rendir -
        efectivo_egresos
    )
    return render(request, 'caja/cerrar_caja.html', {
        'form': form,
        'caja': caja,
        'centro_medico': centro_medico,
        'movimientos': movimientos,
        'resumen_medios': resumen_medios,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'efectivo_rendir': efectivo_rendir,
        'saldo_final': saldo_final,
    })



    centro_medico = obtener_centro_activo(request)

    if not centro_medico:
        messages.error(request, 'No hay una sede activa seleccionada.')
        return redirect('core:index')

    caja = obtener_caja_abierta(centro_medico)

    if not caja:
        messages.error(request, 'No hay caja abierta para cerrar.')
        return redirect('caja_home')

    if request.method == 'POST':
        form = CerrarCajaForm(request.POST, instance=caja)

        if form.is_valid():
            caja = form.save(commit=False)
            caja.estado = 'CERRADA'
            caja.cerrada_por = request.user
            caja.fecha_cierre = timezone.now()
            caja.save()

            HistorialMovimientoCaja.objects.create(
                caja=caja,
                accion='CIERRE_CAJA',
                usuario=request.user,
                centro_medico=centro_medico,
                descripcion=f'Cierre de caja de {centro_medico}.',
                datos_nuevos={
                    'saldo_inicial': str(caja.saldo_inicial),
                    'total_ingresos': str(caja.total_ingresos),
                    'total_egresos': str(caja.total_egresos),
                    'saldo_final': str(caja.saldo_final),
                    'observacion_cierre': caja.observacion_cierre,
                }
            )

            messages.success(request, 'Caja cerrada correctamente.')
            return redirect('caja_home')
    else:
        form = CerrarCajaForm(instance=caja)

    return render(request, 'caja/cerrar_caja.html', {
        'form': form,
        'caja': caja,
        'centro_medico': centro_medico,
    })