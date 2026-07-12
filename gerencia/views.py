from django.contrib.auth.decorators import login_required
from caja.models import DetalleMedioPago
from django.shortcuts import render
from datetime import date
from django.db.models.functions import TruncMonth
from django.db.models import Count
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from turnos.models import (
    Turnos,
    Sobreturno
)
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone

from caja.models import CajaDiaria, MovimientoCaja
from paciente.models import Paciente
from medicos.models import Medico
from core.models import CentroMedico

@login_required
def dashboard_gerencia(request):

    hoy = date.today()

    # ==========================================
    # TURNOS DEL DÍA
    # ==========================================

    turnos_hoy = (

        Turnos.objects.filter(
            fecha=hoy
        ).count()

        +

        Sobreturno.objects.filter(
            fecha=hoy
        ).count()

    )

    # ==========================================
    # ATENDIDOS
    # ==========================================

    atendidos_hoy = (

        Turnos.objects.filter(
            fecha=hoy,
            estado='ATENDIDO'
        ).count()

        +

        Sobreturno.objects.filter(
            fecha=hoy,
            estado='ATENDIDO'
        ).count()

    )

    # ==========================================
    # AUSENTES
    # ==========================================

    ausentes_hoy = (

        Turnos.objects.filter(
            fecha=hoy,
            estado='AUSENTE'
        ).count()

        +

        Sobreturno.objects.filter(
            fecha=hoy,
            estado='AUSENTE'
        ).count()

    )

    # ==========================================
    # CANCELADOS
    # ==========================================

    cancelados_hoy = (

        Turnos.objects.filter(
            fecha=hoy,
            estado='CANCELADO'
        ).count()

        +

        Sobreturno.objects.filter(
            fecha=hoy,
            estado='CANCELADO'
        ).count()

    )

    # ==========================================
    # PENDIENTES
    # ==========================================

    pendientes_hoy = (

        Turnos.objects.filter(
            fecha=hoy,
            estado='PENDIENTE'
        ).count()

        +

        Sobreturno.objects.filter(
            fecha=hoy,
            estado='PENDIENTE'
        ).count()

    )

    # ==========================================
    # PACIENTES
    # ==========================================

    pacientes_totales = Paciente.objects.count()

    # ==========================================
    # MÉDICOS
    # ==========================================

    medicos_totales = Medico.objects.count()

    # ==========================================
    # SEDES
    # ==========================================

    sedes_totales = CentroMedico.objects.count()

    # ==========================================
    # ==========================================
    # RESUMEN POR SEDE
    # ==========================================

    sedes_resumen = []

    for sede in CentroMedico.objects.filter(activo=True):

        atendidos = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='ATENDIDO'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='ATENDIDO'
            ).count()

        )

        ausentes = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='AUSENTE'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='AUSENTE'
            ).count()

        )

        cancelados = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='CANCELADO'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='CANCELADO'
            ).count()

        )

        pendientes = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='PENDIENTE'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='PENDIENTE'
            ).count()

        )

        sedes_resumen.append({

            'nombre': sede.nombre,

            'atendidos': atendidos,

            'ausentes': ausentes,

            'cancelados': cancelados,

            'pendientes': pendientes,

            'total': (
                atendidos
                + ausentes
                + cancelados
                + pendientes
            )
        })
        
        # ==========================================
        # RANKING MÉDICOS
        # ==========================================

        ranking_medicos = []

        for medico in Medico.objects.all():

            atendidos = (

                Turnos.objects.filter(
                    medico=medico,
                    estado='ATENDIDO'
                ).count()

                +

                Sobreturno.objects.filter(
                    medico=medico,
                    estado='ATENDIDO'
                ).count()

            )

            ausentes = (

                Turnos.objects.filter(
                    medico=medico,
                    estado='AUSENTE'
                ).count()

                +

                Sobreturno.objects.filter(
                    medico=medico,
                    estado='AUSENTE'
                ).count()

            )

            cancelados = (

                Turnos.objects.filter(
                    medico=medico,
                    estado='CANCELADO'
                ).count()

                +

                Sobreturno.objects.filter(
                    medico=medico,
                    estado='CANCELADO'
                ).count()

            )

            pendientes = (

                Turnos.objects.filter(
                    medico=medico,
                    estado='PENDIENTE'
                ).count()

                +

                Sobreturno.objects.filter(
                    medico=medico,
                    estado='PENDIENTE'
                ).count()

            )

            total = (
                atendidos
                + ausentes
                + cancelados
                + pendientes
            )

            ranking_medicos.append({

                'nombre': f'{medico.nombre} {medico.apellido}',

                'atendidos': atendidos,

                'ausentes': ausentes,

                'cancelados': cancelados,

                'pendientes': pendientes,

                'total': total,
            })

        ranking_medicos = sorted(
            ranking_medicos,
            key=lambda x: x['atendidos'],
            reverse=True
        )
    return render(
        request,
        'gerencia/dashboard.html',
        {

            'turnos_hoy': turnos_hoy,

            'atendidos_hoy': atendidos_hoy,

            'ausentes_hoy': ausentes_hoy,

            'cancelados_hoy': cancelados_hoy,

            'pendientes_hoy': pendientes_hoy,

            'pacientes_totales': pacientes_totales,

            'medicos_totales': medicos_totales,

            'sedes_totales': sedes_totales,
            'sedes_resumen': sedes_resumen,
            
            'ranking_medicos': ranking_medicos,
        }
    )

@login_required
def operaciones_gerencia(request):

    from datetime import date, timedelta

    hoy = date.today()

    inicio_semana = hoy - timedelta(days=hoy.weekday())

    # ==========================================
    # HOY
    # ==========================================

    turnos_hoy = (
        Turnos.objects.filter(fecha=hoy).count()
        +
        Sobreturno.objects.filter(fecha=hoy).count()
    )

    atendidos_hoy = (
        Turnos.objects.filter(
            fecha=hoy,
            estado='ATENDIDO'
        ).count()
        +
        Sobreturno.objects.filter(
            fecha=hoy,
            estado='ATENDIDO'
        ).count()
    )

    ausentes_hoy = (
        Turnos.objects.filter(
            fecha=hoy,
            estado='AUSENTE'
        ).count()
        +
        Sobreturno.objects.filter(
            fecha=hoy,
            estado='AUSENTE'
        ).count()
    )

    cancelados_hoy = (
        Turnos.objects.filter(
            fecha=hoy,
            estado='CANCELADO'
        ).count()
        +
        Sobreturno.objects.filter(
            fecha=hoy,
            estado='CANCELADO'
        ).count()
    )

    pendientes_hoy = (
        Turnos.objects.filter(
            fecha=hoy,
            estado='PENDIENTE'
        ).count()
        +
        Sobreturno.objects.filter(
            fecha=hoy,
            estado='PENDIENTE'
        ).count()
    )

    # ==========================================
    # SEMANA
    # ==========================================

    turnos_semana = (
        Turnos.objects.filter(
            fecha__gte=inicio_semana
        ).count()
        +
        Sobreturno.objects.filter(
            fecha__gte=inicio_semana
        ).count()
    )

    atendidos_semana = (
        Turnos.objects.filter(
            fecha__gte=inicio_semana,
            estado='ATENDIDO'
        ).count()
        +
        Sobreturno.objects.filter(
            fecha__gte=inicio_semana,
            estado='ATENDIDO'
        ).count()
    )

    # ==========================================
    # MES
    # ==========================================

    turnos_mes = (
        Turnos.objects.filter(
            fecha__month=hoy.month,
            fecha__year=hoy.year
        ).count()
        +
        Sobreturno.objects.filter(
            fecha__month=hoy.month,
            fecha__year=hoy.year
        ).count()
    )

    atendidos_mes = (
        Turnos.objects.filter(
            fecha__month=hoy.month,
            fecha__year=hoy.year,
            estado='ATENDIDO'
        ).count()
        +
        Sobreturno.objects.filter(
            fecha__month=hoy.month,
            fecha__year=hoy.year,
            estado='ATENDIDO'
        ).count()
    )
    # ==========================================
    # COMPARATIVO POR SEDE
    # ==========================================

    sedes_operacion = []

    for sede in CentroMedico.objects.filter(activo=True):

        atendidos = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='ATENDIDO'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='ATENDIDO'
            ).count()

        )

        ausentes = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='AUSENTE'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='AUSENTE'
            ).count()

        )

        cancelados = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='CANCELADO'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='CANCELADO'
            ).count()

        )

        pendientes = (

            Turnos.objects.filter(
                centro_medico=sede,
                estado='PENDIENTE'
            ).count()

            +

            Sobreturno.objects.filter(
                centro_medico=sede,
                estado='PENDIENTE'
            ).count()

        )

        sedes_operacion.append({

            'nombre': sede.nombre,

            'atendidos': atendidos,

            'ausentes': ausentes,

            'cancelados': cancelados,

            'pendientes': pendientes,

        })

    return render(
        request,
        'gerencia/operaciones.html',
        {
            'turnos_hoy': turnos_hoy,
            'atendidos_hoy': atendidos_hoy,
            'ausentes_hoy': ausentes_hoy,
            'cancelados_hoy': cancelados_hoy,
            'pendientes_hoy': pendientes_hoy,
            'sedes_operacion': sedes_operacion,

            'turnos_semana': turnos_semana,
            'atendidos_semana': atendidos_semana,

            'turnos_mes': turnos_mes,
            'atendidos_mes': atendidos_mes,
        }
    )


from datetime import date
@login_required
def pacientes_gerencia(request):

    hoy = timezone.now()

    total_pacientes = Paciente.objects.count()

    nuevos_mes = Paciente.objects.filter(
        fecha_alta__year=hoy.year,
        fecha_alta__month=hoy.month
    ).count()

    pacientes_activos = Paciente.objects.filter(
        activo=True
    ).count()

    pacientes_inactivos = Paciente.objects.filter(
        activo=False
    ).count()
    
    pacientes_por_mes = (
        Paciente.objects
        .annotate(mes=TruncMonth('fecha_alta'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    labels_mes = [
        p['mes'].strftime('%b %Y')
        for p in pacientes_por_mes
    ]

    datos_mes = [
        p['total']
        for p in pacientes_por_mes
    ]
    ultimos_pacientes = Paciente.objects.order_by(
            '-fecha_alta'
        )[:10]
    
    obras_sociales = (
        Paciente.objects
        .values('obrasocial__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    labels_os = [
        item['obrasocial__nombre']
        for item in obras_sociales
    ]
    datos_os = [
        item['total']
        for item in obras_sociales
    ]
    context = {
        'total_pacientes': total_pacientes,
        'nuevos_mes': nuevos_mes,
        'pacientes_activos': pacientes_activos,
        'pacientes_inactivos': pacientes_inactivos,
        'labels_mes': json.dumps(labels_mes),
        'datos_mes': json.dumps(datos_mes),
        'ultimos_pacientes': ultimos_pacientes,
        'labels_os': json.dumps(labels_os),
        'datos_os': json.dumps(datos_os),
    }

    return render(
        request,
        'gerencia/pacientes.html',
        context
    )



@login_required

def medicos_gerencia(request):

    total_medicos = Medico.objects.count()

    total_turnos = Turnos.objects.count()

    total_sobreturnos = Sobreturno.objects.count()

    total_atendidos = (
        Turnos.objects.filter(
            estado='ATENDIDO'
        ).count()
        +
        Sobreturno.objects.filter(
            estado='ATENDIDO'
        ).count()
    )

    ranking_medicos = []

    for medico in Medico.objects.all():

        turnos = Turnos.objects.filter(
            medico=medico
        )

        sobreturnos = Sobreturno.objects.filter(
            medico=medico
        )

        turnos_total = turnos.count()

        sobreturnos_total = sobreturnos.count()

        atendidos = (
            turnos.filter(
                estado='ATENDIDO'
            ).count()
            +
            sobreturnos.filter(
                estado='ATENDIDO'
            ).count()
        )

        ausentes = (
            turnos.filter(
                estado='AUSENTE'
            ).count()
            +
            sobreturnos.filter(
                estado='AUSENTE'
            ).count()
        )

        cancelados = (
            turnos.filter(
                estado='CANCELADO'
            ).count()
            +
            sobreturnos.filter(
                estado='CANCELADO'
            ).count()
        )

        pendientes = (
            turnos.filter(
                estado='PENDIENTE'
            ).count()
            +
            sobreturnos.filter(
                estado='PENDIENTE'
            ).count()
        )

        total_agendado = (
            turnos_total +
            sobreturnos_total
        )

        # Producción real
        produccion = atendidos

        # ==================================================
        # OCUPACIÓN
        # Qué porcentaje de la agenda terminó atendiéndose
        # ==================================================

        ocupacion = 0

        if total_agendado > 0:

            ocupacion = round(
                (atendidos / total_agendado) * 100,
                1
            )

        # ==================================================
        # EFICIENCIA
        # Qué porcentaje de pacientes se atendió
        # respecto de los que efectivamente llegaron
        # ==================================================

        eficiencia = 0

        if (atendidos + ausentes) > 0:

            eficiencia = round(
                (
                    atendidos /
                    (atendidos + ausentes)
                ) * 100,
                1
            )

        # ==================================================
        # SATURACIÓN
        # Cuánto se fuerza la agenda con sobreturnos
        # ==================================================

        saturacion = 0

        if turnos_total > 0:

            saturacion = round(
                (
                    sobreturnos_total /
                    turnos_total
                ) * 100,
                1
            )

        # ==================================================
        # CANCELACIÓN
        # Qué porcentaje de turnos otorgados
        # terminaron cancelados
        # ==================================================

        cancelacion = 0

        if total_agendado > 0:

            cancelacion = round(
                (
                    cancelados /
                    total_agendado
                ) * 100,
                1
            )
        ranking_medicos.append({

            'medico': medico,

            'turnos': turnos_total,

            'sobreturnos': sobreturnos_total,

            'atendidos': atendidos,

            'ausentes': ausentes,

            'cancelados': cancelados,

            'pendientes': pendientes,

            'produccion': produccion,

            'ocupacion': ocupacion,

            'eficiencia': eficiencia,

            'saturacion': saturacion,
            
            'cancelacion': cancelacion,

            'total_agendado': total_agendado,

        })

    ranking_medicos = sorted(
        ranking_medicos,
        key=lambda x: x['produccion'],
        reverse=True
    )

    top_10_medicos = ranking_medicos[:10]

    context = {

        'total_medicos': total_medicos,

        'total_turnos': total_turnos,

        'total_sobreturnos': total_sobreturnos,

        'total_atendidos': total_atendidos,

        'ranking_medicos': ranking_medicos,

        'top_10_medicos': top_10_medicos,

    }

    return render(
        request,
        'gerencia/medicos.html',
        context
    )

@login_required
def sedes_gerencia(request):

    return render(
        request,
        'gerencia/sedes.html'
    )
    
@login_required
def facturacion(request):
    hoy = timezone.localdate()
    mes_actual = hoy.month
    anio_actual = hoy.year

    cajas_cerradas = CajaDiaria.objects.filter(
        estado='CERRADA'
    ).select_related(
        'centro_medico',
        'abierta_por',
        'cerrada_por'
    ).order_by('-fecha', 'centro_medico', 'turno')

    movimientos_activos = (
        MovimientoCaja.objects.filter(
            estado="ACTIVO",
            caja__estado="CERRADA",
        )
        .select_related(
            "centro_medico",
            "creado_por",
            "caja",
        )
        .prefetch_related(
            "detalles_medios_pago__medio_pago",
            "detalles",
        )
    )

    total_ingresos = (
        movimientos_activos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_bruto")
        )["total"] or 0
    )

    total_egresos = (
        movimientos_activos.filter(
            tipo="EGRESO"
        ).aggregate(
            total=Sum("importe_bruto")
        )["total"] or 0
    )



    saldo_neto = total_ingresos - total_egresos

   # =====================================================
    # EFECTIVO
    # =====================================================

    efectivo_ingresos = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="INGRESO",
            movimiento__caja__estado="CERRADA",
            medio_pago__nombre__iexact="Efectivo",
        ).aggregate(
            total=Sum("importe")
        )["total"] or 0
    )

    efectivo_egresos = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="EGRESO",
            movimiento__caja__estado="CERRADA",
            medio_pago__nombre__iexact="Efectivo",
        ).aggregate(
            total=Sum("importe")
        )["total"] or 0
    )

    efectivo_neto = efectivo_ingresos - efectivo_egresos

    # =====================================================
    # BANCARIZADO
    # =====================================================

    bancarizado = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="INGRESO",
            movimiento__caja__estado="CERRADA",
        ).exclude(
            medio_pago__nombre__iexact="Efectivo"
        ).aggregate(
            total=Sum("importe")
        )["total"] or 0
    )

    # =====================================================
    # MOVIMIENTOS ANULADOS
    # =====================================================

    total_anulados = (
        MovimientoCaja.objects.filter(
            estado="ANULADO",
            caja__estado="CERRADA",
        ).aggregate(
            total=Sum("importe_bruto")
        )["total"] or 0
    )

    # =====================================================
    # CANTIDAD DE CAJAS
    # =====================================================

    cantidad_cajas_cerradas = cajas_cerradas.count()

    cajas_abiertas_pendientes = (
        CajaDiaria.objects.filter(
            estado="ABIERTA"
        ).select_related(
            "centro_medico",
            "abierta_por",
        ).order_by(
            "-fecha",
            "centro_medico",
            "turno",
        )
    )

    cantidad_cajas_abiertas = cajas_abiertas_pendientes.count()

    # =====================================================
    # RESUMEN POR MEDIO DE PAGO
    # =====================================================

    resumen_por_medio = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="INGRESO",
            movimiento__caja__estado="CERRADA",
        )
        .values(
            "medio_pago__nombre"
        )
        .annotate(
            total=Sum("importe"),
            cantidad=Count("id"),
        )
        .order_by("-total")
    )

    # =====================================================
    # RESUMEN POR SEDE
    # =====================================================

    resumen_por_sede = (
        movimientos_activos.filter(
            tipo="INGRESO"
        )
        .values(
            "centro_medico__nombre"
        )
        .annotate(
            cantidad=Count("id"),
            bruto=Sum("importe_bruto"),
            iva=Sum("importe_iva"),
            neto=Sum("importe_neto"),
            honorarios=Sum("importe_medico"),
            consultorio=Sum("importe_consultorio"),
        )
        .order_by("-bruto")
    )

    # =====================================================
    # RESUMEN POR TURNO
    # =====================================================

    resumen_por_turno = (
        movimientos_activos.filter(
            tipo="INGRESO"
        )
        .values(
            "caja__turno"
        )
        .annotate(
            cantidad=Count("id"),
            bruto=Sum("importe_bruto"),
        )
        .order_by("caja__turno")
    )

    # =====================================================
    # RESUMEN POR SECRETARIA
    # =====================================================

    resumen_por_secretaria = (
        movimientos_activos.filter(
            tipo="INGRESO"
        )
        .values(
            "creado_por__username"
        )
        .annotate(
            cantidad=Count("id"),
            bruto=Sum("importe_bruto"),
            iva=Sum("importe_iva"),
            neto=Sum("importe_neto"),
        )
        .order_by("-bruto")
    )

    # =====================================================
    # ANULACIONES
    # =====================================================

    anulaciones_por_usuario = (
        MovimientoCaja.objects.filter(
            estado="ANULADO"
        )
        .values(
            "anulado_por__username"
        )
        .annotate(
            total_anulado=Sum("importe_bruto"),
            cantidad=Count("id"),
        )
        .order_by("-total_anulado")
    )

    # =====================================================
    # MOVIMIENTOS DEL MES
    # =====================================================

    movimientos_mes = movimientos_activos.filter(
        fecha_creacion__year=anio_actual,
        fecha_creacion__month=mes_actual,
        tipo="INGRESO",
    )

    total_mes = (
        movimientos_mes.aggregate(
            total=Sum("importe_bruto")
        )["total"] or 0
    )

    resumen_mes_por_sede = (
        movimientos_mes.values(
            "centro_medico__nombre"
        )
        .annotate(
            cantidad=Count("id"),
            bruto=Sum("importe_bruto"),
            iva=Sum("importe_iva"),
            neto=Sum("importe_neto"),
        )
        .order_by("-bruto")
    )
    # =====================================================
    # NUEVOS KPI FINANCIEROS
    # =====================================================

    total_bruto = total_ingresos

    total_iva = (
        movimientos_activos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_iva")
        )["total"] or 0
    )

    total_neto = (
        movimientos_activos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_neto")
        )["total"] or 0
    )

    total_honorarios = (
        movimientos_activos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_medico")
        )["total"] or 0
    )

    total_consultorio = (
        movimientos_activos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_consultorio")
        )["total"] or 0
    )

    total_retenciones = (
        movimientos_activos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("retencion_monto")
        )["total"] or 0
    )
            
    

    context = {

        'hoy': hoy,

        'cajas_cerradas': cajas_cerradas[:20],

        'cajas_abiertas_pendientes': cajas_abiertas_pendientes,

        # =====================================================
        # KPI PRINCIPALES
        # =====================================================

        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,

        # =====================================================
        # NUEVOS KPI FINANCIEROS
        # =====================================================

        'total_bruto': total_bruto,
        'total_iva': total_iva,
        'total_neto': total_neto,
        'total_honorarios': total_honorarios,
        'total_consultorio': total_consultorio,
        'total_retenciones': total_retenciones,

        # =====================================================
        # MEDIOS DE PAGO
        # =====================================================

        'efectivo_ingresos': efectivo_ingresos,
        'efectivo_egresos': efectivo_egresos,
        'efectivo_neto': efectivo_neto,
        'bancarizado': bancarizado,

        # =====================================================
        # CAJAS
        # =====================================================

        'total_anulados': total_anulados,

        'cantidad_cajas_cerradas': cantidad_cajas_cerradas,

        'cantidad_cajas_abiertas': cantidad_cajas_abiertas,

        # =====================================================
        # REPORTES
        # =====================================================

        'resumen_por_medio': resumen_por_medio,

        'resumen_por_sede': resumen_por_sede,

        'resumen_por_turno': resumen_por_turno,

        'resumen_por_secretaria': resumen_por_secretaria,

        'anulaciones_por_usuario': anulaciones_por_usuario,

        # =====================================================
        # MENSUAL
        # =====================================================

        'total_mes': total_mes,

        'resumen_mes_por_sede': resumen_mes_por_sede,

    }

    return render(request, 'gerencia/facturacion.html', context)


@login_required
def facturacion_sede(request, centro_id):

    centro = get_object_or_404(
        CentroMedico,
        id=centro_id
    )

    hoy = timezone.localdate()

    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    movimientos = (
        MovimientoCaja.objects.filter(
            estado="ACTIVO",
            caja__estado="CERRADA",
            centro_medico=centro,
        )
        .select_related(
            "creado_por",
            "caja",
            "centro_medico",
            "paciente",
        )
        .prefetch_related(
            "detalles",
            "detalles_medios_pago__medio_pago",
        )
    )

    cajas = CajaDiaria.objects.filter(
        estado='CERRADA',
        centro_medico=centro
    )

    # ==========================
    # FILTROS
    # ==========================

    if fecha_desde:
        movimientos = movimientos.filter(
            fecha_creacion__date__gte=fecha_desde
        )

        cajas = cajas.filter(
            fecha__gte=fecha_desde
        )

    if fecha_hasta:
        movimientos = movimientos.filter(
            fecha_creacion__date__lte=fecha_hasta
        )

        cajas = cajas.filter(
            fecha__lte=fecha_hasta
        )

    if mes:
        movimientos = movimientos.filter(
            fecha_creacion__month=mes
        )

        cajas = cajas.filter(
            fecha__month=mes
        )

    if anio:
        movimientos = movimientos.filter(
            fecha_creacion__year=anio
        )

        cajas = cajas.filter(
            fecha__year=anio
        )

    # ==========================
    # KPIS PRINCIPALES
    # ==========================

    total_ingresos = movimientos.filter(
        tipo='INGRESO'
    ).aggregate(
        total=Sum('importe_bruto')
    )['total'] or 0

    total_egresos = movimientos.filter(
        tipo='EGRESO'
    ).aggregate(
        total=Sum('importe_bruto')
    )['total'] or 0

    saldo_neto = total_ingresos - total_egresos
    
    total_bruto = total_ingresos

    total_iva = (
        movimientos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_iva")
        )["total"] or 0
    )

    total_neto = (
        movimientos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_neto")
        )["total"] or 0
    )

    total_honorarios = (
        movimientos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_medico")
        )["total"] or 0
    )

    total_consultorio = (
        movimientos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("importe_consultorio")
        )["total"] or 0
    )

    total_retenciones = (
        movimientos.filter(
            tipo="INGRESO"
        ).aggregate(
            total=Sum("retencion_monto")
        )["total"] or 0
    )

    cantidad_movimientos = movimientos.count()

    cantidad_cajas = cajas.count()

    # ==========================
    # EFECTIVO / BANCARIZADO
    # ==========================
    
    efectivo = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="INGRESO",
            movimiento__caja__estado="CERRADA",
            movimiento__centro_medico=centro,
            medio_pago__nombre__iexact="Efectivo",
        ).aggregate(
            total=Sum("importe")
        )["total"] or 0
    )

    bancarizado = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="INGRESO",
            movimiento__caja__estado="CERRADA",
            movimiento__centro_medico=centro,
        ).exclude(
            medio_pago__nombre__iexact="Efectivo"
        ).aggregate(
            total=Sum("importe")
        )["total"] or 0
    )

    
    # ==========================
    # PROMEDIOS
    # ==========================

    dias_con_movimientos = movimientos.values(
        'fecha_creacion__date'
    ).distinct().count()

    promedio_diario = 0

    if dias_con_movimientos:
        promedio_diario = (
            total_ingresos / dias_con_movimientos
        )

    ticket_promedio = 0

    ingresos_count = movimientos.filter(
        tipo='INGRESO'
    ).count()

    if ingresos_count:
        ticket_promedio = (
            total_ingresos / ingresos_count
        )

    # ==========================
    # MEJOR DIA
    # ==========================

    mejor_dia = movimientos.filter(
        tipo='INGRESO'
    ).values(
        'fecha_creacion__date'
    ).annotate(
        total=Sum('importe_bruto')
    ).order_by('-total').first()

    peor_dia = movimientos.filter(
        tipo='INGRESO'
    ).values(
        'fecha_creacion__date'
    ).annotate(
        total=Sum('importe_bruto')
    ).order_by('total').first()

    # ==========================
    # TURNO MAS RENTABLE
    # ==========================

    turno_top = movimientos.filter(
        tipo='INGRESO'
    ).values(
        'caja__turno'
    ).annotate(
        total=Sum('importe_bruto')
    ).order_by('-total').first()

    # ==========================
    # SECRETARIA TOP
    # ==========================

    resumen_secretarias = (
        movimientos.filter(
            tipo="INGRESO"
        )
        .values(
            "creado_por__username"
        )
        .annotate(
            cantidad=Count("id"),
            bruto=Sum("importe_bruto"),
            iva=Sum("importe_iva"),
            neto=Sum("importe_neto"),
        )
        .order_by("-bruto")
    )

    secretaria_top = resumen_secretarias.first()

    # ==========================
    # MEDIOS DE PAGO
    # ==========================

    resumen_medios = (
        DetalleMedioPago.objects.filter(
            movimiento__estado="ACTIVO",
            movimiento__tipo="INGRESO",
            movimiento__caja__estado="CERRADA",
            movimiento__centro_medico=centro,
        )
        .values(
            "medio_pago__nombre"
        )
        .annotate(
            total=Sum("importe"),
            cantidad=Count("id"),
        )
        .order_by("-total")
    )

    # ==========================
    # MAÑANA VS TARDE
    # ==========================

    resumen_turnos = movimientos.filter(
        tipo='INGRESO'
    ).values(
        'caja__turno'
    ).annotate(
        total=Sum('importe_bruto')
    )

    # ==========================
    # EVOLUCION DIARIA
    # ==========================

    evolucion_diaria = movimientos.filter(
        tipo='INGRESO'
    ).values(
        'fecha_creacion__date'
    ).annotate(
        total=Sum('importe_bruto')
    ).order_by(
        'fecha_creacion__date'
    )
    # ==========================
    # CHART MEDIOS DE PAGO
    # ==========================

    labels_medios = []
    data_medios = []

    for item in resumen_medios:
        labels_medios.append(
            item['medio_pago__nombre']
        )

        data_medios.append(
            float(item['total'])
        )

    # ==========================
    # CHART EVOLUCIÓN
    # ==========================

    labels_evolucion = []
    data_evolucion = []

    for item in evolucion_diaria:

        labels_evolucion.append(
            item['fecha_creacion__date'].strftime('%d/%m')
        )

        data_evolucion.append(
            float(item['total'])
        )
    context = {

        'centro': centro,

        'hoy': hoy,

        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'mes': mes,
        'anio': anio,

        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'saldo_neto': saldo_neto,
        'labels_medios': labels_medios,
        'data_medios': data_medios,
        'total_bruto': total_bruto,
        'total_iva': total_iva,
        'total_neto': total_neto,
        'total_honorarios': total_honorarios,
        'total_consultorio': total_consultorio,
        'total_retenciones': total_retenciones,
        'labels_evolucion': labels_evolucion,
        'data_evolucion': data_evolucion,
        'cantidad_cajas': cantidad_cajas,
        'cantidad_movimientos': cantidad_movimientos,
        
        'efectivo': efectivo,
        'bancarizado': bancarizado,

        'promedio_diario': promedio_diario,
        'ticket_promedio': ticket_promedio,

        'mejor_dia': mejor_dia,
        'peor_dia': peor_dia,

        'turno_top': turno_top,
        'secretaria_top': secretaria_top,

        'resumen_medios': resumen_medios,
        'resumen_turnos': resumen_turnos,
        'resumen_secretarias': resumen_secretarias,

        'evolucion_diaria': evolucion_diaria,

        'cajas': cajas[:50],
    }

    return render(
        request,
        'gerencia/facturacion_sede.html',
        context
    )
    
@login_required
def detalle_caja(request, caja_id):

    caja = get_object_or_404(
        CajaDiaria,
        id=caja_id
    )

    movimientos = (
        MovimientoCaja.objects
        .filter(caja=caja)
        .select_related(
            "paciente",
            "creado_por",
            "turno",
            "concepto_facturacion",
        )
        .prefetch_related(
            "detalles",
            "detalles_medios_pago",
        )
        .order_by("-fecha_creacion")
    )

    

    ingresos = (
    movimientos.filter(
        tipo="INGRESO",
        estado="ACTIVO"
    ).aggregate(
        total=Sum("importe_bruto")
    )["total"] or 0
)

    egresos = (
        movimientos.filter(
            tipo="EGRESO",
            estado="ACTIVO"
        ).aggregate(
            total=Sum("importe_bruto")
        )["total"] or 0
    )

    saldo = ingresos - egresos

    total_iva = (
        movimientos.filter(
            estado="ACTIVO"
        ).aggregate(
            total=Sum("importe_iva")
        )["total"] or 0
    )

    total_honorarios = (
        movimientos.filter(
            estado="ACTIVO"
        ).aggregate(
            total=Sum("importe_medico")
        )["total"] or 0
    )

    total_consultorio = (
        movimientos.filter(
            estado="ACTIVO"
        ).aggregate(
            total=Sum("importe_consultorio")
        )["total"] or 0
    )

    total_neto = (
        movimientos.filter(
            estado="ACTIVO"
        ).aggregate(
            total=Sum("importe_neto")
        )["total"] or 0
    )

    saldo = ingresos - egresos

    context = {

        'caja': caja,
        'movimientos': movimientos,

        'ingresos': ingresos,
        'egresos': egresos,
        'saldo': saldo,

    }

    return render(
        request,
        'gerencia/detalle_caja.html',
        context = {

            "caja": caja,

            "movimientos": movimientos,

            "ingresos": ingresos,
            "egresos": egresos,
            "saldo": saldo,

            "total_bruto": ingresos,
            "total_neto": total_neto,
            "total_iva": total_iva,
            "total_honorarios": total_honorarios,
            "total_consultorio": total_consultorio,

        }
    )