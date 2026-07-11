from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from collections import OrderedDict
from .forms import  SeleccionMedicoForm
from .models import Turnos, DisponibilidadMedico,AgendaMedico,Sobreturno,Consultorio,HistorialTurno
from paciente.models import Paciente
from medicos.models import Medico
from django.http import JsonResponse
from datetime import datetime, timedelta, time
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.urls import reverse
from datetime import date
from .forms import AgendaMedicoForm,ConfiguracionAgendaForm,ExcepcionAgendaForm,SeleccionMedicoConsultaForm
from .models import DisponibilidadMedico,ExcepcionAgenda
from turnos.utils.agenda   import obtener_agenda_dia
from turnos.utils.utils_historial import registrar_historial_turno
from collections import defaultdict   
from core.models import CentroMedico
from core.utils import mostrar_exito, mostrar_error
def obtener_consultorio_disponible(fecha, hora_inicio, hora_fin, medico=None):

    consultorios = Consultorio.objects.all()

    for consultorio in consultorios:

        # 🔴 VALIDAR CONTRA AGENDA
        conflicto_agenda = AgendaMedico.objects.filter(
            fecha=fecha,
            consultorio=consultorio,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        )

        if medico:
            conflicto_agenda = conflicto_agenda.exclude(medico=medico)

        # 🔴 VALIDAR CONTRA TURNOS (CLAVE 🔥)
        conflicto_turnos = Turnos.objects.filter(
            fecha=fecha,
            consultorio=consultorio,
            hora__gte=hora_inicio,
            hora__lte=hora_fin,
            estado='PENDIENTE'
        )

        if not conflicto_agenda.exists() and not conflicto_turnos.exists():
            return consultorio

    return None


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

    # 🔵 SEDE ACTIVA
    
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
        centro_activo = CentroMedico.objects.filter(
            id=centro_id
        ).first()

    medico_id = request.session['medico_id']
    medico = get_object_or_404(Medico, id=medico_id)

    offset = int(request.GET.get('offset', 0))
    hoy = datetime.today().date() + timedelta(days=offset)

    # ✅ SOLO DÍAS CON AGENDA DE LA SEDE ACTIVA
    dias = []

    for i in range(6):

        dia = hoy + timedelta(days=i)

        agenda = obtener_agenda_dia(
            medico,
            dia,
            centro_activo
        )

        if agenda:
            dias.append(dia)

    disponibilidad = {}
    horarios_globales = set()

    for dia in dias:

        agenda = obtener_agenda_dia(
            medico,
            dia,
            centro_activo
        )

        if not agenda:
            continue

        horarios = []

        actual = datetime.combine(date.today(), agenda.hora_inicio)
        fin = datetime.combine(date.today(), agenda.hora_fin)

        while actual <= fin:

            horarios.append(actual.time())

            actual += timedelta(
                minutes=agenda.duracion_turno
                if hasattr(agenda, 'duracion_turno')
                else 20
            )

        horarios = sorted(horarios)

        # 🔥 SOLO HORARIOS DE LA AGENDA
        for h in horarios:
            horarios_globales.add(h)

        # 🔵 TURNOS DE LA SEDE ACTIVA
        turnos_dia = Turnos.objects.filter(
            medico=medico,
            fecha=dia,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        )

        # 🟡 SOBRETURNOS DE LA SEDE ACTIVA
        sobreturnos = Sobreturno.objects.filter(
            medico=medico,
            fecha=dia,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        )

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
    
    

    agendas_medico = AgendaMedico.objects.filter(
        medico=medico
    ).order_by('fecha')

    resumen_agenda = OrderedDict()

    for agenda in agendas_medico:

        dia = agenda.fecha.strftime('%A')

        dias_es = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo',
        }

        nombre_dia = dias_es[dia]

        resumen_agenda[nombre_dia] = {
            'inicio': agenda.hora_inicio.strftime('%H:%M'),
            'fin': agenda.hora_fin.strftime('%H:%M'),
            'duracion': agenda.duracion_turno,
            'consultorio': agenda.consultorio.numero
                if agenda.consultorio else '-'
        }

    return render(request, 'turnos/disponibilidad.html', {
        'medico': medico,
        'disponibilidad': disponibilidad,
         'resumen_agenda': resumen_agenda,
        'horarios': horarios_ordenados,
        'offset': offset,
    })
    
    
@login_required
def crear_sobreturno(request):

    if request.method == 'POST':

        # =====================================================
        # 🔵 SEDE ACTIVA
        # =====================================================

        centro_id = request.session.get('centro_id')

        centro_activo = None

        if centro_id:
                centro_activo = CentroMedico.objects.filter(
                    id=centro_id
                ).first()

        # =====================================================
        # 🔵 DATOS
        # =====================================================

        fecha_str = request.POST.get('fecha')

        hora_str = request.POST.get('hora_manual')

        observaciones = request.POST.get(
            'observaciones'
        )

        medico_id = request.session.get('medico_id')

        paciente_id = request.session.get('paciente_id')

        # =====================================================
        # 🔴 VALIDACIONES
        # =====================================================

        if not (
            fecha_str
            and hora_str
            and medico_id
            and paciente_id
        ):

            messages.error(
                request,
                "Faltan datos para el sobreturno."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 PARSEAR FECHA
        # =====================================================

        try:

            fecha = datetime.strptime(
                fecha_str,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            messages.error(
                request,
                "Formato de fecha inválido."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 PARSEAR HORA
        # =====================================================

        try:

            hora = datetime.strptime(
                hora_str,
                '%H:%M'
            ).time()

        except ValueError:

            messages.error(
                request,
                "Formato de hora inválido."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 AGENDA DE ESA SEDE
        # =====================================================

        agenda = AgendaMedico.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            centro_medico=centro_activo
        ).first()

        if not agenda:

            messages.error(
                request,
                "El médico no tiene agenda ese día en esta sede."
            )

            return redirect('turnos:ver_disponibilidad')

        consultorio = agenda.consultorio

        # =====================================================
        # 🔥 VALIDAR TURNO EXISTENTE
        # =====================================================

        existe_turno = Turnos.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        ).exists()

        # =====================================================
        # 🔥 VALIDAR SOBRETURNO EXISTENTE
        # =====================================================

        existe_sobreturno = Sobreturno.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        ).exists()

        if existe_turno or existe_sobreturno:

            messages.warning(
                request,
                "Ya existe un turno o sobreturno en ese horario."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 CREAR SOBRETURNO
        # =====================================================

        sobreturno = Sobreturno.objects.create(

            centro_medico=centro_activo,

            sede_operacion=centro_activo,

            creado_por=request.user,

            medico_id=medico_id,

            paciente_id=paciente_id,

            fecha=fecha,

            hora=hora,

            observaciones=observaciones,

            estado='PENDIENTE'
        )

        # =====================================================
        # 🔥 HISTORIAL
        # =====================================================

        # 🔥 SOLO SI USÁS HISTORIAL SOBRE TURNOS
        # SI QUERÉS HISTORIAL PARA SOBRETURNOS
        # DESPUÉS HACEMOS HistorialSobreturno

        messages.success(
            request,
            f"Sobreturno creado correctamente en Consultorio {consultorio.numero}."
        )

    return redirect('turnos:ver_disponibilidad')
@login_required
def reservar_turno(request):

    if request.method == 'POST':

        # =====================================================
        # 🔵 SEDE ACTIVA
        # =====================================================

        centro_id = request.session.get('centro_id')

        centro_activo = None

        if centro_id:
                centro_activo = CentroMedico.objects.filter(
                    id=centro_id
                ).first()

        # =====================================================
        # 🔵 DATOS FORMULARIO
        # =====================================================

        fecha_str = request.POST.get('fecha')

        hora_str = request.POST.get('hora')

        hora_manual = request.POST.get('hora_manual')

        observaciones = request.POST.get(
            'observaciones',
            ''
        )

        es_sobreturno = (
            request.POST.get('es_sobreturno') == 'true'
        )

        # =====================================================
        # 🔴 VALIDAR FECHA
        # =====================================================

        if not fecha_str:

            messages.error(
                request,
                "Falta la fecha."
            )

            return redirect('turnos:ver_disponibilidad')

        try:

            fecha = datetime.strptime(
                fecha_str,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            messages.error(
                request,
                "Error en el formato de fecha."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔵 SESIÓN
        # =====================================================

        medico_id = request.session.get('medico_id')

        paciente_id = request.session.get('paciente_id')

        especialidad_id = request.session.get('especialidad_id')

        if not medico_id or not paciente_id:

            messages.error(
                request,
                "Error de sesión."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 AGENDA DE ESA SEDE
        # =====================================================

        agenda = AgendaMedico.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            centro_medico=centro_activo
        ).first()

        if not agenda:

            messages.error(
                request,
                "El médico no tiene agenda para ese día en esta sede."
            )

            return redirect('turnos:ver_disponibilidad')

        consultorio = agenda.consultorio

        # =====================================================
        # 🔵 CASO SOBRETURNO
        # =====================================================

        if es_sobreturno:

            if not hora_manual:

                messages.error(
                    request,
                    "Debes ingresar la hora del sobreturno."
                )

                return redirect('turnos:ver_disponibilidad')

            try:

                hora = datetime.strptime(
                    hora_manual,
                    '%H:%M'
                ).time()

            except ValueError:

                messages.error(
                    request,
                    "Formato de hora inválido."
                )

                return redirect('turnos:ver_disponibilidad')

            # =================================================
            # 🔥 VALIDAR EXISTENTE
            # =================================================

            ya_existe = Turnos.objects.filter(
                medico_id=medico_id,
                fecha=fecha,
                hora=hora,
                centro_medico=centro_activo
            ).exclude(
                estado='CANCELADO'
            ).exists()

            if ya_existe:

                messages.warning(
                    request,
                    "Ya existe un turno en ese horario."
                )

                return redirect('turnos:ver_disponibilidad')

            # =================================================
            # 🔥 CREAR SOBRETURNO
            # =================================================

            turno = Turnos.objects.create(

                centro_medico=centro_activo,

                sede_operacion=centro_activo,

                creado_por=request.user,

                especialidad_id=especialidad_id,

                medico_id=medico_id,

                paciente_id=paciente_id,

                fecha=fecha,

                hora=hora,

                observaciones=observaciones,

                estado='PENDIENTE',

                es_sobreturno=True
            )

            # =================================================
            # 🔥 HISTORIAL
            # =================================================

            registrar_historial_turno(

                turno=turno,

                accion='CREADO',

                usuario=request.user,

                sede_operacion=centro_activo,

                descripcion='Sobreturno creado'
            )

            messages.success(
                request,
                f"Sobreturno agregado correctamente en Consultorio {consultorio.numero}."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔵 CASO TURNO NORMAL
        # =====================================================

        if not hora_str:

            messages.error(
                request,
                "Falta la hora del turno."
            )

            return redirect('turnos:ver_disponibilidad')

        try:

            hora = datetime.strptime(
                hora_str,
                '%H:%M'
            ).time()

        except ValueError:

            messages.error(
                request,
                "Formato de hora inválido."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 VALIDAR EXISTENTE
        # =====================================================

        ya_existe = Turnos.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            es_sobreturno=False,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        ).exists()

        if ya_existe:

            messages.warning(
                request,
                "Ese turno ya fue reservado."
            )

            return redirect('turnos:ver_disponibilidad')

        # =====================================================
        # 🔥 CREAR TURNO NORMAL
        # =====================================================

        turno = Turnos.objects.create(

            centro_medico=centro_activo,

            sede_operacion=centro_activo,

            creado_por=request.user,

            especialidad_id=especialidad_id,

            medico_id=medico_id,

            paciente_id=paciente_id,

            fecha=fecha,

            hora=hora,

            observaciones=observaciones,

            estado='PENDIENTE',

            es_sobreturno=False
        )

        # =====================================================
        # 🔥 HISTORIAL
        # =====================================================

        registrar_historial_turno(

            turno=turno,

            accion='CREADO',

            usuario=request.user,

            sede_operacion=centro_activo,

            descripcion='Turno normal creado'
        )

        messages.success(
            request,
            f"Turno reservado correctamente en Consultorio {consultorio.numero}."
        )

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
    turnos_futuros = []

    if dni:

        try:

            paciente = Paciente.objects.get(dni=dni)

            hoy = date.today()

            # 🔵 TURNOS NORMALES
            turnos_normales = Turnos.objects.filter(
                paciente=paciente,
                fecha__gte=hoy
            ).order_by('fecha', 'hora')

            # 🟡 SOBRETURNOS
            sobreturnos = Sobreturno.objects.filter(
                paciente=paciente,
                fecha__gte=hoy
            ).order_by('fecha', 'hora')

            # IDENTIFICAR TIPO
            for turno in turnos_normales:
                turno.tipo_turno = 'NORMAL'

            for sobreturno in sobreturnos:
                sobreturno.tipo_turno = 'SOBRETURNO'

            # 🔥 UNIFICAR
            turnos_futuros = list(turnos_normales) + list(sobreturnos)

            # 🔥 ORDENAR
            turnos_futuros.sort(
                key=lambda x: (x.fecha, x.hora)
            )

        except Paciente.DoesNotExist:

            messages.warning(
                request,
                "No se encontró paciente con ese DNI."
            )

    return render(request, 'turnos/buscar_turnos_dni.html', {
        'paciente': paciente,
        'turnos': turnos_futuros
    })   

""" @login_required
def mis_turnos_medico(request):

    if not hasattr(request.user, 'medico'):

        messages.warning(
            request,
            "No tienes perfil médico."
        )

        return redirect('core:index')

    medico = request.user.medico

    hoy = date.today()

    ahora = datetime.now().time()

    filtro = request.GET.get("filtro")

    fecha = request.GET.get("fecha")

    mes = request.GET.get("mes")
    
    sede = request.GET.get("sede")
    # =====================================================
    # 🔵 TURNOS GLOBALES DEL MÉDICO
    # =====================================================

    turnos_normales = Turnos.objects.filter(
        medico=medico
    ).select_related(
        'paciente',
        'centro_medico',
        'sede_operacion',
        'creado_por',
        'cancelado_por'
    )

    sobreturnos = Sobreturno.objects.filter(
        medico=medico
    ).select_related(
        'paciente',
        'centro_medico',
        'sede_operacion',
        'creado_por',
        'cancelado_por'
    )

    # 🔥 UNIFICAR
    turnos = list(turnos_normales) + list(sobreturnos)

    # =====================================================
    # 🔥 FILTROS
    # =====================================================

    def filtrar(turno):
        if sede:

            if not turno.centro_medico:
                return False

            if str(turno.centro_medico.id) != sede:
                return False
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

                return (
                    turno.fecha.year == int(year)
                    and turno.fecha.month == int(month)
                )

            except ValueError:

                return True

        else:

            return turno.fecha == hoy

    turnos = list(filter(filtrar, turnos))

    # =====================================================
    # 🔥 AGREGAR DATOS VISUALES
    # =====================================================

    for t in turnos:

        # 🔵 TIPO
        if isinstance(t, Sobreturno):

            t.tipo = "Sobreturno"

        else:

            t.tipo = "Turno"

        # 🔵 SEDE
        t.sede_nombre = (
            t.centro_medico.nombre
            if t.centro_medico
            else "Sin sede"
        )

        # 🔵 ESTADO VISUAL
        if t.estado == 'PENDIENTE':

            t.estado_color = 'warning'

        elif t.estado == 'ATENDIDO':

            t.estado_color = 'success'

        elif t.estado == 'AUSENTE':

            t.estado_color = 'secondary'

        elif t.estado == 'CANCELADO':

            t.estado_color = 'danger'

        else:

            t.estado_color = 'light'

        # 🔵 CREADO POR
        t.usuario_creador = (
            t.creado_por.username
            if t.creado_por
            else "Sistema"
        )

        # 🔵 CANCELADO POR
        t.usuario_cancelacion = (
            t.cancelado_por.username
            if hasattr(t, 'cancelado_por') and t.cancelado_por
            else None
        )

    # =====================================================
    # 🔥 ORDENAR
    # =====================================================

    turnos = sorted(
        turnos,
        key=lambda x: (
            x.fecha,
            x.hora
        )
    )

    # =====================================================
    # 🔥 CONTADOR HOY
    # =====================================================

    turnos_hoy_count = (

        Turnos.objects.filter(
            medico=medico,
            fecha=hoy
        ).count()

        +

        Sobreturno.objects.filter(
            medico=medico,
            fecha=hoy
        ).count()
    )

    # =====================================================
    centros = CentroMedico.objects.all()
    return render(request, "turnos/mis_turnos_medico.html", {

        "turnos": turnos,
        "centros": centros,

        "hoy": hoy,

        "ahora": ahora,

        "turnos_hoy_count": turnos_hoy_count
    })
 """
@login_required
def mis_turnos_medico(request):

    if not hasattr(request.user, 'medico'):

        messages.warning(
            request,
            "No tienes perfil médico."
        )

        return redirect('core:index')

    medico = request.user.medico

    hoy = date.today()

    ahora = datetime.now().time()

    filtro = request.GET.get("filtro")

    fecha = request.GET.get("fecha")

    mes = request.GET.get("mes")

    sede = request.GET.get("sede")

    # =====================================================
    # 🔵 SOLO TURNOS PENDIENTES
    # =====================================================

    turnos_normales = Turnos.objects.filter(
        medico=medico,
        estado='PENDIENTE'
    ).select_related(
        'paciente',
        'centro_medico',
        'sede_operacion',
        'creado_por',
        'cancelado_por'
    )

    sobreturnos = Sobreturno.objects.filter(
        medico=medico,
        estado='PENDIENTE'
    ).select_related(
        'paciente',
        'centro_medico',
        'sede_operacion',
        'creado_por',
        'cancelado_por'
    )

    # =====================================================
    # 🔥 UNIFICAR
    # =====================================================

    turnos = list(turnos_normales) + list(sobreturnos)

    # =====================================================
    # 🔥 FILTROS
    # =====================================================

    def filtrar(turno):

        # 🔵 FILTRO POR SUCURSAL
        if sede:

            if not turno.centro_medico:
                return False

            if str(turno.centro_medico.id) != sede:
                return False

        # 🔵 FILTRO RÁPIDO
        if filtro == "hoy":

            return turno.fecha == hoy

        elif filtro == "manana":

            return turno.fecha == hoy + timedelta(days=1)

        elif filtro == "semana":

            return hoy <= turno.fecha <= hoy + timedelta(days=7)

        # 🔵 FILTRO POR FECHA
        elif fecha:

            return str(turno.fecha) == fecha

        # 🔵 FILTRO POR MES
        elif mes:

            try:

                year, month = mes.split("-")

                return (
                    turno.fecha.year == int(year)
                    and turno.fecha.month == int(month)
                )

            except ValueError:

                return True

        # 🔵 POR DEFECTO: HOY
        else:

            return turno.fecha == hoy

    turnos = list(filter(filtrar, turnos))

    # =====================================================
    # 🔥 DATOS VISUALES
    # =====================================================

    for t in turnos:

        # 🔵 TIPO

        if isinstance(t, Sobreturno):

            t.tipo = "Sobreturno"

        else:

            t.tipo = "Turno"

        # 🔵 NOMBRE DE SEDE

        t.sede_nombre = (

            t.centro_medico.nombre

            if t.centro_medico

            else "Sin sede"
        )

        # 🔵 COLOR ESTADO

        if t.estado == 'PENDIENTE':

            t.estado_color = 'warning'

        elif t.estado == 'ATENDIDO':

            t.estado_color = 'success'

        elif t.estado == 'AUSENTE':

            t.estado_color = 'secondary'

        elif t.estado == 'CANCELADO':

            t.estado_color = 'danger'

        else:

            t.estado_color = 'light'

        # 🔵 USUARIO CREADOR

        t.usuario_creador = (

            t.creado_por.username

            if t.creado_por

            else "Sistema"
        )

        # 🔵 USUARIO CANCELACIÓN

        t.usuario_cancelacion = (

            t.cancelado_por.username

            if hasattr(t, 'cancelado_por')
            and t.cancelado_por

            else None
        )

    # =====================================================
    # 🔥 ORDENAR
    # =====================================================

    turnos = sorted(
        turnos,
        key=lambda x: (
            x.fecha,
            x.hora
        )
    )

    # =====================================================
    # 🔥 CONTADOR DEL DÍA
    # SOLO PENDIENTES
    # =====================================================

    turnos_hoy_count = (

        Turnos.objects.filter(
            medico=medico,
            fecha=hoy,
            estado='PENDIENTE'
        ).count()

        +

        Sobreturno.objects.filter(
            medico=medico,
            fecha=hoy,
            estado='PENDIENTE'
        ).count()
    )

    # =====================================================
    # 🔥 SUCURSALES PARA FILTRO
    # =====================================================

    centros = CentroMedico.objects.all()

    # =====================================================

    return render(
        request,
        "turnos/mis_turnos_medico.html",
        {

            "turnos": turnos,

            "centros": centros,

            "hoy": hoy,

            "ahora": ahora,

            "turnos_hoy_count": turnos_hoy_count,
        }
    )




from django.utils import timezone
@login_required
def marcar_ausente(request, turno_id):

    # 🔵 SEDE ACTIVA
    centro_activo = request.centro_activo

    turno = Turnos.objects.filter(
        id=turno_id,
        centro_medico=centro_activo
    ).first()

    es_sobreturno = False

    # 🔵 BUSCAR SOBRETURNO
    if not turno:

        turno = Sobreturno.objects.filter(
            id=turno_id,
            centro_medico=centro_activo
        ).first()

        es_sobreturno = True

    # 🔴 NO EXISTE
    if not turno:

        messages.error(
            request,
            "El turno no existe en esta sede."
        )

        return redirect('turnos:ver_disponibilidad')

    # 🔥 TRAZABILIDAD
    turno.estado = 'CANCELADO'

    turno.cancelado_por = request.user

    turno.fecha_cancelacion = timezone.now()

    # 🔵 DESDE QUÉ SEDE SE OPERÓ
    if hasattr(turno, 'sede_operacion'):

        turno.sede_operacion = centro_activo

    turno.save()

    # 🔵 MENSAJES
    if es_sobreturno:

        messages.warning(
            request,
            "Sobreturno marcado como ausente."
        )

    else:

        messages.warning(
            request,
            "Turno marcado como ausente."
        )

    return redirect('turnos:ver_disponibilidad')    

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
 
@login_required
def historial_turnos_medico(request):

    if not hasattr(request.user, 'medico'):

        messages.warning(
            request,
            "No tienes perfil médico."
        )

        return redirect('core:index')

    medico = request.user.medico

    hoy = date.today()

    filtro = request.GET.get("filtro")

    fecha = request.GET.get("fecha")

    mes = request.GET.get("mes")

    sede = request.GET.get("sede")

    estado = request.GET.get("estado")

    # ==========================================
    # SOLO HISTORIAL
    # ==========================================

    estados_historial = [
        'ATENDIDO',
        'AUSENTE',
        'CANCELADO'
    ]

    turnos_normales = Turnos.objects.filter(
        medico=medico,
        estado__in=estados_historial
    ).select_related(
        'paciente',
        'centro_medico'
    )

    sobreturnos = Sobreturno.objects.filter(
        medico=medico,
        estado__in=estados_historial
    ).select_related(
        'paciente',
        'centro_medico'
    )

    turnos = list(turnos_normales) + list(sobreturnos)

    # ==========================================
    # FILTROS
    # ==========================================

    def filtrar(turno):

        if sede:

            if not turno.centro_medico:
                return False

            if str(turno.centro_medico.id) != sede:
                return False

        if estado:

            if turno.estado != estado:
                return False

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

                return (
                    turno.fecha.year == int(year)
                    and turno.fecha.month == int(month)
                )

            except ValueError:

                return True

        return True

    turnos = list(filter(filtrar, turnos))

    # ==========================================
    # DATOS VISUALES
    # ==========================================

    for t in turnos:

        if isinstance(t, Sobreturno):

            t.tipo = "Sobreturno"

        else:

            t.tipo = "Turno"

        t.sede_nombre = (
            t.centro_medico.nombre
            if t.centro_medico
            else "Sin sede"
        )

        if t.estado == 'ATENDIDO':

            t.estado_color = 'success'

        elif t.estado == 'AUSENTE':

            t.estado_color = 'secondary'

        elif t.estado == 'CANCELADO':

            t.estado_color = 'danger'

        else:

            t.estado_color = 'light'

    # ==========================================
    # ORDENAR
    # ==========================================

    turnos = sorted(
        turnos,
        key=lambda x: (
            x.fecha,
            x.hora
        ),
        reverse=True
    )

    # ==========================================
    # CONTADORES
    # ==========================================

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

    centros = CentroMedico.objects.all()

    return render(
        request,
        'turnos/historial_turnos_medico.html',
        {
            'turnos': turnos,
            'centros': centros,
            'atendidos': atendidos,
            'ausentes': ausentes,
            'cancelados': cancelados,
        }
    )


@login_required
def agenda_mensual_medico(request):

    # 🔵 SEDE ACTIVA
    centro_activo = request.centro_activo

    medicos = Medico.objects.all()
    medico = None
    dias_final = []

    medico_id = request.GET.get('medico_id') or request.POST.get('medico_id')

    consultorio = None

    # 🔵 SI VIENE CONSULTORIO
    consultorio_id = request.POST.get('consultorio')

    if consultorio_id:

        consultorio = get_object_or_404(
            Consultorio,
            id=consultorio_id,
            centro_medico=centro_activo
        )

    # 🔵 SI SELECCIONÓ MÉDICO
    if medico_id:

        medico = get_object_or_404(
            Medico,
            id=medico_id
        )

        hoy = date.today()

        # 🔥 AGRUPAR POR DÍA
        dias_agrupados = defaultdict(list)

        for i in range(30):

            dia = hoy + timedelta(days=i)

            # ❌ EXCLUIR SÁBADO Y DOMINGO
            if dia.weekday() in [5, 6]:
                continue

            # 🔵 SOLO AGENDA DE LA SEDE ACTIVA
            agenda_dia = AgendaMedico.objects.filter(
                medico=medico,
                fecha=dia,
                centro_medico=centro_activo
            ).first()

            dias_agrupados[dia.weekday()].append({
                'fecha': dia,
                'agenda': agenda_dia
            })

        # 🔥 ORDENAR LUNES → VIERNES
        nombres_dias = [
            'Lunes',
            'Martes',
            'Miércoles',
            'Jueves',
            'Viernes'
        ]

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

                # ❌ SI NO CARGA HORARIO → ELIMINAR
                if not hora_inicio or not hora_fin:

                    AgendaMedico.objects.filter(
                        medico=medico,
                        fecha=dia,
                        centro_medico=centro_activo
                    ).delete()

                    continue

                try:

                    hora_inicio = datetime.strptime(
                        hora_inicio,
                        '%H:%M'
                    ).time()

                    hora_fin = datetime.strptime(
                        hora_fin,
                        '%H:%M'
                    ).time()

                except ValueError:
                    continue

                # 🔵 CREAR / ACTUALIZAR AGENDA
                AgendaMedico.objects.update_or_create(

                    medico=medico,
                    fecha=dia,
                    centro_medico=centro_activo,

                    defaults={
                        'hora_inicio': hora_inicio,
                        'hora_fin': hora_fin,
                        'consultorio': consultorio,
                        'duracion_turno': 20,
                        'centro_medico': centro_activo
                    }
                )

        messages.success(
            request,
            f"Agenda guardada correctamente para {centro_activo.nombre}."
        )

        return redirect(f'?medico_id={medico.id}')

    # 🔵 CONSULTORIOS SOLO DE LA SEDE ACTIVA
    consultorios = Consultorio.objects.filter(
        centro_medico=centro_activo
    ).order_by('numero')

    return render(request, 'turnos/agenda_mensual.html', {
        'medicos': medicos,
        'medico': medico,
        'dias_final': dias_final,
        'consultorios': consultorios,
        'centro_activo': centro_activo
    })

def generar_preview(data):
    print("DATA:")
    print(data)
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
        if wd == 5 and data['sabado']:
            dias_preview.append({
                'fecha': dia,
                'inicio': data['sabado_inicio'],
                'fin': data['sabado_fin']
            })

        dia += timedelta(days=1)

    return dias_preview

@login_required
def crear_excepcion(request):

    # =====================================================
    # 🔵 SEDE ACTIVA
    # =====================================================
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
        centro_activo = CentroMedico.objects.filter(
            id=centro_id
        ).first()
    

    medicos = Medico.objects.all()

    medico_id = request.GET.get('medico_id')

    medico = None

    if medico_id:

        medico = Medico.objects.filter(
            id=medico_id
        ).first()

    # =====================================================
    # 🔥 CONSULTORIO DISPONIBLE
    # =====================================================

    def obtener_consultorio_disponible(
        fecha,
        hora_inicio,
        hora_fin,
        medico=None
    ):

        consultorios = Consultorio.objects.filter(
            centro_medico=centro_activo
        )

        for consultorio in consultorios:

            # 🔵 CONFLICTO AGENDA
            conflicto_agenda = AgendaMedico.objects.filter(
                fecha=fecha,
                consultorio=consultorio,
                centro_medico=centro_activo,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio
            )

            if medico:

                conflicto_agenda = conflicto_agenda.exclude(
                    medico=medico
                )

            # 🔵 MÉDICOS EN CONSULTORIO
            medicos_en_consultorio = AgendaMedico.objects.filter(
                fecha=fecha,
                consultorio=consultorio,
                centro_medico=centro_activo
            ).values_list(
                'medico_id',
                flat=True
            )

            # 🔴 TURNOS
            conflicto_turnos = Turnos.objects.filter(
                fecha=fecha,
                centro_medico=centro_activo,
                medico_id__in=medicos_en_consultorio,
                hora__gte=hora_inicio,
                hora__lt=hora_fin,
                estado='PENDIENTE'
            )

            # 🟡 SOBRETURNOS
            conflicto_sobreturnos = Sobreturno.objects.filter(
                fecha=fecha,
                centro_medico=centro_activo,
                medico_id__in=medicos_en_consultorio,
                hora__gte=hora_inicio,
                hora__lt=hora_fin
            ).exclude(
                estado='CANCELADO'
            )

            if (
                not conflicto_agenda.exists()
                and not conflicto_turnos.exists()
                and not conflicto_sobreturnos.exists()
            ):

                return consultorio

        return None

    # =====================================================
    # 🔵 POST
    # =====================================================

    if request.method == 'POST':

        form = ExcepcionAgendaForm(request.POST)

        if form.is_valid():

            data = form.cleaned_data

            # =================================================
            # 🔥 CREAR EXCEPCIÓN
            # =================================================

            excepcion, created = ExcepcionAgenda.objects.update_or_create(

                medico=medico,

                fecha=data['fecha'],

                centro_medico=centro_activo,

                defaults={

                    'tipo': data['tipo'],

                    'hora_inicio': data.get('hora_inicio'),

                    'hora_fin': data.get('hora_fin'),

                    'nueva_fecha': data.get('nueva_fecha'),

                    'motivo': data.get('motivo'),

                    'centro_medico': centro_activo,

                    'creado_por': request.user,

                    'sede_operacion': centro_activo
                }
            )

            # =================================================
            # 🔵 TURNOS
            # =================================================

            turnos = Turnos.objects.filter(
                medico=medico,
                fecha=excepcion.fecha,
                centro_medico=centro_activo
            )

            # =================================================
            # 🟡 SOBRETURNOS
            # =================================================

            sobreturnos = Sobreturno.objects.filter(
                medico=medico,
                fecha=excepcion.fecha,
                centro_medico=centro_activo
            )

            # =================================================
            # 🔵 AGENDA ORIGINAL
            # =================================================

            agenda_original = AgendaMedico.objects.filter(
                medico=medico,
                fecha=excepcion.fecha,
                centro_medico=centro_activo
            ).first()

            # =================================================
            # 🔴 CERRADO
            # =================================================

            if excepcion.tipo == 'CERRADO':

                for turno in turnos:

                    turno.estado = 'CANCELADO'

                    turno.cancelado_por = request.user

                    turno.fecha_cancelacion = timezone.now()

                    turno.sede_operacion = centro_activo

                    turno.save()

                    registrar_historial_turno(

                        turno=turno,

                        accion='EXCEPCION',

                        usuario=request.user,

                        sede_operacion=centro_activo,

                        descripcion='Turno cancelado por excepción tipo CERRADO'
                    )

                for s in sobreturnos:

                    s.estado = 'CANCELADO'

                    s.cancelado_por = request.user

                    s.fecha_cancelacion = timezone.now()

                    s.sede_operacion = centro_activo

                    s.save()

                AgendaMedico.objects.filter(
                    medico=medico,
                    fecha=excepcion.fecha,
                    centro_medico=centro_activo
                ).delete()

                messages.warning(
                    request,
                    f"Se cancelaron {turnos.count()} turnos y se liberó el consultorio."
                )

            # =================================================
            # 🟡 REPROGRAMAR
            # =================================================
            elif excepcion.tipo == 'REPROGRAMAR':

                consultorio = obtener_consultorio_disponible(
                    excepcion.nueva_fecha,
                    excepcion.hora_inicio,
                    excepcion.hora_fin,
                    medico
                )

                if not consultorio:

                    messages.error(
                        request,
                        "No hay consultorios disponibles en la nueva fecha."
                    )

                    return redirect('turnos:crear_excepcion')

                # =============================================
                # 🔵 CREAR NUEVA AGENDA
                # =============================================

                AgendaMedico.objects.update_or_create(

                    medico=medico,

                    fecha=excepcion.nueva_fecha,

                    centro_medico=centro_activo,

                    defaults={

                        'hora_inicio': excepcion.hora_inicio,

                        'hora_fin': excepcion.hora_fin,

                        'duracion_turno':
                            agenda_original.duracion_turno
                            if agenda_original else 20,

                        'consultorio': consultorio,

                        'centro_medico': centro_activo,

                        'modificado_por': request.user,

                        'sede_operacion': centro_activo
                    }
                )

                # =============================================
                # 🔴 CANCELAR TODOS LOS TURNOS
                # =============================================

                cancelados = 0

                for turno in turnos:

                    turno.estado = 'CANCELADO'

                    turno.cancelado_por = request.user

                    turno.fecha_cancelacion = timezone.now()

                    turno.sede_operacion = centro_activo

                    turno.save()

                    registrar_historial_turno(

                        turno=turno,

                        accion='REPROGRAMADO',

                        usuario=request.user,

                        sede_operacion=centro_activo,

                        descripcion=(
                            f'Agenda reprogramada para '
                            f'{excepcion.nueva_fecha}. '
                            f'Turno cancelado para '
                            f'reprogramación manual.'
                        )
                    )

                    cancelados += 1

                # =============================================
                # 🔴 CANCELAR TODOS LOS SOBRETURNOS
                # =============================================

                sobreturnos_cancelados = 0

                for s in sobreturnos:

                    s.estado = 'CANCELADO'

                    s.cancelado_por = request.user

                    s.fecha_cancelacion = timezone.now()

                    s.sede_operacion = centro_activo

                    s.save()

                    sobreturnos_cancelados += 1

                messages.warning(

                    request,

                    f"Se cancelaron "
                    f"{cancelados} turnos y "
                    f"{sobreturnos_cancelados} sobreturnos. "
                    f"La nueva agenda fue creada para "
                    f"{excepcion.nueva_fecha}. "
                    f"Los pacientes deberán ser "
                    f"reprogramados manualmente."
                )

            # =================================================
            # 🟢 MODIFICADO
            # =================================================

            elif excepcion.tipo == 'MODIFICADO':

                consultorio = obtener_consultorio_disponible(
                    excepcion.fecha,
                    excepcion.hora_inicio,
                    excepcion.hora_fin,
                    medico
                )

                if not consultorio:

                    messages.error(
                        request,
                        "No hay consultorios disponibles."
                    )

                    return redirect('turnos:crear_excepcion')

                AgendaMedico.objects.update_or_create(

                    medico=medico,

                    fecha=excepcion.fecha,

                    centro_medico=centro_activo,

                    defaults={

                        'hora_inicio': excepcion.hora_inicio,

                        'hora_fin': excepcion.hora_fin,

                        'consultorio': consultorio,

                        'centro_medico': centro_activo,

                        'modificado_por': request.user,

                        'sede_operacion': centro_activo
                    }
                )

                cancelados = 0

                for turno in turnos:

                    if not (
                        excepcion.hora_inicio
                        <= turno.hora
                        <= excepcion.hora_fin
                    ):

                        turno.estado = 'CANCELADO'

                        turno.cancelado_por = request.user

                        turno.fecha_cancelacion = timezone.now()

                        turno.sede_operacion = centro_activo

                        turno.save()

                        registrar_historial_turno(

                            turno=turno,

                            accion='MODIFICADO',

                            usuario=request.user,

                            sede_operacion=centro_activo,

                            descripcion='Turno cancelado por modificación de agenda'
                        )

                        cancelados += 1

                for s in sobreturnos:

                    if not (
                        excepcion.hora_inicio
                        <= s.hora
                        <= excepcion.hora_fin
                    ):

                        s.estado = 'CANCELADO'

                        s.cancelado_por = request.user

                        s.fecha_cancelacion = timezone.now()

                        s.sede_operacion = centro_activo

                        s.save()

                messages.warning(
                    request,
                    f"Se cancelaron {cancelados} turnos. Consultorio: {consultorio.numero}"
                )

            # =================================================
            # 🔥 OK
            # =================================================

            messages.success(
                request,
                "Excepción aplicada correctamente."
            )

            url = reverse(
                'turnos:excepciones_detalle'
            )

            return redirect(
                f"{url}?medico_id={medico.id}&fecha={excepcion.fecha}"
            )

    else:

        form = ExcepcionAgendaForm()

    return render(request, 'turnos/excepcion_form.html', {

        'form': form,

        'medico': medico,

        'medicos': medicos,

        'centro_activo': centro_activo
    })


@login_required
def agenda_rapida(request):
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
        centro_activo = CentroMedico.objects.filter(
            id=centro_id
        ).first()
    preview = None
    conflictos = []
    pisando_agenda = False
    consultorios_disponibles = []

    medicos = Medico.objects.all()

    # 🔵 Capturar médico
    medico_id = request.GET.get('medico_id') or request.POST.get('medico')
    medico = None

    if medico_id:
        medico = Medico.objects.filter(id=medico_id).first()

    # 🔵 POST
    if request.method == 'POST':

        # ===============================
        # 🟢 CONFIRMAR (PRIMERO 🔥)
        # ===============================
        if 'confirmar' in request.POST:

            form = ConfiguracionAgendaForm(request.POST)
            form.fields['medico'].queryset = medicos

            if not form.is_valid():
                print("ERRORES CONFIRMAR:", form.errors)
                mostrar_error(

                    request,

                    titulo="No fue posible crear la agenda",

                    mensaje="Hay errores en los datos ingresados.",

                )

                return redirect(
                    "turnos:agenda_rapida"
                )
                

            data = form.cleaned_data
            medico = data['medico']

            from .models import Consultorio

            consultorio_id = request.POST.get('consultorio')

            if not consultorio_id:
                mostrar_error(

                    request,

                    titulo="Consultorio requerido",

                    mensaje="Debe seleccionar un consultorio para generar la agenda.",

                )
                
                

            consultorio = Consultorio.objects.get(id=consultorio_id)

            # 🔥 GENERAR PREVIEW CORRECTO
            preview = generar_preview(data)
            print("PREVIEW:", preview)
            

            for d in preview:

                hora_inicio = datetime.strptime(d['inicio'], '%H:%M').time()
                hora_fin = datetime.strptime(d['fin'], '%H:%M').time()

                AgendaMedico.objects.update_or_create(
                    centro_medico=centro_activo,
                    medico=medico,
                    fecha=d['fecha'],
                    defaults={
                        'hora_inicio': hora_inicio,
                        'hora_fin': hora_fin,
                        'duracion_turno': int(
                            data['duracion_turno']
                        ),
                        'consultorio': consultorio
                    }
                )

            mostrar_exito(

                request,

                titulo="Agenda creada",

                mensaje="La agenda se creó correctamente.",

                icono="bi-calendar2-check",

                detalles=[

                    f"Médico: {medico}",

                    f"Consultorio: {consultorio}",

                    f"Días generados: {len(preview)}",

                    f"Duración: {data['duracion_turno']} minutos",

                ],

            )

            return redirect(
                "turnos:agenda_rapida"
)

        # ===============================
        # 🔵 PREVIEW
        # ===============================
        form = ConfiguracionAgendaForm(request.POST)
        form.fields['medico'].queryset = medicos

        # 🔥 FIX → forzar médico si no viene
        if not request.POST.get('medico') and medico_id:
            form.data = form.data.copy()
            form.data['medico'] = medico_id

        if form.is_valid():
            print("FORM VALIDO:", form.is_valid())
            print("ERRORES:", form.errors)

            data = form.cleaned_data
            medico = data['medico']

            # 🔥 GENERAR PREVIEW
            preview = generar_preview(data)
            print("Previews", preview)

            # ===============================
            # 🔴 DETECTAR CONFLICTOS DEL MÉDICO
            # ===============================
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

            # ===============================
            # 🔥 CONSULTORIOS DISPONIBLES
            # ===============================
            from .models import Consultorio

            consultorios = Consultorio.objects.filter(
                centro_medico=centro_activo
)

            consultorios_disponibles = []

            for c in consultorios:

                ocupado = False

                for d in preview:

                    hora_inicio = datetime.strptime(d['inicio'], '%H:%M').time()
                    hora_fin = datetime.strptime(d['fin'], '%H:%M').time()

                    conflicto = AgendaMedico.objects.filter(
                        fecha=d['fecha'],
                        consultorio=c,
                        hora_inicio__lt=hora_fin,
                        hora_fin__gt=hora_inicio
                    ).exists()

                    if conflicto:
                        ocupado = True
                        break

                if not ocupado:
                    consultorios_disponibles.append(c)

            # 🔔 AVISO
            if pisando_agenda:
                messages.warning(
                    request,
                    "⚠️ Esta agenda pisa horarios existentes. Confirmá para continuar."
                )

        else:
            print("ERRORES PREVIEW:", form.errors)

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
        'conflictos_fechas': conflictos_fechas,
        'consultorios_disponibles': consultorios_disponibles
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
    
@login_required
def ver_disponibilidad_consulta(request):

    # 🔵 SEDE ACTIVA
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
        centro_activo = CentroMedico.objects.filter(
            id=centro_id
        ).first()

    medico_id = request.GET.get('medico_id')

    if not medico_id:
        return redirect('turnos:seleccionar_medico')

    medico = get_object_or_404(
        Medico,
        id=medico_id
    )

    offset = int(
        request.GET.get('offset', 0)
    )

    hoy = datetime.today().date() + timedelta(days=offset)

    dias = [
        hoy + timedelta(days=i)
        for i in range(6)
    ]

    disponibilidad = {}

    horarios_globales = set()

    for dia in dias:

        # 🔥 MULTI-SEDE
        agenda = obtener_agenda_dia(
            medico,
            dia,
            centro_activo
        )

        # 🔴 SI NO ATIENDE → NO MOSTRAR
        if not agenda:
            continue

        horarios = []

        # 🔵 GENERAR HORARIOS DE AGENDA
        actual = datetime.combine(
            date.today(),
            agenda.hora_inicio
        )

        fin = datetime.combine(
            date.today(),
            agenda.hora_fin
        )

        while actual <= fin:

            horarios.append(
                actual.time()
            )

            actual += timedelta(
                minutes=agenda.duracion_turno
            )

        horarios = sorted(horarios)

        # 🔵 AGREGAR HORARIOS BASE
        for h in horarios:
            horarios_globales.add(h)

        turnos_dia = Turnos.objects.filter(
            medico=medico,
            fecha=dia,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        )

        # 🟡 SOBRETURNOS
        sobreturnos = Sobreturno.objects.filter(
            medico=medico,
            fecha=dia,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        )

        dia_data = []

        # 🔵 ARMAR TURNOS BASE
        for hora in horarios:

            turno = turnos_dia.filter(
                hora=hora
            ).first()

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

            horarios_globales.add(
                s.hora
            )

            dia_data.append({

                'hora': s.hora,

                'estado': 'sobreturno',

                'paciente': s.paciente,

                'observaciones': s.observaciones,
            })

        # 🔥 ORDENAR POR HORA
        dia_data = sorted(
            dia_data,
            key=lambda x: x['hora']
        )

        disponibilidad[dia] = dia_data

    horarios_ordenados = sorted(
        horarios_globales
    )
    # ===============================
    # 🔵 RESUMEN DE AGENDA (MULTI-SEDE)
    # ===============================

    agendas_medico = AgendaMedico.objects.filter(
        medico=medico,
        centro_medico=centro_activo
    ).order_by('fecha')

    resumen_agenda = OrderedDict()

    dias_es = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo',
    }

    for agenda in agendas_medico:

        dia = agenda.fecha.strftime('%A')
        nombre_dia = dias_es[dia]

        resumen_agenda[nombre_dia] = {
            'inicio': agenda.hora_inicio.strftime('%H:%M'),
            'fin': agenda.hora_fin.strftime('%H:%M'),
            'duracion': agenda.duracion_turno,
            'consultorio': (
                agenda.consultorio.numero
                if agenda.consultorio else '-'
            )
        }

    # 🔥 Duración para mostrar en el badge
    duracion_turno = None

    if resumen_agenda:

        primer_dia = next(
            iter(resumen_agenda.values())
        )

        duracion_turno = primer_dia['duracion']
    return render(
        request,
        'turnos/disponibilidad_consulta.html',
        {

            'medico': medico,
            'resumen_agenda': resumen_agenda,
            'duracion_turno': duracion_turno,

            'centro_activo': centro_activo,

            'disponibilidad': disponibilidad,

            'horarios': horarios_ordenados,

            'offset': offset,
        }
    )

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

    # 🔵 SEDE ACTIVA
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
                centro_activo = CentroMedico.objects.filter(
                    id=centro_id
                ).first()

    if request.method == 'POST':

        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora_manual')
        observaciones = request.POST.get('observaciones')

        medico_id = request.session.get('medico_id')
        paciente_id = request.session.get('paciente_id')

        if not (fecha and hora and medico_id and paciente_id):

            messages.error(
                request,
                "Faltan datos para el sobreturno."
            )

            return redirect('turnos:ver_disponibilidad')

        # 🔥 VALIDAR SI EXISTE AGENDA EN ESA SEDE
        agenda = AgendaMedico.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            centro_medico=centro_activo
        ).first()

        if not agenda:

            messages.error(
                request,
                "El médico no tiene agenda en esta sede."
            )

            return redirect('turnos:ver_disponibilidad')

        # 🔥 VALIDAR SI YA EXISTE SOBRETURNO
        existe = Sobreturno.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            centro_medico=centro_activo
        ).exists()

        if existe:

            messages.warning(
                request,
                "Ya existe un sobreturno en ese horario."
            )

            return redirect('turnos:ver_disponibilidad')

        # 🔥 VALIDAR SI YA EXISTE TURNO NORMAL
        existe_turno = Turnos.objects.filter(
            medico_id=medico_id,
            fecha=fecha,
            hora=hora,
            centro_medico=centro_activo
        ).exclude(
            estado='CANCELADO'
        ).exists()

        if existe_turno:

            messages.warning(
                request,
                "Ya existe un turno reservado en ese horario."
            )

            return redirect('turnos:ver_disponibilidad')

        # 🔵 CREAR SOBRETURNO
        Sobreturno.objects.create(

            centro_medico=centro_activo,

            medico_id=medico_id,
            paciente_id=paciente_id,

            fecha=fecha,
            hora=hora,

            observaciones=observaciones,

            estado='PENDIENTE'
        )

        messages.success(
            request,
            f"Sobreturno creado correctamente en {centro_activo.nombre}."
        )

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
def tablero_consultorios(request):

    # 🔵 SEDE ACTIVA
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
        centro_activo = CentroMedico.objects.filter(
            id=centro_id
        ).first()
    

    fecha_str = request.GET.get('fecha')

    if fecha_str:

        fecha_base = datetime.strptime(
            fecha_str,
            '%Y-%m-%d'
        ).date()

    else:

        fecha_base = date.today()

    # 🔥 RANGO DE DÍAS
    dias = [
        fecha_base + timedelta(days=i)
        for i in range(10)
    ]

    # 🔵 SOLO CONSULTORIOS DE LA SEDE ACTIVA
    consultorios = Consultorio.objects.filter(
        centro_medico=centro_activo
    ).order_by('numero')

    tablero = []

    for c in consultorios:

        fila = {
            'consultorio': c,
            'dias': []
        }

        for dia in dias:

            # 🔵 SOLO AGENDAS DE LA SEDE ACTIVA
            agendas = AgendaMedico.objects.filter(
                consultorio=c,
                fecha=dia,
                centro_medico=centro_activo
            ).select_related('medico')

            bloques = []
            medicos = []
            huecos_total = []

            if agendas.exists():

                for agenda in agendas:

                    # 🔵 MÉDICO + HORARIO
                    medicos.append({
                        'nombre': agenda.medico.nombre,
                        'apellido': agenda.medico.apellido,
                        'hora_inicio': agenda.hora_inicio,
                        'hora_fin': agenda.hora_fin,
                    })

                    # 🔴 TURNOS DE ESA SEDE
                    turnos = Turnos.objects.filter(
                        medico=agenda.medico,
                        fecha=dia,
                        centro_medico=centro_activo,
                        hora__gte=agenda.hora_inicio,
                        hora__lte=agenda.hora_fin
                    ).exclude(
                        estado='CANCELADO'
                    ).order_by('hora')

                    # 🔥 GENERAR HUECOS
                    huecos_total = generar_huecos_consultorio(
                        agendas,
                        list(turnos)
                    )

                    # 🔴 BLOQUES OCUPADOS
                    for t in turnos:

                        bloques.append({
                            'hora': t.hora,
                            'paciente': t.paciente,
                            'medico': t.medico,
                            'estado': t.estado
                        })

                estado = 'ocupado' if bloques else 'libre'

            else:

                estado = 'sin_agenda'

            fila['dias'].append({
                'estado': estado,
                'bloques': bloques,
                'medicos': medicos,
                'huecos': huecos_total
            })

        tablero.append(fila)

    return render(request, 'turnos/tablero_consultorios.html', {
        'tablero': tablero,
        'dias': dias,
        'fecha': fecha_base,
        'centro_activo': centro_activo
    })

def generar_huecos_consultorio(agendas, turnos):

    huecos = []

    # 🔥 rango total del consultorio
    inicio = min(a.hora_inicio for a in agendas)
    fin = max(a.hora_fin for a in agendas)

    # 🔴 BLOQUES OCUPADOS (AGENDAS + TURNOS)
    ocupados = []

    # 🔵 agendas ocupan SIEMPRE el consultorio
    for a in agendas:
        ocupados.append((a.hora_inicio, a.hora_fin))

    # 🔴 turnos (opcional, pero ya están dentro de agenda)
    for t in turnos:
        duracion = 40 if t.es_sobreturno else 20
        fin_turno = (
            datetime.combine(date.today(), t.hora) + timedelta(minutes=duracion)
        ).time()

        ocupados.append((t.hora, fin_turno))

    # 🔥 ordenar bloques ocupados
    ocupados.sort()

    actual = inicio

    for inicio_oc, fin_oc in ocupados:

        if inicio_oc > actual:
            huecos.append({
                'inicio': actual,
                'fin': inicio_oc
            })

        actual = max(actual, fin_oc)

    if actual < fin:
        huecos.append({
            'inicio': actual,
            'fin': fin
        })

    return huecos


@login_required
def consultar_consultorios_disponibles(request):

    # 🔵 SEDE ACTIVA
    centro_id = request.session.get('centro_id')

    centro_activo = None

    if centro_id:
        centro_activo = CentroMedico.objects.filter(
            id=centro_id
        ).first()
    

    fecha = request.GET.get('fecha')
    hora_inicio = request.GET.get('hora_inicio')
    hora_fin = request.GET.get('hora_fin')
    medico_id = request.GET.get('medico_id')

    # 🔴 VALIDACIÓN
    if not (fecha and hora_inicio and hora_fin):

        return JsonResponse({
            'consultorios': []
        })

    try:

        fecha = datetime.strptime(
            fecha,
            '%Y-%m-%d'
        ).date()

        hora_inicio = datetime.strptime(
            hora_inicio,
            '%H:%M'
        ).time()

        hora_fin = datetime.strptime(
            hora_fin,
            '%H:%M'
        ).time()

    except ValueError:

        return JsonResponse({
            'consultorios': []
        })

    # 🔵 SOLO CONSULTORIOS DE LA SEDE ACTIVA
    consultorios = Consultorio.objects.filter(
        centro_medico=centro_activo
    ).order_by('numero')

    disponibles = []

    for c in consultorios:

        # 🔵 1. CONFLICTO CON AGENDA
        conflicto_agenda = AgendaMedico.objects.filter(
            fecha=fecha,
            consultorio=c,
            centro_medico=centro_activo,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        )

        # 🔥 EXCLUIR EL MISMO MÉDICO
        if medico_id:

            conflicto_agenda = conflicto_agenda.exclude(
                medico_id=medico_id
            )

        # 🔵 2. MÉDICOS QUE USAN ESE CONSULTORIO
        medicos_en_consultorio = AgendaMedico.objects.filter(
            fecha=fecha,
            consultorio=c,
            centro_medico=centro_activo
        ).values_list(
            'medico_id',
            flat=True
        )

        # 🔵 3. CONFLICTO CON TURNOS
        conflicto_turnos = Turnos.objects.filter(
            fecha=fecha,
            centro_medico=centro_activo,
            medico_id__in=medicos_en_consultorio,
            hora__gte=hora_inicio,
            hora__lt=hora_fin,
            estado='PENDIENTE'
        )

        # 🔵 4. CONFLICTO CON SOBRETURNOS
        conflicto_sobreturnos = Sobreturno.objects.filter(
            fecha=fecha,
            centro_medico=centro_activo,
            medico_id__in=medicos_en_consultorio,
            hora__gte=hora_inicio,
            hora__lt=hora_fin
        ).exclude(
            estado='CANCELADO'
        )

        # 🔵 5. DISPONIBLE
        if (
            not conflicto_agenda.exists()
            and not conflicto_turnos.exists()
            and not conflicto_sobreturnos.exists()
        ):

            disponibles.append({
                'id': c.id,
                'numero': c.numero
            })

    return JsonResponse({
        'consultorios': disponibles
    })


def validar_agenda(request):
    fecha = request.GET.get('fecha')
    medico_id = request.GET.get('medico_id')

    existe = AgendaMedico.objects.filter(
        medico_id=medico_id,
        fecha=fecha
    ).exists()

    return JsonResponse({
        'existe': existe
    })
    
    
@login_required
def historial_turno(request, turno_id):

    turno = get_object_or_404(
        Turnos,
        id=turno_id
    )

    historial = HistorialTurno.objects.filter(
        turno=turno
    ).select_related(
        'usuario',
        'sede_operacion'
    ).order_by('-fecha')

    return render(
        request,
        'turnos/historial_turno.html',
        {
            'turno': turno,
            'historial': historial
        }
    )
    
@login_required
def previsualizar_excepcion(request):

    medico_id = request.GET.get('medico_id')
    fecha = request.GET.get('fecha')
    tipo = request.GET.get('tipo')

    hora_inicio = request.GET.get('hora_inicio')
    hora_fin = request.GET.get('hora_fin')

    centro_id = request.session.get('centro_id')

    turnos = Turnos.objects.filter(
        medico_id=medico_id,
        fecha=fecha,
        centro_medico_id=centro_id
    ).exclude(
        estado='CANCELADO'
    )

    sobreturnos = Sobreturno.objects.filter(
        medico_id=medico_id,
        fecha=fecha
    ).exclude(
        estado='CANCELADO'
    )

    # ==========================
    # CERRADO
    # ==========================

    if tipo == 'CERRADO':

        turnos_afectados = turnos.count()
        sobreturnos_afectados = sobreturnos.count()

    # ==========================
    # MODIFICADO
    # ==========================

    elif tipo == 'MODIFICADO':

        if hora_inicio and hora_fin:

            hi = datetime.strptime(
                hora_inicio,
                '%H:%M'
            ).time()

            hf = datetime.strptime(
                hora_fin,
                '%H:%M'
            ).time()

            turnos_afectados = turnos.exclude(
                hora__gte=hi,
                hora__lt=hf
            ).count()

            sobreturnos_afectados = sobreturnos.exclude(
                hora__gte=hi,
                hora__lt=hf
            ).count()

        else:
            turnos_afectados = 0
            sobreturnos_afectados = 0

    # ==========================
    # REPROGRAMAR
    # ==========================

    elif tipo == 'REPROGRAMAR':

        turnos_afectados = turnos.count()
        sobreturnos_afectados = sobreturnos.count()

    else:

        turnos_afectados = 0
        sobreturnos_afectados = 0

    pacientes = list(
        turnos.select_related('paciente')
        .values_list(
            'paciente__apellido',
            'paciente__nombre'
        )[:5]
    )

    pacientes = [
        f'{a}, {n}'
        for a, n in pacientes
    ]

    return JsonResponse({

        'turnos': turnos_afectados,
        'sobreturnos': sobreturnos_afectados,
        'pacientes': pacientes

    })