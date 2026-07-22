from .models import ObraSocial,PlanObraSocial

from django.contrib import admin
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
@admin.register(PlanObraSocial)
class PlanObraSocialAdmin(admin.ModelAdmin):

    list_display = (

        "obra_social",

        "nombre",

        "codigo",

        "activo",

    )

    list_filter = (

        "obra_social",

        "activo",

    )

    search_fields = (

        "nombre",

        "codigo",

        "obra_social__nombre",

    )

    autocomplete_fields = (

        "obra_social",

    )

    ordering = (

        "obra_social",

        "nombre",

    )