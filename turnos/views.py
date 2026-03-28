from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import  SeleccionMedicoForm
from .models import Turnos, DisponibilidadMedico,AgendaMedico,Sobreturno
from paciente.models import Paciente
from medicos.models import Medico
from datetime import datetime, timedelta, time
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.urls import reverse
from datetime import date
from .forms import AgendaMedicoForm,ConfiguracionAgendaForm,ExcepcionAgendaForm,SeleccionMedicoConsultaForm
from .models import DisponibilidadMedico,ExcepcionAgenda
from turnos.utils.agenda   import obtener_agenda_dia
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

    # ✅ SOLO DÍAS CON AGENDA
    dias = []
    for i in range(6):
        dia = hoy + timedelta(days=i)
        agenda = obtener_agenda_dia(medico, dia)

        if agenda:
            dias.append(dia)

    disponibilidad = {}
    horarios_globales = set()

    for dia in dias:

        agenda = obtener_agenda_dia(medico, dia)

        horarios = []

        actual = datetime.combine(date.today(), agenda.hora_inicio)
        fin = datetime.combine(date.today(), agenda.hora_fin)

        while actual <= fin:
            horarios.append(actual.time())
            actual += timedelta(minutes=agenda.duracion_turno if hasattr(agenda, 'duracion_turno') else 20)

        horarios = sorted(horarios)

        # 🔥 SOLO HORARIOS DE LA AGENDA
        for h in horarios:
            horarios_globales.add(h)

        turnos_dia = Turnos.objects.filter(
            medico=medico,
            fecha=dia
        ).exclude(estado='CANCELADO')  # 🔥 clave

        sobreturnos = Sobreturno.objects.filter(
            medico=medico,
            fecha=dia
        ).exclude(estado='CANCELADO')  # 🔥 clave

        dia_data = []

        # 🔵 TURNOS NORMALES
        for hora in horarios:

            turno = turnos_dia.filter(hora=hora).first()

            if turno:
                dia_data.append({
                    'hora': hora,
                    'estado': turno.estado,
                    'paciente': turno.paciente,
                    'observaciones': turno.observaciones,
                    'turno_id': turno.id,
                    'tipo': 'normal'
                })
            else:
                dia_data.append({
                    'hora': hora,
                    'estado': 'libre',
                    'tipo': 'normal'
                })

        # 🟡 SOBRETURNOS
        for s in sobreturnos:

            # 🔥 SOLO si está fuera de la agenda
            if s.hora not in horarios:
                horarios_globales.add(s.hora)

            dia_data.append({
                'hora': s.hora,
                'estado': s.estado,
                'paciente': s.paciente,
                'observaciones': s.observaciones,
                 'sobreturno_id': s.id, 
                'tipo': 'sobreturno'
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

        medico_id = request.session.get('medico_id')
        paciente_id = request.session.get('paciente_id')
        especialidad_id = request.session.get('especialidad_id')

        if not medico_id or not paciente_id:
            messages.error(request, "Error de sesión.")
            return redirect('turnos:ver_disponibilidad')

        # ===============================
        # 🔵 CASO 1: SOBRETURNO
        # ===============================
        if es_sobreturno:

            if not hora_manual:
                messages.error(request, "Debes ingresar la hora del sobreturno.")
                return redirect('turnos:ver_disponibilidad')

            try:
                hora = datetime.strptime(hora_manual, '%H:%M').time()
            except ValueError:
                messages.error(request, "Formato de hora inválido.")
                return redirect('turnos:ver_disponibilidad')

            # 🔥 VALIDAR SI YA EXISTE CUALQUIER TURNO EN ESE HORARIO
            ya_existe = Turnos.objects.filter(
                medico_id=medico_id,
                fecha=fecha,
                hora=hora
            ).exists()

            if ya_existe:
                messages.warning(request, "Ya existe un turno en ese horario.")
                return redirect('turnos:ver_disponibilidad')

            # 🔥 CREAR SOBRETURNO
            Turnos.objects.create(
                especialidad_id=especialidad_id,
                medico_id=medico_id,
                paciente_id=paciente_id,
                fecha=fecha,
                hora=hora,
                observaciones=observaciones,
                estado='PENDIENTE',
                es_sobreturno=True
            )

            messages.success(request, "Sobreturno agregado correctamente.")
            return redirect('turnos:ver_disponibilidad')

        # ===============================
        # 🔵 CASO 2: TURNO NORMAL
        # ===============================

        if not hora_str:
            messages.error(request, "Falta la hora del turno.")
            return redirect('turnos:ver_disponibilidad')

        try:
            hora = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Formato de hora inválido.")
            return redirect('turnos:ver_disponibilidad')

        # 🔥 VALIDAR SI YA EXISTE TURNO NORMAL
        ya_existe = Turnos.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            es_sobreturno=False
        ).exists()

        if ya_existe:
            messages.warning(request, "Ese turno ya fue reservado.")
            return redirect('turnos:ver_disponibilidad')

        # 🔥 CREAR TURNO NORMAL
        Turnos.objects.create(
            especialidad_id=especialidad_id,
            medico_id=medico_id,
            paciente_id=paciente_id,
            fecha=fecha,
            hora=hora,
            observaciones=observaciones,
            estado='PENDIENTE',
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

    # 🔵 TRAER TURNOS Y SOBRETURNOS
    turnos_normales = Turnos.objects.filter(
        medico=medico
    )

    sobreturnos = Sobreturno.objects.filter(
        medico=medico
    )

    # 🔥 UNIFICAR (IMPORTANTE)
    turnos = list(turnos_normales) + list(sobreturnos)

    # 🔥 FILTROS (APLICADOS A LISTA)
    def filtrar(turno):
        if filtro == "hoy":
            return turno.fecha == hoy

        elif filtro == "manana":
            return turno.fecha == hoy + timedelta(days=1)

        elif filtro == "semana":
            return hoy <= turno.fecha <= hoy + timedelta(days=7)

        elif fecha:
            return str(turno.fecha) == fecha

        elif mes:
            try:
                year, month = mes.split("-")
                return turno.fecha.year == int(year) and turno.fecha.month == int(month)
            except ValueError:
                return True

        else:
            return turno.fecha == hoy

    turnos = list(filter(filtrar, turnos))

    # 🔥 AGREGAR TIPO
    for t in turnos:
        if isinstance(t, Sobreturno):
            t.tipo = "Sobreturno"
        else:
            t.tipo = "Turno"

    # 🔥 ORDENAR
    turnos = sorted(turnos, key=lambda x: (x.fecha, x.hora))

    # 🔥 CONTADOR HOY (AMBOS)
    turnos_hoy_count = (
        Turnos.objects.filter(medico=medico, fecha=hoy).count() +
        Sobreturno.objects.filter(medico=medico, fecha=hoy).count()
    )

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
    
@login_required
def crear_excepcion(request):

    medicos = Medico.objects.all()
    medico_id = request.GET.get('medico_id')
    medico = None

    if medico_id:
        medico = Medico.objects.filter(id=medico_id).first()

    if request.method == 'POST':
        form = ExcepcionAgendaForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            excepcion, created = ExcepcionAgenda.objects.update_or_create(
                medico=medico,
                fecha=data['fecha'],
                defaults={
                    'tipo': data['tipo'],
                    'hora_inicio': data.get('hora_inicio'),
                    'hora_fin': data.get('hora_fin'),
                    'nueva_fecha': data.get('nueva_fecha'),
                    'motivo': data.get('motivo'),
                }
            )

            turnos = Turnos.objects.filter(
                medico=medico,
                fecha=excepcion.fecha
            )

            sobreturnos = Sobreturno.objects.filter(
                medico=medico,
                fecha=excepcion.fecha
            )

            # ===============================
            # 🔴 CERRADO
            # ===============================
            if excepcion.tipo == 'CERRADO':

                for turno in turnos:
                    turno.estado = 'CANCELADO'
                    turno.save()

                cantidad_sobreturnos = sobreturnos.count()
                sobreturnos.update(estado='CANCELADO')

                messages.warning(
                    request,
                    f"Se cancelaron {turnos.count()} turnos y {cantidad_sobreturnos} sobreturnos."
                )

            # ===============================
            # 🟡 REPROGRAMAR
            # ===============================
            elif excepcion.tipo == 'REPROGRAMAR':

                conflictos = 0
                movidos = 0

                agenda_original = AgendaMedico.objects.filter(
                    medico=medico,
                    fecha=excepcion.fecha
                ).first()

                # 🔥 CREAR NUEVA AGENDA CON HORARIO DE LA EXCEPCIÓN
                AgendaMedico.objects.update_or_create(
                    medico=medico,
                    fecha=excepcion.nueva_fecha,
                    defaults={
                        'hora_inicio': excepcion.hora_inicio,
                        'hora_fin': excepcion.hora_fin,
                        'duracion_turno': agenda_original.duracion_turno if agenda_original else 20
                    }
                )

                # 🔥 TRAER NUEVA AGENDA
                agenda_nueva = AgendaMedico.objects.filter(
                    medico=medico,
                    fecha=excepcion.nueva_fecha
                ).first()

                for turno in turnos:

                    hora_valida = False

                    if agenda_nueva:
                        if agenda_nueva.hora_inicio <= turno.hora <= agenda_nueva.hora_fin:
                            hora_valida = True

                    existe = Turnos.objects.filter(
                        medico=medico,
                        fecha=excepcion.nueva_fecha,
                        hora=turno.hora
                    ).exists()

                    # 🔥 DECISIÓN FINAL
                    if hora_valida and not existe:
                        turno.fecha = excepcion.nueva_fecha
                        turno.save()
                        movidos += 1
                    else:
                        turno.estado = 'CANCELADO'
                        turno.save()
                        conflictos += 1

                cantidad_sobreturnos = sobreturnos.count()
                sobreturnos.update(estado='CANCELADO')

                messages.success(
                    request,
                    f"Turnos movidos: {movidos}. Cancelados: {conflictos}. Sobreturnos cancelados: {cantidad_sobreturnos}"
                )

            # ===============================
            # 🟢 MODIFICADO
            # ===============================
            elif excepcion.tipo == 'MODIFICADO':

                cancelados = 0

                for turno in turnos:

                    if not (excepcion.hora_inicio <= turno.hora <= excepcion.hora_fin):
                        turno.estado = 'CANCELADO'
                        turno.save()
                        cancelados += 1

                sobreturnos_cancelados = 0
                sobreturnos_mantenidos = 0

                for s in sobreturnos:

                    if excepcion.hora_inicio <= s.hora <= excepcion.hora_fin:
                        # ✔ se mantiene
                        sobreturnos_mantenidos += 1
                    else:
                        # ❌ se cancela
                        s.estado = 'CANCELADO'
                        s.save()
                        sobreturnos_cancelados += 1

                messages.warning(
                    request,
                    f"Se cancelaron {cancelados} turnos y {sobreturnos_cancelados} sobreturnos. "
                    f"{sobreturnos_mantenidos} sobreturnos se mantienen."
                )

            messages.success(request, "Excepción aplicada correctamente")

            url = reverse('turnos:excepciones_detalle')
            return redirect(f"{url}?medico_id={medico.id}&fecha={excepcion.fecha}")

    else:
        form = ExcepcionAgendaForm()

    return render(request, 'turnos/excepcion_form.html', {
        'form': form,
        'medico': medico,
        'medicos': medicos
    })    

@login_required
def lista_excepciones(request):

    medico_id = request.GET.get('medico_id')
    fecha = request.GET.get('fecha')

    excepciones = ExcepcionAgenda.objects.all()

    if medico_id:
        excepciones = excepciones.filter(medico_id=medico_id)

    if fecha:
        fecha_parseada = parse_date(fecha)
        excepciones = excepciones.filter(fecha=fecha_parseada)

    excepciones = excepciones.order_by('-fecha')[:10]

    return render(request, 'turnos/lista_excepciones.html', {
        'excepciones': excepciones,
        'fecha': fecha
    })

    
@login_required
def ver_disponibilidad_consulta(request):

    medico_id = request.GET.get('medico_id')

    if not medico_id:
        return redirect('turnos:seleccionar_medico')

    medico = get_object_or_404(Medico, id=medico_id)

    offset = int(request.GET.get('offset', 0))
    hoy = datetime.today().date() + timedelta(days=offset)

    dias = [hoy + timedelta(days=i) for i in range(6)]

    disponibilidad = {}
    horarios_globales = set()

    for dia in dias:

        agenda = obtener_agenda_dia(medico, dia)

        # 🔴 SI NO ATIENDE → NO MOSTRAR
        if not agenda:
            continue

        horarios = []

        # 🔵 GENERAR HORARIOS DE AGENDA
        actual = datetime.combine(date.today(), agenda.hora_inicio)
        fin = datetime.combine(date.today(), agenda.hora_fin)

        while actual <= fin:
            horarios.append(actual.time())
            actual += timedelta(minutes=agenda.duracion_turno)

        horarios = sorted(horarios)

        # 🔵 AGREGAR HORARIOS BASE
        for h in horarios:
            horarios_globales.add(h)

        turnos_dia = Turnos.objects.filter(
            medico=medico,
            fecha=dia
        ).exclude(estado='CANCELADO')

        # 🟡 SOBRETURNOS (MODELO INDEPENDIENTE)
        sobreturnos = Sobreturno.objects.filter(
            medico=medico,
            fecha=dia
        ).exclude(estado='CANCELADO')

        dia_data = []

        # 🔵 ARMAR TURNOS BASE
        for hora in horarios:

            turno = turnos_dia.filter(hora=hora).first()

            if turno:
                estado = 'ocupado'
            else:
                estado = 'libre'

            dia_data.append({
                'hora': hora,
                'estado': estado,
            })

        # 🟡 AGREGAR SOBRETURNOS
        for s in sobreturnos:

            horarios_globales.add(s.hora)

            dia_data.append({
                'hora': s.hora,
                'estado': 'sobreturno',
                'paciente': s.paciente,
                'observaciones': s.observaciones,
            })

        # 🔥 ORDENAR POR HORA (CLAVE)
        dia_data = sorted(dia_data, key=lambda x: x['hora'])

        disponibilidad[dia] = dia_data

    horarios_ordenados = sorted(horarios_globales)

    return render(request, 'turnos/disponibilidad_consulta.html', {
        'medico': medico,
        'disponibilidad': disponibilidad,
        'horarios': horarios_ordenados,
        'offset': offset,
    })
@login_required
def seleccionar_medico_consulta(request):

    if request.method == 'POST':
        form = SeleccionMedicoConsultaForm(request.POST)

        if form.is_valid():
            medico = form.cleaned_data.get('medico')

            if medico:
                return redirect(
                    f"/turnos/disponibilidad-consulta/?medico_id={medico.id}"
                )

    else:
        form = SeleccionMedicoConsultaForm()

    return render(request, 'turnos/seleccionar_medico_consulta.html', {
        'form': form
    })
    
@login_required
def crear_sobreturno(request):

    if request.method == 'POST':

        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora_manual')
        observaciones = request.POST.get('observaciones')

        medico_id = request.session.get('medico_id')
        paciente_id = request.session.get('paciente_id')

        if not (fecha and hora and medico_id and paciente_id):
            messages.error(request, "Faltan datos para el sobreturno.")
            return redirect('turnos:ver_disponibilidad')

        # 🔥 VALIDAR SI YA EXISTE SOBRETURNO EN ESA HORA
        existe = Sobreturno.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora
        ).exists()

        if existe:
            messages.warning(request, "Ya existe un sobreturno en ese horario.")
            return redirect('turnos:ver_disponibilidad')

        Sobreturno.objects.create(
            medico_id=medico_id,
            paciente_id=paciente_id,
            fecha=fecha,
            hora=hora,
            observaciones=observaciones,
            estado='PENDIENTE'
        )

        messages.success(request, "Sobreturno creado correctamente.")

    return redirect('turnos:ver_disponibilidad')

@login_required
def eliminar_sobreturno(request, sobreturno_id):

    sobreturno = get_object_or_404(Sobreturno, id=sobreturno_id)

    # 🔐 (opcional pero recomendable) validar que sea del médico logueado
    medico_id = request.session.get('medico_id')

    if medico_id and sobreturno.medico_id != medico_id:
        messages.error(request, "No tenés permiso para eliminar este sobreturno.")
        return redirect('turnos:ver_disponibilidad')

    sobreturno.delete()

    messages.success(request, "Sobreturno eliminado correctamente.")

    return redirect('turnos:ver_disponibilidad')


@login_required
def excepciones_detalle(request):

    medico_id = request.GET.get('medico_id')
    fecha = request.GET.get('fecha')

    if not medico_id or not fecha:
        return redirect('turnos:agenda_rapida')

    medico = get_object_or_404(Medico, id=medico_id)

    # 🔵 TURNOS CANCELADOS
    turnos = Turnos.objects.filter(
        medico=medico,
        fecha=fecha,
        estado='CANCELADO'
    ).select_related('paciente')

    # 🟡 SOBRETURNOS (ya eliminados → si querés historial después lo vemos)
    sobreturnos = Sobreturno.objects.filter(
        medico=medico,
        fecha=fecha
    ).select_related('paciente')

    pacientes_afectados = []

    # 🔵 TURNOS
    for t in turnos:
        pacientes_afectados.append({
            'nombre': f"{t.paciente.nombre} {t.paciente.apellido}",
            'telefono': t.paciente.telefono,
            'email': t.paciente.email,
            'tipo': 'Turno',
            'hora': t.hora
        })

    # 🟡 SOBRETURNOS
    for s in sobreturnos:
        pacientes_afectados.append({
            'nombre': f"{s.paciente.nombre} {s.paciente.apellido}",
            'telefono': s.paciente.telefono,
            'email': s.paciente.email,
            'tipo': 'Sobreturno',
            'hora': s.hora
        })

    # 🔥 ORDENAR
    pacientes_afectados = sorted(pacientes_afectados, key=lambda x: x['hora'])

    return render(request, 'turnos/excepciones_detalle.html', {
        'medico': medico,
        'fecha': fecha,
        'pacientes': pacientes_afectados
    })