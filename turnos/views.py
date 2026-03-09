from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import  SeleccionMedicoForm
from .models import Turnos
from paciente.models import Paciente
from medicos.models import Medico
from datetime import datetime, timedelta, time
from django.contrib import messages
from datetime import date

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
    horarios = [time(h, m) for h in range(7, 21) for m in (0, 20, 40)]

    disponibilidad = {}
    for dia in dias:
        turnos_dia = Turnos.objects.filter(medico=medico, fecha=dia)
        dia_data = []

        for hora in horarios:
            hora_str = hora.strftime('%H:%M')
            turno = next((t for t in turnos_dia if t.hora.strftime('%H:%M') == hora_str), None)
            

            if turno:
                dia_data.append({
                    'hora': hora,
                    'estado': 'ocupado',
                    'paciente': turno.paciente,
                    'observaciones': turno.observaciones,
                    'turno_id': turno.id,
                })
            else:
                dia_data.append({
                    'hora': hora,
                    'estado': 'libre',
                })

        disponibilidad[dia] = dia_data


    return render(request, 'turnos/disponibilidad.html', {
        'medico': medico,
        'disponibilidad': disponibilidad,
        'horarios': horarios,
        'offset': offset,
    })

@login_required
def reservar_turno(request):
    if request.method == 'POST':
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        observaciones = request.POST.get('observaciones', '')

        if not fecha_str or not hora_str:
            messages.error(request, "Faltan datos de fecha u hora.")
            return redirect('turnos:ver_disponibilidad')
        print("DEBUG - fecha_str:", fecha_str)
        print("DEBUG - hora_str:", hora_str)

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Error en el formato de fecha u hora.")
            return redirect('turnos:ver_disponibilidad')

        ya_existe = Turnos.objects.filter(
            medico_id=request.session['medico_id'],
            fecha=fecha,
            hora=hora
        ).exists()

        if not ya_existe:
            Turnos.objects.create(
                especialidad_id=request.session['especialidad_id'],
                medico_id=request.session['medico_id'],
                paciente_id=request.session['paciente_id'],
                fecha=fecha,
                hora=hora,
                observaciones=observaciones
            )
            messages.success(request, "Turno reservado correctamente.")
        else:
            messages.warning(request, "Ese turno ya fue reservado.")

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