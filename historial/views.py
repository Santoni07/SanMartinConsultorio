from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import HistoriaClinica, ConsultaMedica
from .forms import ConsultaMedicaForm
from paciente.models import Paciente
from django.db.models import Q
from estudios.models import Estudio
from datetime import date
from turnos.models import Turnos
from django.contrib import messages
from datetime import date, datetime


@login_required
def ver_historia_clinica(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)

    consultas = historia.consultas.prefetch_related('estudios').order_by('-fecha')
    print("CONSULTAS:", consultas)

    for consulta in consultas:
        print("Consulta fecha:", consulta.fecha)
        estudios_por_fecha = Estudio.objects.filter(
            paciente=paciente,
            consulta__isnull=True,
            fecha=consulta.fecha
        )
        print("Estudios encontrados:", estudios_por_fecha)
    for consulta in consultas:
        # Estudios vinculados directamente
        estudios_fk = consulta.estudios.all()

        # Estudios sin FK pero misma fecha
        estudios_por_fecha = Estudio.objects.filter(
            paciente=paciente,
            consulta__isnull=True,
            fecha__year=consulta.fecha.year,
            fecha__month=consulta.fecha.month,
            fecha__day=consulta.fecha.day
        )

        # Unificamos ambos
        consulta.estudios_combinados = list(estudios_fk) + list(estudios_por_fecha)

    # Estudios generales (no coinciden con ninguna consulta)
    fechas_consultas = [c.fecha for c in consultas]

    estudios_generales = Estudio.objects.filter(
        paciente=paciente,
        consulta__isnull=True
    ).exclude(
        fecha__in=fechas_consultas
    )

    return render(request, 'historial/buscar_historia_dni.html', {
        'paciente': paciente,
        'historia': historia,
        'consultas': consultas,
        'estudios_generales': estudios_generales,
        'dni': request.GET.get('dni')
    })


@login_required
def buscar_paciente_consulta(request):
    query = request.GET.get('q')
    turnos = None

    if query:
        pacientes = Paciente.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query)
        )

        hoy = date.today()
        ahora = datetime.now().time()

        turnos = Turnos.objects.filter(
            paciente__in=pacientes,
            fecha=hoy
        ).select_related('paciente').order_by('hora')

        # Detectar próximo turno (el más cercano >= ahora)
        turno_proximo = turnos.filter(hora__gte=ahora).first()

        for turno in turnos:
            turno.es_actual = (turno == turno_proximo)

    return render(request, 'historial/buscar_paciente_consulta.html', {
        'turnos': turnos
    })

@login_required
def cargar_consulta_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)

    hoy = date.today()

    # Buscar turno de hoy SIN consulta asociada
    turno = Turnos.objects.filter(
        paciente=paciente,
        fecha=hoy,
        consulta__isnull=True
    ).order_by('hora').first()

    if not turno:
        messages.error(request, "El paciente no tiene turno activo hoy.")
        return redirect('buscar_paciente_consulta')
    if turno.estado != 'PENDIENTE':
        messages.warning(request, "Este turno ya fue cerrado.")
        return redirect('buscar_paciente_consulta')
    if request.method == 'POST':
        form = ConsultaMedicaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.historia_clinica = historia
            consulta.medico = request.user.medico
            consulta.turno = turno  # 🔥 Vinculamos el turno
            consulta.fecha = hoy
            consulta.save()
            turno.estado = 'ATENDIDO'
            turno.save()
            messages.success(request, "Consulta médica guardada con éxito.")
            return redirect('ver_historia_clinica', paciente_id=paciente.id)

    else:
        form = ConsultaMedicaForm(initial={'fecha': hoy})

    return render(request, 'historial/cargar_consulta.html', {
        'form': form,
        'paciente': paciente,
        'turno': turno
    })
@login_required
def buscar_historia_por_dni(request):
    dni = request.GET.get('dni')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    paciente = None
    historia = None
    consultas = []
    estudios_generales = []

    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
            historia = HistoriaClinica.objects.filter(paciente=paciente).first()

            if historia:
                consultas = historia.consultas.prefetch_related('estudios')

                # 🔥 FILTRO
                if mes:
                    consultas = consultas.filter(fecha__month=mes)

                if anio:
                    consultas = consultas.filter(fecha__year=anio)

                consultas = consultas.order_by('-fecha')

                for consulta in consultas:
                    estudios_fk = consulta.estudios.all()

                    estudios_por_fecha = Estudio.objects.filter(
                        paciente=paciente,
                        consulta__isnull=True,
                        fecha=consulta.fecha
                    )

                    consulta.estudios_combinados = list(estudios_fk) + list(estudios_por_fecha)

                fechas_consultas = [c.fecha for c in consultas]

                estudios_generales = Estudio.objects.filter(
                    paciente=paciente,
                    consulta__isnull=True
                ).exclude(
                    fecha__in=fechas_consultas
                )

        except Paciente.DoesNotExist:
            paciente = None

    return render(request, 'historial/buscar_historia_dni.html', {
        'dni': dni,
        'paciente': paciente,
        'historia': historia,
        'consultas': consultas,
        'estudios_generales': estudios_generales,
        'mes': mes,
        'anio': anio,
    })
    
    
@login_required
def detalle_consulta(request, consulta_id):
    consulta = get_object_or_404(ConsultaMedica, id=consulta_id)

    estudios = consulta.estudios.all()

    return render(request, "historial/detalle_consulta.html", {
        "consulta": consulta,
        "estudios": estudios,
    })