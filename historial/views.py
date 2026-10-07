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

    # ======================================================
    # PARÁMETROS DE BÚSQUEDA
    # ======================================================

    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    turnos = []


    # ======================================================
    # BUSCAR PACIENTES
    # ======================================================

    if query:

        # --------------------------------------------------
        # BÚSQUEDA POR DNI
        # --------------------------------------------------

        if tipo == 'dni':

            pacientes = Paciente.objects.filter(
                dni__icontains=query
            )


        # --------------------------------------------------
        # BÚSQUEDA POR NOMBRE
        # --------------------------------------------------

        elif tipo == 'nombre':

            pacientes = Paciente.objects.filter(
                nombre__icontains=query
            )


        # --------------------------------------------------
        # BÚSQUEDA POR APELLIDO
        # --------------------------------------------------

        elif tipo == 'apellido':

            pacientes = Paciente.objects.filter(
                apellido__icontains=query
            )


        # --------------------------------------------------
        # COMPATIBILIDAD CON BÚSQUEDA ANTERIOR
        # --------------------------------------------------
        # Si por algún motivo no viene "tipo",
        # busca en los tres campos como hacía antes.

        else:

            pacientes = Paciente.objects.filter(
                Q(nombre__icontains=query) |
                Q(apellido__icontains=query) |
                Q(dni__icontains=query)
            )


        # ==================================================
        # FECHA Y HORA ACTUAL
        # ==================================================

        hoy = date.today()
        ahora = datetime.now().time()


        # ==================================================
        # TURNOS NORMALES
        # ==================================================

        turnos_normales = Turnos.objects.filter(
            paciente__in=pacientes,
            fecha=hoy
        ).select_related(
            'paciente'
        ).order_by(
            'hora'
        )


        # ==================================================
        # SOBRETURNOS
        # ==================================================

        sobreturnos = Sobreturno.objects.filter(
            paciente__in=pacientes,
            fecha=hoy
        ).select_related(
            'paciente'
        ).order_by(
            'hora'
        )


        # ==================================================
        # IDENTIFICAR TIPO DE TURNO
        # ==================================================

        for turno in turnos_normales:
            turno.tipo_turno = 'NORMAL'


        for sobreturno in sobreturnos:
            sobreturno.tipo_turno = 'SOBRETURNO'


        # ==================================================
        # UNIFICAR TURNOS
        # ==================================================

        turnos = (
            list(turnos_normales)
            +
            list(sobreturnos)
        )


        # ==================================================
        # ORDENAR POR HORA
        # ==================================================

        turnos.sort(
            key=lambda x: x.hora
        )


        # ==================================================
        # DETECTAR PRÓXIMO TURNO PENDIENTE
        # ==================================================

        turnos_futuros = [

            turno

            for turno in turnos

            if (
                turno.hora >= ahora
                and
                turno.estado == 'PENDIENTE'
            )

        ]


        turno_proximo = (
            turnos_futuros[0]
            if turnos_futuros
            else None
        )


        # ==================================================
        # MARCAR TURNO ACTUAL
        # ==================================================

        for turno in turnos:

            turno.es_actual = (
                turno == turno_proximo
            )


    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        'historial/buscar_paciente_consulta.html',
        {
            'turnos': turnos,
            'query': query,
            'tipo': tipo,
        }
    )

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
        
        if "guardar_parcial" in request.POST:
            form.fields["diagnostico"].required = False
            form.fields["tratamiento"].required = False
            
        if not form.is_valid():
            print(form.errors)

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
            consulta.fecha = turno.fecha

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

                messages.success(
                    request,
                    "CONSULTA_FINALIZADA"
                )

                return redirect(
                    'cargar_consulta_paciente',
                    turno_id=turno.id
                )

            return redirect(
                'cargar_consulta_paciente',
                turno_id=turno.id
            )

    else:

        if consulta_existente:

            form = ConsultaMedicaForm(
                instance=consulta_existente
            )

        else:

            consulta_nueva = ConsultaMedica(
                fecha=turno.fecha
            )

            form = ConsultaMedicaForm(
                instance=consulta_nueva
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

    # ======================================================
    # PARÁMETROS DE BÚSQUEDA
    # ======================================================

    tipo = request.GET.get('tipo', 'dni')
    q = request.GET.get('q', '').strip()

    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    paciente = None
    pacientes_encontrados = None
    historia = None
    consultas = []
    estudios_generales = []


    # ======================================================
    # BUSCAR PACIENTE
    # ======================================================

    if q:

        # --------------------------------------------------
        # BÚSQUEDA POR DNI
        # --------------------------------------------------

        if tipo == 'dni':

            try:
                paciente = Paciente.objects.get(dni=q)

            except Paciente.DoesNotExist:
                paciente = None


        # --------------------------------------------------
        # BÚSQUEDA POR NOMBRE
        # --------------------------------------------------

        elif tipo == 'nombre':

            pacientes = Paciente.objects.filter(
                nombre__icontains=q
            ).order_by(
                'apellido',
                'nombre'
            )

            cantidad = pacientes.count()

            if cantidad == 1:

                paciente = pacientes.first()

            elif cantidad > 1:

                pacientes_encontrados = pacientes


        # --------------------------------------------------
        # BÚSQUEDA POR APELLIDO
        # --------------------------------------------------

        elif tipo == 'apellido':

            pacientes = Paciente.objects.filter(
                apellido__icontains=q
            ).order_by(
                'apellido',
                'nombre'
            )

            cantidad = pacientes.count()

            if cantidad == 1:

                paciente = pacientes.first()

            elif cantidad > 1:

                pacientes_encontrados = pacientes


    # ======================================================
    # SI ENCONTRAMOS UN PACIENTE
    # ======================================================

    if paciente:

        historia = HistoriaClinica.objects.filter(
            paciente=paciente
        ).first()


        # ==================================================
        # CONSULTAS
        # ==================================================

        if historia:

            consultas = historia.consultas.prefetch_related(
                'estudios'
            )


            # ----------------------------------------------
            # FILTRO POR MES
            # ----------------------------------------------

            if mes:

                consultas = consultas.filter(
                    fecha__month=mes
                )


            # ----------------------------------------------
            # FILTRO POR AÑO
            # ----------------------------------------------

            if anio:

                consultas = consultas.filter(
                    fecha__year=anio
                )


            consultas = consultas.order_by(
                '-fecha'
            )


            # ==================================================
            # ESTUDIOS ASOCIADOS A CADA CONSULTA
            # ==================================================

            for consulta in consultas:

                estudios_fk = consulta.estudios.all()

                estudios_por_fecha = Estudio.objects.filter(
                    paciente=paciente,
                    consulta__isnull=True,
                    fecha=consulta.fecha
                )

                consulta.estudios_combinados = (
                    list(estudios_fk)
                    +
                    list(estudios_por_fecha)
                )


            # ==================================================
            # ESTUDIOS GENERALES
            # ==================================================

            fechas_consultas = [
                c.fecha
                for c in consultas
            ]


            estudios_generales = Estudio.objects.filter(
                paciente=paciente,
                consulta__isnull=True
            ).exclude(
                fecha__in=fechas_consultas
            )


    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        'historial/buscar_historia_dni.html',
        {
            'tipo': tipo,
            'q': q,

            # Lo dejamos también por compatibilidad
            # con partes antiguas del template
            'dni': paciente.dni if paciente else None,

            'paciente': paciente,
            'pacientes_encontrados': pacientes_encontrados,

            'historia': historia,
            'consultas': consultas,
            'estudios_generales': estudios_generales,

            'mes': mes,
            'anio': anio,
        }
    )
    
@login_required
def detalle_consulta(request, consulta_id):
    consulta = get_object_or_404(ConsultaMedica, id=consulta_id)

    estudios = consulta.estudios.all()

    return render(request, "historial/detalle_consulta.html", {
        "consulta": consulta,
        "estudios": estudios,
    })

from django.http import HttpResponse   

def buscar_antecedentes_por_dni(request):

    paciente = None
    historia = None
    mensaje = None

    # ==========================================
    # GUARDAR
    # ==========================================

    if request.method == "POST":

        dni = request.POST.get("dni")

        try:

            paciente = Paciente.objects.get(dni=dni)

            historia = paciente.historiaclinica

            historia.antecedentes_patologicos = request.POST.get(
                "antecedentes_patologicos"
            )

            historia.antecedentes_alergicos = request.POST.get(
                "antecedentes_alergicos"
            )

            historia.antecedentes_toxicos = request.POST.get(
                "antecedentes_toxicos"
            )

            historia.antecedentes_quirurgicos = request.POST.get(
                "antecedentes_quirurgicos"
            )

            historia.medicacion_base = request.POST.get(
                "medicacion_base"
            )

            historia.save()

            messages.success(
                request,
                "Antecedentes actualizados correctamente."
            )

        except Paciente.DoesNotExist:

            mensaje = "Paciente inexistente."

        except HistoriaClinica.DoesNotExist:

            mensaje = "El paciente no posee Historia Clínica."

    # ==========================================
    # BUSCAR
    # ==========================================

    dni = request.GET.get("dni")

    if request.method == "POST":
        dni = request.POST.get("dni")

    if dni:

        try:

            paciente = Paciente.objects.get(dni=dni)

            historia = paciente.historiaclinica

        except Paciente.DoesNotExist:

            mensaje = "No existe un paciente con ese DNI."

        except HistoriaClinica.DoesNotExist:

            mensaje = "El paciente no posee Historia Clínica."

    return render(
        request,
        "historial/buscar_antecedentes_por_dni.html",
        {
            "paciente": paciente,
            "historia": historia,
            "mensaje": mensaje,
            "dni": dni,
        },
    )