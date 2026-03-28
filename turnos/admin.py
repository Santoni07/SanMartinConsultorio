from django.contrib import admin

from django.contrib import admin
from .models import Turnos

@admin.register(Turnos)
class TurnosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'medico', 'paciente', 'especialidad')
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
from .models import DisponibilidadMedico, AgendaMedico, Sobreturno


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


# ===============================
# 🟩 AGENDA GENERADA
# ===============================
@admin.register(AgendaMedico)
class AgendaMedicoAdmin(admin.ModelAdmin):

    list_display = (
        'medico',
        'fecha',
        'hora_inicio',
        'hora_fin',
        'duracion_turno',
    )

    list_filter = (
        'medico',
        'fecha',
    )

    search_fields = (
        'medico__nombre',
        'medico__apellido',
    )

    ordering = ('-fecha',)

    date_hierarchy = 'fecha'

    list_per_page = 30
    
@admin.register(Sobreturno)
class SobreturnoAdmin(admin.ModelAdmin):
    list_display = ('medico', 'paciente', 'fecha', 'hora', 'estado')
    list_filter = ('medico', 'fecha', 'estado')
    search_fields = ('paciente__nombre', 'medico__nombre')