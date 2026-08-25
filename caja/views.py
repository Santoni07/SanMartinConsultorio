from django.shortcuts import render, redirect, get_object_or_404
from .services import CierreCajaService
from turnos.models import Turnos
from .pdf.cierre_caja import generar_pdf_cierre
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseBadRequest
from honorarios.models import PagoLiquidacionMedica
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
from obrasocial.models import PrestacionPlan
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

    # =====================================
    # VALIDACIONES DE CAJA
    # =====================================

    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect(
            'turnos:ver_disponibilidad'
        )

    if not centro_medico:

        messages.error(
            request,
            'No hay una sede activa seleccionada.'
        )

        return redirect(
            'caja_home'
        )

    caja = obtener_caja_abierta(
        centro_medico
    )

    # =====================================
    # MEDIOS DE PAGO
    # =====================================

    medios_pago = MedioPago.objects.filter(
        activo=True
    ).order_by(
        "nombre"
    )

    if not caja:

        messages.error(
            request,
            'Primero debe abrir la caja de esta sede.'
        )

        return redirect(
            'abrir_caja'
        )

    # =====================================
    # POST
    # =====================================

    if request.method == 'POST':

        form = CobroConsultaForm(
            request.POST,
            centro_medico=centro_medico
        )

        print("=" * 80)

        print(
            "FORM ES VÁLIDO:",
            form.is_valid()
        )

        if not form.is_valid():
            print(form.errors)

        if form.is_valid():

            print("=" * 80)

            turno = form.cleaned_data[
                "turno"
            ]

            # =====================================
            # LEER DETALLES
            # =====================================

            detalles_json = request.POST.get(
                "detalles_json"
            )

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

                detalles = json.loads(
                    detalles_json
                )

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

            # =====================================
            # CALCULAR VALOR DE PRESTACIONES
            # Y MONTO A COBRAR AL PACIENTE
            # =====================================

            total_prestaciones = Decimal(
                "0.00"
            )

            total_a_cobrar_paciente = Decimal(
                "0.00"
            )

            for detalle in detalles:

                cantidad = Decimal(
                    str(
                        detalle.get(
                            "cantidad",
                            1
                        )
                    )
                )

                importe = Decimal(
                    str(
                        detalle.get(
                            "importe",
                            0
                        )
                    )
                )

                subtotal = (
                    cantidad * importe
                )

                # Valor económico de la prestación
                total_prestaciones += subtotal

                origen = detalle.get(
                    "origen"
                )

                # =================================
                # PARTICULAR
                # =================================

                if origen == "PARTICULAR":

                    # Particular lo paga
                    # completamente el paciente.

                    total_a_cobrar_paciente += (
                        subtotal
                    )

                # =================================
                # OBRA SOCIAL
                # =================================

                elif origen == "OBRA_SOCIAL":

                    # =================================
                    # OBTENER PRESTACIÓN DEL CONVENIO
                    # =================================

                    prestacion = (
                        PrestacionPlan.objects
                        .filter(
                            pk=detalle.get("id"),
                            estado="ACTIVA",
                        )
                        .first()
                    )

                    if not prestacion:

                        raise ValueError(
                            "La prestación de Obra Social no existe "
                            "o no se encuentra activa."
                        )

                    # =================================
                    # COSEGURO
                    # =================================
                    #
                    # El coseguro lo paga el paciente.
                    # =================================

                    if prestacion.tiene_coseguro:

                        coseguro = Decimal(
                            str(
                                prestacion.importe_coseguro
                                or 0
                            )
                        )

                        total_a_cobrar_paciente += (
                            cantidad * coseguro
                        )

                    # =================================
                    # COPAGO
                    # =================================
                    #
                    # El copago también lo paga el
                    # paciente.
                    #
                    # IMPORTANTE:
                    # NO se descuenta del importe que
                    # posteriormente paga la OS.
                    # =================================

                    if prestacion.tiene_copago:

                        copago = Decimal(
                            str(
                                prestacion.importe_copago
                                or 0
                            )
                        )

                        total_a_cobrar_paciente += (
                            cantidad * copago
                        )

                else:

                    raise ValueError(
                        "Origen de prestación inválido."
                    )

            # =====================================
            # LEER MEDIOS DE PAGO
            # =====================================

            medios_pago_json = request.POST.get(
                "medios_pago_json"
            )

            # Solamente exigimos medios de pago
            # cuando realmente el paciente
            # tiene algo que pagar.
            #
            # Puede ser:
            #
            # - Particular
            # - Coseguro
            # - Copago

            if (
                total_a_cobrar_paciente
                > Decimal("0.00")
            ):

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
                        "caja/registrar_cobro.html",
                        {
                            "form": form,
                            "caja": caja,
                            "centro_medico": centro_medico,
                            "medios_pago": medios_pago,
                        },
                    )

            else:

                # Obra Social sin coseguro ni copago:
                # no existe dinero recibido
                # del paciente.

                medios_pago_data = []

            # =====================================
            # VALIDAR TOTAL REAL COBRADO
            # =====================================

            total_medios = Decimal(
                "0.00"
            )

            for medio in medios_pago_data:

                total_medios += Decimal(
                    str(
                        medio.get(
                            "importe",
                            0
                        )
                    )
                )

            if abs(
                total_a_cobrar_paciente
                - total_medios
            ) > Decimal("0.01"):

                diferencia = (
                    total_a_cobrar_paciente
                    - total_medios
                )

                if diferencia > 0:

                    messages.error(
                        request,
                        f"El cobro no puede registrarse. "
                        f"Faltan cobrar "
                        f"${diferencia:.2f}."
                    )

                else:

                    messages.error(
                        request,
                        f"El cobro no puede registrarse. "
                        f"Existe un excedente de "
                        f"${abs(diferencia):.2f}."
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

            movimiento = form.save(
                commit=False
            )

            movimiento.caja = caja

            movimiento.centro_medico = (
                centro_medico
            )

            movimiento.turno = turno

            movimiento.paciente = (
                turno.paciente
            )

            movimiento.tipo = "INGRESO"

            movimiento.creado_por = (
                request.user
            )

            movimiento.estado = "ACTIVO"

            # Los importes se calculan
            # posteriormente desde los detalles.

            movimiento.concepto = (
                "Cobro de prestaciones"
            )

            movimiento.importe = 0
            movimiento.importe_bruto = 0
            movimiento.importe_iva = 0
            movimiento.importe_neto = 0
            movimiento.importe_medico = 0
            movimiento.importe_consultorio = 0

            movimiento.save()

            # =====================================
            # RECORRER PRESTACIONES
            # =====================================

            orden = 1

            for item in detalles:

                origen = item.get(
                    "origen"
                )

                cantidad = int(
                    item.get(
                        "cantidad",
                        1
                    )
                )

                # =================================
                # PARTICULAR
                # =================================

                if origen == "PARTICULAR":

                    concepto = get_object_or_404(
                        ConceptoFacturacion.objects.select_related(
                            "nomenclador",
                            "proveedor",
                        ),
                        pk=item["id"],
                        activo=True
                    )

                    detalle = DetalleMovimientoCaja(
                        movimiento=movimiento,
                        concepto_facturacion=concepto,
                        prestacion_obra_social=None,
                        fecha_prestacion=turno.fecha,
                        cantidad=cantidad,
                        orden=orden,
                    )

                # =================================
                # OBRA SOCIAL
                # =================================

                elif origen == "OBRA_SOCIAL":

                    prestacion = get_object_or_404(
                        PrestacionPlan.objects.select_related(
                            "nomenclador",
                            "obra_social",
                            "plan",
                            "proveedor",
                        ),
                        pk=item["id"],
                        estado="ACTIVA"
                    )

                    # =================================
                    # COSEGURO COBRADO AL PACIENTE
                    # =================================
                    #
                    # Si tiene coseguro, anteriormente
                    # ya validamos que ese importe fue
                    # pagado.
                    # =================================

                    coseguro_cobrado = (
                        prestacion.tiene_coseguro
                        and prestacion.importe_coseguro
                        and prestacion.importe_coseguro
                            > Decimal("0.00")
                    )

                    # =================================
                    # COPAGO COBRADO AL PACIENTE
                    # =================================
                    #
                    # Si tiene copago, anteriormente
                    # también validamos que ese importe
                    # fue pagado.
                    # =================================

                    copago_cobrado = (
                        prestacion.tiene_copago
                        and prestacion.importe_copago
                        and prestacion.importe_copago
                            > Decimal("0.00")
                    )

                    # =================================
                    # CREAR DETALLE
                    # =================================

                    detalle = DetalleMovimientoCaja(

                        movimiento=movimiento,

                        concepto_facturacion=None,

                        prestacion_obra_social=prestacion,

                        fecha_prestacion=turno.fecha,

                        cantidad=cantidad,

                        orden=orden,

                        # =============================
                        # COSEGURO
                        # =============================

                        coseguro_cobrado=bool(
                            coseguro_cobrado
                        ),

                        coseguro_liquidado=False,

                        # =============================
                        # COPAGO
                        # =============================

                        copago_cobrado=bool(
                            copago_cobrado
                        ),

                        copago_liquidado=False,

                        # =============================
                        # OBRA SOCIAL
                        # =============================

                        obra_social_cobrada=False,

                        fecha_cobro_obra_social=None,

                        honorario_os_liquidado=False,
                    )

                # =================================
                # ORIGEN INCORRECTO
                # =================================

                else:

                    raise ValueError(
                        "Origen de prestación inválido."
                    )

                # =================================
                # GUARDAR DETALLE
                # =================================
                #
                # El modelo copia la fotografía
                # económica de la prestación:
                #
                # - valor
                # - coseguro
                # - copago
                # - IVA
                # - honorarios
                # - consultorio
                # - proveedor
                # =================================

                detalle.save()

                orden += 1

            # =====================================
            # DESCRIPCIÓN DEL MOVIMIENTO
            # =====================================

            if len(detalles) == 1:

                item = detalles[0]

                origen = item.get(
                    "origen"
                )

                # =================================
                # PARTICULAR
                # =================================

                if origen == "PARTICULAR":

                    concepto = (
                        ConceptoFacturacion.objects
                        .select_related(
                            "nomenclador"
                        )
                        .get(
                            pk=item["id"]
                        )
                    )

                    movimiento.concepto_facturacion = (
                        concepto
                    )

                    movimiento.concepto = (
                        f"{concepto.nomenclador.codigo} - "
                        f"{concepto.nomenclador.descripcion}"
                    )

                # =================================
                # OBRA SOCIAL
                # =================================

                elif origen == "OBRA_SOCIAL":

                    prestacion = (
                        PrestacionPlan.objects
                        .select_related(
                            "nomenclador"
                        )
                        .get(
                            pk=item["id"]
                        )
                    )

                    movimiento.concepto_facturacion = (
                        None
                    )

                    movimiento.concepto = (
                        f"{prestacion.nomenclador.codigo} - "
                        f"{prestacion.nomenclador.descripcion}"
                    )

                else:

                    movimiento.concepto_facturacion = (
                        None
                    )

                    movimiento.concepto = (
                        "Cobro de prestación"
                    )

            # =====================================
            # VARIAS PRESTACIONES
            # =====================================

            else:

                movimiento.concepto_facturacion = (
                    None
                )

                movimiento.concepto = (
                    f"{len(detalles)} prestaciones"
                )

            movimiento.save(
                update_fields=[
                    "concepto",
                    "concepto_facturacion",
                ]
            )

            # =====================================
            # MEDIOS DE PAGO
            # =====================================
            #
            # PARTICULAR:
            # se crean normalmente.
            #
            # OBRA SOCIAL CON COSEGURO:
            # se registra el coseguro.
            #
            # OBRA SOCIAL CON COPAGO:
            # se registra el copago.
            #
            # OBRA SOCIAL SIN COSEGURO NI COPAGO:
            # medios_pago_data está vacío.
            # =====================================

            for item in medios_pago_data:

                medio = MedioPago.objects.get(
                    pk=item["medio"]
                )

                DetalleMedioPago.objects.create(
                    movimiento=movimiento,
                    medio_pago=medio,
                    importe=Decimal(
                        str(
                            item["importe"]
                        )
                    )
                )

            # =====================================
            # MENSAJE FINAL
            # =====================================

            detalles_mensaje = [

                f"Paciente: "
                f"{movimiento.paciente}",

                f"Prestaciones: "
                f"{len(detalles)}",

                f"Valor prestaciones: "
                f"${movimiento.importe}",

            ]

            if (
                total_a_cobrar_paciente
                > Decimal("0.00")
            ):

                detalles_mensaje.append(
                    f"Cobrado al paciente: "
                    f"${total_a_cobrar_paciente}"
                )

            else:

                detalles_mensaje.append(
                    "Cobrado al paciente: $0.00 "
                    "(Obra Social)"
                )

            mostrar_exito(
                request,
                titulo="Cobro registrado",
                mensaje=(
                    "La prestación fue registrada "
                    "correctamente."
                ),
                icono="bi-cash-coin",
                detalles=detalles_mensaje,
            )

            return redirect(
                "caja_home"
            )

    # =====================================
    # GET
    # =====================================

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
            'medios_pago': medios_pago,
        }
    )


@login_required
@transaction.atomic
def anular_movimiento(request, movimiento_id):

    # ==========================================
    # CENTRO ACTIVO
    # ==========================================

    centro_medico = obtener_centro_activo(request)

    # ==========================================
    # VALIDAR PERMISOS
    # ==========================================

    if not validar_permiso_caja(request):

        messages.error(
            request,
            'No tiene permisos para acceder a la caja de esta sede.'
        )

        return redirect(
            'turnos:ver_disponibilidad'
        )

    # ==========================================
    # BUSCAR MOVIMIENTO
    # ==========================================

    movimiento = get_object_or_404(
        MovimientoCaja,
        id=movimiento_id,
        centro_medico=centro_medico,
        estado='ACTIVO'
    )

    # ==========================================
    # NO PERMITIR ANULAR CAJA CERRADA
    # ==========================================

    if movimiento.caja.estado == 'CERRADA':

        messages.error(
            request,
            'No se puede anular un movimiento de una caja cerrada.'
        )

        return redirect(
            'caja_home'
        )

    # ==========================================
    # POST
    # ==========================================

    if request.method == 'POST':

        form = AnularMovimientoCajaForm(
            request.POST
        )

        if form.is_valid():

            motivo = form.cleaned_data[
                'motivo_anulacion'
            ]

            # ==================================
            # GUARDAR DATOS ANTERIORES
            # ==================================

            datos_anteriores = {

                "estado": movimiento.estado,

                "importe": str(
                    movimiento.importe
                ),

                "tipo": movimiento.tipo,

                "concepto": movimiento.concepto,

                "medios_pago": [

                    {

                        "medio":
                            detalle.medio_pago.nombre,

                        "importe":
                            str(detalle.importe),

                    }

                    for detalle
                    in movimiento.detalles_medios_pago.all()

                ],

            }

            # ==================================
            # DETECTAR SI ES PAGO DE HONORARIOS
            # ==================================
            #
            # Lo hacemos ANTES de anular para
            # conservar la referencia.
            # ==================================

            pago_honorarios = (
                PagoLiquidacionMedica.objects
                .select_related(
                    "liquidacion"
                )
                .filter(
                    movimiento_caja=movimiento
                )
                .first()
            )

            # ==================================
            # ANULAR MOVIMIENTO
            # ==================================

            movimiento.anular(
                usuario=request.user,
                motivo=motivo
            )

            # ==================================
            # SI ERA COBRO DE UN TURNO
            # ==================================

            if movimiento.turno:

                movimiento.turno.estado = (
                    "PENDIENTE"
                )

                movimiento.turno.save(
                    update_fields=[
                        "estado"
                    ]
                )

            # ==================================
            # SI ERA PAGO DE HONORARIOS
            # ==================================

            if pago_honorarios:

                liquidacion = (
                    pago_honorarios.liquidacion
                )

                # ------------------------------
                # SUMAR ÚNICAMENTE PAGOS
                # CUYO MOVIMIENTO SIGUE ACTIVO
                # ------------------------------

                total_pagado_activo = (
                    PagoLiquidacionMedica.objects
                    .filter(
                        liquidacion=liquidacion,
                        movimiento_caja__estado="ACTIVO",
                    )
                    .aggregate(
                        total=Sum("importe")
                    )["total"]
                    or Decimal("0.00")
                )

                # ------------------------------
                # CANTIDAD DE PAGOS ACTIVOS
                # ------------------------------

                cantidad_pagos_activos = (
                    PagoLiquidacionMedica.objects
                    .filter(
                        liquidacion=liquidacion,
                        movimiento_caja__estado="ACTIVO",
                    )
                    .count()
                )

                # ------------------------------
                # ACTUALIZAR TOTALES
                # ------------------------------

                liquidacion.total_pagado = (
                    total_pagado_activo
                )

                liquidacion.cantidad_pagos = (
                    cantidad_pagos_activos
                )

                # ==================================
                # DETERMINAR ESTADO
                # ==================================

                if total_pagado_activo <= 0:

                    liquidacion.estado = (
                        "PENDIENTE"
                    )

                    liquidacion.fecha_pago = None
                    liquidacion.pagado_por = None

                elif (
                    total_pagado_activo
                    < liquidacion.total_honorarios
                ):

                    liquidacion.estado = (
                        "PARCIAL"
                    )

                    # Buscamos el último pago
                    # que todavía continúa activo.

                    ultimo_pago = (
                        PagoLiquidacionMedica.objects
                        .filter(
                            liquidacion=liquidacion,
                            movimiento_caja__estado="ACTIVO",
                        )
                        .order_by("-fecha")
                        .first()
                    )

                    if ultimo_pago:

                        liquidacion.fecha_pago = (
                            ultimo_pago.fecha
                        )

                        liquidacion.pagado_por = (
                            ultimo_pago.registrado_por
                        )

                else:

                    liquidacion.estado = (
                        "PAGADA"
                    )

                    ultimo_pago = (
                        PagoLiquidacionMedica.objects
                        .filter(
                            liquidacion=liquidacion,
                            movimiento_caja__estado="ACTIVO",
                        )
                        .order_by("-fecha")
                        .first()
                    )

                    if ultimo_pago:

                        liquidacion.fecha_pago = (
                            ultimo_pago.fecha
                        )

                        liquidacion.pagado_por = (
                            ultimo_pago.registrado_por
                        )

                # ------------------------------
                # GUARDAR LIQUIDACIÓN
                # ------------------------------

                liquidacion.save(
                    update_fields=[
                        "total_pagado",
                        "cantidad_pagos",
                        "estado",
                        "fecha_pago",
                        "pagado_por",
                    ]
                )

            # ==================================
            # HISTORIAL CAJA
            # ==================================

            HistorialMovimientoCaja.objects.create(

                caja=movimiento.caja,

                movimiento=movimiento,

                accion='ANULADO',

                usuario=request.user,

                centro_medico=centro_medico,

                descripcion=(
                    f'Movimiento anulado. '
                    f'Motivo: {motivo}'
                ),

                datos_anteriores=(
                    datos_anteriores
                ),

                datos_nuevos={

                    'estado':
                        movimiento.estado,

                    'anulado_por':
                        request.user.username,

                    'motivo_anulacion':
                        motivo,

                }

            )

            # ==================================
            # MENSAJE
            # ==================================

            detalles_mensaje = [

                f"Concepto: {movimiento.concepto}",

                f"Importe: ${movimiento.importe}",

            ]

            if pago_honorarios:

                detalles_mensaje.append(
                    "El pago de honorarios "
                    "asociado fue revertido."
                )

                detalles_mensaje.append(
                    f"Liquidación "
                    f"#{pago_honorarios.liquidacion_id}"
                )

            mostrar_exito(

                request,

                titulo="Movimiento anulado",

                mensaje=(
                    "El movimiento fue "
                    "anulado correctamente."
                ),

                icono="bi-trash",

                detalles=detalles_mensaje,

            )

            return redirect(
                "caja_home"
            )

    else:

        form = AnularMovimientoCajaForm()

    # ==========================================
    # MOSTRAR CONFIRMACIÓN
    # ==========================================

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
    turno_id = request.GET.get("turno_id")

    if not tipo:
        return JsonResponse([], safe=False)

    # ==========================================
    # OBTENER TURNO Y COBERTURA
    # ==========================================

    if not turno_id:
        return JsonResponse({
            "error": "Debe seleccionar un turno."
        }, status=400)

    try:

        turno = Turnos.objects.select_related(
            "paciente",
            "paciente__obrasocial",
            "paciente__plan_obra_social",
        ).get(
            pk=turno_id
        )

    except Turnos.DoesNotExist:

        return JsonResponse({
            "error": "El turno seleccionado no existe."
        }, status=404)

    paciente = turno.paciente
    obra_social = paciente.obrasocial
    plan = paciente.plan_obra_social

    data = []

    # ==========================================
    # PARTICULAR
    # ==========================================

    if obra_social.es_particular:

        prestaciones = ConceptoFacturacion.objects.filter(
            activo=True,
            tipo_concepto=tipo
        ).select_related(
            "nomenclador"
        ).order_by(
            "nomenclador__descripcion"
        )

        for p in prestaciones:

            if not p.nomenclador:
                continue

            data.append({
                "id": p.id,
                "origen": "PARTICULAR",
                "nombre": (
                    f"{p.nomenclador.codigo} - "
                    f"{p.nomenclador.descripcion}"
                )
            })

        return JsonResponse(data, safe=False)

    # ==========================================
    # OBRA SOCIAL
    # ==========================================

    filtros = {
        "obra_social": obra_social,
        "estado": "ACTIVA",
        "tipo_concepto": tipo,
    }

    # ==========================================
    # OBRA SOCIAL CON PLANES
    # ==========================================

    if obra_social.usa_planes:

        if not plan:

            return JsonResponse({
                "error": (
                    f"El paciente {paciente} no tiene "
                    f"un plan asignado para {obra_social.nombre}."
                )
            }, status=400)

        if plan.obra_social_id != obra_social.id:

            return JsonResponse({
                "error": (
                    "El plan asignado al paciente no pertenece "
                    "a su obra social."
                )
            }, status=400)

        filtros["plan"] = plan

    # ==========================================
    # OBRA SOCIAL SIN PLANES
    # ==========================================

    else:

        filtros["plan__isnull"] = True

    prestaciones = PrestacionPlan.objects.filter(
        **filtros
    ).select_related(
        "nomenclador"
    ).order_by(
        "nomenclador__descripcion"
    )

    for p in prestaciones:

        data.append({
            "id": p.id,
            "origen": "OBRA_SOCIAL",
            "nombre": (
                f"{p.nomenclador.codigo} - "
                f"{p.nomenclador.descripcion}"
            )
        })

    return JsonResponse(data, safe=False)

@login_required
def ajax_importe_prestacion(request):

    prestacion_id = request.GET.get(
        "prestacion_id"
    )

    origen = request.GET.get(
        "origen"
    )

    turno_id = request.GET.get(
        "turno_id"
    )

    # ==========================================
    # VALIDAR DATOS
    # ==========================================

    if (
        not prestacion_id or
        not origen or
        not turno_id
    ):

        return JsonResponse({
            "error": (
                "Faltan datos para obtener "
                "el importe."
            ),
            "importe": 0
        }, status=400)


    # ==========================================
    # OBTENER TURNO
    # ==========================================

    try:

        turno = (
            Turnos.objects
            .select_related(
                "paciente",
                "paciente__obrasocial",
                "paciente__plan_obra_social",
            )
            .get(
                pk=turno_id
            )
        )

    except Turnos.DoesNotExist:

        return JsonResponse({
            "error": "El turno no existe.",
            "importe": 0
        }, status=404)


    paciente = turno.paciente

    obra_social = paciente.obrasocial

    plan = paciente.plan_obra_social


    # ==========================================
    # PARTICULAR
    # ==========================================

    if origen == "PARTICULAR":

        if not obra_social.es_particular:

            return JsonResponse({
                "error": (
                    "El paciente no posee "
                    "cobertura Particular."
                ),
                "importe": 0
            }, status=400)


        try:

            concepto = (
                ConceptoFacturacion.objects
                .select_related(
                    "nomenclador"
                )
                .get(
                    pk=prestacion_id,
                    activo=True
                )
            )

        except ConceptoFacturacion.DoesNotExist:

            return JsonResponse({
                "error": (
                    "La prestación particular "
                    "no existe."
                ),
                "importe": 0
            }, status=404)


        return JsonResponse({

            # ======================================
            # VALOR PARTICULAR
            # ======================================

            "importe": float(
                concepto.importe_particular
            ),


            # ======================================
            # PARTICULAR NO TIENE COSEGURO
            # ======================================

            "tiene_coseguro": False,

            "importe_coseguro": 0,


            # ======================================
            # PARTICULAR NO TIENE COPAGO
            # ======================================

            "tiene_copago": False,

            "importe_copago": 0,


            # ======================================
            # DATOS PRESTACIÓN
            # ======================================

            "codigo":
                concepto.nomenclador.codigo,

            "descripcion":
                concepto.nomenclador.descripcion,

            "origen":
                "PARTICULAR"
        })


    # ==========================================
    # OBRA SOCIAL
    # ==========================================

    if origen == "OBRA_SOCIAL":

        filtros = {

            "pk":
                prestacion_id,

            "obra_social":
                obra_social,

            "estado":
                "ACTIVA",
        }


        # ======================================
        # OBRA SOCIAL CON PLAN
        # ======================================

        if obra_social.usa_planes:

            if not plan:

                return JsonResponse({
                    "error": (
                        "El paciente no tiene "
                        "un plan asignado."
                    ),
                    "importe": 0
                }, status=400)


            if (
                plan.obra_social_id !=
                obra_social.id
            ):

                return JsonResponse({
                    "error": (
                        "El plan del paciente "
                        "no pertenece a su "
                        "obra social."
                    ),
                    "importe": 0
                }, status=400)


            filtros["plan"] = plan


        # ======================================
        # OBRA SOCIAL SIN PLAN
        # ======================================

        else:

            filtros[
                "plan__isnull"
            ] = True


        # ======================================
        # OBTENER PRESTACIÓN
        # ======================================

        try:

            prestacion = (
                PrestacionPlan.objects
                .select_related(
                    "nomenclador"
                )
                .get(
                    **filtros
                )
            )

        except PrestacionPlan.DoesNotExist:

            return JsonResponse({
                "error": (
                    "La prestación no pertenece "
                    "al convenio del paciente."
                ),
                "importe": 0
            }, status=404)


        # ======================================
        # COSEGURO
        # ======================================

        importe_coseguro = 0


        if prestacion.tiene_coseguro:

            importe_coseguro = (
                prestacion.importe_coseguro
                or 0
            )


        # ======================================
        # COPAGO
        # ======================================

        importe_copago = 0


        if prestacion.tiene_copago:

            importe_copago = (
                prestacion.importe_copago
                or 0
            )


        # ======================================
        # RESPUESTA
        # ======================================

        return JsonResponse({

            # ==================================
            # VALOR CONVENIO
            # ==================================
            #
            # Este valor es el valor de la
            # prestación.
            #
            # El copago NO modifica este valor.
            # ==================================

            "importe": float(
                prestacion.valor
            ),


            # ==================================
            # COSEGURO
            # ==================================

            "tiene_coseguro":
                prestacion.tiene_coseguro,

            "importe_coseguro": float(
                importe_coseguro
            ),


            # ==================================
            # COPAGO
            # ==================================

            "tiene_copago":
                prestacion.tiene_copago,

            "importe_copago": float(
                importe_copago
            ),


            # ==================================
            # DATOS PRESTACIÓN
            # ==================================

            "codigo":
                prestacion.nomenclador.codigo,

            "descripcion":
                prestacion.nomenclador.descripcion,

            "origen":
                "OBRA_SOCIAL"
        })


    # ==========================================
    # ORIGEN INVÁLIDO
    # ==========================================

    return JsonResponse({
        "error": (
            "Origen de prestación inválido."
        ),
        "importe": 0
    }, status=400)
@login_required
def ajax_cobertura_turno(request):

    turno_id = request.GET.get("turno_id")

    if not turno_id:
        return JsonResponse({
            "ok": False,
            "error": "No se recibió el turno."
        })

    try:
        turno = Turnos.objects.select_related(
            "paciente",
            "paciente__obrasocial",
            "paciente__plan_obra_social",
        ).get(
            pk=turno_id
        )

    except Turnos.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "error": "El turno no existe."
        })

    paciente = turno.paciente
    obra_social = paciente.obrasocial
    plan = paciente.plan_obra_social

    # ==========================================
    # PARTICULAR
    # ==========================================

    if obra_social.es_particular:

        return JsonResponse({
            "ok": True,
            "tipo": "PARTICULAR",

            "paciente": {
                "id": paciente.id,
                "nombre": str(paciente),
            },

            "obra_social": {
                "id": obra_social.id,
                "nombre": obra_social.nombre,
            },

            "plan": None,
        })

    # ==========================================
    # OBRA SOCIAL QUE UTILIZA PLANES
    # ==========================================

    if obra_social.usa_planes:

        if not plan:

            return JsonResponse({
                "ok": False,
                "error": (
                    f"El paciente {paciente} pertenece a "
                    f"{obra_social.nombre}, pero no tiene un plan asignado."
                )
            })

        # Seguridad:
        # el plan debe pertenecer a la obra social del paciente.

        if plan.obra_social_id != obra_social.id:

            return JsonResponse({
                "ok": False,
                "error": (
                    "El plan asignado al paciente no pertenece "
                    "a su obra social."
                )
            })

        return JsonResponse({
            "ok": True,
            "tipo": "OBRA_SOCIAL",

            "paciente": {
                "id": paciente.id,
                "nombre": str(paciente),
            },

            "obra_social": {
                "id": obra_social.id,
                "nombre": obra_social.nombre,
            },

            "plan": {
                "id": plan.id,
                "codigo": plan.codigo,
                "nombre": plan.nombre,
            },
        })

    # ==========================================
    # OBRA SOCIAL SIN PLANES
    # ==========================================

    return JsonResponse({
        "ok": True,
        "tipo": "OBRA_SOCIAL",

        "paciente": {
            "id": paciente.id,
            "nombre": str(paciente),
        },

        "obra_social": {
            "id": obra_social.id,
            "nombre": obra_social.nombre,
        },

        "plan": None,
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


@login_required
def constancia_prestacion(request):

    # ==========================================
    # SOLO POST
    # ==========================================

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Método no permitido."
        )

    # ==========================================
    # DATOS RECIBIDOS
    # ==========================================

    turno_id = request.POST.get(
    "turno"
)

    detalles_json = request.POST.get(
        "detalles_json"
    )

    # ==========================================
    # VALIDAR TURNO
    # ==========================================

    if not turno_id:

        return HttpResponseBadRequest(
            "No se recibió el turno."
        )

    # ==========================================
    # OBTENER TURNO
    # ==========================================

    turno = get_object_or_404(
        Turnos.objects.select_related(
            "paciente",
            "paciente__obrasocial",
            "paciente__plan_obra_social",
            "medico",
        ),
        pk=turno_id
    )

    paciente = turno.paciente

    obra_social = paciente.obrasocial

    plan = paciente.plan_obra_social

    # ==========================================
    # VALIDAR OBRA SOCIAL
    # ==========================================

    if obra_social.es_particular:

        return HttpResponseBadRequest(
            "La constancia de prestación está disponible únicamente para pacientes con Obra Social."
        )

    # ==========================================
    # PROCESAR PRESTACIONES
    # ==========================================

    try:

        prestaciones = json.loads(
            detalles_json or "[]"
        )

    except json.JSONDecodeError:

        return HttpResponseBadRequest(
            "No se pudieron procesar las prestaciones."
        )

    if not prestaciones:

        return HttpResponseBadRequest(
            "Debe agregar al menos una prestación."
        )

    # ==========================================
    # SEGURIDAD
    # ==========================================
    #
    # Solo necesitamos código y descripción.
    # No enviamos importes al comprobante.
    # ==========================================

    prestaciones_constancia = []

    for item in prestaciones:

        prestaciones_constancia.append({
            "codigo": item.get(
                "codigo",
                ""
            ),

            "descripcion": item.get(
                "descripcion",
                ""
            ),

            "cantidad": item.get(
                "cantidad",
                1
            ),
        })

    # ==========================================
    # FECHA / HORA
    # ==========================================

    fecha = timezone.localtime()

    dias = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo",
    }

    dia = dias[
        fecha.weekday()
    ]

    # ==========================================
    # CENTRO
    # ==========================================

    centro_medico = obtener_centro_activo(
        request
    )

    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "caja/constancia_prestacion.html",
        {
            "turno": turno,
            "paciente": paciente,
            "obra_social": obra_social,
            "plan": plan,
            "medico": turno.medico,
            "centro_medico": centro_medico,
            "prestaciones": prestaciones_constancia,
            "fecha": fecha,
            "dia": dia,
        }
    )