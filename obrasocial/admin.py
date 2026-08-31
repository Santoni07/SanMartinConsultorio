from .models import (
    ObraSocial,
    PlanObraSocial,
    MasterObraSocial,
    DetalleMasterObraSocial,
)
from django.contrib import admin

# ==========================================================
# INLINE PLANES
# ==========================================================

class PlanObraSocialInline(admin.TabularInline):

    model = PlanObraSocial

    extra = 0

    fields = (
        "codigo",
        "nombre",
        "orden",
        "activo",
    )

    ordering = (
        "orden",
        "codigo",
    )

    show_change_link = True


# ==========================================================
# OBRAS SOCIALES
# ==========================================================

@admin.register(ObraSocial)
class ObraSocialAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "sigla",
        "nombre",
        "usa_planes",
        "telefono",
        "email",
        "activa",
    )

    list_filter = (
        "usa_planes",
        "activa",
        "es_particular",
        "provincia",
    )

    search_fields = (
        "codigo",
        "sigla",
        "nombre",
        "cuit",
        "telefono",
        "email",
    )

    ordering = (
        "nombre",
    )

    list_per_page = 25

    inlines = [
        PlanObraSocialInline,
    ]

    fieldsets = (

        (
            "Datos Generales",
            {
                "fields": (
                    ("nombre", "sigla"),
                    ("codigo", "cuit"),
                    ("telefono", "email"),
                    ("domicilio",),
                    ("ciudad", "provincia"),
                    ("usa_planes", "activa","es_particular"),
                    ("observaciones",),
                )
            },
        ),

        (
            "Portal Web",
            {
                "classes": ("collapse",),

                "fields": (
                    "sitio_web",
                    "portal_prestadores",
                    "portal_autorizaciones",
                    "portal_afiliados",
                    "cartilla_online",
                    "credenciales_online",
                    "observaciones_portal",
                )
            },
        ),

    )
# ==========================================================
# PLANES
# ==========================================================

@admin.register(PlanObraSocial)
class PlanObraSocialAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "nombre",
        "obra_social",
        "activo",
        "fecha_alta",
    )

    list_filter = (
        "obra_social",
        "activo",
    )

    search_fields = (
        "codigo",
        "nombre",
        "obra_social__nombre",
        "obra_social__sigla",
    )

    ordering = (
        "obra_social",
        "orden",
        "codigo",
    )

    list_per_page = 30

    autocomplete_fields = (
        "obra_social",
    )

    readonly_fields = (
        "fecha_alta",
        "fecha_modificacion",
    )

    fieldsets = (

        (
            "Datos del Plan",
            {
                "fields": (
                    ("obra_social",),
                    ("codigo", "nombre"),
                    ("orden", "activo"),
                    "observaciones",
                )
            },
        ),

        (
            "Auditoría",
            {
                "classes": ("collapse",),

                "fields": (
                    "fecha_alta",
                    "fecha_modificacion",
                )
            },
        ),

    )
    
# ==========================================================
# INLINE DETALLE MASTER
# ==========================================================

class DetalleMasterObraSocialInline(admin.TabularInline):

    model = DetalleMasterObraSocial

    extra = 0

    fields = (
        "detalle_movimiento",
        "estado",
        "importe_presentado",
        "importe_reconocido",
        "importe_debitado",
        "refacturable",
        "estado_refacturacion",
    )

    readonly_fields = (
        "detalle_movimiento",
        "fecha_incorporacion",
    )

    show_change_link = True


# ==========================================================
# MASTER DE OBRA SOCIAL
# ==========================================================

@admin.register(MasterObraSocial)
class MasterObraSocialAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "obra_social",
        "mes",
        "anio",
        "estado",
        "fecha_presentacion",
        "numero_presentacion",
        "numero_factura",
        "fecha_cobro",
        "creado_por",
    )

    list_filter = (
        "estado",
        "obra_social",
        "anio",
        "mes",
    )

    search_fields = (
        "obra_social__nombre",
        "obra_social__sigla",
        "numero_presentacion",
        "numero_factura",
    )

    ordering = (
        "-anio",
        "-mes",
        "obra_social__nombre",
    )

    list_per_page = 30

    readonly_fields = (
        "fecha_creacion",
        "fecha_modificacion",
    )

    inlines = [
        DetalleMasterObraSocialInline,
    ]

    fieldsets = (

        (
            "Master",
            {
                "fields": (
                    "obra_social",
                    ("mes", "anio"),
                    "estado",
                )
            },
        ),

        (
            "Presentación",
            {
                "fields": (
                    "fecha_presentacion",
                    "numero_presentacion",
                    "numero_factura",
                )
            },
        ),

        (
            "Cobro",
            {
                "fields": (
                    "fecha_cobro",
                )
            },
        ),

        (
            "Observaciones",
            {
                "fields": (
                    "observaciones",
                )
            },
        ),

        (
            "Auditoría",
            {
                "classes": ("collapse",),
                "fields": (
                    "creado_por",
                    "fecha_creacion",
                    "fecha_modificacion",
                )
            },
        ),

    )



# ==========================================================
# DETALLE MASTER DE OBRA SOCIAL
# ==========================================================

@admin.register(DetalleMasterObraSocial)
class DetalleMasterObraSocialAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "master",
        "detalle_movimiento",
        "estado",
        "importe_presentado",
        "importe_reconocido",
        "importe_debitado",
        "refacturable",
        "estado_refacturacion",
        "fecha_resolucion",
    )

    list_filter = (
        "estado",
        "refacturable",
        "estado_refacturacion",
        "master__obra_social",
    )

    search_fields = (
        "master__obra_social__nombre",
        "master__obra_social__sigla",
        "detalle_movimiento__codigo",
        "detalle_movimiento__descripcion",
        "motivo_debito",
    )

    ordering = (
        "-master__anio",
        "-master__mes",
        "id",
    )

    list_per_page = 50

    readonly_fields = (
        "fecha_incorporacion",
    )
