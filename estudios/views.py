from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Estudio
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from .forms import EstudioForm

from paciente.models import Paciente

from historial.models import ConsultaMedica

@login_required
def buscar_y_cargar_estudio(request):
    paciente = None
    estudios = []
    dni = request.POST.get('dni') if request.method == 'POST' else request.GET.get('dni')
    seleccionar = request.GET.get('seleccionar')

    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
        except Paciente.DoesNotExist:
            messages.warning(request, "No se encontró un paciente con ese DNI.")

    if seleccionar:
        paciente = get_object_or_404(Paciente, id=seleccionar)

    if paciente:
        estudios = paciente.estudios.all().order_by('-fecha')

    if request.method == 'POST' and 'guardar_estudio' in request.POST:
        form = EstudioForm(request.POST, request.FILES)

        if paciente:
            # 🔥 FILTRAMOS CONSULTAS DEL PACIENTE
            form.fields['consulta'].queryset = ConsultaMedica.objects.filter(
                historia_clinica__paciente=paciente
            ).order_by('-fecha')

        if form.is_valid() and paciente:
            estudio = form.save(commit=False)
            estudio.paciente = paciente
            estudio.save()

            return render(request, 'estudios/cargar_estudio.html', {
                'form': EstudioForm(),
                'paciente': paciente,
                'estudios': paciente.estudios.all().order_by('-fecha'),
                'modal_exito': True,
            })

    else:
        form = EstudioForm()

        if paciente:
            # 🔥 TAMBIÉN FILTRAMOS EN GET
            form.fields['consulta'].queryset = ConsultaMedica.objects.filter(
                historia_clinica__paciente=paciente
            ).order_by('-fecha')

    return render(request, 'estudios/cargar_estudio.html', {
        'paciente': paciente,
        'form': form,
        'estudios': estudios,
    })
def listar_estudios_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    estudios = paciente.estudios.all()
    return render(request, 'estudios/listar_estudios.html', {'paciente': paciente, 'estudios': estudios})

@login_required
@require_POST
def eliminar_estudio(request, estudio_id):
    estudio = get_object_or_404(Estudio, id=estudio_id)
    paciente_id = estudio.paciente.id
    estudio.delete()
    return redirect(f"{reverse('buscar_y_cargar_estudio')}?seleccionar={paciente_id}")

@login_required
def ver_estudios_paciente(request):
    paciente = None
    estudios = []
    dni = request.GET.get('dni')

    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
            estudios = paciente.estudios.all().order_by('-fecha')
        except Paciente.DoesNotExist:
            messages.warning(request, "No se encontró un paciente con ese DNI.")

    return render(request, 'estudios/ver_estudios.html', {
        'paciente': paciente,
        'estudios': estudios,
    })