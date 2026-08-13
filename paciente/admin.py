from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):

    list_display = (
        'apellido',
        'nombre',
        'dni',
        'edad',
        'sexo',
        'telefono',
        'obrasocial',
        'plan_obra_social',
        'activo',
        'fecha_alta',
    )

    list_filter = (
        'sexo',
        'activo',
        'obrasocial',
        'plan_obra_social',
        'fecha_alta',
    )

    search_fields = (
        'apellido',
        'nombre',
        'dni',
        'telefono',
        'email',
    )

    readonly_fields = (
        'fecha_alta',
        'fecha_modificacion',
    )

    ordering = (
        'apellido',
        'nombre',
    )

    fieldsets = (

        ('Datos Personales', {
            'fields': (
                'apellido',
                'nombre',
                'dni',
                'fecha_nacimiento',
                'sexo',
            )
        }),

        ('Contacto', {
            'fields': (
                'telefono',
                'email',
                'direccion',
            )
        }),

        ('Información Médica', {
            'fields': (
                'obrasocial',
                'plan_obra_social',
                'observaciones',
            )
        }),

        ('Estado', {
            'fields': (
                'activo',
            )
        }),

        ('Auditoría', {
            'fields': (
                'fecha_alta',
                'fecha_modificacion',
            )
        }),
    )