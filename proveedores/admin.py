from django.contrib import admin
from .models import Proveedor, LiquidacionProveedor,PagoLiquidacionProveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "tipo",
        "telefono",
        "activo",
    )

    search_fields = (
        "nombre",
        "razon_social",
        "cuit",
    )

    list_filter = (
        "tipo",
        "activo",
    )
    
    
@admin.register(LiquidacionProveedor)
class LiquidacionProveedorAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "proveedor",
        "fecha",
        "cantidad_prestaciones",
        "total",
        "estado",
    )

    list_filter = (
        "estado",
        "fecha",
    )

    search_fields = (
        "proveedor__nombre",
    )

    autocomplete_fields = (
        "proveedor",
        "generado_por",
    )
    
@admin.register(PagoLiquidacionProveedor)
class PagoLiquidacionProveedorAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "liquidacion",
        "importe",
        "fecha",
        "registrado_por",
    )

    autocomplete_fields = (
        "liquidacion",
        "movimiento_caja",
        "registrado_por",
    )