from .models import ObraSocial,PlanObraSocial

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
        "telefono",
        "email",
        "activa",
    )

    list_filter = (
        "activa",
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
                    ("observaciones",),
                    "activa",
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
    
