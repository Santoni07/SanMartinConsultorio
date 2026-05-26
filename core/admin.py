from django.contrib import admin

# Register your models here.
from .models import CentroMedico


@admin.register(CentroMedico)
class CentroMedicoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'direccion',
        'telefono',
        'email',
        'activo',
    )

    search_fields = (
        'nombre',
        'direccion',
    )

    list_filter = (
        'activo',
    )

    ordering = (
        'nombre',
    )