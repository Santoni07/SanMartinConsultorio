from django.contrib import admin

# Register your models here.
from .models import CentroMedico,PerfilUsuario


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

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'rol',
        'activo',
    )

    list_filter = (
        'rol',
        'activo',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
    )

    filter_horizontal = (
        'centros',
    )

    ordering = (
        'user',
    )