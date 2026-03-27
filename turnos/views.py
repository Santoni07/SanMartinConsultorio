from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import  SeleccionMedicoForm
from .models import Turnos, DisponibilidadMedico,AgendaMedico
from paciente.models import Paciente
from medicos.models import Medico
from datetime import datetime, timedelta, time
from django.contrib import messages
from datetime import date
from .forms import AgendaMedicoForm,ConfiguracionAgendaForm
from .models import DisponibilidadMedico

@login_required
def seleccionar_paciente(request):
    paciente = None
    if request.method == 'POST':
        dni = request.POST.get('dni')
        try:
            paciente = Paciente.objects.get(dni=dni)
        except Paciente.DoesNotExist:
            messages.warning(request, f"No se encontró un paciente con DNI {dni}")
    elif request.method == 'GET' and 'seleccionar' in request.GET:
        paciente_id = request.GET.get('seleccionar')
        request.session['paciente_id'] = paciente_id
        return redirect('turnos:seleccionar_medico')

    return render(request, 'turnos/seleccionar_paciente.html', {'paciente': paciente})

@login_required
def seleccionar_medico(request):
    if 'paciente_id' not in request.session:
        return redirect('turnos:seleccionar_paciente')

    if request.method == 'POST':
        form = SeleccionMedicoForm(request.POST)

        if form.is_valid():

            especialidad = form.cleaned_data.get('especialidad')
            medico = form.cleaned_data.get('medico')

            # Solo guardar si médico fue seleccionado
            if medico:
                request.session['especialidad_id'] = especialidad.id if especialidad else None
                request.session['medico_id'] = medico.id
                return redirect('turnos:ver_disponibilidad')

    else:
        form = SeleccionMedicoForm()

    return render(request, 'turnos/seleccionar_medico.html', {
        'form': form
    })


@login_required
def ver_disponibilidad(request):

    if 'paciente_id' not in request.session or 'medico_id' not in request.session:
        return redirect('turnos:seleccionar_paciente')

    medico_id = request.session['medico_id']
    medico = get_object_or_404(Medico, id=medico_id)

    offset = int(request.GET.get('offset', 0))
    hoy = datetime.today().date() + timedelta(days=offset)

    dias = [hoy + timedelta(days=i) for i in range(6)]

    disponibilidad = {}
    horarios_globales = set()

    for dia in dias:

        # 🔵 BUSCAR AGENDA POR FECHA (NUEVO)
        agenda = AgendaMedico.objects.filter(
            medico=medico,
            fecha=dia
        ).first()

        horarios = []

        # 🔹 SOLO SI HAY AGENDA GENERAMOS HORARIOS
        if agenda:

            actual = datetime.combine(date.today(), agenda.hora_inicio)
            fin = datetime.combine(date.today(), agenda.hora_fin)

            while actual < fin:
                horarios.append(actual.time())
                actual += timedelta(minutes=agenda.duracion_turno)

        horarios = sorted(horarios)

        # 🔥 guardar horarios para la tabla
        for h in horarios:
            horarios_globales.add(h)

        turnos_dia = Turnos.objects.filter(medico=medico, fecha=dia)

        dia_data = []

        # 🔹 TURNOS NORMALES
        for hora in horarios:

            turno = turnos_dia.filter(hora=hora).first()

            if turno:
                dia_data.append({
                    'hora': hora,
                    'estado': turno.estado,
                    'paciente': turno.paciente,
                    'observaciones': turno.observaciones,
                    'turno_id': turno.id,
                    'es_sobreturno': turno.es_sobreturno
                })
            else:
                dia_data.append({
                    'hora': hora,
                    'estado': 'libre',
                })

        # 🔥 SOBRETURNOS SOLO SI EL MÉDICO ATIENDE ESE DÍA
        if agenda:
            for i in range(10):
                dia_data.append({
                    'hora': None,
                    'estado': 'sobreturno_libre'
                })

        disponibilidad[dia] = dia_data

    horarios_ordenados = sorted(horarios_globales)

    return render(request, 'turnos/disponibilidad.html', {
        'medico': medico,
        'disponibilidad': disponibilidad,
        'horarios': horarios_ordenados,
        'offset': offset,
    })
@login_required
def reservar_turno(request):

    if request.method == 'POST':

        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')  # turno normal
        hora_manual = request.POST.get('hora_manual')  # sobreturno
        observaciones = request.POST.get('observaciones', '')
        es_sobreturno = request.POST.get('es_sobreturno') == 'true'

        if not fecha_str:
            messages.error(request, "Falta la fecha.")
            return redirect('turnos:ver_disponibilidad')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Error en el formato de fecha.")
            return redirect('turnos:ver_disponibilidad')

        # 🔵 CASO 1: SOBRETURNO
        if es_sobreturno:

            if not hora_manual:
                messages.error(request, "Debes ingresar la hora del sobreturno.")
                return redirect('turnos:ver_disponibilidad')

            try:
                hora = datetime.strptime(hora_manual, '%H:%M').time()
            except ValueError:
                messages.error(request, "Formato de hora inválido.")
                return redirect('turnos:ver_disponibilidad')

            # 🔥 SOLO 1 SOBRETURNO POR HORARIO
            ya_existe_sobreturno = Turnos.objects.filter(
                medico_id=request.session['medico_id'],
                fecha=fecha,
                hora=hora,
                es_sobreturno=True
            ).exists()

            if ya_existe_sobreturno:
                messages.warning(request, "Ya existe un sobreturno en ese horario.")
                return redirect('turnos:ver_disponibilidad')

            Turnos.objects.create(
                especialidad_id=request.session['especialidad_id'],
                medico_id=request.session['medico_id'],
                paciente_id=request.session['paciente_id'],
                fecha=fecha,
                hora=hora,
                observaciones=observaciones,
                es_sobreturno=True
            )

            messages.success(request, "Sobreturno agregado correctamente.")
            return redirect('turnos:ver_disponibilidad')

        # 🔵 CASO 2: TURNO NORMAL

        if not hora_str:
            messages.error(request, "Falta la hora del turno.")
            return redirect('turnos:ver_disponibilidad')

        try:
            hora = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Formato de hora inválido.")
            return redirect('turnos:ver_disponibilidad')

        ya_existe = Turnos.objects.filter(
            medico_id=request.session['medico_id'],
            fecha=fecha,
            hora=hora,
            es_sobreturno=False
        ).exists()

        if ya_existe:
            messages.warning(request, "Ese turno ya fue reservado.")
            return redirect('turnos:ver_disponibilidad')

        Turnos.objects.create(
            especialidad_id=request.session['especialidad_id'],
            medico_id=request.session['medico_id'],
            paciente_id=request.session['paciente_id'],
            fecha=fecha,
            hora=hora,
            observaciones=observaciones,
            es_sobreturno=False
        )

        messages.success(request, "Turno reservado correctamente.")

    return redirect('turnos:ver_disponibilidad')


@login_required
def eliminar_turno(request, turno_id):
    turno = get_object_or_404(Turnos, id=turno_id)
    turno.delete()
    messages.success(request, "Turno eliminado.")
    return redirect('turnos:ver_disponibilidad')

@login_required
def buscar_turnos_por_dni(request):
    dni = request.GET.get('dni')
    paciente = None
    turnos_futuros = None

    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)

            hoy = date.today()

            turnos_futuros = Turnos.objects.filter(
                paciente=paciente,
                fecha__gte=hoy
            ).order_by('fecha', 'hora')

        except Paciente.DoesNotExist:
            messages.warning(request, "No se encontró paciente con ese DNI.")

    return render(request, 'turnos/buscar_turnos_dni.html', {
        'paciente': paciente,
        'turnos': turnos_futuros
    })
    
    
@login_required
def mis_turnos_medico(request):

    if not hasattr(request.user, 'medico'):
        messages.warning(request, "No tienes perfil médico.")
        return redirect('core:index')

    medico = request.user.medico
    hoy = date.today()
    ahora = datetime.now().time()

    filtro = request.GET.get("filtro")
    fecha = request.GET.get("fecha")
    mes = request.GET.get("mes")

    turnos = Turnos.objects.filter(
        medico=medico
    ).order_by("fecha", "hora")

    # 🔥 FILTROS RÁPIDOS
    if filtro == "hoy":
        turnos = turnos.filter(fecha=hoy)

    elif filtro == "manana":
        manana = hoy + timedelta(days=1)
        turnos = turnos.filter(fecha=manana)

    elif filtro == "semana":
        fin_semana = hoy + timedelta(days=7)
        turnos = turnos.filter(fecha__range=[hoy, fin_semana])

    # 🔵 FILTROS MANUALES
    elif fecha:
        turnos = turnos.filter(fecha=fecha)

    elif mes:
        try:
            year, month = mes.split("-")
            turnos = turnos.filter(
                fecha__year=year,
                fecha__month=month
            )
        except ValueError:
            pass

    else:
        # Por defecto mostrar HOY
        turnos = turnos.filter(fecha=hoy)

    turnos_hoy_count = Turnos.objects.filter(
        medico=medico,
        fecha=hoy
    ).count()

    return render(request, "turnos/mis_turnos_medico.html", {
        "turnos": turnos,
        "hoy": hoy,
        "ahora": ahora,
        "turnos_hoy_count": turnos_hoy_count
    })
    
@login_required
def marcar_ausente(request, turno_id):
    turno = get_object_or_404(Turnos, id=turno_id)
    turno.estado = 'AUSENTE'
    turno.save()
    return redirect('buscar_paciente_consulta')


def generar_horarios(disponibilidad):
    horarios = []

    actual = datetime.combine(date.today(), disponibilidad.hora_inicio)
    fin = datetime.combine(date.today(), disponibilidad.hora_fin)

    while actual < fin:
        horarios.append(actual.time())
        actual += timedelta(minutes=disponibilidad.duracion_turno)

    return horarios

@login_required
def cargar_agenda_medico(request):

    if request.method == 'POST':
        form = AgendaMedicoForm(request.POST)

        if form.is_valid():

            medico = form.cleaned_data['medico']
            dias = form.cleaned_data['dias']
            hora_inicio = form.cleaned_data['hora_inicio']
            hora_fin = form.cleaned_data['hora_fin']
            duracion = form.cleaned_data['duracion_turno']

            # 🔥 BORRA agenda anterior (opcional)
            DisponibilidadMedico.objects.filter(medico=medico).delete()

            for dia in dias:
                DisponibilidadMedico.objects.create(
                    medico=medico,
                    dia_semana=int(dia),
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    duracion_turno=duracion
                )

            messages.success(request, "Agenda cargada correctamente.")
            return redirect('turnos:cargar_agenda_medico')

    else:
        form = AgendaMedicoForm()

    return render(request, 'turnos/cargar_agenda_medico.html', {
        'form': form
    })
 
from collections import defaultdict   


@login_required
def agenda_mensual_medico(request):

    medicos = Medico.objects.all()
    medico = None
    dias_final = []

    medico_id = request.GET.get('medico_id') or request.POST.get('medico_id')

    # 🔵 Si seleccionó médico
    if medico_id:
        medico = get_object_or_404(Medico, id=medico_id)

        hoy = date.today()

        # 🔥 agrupamos por día de la semana
        dias_agrupados = defaultdict(list)

        for i in range(30):
            dia = hoy + timedelta(days=i)

            # ❌ excluir sábado y domingo
            if dia.weekday() in [5, 6]:
                continue

            agenda_dia = AgendaMedico.objects.filter(
                medico=medico,
                fecha=dia
            ).first()

            dias_agrupados[dia.weekday()].append({
                'fecha': dia,
                'agenda': agenda_dia
            })

        # 🔥 ordenar lunes → viernes
        nombres_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

        for i in range(5):
            dias_final.append({
                'nombre': nombres_dias[i],
                'fechas': dias_agrupados[i]
            })

    # 🔵 GUARDAR
    if request.method == 'POST' and medico:

        for dia_grupo in dias_final:
            for item in dia_grupo['fechas']:

                dia = item['fecha']

                hora_inicio = request.POST.get(f'inicio_{dia}')
                hora_fin = request.POST.get(f'fin_{dia}')

                # ❌ si no carga horario → eliminar
                if not hora_inicio or not hora_fin:
                    AgendaMedico.objects.filter(
                        medico=medico,
                        fecha=dia
                    ).delete()
                    continue

                try:
                    hora_inicio = datetime.strptime(hora_inicio, '%H:%M').time()
                    hora_fin = datetime.strptime(hora_fin, '%H:%M').time()
                except ValueError:
                    continue

                AgendaMedico.objects.update_or_create(
                    medico=medico,
                    fecha=dia,
                    defaults={
                        'hora_inicio': hora_inicio,
                        'hora_fin': hora_fin,
                        'duracion_turno': 20
                    }
                )

        messages.success(request, "Agenda guardada correctamente.")
        return redirect(f'?medico_id={medico.id}')

    return render(request, 'turnos/agenda_mensual.html', {
        'medicos': medicos,
        'medico': medico,
        'dias_final': dias_final
    })
    
    

def generar_preview(data):
    dias_preview = []

    dia = data['fecha_desde']

    while dia <= data['fecha_hasta']:

        wd = dia.weekday()

        if wd == 0 and data['lunes']:
            dias_preview.append({
                'fecha': dia,
                'inicio': data['lunes_inicio'],
                'fin': data['lunes_fin']
            })

        if wd == 1 and data['martes']:
            dias_preview.append({
                'fecha': dia,
                'inicio': data['martes_inicio'],
                'fin': data['martes_fin']
            })

        if wd == 2 and data['miercoles']:
            dias_preview.append({
                'fecha': dia,
                'inicio': data['miercoles_inicio'],
                'fin': data['miercoles_fin']
            })

        if wd == 3 and data['jueves']:
            dias_preview.append({
                'fecha': dia,
                'inicio': data['jueves_inicio'],
                'fin': data['jueves_fin']
            })

        if wd == 4 and data['viernes']:
            dias_preview.append({
                'fecha': dia,
                'inicio': data['viernes_inicio'],
                'fin': data['viernes_fin']
            })

        dia += timedelta(days=1)

    return dias_preview



def agenda_rapida(request):

    preview = None
    conflictos = []
    pisando_agenda = False

    medicos = Medico.objects.all()

    # 🔵 Capturar médico
    medico_id = request.GET.get('medico_id') or request.POST.get('medico')
    medico = None

    if medico_id:
        medico = Medico.objects.filter(id=medico_id).first()

    # 🔵 POST
    if request.method == 'POST':

        form = ConfiguracionAgendaForm(request.POST)
        form.fields['medico'].queryset = medicos

        # 🔥 FIX → forzar médico si no viene
        if not request.POST.get('medico') and medico_id:
            form.data = form.data.copy()
            form.data['medico'] = medico_id

        if form.is_valid():

            data = form.cleaned_data
            medico = data['medico']

            # 🔥 GENERAR PREVIEW
            preview = generar_preview(data)

            # 🔴 DETECTAR CONFLICTOS
            conflictos = []

            for d in preview:
                agendas_existentes = AgendaMedico.objects.filter(
                    medico=medico,
                    fecha=d['fecha']
                )

                if agendas_existentes.exists():
                    conflictos.append({
                        'fecha': d['fecha'],
                        'existente': agendas_existentes.first()
                    })

            pisando_agenda = len(conflictos) > 0

            # 🔔 AVISO
            if pisando_agenda and 'confirmar' not in request.POST:
                messages.warning(
                    request,
                    "⚠️ Esta agenda pisa horarios existentes. Confirmá para continuar."
                )

            # 🔵 GUARDAR
            if 'confirmar' in request.POST:

                for d in preview:

                    hora_inicio = datetime.strptime(d['inicio'], '%H:%M').time()
                    hora_fin = datetime.strptime(d['fin'], '%H:%M').time()

                    AgendaMedico.objects.update_or_create(
                        medico=medico,
                        fecha=d['fecha'],
                        defaults={
                            'hora_inicio': hora_inicio,
                            'hora_fin': hora_fin,
                            'duracion_turno': 20
                        }
                    )

                messages.success(request, "Agenda creada correctamente.")
                return redirect('turnos:agenda_rapida')

        else:
            print("ERRORES:", form.errors)

    else:
        form = ConfiguracionAgendaForm(initial={'medico': medico})
        form.fields['medico'].queryset = medicos
    conflictos_fechas = [c['fecha'] for c in conflictos]
    return render(request, 'turnos/agenda_rapida.html', {
        'form': form,
        'preview': preview,
        'medicos': medicos,
        'medico': medico,
        'pisando_agenda': pisando_agenda,
        'conflictos': conflictos,
        'conflictos_fechas': conflictos_fechas
    })