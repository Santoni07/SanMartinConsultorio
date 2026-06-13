from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import LiquidacionMedica


@admin.register(LiquidacionMedica)
class LiquidacionMedicaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'fecha',
        'medico',
        'centro_medico',
        'total_honorarios',
        'cantidad_prestaciones',
    )

    list_filter = (
        'centro_medico',
        'fecha',
    )

    search_fields = (
        'medico__apellido',
        'medico__nombre',
    )