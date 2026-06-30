from django.contrib import admin
from .models import (
    CajaDiaria,
    MedioPago,
    MovimientoCaja,
    HistorialMovimientoCaja,
     ConceptoFacturacion,
)


@admin.register(MedioPago)
class MedioPagoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'activo',
    )

    list_filter = (
        'activo',
    )

    search_fields = (
        'nombre',
    )


class MovimientoCajaInline(admin.TabularInline):
    model = MovimientoCaja
    extra = 0
    readonly_fields = (
        'fecha_creacion',
        'creado_por',
    )

    can_delete = False


@admin.register(CajaDiaria)
class CajaDiariaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'fecha',
        'centro_medico',
        'estado',
        'saldo_inicial',
        'total_ingresos_admin',
        'total_egresos_admin',
        'saldo_final_admin',
        'abierta_por',
    )

    list_filter = (
        'estado',
        'centro_medico',
        'fecha',
    )

    search_fields = (
        'centro_medico__nombre',
    )

    readonly_fields = (
        'fecha_apertura',
        'fecha_cierre',
    )

    inlines = [
        MovimientoCajaInline
    ]

    def total_ingresos_admin(self, obj):
        return obj.total_ingresos
    total_ingresos_admin.short_description = 'Ingresos'

    def total_egresos_admin(self, obj):
        return obj.total_egresos
    total_egresos_admin.short_description = 'Egresos'

    def saldo_final_admin(self, obj):
        return obj.saldo_final
    saldo_final_admin.short_description = 'Saldo Final'


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):


    list_display = (
        'id',
        'fecha_creacion',
        'centro_medico',
        'tipo',
        'importe',
        'concepto_facturacion',
        'importe_medico',
        'importe_consultorio',
        'liquidado',
        'medio_pago',
        'paciente',
        'estado',
        'importe_iva',
        'retencion_monto',
        'creado_por',
    )

    list_filter = (
        'tipo',
        'estado',
        'liquidado',
        'medio_pago',
        'centro_medico',
        'fecha_creacion',
    )

    search_fields = (
        'paciente__nombre',
        'paciente__apellido',
        'concepto',
        'observacion',
    )

    readonly_fields = (
        'fecha_creacion',
        'fecha_anulacion',

        'importe_bruto',
        'importe_iva',

        'retencion_monto',
        'retencion_motivo',

        'importe_neto',

        'importe_medico',
        'importe_consultorio',
    )

    autocomplete_fields = (
        'paciente',
        'turno',
        'medio_pago',
        'centro_medico',
    )

    fieldsets = (

        (
            'Información General',
            {
                'fields': (
                    'caja',
                    'centro_medico',
                    'turno',
                    'paciente',
                )
            }
        ),

        (
            'Movimiento',
            {
                'fields': (
                    'tipo',
                    'medio_pago',
                    'importe',
                    'concepto',
                    'observacion',
                )
            }
        ),

        (
            'Distribución Económica',
            {
                'fields': (
                    'concepto_facturacion',

                    'importe_bruto',
                    'importe_iva',

                    'retencion_monto',
                    'retencion_motivo',

                    'importe_neto',

                    'importe_medico',
                    'importe_consultorio',

                    'liquidado',
                    'liquidacion',
                )
            }
        ),

        (
            'Auditoría',
            {
                'fields': (
                    'estado',
                    'creado_por',
                    'fecha_creacion',
                    'anulado_por',
                    'fecha_anulacion',
                    'motivo_anulacion',
                )
            }
        ),
)




@admin.register(HistorialMovimientoCaja)
class HistorialMovimientoCajaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'fecha_hora',
        'accion',
        'centro_medico',
        'usuario',
        'movimiento',
    )

    list_filter = (
        'accion',
        'centro_medico',
        'fecha_hora',
    )

    search_fields = (
        'usuario__username',
        'descripcion',
    )

    readonly_fields = (
        'fecha_hora',
    )

    fieldsets = (
        (
            'Información',
            {
                'fields': (
                    'caja',
                    'movimiento',
                    'accion',
                )
            }
        ),
        (
            'Auditoría',
            {
                'fields': (
                    'usuario',
                    'centro_medico',
                    'fecha_hora',
                )
            }
        ),
        (
            'Detalle',
            {
                'fields': (
                    'descripcion',
                    'datos_anteriores',
                    'datos_nuevos',
                )
            }
        ),
    )
    
@admin.register(ConceptoFacturacion)
class ConceptoFacturacionAdmin(admin.ModelAdmin):

    list_display = (
        'nomenclador',
        'tipo_concepto',
        'tipo_calculo',
        'porcentaje_medico',
        'porcentaje_consultorio',
        'porcentaje_iva',
        'honorario_fijo_medico',
        'tipo_proveedor',
        'importe_proveedor',
        'activo',
    )

    search_fields = (
        'nomenclador__codigo',
        'nomenclador__descripcion',
    )

    list_filter = (
        'activo',
        'tipo_concepto',
        'tipo_calculo',
        'tipo_proveedor',
    )

    ordering = (
        'nomenclador__codigo',
    )

    autocomplete_fields = (
        'nomenclador',
    )