from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import date

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


@login_required
def pacientes_gerencia(request):

    return render(
        request,
        'gerencia/pacientes.html'
    )


@login_required
def medicos_gerencia(request):

    return render(
        request,
        'gerencia/medicos.html'
    )


@login_required
def sedes_gerencia(request):

    return render(
        request,
        'gerencia/sedes.html'
    )