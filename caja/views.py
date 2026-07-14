from django.shortcuts import render, redirect, get_object_or_404
from .services import CierreCajaService

from .pdf.cierre_caja import generar_pdf_cierre
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from .models import CajaDiaria, MovimientoCaja, HistorialMovimientoCaja,    MedioPago, ConceptoFacturacion, DetalleMovimientoCaja,DetalleMedioPago
from .forms import (
    AperturaCajaForm,
    MovimientoCajaForm,
    CobroConsultaForm,
    AnularMovimientoCajaForm,
    CerrarCajaForm,
)
from core.models import CentroMedico, PerfilUsuario
import json
from django.http import HttpResponse

from decimal import Decimal

from .calculos import calcular_detalle
from core.utils import mostrar_exito
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

def validar_permiso_caja(request):

    perfil = request.user.perfilusuario
    centro = obtener_centro_activo(request)

    return not (
        perfil.rol == 'RECEPCION'
        and centro != perfil.centro_principal
    )
def obtener_caja_abierta(centro_medico):
    return CajaDiaria.objects.filter(
        centro_medico=centro_medico,
        fecha=timezone.localdate(),
        estado='ABIERTA'
    ).order_by('turno').first()


@login_required
def caja_home(request):
    centro_medico = obtener_centro_activo(request)
    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:ver_disponibilidad')

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
    ).prefetch_related(
    "detalles",
    "detalles_medios_pago__medio_pago"

    ).order_by("-fecha_creacion")
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
    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:ver_disponibilidad')

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

            mostrar_exito(

                request,

                titulo="Caja abierta",

                mensaje="La caja se abrió correctamente.",

                icono="bi-safe",

                detalles=[

                    f"Sede: {centro_medico.nombre}",

                    f"Turno: {caja.get_turno_display()}",

                    f"Saldo inicial: ${caja.saldo_inicial}",

                ],

            )

            return redirect("caja_home")

            

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

    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:ver_disponibilidad')

    if not centro_medico:

        messages.error(
            request,
            'No hay una sede activa seleccionada.'
        )

        return redirect('core:index')

    caja = obtener_caja_abierta(centro_medico)

    if not caja:

        messages.error(
            request,
            'Primero debe abrir la caja de esta sede.'
        )

        return redirect('abrir_caja')

    # =====================================
    # MEDIOS DE PAGO DISPONIBLES
    # =====================================

    medios_pago_disponibles = MedioPago.objects.filter(
        activo=True
    ).order_by("nombre")

    if request.method == 'POST':

        print("POST RECIBIDO")

        form = MovimientoCajaForm(request.POST)

        if form.is_valid():

            print("FORM VALIDO")

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
                    "caja/registrar_movimiento.html",
                    {
                        "form": form,
                        "caja": caja,
                        "centro_medico": centro_medico,
                        "medios_pago": medios_pago_disponibles,
                    },
                )

            try:

                medios_pago_data = json.loads(
                    medios_pago_json
                )

            except json.JSONDecodeError:

                messages.error(
                    request,
                    "Error al procesar los medios de pago."
                )

                return render(
                    request,
                    "caja/registrar_movimiento.html",
                    {
                        "form": form,
                        "caja": caja,
                        "centro_medico": centro_medico,
                        "medios_pago": medios_pago_disponibles,
                    },
                )

            movimiento = form.save(commit=False)

            print("ANTES SAVE")

            movimiento.caja = caja
            movimiento.centro_medico = centro_medico
            movimiento.creado_por = request.user
            movimiento.estado = "ACTIVO"

            movimiento.save()

            print("MOVIMIENTO GUARDADO")

            # =====================================
            # GUARDAR DETALLE MEDIOS DE PAGO
            # =====================================

            for item in medios_pago_data:

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

            HistorialMovimientoCaja.objects.create(

                caja=caja,

                movimiento=movimiento,

                accion="CREADO",

                usuario=request.user,

                centro_medico=centro_medico,

                descripcion=f"{movimiento.tipo} registrado por {request.user}.",

                datos_nuevos={

                    "tipo": movimiento.tipo,

                    "importe": str(movimiento.importe),

                    "concepto": movimiento.concepto,

                    "observacion": movimiento.observacion,

                }

            )

            print("HISTORIAL GUARDADO")

            

            mostrar_exito(

                request,

                titulo="Movimiento registrado",

                mensaje="El movimiento fue registrado correctamente.",

                icono="bi-arrow-left-right",

                detalles=[

                    f"Concepto: {movimiento.concepto}",

                    f"Importe: ${movimiento.importe}",

                ],

            )

            return redirect("caja_home")

        else:

            print("FORM INVALIDO")
            print(form.errors)

    else:

        form = MovimientoCajaForm()

    return render(
        request,
        "caja/registrar_movimiento.html",
        {
            "form": form,
            "caja": caja,
            "centro_medico": centro_medico,
            "medios_pago": medios_pago_disponibles,
        },
    )

@login_required
@transaction.atomic
def registrar_cobro(request):

    centro_medico = obtener_centro_activo(request)

    if not validar_permiso_caja(request):
        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )
        return redirect('turnos:ver_disponibilidad')

    if not centro_medico:
        messages.error(
            request,
            'No hay una sede activa seleccionada.'
        )
        return redirect('caja_home')

    caja = obtener_caja_abierta(centro_medico)
        # =====================================
    # MEDIOS DE PAGO
    # =====================================

    medios_pago = MedioPago.objects.filter(
        activo=True
    ).order_by("nombre")

    if not caja:
        messages.error(
            request,
            'Primero debe abrir la caja de esta sede.'
        )
        return redirect('abrir_caja')

    if request.method == 'POST':

        form = CobroConsultaForm(
            request.POST,
            centro_medico=centro_medico
        )
        print("=" * 80)
        print("FORM ES VÁLIDO:", form.is_valid())
        if not form.is_valid():
                print(form.errors)

        if form.is_valid():
            
            
            
            

            print("=" * 80)

            turno = form.cleaned_data["turno"]

            # =====================================
            # LEER DETALLES
            # =====================================

            detalles_json = request.POST.get("detalles_json")

            if not detalles_json:

                messages.error(
                    request,
                    "Debe agregar al menos una prestación."
                )

                return render(
                    request,
                    "caja/registrar_cobro.html",
                    {
                        "form": form,
                        "caja": caja,
                        "centro_medico": centro_medico,
                         "medios_pago": medios_pago,
                    },
                )

            try:

                detalles = json.loads(detalles_json)

            except json.JSONDecodeError:

                messages.error(
                    request,
                    "Error al procesar las prestaciones."
                )

                return render(
                    request,
                    "caja/registrar_cobro.html",
                    {
                        "form": form,
                        "caja": caja,
                        "centro_medico": centro_medico,
                        "medios_pago": medios_pago,
                    },
                )

            if not detalles:

                messages.error(
                    request,
                    "Debe agregar al menos una prestación."
                )

                return render(
                    request,
                    "caja/registrar_cobro.html",
                    {
                        "form": form,
                        "caja": caja,
                        "centro_medico": centro_medico,
                        "medios_pago": medios_pago,
                    },
                )
                
            
            total_prestaciones = Decimal("0")

            for detalle in detalles:

                cantidad = Decimal(str(detalle.get("cantidad", 1)))
                importe = Decimal(str(detalle.get("importe", 0)))

                total_prestaciones += cantidad * importe
            
            #=====================================
            # LEER MEDIOS DE PAGO
            #=====================================

            medios_pago_json = request.POST.get("medios_pago_json")

            if total_prestaciones > Decimal("0"):

                if not medios_pago_json:

                    messages.error(
                        request,
                        "Debe agregar al menos un medio de pago."
                    )

                    return render(
                        request,
                        "caja/registrar_cobro.html",
                        {
                            "form": form,
                            "caja": caja,
                            "centro_medico": centro_medico,
                            "medios_pago": medios_pago,
                        },
                    )

                try:
                    medios_pago_data = json.loads(medios_pago_json)

                except json.JSONDecodeError:

                    messages.error(
                        request,
                        "Error al procesar los medios de pago."
                    )

                    return render(
                        request,
                        "caja/registrar_cobro.html",
                        {
                            "form": form,
                            "caja": caja,
                            "centro_medico": centro_medico,
                            "medios_pago": medios_pago,
                        },
                    )

            else:
                medios_pago_data = []
                
            # =====================================
            # VALIDAR TOTALES DE COBRO
            # =====================================

            total_prestaciones = Decimal("0")

            for detalle in detalles:

                cantidad = Decimal(
                    str(detalle.get("cantidad", 1))
                )

                importe = Decimal(
                    str(detalle.get("importe", 0))
                )

                total_prestaciones += (
                    cantidad * importe
                )

            total_medios = Decimal("0")

            for medio in medios_pago_data:

                total_medios += Decimal(
                    str(medio.get("importe", 0))
                )

            if abs(total_prestaciones - total_medios) > Decimal("0.01"):

                diferencia = (
                    total_prestaciones -
                    total_medios
                )

                if diferencia > 0:

                    messages.error(

                        request,

                        f"El cobro no puede registrarse. "
                        f"Faltan cobrar ${diferencia:.2f}."

                    )

                else:

                    messages.error(

                        request,

                        f"El cobro no puede registrarse. "
                        f"Existe un excedente de ${abs(diferencia):.2f}."

                    )

                return render(

                    request,

                    "caja/registrar_cobro.html",

                    {
                        "form": form,
                        "caja": caja,
                        "centro_medico": centro_medico,
                        "medios_pago": medios_pago,
                    },

                )
            
            # =====================================
            # CREAR MOVIMIENTO
            # =====================================

            movimiento = form.save(commit=False)

            movimiento.caja = caja
            movimiento.centro_medico = centro_medico
            movimiento.turno = turno
            movimiento.paciente = turno.paciente
            movimiento.tipo = "INGRESO"
            movimiento.creado_por = request.user
            movimiento.estado = "ACTIVO"

            # Temporalmente dejamos estos valores.
            # Después los reemplazaremos por los
            # totales calculados.

            movimiento.concepto = "Cobro de prestaciones"
            movimiento.importe = 0
            movimiento.importe_bruto = 0
            movimiento.importe_iva = 0
            movimiento.importe_neto = 0
            movimiento.importe_medico = 0
            movimiento.importe_consultorio = 0

            movimiento.save()
            
            # =====================================
            # TOTALES DEL MOVIMIENTO
            # =====================================

            total_importe = Decimal("0")
            total_bruto = Decimal("0")
            total_iva = Decimal("0")
            total_neto = Decimal("0")
            total_medico = Decimal("0")
            total_consultorio = Decimal("0")

            orden = 1

            # =====================================
            # RECORRER DETALLES
            # =====================================

            for item in detalles:

                concepto = ConceptoFacturacion.objects.select_related(
                    "nomenclador"
                ).get(
                    pk=item["id"]
                )

                cantidad = int(item["cantidad"])
                
                detalle = DetalleMovimientoCaja(

                    movimiento=movimiento,

                    concepto_facturacion=concepto,

                    fecha_prestacion=turno.fecha,

                    cantidad=cantidad,

                    orden=orden,

                )

                detalle.save()

                

                


            if len(detalles) == 1:

                movimiento.concepto_facturacion = concepto

                movimiento.concepto = (
                    f"{concepto.nomenclador.codigo} - "
                    f"{concepto.nomenclador.descripcion}"
                )

            else:

                movimiento.concepto_facturacion = None

                movimiento.concepto = (
                    f"{len(detalles)} prestaciones"
                )

            movimiento.save(
                update_fields=[
                    "concepto",
                    "concepto_facturacion",
                ]
            )
            for item in medios_pago_data:

                medio = MedioPago.objects.get(
                    pk=item["medio"]
                )

                DetalleMedioPago.objects.create(
                    movimiento=movimiento,
                    medio_pago=medio,
                    importe=Decimal(str(item["importe"]))
                )
           
            
            mostrar_exito(

            request,

            titulo="Cobro registrado",

            mensaje="El cobro fue registrado correctamente.",

            icono="bi-cash-coin",

            detalles=[

                f"Paciente: {movimiento.paciente}",

                f"Prestaciones: {len(detalles)}",

                f"Importe: ${movimiento.importe}",

            ],

        )

        return redirect("caja_home")

            
                        
            
    else:

        form = CobroConsultaForm(
            centro_medico=centro_medico
        )

 
    return render(
        request,
        'caja/registrar_cobro.html',
        {
            'form': form,
            'caja': caja,
            'centro_medico': centro_medico,
            "medios_pago": medios_pago,
        }
    )

@login_required
@transaction.atomic
def anular_movimiento(request, movimiento_id):

    centro_medico = obtener_centro_activo(request)

    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:ver_disponibilidad')

    movimiento = get_object_or_404(
        MovimientoCaja,
        id=movimiento_id,
        centro_medico=centro_medico,
        estado='ACTIVO'
    )

    if movimiento.caja.estado == 'CERRADA':

        messages.error(
            request,
            'No se puede anular un movimiento de una caja cerrada.'
        )

        return redirect('caja_home')

    if request.method == 'POST':

        form = AnularMovimientoCajaForm(request.POST)

        if form.is_valid():

            motivo = form.cleaned_data['motivo_anulacion']

            datos_anteriores = {

                "estado": movimiento.estado,

                "importe": str(movimiento.importe),

                "tipo": movimiento.tipo,

                "concepto": movimiento.concepto,

                "medios_pago": [

                    {

                        "medio": detalle.medio_pago.nombre,

                        "importe": str(detalle.importe),

                    }

                    for detalle in movimiento.detalles_medios_pago.all()

                ],

            }

            # =====================================
            # ANULAR MOVIMIENTO
            # =====================================

            movimiento.anular(
                usuario=request.user,
                motivo=motivo
            )

            # =====================================
            # SI ES UN COBRO, EL TURNO VUELVE A
            # PENDIENTE
            # =====================================

            if movimiento.turno:

                movimiento.turno.estado = "PENDIENTE"

                movimiento.turno.save(
                    update_fields=["estado"]
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

           

            mostrar_exito(

            request,

            titulo="Movimiento anulado",

            mensaje="El movimiento fue anulado correctamente.",

            icono="bi-trash",

            detalles=[

                f"Concepto: {movimiento.concepto}",

                f"Importe: ${movimiento.importe}",

            ],

        )

        return redirect("caja_home")

    else:

        form = AnularMovimientoCajaForm()

    return render(
        request,
        'caja/anular_movimiento.html',
        {
            'form': form,
            'movimiento': movimiento,
            'centro_medico': centro_medico,
        }
    )
@login_required
@transaction.atomic
def cerrar_caja(request):
    centro_medico = obtener_centro_activo(request)
    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:ver_disponibilidad')

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
        'paciente',
        'turno',
        'creado_por'
    ).prefetch_related(
        'detalles',
        'detalles_medios_pago__medio_pago'
    ).order_by('fecha_creacion')
    from collections import defaultdict

    resumen_medios = defaultdict(Decimal)

    for movimiento in movimientos:

        signo = Decimal("1")

        if movimiento.tipo == "EGRESO":
            signo = Decimal("-1")

        for detalle in movimiento.detalles_medios_pago.all():

            resumen_medios[
                detalle.medio_pago.nombre
            ] += signo * detalle.importe

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

            mostrar_exito(

            request,

            titulo="Caja cerrada",

            mensaje="La caja se cerró correctamente.",

            icono="bi-safe2-fill",

            detalles=[

                f"Sede: {centro_medico.nombre}",

                f"Turno: {caja.get_turno_display()}",

                f"Ingresos: ${total_ingresos}",

                f"Egresos: ${total_egresos}",

                f"Saldo Final: ${saldo_final}",

            ],

        )

        return redirect("caja_home")
    else:
        form = CerrarCajaForm(instance=caja)

    efectivo_rendir = (
        caja.saldo_inicial +
        resumen_medios.get(
            "Efectivo",
            Decimal("0")
        )
    )
    return render(request, 'caja/cerrar_caja.html', {
        'form': form,
        'caja': caja,
        'centro_medico': centro_medico,
        'movimientos': movimientos,
        'resumen_medios': resumen_medios.items(),
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'efectivo_rendir': efectivo_rendir,
        'saldo_final': saldo_final,
    })

@login_required
def detalle_caja(request, caja_id):

    centro_medico = obtener_centro_activo(request)

    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:ver_disponibilidad')

    caja = get_object_or_404(
        CajaDiaria,
        pk=caja_id,
        centro_medico=centro_medico
    )

    movimientos = (
        MovimientoCaja.objects.filter(
            caja=caja,
            estado="ACTIVO"
        )
        .select_related(
            "paciente",
            "creado_por",
        )
        .prefetch_related(
            "detalles",
            "detalles_medios_pago__medio_pago",
        )
        .order_by("fecha_creacion")
    )

    total_ingresos = (
        movimientos.filter(
            tipo='INGRESO'
        ).aggregate(
            total=Sum('importe')
        )['total'] or 0
    )

    total_egresos = (
        movimientos.filter(
            tipo='EGRESO'
        ).aggregate(
            total=Sum('importe')
        )['total'] or 0
    )

    resultado = total_ingresos - total_egresos

    medios_pago = (
        DetalleMedioPago.objects.filter(
            movimiento__caja=caja,
            movimiento__estado="ACTIVO",
        )
        .values("medio_pago__nombre")
        .annotate(
            total=Sum("importe")
        )
        .order_by("medio_pago__nombre")
    )

    return render(
        request,
        'caja/detalle_caja.html',
        {
            'caja': caja,
            'movimientos': movimientos,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'resultado': resultado,
            'medios_pago': medios_pago,
        }
    )


@login_required
def cajas_cerradas(request):

    
    centro_medico = obtener_centro_activo(request)
    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect('turnos:turnos:ver_disponibilidad')

    fecha = request.GET.get('fecha')

    cajas = CajaDiaria.objects.filter(
        centro_medico=centro_medico,
        estado='CERRADA'
    )

    if fecha:

        cajas = cajas.filter(
            fecha=fecha
        )

    cajas = cajas.order_by(
        '-fecha',
        '-id'
    )

    if not fecha:
        cajas = cajas[:5]

    return render(
        request,
        'caja/cajas_cerradas.html',
        {
            'cajas': cajas,
            'centro_medico': centro_medico,
            'fecha': fecha,
        }
    )


from django.http import JsonResponse

@login_required
def ajax_prestaciones(request):

    tipo = request.GET.get("tipo")

    print("TIPO RECIBIDO:", tipo)

    prestaciones = ConceptoFacturacion.objects.filter(
        activo=True,
        tipo_concepto=tipo
    ).select_related(
        "nomenclador"
    ).order_by(
        "nomenclador__descripcion"
    )

    print("CANTIDAD:", prestaciones.count())

    data = []

    for p in prestaciones:

        print(
            p.id,
            p.nomenclador
        )

        if not p.nomenclador:
            continue

        data.append({
            "id": p.id,
            "nombre": f"{p.nomenclador.codigo} - {p.nomenclador.descripcion}"
        })

    return JsonResponse(data, safe=False)
@login_required
def ajax_importe_prestacion(request):

    concepto_id = request.GET.get("concepto_id")

    if not concepto_id:
        return JsonResponse({"importe": 0})

    try:

        concepto = ConceptoFacturacion.objects.get(
            pk=concepto_id,
            activo=True
        )

        return JsonResponse({
            "importe": float(concepto.importe_particular),
            "codigo": concepto.nomenclador.codigo,
            "descripcion": concepto.nomenclador.descripcion,
        })

    except ConceptoFacturacion.DoesNotExist:

        return JsonResponse({
            "importe": 0
        })
        
@login_required
def pdf_cierre_caja(request, caja_id):

    caja = get_object_or_404(
        CajaDiaria,
        pk=caja_id,
    )

    service = CierreCajaService(
        caja
    )

    datos = service.obtener_datos()

    pdf = generar_pdf_cierre(
        datos
    )

    response = HttpResponse(
        pdf,
        content_type="application/pdf",
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; '
        f'filename="CierreCaja_{caja.id}.pdf"'
    )

    return response