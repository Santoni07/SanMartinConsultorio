from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import HistoriaClinica, ConsultaMedica
from .forms import ConsultaMedicaForm
from paciente.models import Paciente
from django.db.models import Q
from estudios.models import Estudio
from datetime import date
from turnos.models import Turnos, Sobreturno
from django.contrib import messages
from datetime import date, datetime
from estudios.forms import EstudioForm

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
    turnos = []

    if query:

        pacientes = Paciente.objects.filter(
            Q(nombre__icontains=query) |
            Q(apellido__icontains=query) |
            Q(dni__icontains=query)
        )

        hoy = date.today()
        ahora = datetime.now().time()

        turnos_normales = Turnos.objects.filter(
            paciente__in=pacientes,
            fecha=hoy
        ).select_related('paciente').order_by('hora')

        sobreturnos = Sobreturno.objects.filter(
            paciente__in=pacientes,
            fecha=hoy
        ).select_related('paciente').order_by('hora')

        # Identificar tipo
        for turno in turnos_normales:
            turno.tipo_turno = 'NORMAL'

        for sobreturno in sobreturnos:
            sobreturno.tipo_turno = 'SOBRETURNO'

        # Unificamos
        turnos = list(turnos_normales) + list(sobreturnos)

        # Ordenamos por hora
        turnos.sort(key=lambda x: x.hora)

        # Detectar próximo turno
        turnos_futuros = [
            t for t in turnos
            if t.hora >= ahora and t.estado == 'PENDIENTE'
        ]

        turno_proximo = turnos_futuros[0] if turnos_futuros else None

        for turno in turnos:
            turno.es_actual = (turno == turno_proximo)

    return render(request, 'historial/buscar_paciente_consulta.html', {
        'turnos': turnos
    })



@login_required
def cargar_consulta_paciente(request, turno_id):

    turno = Turnos.objects.filter(id=turno_id).first()
    es_sobreturno = False

    if not turno:
        turno = Sobreturno.objects.filter(id=turno_id).first()
        es_sobreturno = True

    if not turno:
        messages.error(request, "El turno no existe.")
        return redirect('buscar_paciente_consulta')

    paciente = turno.paciente

    historia, _ = HistoriaClinica.objects.get_or_create(
        paciente=paciente
    )

    consultas = historia.consultas.order_by('-fecha')

    hoy = date.today()

    if turno.fecha != hoy:
        messages.error(
            request,
            "Este turno no corresponde al día de hoy."
        )
        return redirect('buscar_paciente_consulta')

    consulta_existente = getattr(turno, 'consulta', None)

    if turno.estado != 'PENDIENTE' and not consulta_existente:
        messages.warning(
            request,
            "Este turno ya fue cerrado."
        )
        return redirect('buscar_paciente_consulta')

    if request.method == 'POST':

        form = ConsultaMedicaForm(
            request.POST,
            instance=consulta_existente
        )

        if form.is_valid():

            consulta = form.save(commit=False)
            historia.antecedentes_patologicos = request.POST.get(
            'antecedentes_patologicos'
            )

            historia.antecedentes_alergicos = request.POST.get(
                'antecedentes_alergicos'
            )

            historia.antecedentes_toxicos = request.POST.get(
                'antecedentes_toxicos'
            )

            historia.antecedentes_quirurgicos = request.POST.get(
                'antecedentes_quirurgicos'
            )

            historia.medicacion_base = request.POST.get(
                'medicacion_base'
            )

            historia.save()

            consulta.historia_clinica = historia
            consulta.medico = request.user.medico
            consulta.fecha = hoy

            if es_sobreturno:
                consulta.sobreturno = turno
            else:
                consulta.turno = turno

            if "guardar_parcial" in request.POST:

                consulta.estado = 'BORRADOR'
                consulta.save()

                messages.success(
                request,
                "CONSULTA_GUARDADA"
)

            elif "finalizar_consulta" in request.POST:

                consulta.estado = 'FINALIZADA'
                consulta.save()

                turno.estado = 'ATENDIDO'
                turno.save()

                request.session['mostrar_modal'] = 'CONSULTA_FINALIZADA'

                return redirect(
                    'cargar_consulta_paciente',
                    turno_id=turno.id
                )

            return redirect(
                'cargar_consulta_paciente',
                turno_id=turno.id
            )

    else:

        form = ConsultaMedicaForm(
            instance=consulta_existente
        )

    if consulta_existente and consulta_existente.estado == 'FINALIZADA':

        for field in form.fields.values():
            field.disabled = True
    estudio_form = EstudioForm(
        paciente=paciente
    )
    estudios = paciente.estudios.all().order_by('-fecha')
    modal = request.session.pop(
    'mostrar_modal',
    None
)
    return render(request, 'historial/cargar_consulta.html', {
        'form': form,
        'historia': historia,
         'modal': modal,
        'estudios': estudios,
        'paciente': paciente,
        'turno': turno,
        'consultas': consultas,
        'consulta': consulta_existente,
        'estudio_form': estudio_form,
        'es_sobreturno': es_sobreturno
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