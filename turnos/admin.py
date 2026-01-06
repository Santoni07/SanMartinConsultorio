from django.contrib import admin

from django.contrib import admin
from .models import Turnos

@admin.register(Turnos)
class TurnosAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hora', 'medico', 'paciente', 'especialidad')
    list_filter = ('medico', 'fecha')
    search_fields = ('paciente__nombre', 'paciente__apellido', 'medico__nombre')