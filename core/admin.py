from django.contrib import admin
from .models import PerfilUsuario, CentroMedico


@admin.register(CentroMedico)
class CentroMedicoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'direccion',
        'telefono',
        'email',
        'activo',
    )

    list_filter = (
        'activo',
    )

    search_fields = (
        'nombre',
        'direccion',
    )


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'rol',
        'centro_principal',
        'activo',
        'created_at',
    )

    list_filter = (
        'rol',
        'activo',
        'centro_principal',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
    )

    readonly_fields = (
        'created_at',
    )

    filter_horizontal = (
        'centros',
    )

    fieldsets = (

        ('Usuario', {

            'fields': (
                'user',
                'rol',
                'activo',
            )

        }),

        ('Centro Principal', {

            'fields': (
                'centro_principal',
            )

        }),

        ('Centros Habilitados', {

            'fields': (
                'centros',
            )

        }),

        ('Auditoría', {

            'fields': (
                'created_at',
            )

        }),

    )