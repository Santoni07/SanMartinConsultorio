from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import date
from django.db.models.functions import TruncMonth
from django.db.models import Count
import json
from django.utils import timezone
from turnos.models import (
    Turnos,
    Sobreturno
)

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