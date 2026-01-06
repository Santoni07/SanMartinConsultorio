from django.shortcuts import render, get_object_or_404, redirect
from .models import HistoriaClinica, ConsultaMedica
from .forms import ConsultaMedicaForm
from paciente.models import Paciente
from django.db.models import Q


def ver_historia_clinica(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)
    consultas = historia.consultas.all().order_by('-fecha')
    return render(request, 'historial/historia_clinica.html', {
        'paciente': paciente,
        'historia': historia,
        'consultas': consultas,
    })

def buscar_paciente_consulta(request):
    query = request.GET.get('q')
    pacientes = None
    if query:
        pacientes = Paciente.objects.filter(nombre__icontains=query) | \
                    Paciente.objects.filter(apellido__icontains=query) | \
                    Paciente.objects.filter(dni__icontains=query)
    return render(request, 'historial/buscar_paciente_consulta.html', {'pacientes': pacientes})

def cargar_consulta_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)

    if request.method == 'POST':
        form = ConsultaMedicaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.historia_clinica = historia
            consulta.medico = request.user.medico  # Ajustar según tu modelo
        
            consulta.save()
            return redirect('ver_historia_clinica', paciente_id=paciente.id)
    else:
        form = ConsultaMedicaForm()

    return render(request, 'historial/cargar_consulta.html', {
        'form': form,
        'paciente': paciente
    })

def buscar_historia_por_dni(request):
    dni = request.GET.get('dni')
    paciente = None
    historia = None
    consultas = []

    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
            historia = HistoriaClinica.objects.filter(paciente=paciente).first()
            if historia:
                consultas = historia.consultas.all().order_by('-fecha')
        except Paciente.DoesNotExist:
            paciente = None

    return render(request, 'historial/buscar_historia_dni.html', {
        'dni': dni,
        'paciente': paciente,
        'historia': historia,
        'consultas': consultas,
    })