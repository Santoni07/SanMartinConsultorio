from django.contrib import admin

from django.contrib import admin
from .models import Turnos

@admin.register(Turnos)
class TurnosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'medico', 'paciente', 'especialidad','estado')
    list_filter = ('medico', 'fecha')
    search_fields = ('paciente__nombre', 'paciente__apellido', 'medico__nombre')
    
# turnos/admin.py

from django.contrib import admin
from .models import ExcepcionAgenda


@admin.register(ExcepcionAgenda)
class ExcepcionAgendaAdmin(admin.ModelAdmin):

    list_display = (
        'medico',
        'fecha',
        'tipo',
        'hora_inicio',
        'hora_fin',
        'nueva_fecha',
        'motivo',
    )

    list_filter = (
        'tipo',
        'medico',
        'fecha',
    )

    search_fields = (
        'medico__nombre',
        'medico__apellido',
        'motivo',
    )

    ordering = ('-fecha',)

    date_hierarchy = 'fecha'

    list_per_page = 20

# turnos/admin.py

from django.contrib import admin
from .models import DisponibilidadMedico, AgendaMedico, Sobreturno, Consultorio


# ===============================
# 🟦 DISPONIBILIDAD BASE
# ===============================
@admin.register(DisponibilidadMedico)
class DisponibilidadMedicoAdmin(admin.ModelAdmin):

    list_display = (
        'medico',
        'dia_semana_display',
        'hora_inicio',
        'hora_fin',
        'duracion_turno',
    )

    list_filter = (
        'medico',
        'dia_semana',
    )

    search_fields = (
        'medico__nombre',
        'medico__apellido',
    )

    ordering = ('medico', 'dia_semana')

    list_per_page = 20

    def dia_semana_display(self, obj):
        return obj.get_dia_semana_display()

    dia_semana_display.short_description = "Día"


@admin.register(AgendaMedico)
class AgendaMedicoAdmin(admin.ModelAdmin):

    # ==========================================================
    # LISTADO
    # ==========================================================
    list_display = (
        "id",
        "fecha",
        "medico",
        "centro_medico",
        "consultorio",
        "hora_inicio",
        "hora_fin",
        "duracion_turno",
        "creado_por",
        "fecha_creacion",
    )

    # ==========================================================
    # FILTROS LATERALES
    # ==========================================================
    list_filter = (
        "centro_medico",       # 🔥 Filtrar por sede
        "medico",              # 🔥 Filtrar por médico
        "fecha",
        "consultorio",
        "duracion_turno",
        "sede_operacion",
    )

    # ==========================================================
    # BUSCADOR
    # ==========================================================
    search_fields = (
        "medico__nombre",
        "medico__apellido",
        "medico__matricula",
        "centro_medico__nombre",
    )

    # ==========================================================
    # ORDEN
    # ==========================================================
    ordering = (
        "-fecha",
        "hora_inicio",
    )

    # ==========================================================
    # NAVEGACIÓN POR FECHA
    # ==========================================================
    date_hierarchy = "fecha"

    # ==========================================================
    # CAMPOS SOLO LECTURA
    # ==========================================================
    readonly_fields = (
        "creado_por",
        "modificado_por",
        "fecha_creacion",
        "fecha_modificacion",
        "sede_operacion",
    )

    # ==========================================================
    # FORMULARIO DE ALTA / MODIFICACIÓN
    # ==========================================================
    fieldsets = (
        (
            "Agenda médica",
            {
                "fields": (
                    "centro_medico",
                    "medico",
                    "consultorio",
                    "fecha",
                )
            },
        ),
        (
            "Horario",
            {
                "fields": (
                    "hora_inicio",
                    "hora_fin",
                    "duracion_turno",
                )
            },
        ),
        (
            "Trazabilidad",
            {
                "classes": ("collapse",),
                "fields": (
                    "creado_por",
                    "modificado_por",
                    "sede_operacion",
                    "fecha_creacion",
                    "fecha_modificacion",
                ),
            },
        ),
    )

    # ==========================================================
    # OPTIMIZACIÓN DE CONSULTAS
    # ==========================================================
    list_select_related = (
        "centro_medico",
        "medico",
        "consultorio",
        "creado_por",
        "modificado_por",
        "sede_operacion",
    )

    # ==========================================================
    # REGISTRO AUTOMÁTICO DE TRAZABILIDAD
    # ==========================================================
    def save_model(self, request, obj, form, change):

        if not change or obj.creado_por_id is None:
            obj.creado_por = request.user

        obj.modificado_por = request.user

        # Guardamos la sede desde la que está operando el usuario
        centro_id = request.session.get("centro_id")

        if centro_id:
            obj.sede_operacion_id = centro_id

        super().save_model(request, obj, form, change)

@admin.register(Sobreturno)
class SobreturnoAdmin(admin.ModelAdmin):
    list_display = ('medico', 'paciente', 'fecha', 'hora', 'estado')
    list_filter = ('medico', 'fecha', 'estado')
    search_fields = ('paciente__nombre', 'medico__nombre')
    
    
@admin.register(Consultorio)
class ConsultorioAdmin(admin.ModelAdmin):
    list_display = ('numero',)
    search_fields = ('numero',)